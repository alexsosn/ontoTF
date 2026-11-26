# I-001 structural validator research

**Issue:** #14  
**Recorded:** 2026-09-05  
**Phase:** research only; no production implementation in this commit  
**Accepted design:** P-001 exact reviewed head `ae6907b3140798421f773e74104f3a9434a34d5c`, merged as `e9ab50a759ba72c89047704ac70958fce6376951`

## Question

What is the smallest current Python stack that can implement P-001's structural source boundary with Draft 2020-12 validation, strict duplicate-key rejection, YAML 1.2 parsing, and an explicitly JSON-compatible in-memory model?

## Repository baseline

At accepted main `e9ab50a759ba72c89047704ac70958fce6376951`, ontoTF has research/design documents, scripts and unittest-based tests but no `pyproject.toml`, no importable production package, no `schemas/`, no `profiles/`, and no `src/` package. I-001 is therefore the first production/package scaffold and should keep that scaffold minimal.

## JSON Schema validator

### Evidence

The current PyPI release of `jsonschema` inspected on 2026-09-05 is **4.26.0** (released 2026-01-07). Its project metadata states:

- full support for JSON Schema Draft 2020-12;
- Python `>=3.10`;
- MIT license;
- lazy/programmatic validation with structured error paths.

Sources:

- https://pypi.org/project/jsonschema/
- https://python-jsonschema.readthedocs.io/en/latest/

### Decision

Use `jsonschema>=4.26,<5` and make Python `>=3.10` the first package baseline. Construct `Draft202012Validator` explicitly rather than using draft auto-selection as an implicit contract. Every committed schema must declare:

```json
"$schema": "https://json-schema.org/draft/2020-12/schema"
```

I-001 will self-check each schema with `Draft202012Validator.check_schema` before using it against source data.

Format checking is not required for I-001 unless a structural field specifically needs a format and the checker is explicitly enabled. `jsonschema` itself documents that declaring a format does not automatically activate format validation.

## YAML loader

### Evidence

The current `ruamel.yaml` PyPI line inspected on 2026-09-05 is **0.19.1**, requiring Python `>=3.9`; ontoTF's selected Python `>=3.10` baseline therefore satisfies it. `ruamel.yaml` documents YAML 1.2 support and states that duplicate mapping keys are disallowed by default in its modern API.

Sources:

- https://pypi.org/project/ruamel.yaml/0.19.1/
- https://yaml.dev/doc/ruamel.yaml/
- https://yaml.dev/doc/ruamel.yaml/api/#loading

The duplicate-key documentation explicitly contrasts this with PyYAML, which historically did not enforce uniqueness by default. Duplicate rejection is a P-001/I-001 semantic safety requirement, so relying on a custom PyYAML constructor when the selected loader already enforces the YAML rule would add unnecessary code and maintenance.

### Decision

Use `ruamel.yaml>=0.19.1,<0.20` with the safe loader API and leave `allow_duplicate_keys` false. Prefer the pure-Python parser path for consistent behavior across CI/platforms unless later measurement demonstrates a material performance need for an optional C backend.

Parsing is only half of the source contract. After YAML loading, recursively reject values outside the JSON-compatible data model:

- allowed scalars: `null`, boolean, integer, finite float, string;
- allowed containers: list and mapping;
- mapping keys must be strings;
- reject tagged/custom Python objects, timestamps/date objects, sets, tuples, bytes, non-finite floats, recursive/cyclic aliases, and any other non-JSON-compatible value.

JSON input should use the standard library decoder with an `object_pairs_hook` that rejects duplicate object names; the ordinary `json.loads` behavior of silently retaining the last duplicate is not acceptable for canonical source validation.

## Error boundary

I-001 should expose stable *categories* while retaining detailed library context for humans:

- `decode_error` — invalid UTF-8 or malformed JSON/YAML;
- `duplicate_key` — duplicate mapping/object key;
- `non_json_value` — parsed YAML value cannot be represented by the canonical JSON-compatible model;
- `unknown_schema` — requested schema ID/name is not registered;
- `invalid_schema` — committed schema itself fails Draft 2020-12 meta-validation;
- `schema_validation` — source is structurally invalid under a valid schema.

