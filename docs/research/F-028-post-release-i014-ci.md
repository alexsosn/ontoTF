# F-028 research — narrow post-release I-014 v0.1.1 candidate CI

**Issue:** #188  
**Baseline:** `main` `58c8807fa85369970d9c01eb229ad5971cbfdfc2`  
**Recorded:** 2026-09-26  
**Phase:** research only

## Decision

Retire the published-version I-014 workflow and stale I-014 test module, but first relocate each still-live contract to the correct generic owner:

- current README/release-note truth -> `tests/docs` + D-003;
- PEP 639 package metadata -> existing I-157;
- fresh-wheel semantic acceptance for packaging changes -> existing I-012, triggered on `pyproject.toml` and fixed to exact-head checkout;
- repository regression suite -> existing authoritative `full-suite.yml`.

After those migrations, delete:

- `.github/workflows/i014-v011-release.yml`;
- `tests/i014/test_v011_release.py`;
- `tests/i014/__init__.py`.

Do not retain a write-capable historical publisher after v0.1.1 has been successfully published and independently read back.

## Published release evidence

GitHub API readback already confirmed:

- release/tag `v0.1.1`;
- exact target `d53824c2f5d4f9e209dc685159ba6c56d267aba7`;
- non-draft release;
- wheel `tfont-0.1.1-py3-none-any.whl`;
- asset digest `sha256:a2a63562aba2d8fec25dfe65ee5c807db4f40991377d0d81989d5ab8ed6e6c3d`.

The release workflow's publication job therefore completed its purpose. Keeping a `contents: write` workflow keyed to edits of historical v0.1.1 notes adds post-release mutation surface without creating a new legitimate publication operation.

## Current I-014 PR cost

For every matching PR, `i014-v011-release.yml` runs:

- reusable full-suite 3.10/3.12;
- candidate job 3.10/3.12;
- source/docs I-014 test;
- full PEP 639 wheel+sdist build regression;
- another exact wheel+sdist build;
- fresh venv wheel install;
- v0.1 semantic acceptance;
- artifact digest + upload.

The publish job is skipped on PR.

This is appropriate for a release candidate, but v0.1.1 is now historical output.

## Assertion ownership inventory

### `test_current_package_version_is_v011`

Historical/stale after publication.

It blocks any future package version bump merely because v0.1.1 once existed. A released version should not permanently define current `pyproject.toml`.

**Decision:** remove from current test suite; do not relocate.

### `test_pep639_mixed_license_contract_is_preserved`

Generic current packaging contract.

I-157 already asserts:

- `setuptools>=77.0.3`;
- `MIT AND CC-BY-3.0`;
- exact license-files;
- no legacy license table/classifier;
- wheel/sdist metadata and license bytes;
- separately packaged OLiA resources;
- clean installed package-resource access;
- no TF/MQL payload.

**Decision:** I-157 remains sole owner; remove I-014 duplicate.

### `test_readme_points_to_v011_metadata_only_patch`

Still-live current documentation contract while v0.1.1 is the advertised release.

`tests/docs/test_readme_status.py` already owns:

- local wheel install string `tfont-0.1.1-py3-none-any.whl`;
- no unsupported PyPI claim;
- corpus data not bundled.

It does not yet pin:

- current GitHub release URL `.../releases/tag/v0.1.1`;
- `metadata-only` patch wording.

**Decision:** move those missing assertions into `tests/docs/test_readme_status.py`. D-003 already runs all docs tests for README changes on 3.10/3.12.

### `test_v011_release_notes_define_patch_boundary`

Historical release-document contract.

The release notes file currently matches the body used for the published release. The old main publisher made edits fail closed because an existing release targets the earlier release commit.

If the write-capable workflow is retired, preserve this historical record with a cheap docs-test content lock plus semantic markers. The plan should compute and pin the exact SHA-256 of the current `docs/releases/v0.1.1.md` bytes. Any later change must explicitly update that reviewed lock rather than silently drifting the repository copy from the published release record.

Add `docs/releases/v0.1.1.md` to D-003 PR paths so this lock runs automatically before merge.

**Decision:** move to `tests/docs`, with exact content digest plus useful semantic markers.

### `test_profile_versions_remain_v010`

Historical release assertion that becomes harmful if profiles legitimately advance.

Profile/release identity is already validated by semantic bundle/profile tests and production resource paths. A package patch release should not permanently prevent future profile versions.

**Decision:** remove from I-014 current suite; do not relocate as a “current must equal 0.1.0” assertion.

## Fresh-wheel acceptance ownership

I-014's unique useful non-documentation behavior after removing PEP639 duplicates is fresh-wheel execution of `scripts/acceptance/v01_noun.py`.

The existing `.github/workflows/i012-v01-acceptance.yml` already implements exactly that generic job on Python 3.10/3.12:

1. build the current wheel;
2. fresh venv;
3. install wheel outside checkout;
4. copy/run v0.1 semantic acceptance;
5. validate the final JSON contract.

