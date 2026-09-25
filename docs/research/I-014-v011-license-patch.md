# I-014 research — v0.1.1 mixed-license metadata patch release

**Issue:** #175  
**Baseline:** `main` `77f75285890d39d19525081386a6c0c602ce7df7`  
**Recorded:** 2026-09-25  
**Phase:** research only

## Decision

Publish a **v0.1.1 packaging-only patch release** from a separately reviewed release candidate. Do not alter, retag, replace, or upload over the existing v0.1.0 release.

The patch exists because the supported v0.1.0 wheel predates the reviewed PEP 639 mixed-license correction from #157. The semantic/runtime/resource contract remains the same as v0.1.0.

Use a narrowly version-specific v0.1.1 release workflow rather than broadening the existing v0.1.0 workflow or making every `docs/releases/**` edit publishable. The workflow may validate on PR, but its write-capable publish job runs only on the exact merged `main` push that includes `docs/releases/v0.1.1.md`.

## 1. Verified release state

GitHub release `v0.1.0` exists and is published, non-draft, with wheel asset:

`tfont-0.1.0-py3-none-any.whl`

The release targets commit:

`dcab3a473f3a4347554194ec9a5e34238b7c0769`

The release asset was published on 2026-09-22.

At that exact commit, `pyproject.toml` used:

```toml
[build-system]
requires = ["setuptools>=75", "wheel"]

[project]
version = "0.1.0"
license = {file = "LICENSE"}
classifiers = [
  "License :: OSI Approved :: MIT License",
]
```

The distribution already contained the OLiA CC BY 3.0 payload/license/attribution, so this metadata describes only the root MIT side of a mixed-license distribution.

## 2. Current corrected packaging contract

Current main after #157 uses:

```toml
requires = ["setuptools>=77.0.3", "wheel"]
license = "MIT AND CC-BY-3.0"
license-files = [
  "LICENSE",
  "src/tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/LICENSE.data",
  "src/tfont/resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/ATTRIBUTION.txt",
]
```

The focused #157 contract already verifies wheel and sdist metadata, license-file bytes, separately packaged OLiA resources, clean installed resource access, and absence of corpus TF/MQL payload.

## 3. Patch-scope proof

GitHub compare from the v0.1.0 release target `dcab3a473…` to research baseline `77f752858…` is 13 commits ahead but changes only:

- `.github/workflows/i157-pep639-license.yml`;
- `docs/plans/157-pep639-mixed-license-plan.md`;
- `docs/research/157-pep639-mixed-license.md`;
- `docs/research/R-018-multi-binding-resolution-composition.md`;
- `pyproject.toml`;
- `tests/packaging/test_pep639_mixed_license.py`.

No `src/tfont/*.py`, schema, production profile, mapping, evidence, ontology bytes, or acceptance-runner source changed after the release target.

Therefore v0.1.1 can truthfully state:

- same exact OLiA Noun semantic slice;
- same three pinned corpus revisions;
- same runtime behavior and dependencies;
- corrected distribution license metadata only, plus release/verification infrastructure.

The package version changes to 0.1.1; **profile/resource versions remain 0.1.0** because their semantic content is unchanged.

## 4. Why v0.1.0 must remain immutable

The existing release/tag is historical output from its exact source commit. Replacing the asset or moving the tag would erase provenance and violate the existing I-013 fail-closed publication contract.

v0.1.1 must use a new tag, new release, new wheel filename, and new release notes. It may mention that v0.1.0 remains available as historical output but superseded for installation because of package metadata.

## 5. Publication mechanism

### Rejected: mutate v0.1.0

Never replace the existing wheel, move the tag, edit its source target, or make its old asset appear to have been built from #157.

### Rejected: broad `docs/releases/**` auto-publish

A reusable workflow triggered by any release-notes edit would give old-note maintenance a publication side effect. Dynamic version/path coupling inside GitHub Actions is also more complex than this patch warrants.

### Rejected for this automated loop: workflow_dispatch-only publication

Manual dispatch is a clean generic mechanism, but the currently connected GitHub tool surface exposes no workflow-dispatch action. Using it would leave the automated loop unable to complete publication/readback.

### Chosen: one version-specific v0.1.1 workflow

Add `.github/workflows/i014-v011-release.yml`.

PR triggers cover the candidate files and perform read-only validation. Main push trigger is **only** `docs/releases/v0.1.1.md`; merging the reviewed candidate therefore runs the publication path once, while later unrelated main changes cannot publish.

The publish job alone receives `contents: write`.

## 6. Candidate file scope

Implementation should be limited to:

