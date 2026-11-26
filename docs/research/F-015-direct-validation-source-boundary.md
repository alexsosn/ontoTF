# F-015 research — direct validation must enforce the source-value boundary

**Issue:** #87  
**Baseline:** `main` `789b9fb076c03ed99f3cef05038763540695e127`

## Question

Should callers of `validate_source(data, schema_name, ...)` be able to bypass the JSON-model and depth checks that apply when the same value enters through `loads_source()` / `load_source()`?

## Existing behavior

F-006 established one public source nesting ceiling, `MAX_SOURCE_NESTING = 128`, and `_plain_json()` enforces it while also rejecting recursive aliases, non-finite floats, non-string mapping keys and non-JSON value types.

`loads_source()` parses text and then calls `_plain_json(parsed, ...)`.

`validate_source()` currently does not. It sends caller-provided `data` directly to `Draft202012Validator.iter_errors()`. This means the same logical source object has different admissibility depending on whether it came from text or was constructed in Python.

The bypass is observable even without exhausting Python recursion: structurally loose schema fields such as mapping `native_selector` / `applicability` can contain arbitrarily deep nested objects that JSON Schema does not need to descend through. Text input at depth 129 is rejected by F-006, while the same programmatic value can reach or pass schema validation.

## Upstream validator behavior

`jsonschema` validators recurse through schema/instance structure via validator descent. Historical upstream issue python-jsonschema/jsonschema#847 demonstrates raw `RecursionError` escaping recursive validation. This is additional reason not to let unbounded programmatic values bypass ontoTF's own source boundary.

References:
- jsonschema validator/error documentation: https://python-jsonschema.readthedocs.io/
- upstream recursion report: https://github.com/python-jsonschema/jsonschema/issues/847

## Decision

`validate_source()` is a public source-validation entrypoint and must enforce the same ontoTF JSON-value contract as the loaders.

Before constructing/iterating the JSON Schema validator:

1. compute the effective source identity (`schema_name` when `source_name` is omitted, otherwise the supplied source name);
2. call `_plain_json(data, source_name=effective_source_name)`;
3. validate the returned plain JSON value, not the unchecked input object.

Reusing `_plain_json()` is preferable to adding a second traversal because it makes loader and direct-call behavior identical for:
- maximum depth 128;
- recursive-container aliases;
- non-finite numbers;
- mapping key types;
- unsupported Python values;
- list/dict subclasses, which are normalized to ordinary JSON containers.

The copy is intentional normalization, not a semantic mutation. Direct callers already promise `JSONValue`; the returned value is the canonical runtime representation that text loaders already produce.

## Error contract

Use the existing `_plain_json()` categories unchanged:
- depth >128: `decode_error` with `source nesting exceeds maximum depth 128`;
- recursive alias / unsupported value / non-string key / non-finite YAML-like value: `non_json_value`.

For direct validation, `ValidationProblem.source_name` uses the same effective identity later used for schema-validation diagnostics.

This means a direct call without `source_name` reports `schema_name`, preserving the current default provenance behavior.

## Do not catch all validator recursion as source depth

After preflight, official ontoTF source values are bounded at 128. A remaining `RecursionError` may instead be caused by a deeply/recursively structured custom schema. Translating that to source `decode_error` would misdiagnose the failing authority.

Custom `schema_root` recursion is therefore a separate defect/research lane: F-016 (#88).

## TDD strategy

Use a structurally valid mapping fixture whose `native_selector` contains a nested object/list chain. The mapping schema intentionally treats the selector as an opaque object structurally, so this proves the direct-call bypass independently of jsonschema recursion details.

Required boundary cases:
- exactly 128 total containers accepted;
- 129 rejected before schema validation;
- recursive list/dict alias rejected;
- non-string key, non-finite float, tuple/unsupported object rejected;
- shallow invalid schema instance still produces the same `schema_validation` paths/provenance;
- loader F-006 behavior remains unchanged.

Depth accounting must reuse `_plain_json()` exactly; do not invent a second definition.

## Production scope

Only `src/ontotf/source_validation.py` should change, ideally a few lines at the start of `validate_source()` plus use of the normalized value in `iter_errors()`.

No schema, I-004 semantic, digest, ontology, compatibility or filesystem behavior changes.

## Conclusion

Direct validation is not a privileged bypass around the source model. It must normalize/preflight through `_plain_json()` before JSON Schema validation, while schema-side recursion remains separately classified under F-016.