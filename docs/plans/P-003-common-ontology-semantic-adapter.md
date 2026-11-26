# P-003 plan: common ontology semantic adapter architecture

**Issue:** #44  
**Type:** design-only architecture amendment  
**Baseline:** `main` after P-002 (`a238522c3048ee077a09e090a4b067b72cec901c`)  
**Inputs:** R-001..R-017, R-017 post-review amendment, A-001, merged I-001/I-002/I-003, merged P-002

## 1. Architecture decision

ontoTF is a reviewed semantic compatibility layer over already-materialized Text-Fabric / Context-Fabric corpora:

```text
source representations
        ↓ corpus-specific materializer/converter
materialized TF / Context-Fabric corpus
        ↓
reviewed native semantic records
        ↓
0..N approved typed target-bearing projections
+ 0..N typed non-projection external references
        ↓
validated active ontology bundle + reviewed bridge closure
        ↓
semantic / authority / identity / identifier resolution
        ↓
native Context-Fabric query plan
        ↓
results + provenance + semantic-loss explanation
```

Baseline ontoTF does **not** own generic JSON/XML/CSV/TEI/PDF/database/API ingestion, arbitrary source-record addressing, network dereferencing, adapter authentication/caching, or a generic sidecar/native-adapter runtime.

A mapping becomes a reviewed **native semantic record** with one native TF/CF binding and zero or more complementary approved target-bearing projections. A target-bearing projection is the smallest reviewed unit that may participate in either the common semantic-pivot reverse index or the authority-value reverse index.

Entity identity, scoped catalogue identifiers, provenance/source references and locator URLs are kept in a separate typed reference collection with their own query/index rules.

`native-only` and `unsupported` remain legitimate reviewed no-target states. `ambiguous` remains a reviewed unresolved-target state whose candidates are typed but non-approved and non-executable.

## 2. Normative semantic basis

The seven-model common pivot remains explicit:

- SKOS;
- OLiA;
- OntoLex-Lemon;
- CIDOC CRM;
- CRMtex;
- LRMoo;
- CRMinf.

Preserve accepted R-002 support roles:

- PROV-O for provenance where used;
- SHACL 1.0 for RDF validation/publication tooling, not runtime query execution;
- Web Annotation as optional publication/targeting profile;
- optional/domain resources such as CRMarchaeo, CRMsci, LexInfo, Lexicog, VarTrans, Getty AAT and PeriodO only when their profile/reference contracts are explicitly activated and reviewed.

No live RDF reasoner, SPARQL endpoint or HTTP ontology lookup is required at runtime.

## 3. Native semantic record

Conceptual shape:

```yaml
native_record:
  mapping_id: stable-id
  corpus_id: stable-corpus-id
  native_binding:
    selector: materialized-TF selector/value/entity/path
    applicability: reviewed source/entity/value domain
    execution_shape: membership | value-predicate | edge-path | identity-key | inspection-only
  native_dependencies: [P-002 dependency ids]
  profiles: [controlled profile ids]
  capabilities: [controlled capability ids]
  native_state: positive | native-only | unsupported | ambiguous
  projections: [0..N approved projections]
  ambiguous_candidates: [0..N typed non-approved candidates]
  external_references: [0..N identity/catalogue/provenance/locator records]
  evidence: [...]
  review: content-bound review
  mapping_semantic_digest: versioned semantic digest
```

### 3.1 TF-native source boundary

The native binding may depend only on the accepted P-002 TF-native dependency kinds:

- `component-present`;
- `node-type-present`;
- `feature-present`;
- `edge-present`;
- `path-present`;
- `native-value-present`;
- `value-domain`;
- `extent-interpretation`.

No `native-adapter`, sidecar path, external record/file field, database/API locator, source-format selector or URI dereference instruction is permitted.

### 3.2 Preserve all eight R-002 assessment meanings

Approved target-bearing projections carry one of:

`exact | close | broader | narrower | related`.

Native-record no-target/unresolved states are:

- `ambiguous` — target choice unresolved; one or more typed candidates; no target reverse execution;
- `native-only` — reviewed native semantics exist but no defensible shared/authority target exists;
- `unsupported` — reviewed negative knowledge.

A `native-only` or `unsupported` record cannot carry an approved target-bearing projection.