1. `pyproject.toml` — package version `0.1.1`; keep #157 PEP 639 metadata and dependencies/resources unchanged.
2. `README.md` — installation points to v0.1.1 wheel/release and explains v0.1.1 is metadata-only; semantic capability remains the v0.1 slice.
3. `docs/releases/v0.1.1.md` — short patch notes, exact reason, unchanged semantic/runtime scope, license metadata, supported installation channel.
4. `tests/i014/test_v011_release.py` — cheap current-version/source/docs contract.
5. `tests/i013/test_release_red.py` — retire the obsolete assertion that the **current** package version is permanently 0.1.0; retain historical v0.1.0 release-note/content checks.
6. `tests/docs/test_readme_status.py` — advance the current installation assertion from the v0.1.0 wheel to v0.1.1.
7. `.github/workflows/i013-release.yml` — retire its generic PR-candidate trigger so future version bumps are not judged against hard-coded v0.1.0 wheel/version expectations. Preserve only the historical v0.1.0 main-push guard for edits to `docs/releases/v0.1.0.md`.
8. `.github/workflows/i014-v011-release.yml` — exact build/install/metadata/publication/readback gate for the new patch.

Do not rewrite the historical v0.1.0 release notes. They describe the release that actually happened.

The existing I-013 workflow is not purely historical today: its PR trigger watches `pyproject.toml`, `README.md`, `tests/i013/**`, and docs, while its wheel job hard-codes `tfont-0.1.0`. Leaving it untouched would make every future version bump fail an obsolete candidate gate. The patch must therefore retire that PR trigger deliberately rather than weakening the v0.1.0 publication safeguards.

## 7. TDD contract

Tests-only RED must prove the current main is not yet a v0.1.1 candidate:

- package version is exactly 0.1.1;
- README installation points to `v0.1.1` and `tfont-0.1.1-py3-none-any.whl`;
- v0.1.1 release notes exist and call the patch metadata-only;
- current PEP 639 expression remains `MIT AND CC-BY-3.0`;
- root/OliA license files remain explicit;
- no claim of PyPI publication or corpus bundling appears.

The RED should fail only on version/docs/notes, not by weakening or breaking #157 packaging tests.

## 8. Built-artifact gates

On Python 3.10 and 3.12:

1. build wheel and sdist with current backend;
2. require exactly `tfont-0.1.1-py3-none-any.whl`;
3. require wheel `METADATA`:
   - `Version: 0.1.1`;
   - `License-Expression: MIT AND CC-BY-3.0`;
   - all three reviewed `License-File` entries;
   - no legacy MIT license classifier;
4. verify license-file bytes and OLiA resource bytes using the existing #157 test contract;
5. reject TF/MQL corpus payload;
6. install the wheel into a fresh isolated environment outside checkout;
7. require `importlib.metadata.version("tfont") == "0.1.1"`;
8. run the existing v0.1 Noun acceptance runner unchanged;
9. run full repository suite.

The semantic acceptance runner remains named `v01_noun.py`; it describes the v0.1 semantic contract, not the Python package patch number.

## 9. Publish/readback contract

The main-only publish job:

- checks out exact `${{ github.sha }}`;
- requires `project.version == 0.1.1`;
- requires non-empty `docs/releases/v0.1.1.md`;
- downloads the exact validated 3.12 wheel artifact;
- computes its SHA-256 before publication;
- refuses if `v0.1.1` tag exists without a matching release;
- if release already exists, requires both tag and release target to equal the exact SHA and the named wheel asset to exist with the same GitHub-reported digest, then exits without mutation;
- if absent, creates `v0.1.1` targeting exact SHA with the validated wheel and notes;
- reads back release non-draft state, tag SHA, target SHA, asset name, and asset digest;
- never calls upload/overwrite/retag on v0.1.0.

Do not publish an sdist asset unless a later ticket explicitly changes the supported distribution surface; build the sdist only for metadata verification.

## 10. Independent review targets

Research review should challenge:

1. whether v0.1.1 is justified instead of editing v0.1.0;
2. whether compare really proves no runtime/resource change;
3. whether package version can advance while profile versions stay 0.1.0;
4. whether a one-off path-trigger workflow is safer than generic dispatch/autopublish here;
5. whether main publication can accidentally run from a PR or unrelated commit;
6. whether exact artifact digest is preserved through Actions upload/download and GitHub release upload;
7. whether old I-013 tests/workflow and docs tests create false current-version gates, and whether retiring the I-013 PR trigger leaves a safe historical v0.1.0 guard;
8. whether README/release notes accidentally imply new semantic functionality or PyPI availability.

## Exit decision

Proceed to a plan-only gate for v0.1.1. The patch is justified by distribution metadata correctness, does not change TFont semantic/runtime behavior, and must preserve v0.1.0 as immutable historical provenance.
