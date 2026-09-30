# I-021 plan — productionize authority, identity and identifier resolution

Issue: #238  
Parent: P-004 #202, Workstream B  
Research: `docs/research/I-021-authority-identity-identifier-runtime.md`  
Policy dependency: R-017 #51  
Baseline: main `4d1cc4b7fc83dd003cda4081a9c474aeb23d0fe7`

## Exit condition

ontoTF exposes deterministic, fail-closed resolver/executor surfaces for the
three already-compiled R-017 reverse-index families:

- authority values;
- external entity identity;
- issuer-scoped identifiers.

The implementation:

- never routes these requests through `semantic_index`;
- never treats URI/string shape as semantic or identity authority;
- supports exact and reviewed approximate authority-value filters;
- executes entity identity only for reviewed `same-entity`;
- executes catalogue identifiers only under exact issuer/namespace scope;
- freshly revalidates loaded runtime prerequisites before native access;
- accepts only explicit supported native execution shapes;
- preserves all I-006/I-020 semantic resolver/executor behavior and
  fingerprints.

No new authority mappings, entity links, identifiers, corpus data, source
schema, ontology reasoning, linked-data dereference or structural execution is
introduced.

## Compatibility boundary

I-021 is additive.

Do not change the public shape/semantics/fingerprint payloads of:

- exact semantic request/plan/result/conjunction contracts;
- approximate semantic request/plan/result/conjunction contracts;
- exact/approximate semantic execution results;
- existing runtime prerequisite reports;
- `AuthorityKey`, `IdentityKey`, `IdentifierKey`;
- existing source mapping schemas.

The only compiled-IR shape addition is a defaulted optional canonical parent
mapping payload on `NativeRecordIR`. Existing exact/approximate semantic
fingerprints must remain unchanged.

## Additive compiled review payload

Extend:

```python
NativeRecordIR(
    ...
    mapping_semantic_payload: str | None = None,
)
```

During `compile_semantic_ir()`, populate this field for every compiled mapping
from the already-validated source mapping:

```python
canonical_json_bytes(
    mapping_semantic_projection_v2(source_mapping)
).decode("utf-8")
```

The field is deterministic reviewed-source material, not new execution
authority.

### Payload invariants

Reference resolution must require, for the selected parent native record:

1. exact non-empty `str`;
2. JSON parse succeeds to an exact object;
3. serialized text is already canonical JSON;
4. SHA-256 of the canonical payload equals
   `NativeRecordIR.mapping_semantic_digest`;
5. the selected release signature contains exactly that
   `(mapping_id, digest)`;
6. the selected release signature contains the parent mapping review;
7. mapping review status is `reviewed`;
8. review's reviewed semantic digest equals the same mapping digest;
9. payload `mapping_id`, `corpus_id`, native binding, native dependencies,
   profiles/capabilities/native state and child-ID sets normalize coherently to
   the selected `NativeRecordIR`;
10. the payload contains exactly one authoritative external-reference child for
    a selected `reference_id`;
11. that child normalizes exactly to the selected `ExternalReferenceIR`.

Malformed/tampered payload or row is `invalid_compiled_ir`.

The resolver must use the payload's child object as the reviewed source of
truth and prove coherence with the compiled row; it must not reconstruct
missing source presence from normalized dataclass fields.

No source JSON file is reread at runtime.

## Non-semantic index validation

Add a reference-resolution-specific compiled-IR validation path. It may reuse
existing private variant/release/prerequisite primitives, but exact semantic
request behavior must remain unchanged.

### authority_index

Validate:

- key is exact `AuthorityKey`;
- rows are exact `TargetBindingIR`;
- key authority system equals selected row ontology lock's `ontology_id`;
- key authority resource equals row target;
- key formal kind and semantic role equal row fields;
- route is exactly
  `authority-value / authority-value-filter`;
