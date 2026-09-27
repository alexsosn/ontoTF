# I-016 plan amendment — schema registry regression ownership

**Issue:** #204  
**Amends:** `docs/plans/I-016-seven-corpus-coverage-manifests.md`  
**Trigger:** exact-head CI on implementation PR #210, head `1830510c31c92fa01c5fe17b3acd3edbf38d47bb`

## Finding

The accepted I-016 plan requires a new registered source schema:

`coverage-manifest.schema.json`

and explicitly requires it to be added to `source_validation.SCHEMA_FILES`.

Existing I-001 regression `tests/i001/test_source_validation.py::test_registry_and_all_seven_schema_files_exist` freezes the historical registry cardinality and exact seven-name set. After adding the required I-016 schema, this regression correctly fails because the source-validation registry now contains eight schemas.

The original I-016 implementation file allowlist omitted `tests/i001/**`, so silently editing that regression would violate the reviewed implementation scope.

This is a plan integration gap, not a reason to avoid registering the coverage schema.

## Amendment

Authorize the minimal I-001 regression update required by the already-accepted I-016 source contract:

- update `tests/i001/test_source_validation.py` so the registry expectation includes `coverage-manifest`;
- rename/reword the test if necessary so it does not encode a historical cardinality in its name;
- preserve all existing I-001 schema validation behavior for the seven pre-I-016 schemas;
- do not weaken unknown-schema, schema-root, recursion, source-boundary, duplicate-key, JSON/YAML normalization, or schema self-validation tests.

The implementation may therefore additionally modify:

- `tests/i001/test_source_validation.py`

No other pre-I-016 test module is authorized by this amendment unless a separate reviewed amendment demonstrates another genuine contract integration gap.

## TDD / CI consequence

The already-observed exact-head failure is the RED integration signal:

`Items in the first set but not the second: 'coverage-manifest'`.

GREEN requires:

1. I-001 focused suite passes with all eight registered schemas;
2. F-002/F-015/F-016/F-019/F-020 schema/source boundary regressions remain green;
3. I-016 focused suite passes;
4. full repository suite passes on the exact final head.

The independent final review must verify that the I-001 change is only an additive registry-contract update and does not weaken source validation.

## Separate test-authoring defect

The I-016 test syntax error introduced while applying the accounting-gap amendment is not a production design change. It must be corrected on the implementation branch before GREEN, without changing the intended assertion:

Syriac has exactly one production accounting gap, `node_value:ls="prop"`.

