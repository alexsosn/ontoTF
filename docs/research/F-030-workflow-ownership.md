# F-030 — workflow ownership / CI amplification research

**Parent:** #291 (P0), ADR-001; sibling #290 (data-first compiler).

## Source-backed amplification

- The checked-out `main` tree contained 82+ one-off `.github/workflows/*.yml` workflows, plus `full-suite.yml`. On generic loader PR #294, a single change to `src/tfont/**`, `tests/**` and `pyproject.toml` launched **24 workflows**. On the earlier four-mapping PR #289, it launched 26 workflows.
- Current `full-suite.yml` runs `python -m unittest discover -s tests -v` on Python 3.10 and 3.12. Many legacy workflows repeat subsets of exactly those unittest modules:
  - `i027c2-adj-adv.yml`: repeats `tests.i027c2.test_pos_red`, `test_pos_adversarial`, `test_original_sources`; additionally runs two deterministic `scripts/coverage/build_i027c2_*.py --check` commands **not covered by generic discovery**.
  - `f007-ci-full-suite-dedup.yml`: runs `tests.ci.test_full_suite_workflow_contract`; this is discovered by the full suite.
  - `i157-pep639-license.yml`: repeats package authority and license unit tests + `discover -s tests/i009`.
  - `i027d-current-coverage.yml`: repeats discovered unit tests but uniquely checks two frozen `build_i026_work_queue.py --check` and `build_i027d_current_queue.py --check` generated snapshots.
- **Danger of blanket deletion:** `r011-report-validation.yml` calls `python -m pytest -q tests/research/test_r011_measure.py` and a report-generation script. Those checks must be explicitly accounted for; simple unittest discovery may not cover pytest tests or generated-source checks. `r005-research-inventory.yml` checks out seven pinned upstream TF source datasets for the research inventory. `i027b3-extrabiblical-source.yml` separately checks out exact original compressed MQL and invokes `--verify-frozen`. Do not run expensive source checkouts on every ordinary mapping data edit; but do not delete source integrity gate when its pin changes.
- Legacy feature-specific paths trigger a cascade of per-ticket workflows whenever common core package code is touched, even if no corresponding feature contract changed.

## Classification required before mass migration

Complete a machine-generated inventory of every workflow (including paths, events, commands, `uses:` actions, exact test modules and any external source checkouts). Separate:
1. duplicate unit tests included in full suite;
2. deterministic offline source/coverage/parity generators using `--check`;
3. installation/wheel and licensing checks not implicit in editable-unit suite;
4. external pinned corpus/source/ontology reproducibility;
5. operational lint/governance checks (Node action versions, source-path/branch protection, codegen proof).

For each unique check, map to an owned replacement job and triggering change class; do not drop any unowned check. Pre-existing branch-protection required checks must be inventoried before deleting or renaming GitHub Actions workflow names.

## Target architecture

One `ci.yml` with stable names:
- `fast-contract`: Python 3.12 JSON schema/digest/decision ledger validation and deterministic changed snapshots; no network datasets.
- `source-pins`: only when source/ontology evidence pins or original inventories change; checks out exact pinned sources and validates expected Git blob/byte/semantic observations.
- `release-regression-py310` and `release-regression-py312`: exact-head full suite, plus unique pytest/governance checks, wheel/installed-source parity and packaging.
- `required-release-gate`: always evaluated on current head and requires positive completion of mandatory jobs and source-pins when applicable. Skipped source-pins are not treated as a positive endorsement of changed-source semantic claims.

A Python test-inventory/ownership validator checks every old unique `run` command has a concrete owner before retiring one-off workflows. An ordinary mapping batch must not add a new workflow file.

## Safety / non-goals

Never equate fewer workflows with fewer checks. Do not suppress Python 3.10 or 3.12 tests, alter test discovery order to dodge failures or drop historical artifact--check commands. Pinned original sources are not downloaded for ordinary mapping edits, only when upstream pin/evidence changes and for scheduled reproducibility audits. Full exact-head CI and independently posted logical adversarial review remain required before expected-head merge.

**Progress:** evidence sampling and implementation design; not yet a complete one-for-one accounting of all 82 workflow definitions. Do not claim CI consolidation is done.
