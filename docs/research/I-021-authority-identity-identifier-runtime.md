# I-021 research — authority, identity and identifier runtime authority

Issue: #238  
Parent: P-004 #202, Workstream B  
Research dependency: R-017 #51  
Baseline: main `45b4584f7a8ab8ce5d5c3920fa144819a88fdfbe`  
Status: research complete; ready for independently reviewed plan

## Question

What is the smallest production resolver/executor surface that can use the
already-compiled R-017 reverse indexes without allowing authority/identity/
identifier references to leak into semantic-pivot resolution or allowing a
caller-forged compiled row to inherit unrelated review authority?

The three reverse indexes are already sufficient to express the lookup
semantics. No source schema migration and no index-key migration are required.

Identity/identifier execution does require one additive compiled-IR trust
artifact: the canonical reviewed parent mapping semantic payload must survive
compilation so runtime can prove that an `ExternalReferenceIR` row is the
reference that was actually covered by the reviewed mapping digest.

## Executable reconciliation evidence

Probe:

`scripts/research/i021_reference_runtime_reconciliation.py`

Committed output:

`docs/research/data/generated/i021/reference-runtime-reconciliation.json`

The exact-head research workflow runs it on Python 3.10 and 3.12 and retains
the I-005 compiler routing controls.

The probe demonstrates the current production state:

- authority-value projection routes only through
  `authority_index[AuthorityKey]`;
- entity identity routes only through
  `identity_index[IdentityKey]`;
- catalogue identifiers route only through
  `identifier_index[IdentifierKey]`;
- provenance-source and locator rows remain attached to the native record and
  do not enter identity/identifier reverse indexes;
- authority rows are `TargetBindingIR` and already retain the I-020 reviewed
  projection semantic payload;
- identity/identifier rows are `ExternalReferenceIR` and carry no own review
  or semantic digest;
- their parent mapping semantic digest can be reproduced exactly from the
  canonical source mapping payload;
- `NativeRecordIR` does not currently retain that payload;
- a public-dataclass replacement of an `ExternalReferenceIR` succeeds while
  the selected release continues to carry the original mapping digest;
- explicit `execution_shape="value-predicate"` on identity/identifier
  native bindings validates and compiles without any source-schema change;
- the old I-005 fixtures omit execution shape and therefore are useful resolver
  fixtures but must not be silently treated as executable runtime plans.

This is the intended pre-I-021 state.

## Existing R-017 separation is already correct

The six source/reference roles remain distinct:

- semantic-pivot;
- authority-value;
- entity-identity;
- catalogue-identifier;
- provenance-source;
- locator.

I-021 productionizes only three non-semantic lookup families:

1. authority-value;
2. entity-identity;
3. catalogue-identifier.

Provenance-source and locator stay explanation/metadata-only in this ticket.
Ordinary semantic-pivot behavior remains owned by I-006/I-020.

No resolver may infer a role from URI hostname, URI syntax, labels, local
names, identifier spelling or equality of strings.

## Current compiled key contracts

### Authority

`AuthorityKey` already contains:

- authority system;
- authority resource;
- formal kind;
- semantic role.

Rows are reviewed `TargetBindingIR` values. Therefore authority resolution
already has:

- corpus/variant identity;
- profile/capability;
- assessment;
- native execution binding identity;
- native dependencies;
- mapping/projection digests and reviews;
- ontology lock/bundle identity;
- evidence;
- approximation envelope;
- reviewed projection semantic payload.

This is enough for an authority resolver without an authority-specific IR
migration.

### Identity

`IdentityKey` contains:

- authority system;
- external entity ID;
- identity strength.

Rows are `ExternalReferenceIR`.

The key is deliberately strength-sensitive so the compiler does not collapse
`same-entity`, `probable-same-entity`, `related-record` and
`ambiguous-identity`.

For public resolution, identity strength should **not** be caller-supplied
execution authority. A request should name authority system + external entity
ID + corpora; the resolver inspects all reviewed strength buckets for that
identity.

