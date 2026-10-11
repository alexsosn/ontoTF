# F-030 / #291: POS-workflow consolidation pilot — research

**Issue:** #291
**Observed source:** `main` at `e7b4a7464b7f83b0733565101964981e413eaffa` (2026-10-11).

## Scope and evidence

The GitHub API lists 84 workflow YAML files in `.github/workflows`. `full-suite.yml` already runs unconditional `pull_request` regression on the exact head, Python 3.10 and 3.12, `unittest discover -s tests`, `pytest tests/research`, two frozen-coverage generators, wheel build and packaging checks. Seven prior POS/accounting workflows repeat those same Python test modules but add eight standalone reproducibility `--check` commands:

| Retire workflow | Additional frozen command(s) to preserve |
| --- | --- |
| i026-work-queue.yml | build_i026_work_queue.py (already in full-suite) |
| i027a-bhsa-stems.yml | build_i027a_bhsa_verbal_stems.py |
| i027b1-bhsa-verb.yml | build_i027b1_bhsa_verb.py |
| i027b2-syriac-verb.yml | build_i027b2_syriac_verb.py |
| i027b4-extrabiblical-verb.yml | build_i027b4_extrabiblical_verb.py |
| i027c2-adj-adv.yml | build_i027c2_bhsa_adj_adv.py, build_i027c2_syriac_adj_adv.py |
| i027d-current-coverage.yml | build_i027d_current_queue.py |

All commands read pinned local artifacts. Their `--check` validation remains meaningful even though the specific historical workflows are duplicated. `full-suite.yml` is already the release regression owner; relocate each unique check there rather than deleting it. Tests for each workflow are included in unconditional test discovery.

**Excluded intentionally:** `i027b3-extrabiblical-source.yml` checks out the original ETCBC source at a fixed SHA and compares original compressed MQL evidence; `i027c1-native-pos.yml` checks out three upstream repositories for exact pinned reconciliation. These are not equivalent to `unittest discover` or offline --check and remain active. The trusted `i033e3-protected-batch-review.yml` remains untouched.

## Alternatives and risks

- Delete all per-ticket workflows without an inventory: rejected (external-source and historical reproducibility gates are distinct).
- Add another path-filtered, skip-able PR workflow: rejected (would preserve duplicated jobs and risk bypassing a required check).
- Keep all eight builders as separate two-version jobs: rejected (duplicate dependency setup; no new evidence of coverage).
- Run the eight offline checks in each full-suite version: selected for this bounded pilot. Slightly longer shared regression jobs, but fewer workflow starts and explicit checks on every PR head, even for changes that historical paths excluded.

No corpus or ontology semantics, source pins, licenses or published artifacts are changed. Actual runner-minute savings cannot be inferred from static YAML: measure the PR and a comparable previous POS PR once Actions data is available.
