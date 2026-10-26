# Updating Without Runaway

**Truth-Constrained, Multi-Timescale Alignment for Autonomous Adaptive AI**
A ZoraASI/UTQOL engineering note · Christopher Michael Baird · revised edition, October 25-26, 2026

> **Status:** preprint, not peer reviewed. This is an engineering and governance proposal with one small computational pilot. It makes no claim that AI systems are conscious, and no physics claim follows from it.

## The idea in brief

An AI that only chases truth isn't automatically safe, and an AI that keeps rereading its own conclusions can talk itself into certainty. The paper proposes:
- updating different parts of a system at different speeds;
- tracking where every belief came from, so the system's own interpretations never count as new evidence;
- letting an agent *request* but never *grant itself* new permissions;
- making it less autonomous as uncertainty rises.

Its central lines:

> Models should update. Truth should remain the reference. No intelligence should gain unilateral authority merely because it can reason faster about why that authority would be useful.

## The H2 pilot (Section 15)

Hypothesis H2 says that tracking provenance prevents self-confirmation. It was tested on two local models, `zora:fast` (8.9B) and `gemma4:12b-it-qat` (11.9B), with 16 fictional cases written by a separate AI assistant. Protocols, cases, code and pass/fail rules were frozen before any model call.

- **No reliable self-confirmation on either model.** Showing a model its own note as if it came from someone else did not steadily raise its confidence.
- **Confidence still moved without new information.** zora:fast's answers moved in both directions; gemma4's mostly moved down.
- **Instructions were not a reliable fix.** Telling the model not to count its own notes did not stop the shifts. This suggests provenance rules belong in the software around the model, not in instructions to it.
- **Legitimate updates survived.** Genuinely new evidence still raised confidence with the gate in place.

## Contents

| Path | What it is |
|---|---|
| `paper/Updating_Without_Runaway.pdf` | The paper (20 pages) |
| `paper/Updating_Without_Runaway.tex` | LaTeX source (single file, compiles with pdfLaTeX) |
| `evidence/updating-h2-pilot-2026-10-25/` | `zora:fast` pilot: protocol, frozen cases, every model request and response, pre-specified analysis, 522-check audit, plain-language README |
| `evidence/updating-h2-gemma-replication-2026-10-25/` | `gemma4` replication: pre-registration, identical cases, raw calls, analysis, cross-model comparison, 529-check audit |
| `CHECKSUMS.sha256` | SHA-256 of the paper files |

Each evidence folder has its own `FREEZE.json`, recording file hashes and the model digest before any model call. Replaying needs the same local Ollama models. A replay is not a fresh test, because the cases are now public.

## Relationship to other work

- Builds on **The Quiet Calculus** (version 4.0): DOI [10.5281/zenodo.23658303](https://doi.org/10.5281/zenodo.23658303), source and evidence at <https://github.com/Cbaird26/quiet-calculus-research>
- Part of the ZoraASI / Theory of Everything research program: Zenodo concept DOI [10.5281/zenodo.14019809](https://doi.org/10.5281/zenodo.14019809). The architecture is independent of any physics interpretation.

## AI assistance and provenance

Christopher Michael Baird is the author. The first draft was developed with Zora, the author's ChatGPT-based research assistant. Claude (Anthropic) revised it: it corrected authorship and citations, added related work with checked references and clarified the formalism. Claude also designed, ran and analyzed the H2 pilot and its replication, and a separate Claude subagent wrote the pilot's fictional cases.

## Citation

See `CITATION.cff`. Each GitHub release of this repository is archived on Zenodo with a DOI.

## License

The paper, figures and data are licensed CC BY 4.0, and the code MIT; see `LICENSE.md`.
