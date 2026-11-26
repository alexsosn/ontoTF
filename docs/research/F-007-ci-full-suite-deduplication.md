# F-007 research: deduplicate full-repository CI execution

**Issue:** #34  
**Recorded:** 2026-09-06  
**Baseline:** `main` at `e513643450c8a090c026d6f49ede4c1a7a9b64fe`

## Question

Can ontoTF retain the existing exact-head full-repository test gate while eliminating repeated execution of the same full suite by historical feature/follow-up workflows?

## Repository evidence

The current merged workflows that each contain the canonical command

```text
python -m unittest discover -s tests -v
```

are:

1. `.github/workflows/d001-readme-status.yml`
2. `.github/workflows/f002-wheel-schema-resources.yml`
3. `.github/workflows/f003-digest-projection-key-errors.yml`
4. `.github/workflows/f004-source-bundle-diagnostic-paths.yml`
5. `.github/workflows/f005-utf16-diagnostic-paths.yml`
6. `.github/workflows/i001-validation.yml`
7. `.github/workflows/i002-validation.yml`

Each of these also owns a more specific focused/contract suite. The full-suite step is therefore duplicated cross-workflow rather than being the workflow's unique purpose.

Two pending branches add the same pattern:

- I-003 `.github/workflows/i003-validation.yml` runs the full repository suite in a Python 3.10/3.12 matrix;
- F-006 `.github/workflows/f006-deep-source-nesting.yml` runs focused F-006, I-001, then the full repository suite in a Python 3.10/3.12 matrix.

These pending workflows must be incorporated if they merge before F-007 lands.

## Observed fan-out

Exact I-003 integration head `c22a4bd166a6062fd1a62bf0f066b69e41ee7103` triggered seven workflows:

- I-003
- I-002
- I-001
- F-002
- F-003
- F-004
- F-005

All seven were GREEN. Six execute the full repository suite once; I-003 executes it in both Python 3.10 and 3.12 matrix jobs. The same exact source tree therefore receives **eight full-suite executions**, before counting the focused tests that are genuinely distinct.

This is runner duplication, not additional semantic coverage: the repository test command and checkout tree are the same, with Python-version variation only in I-003.

## GitHub Actions semantics

GitHub's workflow syntax documentation establishes:

- `push` and `pull_request` may use `paths` filters; if any changed path matches, the workflow runs;
- matrix strategies are the supported mechanism for testing multiple Python/runtime versions;
- `concurrency` can group runs by an expression and `cancel-in-progress: true` can cancel an older in-progress run in the same group;
- `github.head_ref` is pull-request-only, so expressions spanning push/PR need a fallback;
- skipped workflows can remain Pending if they are configured as required checks, so path filters must be chosen conservatively for any authoritative required gate.

Primary source:
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## Coverage-preserving architecture

### One authoritative full-suite workflow

Add `.github/workflows/full-suite.yml` with one job matrix:

```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.10", "3.12"]
```

Each matrix job:

1. checks out the exact head;
2. installs the package;
3. installs `build` so packaging tests do not silently skip their build-dependent cases;
4. runs exactly `python -m unittest discover -s tests -v`.

This preserves and strengthens the current full-suite gate: both supported Python versions execute the entire repository suite in one named workflow, and packaging regressions have their optional build frontend available.

### Trigger scope

The authoritative workflow should run for both `push` and `pull_request` whenever changes can affect runtime/tests/CI execution:

- `pyproject.toml`
- `src/**`
- `tests/**`
- `.github/workflows/**`

`workflow_dispatch` remains available.

Documentation-only changes outside `tests/**` do not need the full runtime suite; their owning workflows keep focused documentation contracts. A documentation PR that changes tests still matches `tests/**`.

### Push + PR exact-head behavior

Both push and pull-request events are useful:

- push preserves the automated pre-PR RED/GREEN branch gate;
- pull_request provides the explicit merge/review gate against the PR head/base context.

Use a workflow-level concurrency group based on the actual source head SHA rather than event type:

```yaml
concurrency:
  group: full-suite-${{ github.event.pull_request.head.sha || github.sha }}
  cancel-in-progress: true
```

For a push and subsequent PR/synchronize event on the same exact head, the group key resolves to the same head SHA. Overlapping duplicate runs therefore cannot both consume runner capacity to completion. A later different head SHA is intentionally a different gate and must run.

