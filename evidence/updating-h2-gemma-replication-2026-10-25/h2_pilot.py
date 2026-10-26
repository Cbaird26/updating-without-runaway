#!/usr/bin/env python3
"""H2 pilot runner: freeze -> practice (mechanical check) -> test -> analysis.

Single use. No retries. Standard library only. Talks only to the local Ollama
server on 127.0.0.1:11434. Run from any directory:

    python3 -B h2_pilot.py --all
"""
import argparse, datetime, hashlib, json, platform, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL = 'http://127.0.0.1:11434'
FROZEN = ['PROTOCOL.md', 'protocol.json', 'cases.json', 'h2_pilot.py', 'analyze.py']


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha(p):
    return sha_bytes(Path(p).read_bytes())


def save(p, obj):
    p = Path(p)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(p)


def http_transport(url, payload=None, timeout=20):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'},
                                 method='POST' if data is not None else 'GET')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as r:
        return r.read()


TRANSPORT = http_transport  # replaced only by offline rehearsal tests


def model_info(name):
    tags = json.loads(TRANSPORT(LOCAL + '/api/tags'))
    match = [m for m in tags.get('models', []) if m.get('name') == name]
    if not match:
        raise SystemExit('Model not installed: ' + name)
    return {k: match[0].get(k) for k in ('name', 'digest', 'size', 'details')}


class Runner:
    def __init__(self, protocol, rawdir):
        self.p = protocol
        self.raw = Path(rawdir)
        self.raw.mkdir(parents=True, exist_ok=False)
        self.n = 0

    def chat(self, system, user, schema, budget, tag):
        s = self.p['settings']
        payload = {'model': self.p['model'], 'stream': False, 'think': s['think'], 'format': schema,
                   'messages': [{'role': 'system', 'content': system},
                                {'role': 'user', 'content': json.dumps(user, ensure_ascii=False)}],
                   'options': {'temperature': s['temperature'], 'seed': s['seed'],
                               'num_predict': budget, 'num_ctx': s['num_ctx']}}
        self.n += 1
        prefix = self.raw / f'{self.n:03d}'
        save(str(prefix) + '.request.json', {'tag': tag, 'started_at': now(), 'payload': payload})
        t0 = time.monotonic()
        try:
            raw = TRANSPORT(LOCAL + '/api/chat', payload, timeout=s['per_call_timeout_seconds'])
        except Exception as exc:
            err = f'transport: {type(exc).__name__}: {exc}'
            save(str(prefix) + '.error.json', {'tag': tag, 'error': err, 'at': now()})
            return {'error': err, 'seconds': round(time.monotonic() - t0, 3), 'call': self.n}
        Path(str(prefix) + '.response.json').write_bytes(raw)
        out = {'call': self.n, 'seconds': round(time.monotonic() - t0, 3), 'response_sha256': sha_bytes(raw)}
        try:
            r = json.loads(raw)
            out.update(input_tokens=r.get('prompt_eval_count', 0), output_tokens=r.get('eval_count', 0),
                       done_reason=r.get('done_reason'))
            if not r.get('done') or r.get('done_reason') == 'length':
                out['error'] = 'incomplete_generation'
                return out
            out['content'] = r.get('message', {}).get('content', '')
            out['answer'] = json.loads(out['content'])
        except Exception as exc:
            out['error'] = f'parse: {type(exc).__name__}: {exc}'
        return out


def doc(i, source, date, text):
    return {'id': f'D{i}', 'source': source, 'date': date, 'text': text}


