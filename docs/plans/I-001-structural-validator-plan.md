# I-001 structural schemas and source validator plan

**Issue:** #14  
**Recorded:** 2026-09-05  
**Research dependency:** `docs/research/I-001-structural-validator-research.md` at commit `8e28ff2d0171aa038d5f91b09c40c4aa4c627aa5`  
**Design dependency:** P-001 reviewed head `ae6907b3140798421f773e74104f3a9434a34d5c`, merged as `e9ab50a759ba72c89047704ac70958fce6376951`

## 1. Scope

I-001 implements only the **parse + structural JSON Schema validation** stage of P-001.

It creates:

- the first minimal Python package scaffold;
- seven Draft 2020-12 schemas;
- strict YAML/JSON loading into a plain JSON-compatible Python data model;
- a local schema registry/loader;
- typed structural validation errors;
- focused positive/negative contract fixtures and CI.

It does not calculate any semantic/content digest, resolve cross-file references, inspect parent corpus bytes, evaluate ontology terms, prove review bindings, calculate compatibility, compile semantic IR, resolve queries, or generate documentation.

## 2. Repository layout

```text
pyproject.toml
schemas/
  profile.schema.json
  parent-component-manifest.schema.json
  ontology-lock.schema.json
  evidence.schema.json
  review.schema.json
  mapping.schema.json
  compatibility-report.schema.json
src/ontotf/
  __init__.py
  source_validation.py
tests/i001/
  __init__.py
  test_source_loading.py
  test_schema_contracts.py
  fixtures/
    valid/*.yaml
    invalid/*.yaml
.github/workflows/i001-validation.yml
```

Root `schemas/` remains the single canonical schema source per P-001. `source_validation.py` accepts an explicit `schema_root`. In a repository checkout its default is the repository `schemas/` directory discovered relative to the module. Shipping schemas inside a standalone wheel is not solved by copying them into a second package location in I-001; distribution packaging may later add a non-duplicating resource strategy.

## 3. Python/package baseline

`pyproject.toml` uses a minimal setuptools build and:

```toml
requires-python = ">=3.10"
dependencies = [
  "jsonschema>=4.26,<5",
  "ruamel.yaml>=0.19.1,<0.20",
]
```

No Text-Fabric, RDF, HTTP, CLI-framework, or ontology dependencies enter this ticket.

The package public surface exported by `ontotf` is intentionally small:

```python
SourceValidationError
load_source
loads_source
validate_source
load_and_validate
```

No CLI is required in I-001.

## 4. JSON-compatible data model

The loader returns only recursively plain JSON-compatible Python values:

```text
None | bool | int | finite float | str | list[JSONValue] | dict[str, JSONValue]
```

The recursive normalizer:

- accepts `None`, `bool`, `int`, finite `float`, `str`;
- copies sequences to plain `list`;
- copies mappings to plain `dict` only when every key is `str`;
- tracks active container object IDs and rejects recursive/cyclic aliases;
- rejects non-finite floats;
- rejects date/datetime, set, tuple, bytes, custom/tagged values, non-string mapping keys, and other objects.

The normalizer is not semantic canonicalization and does not sort mappings/arrays or normalize Unicode; I-002 owns semantic canonicalization/digests.

## 5. Strict source loading API

### 5.1 `loads_source`

```python
loads_source(text: str, *, format: Literal["yaml", "json"], source_name: str = "<memory>") -> JSONValue
```

For YAML:

- instantiate `ruamel.yaml.YAML(typ="safe", pure=True)`;
- keep `allow_duplicate_keys = False` explicitly even though it is the documented default;
- parse exactly one document;
- reject an empty document unless the caller's schema later explicitly accepts `None` (the loader itself may return `None` for YAML `null`);
- catch duplicate-key exceptions separately from generic parse errors;
- pass the parsed value through the JSON-compatible normalizer.

For JSON:

- use `json.loads` with `object_pairs_hook` that constructs a dict while rejecting duplicate names;
- use `parse_constant` that rejects `NaN`, `Infinity`, and `-Infinity`;
- pass the value through the same JSON-compatible normalizer.

Unsupported format is a stable decode/configuration error; no filename sniffing happens inside `loads_source`.

### 5.2 `load_source`

```python
load_source(path: str | Path) -> JSONValue
```

- read raw bytes;
- decode UTF-8 strictly, allowing no replacement characters;
- select YAML for `.yaml`/`.yml`, JSON for `.json`;
- reject unsupported suffixes;
- delegate to `loads_source`.

An optional UTF-8 BOM is accepted by decoding with `utf-8-sig`; line-ending normalization is not needed for parsing and source hashing belongs to I-002.

## 6. Stable error contract

```python
@dataclass(frozen=True)
class ValidationProblem:
    category: str
    message: str
    source_name: str
    instance_path: tuple[str | int, ...] = ()
    schema_path: tuple[str | int, ...] = ()

class SourceValidationError(ValueError):
    problem: ValidationProblem
```

