# F-030 / #291 — phase 1: completeness before workflow pruning

**Issue:** #291

## Evidence from repository and exact-head run

- 83 workflow YAML files in `.github/workflows` at the current `main`.
- PR #294 (generic loader) required **24 independently queued workflow runs** and repeated package installs. All eventually passed, but the full Python 3.10/3.12 suite was only one of those workflows.
- Prior to #294, `tests/i033a/test_batch_compiler_pilot.py` lacked an `__init__.py` in its containing directory. Standard `python -m unittest discover -s tests -v` therefore did not import the 30-decision parity tests; they were only covered after PR #294 fixed package discovery.
- Seven **other** existing directories with `test_*.py` lack package markers: `architecture`, `f008`, `i003`, `i011`, `i013`, `plans`, and `research`. Tests must not disappear when old focused workflows are disabled.

## Scope and negative cases

1. An always-discovered contract asserts that **every** Python test directory under `tests/` is importable. This closes a class of silent skip regressions; it does not just assert one expected test count.
2. Put package markers in the seven historical directories and execute the newly discovered tests on both supported Python versions. Fix real failures rather than disabling new discovery.
3. Only prune `src/tfont/**` from **legacy, redundant unittest-focused** pull-request filters: I-001, I-002, I-003, I-004, I-005, I-006, I-015 and F-002. Those workflows remain runnable when their own tests, workflow files or research/documentation/packaging contracts change. Every `src/**` change still triggers the exact-head full suite.
4. Fold wheel-build verification into the full repository suite on both Python 3.10/3.12, so pruning F-002's broad source trigger does not remove wheel packaging from the final-head gate. Existing F-002 focused workflow still runs if packaging files change.
5. Do not migrate workflows with unique original-source checkout, TF network tests, external runtime pinning, or standalone `--check` artifact generators until equivalent checks are explicitly included elsewhere. Do not remove historical workflow YAML files in phase 1.

## Acceptance/metrics

- New full suite discovers all test packages, including previously excluded historical suites.
- Full wheel build completes in each matrix environment.
- A PR changing only `src/tfont/release_registry.py` should no longer start redundant I-001/I-002/I-003/I-004/I-005/I-006/I-015/F-002 workflows; the full suite still runs.
- No changed topic-specific test path loses its focused workflow trigger.
- This is an incremental migration toward the single stable final-head gate described by #291, not a claim that all 83 files are consolidated.

## Risk

Tests that were previously hidden may now legitimately fail. The PR remains unmergeable until all regressions pass; do not suppress failures or exclude the added test packages to make CI green.

## Exact-head CI RED evidence: pytest research modules

Once all seven missing package markers were installed, the *actual* Python 3.10 full suite discovered **1,264 unittest cases**, but failed importing eight previously invisible `tests/research/test_*.py` modules that depend on `pytest`. This is not a reason to hide them again. They are pytest-function tests, so importing under `unittest` is insufficient for coverage even if import succeeds. Install pytest in the canonical full-suite environment and execute `python -m pytest tests/research -q` as a second, named full-suite step on both Python versions. The existing single `python -m unittest discover -s tests -v` owner remains unique, and existing exact-head wheel-build verification remains. Review actual pytest failures rather than suppressing or marking skipped tests.