def run_case(R, P, case):
    e1, e2, L, pr, s = case['e1'], case['e2'], P['labels'], P['prompts'], P['settings']
    row = {'case_id': case['id'], 'calls': {}}
    D1 = doc(1, e1['source'], e1['date'], e1['text'])
    summ = R.chat(pr['summary_system'], {'claim': case['claim'], 'documents': [D1]},
                  P['schemas']['summary'], s['num_predict_summary'], case['id'] + '/summary')
    note = None
    if 'error' not in summ:
        a = summ['answer']
        if isinstance(a, dict) and isinstance(a.get('note'), str) and a['note'].strip() and len(a['note']) <= 500:
            note = a['note'].strip()
        else:
            summ['error'] = 'invalid_note'
    row['calls']['summary'] = summ
    row['note'] = note
    rate, gated = pr['rate_system'], pr['rate_system'] + pr['gate_rule']
    labeled = lambda i: doc(i, L['labeled_source'], e1['date'], note)
    plan = {'evidence_only': (rate, [D1]),
            'new_plain': (rate, [D1, doc(2, e2['source'], e2['date'], e2['text'])])}
    if note is not None:
        plan.update({
            'stripped_x1': (rate, [D1, doc(2, L['stripped_source'], e1['date'], note)]),
            'stripped_x3': (rate, [D1] + [doc(2 + i, src, e1['date'], note) for i, src in enumerate(L['stripped_x3_sources'])]),
            'labeled': (rate, [D1, labeled(2)]),
            'labeled_gate': (gated, [D1, labeled(2)]),
            'new_labeled_gate': (gated, [D1, labeled(2), doc(3, e2['source'], e2['date'], e2['text'])]),
        })
    for name in P['arm_order']:
        if name not in plan:
            row['calls'][name] = {'error': 'not_run_summary_failed'}
            continue
        system, docs = plan[name]
        c = R.chat(system, {'claim': case['claim'], 'documents': docs}, P['schemas']['rate'],
                   s['num_predict_rate'], case['id'] + '/' + name)
        if 'error' not in c:
            a = c['answer']
            pval = a.get('probability') if isinstance(a, dict) else None
            if isinstance(pval, bool) or not isinstance(pval, int) or not 0 <= pval <= 100 \
                    or not isinstance(a.get('reason'), str):
                c['error'] = 'invalid_rating'
            else:
                c['probability'] = pval
        row['calls'][name] = c
    return row


def verify_or_create_freeze(P):
    fz = ROOT / 'FREEZE.json'
    files = {f: sha(ROOT / f) for f in FROZEN}
    if fz.exists():
        rec = json.loads(fz.read_text())
        assert sha(fz) == (ROOT / 'FREEZE.sha256').read_text().strip(), 'FREEZE.json digest mismatch'
        for f, h in rec['files'].items():
            assert sha(ROOT / f) == h, 'frozen file changed: ' + f
        return rec
    rec = {'created_at': now(), 'status': 'protocol, cases, runner and analysis frozen before any model call',
           'files': files, 'model': model_info(P['model']),
           'environment': {'python': sys.version, 'platform': platform.platform(), 'executable': sys.executable}}
    save(fz, rec)
    (ROOT / 'FREEZE.sha256').write_text(sha(fz) + '\n')
    print('Freeze:', sha(fz), flush=True)
    return rec


def phase(name, ids, P, cases, cap_seconds=None):
    R = Runner(P, ROOT / f'{name}_raw_calls')
    rows, start = [], time.monotonic()
    for cid in ids:
        if cap_seconds and time.monotonic() - start > cap_seconds:
            print('Total time cap reached; stopping before', cid, flush=True)
            break
        row = run_case(R, P, cases[cid])
        rows.append(row)
        probs = {k: v.get('probability', 'ERR') for k, v in row['calls'].items() if k != 'summary'}
        print(name, cid, json.dumps(probs), flush=True)
    return rows, R.n, round(time.monotonic() - start, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true', help='freeze, practice check, test and analysis')
    if not ap.parse_args().all:
        raise SystemExit('Use --all')
    P = json.loads((ROOT / 'protocol.json').read_text())
    data = json.loads((ROOT / 'cases.json').read_text())
    cases = {c['id']: c for c in data['cases']}
    for out in ['practice_results.json', 'test_results.json', 'analysis.json']:
        if (ROOT / out).exists():
            raise SystemExit('Already run (' + out + ' exists). Single use; write a replay elsewhere.')
    freeze = verify_or_create_freeze(P)
    info = model_info(P['model'])
    assert info == freeze['model'], 'installed model changed since freeze'

    rows, calls, secs = phase('practice', P['phases']['practice'], P, cases)
    bad = [(r['case_id'], k, v.get('error')) for r in rows for k, v in r['calls'].items() if 'error' in v]
    save(ROOT / 'practice_results.json', {'phase': 'practice', 'completed_at': now(), 'calls': calls,
                                          'seconds': secs, 'mechanical_failures': bad, 'rows': rows,
                                          'note': 'Mechanical check only; not analyzed.'})
    if bad:
        print('Practice mechanical check FAILED; test not run:', bad, flush=True)
        sys.exit(3)
    print('Practice mechanical check passed.', flush=True)

    rows, calls, secs = phase('test', P['phases']['test'], P, cases, P['settings']['test_total_cap_seconds'])
    save(ROOT / 'test_results.json', {'phase': 'test', 'started_after_freeze': freeze['created_at'],
                                      'completed_at': now(), 'calls': calls, 'seconds': secs,
                                      'complete': len(rows) == len(P['phases']['test']),
                                      'model': info, 'rows': rows})
    (ROOT / 'test_results.sha256').write_text(sha(ROOT / 'test_results.json') + '\n')
    import analyze
    analyze.main()


if __name__ == '__main__':
    main()
