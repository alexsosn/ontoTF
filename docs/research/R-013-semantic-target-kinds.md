# R-013: common semantic target kinds and semantic roles

**Status:** research complete; revised after accepted R-011 and fresh skeptical review; pending final logically-independent adversarial review  
**Issue:** #47  
**Recorded:** 2026-09-07  
**Depends on:** accepted R-002/R-003/R-005, merged R-006/R-007/R-008/R-009/R-010/R-011/R-012, roadmap guardrail #45

## Decision

ontoTF needs **two independent controlled dimensions** for every common semantic projection:

1. **formal target kind** — the stable cross-encoding structural kind of the target term/resource;
2. **semantic role** — what that target means in the ontoTF mapping contract and how the reviewed native binding may be executed.

A third concern, **ontology-artifact declaration metadata**, records encoding-specific facts such as `rdf:Property`, `owl:ObjectProperty`, `owl:DatatypeProperty`, class memberships, domain/range declarations, and source ontology release. Those declarations are evidence for validation/publication, but they are **not** the canonical ontoTF target-kind vocabulary.

The minimum first-profile formal-kind vocabulary is:

- `class`
- `property`
- `skos-concept`
- `named-resource`

The minimum first-profile semantic-role vocabulary is:

- `entity-type`
- `annotation-category`
- `annotation-value`
- `relation`
- `attribute`
- `lexical-entry-identity`
- `lexical-form-identity`
- `lexical-sense-identity`
- `lexical-concept-identity`
- `authority-reference`
- `claim-proposition`
- `inference-activity`

These are research-contract names, not frozen production enum spellings. P-003 may rename them but must preserve the distinctions. R-014 owns final profile/capability identifiers; R-017 owns final authority-reference semantics.

The governing invariant is:

> **Formal target kind does not determine semantic role; semantic role does not determine publication relation; ontology serialization does not redefine canonical target kind. Query execution is authorized by a reviewed `(profile, target, formal-kind, semantic-role, native binding, ontology lock)` tuple, not by URI syntax, labels, or ontology inference alone.**

## 1. Why one `external_target` URI is insufficient

The accepted corpus family already requires targets with materially different semantics:

```text
olia:Noun
  formal kind: class
  semantic role: annotation-value

crmtex:TXP4_has_segment
  formal kind: property
  semantic role: relation

external-dictionary:sense-123
  formal kind: named-resource
  semantic role: lexical-sense-identity

PeriodO period URI
  formal kind: skos-concept
  semantic role: authority-reference
```

One opaque URI cannot tell the resolver whether to compile:

- node/type membership;
- feature/value filtering;
- entity-valued edge/path traversal;
- literal-valued attribute filtering;
- identity lookup;
- authority navigation;
- claim/inference provenance.

It also cannot determine publication-predicate legality. A ontoTF `exact` assessment does not imply `skos:exactMatch`, `owl:equivalentClass`, `owl:equivalentProperty`, or `owl:sameAs`.

## 2. Standards evidence

### 2.1 OLiA

OLiA is an OWL2/DL architecture with annotation models, a Reference Model, and linking models. The Reference Model exposes shared grammatical concepts such as `olia:Noun`, `olia:Plural`, and related values as classes, while system/annotation models also use properties.

Primary sources:

- <https://acoli-repo.github.io/olia/>
- <https://acoli-repo.github.io/olia/owl/>

Consequences:

- OLiA category/value targets can be `class` + `annotation-value`;
- an OLiA property target is canonical ontoTF kind `property`, with role determined separately;
- OLiA linking-model subclass relations are prior art/evidence, not runtime permission for ontoTF to infer new executable mappings.

### 2.2 SKOS

SKOS mapping properties (`exactMatch`, `closeMatch`, `broadMatch`, `narrowMatch`, `relatedMatch`) are concept-mapping predicates whose intended operands are SKOS concepts.

Primary source:

- <https://www.w3.org/TR/skos-reference/>

Consequences:

- `skos-concept` remains a distinct ontoTF formal kind because concept-scheme and publication-mapping semantics are materially different from a generic named resource;
- ontoTF assessment is formalism-neutral and must not be mechanically serialized as a SKOS mapping predicate;
- an OWL class or ontology property does not become a SKOS concept merely because the ontoTF assessment vocabulary happens to contain the words `exact`, `close`, `broader`, etc.

### 2.3 OntoLex-Lemon

