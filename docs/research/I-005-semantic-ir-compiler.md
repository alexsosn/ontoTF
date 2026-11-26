# I-005 research: deterministic semantic IR compiler

**Issue:** #123  
**Type:** implementation research only  
**Baseline:** `main` at `0f6d09fbdae5754fb874c7b6d08539218648aa66` after merged F-023 / PR #120  
**Architecture:** accepted P-003 common ontology semantic adapter  
**Primary implementation dependency:** merged I-004 cross-artifact semantic validation

## Decision

I-005 should compile **one or more already validated, per-corpus semantic bundles** into one deterministic protocol-independent semantic IR. It must not resolve queries, evaluate the currently loaded parent corpus, execute Context-Fabric, infer ontology relations, or reinterpret source mappings.

The public compiler boundary should be conceptually:

```python
compile_semantic_ir(
    bundles: Iterable[ValidatedSemanticBundle],
) -> CompiledSemanticIR
```

A single-bundle call is valid, but cross-corpus IR requires composition of several validated bundles. This is required by R-001's independently versioned per-corpus semantic bundles and by P-003's cross-corpus reverse indexes. Treating one `SemanticSourceBundle` as a multi-corpus container would bind mappings for several `corpus_id` values to one expected-parent manifest and would make parent provenance ambiguous.

Each input bundle must therefore compile to exactly one corpus scope. I-005 may derive that scope from the set of `mapping.corpus_id` values because the current profile schema does not carry a separate `corpus_id`; a bundle with zero or multiple mapping corpus IDs is not compilable into the cross-corpus runtime IR. This is a compiler composition precondition, not a second pass over I-004 semantic rules.

## Current production boundary

I-004 exports frozen public records:

```text
SemanticSourceBundle
ValidatedSemanticBundle
SemanticIndexes
validate_semantic_bundle()
```

`ValidatedSemanticBundle` already carries:

- the original validated source bundle;
- deterministic `expected_parent_manifest_digest`;
- reviewed mapping-v2 semantic digests;
- validated `ontology_bundle_digest` when a bundle is present;
- deterministic validation indexes for components, dependencies, mappings, projections, candidates, references, ontology locks and evidence.

I-004 already proves component authority, dependency closure, controlled vocabularies, record-state legality, kind/role legality, routing, ontology target membership, bundle/bridge source closure, evidence bindings, mapping/projection review binding, native semantic assertions and approximation/publication policy. I-005 must consume those facts rather than re-run or partially duplicate them.

The current `SemanticIndexes` are **validation lookup indexes**, not the P-003 runtime semantic IR. In particular, the flattened `projections` index does not retain the parent mapping/corpus association. I-005 must iterate the validated mapping records and their child projections/references so that every compiled binding preserves `corpus_id`, `mapping_id`, native binding, mapping review and mapping digest.

## Multi-bundle composition

R-001's still-valid distribution result is central ontoTF source with independently versioned per-corpus semantic bundles; A-001 later removes the obsolete generic outside-TF sidecar/runtime assumption but does not change the per-corpus release boundary.

Therefore the compiler should:

1. accept one or more `ValidatedSemanticBundle` objects;
2. derive one `corpus_id` per bundle from its mappings;
3. reject a bundle whose mappings claim multiple corpus IDs, because one expected-parent digest cannot then be attributed safely;
4. permit several bundles in one IR;
5. key all mapping/projection provenance by corpus as well as local IDs so equal local IDs in independent corpus packages do not collide accidentally;
6. require duplicate `(corpus_id, profile artifact id, profile version)` inputs to be byte/semantic-identical or fail deterministically rather than choose one by input order;
7. sort all emitted keys/bindings deterministically, independent of bundle and source order.

The first acceptance composition is three separate validated bundles for BHSA, ETCBC Syriac and ETCBC ExtraBiblical.

## First exact semantic path

R-011 provides the strongest conservative cross-corpus control:

