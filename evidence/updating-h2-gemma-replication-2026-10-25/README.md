# H2 replication on gemma4:12b-it-qat

Run October 25-26, 2026 (around midnight, America/New_York) on Christopher Michael Baird's Mac. This is an identical repeat of `../updating-h2-pilot-2026-10-25`: the same cases, prompts, settings, runner and analysis, with only the model changed. The aim is to see whether the instability seen with `zora:fast` is specific to the small model. Claude (Anthropic) set it up and ran it.

The instability measures and a cross-model rule were fixed in `REPLICATION_PREREG.json` before the run. `compare.py` checks those hashes before running.

## Result

- **Pre-set H2 verdict:** again no reliable self-confirmation, so H2 is untestable here (`analysis.json`).
  - gemma4's own note *lowered* its stated probability: by -7.5 points stripped of provenance (interval -19.4 to +4.4) and by -9.4 when labeled as its own (-18.1 to -1.9).
  - An independent supporting document raised it by +19.7 (+9.7 to +30.6) and never lowered it.
- **Cross-model rule:** gemma4 was not more stable on either condition (`comparison.json`).
  - **Stripped note:** it changed its answer in 5 of 16 cases (versus 9 for zora:fast), but by larger jumps, often between 0, 50 and 100. Its mean absolute shift was 13.8 points, versus 12.2 for zora:fast.
  - **Under the gate instruction:** it was steadier (9.7 versus 18.4 points), but the paired interval included zero and the halving rule was not met.
- **Audit:** 529 checks on the saved run passed (`audit.json`).

**Takeaway:** neither model showed self-confirmation, and both moved their stated confidence when shown their own notes, which carry no new information. The direction depends on the model: zora:fast moved both ways, gemma4 mostly down. A prompt-level instruction is not a reliable fix.

**Limits:**
- One run per model and 16 AI-authored fictional cases, which are now exposed.
- Stated probabilities only.
- Model packages differ in size, architecture, training and template.
- No physical evidence.