Only `same-entity` may authorize the first exact identity filter.

If no same-entity row exists but probable/related/ambiguous rows do, the
resolver returns a deterministic non-exact/non-authorized problem rather than
choosing one or treating probable identity as semantic approximation.

I-021 does not define approximate identity losses. Semantic
undercoverage/overcoverage is not an identity-strength algebra.

### Identifier

`IdentifierKey` contains:

- issuer or namespace;
- literal ID.

This is already the correct exact lookup key. Equal literal strings under
different issuers are different requests and different reverse-index buckets.

No unscoped identifier lookup is added.

## Why parent mapping payload binding is required

An external reference has no independent review object or semantic digest in
the accepted source contract. Its scholarly/runtime authority is part of the
reviewed parent mapping.

`mapping_semantic_digest_v2()` includes `external_references` in the
mapping semantic projection. Mapping review already binds that digest, and the
selected release signature already binds the mapping digest/review.

The missing runtime link is the exact reviewed mapping payload.

Today a caller can create:

```python
replace(reference, external="https://example.org/forged")
```

and place the row back into a public `CompiledSemanticIR`. The release still
contains the old reviewed parent mapping digest. A future resolver that merely
checks `mapping_id` membership would therefore authorize a row that was not
reviewed.

Do not try to reconstruct the exact mapping payload from normalized
`NativeRecordIR`. The mapping semantic projection contains source
presence/order distinctions and child objects that the normalized IR does not
retain exactly. I-020 already demonstrated why guessed source reconstruction is
a brittle trust boundary.

## Additive IR trust artifact

The implementation plan should add one optional field:

`NativeRecordIR.mapping_semantic_payload: str | None = None`

During `compile_semantic_ir()`, for every reviewed mapping, store:

```python
canonical_json_bytes(
    mapping_semantic_projection_v2(source_mapping)
).decode("utf-8")
```

The payload is evidence of the already-authoritative digest, not new
authority.

The parent mapping's `native_state` remains part of the reviewed payload but
is **not** by itself a semantic-capability gate for identity/identifier
resolution. In particular, an external reference attached to a
`native-only` mapping can still be a valid reviewed identity or scoped
identifier: R-017 deliberately separates external-reference semantics from
common-pivot support. Conversely, the resolver must not manufacture reference
authority merely because the parent mapping is `positive`.

Reference execution authority comes from the reviewed child contained in the
reviewed mapping payload, its explicit native binding, and fresh runtime
prerequisites. If a future policy wants to forbid references under a particular
mapping state, that must be an explicit reviewed rule rather than an accidental
reuse of semantic capability activation.

A reference resolver must require:

1. exact non-empty string;
2. valid canonical JSON object;
3. SHA-256 equal to `NativeRecordIR.mapping_semantic_digest`;
4. the same digest present in selected release
   `ProfileReleaseSignature.mapping_digests`;
5. reviewed mapping fingerprint present in
   `ProfileReleaseSignature.mapping_reviews`;
6. review status `reviewed`;
7. review's reviewed semantic digest equal to the mapping digest;
8. mapping ID/corpus/native state/native dependencies coherent with the
   selected native record;
9. exactly one external-reference child with the requested
   `reference_id`;
10. that authoritative child normalizes to the current
    `ExternalReferenceIR` row, including routing, external value,
    authority/issuer/identity strength, native binding identity/binding,
    publication relation and evidence.

A caller who replaces both the index row and the corresponding normalized
`NativeRecordIR.external_references` still cannot obtain authority without
also supplying a payload whose hash matches the reviewed release digest.

The exact semantic resolver may ignore `mapping_semantic_payload`; it must not
enter existing exact/approximate semantic fingerprints.

## Full reference-index validation is separate from exact semantic IR validation

Current `_validate_ir_shape()` validates the semantic index and capability
facts because I-006 never consumes the other indexes.

I-021 should add an external/reference-specific validation path rather than
changing exact semantic request behavior.

