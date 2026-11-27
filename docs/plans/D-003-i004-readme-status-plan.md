# D-003 plan — document shipped I-004 semantic validation

**Issue:** #101  
**Research:** `docs/research/D-003-i004-readme-status.md`

## Scope

Documentation and documentation-contract tests only.

Allowed implementation files:
- `README.md`;
- `tests/docs/test_readme_status.py`;
- focused D-003 workflow if needed.

No `src/**`, schema, digest, ontology, semantic-validator, packaging, or runtime behavior changes.

## Contract migration

The current docs test encodes the now-stale pre-I-004 state by:
- accepting/requiring `not yet shipped` or `not yet implemented` around cross-artifact semantic validation;
- forbidding `cross-artifact semantic validation is implemented`.

D-003 must not simply delete those assertions. Before README changes, replace them with a positive durable contract that distinguishes:

### Shipped
- an implemented-capability section named `Cross-artifact semantic validation`;
- public `SemanticSourceBundle` surfaced;
- public `validate_semantic_bundle` surfaced;
- semantic validation described as cross-artifact validation of authored semantic source bundles, not merely structural JSON Schema validation.

### Still future/unshipped
README must continue to identify these as later stages:
- compatibility evaluation;
- semantic IR/compiler;
- runtime resolution/query execution;
- corpus-specific mapping releases.

The test should reject stale statements that semantic validation itself is not shipped/not implemented, but should not forbid generic `not yet shipped` wording when it clearly describes a genuinely future surface.

## RED phase

First edit only `tests/docs/test_readme_status.py` (plus a focused workflow if introduced).

Required RED assertions:
1. `Cross-artifact semantic validation` is named among implemented capabilities;
2. README contains `SemanticSourceBundle`;
3. README contains `validate_semantic_bundle`;
4. stale phrases tying `cross-artifact semantic validation` to `not yet shipped` / `not yet implemented` are absent;
5. future-work prose still contains compatibility evaluation, semantic IR/compiler, runtime resolution, and corpus-specific mappings;
6. existing structural/canonicalization/parent identity/install/API-name controls remain.

The current README must fail the new positive semantic-validation checks while unrelated existing controls pass.

Avoid exact full-paragraph matching. Where negation is checked, use a small list of the known stale fragments rather than banning every occurrence of words like `not yet shipped`.

## GREEN README changes

After RED is observed:

1. Current status:
   - change three production foundations to four;
   - add cross-artifact semantic validation;
   - remove claim that validator is not implemented;
   - leave compatibility, IR/compiler, runtime resolution and corpus-specific mappings as future work.

2. Implemented capabilities:
   - add `### Cross-artifact semantic validation` after parent/component identity or another logical location;
   - describe deterministic bundle validation at a stable conceptual level: component/dependency authority, controlled semantic states/vocabulary, projections/candidates, target/lock/bundle closure, evidence/review/digest binding, native semantics and policy legality;
   - name `SemanticValidationError` only if useful; do not dump internal helper details.

3. Accepted semantic architecture:
   - retain architectural explanation;
   - replace `not yet shipped cross-artifact semantic validation` with wording that says the validator is implemented but later compatibility/compiler/runtime stages remain future.

4. Minimal usage:
   - add a schematic public API example importing `SemanticArtifact`, `SemanticSourceBundle`, and `validate_semantic_bundle`;
   - do not pretend placeholder dictionaries are a complete executable bundle; label the example as assembly shape or use comments/ellipsis clearly.

## CI

Add `.github/workflows/d003-readme-i004-status.yml` only if a focused exact-head workflow is needed. It should:
- use actions/checkout@v5 and setup-python@v6;
- run Python 3.10/3.12;
- install package + `build`;
- run `tests/docs`;
- avoid duplicating the generic repository-wide test command owned by `full-suite.yml`.

Existing D-001/readme workflow and centralized full suite remain regression owners; final PR CI should include them via path filters.

## GREEN acceptance

- focused docs tests green;
- existing README/status tests are migrated, not skipped/xfail'd;
- current public API names in README match `src/ontotf/__init__.py`;
- no runtime/source changes;
- exact-head PR CI/full suite green;
- fresh logically-independent adversarial review confirms README neither understates I-004 nor overstates compatibility/runtime/corpus-mapping capabilities.

Any material head change invalidates final review.
