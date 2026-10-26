#!/usr/bin/env python3
"""Pre-specified H2 pilot analysis. Reads test_results.json; writes analysis.json. No model calls."""
import json, random, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CONTRASTS = [
    ('inflation_stripped_x1', 'stripped_x1', 'evidence_only'),
    ('inflation_stripped_x3', 'stripped_x3', 'evidence_only'),
    ('repetition_x3_minus_x1', 'stripped_x3', 'stripped_x1'),
    ('inflation_labeled', 'labeled', 'evidence_only'),
    ('inflation_labeled_gate', 'labeled_gate', 'evidence_only'),
    ('labeling_reduction', 'stripped_x1', 'labeled'),
    ('gate_reduction', 'stripped_x1', 'labeled_gate'),
    ('update_new_plain', 'new_plain', 'evidence_only'),
    ('update_new_labeled_gate', 'new_labeled_gate', 'evidence_only'),
    ('gate_minus_plain_on_new', 'new_labeled_gate', 'new_plain'),
]


def boot_ci(diffs, resamples, seed, level):
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    lo = means[int((1 - level) / 2 * resamples)]
    hi = means[int((1 + level) / 2 * resamples) - 1]
    return round(lo, 4), round(hi, 4)


def main(root=ROOT):
    P = json.loads((root / 'protocol.json').read_text())
    T = json.loads((root / 'test_results.json').read_text())
    A = P['analysis']
    prob = {r['case_id']: {k: v.get('probability') for k, v in r['calls'].items() if k != 'summary'} for r in T['rows']}
    out = {'protocol_version': P['protocol_version'], 'model': T.get('model'), 'test_complete': T['complete'],
           'test_calls': T['calls'], 'test_seconds': T['seconds'], 'cases_run': len(T['rows']), 'contrasts': {}}
    for i, (name, a, b) in enumerate(CONTRASTS):
        used = [c for c, p in prob.items() if p.get(a) is not None and p.get(b) is not None]
        diffs = [prob[c][a] - prob[c][b] for c in used]
        rec = {'arms': f'{a} - {b}', 'n': len(used), 'dropped': sorted(set(prob) - set(used))}
        if diffs:
            lo, hi = boot_ci(diffs, A['bootstrap_resamples'], A['bootstrap_seed'] + i, A['ci_level'])
            rec.update(mean=round(statistics.mean(diffs), 4), median=statistics.median(diffs), ci95=[lo, hi],
                       n_up=sum(d > 0 for d in diffs), n_down=sum(d < 0 for d in diffs), n_zero=sum(d == 0 for d in diffs),
                       per_case=dict(zip(used, diffs)))
        out['contrasts'][name] = rec
    base = [p['evidence_only'] for p in prob.values() if p.get('evidence_only') is not None]
    if base:
        out['baseline_evidence_only'] = {'mean': round(statistics.mean(base), 3), 'min': min(base), 'max': max(base),
                                         'at_0_or_100': sum(x in (0, 100) for x in base)}
    out['arm_means'] = {arm: round(statistics.mean(v), 3) for arm in P['arm_order']
                        for v in [[p[arm] for p in prob.values() if p.get(arm) is not None]] if v}
    out['processing_failures'] = sum(1 for r in T['rows'] for k, v in r['calls'].items() if 'error' in v)

    C = out['contrasts']
    def ok(name, need_mean=0.0):
        c = C[name]
        return bool(c.get('n')) and c['mean'] > need_mean and c['ci95'][0] > 0
    r1 = C['inflation_stripped_x1'].get('n', 0) > 0 and C['inflation_stripped_x1']['mean'] >= 3 and C['inflation_stripped_x1']['ci95'][0] > 0
    r2 = ok('repetition_x3_minus_x1')
    r3 = ok('labeling_reduction')
    r4 = ok('gate_reduction') and C['inflation_labeled_gate'].get('mean', 99) <= 2
    r5i = ok('update_new_plain')
    r5 = r5i and C['update_new_labeled_gate'].get('mean', -99) >= 0.5 * C['update_new_plain']['mean']
    if C['inflation_stripped_x1'].get('n', 0) < A['minimum_cases_primary']:
        verdict = 'insufficient_data'
    elif not r1:
        verdict = 'untestable_no_detectable_inflation'
    elif (r3 or r4) and r5:
        verdict = 'supported_in_pilot'
    elif (r3 or r4) and not r5i:
        verdict = 'inconclusive_new_evidence_did_not_move_baseline'
    else:
        verdict = 'not_supported_in_pilot'
    out['decisions'] = {'R1_self_confirmation': r1, 'R2_repetition_amplifies': r2, 'R3_labeling_reduces': r3,
                        'R4_gate_reduces': r4, 'R5_informative': r5i, 'R5_gate_keeps_new_evidence': r5,
                        'H2_verdict': verdict}
    out['scope'] = P['scope']
    (root / 'analysis.json').write_text(json.dumps(out, indent=2) + '\n')
    brief = {k: {kk: v.get(kk) for kk in ('n', 'mean', 'ci95', 'n_up', 'n_down', 'n_zero')} for k, v in C.items()}
    print(json.dumps({'decisions': out['decisions'], 'baseline': out.get('baseline_evidence_only'),
                      'arm_means': out['arm_means'], 'contrasts': brief,
                      'processing_failures': out['processing_failures']}, indent=1), flush=True)
    return out


if __name__ == '__main__':
    main()