It must validate:

- `authority_index` key/row types and key/row coherence;
- `identity_index` key/row types and key/row coherence;
- `identifier_index` key/row types and key/row coherence;
- every row references a selected variant;
- every external row has exactly one reviewed parent native record for
  `(variant, mapping_id)`;
- no duplicate reverse-index keys;
- no duplicate identical rows;
- no row of the wrong reference/query family;
- no identity/identifier row can be manufactured from provenance/locator
  records;
- parent mapping payload binding described above.

This path may reuse current variant/prerequisite validation internals.

## Authority-value execution policy

Authority-value rows use ordinary mapping assessments and the I-020
approximation envelope. R-017 explicitly deferred non-exact authority
execution to R-016; R-016 is now productionized by I-020.

Therefore I-021 should support two authority request surfaces, following the
semantic resolver compatibility pattern:

### exact authority request

- exact assessment only;
- one exact row per requested corpus;
- multiple exact rows fail closed;
- close/broader/narrower/related do not substitute.

### approximate authority request

- exact authority row wins with zero loss;
- otherwise only reviewed eligible close/broader/narrower rows may execute;
- caller accepts the same closed loss vocabulary as I-020;
- related remains non-substitutive;
- multiple eligible approximate authority rows fail closed;
- loss records/fingerprints preserve authority key and authority query role.

The implementation should reuse/refactor I-020 approximation validation and
loss vocabulary rather than create a second direction semantics.

This does not make an authority resource a semantic pivot. Results remain
explicitly authority-value filters.

## Identity execution policy

Public request identity is:

- authority system;
- external entity ID;
- requested corpora.

The resolver searches reviewed identity buckets for those two fields.

Per corpus:

1. validate selected release/runtime prerequisite;
2. collect reviewed parent-bound identity references;
3. if exactly one executable `same-entity` row exists, select it;
4. if multiple same-entity rows exist, fail closed;
5. if none exists but probable/related/ambiguous rows exist, fail with a
   deterministic non-exact identity category;
6. if none exists at all, report identity absent.

`probable-same-entity`, `related-record`, and `ambiguous-identity` may be
returned in diagnostics/explanation but cannot produce a native execution plan
in I-021.

No `owl:sameAs` presence is required for runtime identity resolution; the
reviewed `same-entity` strength is the runtime contract. Publication relation
remains publication metadata and must remain coherent with the source
validator.

## Identifier execution policy

Public request uses exact `IdentifierKey` semantics:

- issuer/namespace;
- literal ID;
- corpora.

Per corpus the resolver requires exactly one reviewed parent-bound
catalogue-identifier row with an explicit native binding. The row may belong
to a mapping whose common-pivot state is `native-only`; that does not make
the scoped identifier less exact. Semantic capability state and identifier
identity are separate contracts.

Multiple rows for the same issuer/literal/corpus fail closed pending explicit
composition semantics.

No approximate identifier mode exists.

## Resolution versus execution

Resolution and execution must remain separate concepts.

A reviewed row can be resolvable but not currently executable if its native
binding lacks an explicit supported `execution_shape`.

The standard old I-005 fixtures demonstrate this: they have native
feature/value selectors but no execution-shape declaration.

I-021 execution accepts only the already-productionized native shapes:

- `value-predicate`;
- `value-set-predicate`.

A source can opt into those shapes today without a schema change, as the
research probe demonstrates.

Do not infer execution shape from the presence of feature/value fields.

Structural edge/path/native-kind execution stays with the later P-004
structural runtime ticket.

## Fresh runtime authorization

As in I-008/I-020, public execution takes:

- compiled IR;
- a typed reference request;
- loaded corpus contexts.

It does not take a caller-supplied plan.

Execution must:

1. validate request shape;
2. identify the selected variants;
3. freshly evaluate current runtime prerequisites against loaded contexts;
4. convert fresh reports to prerequisite states;
5. invoke the relevant I-021 resolver;
6. execute only the fresh returned plans.

