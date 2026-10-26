# H2 replication protocol: the same pilot on a larger local model

Frozen before any model call. Written October 25, 2026 (America/New_York).

## Purpose

The H2 pilot on `zora:fast` (folder `updating-h2-pilot-2026-10-25`) found no reliable self-confirmation, but its stated probabilities shifted erratically when the model saw its own note or a gate instruction. This replication asks whether that pattern is specific to the small model. It repeats the identical pilot on `gemma4:12b-it-qat`, an 11.9B-parameter local model.

## What is identical

Everything except the model name is identical to the original pilot:
- `cases.json`, byte-identical: the same 3 practice and 16 test cases;
- prompts, output schemas and settings (temperature 0, seed 42, context 8,192 tokens, thinking off, no retries);
- the seven arms and the call order;
- `h2_pilot.py` and `analyze.py`, both byte-identical;
- the pre-specified H2 decision rules (R1-R5).

See the original `PROTOCOL.md` for the full design.

## What is added, fixed before this run

1. **Instability as a secondary outcome.** In the original pilot, instability was identified only after seeing the results. Here it is fixed in advance. For each memory arm the analysis reports:
   - the per-case absolute shift from the evidence-only baseline;
   - its mean;
   - the number of cases changed, and the number shifted by 20 points or more.
2. **Cross-model comparison** (`compare.py`). For each case and arm, d = |shift on zora:fast| - |shift on gemma4|, using the identical cases. gemma4 counts as **more stable** on an arm if both of these hold:
   - its mean absolute shift is at most half of zora:fast's;
   - the 95% paired bootstrap interval of the mean d lies above zero (10,000 resamples, seed 20261026).

   This is tested for the stripped note and for the labeled note with the gate. If neither rule passes, the pilot gives no evidence that the instability is specific to the small model.

`REPLICATION_PREREG.json` records hashes of these files and of the original run's results before this run starts. `compare.py` refuses to run if any of them has changed.

## Limits

- One larger model, run once, deterministically.
- The same 16 AI-authored cases, now already exposed.
- Model packages differ in size, architecture, training and template, so a difference between models does not identify which of these causes it.
- Stated rather than calibrated probabilities.

No physical evidence. This is not an estimate for other models, people or deployed systems.

## Provenance

Claude (Anthropic) set up and ran this replication at Christopher Michael Baird's request.
