# F-015 plan — direct validation source-model preflight

**Issue:** #87  
**Research:** `docs/research/F-015-direct-validation-source-boundary.md`

## Scope

Make `validate_source(data, ...)` enforce the same ontoTF JSON-value and `MAX_SOURCE_NESTING=128` boundary as `loads_source()` before **instance** JSON Schema validation.

Production scope is limited to `src/ontotf/source_validation.py`. No schema files, semantic validator, digests, compatibility, ontology, filesystem code, or public signatures change.

## Implementation

Preserve existing schema-authority precedence: resolve `schema_name`, read/parse the selected schema, and run `Draft202012Validator.check_schema(schema)` exactly as today. An invalid schema must still report `invalid_schema` regardless of the supplied instance; schema-side recursion remains F-016.

After successful schema self-validation and immediately before constructing/iterating the instance validator:

1. compute `effective_source_name = schema_name if source_name is None else source_name`;
2. normalize/preflight `data` with `_plain_json(data, source_name=effective_source_name)`;
3. pass that normalized value to `validator.iter_errors()`;
4. reuse `effective_source_name` for ordinary schema-validation diagnostics.

Do not catch `RecursionError` around `Draft202012Validator.check_schema()` or `iter_errors()` in this ticket. Schema-side recursion belongs to F-016.

## RED tests

Add `tests/f015/test_direct_validation_source_boundary.py` before production edits.

Use a valid normalized-record evidence fixture because `reviewed_content` is structurally unconstrained by the evidence schema. Build nested dictionary chains so the complete evidence document has:
- total container depth 128: accepted;
- total container depth 129: `decode_error`, source name preserved.

Additional direct-call RED cases:
- recursive dict/list alias -> `non_json_value`;
- non-string nested key -> `non_json_value`;
- non-finite nested float -> `non_json_value`;
- tuple/unsupported nested value -> `non_json_value`.

Controls:
- shallow valid normalized evidence remains valid;
- shallow schema-invalid evidence still reports `schema_validation` with the same instance/schema paths;
- omitted `source_name` still defaults diagnostics to schema name;
- an invalid selected schema still reports `invalid_schema` before direct-instance preflight;
- existing F-006 loader boundary remains unchanged.

## CI

Add `.github/workflows/f015-direct-validation-boundary.yml` with:
- exact-head checkout;
- actions/checkout@v5 + setup-python@v6;
- Python 3.10/3.12;
- editable install + `build`;
- focused `tests/f015`;
- `tests/f006` loader-depth regressions;
- `tests/i001` structural validation regressions.

Do not add another generic full-repository discovery command; F-007 `full-suite.yml` remains the sole owner.

## GREEN acceptance

- direct depth 129 is rejected before instance jsonschema traversal;
- depth 128 remains valid;
- all direct non-JSON/alias cases use established ontoTF diagnostics;
- invalid schema authority retains existing precedence;
- shallow schema diagnostics/provenance remain unchanged;
- F-006/I-001 and authoritative full suite are green on the exact final head;
- fresh logically-independent adversarial review passes the exact final head.