# I-014 plan — v0.1.1 mixed-license metadata patch release

**Issue:** #175  
**Research:** `docs/research/I-014-v011-license-patch.md` merged in `e684cfe6e81c9c4071cdbdc545702611df94bd99`  
**Phase:** plan only

## Goal

Ship package version **0.1.1** as a metadata-only patch over the existing v0.1 semantic/runtime contract. The patch corrects the distribution license metadata introduced by #157 and publishes a new GitHub release/tag without mutating v0.1.0.

## Exact implementation scope

Expected implementation files:

1. `pyproject.toml`
   - change package version only: `0.1.0 -> 0.1.1`;
   - preserve `setuptools>=77.0.3`, `MIT AND CC-BY-3.0`, explicit `license-files`, dependencies, package data.

2. `README.md`
   - describe v0.1.1 as the current package release;
   - retain that the supported semantic contract is the v0.1 OLiA Noun slice;
   - install from GitHub `v0.1.1` and `tfont-0.1.1-py3-none-any.whl`;
   - state that v0.1.1 changes package metadata only and does not expand semantic/runtime support;
   - retain no-PyPI and no-corpus-bundling boundaries.

3. `docs/releases/v0.1.1.md`
   - metadata-only patch notes;
   - exact mixed-license correction;
   - same pinned corpora/OLiA/runtime behavior as v0.1.0;
   - GitHub wheel remains the supported distribution channel;
   - v0.1.0 remains immutable historical output.

4. `tests/i014/__init__.py`
5. `tests/i014/test_v011_release.py`
   - current package version is exactly 0.1.1;
   - PEP 639 expression/files remain exact;
   - README points to the v0.1.1 release/wheel and labels the patch metadata-only;
   - v0.1.1 notes exist and preserve no-PyPI/no-corpus claims;
   - production profile/resource versions stay 0.1.0.

6. `tests/i013/test_release_red.py`
   - remove the obsolete assertion that the *current* package version is always 0.1.0;
   - keep historical v0.1.0 release-note assertions and semantic/docs truthfulness checks.

7. `tests/docs/test_readme_status.py`
   - current local-wheel installation assertion becomes `tfont-0.1.1-py3-none-any.whl`.

8. `.github/workflows/i013-release.yml`
   - retire `pull_request` trigger entirely;
   - keep only historical main push on `docs/releases/v0.1.0.md`;
   - do not change v0.1.0 build/publish immutability behavior.

9. `.github/workflows/i014-v011-release.yml`
   - PR: read-only validation for candidate files;
   - main push: trigger only when `docs/releases/v0.1.1.md` changes;
   - default `contents: read`;
   - full-suite reusable job;
   - wheel/sdist acceptance matrix on Python 3.10/3.12;
   - publish job only on main push and only job with `contents: write`;
   - exact release/tag/asset digest readback.

No runtime Python, schema, production profile/mapping/evidence, ontology bytes, or acceptance-runner logic may change.

## RED gate

Create a tests-only branch commit first:

- add `tests/i014/__init__.py`;
- add `tests/i014/test_v011_release.py`;
- add a focused read-only `i014` candidate workflow if needed to obtain exact-head CI evidence.

Do **not** change `pyproject.toml`, README, release notes, I-013 tests/workflow, or production code in RED.

Expected RED reasons on current 0.1.0 main:

- package version is 0.1.0, not 0.1.1;
- README points to v0.1.0;
- v0.1.1 release notes are absent.

PEP 639 assertions must already pass. Existing full suite should remain green outside the new I-014 test. Record the exact RED SHA and logs before GREEN.

## GREEN gate

Make the smallest candidate changes listed above.

The old I-013 current-version assertion and PR trigger are migrated only now, after RED is proven. They must not be disabled merely to manufacture RED.

Focused I-014 source/docs tests must pass on Python 3.10 and 3.12.

## Built artifact contract

The I-014 workflow builds wheel + sdist on 3.10/3.12.

For the wheel require:

- exactly one wheel named `tfont-0.1.1-py3-none-any.whl`;
- `Version: 0.1.1`;
- `License-Expression: MIT AND CC-BY-3.0`;
- `License-File` entries for root LICENSE, OLiA `LICENSE.data`, OLiA `ATTRIBUTION.txt`;
- no legacy MIT classifier;
- license-file bytes equal source bytes;
- OLiA package resource bytes remain present;
- no `.tf`, `.mql`, `.mql.gz`, or `.mql.bz2` payload.

For sdist, reuse the existing #157 PEP 639 contract under the bumped version.

Fresh install:

- install exact wheel into a new venv outside checkout;
- `importlib.metadata.version("tfont") == "0.1.1"`;
- copy and execute `scripts/acceptance/v01_noun.py` with checkout forbidden;
- no source checkout imports.

Run the authoritative full suite on exact head.

## Release artifact transport

Use the wheel built in the 3.12 matrix as the publication artifact.

Before upload, compute:

`sha256sum tfont-0.1.1-py3-none-any.whl`

Persist the digest as a small text artifact or recompute after Actions artifact download and compare with the matrix-produced digest. The publish job must prove Actions upload/download did not alter bytes before GitHub release creation.

## Publication guard

On PR, publish job is skipped.

On merged main push caused by the new `docs/releases/v0.1.1.md`:

1. require exact checkout SHA equals `GITHUB_SHA`;
2. require package version 0.1.1;
3. require non-empty v0.1.1 notes;
4. download the validated 3.12 wheel + recorded digest;
5. verify wheel digest before any GitHub write;
6. if `v0.1.1` release exists:
   - release target == exact `GITHUB_SHA`;
   - tag object SHA == exact `GITHUB_SHA`;
   - release non-draft;
   - asset name exact;
   - GitHub asset `digest` == local `sha256:<digest>`;
   - then exit without mutation;
7. if no release but tag exists, fail closed;
8. otherwise create `v0.1.1` with exact target, title, notes, and wheel;
9. read back release target, tag SHA, non-draft state, asset name, asset digest;
10. never use `--clobber`, force-push, asset replacement, or v0.1.0 mutation.

## Exact-head adversarial review

Fresh review after GREEN must challenge:

- no runtime/resource drift;
- current-vs-historical version assertions;
- I-013 retirement cannot publish or retag v0.1.0 from a v0.1.1 PR;
- I-014 write permission exists only in main publish job;
- path trigger cannot publish from unrelated main commits;
- artifact digest is checked after Actions transport and after GitHub upload;
- wheel/sdist PEP 639 metadata remains exact;
- README/notes make no new semantic/PyPI/corpus claims;
- existing v0.1.0 release is untouched.

Any review fix resets exact-head CI/review requirements.

## Merge and post-merge gate

Merge with expected head SHA only after:

- focused I-014 3.10/3.12 green;
- #157 packaging regression green;
- full suite 3.10/3.12 green;
- fresh-wheel acceptance 3.10/3.12 green;
- independent adversarial review PASS.

After merge, observe the main I-014 workflow to completion. Do not close #175 until GitHub API confirms:

- release `v0.1.1` exists, non-draft;
- tag and release target equal the exact merged main SHA;
- wheel asset exists;
- GitHub-reported asset digest equals validated local digest;
- v0.1.0 target/asset remain unchanged.
