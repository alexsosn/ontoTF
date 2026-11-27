# I-005 implementation plan: deterministic semantic IR compiler

**Issue:** #123  
**Research:** `docs/research/I-005-semantic-ir-compiler.md` + review amendment  
**Baseline:** `main` at `2612ce0bd224a1f94a0b2a7ae56292d535d910d4`  
**Architecture:** accepted P-003, implementation decomposition step 2

## 1. Goal

Add a deterministic compiler that consumes one or more already validated per-corpus `ValidatedSemanticBundle` objects and produces one protocol-independent cross-corpus semantic IR.

I-005 ends at compiled IR/indexes. It does not evaluate the currently loaded parent corpus, resolve a semantic request, emit Context-Fabric query syntax, execute a query, perform ontology reasoning, or fetch network resources.

The acceptance path is the reviewed exact OLiA Noun tuple across BHSA, ETCBC Syriac and ETCBC ExtraBiblical.

## 2. Public API

Add `src/ontotf/semantic_ir.py` and export its public surface from `ontotf.__init__`.

Freeze:

```python
NATIVE_BINDING_IDENTITY_ALGORITHM = "tfont-native-binding-jcs-sha256-v1"

@dataclass(frozen=True)
class SemanticIRProblem:
    category: str
    message: str
    corpus_id: str | None = None
    mapping_id: str | None = None
    related_id: str | None = None

class SemanticIRError(ValueError): ...


def compile_semantic_ir(
    bundles: Iterable[ValidatedSemanticBundle],
) -> CompiledSemanticIR: ...
```

Passing a non-iterable or an iterable item that is not an exact `ValidatedSemanticBundle` is a programmer/API type error (`TypeError`), not a semantic source error.

The compiler does not call `validate_semantic_bundle()` internally.

## 3. Immutable value types

Use frozen dataclasses and tuples; do not expose mutable source dictionaries as compiled runtime authority.

### 3.1 Native binding

```python
@dataclass(frozen=True)
class EdgeStepIR:
    edge: str
    direction: str

@dataclass(frozen=True)
class NativeBindingIR:
    component_id: str | None
    node_type: str | None
    feature: str | None
    value_present: bool
    value: str | int | float | bool | None
    closed_values: tuple[str | int | float | bool | None, ...] | None
    edge: str | None
    direction: str | None
    steps: tuple[EdgeStepIR, ...] | None
    interpretation: str | None
    execution_shape: str | None
```

`value_present` is required because JSON `null` is a legal authored `value` and must remain distinguishable from an absent field.

`native_binding_identity(binding)` is internal/public only as needed by tests; it computes SHA-256 over `canonical_json_bytes()` of the exact closed authored binding object and prefixes `sha256:`. The exported algorithm constant pins the contract.

The compiler retains both the typed binding and its digest identity.

### 3.2 Provenance fingerprints

```python
@dataclass(frozen=True)
class EvidenceFingerprint:
    evidence_id: str
    content_digest: str

@dataclass(frozen=True)
class ReviewFingerprint:
    review_id: str
    status: str
    reviewed_semantic_digest: str

@dataclass(frozen=True)
class OntologyLockFingerprint:
    lock_id: str
    ontology_id: str
    release: str
    content_digest: str
    term_namespace: str
```

Do not label ontology `content_digest` as a digest of the lock metadata.

### 3.3 Bundle variant

```python
@dataclass(frozen=True, order=True)
class BundleVariantKey:
    corpus_id: str
    authored_profile_id: str
    profile_version: str
    expected_parent_manifest_digest: str
    ontology_bundle_digest: str | None
```

One semantic profile release may therefore have more than one validated parent variant. Exact duplicate variant keys are rejected; v1 never silently deduplicates input bundles.

`BundleVariantIR` retains, at minimum:

- key;
- profile schema version;
- profile catalog version;
- dependency contract version;
- mapping document schema version;
- `MAPPING_SEMANTIC_ALGORITHM_V2`;
- `PROJECTION_SEMANTIC_ALGORITHM`;
- mapping ID/digest pairs;
- ontology lock fingerprints participating in the source bundle.

No new P-003 profile semantic digest is invented in I-005.

## 4. Compiled records

### 4.1 Native record

```python
@dataclass(frozen=True)
class NativeRecordIR:
    variant: BundleVariantKey
    corpus_id: str
    mapping_id: str
    native_binding_identity: str
    native_binding: NativeBindingIR
    native_dependencies: tuple[str, ...]
    profiles: tuple[str, ...]
    capabilities: tuple[str, ...]
    native_state: str
    mapping_semantic_digest: str
    mapping_review: ReviewFingerprint
    evidence: tuple[EvidenceFingerprint, ...]
    projection_ids: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    reference_ids: tuple[str, ...]
```

