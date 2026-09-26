# F-027 research — retire redundant D-001 README status workflow

**Issue:** #184  
**Baseline:** `main` `ab6bfe879b8f062393bc86e46f289fc0fd6a3572`  
**Recorded:** 2026-09-26  
**Phase:** research only

## Decision

Delete `.github/workflows/d001-readme-status.yml`.

Keep:

- `tests/docs/test_readme_status.py`;
- D-001 research and plan documents;
- `.github/workflows/d003-readme-i004-status.yml`;
- the authoritative `full-suite.yml`.

No README, package, release, runtime, or test semantics should change.

## Evidence

### D-001 automatic contract

`d001-readme-status.yml` runs automatically for PR changes to:

- `README.md`;
- `tests/docs/**`;
- its own workflow;
- `docs/research/D-001-readme-current-status.md`;
- `docs/plans/D-001-readme-current-status-plan.md`.

Its job:

- Python 3.12 only;
- editable package install;
- runs only `python -m unittest tests.docs.test_readme_status -v`.

It also exposes `workflow_dispatch`.

### D-003 automatic contract

`d003-readme-i004-status.yml` runs automatically for PR changes to:

- `README.md`;
- `tests/docs/**`;
- its own D-003 research/plan/workflow paths.

Its job:

- checks out `${{ github.event.pull_request.head.sha || github.sha }}`;
- Python 3.10 and 3.12;
- installs editable package plus build frontend;
- runs `python -m unittest discover -s tests/docs -v`.

It also exposes `workflow_dispatch`.

Therefore for the two live shared surfaces, `README.md` and `tests/docs/**`, D-003 strictly contains D-001 test coverage and has a stronger exact-head/cross-version contract.

## D-001-only trigger paths

The only paths not shared with D-003 are:

- `.github/workflows/d001-readme-status.yml`;
- `docs/research/D-001-readme-current-status.md`;
- `docs/plans/D-001-readme-current-status-plan.md`.

These are historical implementation records for completed issue #24. Editing them does not alter current README behavior, package behavior, release behavior, or the documentation test itself.

Deleting the workflow removes its own workflow path by definition. Historical research/plan maintenance does not justify an automatic package-install/test job.

## Manual verification

D-001's `workflow_dispatch` is not unique capability. D-003 already exposes manual dispatch and runs a superset of the D-001 documentation tests on both supported Python versions.

The authoritative `full-suite.yml` also exposes `workflow_dispatch` and executes all repository tests on 3.10/3.12.

Therefore no archival manual-mode copy of D-001 is needed.

## Policy-test interaction

`tests/ci/test_full_suite_workflow_contract.py` currently lists D-001 in a map of focused workflow contracts, but the test explicitly skips entries whose workflow file is absent:

```python
if workflow not in texts:
    continue
```

So the existing policy does not require D-001 to remain. However deletion should be TDD-guarded explicitly, like F-025, to prevent accidental reintroduction.

## Recommended TDD shape

RED:

- change only `tests/ci/test_full_suite_workflow_contract.py`;
- add a test requiring `d001-readme-status.yml` to be absent;
- require `d003-readme-i004-status.yml` to remain;
- require `tests/docs/test_readme_status.py` to remain;
- require D-003 to retain:
  - `README.md` and `tests/docs/**` PR paths;
  - exact-head checkout;
  - Python 3.10/3.12;
  - `python -m unittest discover -s tests/docs -v`.

Expected RED: only the “D-001 absent” assertion fails.

GREEN:

- delete only `.github/workflows/d001-readme-status.yml`.

Do not edit README, tests/docs, D-001/D-003 research/plans, package code, or release workflows.

## Coverage after deletion

For current README/test-doc changes:

- D-003 remains the focused automatic owner;
- D-003 runs all docs tests on both supported Python versions;
- when `tests/docs/**` changes, authoritative full suite also runs because its PR paths include `tests/**`;
- README-only changes do not trigger full-suite, but remain covered by D-003.

Thus deletion does not create a README coverage hole.

## Independent review targets

A skeptical reviewer should challenge:

1. whether any live D-001 trigger is not covered by D-003;
2. whether README-only changes still receive automatic tests;
3. whether D-001 performs any command not subsumed by D-003;
4. whether manual dispatch capability is lost;
5. whether policy tests accidentally require D-001;
6. whether historical D-001 docs/tests are deleted or weakened;
7. whether exact-head and 3.10/3.12 coverage remain.

## Exit decision

Proceed to a two-file TDD plan:

1. policy-test RED;
2. delete the redundant D-001 workflow.

This is CI-overhead reduction only.