But I-012 currently triggers only when its own acceptance script/workflow changes, and checkout is not explicitly pinned to the PR head.

**Decision:** make I-012 the generic packaging clean-wheel owner by:

- adding `pyproject.toml` to its PR path trigger;
- using `ref: ${{ github.event.pull_request.head.sha || github.sha }}` on checkout;
- preserving Python 3.10/3.12 and the existing runner unchanged.

Do not broaden I-012 to every `src/**` change in F-028. I-014 itself never covered `src/**` PRs, so that would be scope expansion rather than preservation.

## Full-suite ownership

I-014 also calls the reusable full suite. That is duplicate for:

- `pyproject.toml`;
- `tests/i014/**`;
- `tests/i013/**`;
- `tests/docs/**`;
- packaging tests;
- workflow changes,

because authoritative `full-suite.yml` already triggers on `pyproject.toml`, `tests/**`, and `.github/workflows/**`.

For README/release-note-only PRs, full repository tests are unnecessary once live release/docs assertions move to `tests/docs` and D-003 owns those paths.

## D-003 extension

D-003 is now the sole automatic README documentation workflow after F-027 and already:

- watches README and `tests/docs/**`;
- checks out exact PR head;
- runs Python 3.10/3.12;
- runs all `tests/docs`;
- supports manual dispatch.

Extend its PR paths with:

`docs/releases/v0.1.1.md`

This keeps post-release documentation validation lightweight and explicit.

## I-014 workflow retirement

Delete `.github/workflows/i014-v011-release.yml` after migration.

Reasons:

1. v0.1.1 publication succeeded and was API-verified;
2. no future legitimate operation should recreate or retarget the same release;
3. current main-only path is write-capable despite being historical;
4. its PR candidate is release-version-specific and carries stale version assumptions;
5. its generic checks have surviving owners after the migrations above.

The published GitHub release/tag/asset are external historical state and are not mutated by deleting repository workflow code.

## CI policy migration

`tests/ci/test_full_suite_workflow_contract.py` currently contains an F-025 preservation assertion requiring `i014-v011-release.yml` to exist.

F-028 must migrate that policy deliberately:

- require I-014 workflow absence after release;
- require I-012 present with `pyproject.toml`, exact-head checkout, Python 3.10/3.12 and the fresh-wheel acceptance command;
- require D-003 present with README, `tests/docs/**`, `docs/releases/v0.1.1.md`, exact-head checkout and docs discovery;
- require current release docs test file remains.

Do not simply delete the old assertion.

## Expected CI savings

Approximate jobs removed per matching PR:

- README-only: D-003 2 + I-014 4 -> D-003 2 (**save 4 jobs**);
- `tests/docs/**`: full-suite 2 + D-003 2 + I-014 4 -> full-suite 2 + D-003 2 (**save 4**);
- v0.1.1 release notes: I-014 4 -> D-003 2 (**save 2**);
- `pyproject.toml`: full-suite 2 + I-157 2 + I-014 4 -> full-suite 2 + I-157 2 + I-012 clean-wheel 2 (**save 2**, while preserving fresh-wheel acceptance).

Exact totals can be higher because other focused workflows may also trigger, but F-028 does not alter them.

## TDD recommendation

### RED

Change tests only:

1. `tests/ci/test_full_suite_workflow_contract.py`:
   - require retired I-014 workflow absent;
   - require I-012 generic packaging acceptance ownership;
   - require D-003 current-release docs ownership.
2. `tests/docs/test_readme_status.py`:
   - require current release URL and metadata-only wording;
   - require v0.1.1 notes markers;
   - require exact SHA-256 lock of current v0.1.1 notes.

Current main should fail because:

- I-014 still exists;
- I-012 does not watch `pyproject.toml` or explicit exact head;
- D-003 does not watch v0.1.1 notes;
- docs test lacks the new release-note lock.

Do not change workflows or delete I-014 tests in RED.

### GREEN

Then:

- extend I-012 trigger + exact-head checkout;
- extend D-003 path;
- delete I-014 workflow;
- delete stale `tests/i014` module after its surviving assertions have moved/been assigned.

No README, release notes, package code, pyproject, profiles, mappings, ontology bytes, or acceptance runner changes.

## Independent review targets

A skeptical reviewer should verify:

1. every removed I-014 assertion has either a surviving owner or is explicitly stale historical pinning;
2. README-only PRs remain automatically checked;
3. v0.1.1 release-note changes run a cheap exact-head docs gate;
4. release notes content lock matches the published release body/repository bytes;
5. PEP639 remains covered by I-157;
6. `pyproject.toml` still receives clean-wheel v0.1 acceptance through I-012;
7. I-012 exact-head behavior is corrected before it becomes a live packaging gate;
8. future version/profile bumps are no longer blocked by I-014 hard-coded pins;
9. no workflow with `contents: write` remains for v0.1.1;
10. GitHub v0.1.1 tag/release/asset are unchanged.

## Exit decision

Proceed to plan/TDD. This is a post-release ownership migration, not a reduction in release/package correctness.