OntoLex distinguishes ontology classes such as `LexicalEntry`, `Form`, `LexicalSense`, and `LexicalConcept`, particular instances of those classes, and properties such as `sense`, `reference`, and `canonicalForm`.

Primary source:

- <https://www.w3.org/community/ontolex/wiki/Final_Model_Specification>

This proves that formal kind and semantic role are independent:

```text
ontolex:LexicalSense
  kind: class
  role when classifying native sense entities: entity-type

external-dictionary:sense-123
  kind: named-resource
  role: lexical-sense-identity

ontolex:sense
  kind: property
  role: relation
```

A gloss string is none of these identities by default.

### 2.4 CIDOC CRM family and the RDFS/OWL boundary

CIDOC CRM 7.1.3 distinguishes classes, properties, and instances/resources such as `E55 Type` values. Its official release provides RDFS encodings; CRM and extensions are therefore not safely modeled by assuming that every property has one canonical OWL `ObjectProperty` versus `DatatypeProperty` identity independent of serialization.

Primary sources:

- <https://cidoc-crm.org/get-last-official-release>
- <https://cidoc-crm.org/html/cidoc_crm_v7.1.3.html>
- <https://cidoc-crm.org/Issue/ID-555-rdfs-implementation-and-related-issues>

The CRM SIG's RDFS implementation discussion explicitly records cases where supplementary RDFS/OWL declarations create object/datatype-property classification problems. That makes an OWL-specific split unsuitable as ontoTF's cross-formalism canonical kind.

Consequences:

- `crm:E22_Human-Made_Object` -> `class` + `entity-type`;
- `crm:P46_is_composed_of` -> `property` + `relation`;
- a literal-valued CRM property -> `property` + `attribute`;
- a particular `E55 Type` resource -> `named-resource` (or `skos-concept` when the authority is actually SKOS) + an appropriate value/authority role;
- an ontology lock may separately record whether one particular artifact declares a property as `rdf:Property`, `owl:ObjectProperty`, `owl:DatatypeProperty`, or another compatible refinement.

### 2.5 Why `property` is canonical and OWL subtyping is metadata

The first-profile target vocabulary must be stable when the same reviewed semantic term is consumed from an accepted RDFS or OWL serialization.

Therefore:

```text
canonical ontoTF kind: property
semantic role: relation | attribute | annotation-category
ontology declaration evidence:
  may include rdf:Property
  may include owl:ObjectProperty
  may include owl:DatatypeProperty
  plus domain/range and ontology release
```

The role determines the required native execution shape:

- `relation` -> entity-valued source/target traversal;
- `attribute` -> literal/value predicate;
- `annotation-category` -> category/dimension applicability.

Artifact declarations still matter. If a locked ontology artifact explicitly gives a primitive/literal range while a proposed mapping claims an entity-valued `relation`, validation should fail closed. But the canonical target kind remains `property`; switching serialization must not change the projection's ontoTF identity.

## 3. Formal target kinds

### 3.1 `class`

Use for ontology classes whose instances correspond to native entities or reviewed categorical classes.

Representative targets:

- `olia:Noun`
- `olia:Plural`
- `ontolex:LexicalEntry`
- `crm:E22_Human-Made_Object`
- `crmtex:TX7_Written_Text_Segment`
- `lrmoo:F2_Expression`
- CRMinf classes where explicit claim/inference semantics are supported.

Execution normally requires a reviewed type/value membership selector. It never follows merely from RDF class hierarchy reasoning at runtime.

### 3.2 `property`

Use for ontology properties/predicates whose semantic role is separately controlled.

Allowed first-profile roles include:

- `relation` — entity-valued relation/path;
- `attribute` — literal/open-valued property;
- `annotation-category` — where the property itself identifies an annotation dimension.

Execution shape is role-sensitive and binding-sensitive. Relation direction, source applicability, target applicability, and any derived path must be explicit.

OWL object/datatype declarations are ontology-artifact refinements, not separate canonical ontoTF kinds.

### 3.3 `skos-concept`

Use when the target is a concept in a SKOS concept scheme and concept-scheme/mapping semantics matter.

Examples:

- reviewed shared lexical concepts;
- PeriodO period definitions;
- semantic-domain/category schemes;
- external authorities published as SKOS concepts.

This is intentionally more specific than `named-resource` because publication legality and concept mapping behavior differ.

### 3.4 `named-resource`

Use for a particular identified RDF/resource individual whose semantics do not require the special SKOS-concept kind.

Examples:

- a particular external lexical entry/form/sense;
- a particular CRM type/resource from a non-SKOS authority;
- a museum, catalogue, place, or other authority entity;
- a particular proposition/belief/inference instance.

