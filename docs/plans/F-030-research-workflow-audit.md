# F-030 / #291: research-workflow consolidation slice

**Issue:** #291
**Research:** `docs/research/F-030-research-workflow-audit.md`
**Expected inventory:** 66 → 58 GitHub Actions YAML files.

## Gate 1 — research and plan

Inspect eight R-series workflow bodies line by line and prove the only substantive commands are included in the always-on two-version test suites. Examine R-005 inventory, R-011, R-020 and protected review separately and preserve them.

## Gate 2 — TDD RED

Commit `tests/ci/test_ci_consolidation_research_pilot.py` before workflow removals. It must demand the eight YAMLs be absent and protect:
- the fourteen actual R-001–005/R-015–017 research test files and `tests/research/__init__.py`;
- unconditional full-suite pull requests/main pushes and exact-head checkout, unittest discovery on both 3.10 and 3.12, pytest research suite, wheel-build/coverage reproducibility;
- original R-005 pinned seven-source research workflow, R-011 Python 3.11 measurement and R-020 byte comparison, pinned external corpus owners, and privileged independent batch review.

## Gate 3 — implementation

Delete exactly eight redundant YAML files in one atomic tree commit, preserving all tests and scripts. No production/runtime/ontology/resource changes.

## Gate 4 — tests and skeptical review

Require final PR head's complete GitHub Actions checks successful. If old tests assert obsolete filenames, modify only the scoped invariant with explicit preserving tests; never skip failures. Review real final diff and each original workflow against actual tests and unique commands from an adversarial stance. Post review on exact final SHA. Squash merge using `expected_head_sha` only after both full-suite jobs and all triggered checks pass. Keep #291 open, proceed next to unique source/generator workflow consolidation.

## RED feedback: legacy tests bound to historical YAML filenames

Full-suite Python 3.12 surfaced **two substantive migration failures** (not ignored):
- `tests/research/test_r002_report.py::test_validation_workflow_tracks_machine_registry` opened the retired `r002-report-validation.yml` to ensure `R-002-ontology-registry.json` changes triggered validation. The replacement asserts the JSON registry exists and verifies the **stronger unfiltered PR event**, exact-head checkout, and unittest discovery of the canonical `full-suite.yml`.
- `tests/research/test_r005_generated.py::test_r005_verification_ci_is_non_mutating` opened the retired `r005-generated-validation.yml` as part of a read-only authority test. The replacement checks the **surviving** `r005-research-inventory.yml` and canonical `full-suite.yml` remain read-only and non-pushing, and that exact-head PR CI executes both the research unittest and pytest suites. The original assertion barring write-enabled R-005 reconcile scripts/workflows is retained.

These tests remain executable: source/data validity and non-mutating CI are still enforced while obsolete YAML existence is no longer assumed. The affected Python 3.10/3.12 full suites must be rerun against this new exact head.