Stable categories in I-001:

- `decode_error`;
- `duplicate_key`;
- `non_json_value`;
- `unknown_schema`;
- `invalid_schema`;
- `schema_validation`.

The exact third-party exception string is diagnostic only. Tests assert category and paths, not full library prose.

## 7. Schema registry and API

Schema names are fixed in one registry:

```python
SCHEMA_FILES = {
    "profile": "profile.schema.json",
    "parent-component-manifest": "parent-component-manifest.schema.json",
    "ontology-lock": "ontology-lock.schema.json",
    "evidence": "evidence.schema.json",
    "review": "review.schema.json",
    "mapping": "mapping.schema.json",
    "compatibility-report": "compatibility-report.schema.json",
}
```

### 7.1 `validate_source`

```python
validate_source(data: JSONValue, schema_name: str, *, schema_root: str | Path | None = None) -> None
```

Behavior:

1. resolve only a registry name, never a caller-provided remote `$ref` URL;
2. load the local schema as strict JSON using the same JSON loader;
3. require its `$schema` to be exactly Draft 2020-12;
4. call `Draft202012Validator.check_schema`;
5. instantiate `Draft202012Validator(schema)`;
6. collect validation errors, sort deterministically by instance path then schema path/message, and raise the first as `schema_validation`.

Schemas are written to avoid network resolution. Cross-schema duplication is acceptable at this stage when the alternative would require a remote/custom resolver; semantic single-source concerns apply to mapping data, not a few structural `$defs`. If common definitions become large, a later schema-maintenance ticket may introduce a local resolver/store without changing source semantics.

### 7.2 `load_and_validate`

```python
load_and_validate(path: str | Path, schema_name: str, *, schema_root: str | Path | None = None) -> JSONValue
```

Load, validate, return the plain JSON-compatible value. No mutation or semantic enrichment occurs.

## 8. Schema rules

Every schema:

- declares Draft 2020-12 in `$schema`;
- has a stable local `$id` under `https://tfont.dev/schema/v1/...` as a logical identifier only;
- uses `type`, `required`, `enum`/`const`, arrays/objects and `additionalProperties: false` where P-001 defines a closed record;
- does not fetch external schemas;
- contains only structural rules expressible without opening another source artifact.

### 8.1 Profile schema

Requires at least:

- `schema_version` integer `1`;
- `profile_id`, `profile_version` non-empty strings;
- `semantic_domains` non-empty unique string array;
- `parent_component_manifest` non-empty string;
- `required_components` non-empty unique string array;
- `ontology_locks` unique string array;
- `mapping_sources` non-empty unique string array;
- `dependency_contract_version` integer;
- `minimum_tfont_runtime`, `license` non-empty strings;
- optional object `provenance` with JSON-compatible values.

Structural schema does not prove referenced paths/IDs exist.

### 8.2 Parent component manifest schema

Requires:

- `algorithm` const `tfont-parent-components-sha256-v1`;
- non-empty `components` array;
- each component has `component_id`, `kind`, `identity_algorithm`, `content_digest`;
- component `kind` enum: `tf-payload | sidecar | catalogue | zero-span | native-adapter`;
- optional `logical_locator`, `license_ref` strings;
- component record `additionalProperties: false` so an independent `required` field is rejected.

Uniqueness of `component_id` values is cross-item semantic validation and deferred to I-004 because JSON Schema `uniqueItems` cannot express uniqueness by one object property without making whole objects identical.

### 8.3 Ontology lock schema

Requires fields from P-001: `lock_id`, `ontology_id`, `support_tier`, `term_namespace`, `release`, `source_uri`, `content_digest`, `license`, `snapshot_artifact`, `terms_used`; allows optional source revision/retrieved status metadata.

I-001 validates only shape/types; it does not fetch the URI, verify the digest, or prove terms exist.

### 8.4 Evidence schema

Requires `evidence_id`, `kind`, `source_uri`, `content_mode`, `content_digest`.

Local conditional shape:

- `content_mode = external-payload` => `reviewed_content` absent;
- `content_mode = normalized-record` => `reviewed_content` required and JSON-compatible;
- optional `source_revision`, `license_ref`, citation metadata.

Digest verification is I-002/I-004.

### 8.5 Review schema

Requires:

- `review_id`;
- `status` enum `reviewed | provisional | disputed`;
- `reviewed_mapping_digest`;
- `reviewer_id`;
- `reviewed_at` string;
- `review_source`;
- `review_method`.

Timestamp format checking is not enabled in I-001; it remains a string structurally. Review independence and digest equality are process/I-004 semantics.

### 8.6 Mapping schema

A mapping source file is an object with `schema_version: 1` and non-empty `mappings` array. Each mapping record requires P-001's local fields.

Assessment shape is enforced structurally:

- `exact | close | broader | narrower | related` => non-null string `external_target`, non-null string `ontology_lock`, `candidate_projections` empty; `publication_relation` is string or null;
- `native-only | unsupported` => `external_target`, `ontology_lock`, `publication_relation` all null, `candidate_projections` empty;
- `ambiguous` => top-level `external_target`, `ontology_lock`, `publication_relation` null and non-empty `candidate_projections`;
- every candidate projection requires `external_target`, `ontology_lock`, `assessment_candidate`, `evidence`;
- candidate assessment enum only `exact | close | broader | narrower | related`.

The mapping schema checks local `review` as an inline review-record-shaped object in I-001. A later refactor may move audit records to separate files, but the semantic contract is the same review object keyed by stable `review_id`; I-001 must not introduce reference resolution.

`native_selector`, `applicability`, rationale/release metadata are structured conservatively as JSON-compatible objects/strings where P-001 has not yet fixed deeper subshape. I-004 can tighten semantic validation without breaking the source loader API.

### 8.7 Compatibility report schema

Requires the shared P-001 fields:

- `compatibility_report_id`, `report_digest`;
- `profile_id`, `profile_version`, `profile_semantic_digest`;
- expected/observed parent manifest digests;
- `state` enum four compatibility states;
- arrays `changed_components`, `dependency_results`, `incomplete_reasons`, `failure_reasons`;
- `evaluator_version`.

Each dependency result requires dependency ID, component ID, result `pass | fail | unknown`, evaluator rule version, and optional observed evidence digest/summary.

The schema does not attempt to prove state/reason consistency or report digest identity; I-005 owns those semantics.

## 9. RED test sequence

Before production files are created, add tests that import the not-yet-existing package/schemas and fail for the intended reason.

RED contract covers:

1. all seven schema files exist and self-validate as Draft 2020-12;
2. valid minimal fixture for each schema validates;
3. duplicate YAML key raises category `duplicate_key`;
4. duplicate JSON key raises category `duplicate_key`;
5. date/non-string-key/non-finite/cyclic-like non-JSON YAML shapes fail with `non_json_value` or decode error as appropriate;
6. parent component `required` property is rejected structurally;
7. external-payload evidence with `reviewed_content` rejected; normalized-record without it rejected;
8. review missing `reviewed_mapping_digest`/provenance field rejected;
9. approved mapping missing target/lock rejected;
10. ambiguous mapping candidate missing its ontology lock rejected;
11. native-only/unsupported non-null target/lock/publication relation rejected;
12. structurally valid mapping with nonexistent dependency/evidence/ontology IDs **passes** I-001, proving no cross-artifact semantic leakage;
13. unknown schema returns `unknown_schema`;
14. committed malformed schema fixture via temporary schema root returns `invalid_schema`.

Confirm RED in CI on an exact commit before creating production code.

## 10. GREEN implementation order

1. add `pyproject.toml` + `src/ontotf/__init__.py`;
2. add loader/error model with loader-focused tests;
3. add seven schemas;
4. add registry/validator;
5. add structural fixtures;
6. run focused `python -m unittest discover -s tests/i001 -v`;
7. run repository `python -m unittest discover -s tests -v`;
8. install package in CI, log Python + dependency versions, run both suites.

Implementation stays minimal; no refactor outside I-001 unless required for tests.

## 11. CI workflow

`.github/workflows/i001-validation.yml` triggers on the implementation branch and relevant paths. It:

- checks out code;
- sets up Python 3.12 (inside supported `>=3.10` range);
- upgrades pip;
- installs `-e .`;
- prints `python`, `jsonschema`, and `ruamel.yaml` versions;
- runs focused I-001 suite;
- runs full repository suite.

The workflow itself is part of the exact-head review scope.

## 12. Acceptance trace

- **Research before plan:** research commit `8e28ff2d...` predates this plan.
- **Plan before production:** this plan commit must precede schemas/package implementation.
- **Draft 2020-12:** explicit validator + self-check contract.
- **Strict YAML/JSON:** duplicate rejection + JSON-model normalization.
- **Seven schemas:** fixed registry and schema rules above.
- **Required negative cases:** enumerated in RED sequence.
- **No semantic leakage:** explicit positive test for unresolved IDs.
- **Review gate:** exact final head requires fresh logically-independent skeptical review; any content change invalidates it.

## 13. Deferred decisions

I-001 intentionally leaves these to later accepted tickets:

- exact canonical JSON and all content digest algorithms (I-002);
- TF/directory/sidecar byte identity (I-003);
- cross-artifact IDs, review/evidence digest equality, ontology term existence, uniqueness-by-ID, dense-empty semantics (I-004);
- compatibility state proof/report digest generation (I-005);
- IR/package resource distribution/runtime/resolver/doc generation (I-006+).

If implementation reveals a need to change P-001's semantic fields or authority boundaries, stop and amend design rather than hiding the change inside a schema.