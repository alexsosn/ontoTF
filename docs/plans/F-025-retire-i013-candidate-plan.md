# F-025 plan — retire automatic I-013 historical candidate CI

**Issue:** #179  
**Research:** `docs/research/F-025-retire-i013-candidate.md`  
**Baseline:** `main` `da9fd1f239019d66c933fb7023d17293ae2ca9b1`  
**Phase:** plan only

## Goal

Remove the obsolete automatic I-013 release-candidate workflow while preserving its tests through the authoritative full suite and preserving both historical v0.1.0 publication safety and current v0.1.1 release verification.

## Exact implementation scope

Expected behavioral diff:

1. extend `tests/ci/test_full_suite_workflow_contract.py` with one historical-release-workflow policy regression;
2. delete `.github/workflows/i013-release-candidate.yml`.

No other workflow, test, source, package metadata, documentation, release note, semantic resource, or release artifact changes.

## RED contract

Extend only `tests/ci/test_full_suite_workflow_contract.py`.

That file already freezes the authoritative full-suite command, Python 3.10/3.12 matrix, exact-head checkout and `workflow_dispatch`. Add one new test that establishes only the missing post-maintenance policy:

- obsolete `.github/workflows/i013-release-candidate.yml` is absent from the workflow inventory;
- `tests/i013` and `tests/i009` still contain test files;
- `.github/workflows/i013-release.yml` still exists;
- historical I-013 publication workflow still has no `pull_request:` trigger and retains exact main path `docs/releases/v0.1.0.md`;
- `.github/workflows/i014-v011-release.yml` still exists.

Do not duplicate the full-suite matrix/dispatch assertions already present in the same test module.

RED exact head should fail only because the obsolete candidate workflow still exists. All preservation assertions must pass.

Do not delete or edit the workflow before the RED result is observed.

## GREEN contract

Delete exactly:

`.github/workflows/i013-release-candidate.yml`.

Do not edit the policy test after the RED unless the RED reveals a test defect unrelated to the intended existence assertion.

Expected automatic CI:

- full repository suite runs because both `tests/**` and `.github/workflows/**` change;
- the obsolete candidate workflow may run one last time from the base/changed workflow semantics; if it does, it must remain green and is not a blocker;
- I-014/I-157 may run according to existing path filters but are not modified.

## Test design constraints

The policy regression extends the existing workflow-policy suite and protects capabilities rather than copying complete YAML:

- assert only required trigger/job command fragments;
- do not snapshot whole workflows;
- do not require job names, runner labels, action major versions, concurrency wording, or formatting;
- do not parse YAML with an additional dependency;
- use `pathlib.Path` and text assertions under stdlib `unittest`.

The historical I-013 publication guard assertion should prove:

- file exists;
- main push trigger exists;
- `docs/releases/v0.1.0.md` exact path exists;
- no `pull_request:` trigger exists.

This freezes the already-reviewed post-I-014 historical boundary without reopening release engineering.

## Exact-head final gates

Before merge require:

1. RED evidence on tests-only head;
2. GREEN policy test;
3. authoritative full suite PASS on Python 3.10 and 3.12;
4. no unexpected changed files;
5. fresh independent adversarial review on exact final SHA.

The reviewer should independently challenge:

- coverage subset claim;
- current README/v0.1.1 release coverage after deletion;
- preservation of historical tests;
- preservation of v0.1.0 write guard;
- accidental modification of I-014;
- overfitting of the policy test.

Merge with expected-head SHA only.

## Exit condition

The historical I-013 candidate workflow no longer consumes automatic PR CI, while all underlying regression tests and current/historical release guards remain available.