## 4. Approved target-bearing projections

Conceptual shape:

```yaml
projection:
  projection_id: stable id
  target: locked IRI/resource id
  reference_kind: semantic-pivot | authority-value
  query_role: semantic-constraint | authority-value-filter
  formal_kind: class | property | skos-concept | named-resource
  semantic_role: controlled R-013 role
  profile_id: controlled R-014 profile
  capability_id: controlled R-014 capability
  assessment: exact | close | broader | narrower | related
  ontology_lock: participating lock identity
  ontology_bundle_requirement: active bundle/profile requirement
  ontology_declaration_evidence: optional locked class/property/domain/range facts
  publication_relation: optional; independently validated
  native_execution_binding: role-compatible TF-native binding
  approximation: optional R-016 reviewed loss/eligibility contract
  evidence: [...]
  review: projection-content-bound review
```

`semantic-pivot` projections route to the common semantic index. `authority-value` projections route to a separate authority-value index. Neither route bypasses parent/profile/bundle/dependency/review prerequisites.

### 4.1 Closed formal kinds

Freeze the first production vocabulary to:

- `class`;
- `property`;
- `skos-concept`;
- `named-resource`.

OWL `ObjectProperty` / `DatatypeProperty` remain locked ontology-declaration metadata, not canonical ontoTF target kinds.

### 4.2 Closed semantic roles

Freeze the first production vocabulary equivalent to:

- `entity-type`;
- `annotation-category`;
- `annotation-value`;
- `relation`;
- `attribute`;
- `lexical-entry-identity`;
- `lexical-form-identity`;
- `lexical-sense-identity`;
- `lexical-concept-identity`;
- `authority-reference`;
- `claim-proposition`;
- `inference-activity`.

Formal kind does not determine semantic role. Semantic role does not determine publication relation. URI syntax determines neither.

### 4.3 Kind/role compatibility

At minimum:

- `class` → entity/category/value roles; not relation/attribute/particular identity;
- `property` → relation/attribute/annotation-category; not entity-type/particular identity;
- `skos-concept` → annotation-value, lexical-concept-identity, authority-reference; not relation/attribute;
- `named-resource` → particular lexical identities, authority-reference, proposition/inference identity; not ontology class/property semantics.

Exceptional RDF multi-typing is represented as separate reviewed projections when execution/publication semantics differ.

### 4.4 Complementarity versus ambiguity

Approved projections are complementary only when all are simultaneously defensible for the same native semantics.

Examples:

- physical-object semantic-pivot projection + material authority-value projection;
- lexical-entry entity-type projection + separately reviewed particular lexical identity reference;
- written-text-segment class + reviewed relation projection.

Unresolved mutually exclusive targets must remain ambiguous candidates and never appear in the approved projection list.

### 4.5 Closed ambiguous candidate envelope

An ambiguous candidate must carry the same target identity dimensions needed to validate a future approved projection:

```yaml
candidate:
  candidate_id: stable id
  target: locked IRI/resource id
  reference_kind: semantic-pivot | authority-value
  query_role: semantic-constraint | authority-value-filter
  formal_kind: class | property | skos-concept | named-resource
  semantic_role: controlled R-013 role
  profile_id: controlled R-014 profile
  capability_id: controlled R-014 capability
  assessment_candidate: exact | close | broader | narrower | related
  ontology_lock: participating lock identity
  ontology_declaration_evidence: optional locked facts
  evidence: non-empty reviewed candidate evidence
```

Candidates deliberately do **not** carry executable native-plan authorization, approximation authorization or positive publication authorization. Candidate evidence may explain why an alternative is plausible; it does not make the alternative executable.

The validator must reject both:

- an opaque ambiguous URI without kind/role/profile/capability/lock evidence;
- an ambiguous candidate placed into the approved projection array.

## 5. Controlled profiles and capabilities

Replace free-form `semantic_domains` as discovery/execution authority with the R-014 controlled catalog.

Core profiles:

- `structural`;
- `linguistic`;
- `lexical`;
- `written-text`;
- `textology`;
- `heritage`;
- `scholarly-inference`.

Optional evidence-gated profiles:

- `archaeology`;
- `scientific-analysis`;
- `lexicography`.

Profile/capability operational state is distinct from mapping assessment:

`active | absent | unavailable`.

A profile is active only when at least one capability is active. A capability is active only when at least one reviewed positive native record actually instantiates it. No profile inheritance auto-activates another profile.

Initial capability IDs are the accepted R-014 catalog:

```text
structural.entity-kind
structural.slot-coverage
structural.edge-traversal
structural.section-navigation

linguistic.part-of-speech
linguistic.morphology
linguistic.syntax
linguistic.discourse

lexical.entry
lexical.form
lexical.sense
lexical.concept
lexical.relation

written-text.segment
written-text.sign
written-text.writing-system
written-text.transcription-recognition

textology.textual-version
textology.witness
textology.fragment-transmission
textology.apparatus-reading
textology.witness-attestation
textology.explicit-omission

heritage.physical-object
heritage.physical-part
heritage.identifier
heritage.material
heritage.place-provenance
heritage.custody-location

scholarly-inference.claim
scholarly-inference.inference
scholarly-inference.meaning-comprehension
scholarly-inference.provenance-assessment
```

Optional-profile capabilities require a versioned catalog addition backed by demonstrated semantics; current seven-pilot evidence does not retroactively activate archaeology, scientific-analysis or lexicography.

Profile/capability state is discovery information only. Target execution requires an exact requested tuple in the appropriate target index.

## 6. Active ontology bundle and bridge prerequisite

R-015 is authoritative for semantic composition.

The active bundle identity is content-addressed from:

```text
active profile-contract IDs
+ full I-002 semantic ontology-lock identities
+ reviewed term-scoped bridge artifacts referenced by active edges
+ active dependency bindings
```

using accepted JCS/SHA-256 semantics.

A bridge is executable only when endpoint lock IDs/releases/payload digests, scoped terms, edge scope, review/content digest and compatibility all match; v1 active bundle execution requires exact bridge strength.

A term-scoped bridge never implies ontology-wide equivalence.

Preserve known skew cases including CRMtex historical FRBRoo/LRMoo continuity and CRMarchaeo 2.1.1 dependency skew against current CRM/CRMsci releases.

Inactive optional profiles do not create bridge failures. An activated optional profile with unresolved required bridges becomes unavailable/non-executable.

No approximation path may repair an invalid R-015 active bundle.

## 7. R-017 routing and external references

### 7.1 Target-bearing families

These remain approved projections because they use the R-002 assessment and R-013 target-kind/role contract:

- `semantic-pivot` + `semantic-constraint` → `semantic_index`;
- `authority-value` + `authority-value-filter` → `authority_index`.

Both require a real external target. `native-only` and `unsupported` therefore cannot masquerade as target-bearing reference records.

Exact target-bearing mappings still require the same derived upstream execution prerequisite. Non-exact target-bearing mappings delegate to R-016.

### 7.2 Non-projection reference kinds

These live in `external_references`:

- `entity-identity`;
- `catalogue-identifier`;
- `provenance-source`;
- `locator`.

Their query roles are constrained to reviewed combinations equivalent to:

- identity filter;
- scoped identifier filter;
- metadata filter where a native field is explicitly queryable, otherwise explanation-only;
- explanation-only.

They never enter semantic or authority target indexes.

### 7.3 Identity and identifier semantics

Entity identity uses a separate vocabulary equivalent to:

- `same-entity`;
- `probable-same-entity`;
- `related-record`;
- `ambiguous-identity`.

Do not reuse `broader/narrower` for entity identity.

Catalogue identifiers are keyed by issuing authority/namespace plus literal/code; equal strings from different issuers are not equal identifiers.

A provenance/source or locator record requires a real external value but never creates network access or semantic-target status.

## 8. Publication predicates

Publication predicates are projection/reference-specific and never mechanically derived from ontoTF assessment.

- SKOS mapping predicates require concept-to-concept legality;
- `owl:equivalentClass` requires class-to-class semantics;
- `owl:equivalentProperty` requires property-to-property semantics;
- canonical `owl:sameAs` uses the HTTP OWL namespace IRI and is locally valid only for reviewed `entity-identity` + `same-entity`;
- RDFS subclass/subproperty relations require actual hierarchy semantics;
- OntoLex predicates retain their domain/range meaning.