No network dereference of external authority/entity URLs is required or
allowed.

## Suggested public API decomposition

Do not create one generic “external URI resolver” request.

Keep operation semantics explicit with separate request keys/surfaces:

- authority exact request/result/plan;
- authority approximate request/result/plan;
- identity request/result/plan;
- identifier request/result/plan.

Identity and identifier may share a private/reference-plan representation, but
their public requests remain typed so issuer-scoped identifiers cannot be
mistaken for entity identity.

All plans/results expose deterministic provenance appropriate to the family.

### Authority provenance

At minimum:

- authority key;
- corpus/variant;
- mapping/projection IDs;
- assessment;
- mapping/projection review/digests;
- ontology lock/bundle;
- native binding identity;
- prerequisite fingerprint/source contract;
- approximation/loss record when applicable.

### Identity/identifier provenance

At minimum:

- reference kind/query role;
- corpus/variant;
- parent mapping ID;
- reference ID;
- authority system or issuer;
- external entity/literal ID;
- identity strength when relevant;
- parent mapping semantic digest/review;
- reference evidence;
- native binding identity;
- prerequisite fingerprint/source contract.

## Error/refusal precedence

Request-shape validation first.

Then preserve I-007 runtime prerequisite precedence before mapping/reference
authorization:

1. request type/vocabulary/issuer/authority/corpus shape;
2. compiled index structure and reviewed-payload coherence;
3. selected variant/prerequisite freshness;
4. family-specific lookup;
5. review/reference authority;
6. multiplicity;
7. executable native-shape validation at execution time.

A stale or incompatible loaded corpus must not be masked by an identity or
identifier lookup error after a valid request.

Likely family-specific categories should distinguish:

- reference absent;
- non-exact identity only;
- multiple authority/identity/identifier bindings;
- authority mapping non-exact in exact mode;
- approximate authority loss not accepted;
- malformed/forged compiled reference;
- reference resolved but native binding shape unsupported for execution.

The reviewed plan should freeze exact names.

## Negative controls

I-021 must prove:

- semantic-pivot target cannot satisfy authority/identity/identifier requests;
- authority-value row cannot satisfy semantic-pivot resolution;
- entity identity cannot be inferred from an authority URL/string;
- probable/related/ambiguous identity cannot execute as same-entity;
- identifier literal under issuer A cannot resolve under issuer B;
- provenance-source and locator cannot enter identity/identifier resolution;
- reference with no native binding cannot execute;
- native binding without explicit execution shape cannot execute;
- caller-modified `ExternalReferenceIR` cannot inherit parent review;
- caller-modified parent external-reference tuple cannot inherit review;
- forged mapping semantic payload/digest/review combinations fail closed;
- no ontology/authority URL is dereferenced;
- no label/name/hostname matching occurs.

## Exact/approximate semantic compatibility

I-021 must not alter:

- I-006 exact semantic request/result/fingerprint contracts;
- I-020 approximate semantic request/result/fingerprint contracts;
- exact/approximate conjunction behavior;
- semantic index contents;
- projection semantic payload behavior.

Adding `mapping_semantic_payload` to `NativeRecordIR` is intentionally
outside existing semantic plan fingerprints.

Focused CI should rerun I-005 compiler controls plus I-006/I-020 fingerprint
anchors.

## Plan handoff

The reviewed implementation plan should freeze:

1. additive `NativeRecordIR.mapping_semantic_payload`;
2. canonical payload/hash/review validation;
3. exact authority API;
4. approximate authority API reusing I-020 loss semantics;
5. same-entity-only identity API;
6. exact issuer-scoped identifier API;
7. family-specific deterministic plan/result/fingerprint algorithms;
8. full non-semantic index validation;
9. fresh loaded-runtime executor surfaces;
10. explicit execution-shape requirement;
11. exact/approximate semantic compatibility anchors;
12. tests-only RED before production changes.

No production behavior should change before that plan is independently
reviewed.
