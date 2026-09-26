# F-028 plan — migrate post-release I-014 CI ownership

**Issue:** #188  
**Research:** `docs/research/F-028-post-release-i014-ci.md`  
**Research merge:** `1cff1bcf592aea52b0fcdde815c578f73488d0a6`  
**Phase:** plan only

## Goal

Remove release-version-specific v0.1.1 PR/publisher CI after successful publication while preserving every still-live contract under generic lightweight owners.

## Exact file scope

Implementation may change only:

1. `tests/ci/test_full_suite_workflow_contract.py`;
2. `tests/docs/test_readme_status.py`;
3. `.github/workflows/i012-v01-acceptance.yml`;
4. `.github/workflows/d003-readme-i004-status.yml`;
5. delete `.github/workflows/i014-v011-release.yml`;
6. delete `tests/i014/test_v011_release.py`;
7. delete `tests/i014/__init__.py`.

Do not change:

- README;
- `docs/releases/v0.1.1.md`;
- pyproject;
- package/runtime source;
- profile/mapping/evidence/ontology resources;
- `scripts/acceptance/v01_noun.py`;
- I-157 workflow/tests;
- published GitHub release/tag/assets.

## Historical release-note lock

Current repository `docs/releases/v0.1.1.md` is byte-for-byte equal to the published GitHub release body.

Exact UTF-8 SHA-256:

`9fe8ab941cc06fe37f45e99e0eb98a75cdc26ddde433bc3ed4ae582691b5e280`

Move this invariant into `tests/docs/test_readme_status.py`.

The docs test should also retain semantic markers such as:

- `metadata-only`;
- `MIT AND CC-BY-3.0`;
- `BHSA`, `Syriac`, `ExtraBiblical`;
- no supported PyPI claim.

A digest mismatch must fail with a message explaining that the checked-in historical release notes no longer match the reviewed published v0.1.1 record.

## RED phase

Change tests only.

### `tests/docs/test_readme_status.py`

Add:

1. current README must contain exact release URL:
   `https://github.com/alexsosn/ontoTF/releases/tag/v0.1.1`;
2. current README must contain `metadata-only`;
3. existing wheel-install/no-PyPI/no-bundled checks remain;
4. v0.1.1 release notes must exist;
5. release notes SHA-256 must equal the exact digest above;
6. release notes must retain the semantic markers.

These assertions should already pass on the baseline. Their role is migration-before-deletion, not manufactured failure.

### `tests/ci/test_full_suite_workflow_contract.py`

Migrate the F-025 assertion that currently requires I-014 presence.

Add/replace policy so future GREEN requires:

- `i014-v011-release.yml` absent;
- `tests/i014/test_v011_release.py` absent;
- `tests/i014/__init__.py` absent;
- I-157 workflow still present;
- I-012 workflow present and containing:
  - `pull_request:`;
  - `pyproject.toml`;
  - exact-head token `github.event.pull_request.head.sha || github.sha`;
  - Python 3.10 and 3.12;
  - wheel build;
  - copied `scripts/acceptance/v01_noun.py`;
- D-003 workflow present and containing:
  - `README.md`;
  - `tests/docs/**`;
  - `docs/releases/v0.1.1.md`;
  - exact-head token;
  - Python 3.10/3.12;
  - tests/docs discovery.

Expected RED failures are only repository ownership state:

- I-014 workflow/tests still present;
- I-012 lacks `pyproject.toml` and explicit exact-head checkout;
- D-003 lacks v0.1.1 release-note path.

The newly migrated docs assertions must pass in RED.

Record exact RED head/logs before workflow/test deletions.

## GREEN phase

Make only ownership migrations:

### I-012

In `.github/workflows/i012-v01-acceptance.yml`:

- add `pyproject.toml` to `pull_request.paths`;
- optionally add it to historical feature-branch push paths only if doing so is needed for symmetry; do not add broad `src/**`;
- set checkout ref:
  `${{ github.event.pull_request.head.sha || github.sha }}`;
- keep Python 3.10/3.12 and acceptance runner logic unchanged.

### D-003

In `.github/workflows/d003-readme-i004-status.yml`:

- add `docs/releases/v0.1.1.md` to pull-request paths;
- adding the same path to its historical feature-branch push list is allowed for symmetry;
- leave exact-head, Python matrix and docs discovery unchanged.

### Retire I-014

Delete:

- `.github/workflows/i014-v011-release.yml`;
- `tests/i014/test_v011_release.py`;
- `tests/i014/__init__.py`.

No replacement `contents: write` workflow is allowed in this ticket.

## Ownership after GREEN

### README/release docs

D-003 + tests/docs:
- automatic PR coverage;
- exact head;
- 3.10/3.12;
- current release URL/install/metadata-only truth;
- exact historical release-note content lock.

### Packaging metadata

I-157:
- PEP 639 source + wheel/sdist;
- license bytes/resources;
- clean installed resource access;
- no TF/MQL payload.

### Packaging-change fresh wheel

I-012:
- pyproject PR trigger;
- exact head;
- wheel build;
- fresh venv install;
- copied v0.1 semantic acceptance;
- 3.10/3.12.

### Generic regression

Full repository suite:
- pyproject/tests/workflows;
- 3.10/3.12.

## Expected CI savings

Compared with current I-014 PR behavior:

- README-only: save four I-014 jobs;
- tests/docs: save four I-014 jobs;
- v0.1.1 notes: replace four I-014 jobs with two D-003 docs jobs;
- pyproject: replace four I-014 jobs with two I-012 fresh-wheel jobs, while I-157/full-suite remain.

## GREEN acceptance

Exact head must show:

- F-007 policy PASS;
- D-003 docs workflow PASS when triggered by test/workflow changes as applicable;
- I-012 focused workflow policy covered by F-007 and its own workflow syntax/config inspected; direct I-012 job may not trigger unless a listed path changes — this ticket changes I-012 itself, so it must trigger and PASS 3.10/3.12;
- authoritative full-suite PASS 3.10/3.12;
- F-011 action-major policy PASS for workflow changes;
- no I-014 workflow remains;
- no tests/i014 module remains.

## Independent adversarial review

Fresh reviewer must verify:

1. release-note digest constant is correct for the exact published/repository body;
2. README-only and release-note PRs still have automatic exact-head coverage;
3. I-012 now preserves I-014 fresh-wheel coverage for pyproject changes;
4. I-012 did not broaden to all src changes;
5. I-157 still owns PEP639 and was not altered;
6. future package/profile version bumps are no longer blocked by v0.1.1/0.1.0 historical pins;
7. no `contents: write` v0.1.1 workflow remains;
8. published v0.1.1 API state remains unchanged;
9. final diff is limited to the seven authorized files.

Any final-head change invalidates review.

## Merge and post-merge readback

Merge with expected head SHA after exact-head CI and adversarial PASS.

After merge, independently read GitHub API state and require:

- release `v0.1.1` still targets `d53824c2f5d4f9e209dc685159ba6c56d267aba7`;
- tag `refs/tags/v0.1.1` still points to that commit;
- asset `tfont-0.1.1-py3-none-any.whl` still reports digest `sha256:a2a63562aba2d8fec25dfe65ee5c807db4f40991377d0d81989d5ab8ed6e6c3d`;
- release remains non-draft.

Only then treat #188 as operationally complete.