The exact schema error path/message may be library-derived and is not a stable public semantic contract. Stable category + source path + instance path + schema path is sufficient for this ticket.

## Package/layout choice

Use the standard `src` layout introduced only now that P-001 is accepted:

```text
pyproject.toml
src/ontotf/
  __init__.py
  source_validation.py
schemas/
  profile.schema.json
  parent-component-manifest.schema.json
  ontology-lock.schema.json
  evidence.schema.json
  review.schema.json
  mapping.schema.json
  compatibility-report.schema.json
tests/i001/
  ...
```

The package should not depend on Text-Fabric, Context-Fabric, RDF libraries, HTTP clients, or ontology libraries for this ticket.

## Structural versus semantic validation boundary

JSON Schema should enforce local shape constraints that do not require resolving another file, including:

- `additionalProperties: false` for closed machine records where P-001 defines the field set;
- enums and nullability;
- assessment-dependent local shape using `if`/`then`/`else` or `oneOf`;
- candidate projection requires its own ontology lock;
- `native-only` / `unsupported` require top-level target, ontology lock and publication relation to be null;
- parent component records do not admit an independent `required` field;
- evidence `content_mode` determines whether `reviewed_content` is required/forbidden where structurally expressible;
- review record contains the minimum audit fields from P-001;
- compatibility report contains the common release/activation report fields.

I-001 must **not** resolve or prove cross-artifact facts such as whether:

- a referenced component/dependency/evidence/lock/review actually exists;
- a target URI is present in an ontology lock;
- `reviewed_mapping_digest` matches recomputed mapping content;
- evidence content bytes match `content_digest`;
- parent component bytes match `content_digest`;
- dependency closure validates;
- a compatibility state is justified.

Those belong to I-002 through I-005. Keeping this boundary explicit prevents a structural validator from becoming an accidental partial compiler.

## Dependency/version policy

For the first POC package:

```text
requires-python = ">=3.10"
jsonschema >=4.26,<5
ruamel.yaml >=0.19.1,<0.20
```

Use bounded major/minor-family ranges in package metadata rather than exact runtime pins. CI records the actually installed versions, and future lock/reproducible-release work may add a lock file without changing the public validator API.

## Rejected alternatives

### PyYAML + custom duplicate-key constructor

Rejected for I-001. It can be made strict, but duplicate-key rejection would be project-owned customization whereas `ruamel.yaml` already documents it as default behavior. It also weakens the YAML 1.2 rationale.

### JSON-only source

Rejected because accepted P-001 chooses YAML as the canonical human authoring surface while compiling through a JSON-compatible model.

### Pydantic as schema/source authority

Rejected. P-001 explicitly makes JSON Schema Draft 2020-12 the machine contract. Generating schemas indirectly from a Python model would create a competing authority and unnecessary dependency.

### Semantic checks in custom JSON Schema extensions

Rejected. Cross-artifact existence, hashes, ontology semantics and compatibility evidence are later explicit compiler stages, not custom structural keywords.

## Risks and mitigations

- **YAML implicit types:** recursively enforce the JSON-compatible type set after parsing; tests cover dates/tags/non-string keys/non-finite numbers.
- **Duplicate JSON names:** use `object_pairs_hook`; do not trust default `json.loads` object construction.
- **Schema overreach:** negative tests assert missing cross-artifact references still pass structural validation when their local shape is valid.
- **Library drift:** bounded dependency ranges plus exact CI version logging; public behavior is contract-tested.
- **Schema recursion/reference complexity:** keep I-001 schemas locally resolvable and use shared `$defs` inside files only where useful; do not require network schema fetching.

## Recommendation

Proceed with `jsonschema` Draft 2020-12 + strict `ruamel.yaml` safe loading, a recursive JSON-compatibility guard, and a minimal `src/ontotf` package. The implementation plan should keep the API small: load a source file/text into the JSON-compatible model, select a registered local schema, structurally validate, and return data or raise one stable typed validation error. No semantic cross-artifact behavior should enter I-001.