`named-resource` is not an “unknown” fallback. If the locked artifact cannot establish the target's formal status sufficiently for the requested role, the projection is unresolved/invalid rather than silently accepted.

## 4. Kinds deliberately excluded from the first closed vocabulary

### 4.1 Literal

A literal is a source/query value or operand, not a semantic target identity. `"stone"`, `"noun"`, a gloss, or an English label must not substitute for a reviewed target resource.

### 4.2 OWL `ObjectProperty` / `DatatypeProperty` as canonical subkinds

Rejected for the first canonical vocabulary because:

1. the accepted pivot spans RDFS and OWL serializations;
2. CRM provides authoritative RDFS encodings and has documented object/datatype classification complications in supplementary reasoning encodings;
3. ontoTF already needs semantic role `relation` versus `attribute`, which determines the native execution shape;
4. artifact-specific OWL declarations remain available as validation/publication evidence without changing canonical target kind.

A future schema may expose a controlled **declaration refinement** field, but must not make projection identity depend on which equivalent serialization was loaded.

### 4.3 Annotation property

No accepted R-006–R-011 executable common-pivot mapping needs an OWL annotation property as the semantic target. Labels/comments/documentation remain ontology metadata unless a later profile demonstrates an execution requirement.

### 4.4 Blank node

Released mappings require stable reviewable target identity and reverse indexing. Anonymous targets are not first-profile mapping targets unless independently canonicalized inside a locked artifact.

### 4.5 RDF-star or property-of-property construct

Potentially useful for publication, but no accepted pilot requires a distinct canonical target kind. Add only through a versioned vocabulary change backed by demonstrated mappings.

## 5. Semantic roles

### 5.1 `entity-type`

The target classifies the kind of native entity represented by a selector/node type.

Examples:

- CUC `otype=tablet` -> CRM physical-object class;
- reviewed CUC/TLH/ORACC line -> CRMtex written-text-segment class;
- Pseudepigrapha textual version -> LRMoo Expression candidate.

### 5.2 `annotation-category`

The target denotes an annotation dimension/property family rather than one categorical value.

Example: a reviewed shared grammatical-gender category corresponding to native feature `gn`.

### 5.3 `annotation-value`

The target denotes one categorical annotation value.

Examples:

- BHSA `sp=subs` -> OLiA Noun;
- BHSA `nu=pl` -> OLiA Plural;
- Syriac `ps=first` -> OLiA First.

### 5.4 `relation`

The target is a semantic entity-to-entity relation. A property/relation binding needs explicit direction, source/target applicability, and native edge/path semantics.

### 5.5 `attribute`

The target is a literal/open-valued semantic property. It normally compiles to feature presence/value comparison, not graph traversal.

### 5.6 `lexical-entry-identity`

One particular lexical-entry identity. The class `ontolex:LexicalEntry` is not this role; it is normally `class + entity-type`.

### 5.7 `lexical-form-identity`

One particular lexical form identity.

### 5.8 `lexical-sense-identity`

One particular source/external lexical sense identity. Gloss/guide-word/definition literals cannot satisfy it by themselves.

### 5.9 `lexical-concept-identity`

A shared lexical-semantic concept intended as cross-resource semantic pivot, commonly `skos-concept`.

### 5.10 `authority-reference`

An external authority/value/identity resource used for filtering, linking, documentation, or controlled classification without automatically becoming a common semantic-pivot schema concept.

Examples: PeriodO definitions, Getty AAT terms, place authorities, museum/catalogue authorities. R-017 owns final activation/execution rules.

### 5.11 `claim-proposition`

A particular proposition/claim identity or a projection whose source semantics explicitly denote a proposition-bearing object.

### 5.12 `inference-activity`

An attributed argumentation/inference/assessment activity. It is distinct from the proposition produced/adopted and from an ordinary source fact.

## 6. Kind/role compatibility matrix

`Allowed` means structurally possible, not automatically approved for every ontology term.

| formal kind | normally allowed roles | normally invalid roles |
|---|---|---|
| `class` | entity-type, annotation-category, annotation-value | relation, attribute, particular lexical identity, authority-reference |
| `property` | relation, attribute, sometimes annotation-category | entity-type, particular lexical identity, claim-proposition identity |
| `skos-concept` | annotation-value, lexical-concept-identity, authority-reference | relation property, attribute property |
| `named-resource` | lexical-entry/form/sense/concept identity, authority-reference, claim-proposition, inference-activity, controlled value | ontology class-as-type, ontology property-as-predicate |