A provisional/disputed mapping may be retained as a non-authoritative native inspection record, but its review status is explicit.

### 4.2 Target projection binding

```python
@dataclass(frozen=True)
class TargetBindingIR:
    variant: BundleVariantKey
    corpus_id: str
    mapping_id: str
    projection_id: str
    target: str
    reference_kind: str
    query_role: str
    formal_kind: str
    semantic_role: str
    profile_id: str
    capability_id: str
    assessment: str
    native_execution_binding_identity: str
    native_execution_binding: NativeBindingIR
    native_dependencies: tuple[str, ...]
    mapping_semantic_digest: str
    projection_semantic_digest: str
    mapping_review: ReviewFingerprint
    projection_review: ReviewFingerprint
    ontology_lock: OntologyLockFingerprint
    ontology_bundle_digest: str | None
    evidence: tuple[EvidenceFingerprint, ...]
```

This is the authoritative payload used by semantic/authority reverse indexes only after the review-status gate in §7.

### 4.3 Ambiguous candidate / external reference preservation

Use frozen records sufficient to preserve all schema fields that affect later inspection/routing. They do not need executable helper methods in I-005.

At minimum:

- `CandidateIR` retains variant/corpus/mapping/candidate identity, target routing/kind/role/profile/capability/assessment candidate, ontology-lock fingerprint and evidence;
- `ExternalReferenceIR` retains variant/corpus/mapping/reference identity, kind/query role/external value, explicit authority/issuer/identity strength, typed native binding where present and evidence.

Do not add child review state where the source schema has none.

## 5. Index key types

Use frozen orderable dataclasses for keys rather than raw positional tuples in public API:

```python
SemanticKey(profile_id, capability_id, target, formal_kind, semantic_role)
AuthorityKey(authority_system, authority_resource, formal_kind, semantic_role)
IdentityKey(authority_system, external_entity_id, identity_strength)
IdentifierKey(issuer_or_namespace, literal_id)
NativeKey(corpus_id, native_binding_identity)
CapabilityKey(variant, profile_id, capability_id)
```

Ordering is explicit and deterministic. String ordering must match repository UTF-16 code-unit ordering; do not rely on Python's default Unicode code-point ordering for contract-visible sorted collections.

## 6. `CompiledSemanticIR`

Freeze a tuple-based public container:

```python
@dataclass(frozen=True)
class CompiledSemanticIR:
    variants: tuple[BundleVariantIR, ...]
    native_index: tuple[tuple[NativeKey, tuple[NativeRecordIR, ...]], ...]
    semantic_index: tuple[tuple[SemanticKey, tuple[TargetBindingIR, ...]], ...]
    authority_index: tuple[tuple[AuthorityKey, tuple[TargetBindingIR, ...]], ...]
    identity_index: tuple[tuple[IdentityKey, tuple[ExternalReferenceIR, ...]], ...]
    identifier_index: tuple[tuple[IdentifierKey, tuple[ExternalReferenceIR, ...]], ...]
    capability_facts: tuple[tuple[CapabilityKey, CapabilityFactsIR], ...]
```

Tuple indexes are chosen for deterministic equality/serialization and dependency-free runtime. Callers may construct dicts for lookup; I-006 may add private/public lookup helpers without changing source authority.

## 7. Review authority gate

I-004 validates source closure and review digest freshness but accepts review status vocabulary including provisional/disputed. I-005 must distinguish freshness from authorization.

### Mapping-level gate

`mapping.review.status == "reviewed"` is required for:

- positive capability-support facts;
- entity-identity reverse-index rows;
- catalogue-identifier reverse-index rows;
- any child target projection to become authoritative.

`unsupported` never contributes positive capability support even when reviewed.

A reviewed `ambiguous` or `native-only` mapping may contribute native capability support while producing no approved target reverse row.

### Projection-level gate

Both must be reviewed:

```text
mapping.review.status == reviewed
projection.review.status == reviewed
```

before a projection contributes to `semantic_index`, `authority_index`, shared-projection counts, exact counts or non-exact projection counts.

A reviewed mapping with a provisional/disputed projection can still contribute reviewed native support at mapping level.

### External references

`entity-identity` / `catalogue-identifier` references inherit authority from the reviewed mapping-level semantic digest/review because they have no child review object. Provenance/locator references never become target reverse rows.

## 8. Index routing

### `native_index`

Every compiled native record is retained for inspection, including explicit review status and negative/ambiguous/native-only state. Key is `(corpus_id, native_binding_identity)`. Multiple bundle variants may legally appear under one key.

### `semantic_index`

Only reviewed target bindings with:

