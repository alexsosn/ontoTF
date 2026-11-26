# F-016 implementation plan — contain custom schema recursion failures

**Issue:** #88  
**Research:** `docs/research/F-016-custom-schema-recursion-boundary.md`  
**Baseline:** `main` `ef3e92b5da52d4f4762c4162e1d2769077470cd3`

## 1. Goal

Keep recursion failures attributable to schema parsing/validation inside ontoTF's existing `invalid_schema` authority boundary, without introducing a ontoTF schema-depth limit or changing source-instance depth policy.

F-015 is now merged, so direct programmatic instance values are normalized/preflighted before `Draft202012Validator.iter_errors()`. A `RecursionError` that escapes after that preflight can therefore be attributed to schema/validator traversal for this ticket.

## 2. Public contract

Translate only these schema-side `RecursionError` boundaries to `SourceValidationError(category="invalid_schema")` with the selected schema's existing `schema_source_name` provenance:

1. schema UTF-8/JSON parse block (`json.loads(...)`);
2. `Draft202012Validator.check_schema(schema)`;
3. consumption of `validator.iter_errors(normalized_data)` / sorting of yielded validation errors after F-015 preflight.

Use one stable ontoTF-owned message for all three, e.g. `schema validation exceeded recursion capacity`. Tests must assert category and provenance; message equality may be asserted only to keep the ontoTF-owned diagnostic stable, never interpreter recursion text.

Do not catch `RecursionError` from source normalization `_plain_json()`: F-015/F-006 own that source-side boundary.

## 3. Explicit non-design

F-016 must not:

- add `MAX_SCHEMA_NESTING`;
- reuse `MAX_SOURCE_NESTING` for schemas;
- mutate `sys.setrecursionlimit()`;
- pre-walk schema container depth;
- catch `Exception`, `RuntimeError`, or another broad superclass;
- change JSON Schema draft/version or schema contents;
- change F-019/F-020 filesystem-path boundaries;
- change packaged-resource acquisition;
- add remote `$ref` fetching/resolution behavior.

The superseded `research/f-016-custom-schema-recursion` fixed-depth design is not an implementation source.

## 4. RED test design

Create `tests/f016/test_custom_schema_recursion_containment.py` with deterministic injection rather than relying on interpreter depth thresholds.

### RED-A — schema JSON parser recursion

With a real explicit schema file present, patch `ontotf.source_validation.json.loads` to raise `RecursionError` only at the schema parse call. Assert:

- `validate_source(...)` raises `SourceValidationError` rather than raw `RecursionError`;
- category is `invalid_schema`;
- `source_name` is the exact explicit schema file path;
- stable ontoTF recursion message is used.

### RED-B — `check_schema()` recursion

Patch `Draft202012Validator.check_schema` to raise `RecursionError` after a valid Draft 2020-12 schema has parsed. Assert the same `invalid_schema` category and schema provenance.

### RED-C — validator traversal recursion

Use a valid shallow direct instance that passes `_plain_json()`. Patch `Draft202012Validator.iter_errors` to return a generator/iterator whose creation succeeds but whose first advancement raises `RecursionError`. The failure must therefore occur lazily when `sorted(...)` consumes the iterator, not when `iter_errors()` is called. Assert:

- raw recursion does not escape;
- category is `invalid_schema`;
- provenance names the schema, not the instance;
- `iter_errors()` was actually called after source preflight;
- the injected iterator was advanced, proving the catch covers recursive traversal/consumption rather than only method invocation.

Add a control where the direct instance itself is recursively aliased/non-JSON and `iter_errors` is patched to fail if called; existing F-015 source-side category/provenance must win and the validator traversal must not be reached.

## 5. Regression controls

Pin existing behavior for:

- invalid UTF-8 custom schema -> `invalid_schema`;
- malformed JSON custom schema -> `invalid_schema`;
- ordinary `SchemaError` -> `invalid_schema` with its existing `instance_path` / `schema_path` diagnostics;
- valid explicit schema + invalid instance -> `schema_validation` with instance provenance;
- packaged canonical schema validation unchanged;
- F-006 deep source and F-015 direct source-boundary tests unchanged;
- F-019 invalid source path and F-020 invalid schema-root path tests unchanged;
- I-001/I-004 source/semantic validation regressions unchanged.

## 6. TDD gate

Tests and focused workflow land before production changes.

The tests-only RED head must show:

- the three intended recursion tests failing because raw `RecursionError` escapes;
- all controls green;
- no production file changed.

Because this defect is interpreter/library recursion behavior rather than OS filesystem behavior, the mandatory focused compatibility matrix is Python 3.10 and 3.12 on Ubuntu 24.04. Windows-specific semantics are not part of the contract; existing full/overlapping workflows remain regression gates. If RED reveals platform-specific behavior, expand the matrix before GREEN rather than weakening the assertion.

## 7. Minimal GREEN

Production should remain confined to `src/ontotf/source_validation.py`.

Preferred shape:

- add a small private helper such as `_raise_schema_recursion(schema_source_name)` only if it prevents repeated literal diagnostic construction;
- add `except RecursionError` to the schema parse block;
- add a sibling `except RecursionError` after the existing `SchemaError` branch around `check_schema()`;
- wrap only the `sorted(validator.iter_errors(...), key=...)` consumption in `try/except RecursionError`.

Do not wrap `normalized_data = _plain_json(...)` or the whole function.

## 8. Exact-head verification

Before final review require on the exact merge candidate:

- focused F-016 Python 3.10/3.12 GREEN;
- F-006 and F-015 source-boundary regressions green;
- F-019/F-020 path-boundary regressions green;
- I-001/I-004 validation regressions green;
- packaging/schema-authority controls green;
- authoritative full repository suite green;
- compare against then-current `main` shows only this plan/tests/workflow plus the narrow `source_validation.py` delta.

If `main` advances materially, integrate it and repeat exact-head CI.

## 9. Independent adversarial review

Fresh exact-head review must attack at least:

- accidental fixed schema-depth policy;
- catch broadening to source `_plain_json()` recursion;
- wrong provenance (`source_name` instead of schema source);
- wrong category (`decode_error` or `schema_validation`);
- ordinary `SchemaError` path diagnostics being lost;
- `iter_errors()` recursion being caught before F-015 preflight;
- packaged/custom schema behavior divergence introduced accidentally;
- catching interpreter recursion outside known third-party schema operations;
- tests that merely monkeypatch the public function and can pass without exercising the intended boundary.

Any blocker returns to RED -> minimal GREEN -> exact-head CI -> fresh review.

## 10. Exit condition

F-016 completes when schema-side recursion at parse, meta-schema validation, or post-preflight validator traversal is deterministically contained as `invalid_schema` with schema provenance, source-side recursion contracts remain unchanged, no schema-depth ceiling is introduced, exact-head regressions are green, and a fresh logically-independent adversarial review finds no blocker.