| corpus | pinned parent research revision | native semantics | target | assessment |
|---|---|---|---|---|
| BHSA | `4db00e2157915495e1a4d3d57e41223df24775da` | `word.sp=subs` | OLiA Noun | exact |
| Syriac | `bb0eaa7e21b020a26b7566d2e495da9b1f84a919` | `word.sp=subs` | OLiA Noun | exact |
| ExtraBiblical | `9a56288e6777bad6328856acf055c780e65dd5d9` | `word.sp=subs` | OLiA Noun | exact |

R-013 establishes the production target classification:

```text
target: http://purl.org/olia/olia.owl#Noun
reference_kind: semantic-pivot
query_role: semantic-constraint
formal_kind: class
semantic_role: annotation-value
profile_id: linguistic
capability_id: linguistic.part-of-speech
```

The existing I-004 phase-1 fixture already uses exactly this full IRI, kind/role, capability and native execution binding. The compiler therefore needs no new interpretation rule for the noun slice.

R-011 remains research evidence. I-005 tests may promote only the reviewed noun facts into dedicated production-owned fixtures; the whole `pilots.json` file must not become an implicit production mapping registry.

## Runtime IR index families

P-003 requires distinct reverse-index families. I-005 should compile all of them now because their routing is already explicit in mapping-v2; implementing only `semantic_index` would force I-006 or later tickets to reinterpret source rows again.

### `native_index`

Key:

```text
(corpus_id, native_binding_identity)
```

Value contains the reviewed native semantic record, child projections and external references needed for inspection/provenance. The binding identity must be derived only from the closed `nativeBinding` object, not from display strings or mapping IDs.

Use the already selected RFC 8785/JCS canonical JSON boundary and SHA-256 to derive a versioned native-binding identity. A suitable algorithm name is `ontotf-native-binding-jcs-sha256-v1`. This adds no dependency and gives a portable key for nested edge-path bindings. The original typed binding is retained alongside the digest; the digest is an identity/index key, not a replacement for executable fields.

### `semantic_index`

Exact key from P-003:

```text
(profile_id, capability_id, target, formal_kind, semantic_role)
```

Only approved projections with:

```text
reference_kind = semantic-pivot
query_role = semantic-constraint
```

enter this family. Assessment is retained in the value and is **not** part of the semantic key because the same requested concept can have different reviewed strengths in different corpora.

The `olia:Noun` key must contain three per-corpus binding records in the acceptance fixture.

### `authority_index`

P-003 key:

```text
(authority_system, authority_resource, formal_kind, semantic_role)
```

Current mapping-v2 authority-value projections do not contain a free `authority_system` field. They do contain an exact `ontology_lock`. I-004 has already resolved that lock and checked target membership. The compiler can therefore derive `authority_system` from the referenced lock's explicit `ontology_id`, and `authority_resource` from projection `target`.

This is reviewed metadata derivation, not URI hostname/name inference.

Only `authority-value + authority-value-filter` projections enter this family.

### `identity_index`

Key:

```text
(authority_system, external_entity_id, identity_strength)
```

All fields come directly from an `entity-identity` external reference (`authority_system`, `external`, `identity_strength`). No semantic mapping assessment is substituted for identity strength.

### `identifier_index`

Key:

```text
(issuer_or_namespace, literal_id)
```

Both fields come directly from a `catalogue-identifier` reference (`issuer_or_namespace`, `external`). Equal literal IDs under different issuers remain distinct.

### provenance and locator references

`provenance-source` and `locator` records remain attached to the native record/provenance payload but intentionally receive no target reverse index in I-005. Their presence must never cause semantic/authority/identity lookup entries.

## Record-state routing

Compiler routing must follow validated source state mechanically:

- approved semantic-pivot projections -> `semantic_index`;
- approved authority-value projections -> `authority_index`;
- entity-identity references -> `identity_index`;
- catalogue identifiers -> `identifier_index`;
- provenance/locator -> native/provenance payload only;
- ambiguous candidates -> preserved for inspection, **never** approved reverse indexes;
- native-only -> preserved in native/capability facts, no target reverse index;
- unsupported -> preserved as negative knowledge, no target reverse index.

No compiler branch may manufacture a target from `native_binding`, labels, feature names, target namespace similarity or ontology hierarchy.

## Capability facts versus operational state

R-014 corrects an ambiguity in the earlier short P-003 wording. A reviewed `native-only` record can legitimately instantiate a capability; `unsupported` cannot. `ambiguous` can also represent positive native capability support even though no common target is executable.

However final capability state `active | absent | unavailable` depends on current parent/profile compatibility and loadability. `ValidatedSemanticBundle` carries the **expected** parent digest, not the identity/status of a currently loaded parent. I-005 therefore cannot honestly emit final operational state.

I-005 should compile deterministic capability **facts/summaries**, grouped by:

```text
(corpus_id, profile_id, capability_id)
```

including at least:

- reviewed native-support record count, excluding `unsupported`;
- shared approved projection count;
- exact projection count;
- non-exact projection counts/assessment summary;
- ambiguous record count;
- native-only record count;
- unsupported record count;
- contributing mapping IDs.

I-006 combines these facts with runtime parent/profile/bundle prerequisite status to expose `semantic_capabilities` operational state. I-005 must not emit `unavailable` merely because it has no loaded corpus context.

## Typed immutable IR

Do not expose mutable source dictionaries as the public compiled IR contract.

The mapping-v2 native binding schema is closed and small enough for typed frozen records:

```text
NativeBindingIR
  component_id?
  node_type?
  feature?
  value?
  closed_values
  edge?
  direction?
  steps
  interpretation?
  execution_shape?
```

with an immutable `EdgeStepIR` and tuple-valued collections. This preserves the exact execution fields without requiring a generic recursive frozen-JSON abstraction.

Compiled binding/provenance records should likewise be frozen dataclasses/tuples. Source audit prose need not be copied into runtime IR unless P-003 requires it for explanation.

## Fingerprints retained in IR

I-005 should carry already validated identities rather than invent new semantic authority:

### Parent

- `expected_parent_manifest_digest` from `ValidatedSemanticBundle`.

This is an expected-parent fingerprint, not proof that the currently loaded corpus matches it.

### Profile source contract

Carry explicit version facts available on validated source:

- authored profile `profile_id`;
- `profile_version`;
- profile `schema_version`;
- `profile_catalog_version`;
- `dependency_contract_version`;
- mapping document `schema_version`.

The existing `profile_semantic_digest()` is a pre-P-003/v1 projection with obsolete free-form/source fields and must **not** be repurposed as the new runtime profile fingerprint. A future versioned profile semantic digest requires a separate reviewed change if a single hash is needed.

### Mappings/projections

Carry:

- mapping ID + I-004-verified mapping-v2 semantic digest;
- projection ID + authored/verified projection semantic digest;
- mapping and projection review IDs plus the reviewed digest binding;
- evidence IDs/content digests used by the mapping/projection.

### Ontologies

For a participating projection carry an `OntologyLockFingerprint` derived from the already validated lock source:

- `lock_id`;
- `ontology_id`;
- release;
- `content_digest`;
- term namespace where useful for explanation.

When an active ontology bundle exists, also carry I-004's `ontology_bundle_digest`. I-005 does not recompute bundle/bridge closure.

The current lock schema has no standalone lock semantic-digest field. Do not call the ontology payload `content_digest` a digest of the lock metadata. If a future single lock-record semantic digest is required, version it separately. For I-005, explicit lock identity fields plus any containing bundle digest avoid this false claim.

### Evidence/review

Carry IDs and content/reviewed semantic digests needed to explain which reviewed assertion authorized the IR row. Audit timestamps/reviewer prose are source metadata and need not affect compiled semantic identity unless a later publication contract requires them.