Exceptional multi-typing does not justify free-form exceptions. If one RDF resource participates legitimately in several roles, P-003 should represent separate complementary projections or role-specific bindings when execution/publication semantics differ.

## 7. Publication-relation legality

Publication relation is a third concern and remains projection-specific.

### 7.1 SKOS mapping predicates

Use only for concept-to-concept mappings whose source publication entity and target are actually SKOS concepts and whose predicate meaning is independently justified.

Never auto-convert:

```text
ontoTF exact    -> skos:exactMatch
ontoTF close    -> skos:closeMatch
ontoTF broader  -> skos:broadMatch
ontoTF narrower -> skos:narrowMatch
ontoTF related  -> skos:relatedMatch
```

### 7.2 OWL equivalence

`owl:equivalentClass` requires class-to-class semantics. `owl:equivalentProperty` requires property-to-property semantics. Neither follows from ontoTF `exact`.

Artifact metadata may additionally validate whether an OWL serialization declares a property as object/datatype, but publication logic must not make the canonical ontoTF kind encoding-dependent.

### 7.3 `owl:sameAs`

Only for genuine resource identity. Same label, gloss, catalogue number, period name, translation, or mapping assessment is insufficient.

### 7.4 RDFS subclass/subproperty

Only where the source/target ontology semantics establish an actual class/property hierarchy. ontoTF broader/narrower assessment is not automatically an RDFS hierarchy assertion.

### 7.5 OntoLex relations

`ontolex:sense`, `reference`, `canonicalForm`, etc. have specific domain/range semantics and are not generic publication predicates for arbitrary ontoTF mappings.

## 8. Execution implications

The `(formal-kind, semantic-role)` pair constrains the required native binding shape but never creates the binding.

| target kind | role | minimum native execution shape |
|---|---|---|
| class | entity-type | node/entity type or reviewed membership selector |
| class | annotation-value | feature/value/category selector |
| class | annotation-category | feature/category applicability binding |
| property | relation | directed native edge/path + source/target applicability |
| property | attribute | literal feature/value or presence predicate |
| property | annotation-category | reviewed category/dimension applicability binding |
| skos-concept | lexical-concept-identity | reviewed native sense/entry/concept -> shared concept binding |
| skos-concept | authority-reference | reviewed authority-valued native field/key; execution governed by R-017 |
| named-resource | lexical-entry/form/sense identity | stable native identity construction + occurrence/path binding |
| named-resource | authority-reference | reviewed native authority key/field + R-017 policy |
| named-resource | claim-proposition | explicit native claim/assertion identity |
| named-resource | inference-activity | explicit attributed process/activity identity |

If ontology-declaration evidence contradicts the requested role/binding shape, validation fails closed. For example, a property with authoritative primitive/literal range cannot be executed as an entity-valued relation merely because a native edge exists.

## 9. Corpus tests against accepted R-011

These are research contract examples, not released production mappings.

### 9.1 BHSA

```text
native: word.sp = subs
target: olia:Noun
kind: class
role: annotation-value
binding: F.sp.v(n) == "subs"
```

Valid as a reviewed category projection. `skos:exactMatch` remains invalid merely from ontoTF assessment because the target is an OLiA class, not a concept-to-concept SKOS mapping.

BHSA `otype=lex -> ontolex:LexicalEntry` uses `class + entity-type`. A particular BHSA lexeme linked to a particular dictionary entry instead uses `named-resource + lexical-entry-identity`.

### 9.2 ETCBC Syriac

A repeated `lex` feature may define a reviewed corpus-scoped native lexical key, while a particular external entry remains `named-resource + lexical-entry-identity`. The string itself is not an RDF target identity.

### 9.3 CUC

Reviewed line -> `crmtex:TX7` uses `class + entity-type`.

Reviewed tablet -> `crm:E22_Human-Made_Object` uses `class + entity-type` as a conservative physical-object candidate.

A native sign cannot be promoted to CRMtex Grapheme/Glyph merely from `otype=sign`.

### 9.4 Pseudepigrapha-TF

The apparatus graph has accepted profile-local semantics but no accepted common apparatus target:

```text
native: reading_of
assessment: native-only
semantic projection: none
```

No target kind is invented merely because the native relation is an edge.

Pinned textual-version identity may conservatively project `close` to `lrmoo:F2_Expression` as `class + entity-type`; manuscript/witness identity remains separate from physical carrier identity.

