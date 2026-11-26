# F-007 plan: centralize full-repository CI ownership

**Issue:** #34  
**Research:** `docs/research/F-007-ci-full-suite-deduplication.md` at `391c7b96d710564e4bc0faaaffaeca88d9d74d51`

## Scope

Move the generic full-repository unittest discovery command out of historical feature/follow-up workflows into one authoritative GitHub Actions workflow, while preserving every focused contract suite and maintaining full-repository coverage on Python 3.10 and 3.12.

This ticket changes CI configuration and static CI-contract tests only. Runtime/package semantics are out of scope.

## Baseline problem

On the research baseline, seven merged workflows own:

```text
python -m unittest discover -s tests -v
```

Pending I-003 and F-006 branches add two more owners if merged.

Observed I-003 head `c22a4bd...` caused eight full-suite job executions across seven triggered workflows because I-003 runs a two-version matrix.

## Authoritative workflow

Add `.github/workflows/full-suite.yml`.

### Events

```yaml
on:
  push:
    paths:
      - pyproject.toml
      - "src/**"
      - "tests/**"
      - ".github/workflows/**"
  pull_request:
    paths:
      - pyproject.toml
      - "src/**"
      - "tests/**"
      - ".github/workflows/**"
  workflow_dispatch:
```

Rationale:
- push preserves pre-PR branch RED/GREEN validation;
- pull_request provides the merge/review exact-head gate;
- docs-only changes outside tests/workflows do not need generic runtime discovery;
- workflow changes themselves always exercise the CI contract.

### Concurrency

Use:

```yaml
concurrency:
  group: full-suite-${{ github.event.pull_request.head.sha || github.sha }}
  cancel-in-progress: true
```

This lets overlapping push/PR runs for the same source head cancel rather than consume runner capacity concurrently. Different content SHAs remain independent gates.

### Test matrix

```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.10", "3.12"]
```

Each matrix job:
1. checkout exact head;
2. set up matrix Python;
3. upgrade pip;
4. install editable package;
5. install `build`;
6. run exactly `python -m unittest discover -s tests -v`.

Installing `build` is mandatory so packaging tests that conditionally depend on it execute rather than skip.

## Focused workflow edits

Remove only the generic full-repository discovery step from each workflow where it exists.

On the current baseline:
- `d001-readme-status.yml`: retain README status contract;
- `f002-wheel-schema-resources.yml`: retain wheel regression and I-001 suite;
- `f003-digest-projection-key-errors.yml`: retain F-003 regression and I-002 suite;
- `f004-source-bundle-diagnostic-paths.yml`: retain F-004 regression and I-002 suite;
- `f005-utf16-diagnostic-paths.yml`: retain F-005 regression and I-002 suite;
- `i001-validation.yml`: retain I-001 contract tests;
- `i002-validation.yml`: retain I-002 focused tests.

If I-003 and/or F-006 merge before final integration:
- I-003 retains its 3.10/3.12 **focused I-003** matrix but loses its per-matrix full repository step;
- F-006 retains focused F-006 + I-001 matrix steps but loses its full repository step.

No other workflow step is removed in this ticket.

## Static TDD contract

Add package `tests/ci/` and `tests/ci/test_full_suite_workflow_contract.py` before workflow implementation.

The test must use plain text inspection rather than YAML deserialization so GitHub-specific expression syntax and YAML-version handling cannot distort the contract.

### Required assertions

1. Enumerate every `.github/workflows/*.yml` file.
2. Count files containing the exact canonical command:
   `python -m unittest discover -s tests -v`.
3. Assert the sole owner list is exactly `['full-suite.yml']`.
4. Assert `full-suite.yml` exists.
5. Assert it contains:
   - `push:`
   - `pull_request:`
   - `workflow_dispatch:`
   - `pyproject.toml`
   - `src/**`
   - `tests/**`
   - `.github/workflows/**`
   - Python versions `3.10` and `3.12`
   - `fail-fast: false`
   - `github.event.pull_request.head.sha || github.sha`
   - `cancel-in-progress: true`
   - `python -m pip install build`
   - exactly one canonical full-suite command in the workflow text.
6. For each known focused workflow that exists, assert its distinctive focused command/token remains present:
   - D-001: `tests.docs.test_readme_status`
   - F-002: `tests.packaging.test_wheel_schema_resources` and `discover -s tests/i001`
   - F-003: `tests.i002.test_projection_key_error_boundary` and `discover -s tests/i002`
   - F-004: `tests.i002.test_source_bundle_diagnostic_paths` and `discover -s tests/i002`
   - F-005: `tests.i002.test_utf16_diagnostic_paths` and `discover -s tests/i002`
   - I-001: `discover -s tests/i001`
   - I-002: `discover -s tests/i002`
   - I-003, if present: `discover -s tests/i003`
   - F-006, if present: `tests.i001.test_deep_source_nesting` and `discover -s tests/i001`.

The test intentionally checks I-003/F-006 conditionally so the RED artifact is valid before those concurrent PRs land, while the final integrated head automatically enforces them if present.

## RED gate

Add, in order:
1. `tests/ci/__init__.py`;
2. `tests/ci/test_full_suite_workflow_contract.py`;
3. `.github/workflows/f007-ci-full-suite-deduplication.yml`.

F-007 workflow:
- branch push trigger `perf/ci-full-suite-dedup` and PR trigger;
- install package;
- run only `python -m unittest tests.ci.test_full_suite_workflow_contract -v` as the focused gate;
- after implementation it may also run `python -m unittest discover -s tests/ci -v`, but it must never own the generic full-repository command.

The RED head must fail because `full-suite.yml` does not exist and multiple historical workflows own the canonical command. No workflow production edits occur before this failure is recorded.

## GREEN implementation order

After RED is observed:
1. add `full-suite.yml`;
2. remove generic full-suite steps from the seven baseline workflows;
3. run static F-007 contract;
4. observe central full-suite 3.10/3.12 push matrix;
5. verify no focused workflow lost its distinguishing command.

## Concurrent-PR integration gate

Before opening/finalizing the F-007 PR:
1. fetch then-current `main`;
2. if I-003/F-006 have merged, integrate current main first;
3. apply the same generic-step removal to their new workflows;
4. static contract must dynamically find exactly one full-suite owner;
5. compare final head to current main and confirm runtime `src/ontotf/**` files are untouched by F-007;
6. rerun central matrix and F-007 focused gate on the integrated exact head.

If concurrent main integration introduces any workflow containing the canonical command, the static test must go RED until that workflow is deduplicated. This is intentional.

## PR-level expected checks

On the final PR:
- `full-suite` runs Python 3.10 and 3.12 full discovery;
- F-007 static contract runs;
- changed historical workflow files may trigger their focused workflows; those should execute focused suites only;
- there must be no other job step containing the canonical generic full-suite command.

## Review gate

After exact-head GREEN, require a fresh logically-independent adversarial review of the exact head. Review must specifically test for coverage loss, path-filter bypass, packaging-test skipping, concurrency mistakes, and accidental removal of focused gates.

The authoring context does not count. Any material head change restarts CI and review.

## Non-goals

- no runtime code changes;
- no test logic changes outside the static CI contract;
- no dependency caching;
- no branch-protection administration;
- no removal of focused workflows;
- no conversion to another test runner or CI provider.