## Determinism and collisions

- Sort string dimensions using the repository's existing UTF-16 code-unit convention where semantic set ordering is required.
- Sort composite index keys lexicographically by their component UTF-16 keys.
- Sort binding lists by `(corpus_id, mapping_id, projection/reference id, native_binding_identity)`.
- Never let input iteration order select a winner.
- Duplicate exact compiled identities with different semantic payloads fail deterministically.
- Identical duplicate input bundles may be rejected rather than silently deduplicated in v1; this is easier to audit and avoids accidental double installation.

## Compiler error boundary

I-005 consumes `ValidatedSemanticBundle`; passing another type is a programmer error (`TypeError`).

Compiler-specific failures should be narrow and machine-oriented, for example:

```text
invalid_bundle_scope
compiled_identity_conflict
```

They cover properties that exist only when composing validated bundles, especially multi-corpus ambiguity and cross-bundle key conflicts. They must not re-label an I-004 semantic error.

The compiler must not call `validate_semantic_bundle()` internally. Callers decide when source validation occurs; this keeps validation and compilation independently testable.

## Rejected alternatives

### Compile directly from `SemanticSourceBundle`

Rejected. It bypasses I-004 and makes the compiler responsible for semantic validation again.

### Treat `SemanticIndexes.projections` as runtime semantic index

Rejected. It is keyed only by projection ID and loses parent mapping/corpus association.

### Put authority values into `semantic_index`

Rejected by R-017/P-003 routing.

### Infer authority system from target URI hostname

Rejected. Use the explicit referenced ontology lock's `ontology_id`.

### Make capability declarations executable

Rejected. Profile/capability declarations are discovery scope. Concept-level reviewed projections remain execution authority.

### Compute final `active|absent|unavailable` in I-005

Rejected. `unavailable` depends on current parent/runtime compatibility, which is outside compiler inputs and is resolved in I-006.

### Promote R-011 `pilots.json` wholesale to production

Rejected. R-011 is a conservative research fixture with explicit overrides and known incomplete/raw denominators. I-005 should use only dedicated reviewed acceptance facts; the seven-pilot promotion remains P-003 step 7.

## Plan inputs

The implementation plan should freeze:

1. `compile_semantic_ir(bundles)` public API;
2. typed frozen IR records and closed native binding type;
3. versioned native-binding identity algorithm;
4. single-corpus-per-bundle composition check;
5. exact five index/fact families and key definitions;
6. authority-system derivation from validated lock `ontology_id`;
7. capability facts without final operational state;
8. provenance/fingerprint fields;
9. deterministic ordering and conflict diagnostics;
10. three independent production-owned noun bundle fixtures, each structurally and semantically valid under current I-004;
11. tests proving non-semantic routing exclusions and no source-order dependence;
12. explicit I-006 handoff: resolver consumes only `CompiledSemanticIR` plus runtime compatibility/prerequisite state and does not reopen mapping source semantics.

## TDD implications

RED should fail because `ontotf.semantic_ir` / `compile_semantic_ir` does not exist while each source fixture passes current `validate_semantic_bundle()` independently.

The strongest first RED should construct three valid I-004 noun bundles with the full OLiA Noun IRI and distinct `corpus_id`/expected-parent fingerprints, compile them together, and assert that one semantic key has three deterministic bindings. Controls then exercise native-only, unsupported, ambiguous, authority-value, identity, identifier, provenance and locator routing.

No test should require a live corpus checkout or network lookup in I-005.

## Exit judgment

**GO.** Current I-004 outputs contain enough reviewed source information to build the P-003 runtime IR without schema changes for the noun slice or for the separate semantic/authority/identity/identifier index families.

The main new contract I-005 must add is cross-bundle composition plus deterministic typed runtime indexes. Current-parent compatibility and executable resolution remain I-006 responsibilities.