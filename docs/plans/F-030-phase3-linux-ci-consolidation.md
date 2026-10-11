# F-030 phase 3 — research → plan → TDD → CI → skeptical review

**Issue:** #336. **Research:** `docs/research/F-030-phase3-linux-ci-consolidation.md`.

1. RED: add `tests/ci/test_ci_consolidation_f_core_phase3.py` before editing workflows. Require six redundant Linux-only focused workflows to be absent, their per-ticket test suites and packaging schema authority test present, an unconditional `python scripts/check_f_series_ownership.py .` command in `full-suite.yml`, and cross-version original exact-head full unittest/pytest/wheel checks still present.
2. Audit negative test for loss of unique conditions: retain Windows-specific `f014/f018/f019/f020` (Windows + Ubuntu matrix); pinned TF source checkout workflows, i008 real TF integration, separate protected token-based batch reviewer, and no `continue-on-error` or `if` on required shared ownership gate.
3. GREEN: delete only six workflows and add one direct ownership step to unconditional full-suite; do not change any test implementation or production Python modules.
4. CI: exact PR head Python 3.10/3.12 full suite, executed original ownership checker, wheel build and schema packaging all green. Validate all surviving workflow-contract tests.
5. Independent adversarial review must compare removed workflow commands, test packages, platform matrices and trusted review permissions; note Windows-specific exception and published-source evidence separately.
6. Expected-head squash merge and update #336/#291. No new per-issue workflow.