### 9.5 ORACC-TF

Accepted R-011 deliberately fails closed for generic physical-object projection:

```text
native: otype=document
assessment: native-only for generic physical-object common-pivot request
target: none
reason: document identity is broader than a reproducibly proven physical-carrier selector
```

A future **separately reviewed object-bearing catalogue/carrier selector** may map to `crm:E22_Human-Made_Object` as `class + entity-type`, but R-013 must not infer that projection from `otype=document` alone.

Other ORACC patterns:

- line -> CRMtex segment: `class + entity-type` where written-text semantics are reviewed;
- particular glossary entries/senses -> `named-resource` + lexical identity role;
- material/period/place authority -> `skos-concept` or `named-resource` + `authority-reference` depending on the selected authority;
- `cf`, `gw`, `mng` literals -> native literals, not target identities.

### 9.6 TLHdig-TF

- document physical carrier candidate -> CRM class + entity-type where pinned source semantics justify it;
- line -> CRMtex segment class + entity-type;
- `surface` remains native-only for TX7 after R-011 because it is carrier structure, not written-text segment;
- `analysis -> lex` cannot be assigned an OntoLex property target by label similarity;
- edit/history objects activate CRMinf roles only with explicit attributed proposition/inference evidence.

### 9.7 ExtraBiblical control

ExtraBiblical reuses several exact OLiA category projections from the BHSA-like annotation system but demonstrates that similarity does not authorize unobserved fields: R-011 excluded `extra-gloss` because the pinned inventory contained no such feature. R-013 target-kind validation therefore operates only after native evidence is established.

## 10. RED-style contract cases for P-003/TDD

The future production contract should reject at least:

1. **Opaque target** — target URI with no formal kind/role.
2. **Unknown kind** — free-string formal kind outside the versioned vocabulary.
3. **Unknown role** — free-string semantic role outside the versioned vocabulary.
4. **Class as relation** — `class + relation`.
5. **Property as entity type** — `property + entity-type`.
6. **Property declaration/role conflict** — authoritative primitive/literal range but mapping claims entity-valued relation execution.
7. **Encoding leak** — same reviewed CRM property receives different canonical ontoTF kinds solely because one artifact is RDFS and another declares OWL Object/DatatypeProperty refinement.
8. **SKOS publication misuse** — OWL/RDFS class target mechanically published with `skos:exactMatch`.
9. **SKOS concept as relation property** — `skos-concept + relation`.
10. **Class/identity conflation** — `ontolex:LexicalSense` class used as particular `lexical-sense-identity`.
11. **Gloss promotion** — native gloss/guide word promoted to lexical concept identity without reviewed mapping.
12. **Authority/class conflation** — PeriodO/AAT authority target marked entity-type solely from label semantics.
13. **Assessment/publication conflation** — ontoTF `exact` auto-generates `owl:sameAs`, `owl:equivalentClass`, `owl:equivalentProperty`, or `skos:exactMatch`.
14. **Native-only fake target** — no-target state forced to carry semantic target kind/role.
15. **Unsupported fake target** — unsupported capability inserted into semantic->native target index.
16. **Relation direction omitted** — executable `property + relation` binding lacks source/target direction/applicability.
17. **Particular resource without identity rule** — executable lexical/authority resource has no stable native identity construction.
18. **Kind inferred from URI text** — local name/suffix used instead of locked ontology evidence.
19. **Complementarity collapsed into ambiguity** — compatible role-distinct projections represented as mutually exclusive candidates.
20. **Ambiguity collapsed into complementarity** — incompatible alternatives represented as simultaneously approved projections.
21. **Claim/fact conflation** — ordinary source fact promoted to CRMinf proposition/inference activity without attributed claim/process evidence.
22. **ORACC document overprojection** — generic `otype=document` compiled to CRM E22 despite accepted R-011 fail-closed carrier evidence boundary.

## 11. P-003 schema/IR inputs

P-003 needs conceptually:

```yaml
projection:
  target: <locked IRI>
  formal_kind: class|property|skos-concept|named-resource
  semantic_role: <controlled role>
  ontology_lock: <artifact/version/digest identity>
  ontology_declaration_evidence:
    rdf_types: <artifact declarations when relevant>
    domain_range: <artifact declarations when relevant>
  assessment: exact|close|broader|narrower|related|ambiguous
  publication_relation: <optional; kind/role/artifact validated>
  native_binding:
    selector_or_path: <reviewed binding>
    applicability: <native source/value/entity domain>
    execution_shape: <membership | value predicate | edge/path | identity key | non-executable>
  evidence: <review/research provenance>
```