R-017 can locally prove only the same-entity `owl:sameAs` case. Other positive publication claims delegate fail-closed to the R-013 formal-kind-aware validator. Noncanonical lookalike IRIs are never normalized by spelling.

## 9. Approximate execution

R-016 is authoritative.

Requests expose at least:

```text
semantic_mode = exact | approximate
accept_losses = subset of {undercoverage, overcoverage}
```

Policy:

- `exact`: executable only after upstream prerequisites pass;
- `broader`: approximate mode only, reviewed eligibility, caller accepts undercoverage;
- `narrower`: approximate mode only, reviewed eligibility, caller accepts overcoverage;
- `close`: informative-only by default; execution requires a separate reviewed loss contract and caller acceptance;
- `related`: never a substitute constraint;
- `ambiguous`: never auto-selected;
- `native-only`: no target reverse execution;
- `unsupported`: refuse.

Assessment direction is native/source → target; reverse execution through `broader` under-covers and through `narrower` over-covers.

Approximation eligibility, loss shape, rationale/evidence and review identity participate in projection semantic identity/review binding.

Approximation cannot repair parent incompatibility, unavailable capability, invalid active bundle, missing/stale bridge, unresolved lock or non-executable TF-native dependency.

Every required atom resolves independently; no atom is silently dropped. Losses compose by union.

Multi-corpus comparison state is at least:

- `exactly-comparable`;
- `approximately-comparable`;
- `heterogeneous-loss`;
- `partial/non-executable`.

Cross-corpus aggregates remain exact-only by default. Approximate aggregation requires explicit boolean opt-in and uniform non-empty loss shape; heterogeneous-loss aggregates remain forbidden in v1.

## 10. Common semantic IR

Every compiled IR carries fingerprints for:

- parent materialized corpus identity / expected-parent manifest;
- profile catalog and per-profile contract versions;
- native dependency contract version;
- mapping semantic contract/digest version;
- active ontology-bundle identity;
- participating ontology-lock semantic identities;
- bridge review/content identities;
- reference policy/catalog version;
- approximation policy version where relevant.

Authoritative indexes:

```text
native_index[
  corpus,
  native-binding-identity
] -> native record + projections + external references

semantic_index[
  profile,
  capability,
  target,
  formal-kind,
  semantic-role
] -> per-corpus approved semantic-pivot bindings

authority_index[
  authority-system,
  authority-resource,
  formal-kind,
  semantic-role
] -> per-corpus approved authority-value bindings

identity_index[
  authority-system,
  external-entity-id,
  identity-strength
] -> per-corpus reviewed native entity bindings

identifier_index[
  issuer-or-namespace,
  literal-id
] -> per-corpus native identifier bindings

capability_index[
  corpus,
  profile,
  capability
] -> operational state + summary counts + record ids
```

`semantic_index` and `authority_index` exclude native-only, unsupported, unresolved ambiguous candidates, provenance/locator links and catalogue identifiers.

A resolved target atom exposes at least requested target/routing/kind/role/profile/capability, corpus, mapping/projection IDs, assessment, native binding, prerequisite state, ontology-bundle ID, parent identity, review/evidence identity and any approximation/loss record.

## 11. Resolver contract

Protocol-independent flow:

```text
semantic_capabilities
    ↓ discovery only
semantic_resolve / authority_resolve / identity_resolve
    ↓ authoritative per-corpus resolution
native query plan(s)
    ↓
semantic_search / Context-Fabric execution
    ↓
results + exact resolution provenance
```

`semantic_capabilities` returns compact profile/capability summaries and never authorizes execution by itself.

Fail-closed target-resolution order:

1. validate request vocabulary/version/routing;
2. establish parent/profile operational availability;
3. validate active ontology bundle/bridge closure;
4. locate the exact requested tuple in the correct index family;
5. validate projection review/content identity;
6. validate TF-native dependency closure and native binding executability;
7. apply R-016 mode/loss gates;
8. compile one native plan per corpus;
9. compute comparison/loss state and provenance fingerprint.

Identity and identifier resolution consume the same upstream prerequisite before producing a native plan, but use their own index/strength/scope contract.

No fuzzy labels, namespace inference, ontology hierarchy inference, stale cached fallback or similar-feature fallback.

