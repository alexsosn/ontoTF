# F-006 research: fail closed on excessively deep source nesting

**Issue:** #32  
**Recorded:** 2026-09-07  
**Scope:** source-loading stability only; no schema, semantic, canonicalization, or digest changes.

## 1. Existing public contract

`src/ontotf/source_validation.py` already normalizes source-loading failures into `SourceValidationError` with stable categories:

- `decode_error` for syntax/decoding/source-format failures;
- `duplicate_key` for duplicate object/mapping keys;
- `non_json_value` for parsed values that cannot be represented as plain JSON values.

`_plain_json()` recursively copies parser output, rejects recursive aliases, non-string mapping keys, non-finite floats, and unsupported Python value types. It has no explicit depth guard and `loads_source()` does not catch `RecursionError`.

Therefore sufficiently deep input can escape the public fail-closed boundary as a raw interpreter/parser exception.

## 2. Python JSON behavior

CPython's `json` documentation states that the standard decoder does not impose a maximum nesting limit beyond limits of Python data types/interpreter. `RecursionError` is the interpreter's standard signal when maximum recursion depth is exceeded.

Consequences:

1. ontoTF cannot rely on `json.loads()` to provide a portable source nesting policy.
2. A raw `RecursionError` is an implementation/resource-limit failure, not part of ontoTF's public source-loading API.
3. Catching only `JSONDecodeError`/`ValueError` is insufficient.

Primary sources:
- https://docs.python.org/3.12/library/json.html — implementation limitations;
- https://docs.python.org/3.12/library/exceptions.html#RecursionError.

## 3. ruamel.yaml behavior

ontoTF pins `ruamel.yaml>=0.19.1,<0.20` and uses `YAML(typ="safe", pure=True)`.

Current ruamel.yaml 0.19.x documents a `YAML.max_depth` setting that makes excessive recursion fail during loading with a dedicated depth error. This is useful parser hardening, but it should not be ontoTF's only nesting contract because:

- JSON has no matching parser-level limit;
- `_plain_json()` still recursively traverses parsed containers;
- a single source policy should apply to both formats;
- ontoTF should not expose parser-specific exception classes/categories.

Primary source:
- https://yaml.dev/doc/ruamel.yaml/ and ruamel.yaml 0.19.x release notes.

## 4. Public error category

Choose **`decode_error`** for excessive source nesting.

Rationale:

- the source is rejected at the loading/decoding boundary before schema validation;
- excessive nesting is an unsupported source-document shape/resource condition, not a valid parsed JSON value with an illegal scalar/container type;
- `non_json_value` remains reserved for successfully parsed Python values that violate ontoTF's JSON-value contract (recursive aliases, non-string keys, non-finite values, unsupported types);
- callers already treat `decode_error` as source-input failure.

Stable message prefix:

`source nesting exceeds maximum depth <N>`

Exact parser exception text must not become API.

## 5. Deterministic nesting policy

Introduce one ontoTF-owned constant:

`MAX_SOURCE_NESTING = 128`

Depth definition:

- root scalar: depth 0;
- root list/dict: depth 1;
- each nested list/dict increments depth by one;
- scalars inside a depth-N container do not add another container level.

Why 128:

- comfortably below CPython recursion limits, so ontoTF rejects deterministically before `_plain_json()` approaches interpreter recursion exhaustion;
- far above the depth required by current schemas and ordinary mapping/evidence/profile sources;
- format-independent and cheap to enforce;
- intentionally a source-safety ceiling, not a semantic/schema constraint.

Changing this constant later is a source-loading policy change but does not change semantic digests for accepted documents.

## 6. Enforcement strategy

Use defense in depth:

1. `_plain_json()` receives a `depth` parameter and rejects any parsed list/dict whose container depth would exceed `MAX_SOURCE_NESTING` with `SourceValidationError(category="decode_error")`.
2. JSON `loads_source()` catches `RecursionError` from `json.loads()` and normalizes it to the same stable depth failure.
3. YAML sets `parser.max_depth = MAX_SOURCE_NESTING` when supported by the pinned 0.19.x API, and catches parser depth/recursion failures as the same stable `decode_error`.
4. `_plain_json()` remains the format-independent final authority; parser-level limits are only earlier resource protection.

Do not increase Python's recursion limit and do not truncate/flatten input.

## 7. RED / control cases

RED must prove on pre-fix main:

- deeply nested JSON leaks `RecursionError` (or otherwise bypasses stable ontoTF depth handling);
- deeply nested YAML does not produce the planned stable ontoTF depth error;
- ordinary nested JSON/YAML well below the limit round-trip to identical plain values;
- duplicate keys keep `duplicate_key`;
- non-finite values keep existing categories;
- recursive YAML aliases remain `non_json_value`, not reclassified as depth.

Boundary tests after GREEN:

- exactly `MAX_SOURCE_NESTING` containers accepted;
- `MAX_SOURCE_NESTING + 1` rejected in JSON and YAML with `decode_error` and source name preserved.

## 8. Non-goals

- no source byte-size limit;
- no scalar/string length limit;
- no schema recursion changes;
- no YAML parser replacement;
- no canonicalization/digest changes;
- no semantic interpretation;
- no global `sys.setrecursionlimit()` changes.

## Conclusion

F-006 should add a small, format-independent source nesting ceiling and normalize parser/interpreter recursion failures into the existing `decode_error` contract. Parser-specific depth controls may be used as an optimization/early guard, but `_plain_json()` remains the deterministic cross-format policy boundary.
