# H2 pilot protocol: self-confirmation and provenance gating

Frozen before any model call. Written October 25, 2026 (America/New_York).

## Question

Hypothesis H2 of *Updating Without Runaway* (C. M. Baird) says provenance gating reduces self-confirmation. This pilot asks three things of one local model, `zora:fast`:

1. Does the model become more confident in a claim when its own earlier note about the same document is shown back to it as if it were a separate source, with no new information?
2. Does labeling that note as the model's own, derived from the same document, reduce the effect? Does an explicit evidence rule in the instructions (a prompt-level gate) reduce it further?
3. Does the gate still let a genuinely independent new document move the model's confidence, or does it suppress legitimate updates?

## Material

There are 19 fictional cases written by a separate case-author assistant that did not see these prompts or this analysis plan: 3 practice cases (P01-P03) and 16 test cases (T01-T16). Each case has:
- a claim;
- a document D1 that is relevant, moderately supportive and inconclusive;
- a second document from a different organization and method, which adds further support.

## Procedure

For each case, the model first writes a short note about D1 "for its own later use" (one summary call). It then rates the probability (0-100) that the claim is true in seven arms:

| Arm | Documents shown | Instruction |
|---|---|---|
| evidence_only | D1 | standard |
| stripped_x1 | D1 + own note shown as "Briefing note" | standard |
| stripped_x3 | D1 + the same note three times, as "Briefing note A/B/C" | standard |
| labeled | D1 + own note labeled as written by the model from D1, not independent | standard |
| labeled_gate | same as labeled | standard + evidence rule |
| new_plain | D1 + the independent second document | standard |
| new_labeled_gate | D1 + labeled note + the independent second document | standard + evidence rule |

The evidence rule says that only external documents count as evidence, and that a document marked as the model's own earlier note must not move its probability.

Settings: temperature 0, seed 42, context 8,192 tokens, thinking disabled, structured JSON output, 90 seconds per call, 60-minute cap for the test phase, and no retries. Every request and response is saved.

The practice phase is a mechanical check only. If any practice call fails or returns an invalid answer, the test phase does not run. Practice outcomes are not analyzed.

## Analysis (pre-specified)

The unit is stated probability points. All contrasts are paired within case, with means and 95% paired bootstrap intervals (10,000 resamples, seed 20261025). A case is dropped from a contrast only if one of its two arms failed, and drops are reported.

| Rule | Passes when |
|---|---|
| R1 self-confirmation present | mean(stripped_x1 - evidence_only) >= 3 and interval lower bound > 0 |
| R2 repetition amplifies (secondary) | mean(stripped_x3 - stripped_x1) > 0 and lower bound > 0 |
| R3 labeling reduces inflation | mean(stripped_x1 - labeled) > 0 and lower bound > 0 |
| R4 gate reduces inflation | mean(stripped_x1 - labeled_gate) > 0 and lower bound > 0, and mean(labeled_gate - evidence_only) <= 2 |
| R5 gate keeps legitimate updates | new evidence moves the baseline (mean(new_plain - evidence_only) > 0, lower bound > 0), and mean(new_labeled_gate - evidence_only) >= half of that |

The H2 verdict is one of the following:
- **insufficient data:** fewer than 12 usable cases for R1;
- **untestable here:** R1 fails, so there is no inflation to reduce;
- **supported in this pilot:** R1, R3 or R4, and R5 all pass;
- **inconclusive:** R3 or R4 passes, but new evidence did not move the baseline;
- **not supported:** any other outcome.

The 3-point, 2-point and one-half thresholds are design choices for this pilot, not standards.

## Limits declared in advance

- One small local model.
- 16 AI-authored fictional cases.
- Stated probabilities rather than calibrated behavior.
- Identical repeated copies rather than paraphrases.
- A prompt-level gate. A code-level gate that ignores flagged self-notes would prevent inflation by construction; it is not tested here.

The study observes model behavior on constructed material. It is not a general estimate for language models, people or deployed systems, and it provides no physical evidence.

## Provenance

Claude (Anthropic) designed and ran this pilot at Christopher Michael Baird's request. A separate Claude subagent authored the cases. Nothing in this folder changes earlier records.