Search executes only resolver-produced executable plans bound to the resolution fingerprint. Missing required atoms fail the request rather than being silently dropped.

Runtime execution reads materialized TF/Context-Fabric only.

## 12. Seven-corpus POC acceptance

Required pilots:

- BHSA;
- CUC;
- one ETCBC Syriac corpus;
- ETCBC ExtraBiblical;
- Pseudepigrapha-TF;
- ORACC-TF;
- TLHdig-TF.

Minimum scenarios:

1. exact OLiA noun across BHSA/Syriac/ExtraBiblical;
2. exact OLiA plural/person conjunction across at least two linguistic corpora;
3. OntoLex lexical-entry mixed-strength case across BHSA plus at least two close/native variants;
4. CRMtex TX7 written-text segment across CUC/ORACC/TLH with reviewed strengths preserved;
5. CRM E22 positive controls only where native identity really denotes a carrier;
6. Pseudepigrapha textual-version/textology positive case with manuscript physical-carrier overprojection rejected;
7. ORACC material/period/place authority-value examples outside `semantic_index` unless separately reviewed as semantic-pivot targets;
8. TLH witness/fragment/editorial native-only/ambiguous controls;
9. explicit native-only, unsupported, ambiguous, related, unreviewed-close, unavailable-bundle, stale-bridge and incompatible-parent failures;
10. ORACC synthetic/empty slots treated as `technicalAnchor`, never semantic sign content or sidecar justification.

First prove a thin vertical slice:

```text
one exact ontology concept
 -> two or more corpora
 -> distinct native TF bindings
 -> executable native plans
 -> explained result provenance
```

before broader infrastructure generalization.

## 13. Migration from current production contracts

### I-001

Keep JSON Schema 2020-12, strict closed shapes, duplicate/non-JSON fail-closed loading, stable diagnostics and packaged canonical schemas.

Versioned amendments:

- mapping schema v1 → v2 native-record/projection/candidate/reference contract;
- profile schema evolves from free-form `semantic_domains` to controlled catalog/profile-capability declarations while preserving P-002 dependencies;
- add/close ontology-bundle/bridge/reference records as required.

No in-place reinterpretation of mapping v1.

### I-002

Keep RFC 8785/JCS, SHA-256, source/evidence boundaries, ontology-lock semantic identity, UTF-16 set ordering/duplicate rejection and depth/recursion guards.

`MAPPING_SEMANTIC_ALGORITHM` requires a new version because projections, typed ambiguity, routing/reference kinds, profile/capability membership, approximation authorization and projection-level review binding change semantic identity.

A v1 mapping digest must never validate a migrated v2 record.

Profile semantic identity binds controlled catalog/profile contract, P-002 dependency content, mapping-v2 identities and semantic-bundle requirement/identity fields that determine execution. A source profile file by itself does **not** prove that the runtime active bundle is executable; that is derived cross-artifact/runtime state.

### I-003

Keep parent component identity unchanged.

### P-002

Keep the exact eight TF-native dependency kinds and profile-owned registry. Structural validity remains insufficient for execution; I-004 validates cross-artifact resolution, evidence/content binding and closure.

Never reintroduce pre-A-001 sidecar/native-adapter vocabulary.

### Mapping-v1 field migration

| v1 field | P-003 destination |
|---|---|
| `mapping_id` | native record identity |
| `profile_id` | controlled profile/capability membership |
| `native_selector` | TF-native binding |
| `native_dependencies` | P-002 dependency refs |
| `external_target` | approved target-bearing projection, if any |
| `candidate_projections` | typed `ambiguous_candidates` |
| positive `assessment` | projection-level assessment |
| ambiguous/native-only/unsupported | native-record state |
| `publication_relation` | projection/reference-specific publication field |
| `applicability` | native binding applicability |
| `ontology_lock` | projection/candidate ontology lock/bundle requirement |
| `evidence` | record/projection/candidate/reference evidence as appropriate |
| `review` | content-bound review authority |
| `mapping_semantic_digest` | new v2 semantic digest |

Automatic migration is allowed only when the v1 row is semantically unambiguous under the new contract. New kind/role/profile/capability/reference classification must be re-reviewed, not guessed.

## 14. I-004 boundary

Existing I-004 #36 is the first production consumer after P-003 acceptance.