A push run that has already completed before a PR event is not retroactively reusable by GitHub; a later PR run may still execute. That is acceptable because the PR gate has a distinct lifecycle purpose. The optimization target is cross-workflow sixfold/eightfold duplication, not eliminating every push/PR lifecycle rerun.

## Focused workflow responsibility after F-007

Historical feature/follow-up workflows keep the tests that distinguish them:

- D-001: README status contract;
- F-002: wheel/packaging regression + I-001 structural suite where currently required;
- F-003/F-004/F-005: their focused regression + I-002 suite;
- I-001: I-001 contract suite;
- I-002: I-002 focused suite;
- pending I-003: I-003 focused tests on 3.10/3.12;
- pending F-006: F-006 focused tests + I-001 suite on 3.10/3.12.

Only the generic full-repository command moves to the authoritative workflow.

This keeps ticket-specific diagnostics fast: a focused failure remains attached to the workflow that owns the contract, while a single central workflow answers the cross-repository regression question.

## Expected execution reduction

For the observed `c22a4bd...` fan-out:

- before: 8 full-repository suite executions across 7 workflows;
- after: 2 authoritative full-repository executions (Python 3.10 and 3.12), plus unchanged focused suites.

That is a 75% reduction in full-suite executions for that path pattern, without reducing supported-Python full-suite coverage.

For a typical digest follow-up that currently triggers I-001, I-002, F-002, F-003, F-004, and F-005, the repeated full suite drops from roughly six executions to two.

## Static contract / TDD strategy

A repository test can enforce the architecture without needing to execute GitHub Actions locally.

The RED contract should:

1. scan `.github/workflows/*.yml` for the exact canonical full-suite command;
2. require exactly one owner, `.github/workflows/full-suite.yml`;
3. require that workflow to contain Python `3.10` and `3.12` matrix values;
4. require `push`, `pull_request`, and `workflow_dispatch` triggers;
5. require trigger coverage for `pyproject.toml`, `src/**`, `tests/**`, and `.github/workflows/**`;
6. require a head-SHA concurrency group and `cancel-in-progress: true`;
7. ensure known focused workflows still contain their focused commands after the generic full-suite step is removed.

On the current baseline this test must fail because there is no authoritative `full-suite.yml` and seven merged workflows own the full-suite command.

## Integration with pending I-003/F-006

Do not freeze the implementation to this research baseline.

Before final GREEN/review:

1. rebase/rebuild on the then-current `main`;
2. rescan all workflow YAML files dynamically;
3. if I-003 and/or F-006 have merged, remove their generic full-suite commands while preserving their focused/matrix behavior;
4. rerun the static contract and full CI on the integrated exact head.

This avoids merging a central workflow while newly merged feature workflows immediately reintroduce duplicate ownership.

## Risks and controls

### Risk: accidental coverage loss
Control: central full suite is a 3.10/3.12 matrix and is the sole command owner; static test enforces uniqueness and supported versions.

### Risk: packaging tests silently skip
Control: central workflow installs `build` before full discovery.

### Risk: source changes bypass central gate
Control: conservative `src/**`, `tests/**`, `pyproject.toml`, workflow-path filters on both push and PR.

### Risk: feature diagnostics become less specific
Control: retain focused suites in every owning workflow.

### Risk: stale runner consumption
Control: source-head-SHA concurrency with `cancel-in-progress: true`.

### Risk: required-check + path-filter interaction
GitHub documents that a skipped path-filtered required workflow may remain Pending. F-007 does not change repository branch-protection settings. If `full-suite` is later configured as required, its path scope must remain aligned with what maintainers intend to require; no administration change is part of this ticket.

## Non-goals

- no runtime code changes;
- no test-semantic changes;
- no removal of focused gates;
- no branch-protection settings change;
- no dependency caching in this ticket;
- no switch away from unittest or GitHub Actions.

## Conclusion

The duplicate full-suite ownership is measurable and avoidable. Centralizing full discovery into one 3.10/3.12 workflow reduces runner duplication substantially while retaining stronger, clearer ownership: feature workflows answer their specific contract questions; `full-suite` alone answers whether the repository as a whole remains green.
