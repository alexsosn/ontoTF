# F-025 research — retire automatic I-013 historical candidate CI

**Issue:** #179  
**Baseline:** `main` `d53824c2f5d4f9e209dc685159ba6c56d267aba7`  
**Recorded:** 2026-09-25  
**Phase:** research only

## Decision

Delete `.github/workflows/i013-release-candidate.yml`.

Do not replace it with another automatic trigger or a dedicated `workflow_dispatch` archival workflow. Its test coverage is already a strict subset of `.github/workflows/full-suite.yml`, and the full suite itself already supports `workflow_dispatch`.

Keep:

- `tests/i013/**` as historical release-contract regression tests;
- `tests/i009/**` as production semantic-bundle regressions;
- `.github/workflows/i013-release.yml` as the fail-closed historical v0.1.0 publication guard;
- `.github/workflows/i014-v011-release.yml` as the current v0.1.1 release verification/publication workflow.

## 1. Current redundant workflow

`i013-release-candidate.yml` still has automatic triggers for:

- feature branch `impl/i013-v010-release`;
- pull requests touching `tests/i013/**`;
- `pyproject.toml`;
- `README.md`;
- every `docs/releases/**` file;
- the workflow itself.

It runs three jobs:

1. `tests/i013` on Python 3.10;
2. `tests/i013` on Python 3.12;
3. `tests/i009` on Python 3.12.

On PR #178 / v0.1.1, this historical workflow ran successfully even though the current release candidate was I-014. That run contributed three additional jobs but no unique current-release signal.

## 2. Full-suite overlap

`full-suite.yml` already runs:

```text
python -m unittest discover -s tests -v
```

on both Python 3.10 and 3.12.

Therefore it includes:

- all `tests/i013/test_*.py` on 3.10 and 3.12;
- all `tests/i009/test_*.py` on 3.10 and 3.12.

This is a strict superset of the I-013 candidate test matrix.

For code/test/workflow changes, full-suite automatic triggers already include:

- `pyproject.toml`;
- `src/**`;
- `tests/**`;
- `.github/workflows/**`.

Its checkout explicitly selects the exact PR head SHA, unlike the obsolete candidate workflow's default checkout behavior.

## 3. README and current release coverage

The old I-013 candidate additionally triggers on README and release-note changes.

For the **current** release line, I-014 already triggers on PR changes to:

- `README.md`;
- `docs/releases/v0.1.1.md`;
- `pyproject.toml`;
- release/docs/packaging tests;
- relevant workflows.

I-014 calls the reusable full suite and also performs the stronger current-release wheel/sdist/fresh-install contract.

Thus keeping I-013 candidate for README/current-release changes adds no current verification authority.

## 4. Historical v0.1.0 notes

The only remaining automatic path unique to I-013 candidate is an edit to `docs/releases/v0.1.0.md`.

That is not a reason to preserve an automatic candidate pipeline:

- v0.1.0 is immutable historical output;
- its tag/release still points to `dcab3a473f3a4347554194ec9a5e34238b7c0769`;
- the historical write-capable `i013-release.yml` runs on a main push changing `docs/releases/v0.1.0.md` and refuses mutation if the existing release/tag target differs from the new main SHA.

A future edit to historical v0.1.0 notes is therefore not an ordinary release-candidate path. It should be treated as an exceptional historical-document change, not a reason for every normal PR to pay three legacy jobs.

This ticket does not alter the v0.1.0 publication guard.

## 5. Manual historical verification remains available

Deleting the candidate workflow does not remove the tests.

Historical/current regression verification remains possible by:

- running `python -m unittest discover -s tests/i013 -p 'test_*.py' -v`;
- running `python -m unittest discover -s tests/i009 -p 'test_*.py' -v`;
- running the repository full suite;
- using `full-suite.yml`'s existing `workflow_dispatch`, which can be dispatched against an appropriate ref in GitHub Actions.

Git history also preserves the exact old workflow and release implementation.

A second dedicated manual workflow would duplicate the existing dispatchable full suite without adding authority.

## 6. Proposed maintenance change

Production change should be exactly:

1. add one CI-policy regression test that freezes:
   - obsolete `.github/workflows/i013-release-candidate.yml` must not exist;
   - `tests/i013` and `tests/i009` still exist;
   - `full-suite.yml` still runs all `tests` and exposes `workflow_dispatch`;
   - historical `i013-release.yml` remains present;
   - current `i014-v011-release.yml` remains present;
2. delete `.github/workflows/i013-release-candidate.yml`.

No release notes, package metadata, runtime code, semantic resources, or publication workflows change.

## 7. TDD gate

RED:

- add the CI-policy test only;
- exact RED must fail because `i013-release-candidate.yml` still exists;
- all other assertions should pass.

GREEN:

- delete only `i013-release-candidate.yml`;
- new policy test passes;
- authoritative full suite passes on 3.10/3.12;
- current I-014/I-157 behavior remains untouched.

Because deleting the obsolete workflow itself changes `.github/workflows/**`, the authoritative full suite will run automatically.

## 8. Risk review

A logically independent reviewer should challenge:

1. whether any I-013 candidate job covers something not in full-suite;
2. whether README or current-release docs lose a gate;
3. whether historical v0.1.0 verification becomes impossible;
4. whether deleting the workflow can affect the existing v0.1.0 release/tag;
5. whether the CI-policy test over-specifies filenames instead of protecting actual coverage;
6. whether I-014 should be changed in the same ticket (it should not).

## Exit decision

Proceed to plan. The obsolete I-013 candidate workflow is redundant CI overhead; its tests and historical publication guard remain independently preserved.