It owns deterministic validation of controlled vocabularies, cross-artifact IDs, P-002 dependency closure/component authority, ontology target/lock membership, kind/role compatibility, approved projection versus ambiguity/no-target consistency, bundle/bridge inputs, evidence digests, review/content binding, approximation contract, R-017 routing/identity rules and parent required-component consistency.

It does not execute corpus queries, fetch ontology/network resources or infer meaning from labels/namespaces.

## 15. Dependency-ordered implementation decomposition

Every production ticket follows:

`research → plan → RED → minimal implementation → focused/full exact-head CI → fresh logically-independent adversarial review`.

1. **I-004 #36 — semantic validator.** Mapping/profile/bundle/reference vNext schemas, cross-artifact semantic validation, mapping-digest migration, exact/native-only/unsupported/ambiguous/reference fixtures.
2. **Semantic IR compiler.** Native/projection/candidate/reference IR, semantic/authority/identity/identifier indexes, capability summaries; no Context-Fabric execution.
3. **Exact resolver thin slice.** `semantic_capabilities`, exact `semantic_resolve`, one exact concept across at least two corpora, native-plan explanation/provenance.
4. **Context-Fabric execution handoff.** Execute only resolver-produced TF/CF plans, enforce plan fingerprint, return result provenance.
5. **Approximate resolution.** R-016 reviewed eligibility, caller losses, loss records, conjunction union, comparison states, exact-only aggregate default.
6. **Authority/identity/identifier resolution.** R-017 target/reference index families, same-entity rules, scoped identifiers, explanation-only provenance/locators with the same upstream gate.
7. **Seven-pilot POC package.** Promote reviewed R-011 evidence into versioned fixtures/mappings and full positive/negative suite. Unreviewed schema remains unreviewed.

## 16. Required RED cases for later implementation

At minimum reject:

1. opaque target without formal kind/role;
2. unknown kind/role/profile/capability/reference vocabulary;
3. class/property/SKOS kind-role incompatibility;
4. native-only/unsupported record carrying approved target projection;
5. ambiguous candidate lacking typed target envelope;
6. ambiguous candidate entering approved target index;
7. complementary projections collapsed into ambiguity;
8. URI/local-name inference of kind/semantics;
9. assessment auto-generating SKOS/OWL publication relation;
10. noncanonical OWL lookalike predicate accepted as canonical;
11. ORACC generic document → CRM E22 overprojection;
12. Pseudepigrapha manuscript → physical-carrier overprojection;
13. TLH surface → CRMtex TX7 overprojection;
14. authority-value projection entering `semantic_index`;
15. provenance/locator/catalogue reference entering target index;
16. same identifier literal across issuers conflated;
17. `same-entity` replaced by broader/narrower identity semantics;
18. profile/capability match alone authorizing execution;
19. active optional profile with unresolved bridge executing;
20. approximation repairing stale/missing bridge or incompatible parent;
21. broader reverse execution without accepted undercoverage;
22. narrower reverse execution without accepted overcoverage;
23. close executing without reviewed loss contract;
24. related/ambiguous used as substitute constraint;
25. required conjunction atom silently dropped;
26. heterogeneous-loss approximate aggregate accepted;
27. `technicalAnchor` treated as source-sign semantics;
28. outside-TF sidecar/path/backend smuggled through source dependency/native binding;
29. exact authority/identity/identifier filter executing without derived upstream prerequisite.

## 17. Independent review gate

The final P-003 design head requires fresh logically-independent skeptical review against R-001..R-017 plus the R-017 amendment, A-001, merged P-002, current I-001/I-002/I-003 behavior, authoritative ontology semantics already evidenced by the research tickets and all seven pilot boundaries.

Review must try to falsify:

1. any recreation of a generic outside-TF runtime carrier;
2. mechanical distinction between complementarity and ambiguity;
3. independence of target kind, semantic role, routing kind, assessment and publication relation;
4. leakage among semantic, authority, identity, identifier and provenance index families;
5. approximation bypass of bundle/parent/review gates;
6. discovery state becoming concept execution authority;
7. mapping-v1 migration silently preserving an invalid semantic digest;
8. any required POC negative control becoming executable.

Merge P-003 only when the exact design head has no blocker. Production implementation begins only afterward.
