# P-002 plan: forward-compatible TF-native source contract for I-004

**Issue:** #37  
**Research:** `docs/research/P-002-i004-source-contract-amendment.md`  
**Assertion-shape research head:** `81cf9049b7ef89d73ac5eae36ded7c7af81aabe2`  
**Architecture dependency:** A-001 merged main `9e644f57ab5b5a019f6a4a9384e5bee897c62003`

## 1. Goal and boundary

P-002 makes the native/source-side facts required by later I-004 mechanically representable without selecting P-003's ontology-projection architecture.

It must not add generic `native-adapter`/sidecar runtime carriers, external record/file/field selectors, data-format/database/API adapters, runtime URI dereferencing, target multiplicity, target roles, semantic profiles/capabilities, ontology bundles, approximation policy, authority-reference roles, or common semantic IR.

External identifiers/URIs may remain reviewed identity, authority, semantic, evidence, or provenance references without implying storage/fetch capability.

## 2. Production scope

Production edits stay limited to `src/ontotf/schemas/profile.schema.json` plus existing profile-v2 fixture updates. No runtime/compiler/resolver code and no `mapping.schema.json` change.

Profile schema version is **2**. `dependency_contract_version` is exactly **1** (`const: 1`). Unknown future dependency-contract versions fail closed.

Every dependency has a closed common envelope:

```text
dependency_id    non-empty string
component_id     non-empty string
kind             one v1 TF-native kind
assertion        closed kind-specific object
evidence?        content-addressed evidence bindings
```

Cross-artifact ID uniqueness/resolution and complete dependency closure remain I-004 semantic validation. A source dependency is not executable merely because it passes P-002 structural validation.

## 3. Exact v1 dependency kinds

Exactly:

- `component-present`
- `node-type-present`
- `feature-present`
- `edge-present`
- `path-present`
- `native-value-present`
- `value-domain`
- `extent-interpretation`

Forbidden runtime kinds include `adapter-capability`, `sidecar-field`, `carrier-interpretation`, and equivalent external-storage/record abstractions.

## 4. Exact v1 assertion shapes

All assertion objects use `additionalProperties: false`.

### `component-present`

Exactly `{}`. `component_id` already identifies the materialized component.

### `node-type-present`

Required:

```text
node_type: non-empty string
```

### `feature-present`

Required:

```text
node_type: non-empty string
feature:   non-empty string
```

### `edge-present`

Required:

```text
edge:      non-empty string
direction: outgoing | incoming
```

Direction is relative to the native entity later selected by mapping/query logic and must never be guessed from an edge name.

### `path-present`

Required:

```text
steps: non-empty ordered array of closed {edge, direction} objects
```

`edge` is non-empty; `direction` is `outgoing | incoming`. This is a TF graph path, not a filesystem/source path.

### `native-value-present`

Required:

```text
node_type:       non-empty string
feature:         non-empty string
value:           JSON scalar
value_semantics: semantic
```

JSON scalar means string, finite JSON number, boolean, or null under the existing source loader. `value_semantics: semantic` is explicit even for `""`/`null`; dense storage alone never makes those values semantic.

### `value-domain`

Required:

```text
node_type:        non-empty string
feature:          non-empty string
values:           non-empty unique array of JSON scalars
domain_semantics: observed | closed-reviewed
```

`observed` never implies closure. `closed-reviewed` requires a non-empty dependency-level `evidence` array. This prevents finite observed release values from silently becoming a closed semantic domain.

### `extent-interpretation`

Required:

```text
node_type:       non-empty string
interpretation: textualExtent | occurrenceSet | technicalAnchor | noSlot
```

These are interpretations of already-materialized TF structure only. `technicalAnchor` is positional mechanics, not semantic source-sign content. `noSlot` does not authorize an external carrier. No semantics are inferred from `oslots` alone.

## 5. JSON Schema construction

Add `$defs` for:

- JSON scalar;
- directed edge step;
- each assertion shape.

The dependency schema remains one closed object with common fields and uses `allOf` conditionals keyed by `kind` so exactly the matching assertion schema applies.

For `value-domain` with `domain_semantics = closed-reviewed`, the dependency object also requires `evidence` with `minItems: 1`.

Do not implement semantic existence checks in JSON Schema: whether node types/features/edges/components/evidence IDs actually exist is I-004 reference/native validation.

## 6. Digest compatibility

No I-002 algorithm changes.

Profile semantic identity already includes normalized dependency content, so assertion fields and their order-independent object representation are already bound into the profile digest. Existing mapping/evidence digest vectors must remain unchanged.

## 7. P-003 deferrals

P-002 does not decide:

- number of ontology projections;
- target formal kind / semantic role;
- mapping assessment placement per projection;
- semantic profile/capability IDs;
- ontology bundle/bridge identity;
- publication-relation placement/legality;
- semantic target CURIE/IRI matching rules;
- approximate execution;
- authority/identity/reference reverse indexes;
- final common semantic IR.

## 8. Assertion-contract TDD gate

### RED before schema assertion changes

Add tests that require:

1. all eight canonical valid assertion shapes pass;
2. missing required fields fail for every non-empty assertion kind;
3. unknown fields fail inside every assertion shape;
4. `component-present` rejects any assertion field;
5. edge/path directions outside `outgoing|incoming` fail;
6. `path-present.steps` cannot be empty and step order remains authored/semantic;
7. `native-value-present` accepts explicit `""` and null only with `value_semantics: semantic` and rejects missing/wrong marker;
8. `value-domain` requires non-empty unique scalar values and explicit `observed|closed-reviewed` status;
9. `closed-reviewed` requires non-empty evidence while `observed` need not;
10. `extent-interpretation` accepts exactly the four TF-native modes and rejects sidecar/path/backend fields;
11. a representative `{"sidecar_path": ...}` / `{"external_record": ...}` escape attempt fails under allowed kinds;
12. the exact eight-kind enum and `dependency_contract_version: const 1` remain pinned.

This RED must fail against the current unconstrained `assertion: {"type":"object"}` production schema.

### GREEN

Implement only the schema definitions/conditionals needed to satisfy that RED. Do not add Python runtime/semantic validation.

Run focused P-002 tests, I-001 schema/source tests, I-002 digest tests, A-001 architecture tests, and the full suite on the exact head.

## 9. Independent review gate

Fresh exact-head adversarial review must try to falsify:

- renamed outside-TF carrier escape through assertion fields;
- under-specified edge direction/path order;
- dense-empty semantic leakage;
- observed-domain accidental closure;
- `technicalAnchor` being treated as source content;
- future contract-version acceptance;
- P-003 semantic leakage;
- digest drift;
- fixture edits hiding regressions;
- source records becoming executable before I-004 validates reference integrity/closure.

Merge only with exact-head green CI and no review blocker.