```text
reference_kind = semantic-pivot
query_role = semantic-constraint
```

Assessment is retained in the binding value, not included in the key.

No ambiguous candidate enters this index.

### `authority_index`

Only reviewed:

```text
reference_kind = authority-value
query_role = authority-value-filter
```

The key `authority_system` is the referenced validated ontology lock's explicit `ontology_id`. Never parse it from the target URI.

### `identity_index`

Only `entity-identity` references under a reviewed mapping. Key fields come directly from `authority_system`, `external`, `identity_strength`.

### `identifier_index`

Only `catalogue-identifier` references under a reviewed mapping. Key fields come directly from `issuer_or_namespace`, `external`.

### Non-indexed references

`provenance-source` and `locator` remain attached to native/reference IR for explanation but have no reverse target index in I-005.

## 9. Capability facts

```python
@dataclass(frozen=True)
class CapabilityFactsIR:
    reviewed_native_support: int
    shared_projections: int
    exact: int
    close: int
    broader: int
    narrower: int
    related: int
    ambiguous: int
    native_only: int
    unsupported: int
    mapping_ids: tuple[str, ...]
```

Facts are variant-scoped via `CapabilityKey(variant, profile_id, capability_id)`.

Rules:

- reviewed mapping + any valid declared profile/capability membership may contribute one native semantic record to that capability;
- `unsupported` increments negative knowledge but not `reviewed_native_support`;
- reviewed `ambiguous` increments native support + ambiguous;
- reviewed `native-only` increments native support + native_only;
- reviewed positive mapping increments native support;
- shared/exact/non-exact projection counters include only reviewed child target projections under a reviewed mapping;
- declarations without mapping evidence do not generate capability facts;
- I-005 emits no final `active|absent|unavailable` state and no `executable_exact` boolean.

I-006 derives operational state only after selecting/evaluating the current compatible bundle variant.

## 10. Bundle composition and errors

### Corpus scope

For every input `ValidatedSemanticBundle`, collect `corpus_id` from validated mapping records.

- zero corpus IDs -> `SemanticIRError(category="invalid_bundle_scope")`;
- more than one corpus ID -> same category;
- exactly one -> compile that corpus scope.

The profile schema currently has no independent `corpus_id`, so no additional invented source field is used.

### Duplicate variant

Two input bundles producing the same exact `BundleVariantKey` fail with:

```text
category = duplicate_bundle_variant
```

even if their payloads are otherwise identical.

### Compiled identity conflict

If the same exact local compiled identity within one variant (mapping/projection/reference identity) would yield different immutable payloads, fail:

```text
category = compiled_identity_conflict
```

Do not choose by input order.

I-004 already rejects duplicate child IDs within one bundle; this compiler category protects cross-input composition only.

## 11. Determinism

- Accept any iterable, materialize once, and never depend on caller order.
- UTF-16-sort bundle variants by component string fields plus digest strings/nullable bundle digest with a pinned `None` ordering.
- UTF-16-sort profile/capability/key string dimensions.
- Sort binding values by `(variant, corpus_id, mapping_id, child id, native-binding identity)`.
- Keep mapping `native_dependencies`, profiles, capabilities, evidence IDs and local ID lists set-like and UTF-16 sorted where source semantics already treat them as sets.
- Native `closed_values` retain their validated authored semantic meaning; do not sort unless the source/digest contract already treats that field as set-like. The compiler must not silently alter execution semantics.
- No mapping/source input ordering changes `CompiledSemanticIR` equality.

## 12. RED fixture strategy

Add `tests/i005/` with a self-contained production-valid fixture builder rather than importing a partially reviewed I-004 fixture as authoritative data.

`tests/i005/_fixtures.py` should:

1. construct one minimal profile/parent/mapping/lock/evidence set;
2. use full OLiA Noun IRI;
3. use `class + annotation-value`, `linguistic.part-of-speech`, exact semantic-pivot routing;
4. use native `word.sp=subs` execution binding;
5. compute evidence, projection-v1 and mapping-v2 digests using current public helpers;
6. populate complete mapping + projection review records with `status=reviewed`;
7. structurally validate profile, parent, mapping root, ontology lock and evidence using current I-001 schemas;
8. assemble and pass `validate_semantic_bundle()`;
9. parameterize `corpus_id`, authored profile ID/version and parent content digest so BHSA/Syriac/ExtraBiblical and parent-variant cases are independent validated bundles.

The fixture is a dedicated I-005 contract fixture; it does not claim to be a released corpus mapping package.

## 13. TDD RED matrix

Commit tests/workflow before `src/ontotf/semantic_ir.py` or `__init__.py` exports.

RED must fail because the compiler public API does not exist, while fixture setup controls pass independently.

Required tests:

### Public / determinism

1. importing `compile_semantic_ir` from `ontotf` is the intended missing production surface;
2. same validated inputs compile identically on repeated calls after GREEN;
3. reversing bundle order and mapping authored order does not change IR;
4. native binding identity is stable across object key order and changes when an execution-significant field changes;
5. JSON null native value remains distinct from missing `value`.

### Exact noun composition

6. three separately validated BHSA/Syriac/ExtraBiblical noun bundles produce one `SemanticKey` for full OLiA Noun tuple;
7. that key has three deterministic corpus bindings;
8. each binding retains `word/sp/subs`, mapping/projection IDs, mapping/projection semantic digests, expected-parent fingerprint, lock fingerprint and review/evidence identity;
9. no Context-Fabric plan string is generated in I-005.

### Bundle variants

10. same corpus/profile/version with two different expected-parent digests compiles as two legal variants;
11. both variants coexist under the same semantic key with distinct variant provenance;
12. exact duplicate `BundleVariantKey` input fails `duplicate_bundle_variant`.

### Review gate

13. digest-fresh mapping with `status=provisional` produces no authoritative semantic/authority/identity/identifier row and no positive capability support;
14. reviewed mapping + digest-fresh provisional projection preserves reviewed native capability support but excludes that projection from target reverse indexes/counts;
15. reviewed mapping + reviewed projection enters target reverse index;
16. reviewed native-only and ambiguous mappings contribute native support but no target reverse index;
17. reviewed unsupported increments only negative knowledge.

### Routing isolation

18. authority-value projection appears only in `authority_index`, with authority system from lock `ontology_id`;
19. entity-identity reference appears only in `identity_index` under reviewed mapping;
20. catalogue identifier appears only in `identifier_index` under reviewed mapping;
21. provenance-source and locator enter none of the four target reverse indexes;
22. ambiguous candidates enter none of the four target reverse indexes;
23. a matching target IRI with semantic-pivot versus authority-value routing remains separated.

### Compiler boundary

24. zero/multi-corpus bundle scope fails `invalid_bundle_scope`;
25. non-`ValidatedSemanticBundle` item fails `TypeError`;
26. compiler does not call `validate_semantic_bundle()` internally (test via patch/mock sentinel);
27. compiler performs no network/file/corpus access.

## 14. GREEN implementation order

1. add frozen IR/error/key/value types and UTF-16 ordering helpers;
2. native-binding conversion + versioned JCS/SHA-256 identity;
3. bundle-scope + `BundleVariantKey` builder;
4. native record compiler;
5. explicit review authority helpers;
6. semantic/authority target binding compiler;
7. candidate/reference preservation;
8. semantic/authority/identity/identifier/native index assembly;
9. variant-scoped capability facts;
10. deterministic final sorting/equality;
11. export public surface from `ontotf.__init__`.

Do not refactor I-004 internals unless a RED proves a shared helper is necessary. Favor read-only consumption of its public result.

## 15. CI

Add `.github/workflows/i005-semantic-ir.yml`:

- `push` on the active I-005 implementation branch;
- `pull_request` paths covering `src/ontotf/**`, `tests/i005/**`, relevant I-004 tests, I-005 research/plan and the workflow itself;
- exact-head `actions/checkout@v5`;
- `actions/setup-python@v6`;
- Python 3.10 and 3.12;
- install editable package;
- run `tests/i005` focused suite;
- run `tests/i004` semantic-validation regressions.

Do **not** add another generic full-suite command. `.github/workflows/full-suite.yml` remains authoritative under F-007.

At final PR head require:

- I-005 focused green 3.10/3.12;
- I-004 regressions green;
- F-007/F-011 CI policy checks green if triggered;
- authoritative full suite green;
- current-main integration check.

## 16. Scope guardrails

No I-005 production code may:

- inspect a live TF/Context-Fabric corpus;
- decide current parent compatibility;
- return `active|absent|unavailable` operational state;
- emit executable CF query plans;
- execute approximate mappings;
- resolve ontology hierarchy/subclass relations;
- perform label/feature-name similarity;
- dereference ontology/authority URIs;
- introduce RDF/SPARQL runtime dependency;
- add a generic source-format/sidecar adapter;
- promote the complete R-011 research fixture as a production mapping release.

## 17. I-006 handoff

I-006 receives `CompiledSemanticIR` and separately established runtime prerequisite/compatibility state.

For exact OLiA Noun it must be able to perform one exact `SemanticKey` lookup, select one current compatible bundle variant per requested corpus, reject non-reviewed/non-exact/non-compatible bindings, and return native plan records with provenance without reopening source mapping semantics.

I-005 is complete when the compiled IR exposes all data required for that handoff deterministically.