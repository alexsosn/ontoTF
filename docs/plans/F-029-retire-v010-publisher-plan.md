# F-029 plan — retire historical v0.1.0 publisher

**Issue:** #192  
**Research:** `docs/research/F-029-retire-v010-publisher.md`  
**Research merge:** `befbb030bedcced88995d87a4f15c0f08154307d`

## Scope

Implementation may change exactly:

1. `tests/docs/test_readme_status.py`;
2. `tests/ci/test_full_suite_workflow_contract.py`;
3. `.github/workflows/d003-readme-i004-status.yml`;
4. delete `.github/workflows/i013-release.yml`.

Preserve unchanged:

- `tests/i013/test_release_red.py`;
- `docs/releases/v0.1.0.md`;
- README;
- pyproject/package/runtime/resources;
- I-012/I-157;
- published v0.1.0 release/tag/assets.

## RED

Tests only.

### Docs test

Add a v0.1.0 historical release-note contract:

- file exists;
- compute exact standard Git blob SHA-1 from bytes and require
  `2dbd212d7f69081d21770aaa3736d8647fee6996`;
- retain markers:
  `0.1.0`, `Noun`, `BHSA`, `Syriac`, `ExtraBiblical`,
  `CC BY 3.0`, `MIT`, `API doubles`.

These assertions must already pass in RED.

### CI policy

Replace the old historical-v0.1.0-workflow preservation assertion with:

- `i013-release.yml` absent;
- `tests/i013/test_release_red.py` present;
- D-003 present and containing both
  `docs/releases/v0.1.0.md` and `docs/releases/v0.1.1.md`;
- I-012 and I-157 workflows remain present.

Expected RED failures only:

- I-013 publisher still exists;
- D-003 does not yet watch v0.1.0 notes.

Record exact RED logs.

## GREEN

- add `docs/releases/v0.1.0.md` to D-003 pull-request paths;
- delete only `.github/workflows/i013-release.yml`.

No replacement write-capable v0.1.0 workflow.

## Acceptance

Exact GREEN head:

- D-003 PASS 3.10/3.12;
- F-007 PASS;
- F-011 PASS;
- full-suite PASS 3.10/3.12;
- `tests/i013` remains and passes through full-suite;
- I-012/I-157 unchanged;
- diff limited to four authorized files.

## Independent review

Verify exact note blob lock, D-003 exact-head ownership, retention of I-013 semantic regression, removal of v0.1.0 `contents: write`, and no release/package/runtime changes.

## Merge and post-merge readback

Merge with expected head SHA only after exact-head PASS + fresh adversarial review.

Then require GitHub API to still show:

- release/tag target `dcab3a473f3a4347554194ec9a5e34238b7c0769`;
- non-draft/non-prerelease;
- asset `tfont-0.1.0-py3-none-any.whl`;
- digest `sha256:4c85b6ce0aeddf226c105400472077014b7a6a9eb96005ea641776143c2a1560`.

Only then close #192.
