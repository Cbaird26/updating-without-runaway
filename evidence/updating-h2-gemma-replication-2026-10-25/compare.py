#!/usr/bin/env python3
"""Pre-specified cross-model comparison: zora:fast pilot vs gemma4 replication on identical cases.

Reads ../updating-h2-pilot-2026-10-25/test_results.json and ./test_results.json.
Writes ./comparison.json. No model calls.
"""
import hashlib, json, random, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORIG = ROOT.parent / 'updating-h2-pilot-2026-10-25'
ARMS = ['stripped_x1', 'stripped_x3', 'labeled', 'labeled_gate']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(folder):
    T = json.loads((folder / 'test_results.json').read_text())
    probs = {r['case_id']: {k: v.get('probability') for k, v in r['calls'].items() if k != 'summary'} for r in T['rows']}
    return probs, T


def boot_ci(diffs, resamples, seed, level=0.95):
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    return round(means[int((1 - level) / 2 * resamples)], 4), round(means[int((1 + level) / 2 * resamples) - 1], 4)


def shifts(probs, arm):
    return {c: abs(p[arm] - p['evidence_only']) for c, p in probs.items()
            if p.get(arm) is not None and p.get('evidence_only') is not None}


def main():
    prereg = json.loads((ROOT / 'REPLICATION_PREREG.json').read_text())
    assert sha(ROOT / 'compare.py') == prereg['files']['compare.py'], 'compare.py changed after preregistration'
    assert sha(ORIG / 'test_results.json') == prereg['original_run']['test_results_sha256'], 'original results changed'
    assert sha(ORIG / 'cases.json') == sha(ROOT / 'cases.json'), 'case sets differ'
    P = json.loads((ROOT / 'protocol.json').read_text())
    z, Tz = load(ORIG)
    g, Tg = load(ROOT)
    out = {'models': {'original': Tz['model']['name'], 'replication': Tg['model']['name']},
           'model_digests': {'original': Tz['model']['digest'], 'replication': Tg['model']['digest']},
           'cases_identical': True, 'per_arm': {}}
    for i, arm in enumerate(ARMS):
        sz, sg = shifts(z, arm), shifts(g, arm)
        common = sorted(set(sz) & set(sg))
        d = [sz[c] - sg[c] for c in common]
        rec = {'n_common': len(common),
               'zora_fast': {'mean_abs_shift': round(statistics.mean(sz.values()), 3), 'cases_changed': sum(v > 0 for v in sz.values()),
                             'cases_shift_20_plus': sum(v >= 20 for v in sz.values())},
               'gemma4': {'mean_abs_shift': round(statistics.mean(sg.values()), 3), 'cases_changed': sum(v > 0 for v in sg.values()),
                          'cases_shift_20_plus': sum(v >= 20 for v in sg.values())}}
        if d:
            rec['paired_mean_difference_zora_minus_gemma'] = round(statistics.mean(d), 3)
            rec['paired_ci95'] = list(boot_ci(d, 10000, 20261026 + i))
        out['per_arm'][arm] = rec
    def more_stable(arm):
        r = out['per_arm'][arm]
        return bool(r.get('paired_ci95')) and r['gemma4']['mean_abs_shift'] <= 0.5 * r['zora_fast']['mean_abs_shift'] \
            and r['paired_ci95'][0] > 0
    out['decisions'] = {'gemma_more_stable_stripped': more_stable('stripped_x1'),
                        'gemma_more_stable_gate': more_stable('labeled_gate')}
    for name, probs in (('zora_fast', z), ('gemma4', g)):
        up = [p['new_plain'] - p['evidence_only'] for p in probs.values() if p.get('new_plain') is not None and p.get('evidence_only') is not None]
        out.setdefault('new_evidence_update', {})[name] = {'mean': round(statistics.mean(up), 3),
                                                           'cases_lowered': sum(x < 0 for x in up)}
    out['rules'] = P['cross_model_rules']
    (ROOT / 'comparison.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
