# F-008: retire stale P-001 repository-state assertion

**Status:** research complete  
**Issue:** #66  
**Recorded:** 2026-09-07  
**Type:** test-suite maintenance / stability

## Question

What invariant was `tests/plans/test_p001_plan.py::P001FoundationDesignContractTests::test_design_ticket_contains_no_production_artifacts` intended to enforce, and how should it survive after production implementation legitimately added `src/`, `schemas/`, and related artifacts?

## Evidence

### P-001 itself is explicitly design-only

`docs/plans/P-001-foundation-poc-design.md` states:

- scope: `design only; no production schemas, profiles, compiler, resolver, or MCP implementation`;
- under **Future production layout**: `This design PR does not create these directories. Implementation tickets will create them after this plan is accepted.`

Therefore the intended invariant is about the **P-001 design change**, not an eternal property of the repository after implementation begins.

### The merged P-001 PR changed only design/test/CI paths

Merged PR #13 changed exactly:

- `.github/workflows/p001-plan-validation.yml`
- `docs/plans/P-001-foundation-poc-design.md`
- `tests/plans/test_p001_plan.py`

It did not add production paths.

### I-001 intentionally begins the production phase

Immediately after P-001, I-001 introduced production implementation. In particular:

- commit `d12a7be3a72ef48caaf61b0333c6564d4962572d` added the package scaffold and configured setuptools to find packages under `src`;
- commit `e89470f3015fa41c1ee7262960fd9aa520801e71` implemented I-001 structural validation and added `src/ontotf/**` plus production schemas.

The later merged I-001 implementation therefore makes repository-level assertions such as `assert not (ROOT / "src").exists()` permanently invalid.

## Failure mode

The current test checks repository state at test execution time:

```python
self.assertFalse((ROOT / "schemas").exists())
self.assertFalse((ROOT / "profiles").exists())
self.assertFalse((ROOT / "src").exists())
```

This turns a phase-local review condition into a time-dependent global invariant. Once legitimate implementation lands, a historical design test begins failing even though P-001 itself has not changed.

This is a test design bug, not a production regression.

## Preserved invariant

The useful invariant is:

> A design-only P-001 change must not itself introduce production artifacts.

That is naturally expressed over the **changed-path set of the design change**, not over the current repository tree.

For the historical P-001 contract, production-path families are:

- `src/**`
- `schemas/**`
- `profiles/**`

A design-only changed-path set containing one of those families violates the historical scope. The existence of those paths elsewhere in the current repository is irrelevant.

## Recommended replacement

Use a small deterministic path-classification helper in test code:

```text
changed paths -> production-scope violations
```

Then test both:

1. the actual historical P-001 PR #13 changed-path set has no production-scope violation while the current repository may legitimately contain `src/`;
2. a synthetic design change that adds `src/...`, `schemas/...`, or `profiles/...` is rejected.

This preserves the meaningful design boundary without querying GitHub at test runtime, pinning a whole historical tree, or weakening the suite with skip/xfail.

## Alternatives rejected

- **Delete the test entirely:** loses a still-useful historical scope invariant.
- **Skip/xfail:** hides a known stale assertion instead of repairing it.
- **Check an old commit/tree at runtime:** brittle and requires VCS/network/history availability in ordinary test execution.
- **Assert current production directories are absent:** already disproved by the accepted implementation phase.
- **Hard-code that only the three historical files may ever be touched:** too narrow; the semantic invariant is absence of production artifacts, not exact file-count identity.

## Conclusion

F-008 should replace the repository-state assertion with a pure changed-path scope contract. No production code or semantic architecture should change.