Field names are not frozen. The required distinction is that canonical `formal_kind` stays cross-encoding while artifact-specific declaration metadata stays locked and reviewable.

`native-only` and `unsupported` remain first-class reviewed mapping/capability records with no semantic target projection.

Reverse indexes must distinguish at least:

```text
native selector/path/value identity
  -> approved projection(s)

profile + target + formal kind + semantic role
  -> per-corpus reviewed native binding(s)
```

Target IRI alone is insufficient because the same resource may participate in different reviewed roles.

## 12. Extensibility/versioning

The vocabulary is closed and versioned.

1. Add a canonical formal kind only when an accepted ontology/profile demonstrates a structurally distinct target form whose validation/execution/publication behavior cannot be represented safely by existing kinds + roles + artifact declaration metadata.
2. Add a semantic role only after a demonstrated mapping cannot be represented safely by existing roles.
3. OWL/RDFS declaration refinements do not create new canonical formal kinds by themselves.
4. Aliases are not silently accepted; canonical identifiers participate in digest/schema identity.
5. A vocabulary change altering validation or reverse-index semantics requires mapping/IR versioning.
6. Released mappings retain their original vocabulary version and never silently acquire new interpretations.

## 13. Rejected alternatives

### 13.1 One mixed `target_type` enum

Rejected because it combines formal shape and semantic role into a combinatorial vocabulary such as `class-linguistic-value` or `resource-lexical-sense`.

### 13.2 Canonical `object-property` versus `datatype-property`

Rejected for the first cross-formalism vocabulary because the distinction is encoding-sensitive across accepted RDFS/OWL artifacts and duplicates role-level execution semantics. Preserve artifact declarations separately.

### 13.3 Infer kind from namespace/local name

Rejected. OntoLex classes and particular dictionary resources may share a namespace; CRM resources may be classes, properties, or controlled individuals. URI syntax is not sufficient evidence.

### 13.4 RDF type only, no semantic role

Rejected. `rdf:type` can help establish class/concept/resource metadata but cannot tell the resolver whether a mapping represents an annotation value, lexical identity, authority reference, claim, or another role.

### 13.5 Make every authority concept part of the common pivot

Rejected. R-010/R-017 require authority identities to remain distinct from common semantic schema semantics.

### 13.6 Let publication predicate determine mapping assessment

Rejected. Publication relation is ontology-specific serialization; ontoTF mapping assessment is the canonical cross-formalism review result.

## 14. Acceptance-criteria closure

- **Minimal controlled formal-kind vocabulary:** `class`, `property`, `skos-concept`, `named-resource`.
- **Separate semantic-role vocabulary:** entity type; annotation category/value; relation/attribute; lexical entry/form/sense/concept identity; authority reference; claim proposition; inference activity.
- **Opaque URI shown insufficient:** demonstrated across OLiA, OntoLex, CIDOC CRM family, SKOS authorities, and no-target apparatus cases.
- **Cross-encoding stability:** object/datatype OWL declarations retained as artifact metadata rather than canonical kind.
- **Publication legality:** SKOS/OWL/RDFS/OntoLex predicates are kind/role/artifact validated and never mechanically derived from ontoTF assessment.
- **Execution implications:** binding shape is explicit for class membership, categorical values, entity relations, literal attributes, identities, authorities, claims, and inference activities.
- **Heterogeneous corpus tests:** BHSA, Syriac, CUC, Pseudepigrapha-TF, ORACC-TF, TLHdig-TF, plus ExtraBiblical control.
- **Accepted R-011 carried forward:** ORACC generic document remains fail-closed for E22; TLH surface remains non-TX7; unsupported ExtraBiblical gloss is not resurrected.
- **P-003 inputs:** projection shape, ontology declaration evidence, reverse-index key, no-target records, versioning, and RED cases are explicit.

## 15. Remaining boundaries

R-013 intentionally does not decide:

- final semantic profile/capability identifiers — R-014;
- ontology-bundle/bridge-lock schema — R-015;
- approximate execution authorization — R-016;
- final authority identity/query policy — R-017;
- production field names — P-003;
- whether future corpora require an additional generic non-lexical entity-identity role — add only when evidenced rather than pre-generalizing;
- empirical mapping frequencies beyond accepted R-011.

These later tickets may refine names or activation policy, but should not collapse the formal-kind / semantic-role / artifact-declaration separation established here.