- selected variant/release/mapping/projection review and digests are coherent;
- I-020 reviewed projection semantic payload validation applies unchanged;
- duplicate key buckets fail.

### identity_index

Validate:

- key is exact `IdentityKey`;
- rows are exact `ExternalReferenceIR`;
- route is exactly
  `entity-identity / identity-filter`;
- key authority system, external entity ID and identity strength equal row
  fields;
- identity strength is in the existing closed vocabulary;
- row has an explicit native binding;
- row has exactly one reviewed parent native record in the selected variant;
- parent mapping payload proves row membership/coherence;
- duplicate key buckets fail.

### identifier_index

Validate:

- key is exact `IdentifierKey`;
- rows are exact `ExternalReferenceIR`;
- route is exactly
  `catalogue-identifier / identifier-filter`;
- key issuer/namespace and literal ID equal row fields;
- row has an explicit native binding;
- row has exactly one reviewed parent native record in the selected variant;
- parent mapping payload proves row membership/coherence;
- duplicate key buckets fail.

### Explicit non-index families

`provenance-source` and `locator` remain non-resolvable by I-021.

A forged row of either kind inserted into identity/identifier indexes is
`invalid_compiled_ir`.

## Parent semantic native state

Do not make `NativeRecordIR.native_state` a surrogate reference-authorization
flag.

A reviewed identity/identifier child under a `native-only` parent mapping can
still be exact reference authority.

Conversely, `positive` does not authorize an external reference by itself.

The reviewed child inside the digest-bound parent payload plus explicit native
binding and fresh runtime prerequisite state is the authority boundary.

No new behavior is inferred for external references under `unsupported` or
`ambiguous` mappings merely from those labels. If such a row is present and
passes the accepted source contracts, the reference-specific child review
binding remains decisive; tests must include a `native-only` positive control
to prevent accidental coupling to common-pivot capability state.

## Public resolver contracts

Add versioned constants, names finalized as:

```python
EXACT_AUTHORITY_RESOLVER_CONTRACT = "tfont-exact-authority-resolver-v1"
APPROXIMATE_AUTHORITY_RESOLVER_CONTRACT = "tfont-approximate-authority-resolver-v1"
IDENTITY_RESOLVER_CONTRACT = "tfont-identity-resolver-v1"
IDENTIFIER_RESOLVER_CONTRACT = "tfont-identifier-resolver-v1"
```

Each family has its own fingerprint-algorithm constant.

Keep requests explicitly typed; do not create a generic URI/reference resolver.

## Exact authority request

Add immutable:

```python
AuthorityResolveRequest(
    key: AuthorityKey,
    corpora: tuple[str, ...],
    authority_mode: str = "exact",
)
```

Validation:

- exact request type;
- `authority_mode == "exact"`;
- exact `AuthorityKey`;
- all key fields non-empty strings;
- corpora exact non-empty tuple of unique non-empty strings;
- canonical UTF-16 corpus ordering.

Add:

`authority_resolve_exact(ir, request, prerequisites)`.

Per corpus:

1. validate IR/reference-index shape;
2. select one current variant using existing prerequisite precedence;
3. find rows for exact authority key and selected variant/corpus;
4. validate every row against release/review/projection payload;
5. if more than one exact row exists, fail
   `multiple_authority_bindings`;
6. if exactly one exact row exists, build exact authority plan;
7. otherwise:
   - if close/broader/narrower rows exist, fail
     `non_exact_authority_mapping`;
   - if only related exists, fail `non_substitutive_authority_mapping`;
   - if no row exists, fail `authority_reference_absent`.

Do not choose by source ordering, label, capability name or URI.

The selected authority row carries profile/capability. Preserve current
capability/prerequisite safety: the selected row's declared profile/capability
must be valid for the selected release. Do not require the request itself to
guess a capability.

## Approximate authority request

Add immutable:

```python
ApproximateAuthorityResolveRequest(
    key: AuthorityKey,
    corpora: tuple[str, ...],
    authority_mode: str = "approximate",
    accept_losses: tuple[str, ...] = (),
)
```

Add:

`authority_resolve_approximate(ir, request, prerequisites)`.

Reuse I-020 request-loss validation, approximation-envelope validation, loss
effects and direction semantics.

Per corpus:

1. validate all authority rows first;
2. exact authority row wins with zero loss;
3. multiple exact rows fail;
4. with no exact row:
   - related is non-substitutive;
   - close/broader/narrower require reviewed eligible approximation;
   - multiple eligible approximate rows fail
     `multiple_approximate_authority_bindings`;
   - every required loss must be caller-accepted;
5. produce authority-specific loss record/provenance.

The authority result stays an authority-value filter; it never enters semantic
comparison/index lookup.

Multi-corpus comparison uses I-020's exact/uniform/heterogeneous loss-shape
rules.

## Authority plan/result

Use separate authority dataclasses rather than `ExactNativePlan` because the
request key and query role are different.

At minimum the plan retains:

- resolver contract;
- corpus ID;
- authority key;
- authority mode;
- variant/profile-release/prerequisite identity;
- mapping/projection IDs;
- profile/capability;
- assessment;
- native execution binding identity/binding;
- native dependencies;
- mapping/projection digests and reviews;
- ontology lock/bundle identity;
- evidence;
- approximation/loss record when applicable;
- deterministic plan fingerprint.

Exact and approximate authority result types retain canonical plan ordering,
comparison state, losses and fingerprints.

## Identity request

Do **not** make identity strength a caller-selected execution mode.

Add immutable:

```python
IdentityResolveRequest(
    authority_system: str,
    external_entity_id: str,
    corpora: tuple[str, ...],
)
```

Add:

`identity_resolve(ir, request, prerequisites)`.

For each corpus:

1. select current variant using normal prerequisite precedence;
2. inspect all identity-index buckets matching authority system + external
   entity ID;
3. validate every candidate against reviewed parent mapping payload;
4. collect `same-entity` rows;
5. if exactly one same-entity row remains, build identity plan;
6. if more than one same-entity row remains, fail
   `multiple_identity_bindings`;
7. if no same-entity row exists but probable/related/ambiguous rows exist, fail
   `identity_not_exact` and retain available strengths in the problem
   explanation if practical;
8. if no reviewed row exists, fail `identity_reference_absent`.

`probable-same-entity`, `related-record` and `ambiguous-identity` never
produce an executable I-021 plan.

No I-020 under/overcoverage vocabulary is applied to identity strengths.

## Identity plan/result

At minimum retain:

- corpus/variant;
- parent mapping ID;
- reference ID;
- reference kind/query role;
- authority system;
- external entity ID;
- identity strength (= `same-entity`);
- mapping semantic digest/review;
- reference evidence;
- authoritative child reference fingerprint derived from canonical payload;
- native binding identity/binding;
- native dependencies;
- prerequisite fingerprint/source contract;
- plan/result fingerprint.

The child reference fingerprint is:

`sha256(canonical_json_bytes(authoritative_reference_child))`

with the normal `sha256:` prefix. It is provenance inside the reviewed parent
mapping, not an independent review digest.

## Identifier request

Add immutable:

```python
IdentifierResolveRequest(
    key: IdentifierKey,
    corpora: tuple[str, ...],
)
```

Add:

`identifier_resolve(ir, request, prerequisites)`.

Per corpus:

1. exact issuer + literal key only;
2. validate every row through reviewed parent payload;
3. exactly one row -> identifier plan;
4. more than one row -> `multiple_identifier_bindings`;
5. no row -> `identifier_reference_absent`.

Equal literal under a different issuer is not a candidate.

No approximate identifier mode exists.

Identifier plan/result retains the same parent/reference/runtime provenance as
identity, replacing authority/identity fields with issuer + literal ID.

