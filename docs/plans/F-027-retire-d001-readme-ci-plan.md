# F-027 plan — retire redundant D-001 README status workflow

**Issue:** #184  
**Research:** `docs/research/F-027-retire-d001-readme-ci.md`  
**Research merge:** `e203811a866cc0f05275bdc63d4b5f533145e935`  
**Phase:** plan only

## Scope

Exactly two implementation files:

1. `tests/ci/test_full_suite_workflow_contract.py`;
2. delete `.github/workflows/d001-readme-status.yml`.

Preserve unchanged:

- `README.md`;
- `tests/docs/test_readme_status.py`;
- all other `tests/docs/**`;
- `.github/workflows/d003-readme-i004-status.yml`;
- D-001/D-003 research and plan documents;
- package/runtime/release files.

## RED

Before deleting D-001, change only `tests/ci/test_full_suite_workflow_contract.py`.

Add a contract test that:

1. asserts `d001-readme-status.yml` is absent;
2. asserts `d003-readme-i004-status.yml` is present;
3. asserts `tests/docs/test_readme_status.py` exists;
4. verifies D-003 retains:
   - `pull_request:`;
   - `README.md`;
   - `tests/docs/**`;
   - exact-head token `github.event.pull_request.head.sha || github.sha`;
   - Python 3.10 and 3.12;
   - `python -m unittest discover -s tests/docs -v`;
   - `workflow_dispatch:`.

Expected RED: exactly the “D-001 absent” assertion fails while all preservation assertions pass.

Run/record exact RED head through F-007 CI policy workflow and authoritative full suite.

## GREEN

Delete only:

`.github/workflows/d001-readme-status.yml`.

Do not alter D-003 or documentation tests to make GREEN easier.

## Acceptance

On exact GREEN head:

- F-007 CI policy workflow passes;
- authoritative full repository suite passes 3.10/3.12;
- no D-001 workflow file remains;
- D-003 remains exact-head and cross-version;
- docs test file remains;
- diff contains only policy test + deleted workflow.

## Adversarial review

Fresh exact-head review must independently verify:

- README-only PRs still trigger D-003;
- tests/docs changes still trigger D-003 and full suite;
- D-003 actually runs the D-001 test as part of discovery;
- manual dispatch remains available through D-003/full-suite;
- no release/package/runtime guard was deleted;
- historical D-001 research/plan and docs test remain;
- GREEN did not weaken the policy test.

Any final-head change invalidates the review.

## Merge

Merge with expected head SHA only after exact-head CI and adversarial PASS. Close #184 through the implementation PR.
