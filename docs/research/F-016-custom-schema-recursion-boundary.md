# F-016 research — custom schema recursion failure boundary

**Issue:** #88  

## Question

`validate_source(..., schema_root=...)` accepts caller-supplied JSON Schema files. ontoTF currently translates ordinary schema decoding and `SchemaError` failures into `SourceValidationError(category="invalid_schema")`, but raw `RecursionError` can escape from schema JSON decoding, `Draft202012Validator.check_schema()`, or later recursive schema traversal.

This research asks whether ontoTF should impose a deterministic schema nesting limit, or instead preserve the JSON Schema language while translating recursion failures at the third-party boundary.

## Current boundary

The source-value contract and the schema contract are separate:

- F-006 defines `MAX_SOURCE_NESTING = 128` for source JSON/YAML values and maps source parsing/depth failures to `decode_error`.
- `validate_source()` loads the selected schema separately, requires Draft 2020-12, calls `Draft202012Validator.check_schema(schema)`, then validates the instance.
- custom schema read/decode/meta-schema failures already use `invalid_schema` and the schema file path as `source_name`.

A schema recursion failure is therefore not a source decoding failure and must not be reported as `decode_error`.

## External evidence

`jsonschema` documents `Draft202012Validator.check_schema(schema)` as validation of the schema against the validator meta-schema, raising `SchemaError` for ordinary invalid schemas. The validator API also exposes recursive `descend()` / `iter_errors()` traversal. Upstream issue python-jsonschema/jsonschema#847 records raw `RecursionError` arising through `check_schema()` / recursive validator descent. The historical issue was connected to draft-specific recursive-reference behavior, demonstrating that `SchemaError` is not the only possible failure class at this boundary.

The current jsonschema API documentation still describes `check_schema`, `descend`, and `iter_errors`; it does not promise that arbitrarily deep or recursive schema graphs are converted to `SchemaError`.

## Decision: no ontoTF schema-depth ceiling in this ticket

Do **not** reuse `MAX_SOURCE_NESTING` for schemas and do not introduce `MAX_SCHEMA_NESTING` without separate evidence.

Reasons:

1. F-006's 128 ceiling is a ontoTF source-model policy, not a JSON Schema language limit.
2. JSON Schema composition depth is not semantically equivalent to instance/source nesting depth. Legitimate schemas may be generated or deeply composed.
3. A fixed schema-depth preflight would reject schemas before the selected Draft 2020-12 validator evaluates their actual semantics, creating a new compatibility restriction unrelated to the observed error-boundary defect.
4. Recursion can arise from reference/composition traversal rather than literal JSON container depth, so a container-depth check would not close the whole failure class anyway.

The narrow contract is therefore exception containment, not a new schema language subset.

## Required public error contract

For custom or packaged schemas:

- schema bytes UTF-8/JSON decoding failure → existing `invalid_schema`;
- schema JSON parser `RecursionError` → `invalid_schema` at the schema source name;
- `Draft202012Validator.check_schema()` `RecursionError` → `invalid_schema` at the schema source name;
- schema-driven `validator.iter_errors()` `RecursionError`, once the source value has passed the F-015 direct-validation preflight, → `invalid_schema` at the schema source name.

Use a stable message such as `schema validation exceeded recursion capacity`; callers must branch on category, not message text.

Do not catch `Exception` broadly. The new boundary is specifically `RecursionError` in the known recursive schema operations.

## Dependency on F-015

The `iter_errors()` case is intentionally blocked on F-015.

Before F-015, a raw `RecursionError` during `validator.iter_errors(data)` is ambiguous: it can be caused by a direct programmatic instance that bypassed the F-006 source-depth/model preflight, or by schema traversal. Labeling every such failure `invalid_schema` would misattribute an invalid/deep source value to the schema.

F-015 establishes the direct-instance preflight. Only after that lands can F-016 safely say that a remaining recursion escaping `iter_errors()` is on the schema/validator side of the contract.

The parse and `check_schema()` boundaries are independently attributable today, but splitting production changes before F-015 would create two temporary recursion policies in the same function and force immediate reintegration in the same hot file. The safer implementation sequence is to wait for F-015, then add all three narrow schema-side translations in one TDD slice.

## TDD plan seed after F-015 lands

A future implementation plan should require RED tests before code for:

1. custom schema JSON decoding recursion translated to `invalid_schema`, preserving the custom schema pathname;
2. injected/deterministic `Draft202012Validator.check_schema()` `RecursionError` translated to `invalid_schema`, preserving schema pathname;
3. deterministic schema-driven `iter_errors()` recursion translated to `invalid_schema` only after the direct instance preflight passes;
4. ordinary `SchemaError` paths/diagnostics unchanged;
5. malformed UTF-8/JSON schema diagnostics unchanged;
6. packaged canonical schemas continue to validate ordinary shallow inputs unchanged;
7. F-015 source-depth/non-JSON diagnostics retain their source-side categories and provenance;
8. full I-001/I-004/packaging regressions green on Python 3.10 and 3.12.

Tests should prefer deterministic injected recursion at the third-party boundary over depending exclusively on interpreter recursion thresholds. One real deep/composed-schema characterization case may be retained as a control, but must not define the public threshold.

## Non-goals

- no schema redesign or new JSON Schema draft;
- no schema nesting limit;
- no global recursion-limit changes;
- no broad exception swallowing;
- no change to source depth policy;
- no semantic I-004 behavior change;
- no remote schema fetching/resolution feature.

## Gate result

The defect is implementable, but the complete and correctly attributed implementation is **blocked on F-015** because both changes meet at `validate_source()` and F-015 is what makes post-preflight `iter_errors()` recursion attributable to schema traversal.

Stop after research in this branch. After F-015 merges, create/update the implementation plan, add deterministic RED tests, implement the narrow `RecursionError → invalid_schema` boundaries, run exact-head CI, and perform a fresh logically-independent adversarial review.