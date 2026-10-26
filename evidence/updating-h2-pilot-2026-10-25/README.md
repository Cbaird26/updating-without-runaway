# H2 pilot: does Zora's local model get more confident from re-reading its own notes?

Run on October 25, 2026 (evening, America/New_York) on Christopher Michael Baird's Mac, with the local Ollama model `zora:fast` (8.9B, Ministral-based; digest recorded in `FREEZE.json`). This tests hypothesis H2 of *Updating Without Runaway*. Claude (Anthropic) designed, ran and analyzed it; a separate Claude subagent wrote the fictional cases without seeing the prompts or analysis plan.

## Result

**Pre-set verdict:** no reliable self-confirmation, so H2 is untestable here (`analysis.json`). Showing the model its own note as an ordinary "briefing note" changed its stated probability by +4.7 points on average (95% interval -4.7 to +16.9; 4 up, 5 down, 7 unchanged). Repeating the note three times added nothing. Labeling the note and adding a prompt-level gate produced no measurable reduction. The gate did not block legitimate updates: an independent second document raised the probability by +15.9 points without the gate and +21.9 with it.

**Exploratory, not pre-specified** (`audit_and_exploratory.json`): re-reading its own note moved the answer erratically, in both directions.
- With the stripped note, answers changed in 9 of 16 cases, by 12.2 points on average, and once from 20 to 95.
- The gate instruction made answers less stable: they changed in 12 of 16 cases, by 18.4 points on average.
- In 3 cases the supporting second document lowered the probability; 2 of those 3 claims were negatively worded.

**Limits:**
- One small model, 16 AI-authored fictional cases and single deterministic runs.
- Stated rather than calibrated probabilities.
- 7 of 16 baselines were 85 or higher, which leaves little room to observe inflation.
- No physical evidence; this is not an estimate for other models, people or deployed systems.

## Files

- `PROTOCOL.md`, `protocol.json`: design, prompts, settings and decision rules, frozen first.
- `cases.json`: 3 practice and 16 test cases.
- `h2_pilot.py`, `analyze.py`: the runner and the pre-specified analysis.
- `FREEZE.json`, `FREEZE.sha256`: file hashes and the model digest, written before any model call.
- Practice records: `practice_results.json` and `practice_raw_calls/` (mechanical check only).
- Test records: `test_results.json`, `test_results.sha256` and `test_raw_calls/`, with every request and response.
- Outputs: `analysis.json` holds the pre-specified results; `audit_and_exploratory.json` holds the 522-check audit of the saved run and the post hoc statistics.
- `run.log`: console output.

To replay, copy the folder elsewhere, delete the result files, and run `python3 -B h2_pilot.py --all` with the same model installed. A replay is not a fresh test, because the cases are now exposed.

## Replication

The identical pilot was repeated on `gemma4:12b-it-qat`; see `../updating-h2-gemma-replication-2026-10-25/README.md`.