## Request/error precedence

Request-shape validation occurs before runtime lookup.

For a structurally valid request:

1. compiled reference-index structural/payload validation;
2. selected variant/prerequisite coherence and freshness;
3. family lookup;
4. review/identity/assessment authorization;
5. multiplicity;
6. caller loss acceptance where applicable.

Malformed compiled payload/row is always `invalid_compiled_ir`; never
downgrade it to “absent”.

Reuse `SemanticResolutionError` / `SemanticResolutionProblem` as the common
fail-closed resolver error envelope unless RED proves that family-specific
fields require a new type. New categories remain family-specific as above.

## Fingerprints

Introduce separate JCS/SHA-256 algorithms for:

- exact authority plan/resolution;
- approximate authority plan/resolution;
- identity plan/resolution;
- identifier plan/resolution;
- reference child fingerprint.

Fingerprint payloads include request family explicitly so no authority,
identity, identifier or semantic request can collide by sharing a native
binding.

Approximate authority resolution fingerprint includes the full canonical
caller `accept_losses`; non-exact authority plan/loss record binds consumed
authorization exactly as I-020 does.

Identity/identifier plan fingerprints include the authoritative child
reference fingerprint and parent mapping digest/review.

## Execution

Add execution contract constants and typed results for:

- exact authority execution;
- approximate authority execution;
- identity execution;
- identifier execution.

Public functions conceptually:

- `execute_exact_authority(...)`;
- `execute_approximate_authority(...)`;
- `execute_identity(...)`;
- `execute_identifier(...)`.

Each takes:

- compiled IR;
- typed request;
- loaded corpus contexts.

No public function accepts a caller-created plan.

### Fresh execution sequence

1. validate request/context family;
2. identify selected variants;
3. freshly evaluate current runtime prerequisites using a new
   reference/authority execution source-contract string;
4. convert reports to prerequisite states;
5. call the corresponding I-021 resolver;
6. validate supported native execution shape;
7. execute fresh plans;
8. return canonical per-corpus nodes + fresh report + plan + full resolution.

### Supported native shapes

Only:

- `value-predicate`;
- `value-set-predicate`.

Reuse the already-tested I-008/I-020 native predicate execution machinery.

A reviewed resolver plan whose binding has no explicit execution shape may
resolve successfully but execution fails
`unsupported_native_binding`.

Do not infer execution shape from feature/value presence.

## Resolver-only versus executable rows

Resolver success means reviewed lookup authority exists.

Execution additionally requires an explicit supported execution shape.

This distinction is required because historical I-005 reference fixtures are
reviewed/indexed but intentionally have `execution_shape=None`.

Tests must include both:

- resolver success + execution refusal for legacy shape-less row;
- resolver and execution success for an otherwise identical source row with
  explicit `value-predicate`.

## No conjunction/composition in I-021

I-021 does not introduce:

- arbitrary conjunction of reference requests;
- identity + semantic conjunction;
- identifier + semantic conjunction;
- same-key multi-binding composition.

Those can be planned after R-018/structural runtime work. One request may still
target multiple corpora deterministically.

## TDD RED

After this plan is independently reviewed and merged, create
`tests/i021/` before any production changes.

Tests-only RED must cover at least:

### Compiler trust payload

1. `NativeRecordIR.mapping_semantic_payload` exists;
2. canonical payload digest equals parent mapping digest;
3. source-order changes do not alter payload/digest;
4. exact/approximate semantic fingerprints from I-020 remain unchanged.

### Authority exact/approximate

5. exact authority row resolves under `AuthorityKey`;
6. same authority URI cannot satisfy ordinary semantic resolver;
7. close/broader/narrower fail exact authority mode;
8. approximate authority requires reviewed eligible envelope and full caller
   loss acceptance;
9. exact row wins over approximate authority alternative;
10. related is non-substitutive;
11. multiple exact/approximate authority rows fail closed;
12. authority request ordering is deterministic.

