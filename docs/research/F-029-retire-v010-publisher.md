# F-029 research — retire historical v0.1.0 release publisher

**Issue:** #192  
**Baseline:** `main` `3a24af700d551e664840d58c452e54f45bdf6922`  
**Recorded:** 2026-09-27  
**Phase:** research only

## Decision

Delete `.github/workflows/i013-release.yml` after moving the exact v0.1.0 release-note history into the generic documentation contract.

Keep `tests/i013/test_release_red.py`: unlike the retired publisher, it no longer pins the current package version and still provides useful regression coverage for the shipped semantic slice, real-local-TF first-success guidance, and historical v0.1.0 limitation wording.

## External release state

Independent GitHub API readback on the baseline confirms:

- release `v0.1.0` target: `dcab3a473f3a4347554194ec9a5e34238b7c0769`;
- tag `refs/tags/v0.1.0` points to the same commit;
- release is non-draft/non-prerelease;
- wheel `tfont-0.1.0-py3-none-any.whl` digest is `sha256:4c85b6ce0aeddf226c105400472077014b7a6a9eb96005ea641776143c2a1560`;
- checked-in `docs/releases/v0.1.0.md` is byte-for-byte equal to the published release body;
- current Git blob ID for the exact checked-in release-note bytes is `2dbd212d7f69081d21770aaa3736d8647fee6996`.

## Why the publisher is obsolete

The workflow triggers only on a main push changing `docs/releases/v0.1.0.md`. Its wheel build is hard-coded to package version 0.1.0, while current package version is 0.1.1.

Therefore a future edit to historical v0.1.0 notes cannot legitimately republish from current main; the workflow's own `grep '^version = "0.1.0"$'` fails closed before publication. The `contents: write` permission is consequently retained mutation authority with no valid current publication path.

F-028 already established the post-release ownership pattern for v0.1.1: exact historical notes lock + generic docs owner, current packaging acceptance under I-012, PEP 639 under I-157.

## I-013 test ownership

`tests/i013/test_release_red.py` now contains no assertion that current package version equals 0.1.0.

It still verifies:

- README describes OLiA Noun support for BHSA/Syriac/ExtraBiblical;
- README uses real local TF identity in first-success guidance and does not substitute test doubles;
- historical v0.1.0 notes retain functionality/licensing/testing limitation markers.

These are legitimate repository regressions and are already executed by the authoritative full suite on Python 3.10/3.12.

**Decision:** keep the test module. Do not retain a dedicated I-013 workflow merely to run it.

## Historical note lock

Add v0.1.0 to `tests/docs/test_readme_status.py`.

The test should:

- require `docs/releases/v0.1.0.md`;
- verify the exact Git blob content identity `2dbd212d7f69081d21770aaa3736d8647fee6996` by computing standard Git blob SHA-1 from file bytes:
  `sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw)`;
- retain semantic markers such as `0.1.0`, `Noun`, `BHSA`, `Syriac`, `ExtraBiblical`, `CC BY 3.0`, `MIT`, `API doubles`.

Using the Git blob identity is exact byte-level locking and directly matches GitHub's content object.

Extend D-003 PR paths with `docs/releases/v0.1.0.md`, alongside the v0.1.1 path introduced by F-028.

## Current package/release ownership after deletion

- README and historical release-note truth: D-003 + tests/docs;
- I-013 semantic/documentation regression: authoritative full suite;
- fresh-wheel acceptance for `pyproject.toml`: I-012;
- PEP 639 packaging: I-157;
- generic regressions: full-suite.

No current package path depends on `i013-release.yml`.

## Policy migration

`tests/ci/test_full_suite_workflow_contract.py` currently requires `i013-release.yml` as a “historical v0.1.0 guard”.

Migrate that assertion to require:

- `i013-release.yml` absent;
- `tests/i013/test_release_red.py` present;
- D-003 contains `docs/releases/v0.1.0.md` and `docs/releases/v0.1.1.md`;
- I-012/I-157 generic owners remain present.

Do not delete the policy assertion without replacement.

## TDD shape

### RED

Tests only:

1. docs test gains exact v0.1.0 note lock and markers — these should already PASS;
2. CI policy requires historical publisher absence + D-003 v0.1.0 ownership while preserving I-013/I-012/I-157.

Expected RED failures:
- `i013-release.yml` still exists;
- D-003 does not yet watch v0.1.0 notes.

### GREEN

- add `docs/releases/v0.1.0.md` to D-003 pull-request paths;
- delete only `.github/workflows/i013-release.yml`.

Keep `tests/i013` unchanged.

## Independent review

Verify:

1. exact v0.1.0 repository notes still equal the published release body before and after;
2. Git blob lock matches the exact note bytes;
3. I-013 semantic regression remains;
4. v0.1.0 note PRs receive D-003 exact-head 3.10/3.12 coverage;
5. I-012/I-157 are unchanged;
6. no v0.1.0 `contents: write` publisher remains;
7. published release/tag/asset are unchanged after merge.

## Exit

Proceed through plan -> TDD RED -> GREEN -> exact-head CI -> fresh adversarial review -> expected-head merge -> post-merge API readback.