### Identity

13. same-entity resolves;
14. probable-same-entity alone fails `identity_not_exact`;
15. related-record alone fails `identity_not_exact`;
16. ambiguous-identity alone fails `identity_not_exact`;
17. same-entity wins when non-exact strengths coexist;
18. multiple same-entity rows fail;
19. request does not accept caller-supplied identity strength;
20. native-only parent mapping can still authorize reviewed exact identity.

### Identifier

21. issuer+literal exact lookup resolves;
22. same literal under another issuer is absent;
23. multiple rows for same issuer/literal/corpus fail;
24. native-only parent mapping can still authorize reviewed identifier.

### Forged IR

25. replaced identity external value fails `invalid_compiled_ir`;
26. replaced identity strength fails;
27. replaced issuer/literal fails;
28. replaced reference native binding fails;
29. replacing both index row and parent normalized external-reference tuple
    still fails without matching reviewed mapping payload;
30. forged payload with old digest fails;
31. forged digest/review with release mismatch fails;
32. provenance/locator row inserted into identity/identifier index fails.

### Execution

33. explicit scalar authority filter executes after fresh runtime evaluation;
34. explicit scalar same-entity filter executes;
35. explicit scalar identifier filter executes;
36. value-set shape executes;
37. shape-less reviewed reference resolves but execution refuses;
38. structural/native unsupported shape refuses;
39. stale/incompatible/mutated loaded state prevents native access;
40. no caller-plan execution path exists.

### Compatibility

41. exact semantic fingerprint anchors remain exact;
42. approximate semantic fingerprint/behavior anchors remain exact;
43. I-005 index separation tests remain green.

RED must be observed on an exact head before production implementation.

## Implementation scope

Expected production files:

- `src/tfont/semantic_ir.py`;
- `src/tfont/semantic_resolver.py`;
- `src/tfont/semantic_execution.py`;
- `src/tfont/__init__.py`;
- `tests/i021/**`;
- `.github/workflows/i021-reference-resolution.yml`.

A small private helper extraction is allowed to share prerequisite/native
predicate machinery, provided exact/approximate semantic public behavior and
fingerprints remain unchanged.

No expected changes to:

- source schemas;
- semantic digest algorithms;
- semantic validation policy;
- production mapping data;
- ontology resources;
- coverage manifests;
- runtime prerequisite schema/evaluator.

Any required change outside this scope requires a plan amendment before code.

## Focused CI

Exact-head Python 3.10/3.12 workflow must:

1. install package;
2. run `tests/i021`;
3. rerun I-005 authority/identity/identifier index controls;
4. rerun I-006 exact semantic resolver anchors;
5. rerun I-020 approximate semantic anchors;
6. rerun the I-021 research probe and compare committed evidence;
7. build a wheel and import all new resolver/executor APIs from the isolated
   wheel.

The authoritative Full repository suite must pass on the final exact head.

## Final adversarial review

Fresh logically-independent review of the implementation exact head must
challenge:

- mapping-payload digest/review binding;
- forged ExternalReferenceIR + forged parent tuple attacks;
- source-presence normalization;
- authority/semantic index isolation;
- authority approximation direction/loss semantics;
- exact authority precedence;
- same-entity-only identity authority;
- probable/related/ambiguous identity refusal;
- issuer-scoped identifier equality;
- native-only reference independence from semantic capability state;
- provenance/locator non-leakage;
- explicit execution-shape boundary;
- fresh runtime revalidation;
- absence of caller-plan trust;
- exact/approximate semantic fingerprint immutability;
- absence of URI/label/hostname inference or network dereference;
- absence of R-018 composition or structural execution scope creep.

Merge only with the reviewed exact head SHA. After merge, read back one exact
authority, one same-entity and one issuer-scoped identifier fixture from
`main`, plus semantic fingerprint anchors, before closing #238.
