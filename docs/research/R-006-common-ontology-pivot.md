# R-006: common-ontology semantic pivot

**Status:** research complete; pending fresh logically-independent review  
**Issue:** #38  
**Recorded:** 2026-09-06  
**Baseline:** accepted R-002 ontology governance, R-003 agent ergonomics, R-005 corpus semantic census, merged roadmap guardrail #45

## Decision

ontoTF should retain the accepted seven-model basis:

- **SKOS** — concept schemes and concept-to-concept mappings;
- **OLiA** — cross-corpus linguistic annotation categories and relations;
- **OntoLex-Lemon** — lexical entries, forms, senses, and lexical concepts;
- **CIDOC CRM** — cultural objects, events, actors, places, identifiers, and heritage provenance;
- **CRMtex** — physical writing, written-text segments, graphemes/glyphs, text recognition, transcription, and reading;
- **LRMoo** — works, expressions, manifestations, items, derivation, components, and fragments;
- **CRMinf** — propositions, beliefs, inference, argumentation, and scholarly evidence.

The seven models must **not** be implemented as one undifferentiated ontology, one generic `external_target` namespace, or one blindly imported OWL closure. The common pivot is a **reviewed, versioned composition of semantic profiles** whose mappings compile ontology-addressed semantic requests into corpus-native Context-Fabric selectors and paths.

The architecture should follow the same separation that makes OLiA useful for heterogeneous annotation schemes: native annotation remains native; a linking layer connects native categories to a shared reference layer; query preprocessing resolves a shared request into the concrete native tags/selectors used by the corpus. ontoTF generalizes that pattern beyond linguistic annotation and executes through Context-Fabric rather than requiring RDF/SPARQL at runtime.

The central runtime route is therefore:

```text
common semantic atom
  (profile + target IRI + target kind/role)
        ↓
reviewed corpus capability binding
        ↓
reviewed semantic projection(s)
        ↓
native selector / feature-value / edge / path constraint
        ↓
Context-Fabric native query plan
```

Ontology hierarchy, label similarity, identical TF feature names, or identical local ontology identifiers must never create a runtime mapping by themselves.

## 1. Evidence basis

### 1.1 Accepted ontoTF research

This report does not reopen R-002 merely because P-001 became generic.

- [R-002 ontology governance](R-002-ontology-governance.md) established the seven-model semantic basis, ontology locks, eight ontoTF mapping assessments, the separation between runtime assessment and publication relation, and the policy against casual OWL/SKOS equivalence.
- [R-003 ergonomics](R-003-ergonomics.md) established `semantic_capabilities → semantic_resolve → semantic_search`, exact/approximate execution gates, inspectable native plans, and fail-closed behavior.
- [R-005 corpus semantic census](R-005-corpus-semantic-census.md) established that the corpus family is heterogeneous in slot type, graph structure, lexical representation, witness semantics, editorial uncertainty, and physical-object metadata.
- [P-001 foundation POC design](../plans/P-001-foundation-poc-design.md) remains authoritative for artifact integrity, parent-component identity, ontology locks, evidence/review bindings, deterministic canonicalization/digests, and fail-closed infrastructure. It is not treated as final authority for semantic target shape after #45.

### 1.2 Authoritative ontology sources inspected

The primary sources used for the semantic-composition conclusions are:

- W3C SKOS Reference: <https://www.w3.org/TR/skos-reference/>
- OLiA project and architecture: <https://acoli-repo.github.io/olia/> and <https://acoli-repo.github.io/olia/overview.html>
- OntoLex-Lemon final model specification: <https://www.w3.org/community/ontolex/wiki/Final_Model_Specification>
- CIDOC CRM 7.1.3: <https://cidoc-crm.org/Version/version-7.1.3>
- CRMtex 2.0: <https://cidoc-crm.org/crmtex/ModelVersion/version-2.0> and its class/property declarations at <https://cidoc-crm.org/extensions/crmtex/html/CRMtex_v2.0.html>
- LRMoo 1.1.1: <https://cidoc-crm.org/lrmoo/ModelVersion/version-1.1.1> and declarations at <https://cidoc-crm.org/extensions/lrmoo/html/LRMoo_v1.1.1.html>
- CRMinf 1.2.1: <https://cidoc-crm.org/crminf/ModelVersion/crminf-1.2.1> and declarations at <https://cidoc-crm.org/extensions/crminf/html/CRMinf_v1.2.1.html>
- W3C PROV-O and SHACL remain the R-002 provenance/validation infrastructure rather than members of the seven-model semantic-domain pivot: <https://www.w3.org/TR/prov-o/> and <https://www.w3.org/TR/shacl/>.

### 1.3 Corpus evidence reused and spot-checked

R-005 is the authoritative pinned census. This report additionally spot-checks representative native contracts rather than treating repository prose as semantic truth:

- BHSA pinned corpus uses native POS values such as `sp=subs`, `sp=verb`, etc.; its lexical and syntactic relations remain ETCBC-native.
- TLHdig-TF explicitly uses `sign` slots, separate `analysis` nodes for morphological alternatives, `analysis -> lex` links, `cluster` nodes for damage/editorial ranges, and a `sign → word → line → column → surface → document` hierarchy at the R-005 pin.
- Pseudepigrapha-TF apparatus helpers require explicit `reading_of`, `witness`, `is_primary`, and manuscript relations; explicit empty readings represent omissions. Absence of an edge is not silently treated as an omission or reading.
- ORACC-TF remains a conversion target/stress corpus rather than a finalized released ontoTF profile; the source tree contains separate catalogue, corpus, glossary, and per-text structures that must not be collapsed into one linguistic layer.

These observations agree with R-005's stronger empirical warning: identical names such as `sentence`, `lex`, or `witness` do not establish identity across corpora.

## 2. Evidence-based refinement to R-002: composition is not one import closure

No foundation ontology is rejected by R-006. One implementation assumption does require explicit refinement.

Stable **CRMtex 2.0** declares dependencies on:

- CIDOC CRM **7.1.2**;
- CRMinf **0.7(b)**;
- CRMsci 2.0;
- FRBRoo **2.4**.

Current accepted ontoTF research otherwise uses:

- CIDOC CRM **7.1.3**;
- LRMoo **1.1.1** (the successor of FRBRoo for the current bibliographic model);
- CRMinf **1.2.1**.

The mismatch is semantically relevant, not cosmetic. CRMtex 2.0 formally declares, for example, `TX2 Writing` as a subclass of the older-family `F28 Expression Creation`, and `TX14 Reading` as a subclass of `I1 Argumentation`. Current LRMoo 1.1.1 still has an `F28 Expression Creation`, and current CRMinf 1.2.1 still has `I1 Argumentation`, but matching local codes/names do not by themselves prove URI identity or unchanged semantics across model generations. The official FRBRoo→LRMoo migration material also shows that some properties were retained while others were renamed, generalized, deprecated, or replaced by paths.

**Therefore:**

1. each ontology release/snapshot remains independently locked;
2. ontoTF must not assume that loading the seven RDF/OWL resources creates a coherent current-version reasoning closure;
3. cross-version bridge assertions must be explicit, evidence-backed, reviewable, and versioned;
4. a query can use several profiles without requiring their RDF documents to import each other;
5. a missing or unreviewed required bridge fails closed.

This is a refinement of the **composition mechanism**, not a change to the selected semantic basis.

R-012 #46 now owns the detailed CRMtex 2.0 ↔ current LRMoo/CRMinf bridge research. R-015 #49 owns the more general ontology-bundle/bridge-lock identity and provenance problem.

## 3. Seven-ontology role and composition matrix

| model | primary ontoTF role | typical target form | composes directly with | must not be used as |
|---|---|---|---|---|
| **SKOS** | controlled concept schemes, hierarchy, and concept-to-concept mappings | `skos:Concept` / concept scheme / SKOS mapping property | OntoLex `LexicalConcept` is a `skos:Concept`; external controlled vocabularies | generic mapping predicate system for arbitrary OWL classes/properties |
| **OLiA** | morphosyntax, morphology, syntactic/annotation categories and relations | OWL classes/properties such as `olia:Noun`, `olia:Singular` | native annotation models through reviewed linking mappings; lexical entries can carry OLiA/LexInfo-like linguistic categorization | lexical identity, manuscript ontology, physical-object model |
| **OntoLex-Lemon** | lexical entry/form/sense/concept identity and lexicon-to-ontology grounding | lexical entities and classes; lexical concept resources | SKOS concept schemes; external linguistic category vocabularies | universal POS/morphology inventory or document ontology |
| **CIDOC CRM** | physical/cultural objects, events, actors, places, identifiers, production/custody/provenance backbone | CRM classes/properties | LRMoo, CRMinf, CRMtex family extensions; domain extensions | linguistic annotation ontology or lexical sense inventory |
| **CRMtex** | material writing and its scholarly recognition: written text, writing field, segment, glyph/grapheme, transliteration, reading | CRM-family classes/properties | CIDOC CRM; historically FRBRoo/CRMinf/CRMsci with version-specific dependencies | generic abstract text/version model or universal critical apparatus |
| **LRMoo** | bibliographic/intellectual levels and transmission: work, expression, manifestation, item, derivation, component/fragment | LRMoo classes/properties | CIDOC CRM 7.1.3; selected textology mappings | physical writing/glyph model or linguistic annotation inventory |
| **CRMinf** | scholarly propositions, beliefs, inference/argumentation, evidence and provenance of claims | CRMinf classes/properties | CIDOC CRM 7.1.3; CRMtex reading/recognition only through reviewed version bridge | unqualified storage of corpus facts or generic provenance replacement for PROV-O |

### 3.1 Two semantic spines

For engineering and explanation, the seven models form two complementary spines joined by SKOS/explicit projections rather than one monolith:

```text
LANGUAGE / LEXICON
  OLiA ───── OntoLex-Lemon
                 │
                SKOS

OBJECT / WRITTEN TEXT / TRANSMISSION
  CIDOC CRM ─ CRMtex
      │          │
    LRMoo      CRMinf
```

This is a conceptual division of responsibility, not an RDF import declaration. A corpus may activate only the profiles it actually supports.

### 3.2 OLiA is direct architectural prior art for the resolver

OLiA explicitly separates:

1. corpus/tagset-specific **Annotation Models**;
2. a shared **Reference Model**;
3. separate **Linking Models**.

Its historical query preprocessor expands a query over the reference vocabulary into concrete corpus tags for a downstream corpus query engine. ontoTF should copy the architectural principle, not necessarily serialize every ontoTF mapping as an OLiA Annotation Model:

```text
OLiA-style pattern                    ontoTF pattern
------------------                    -------------
annotation model                      native TF schema/value/path
linking model                         reviewed ontoTF mapping package
reference model                       shared ontology/profile target
query preprocessor                    semantic_resolve
corpus query engine                   Context-Fabric native execution
```

This is the strongest precedent found for ontoTF's language-side common pivot.

### 3.3 OntoLex ↔ SKOS is an explicit formal composition point

OntoLex defines `ontolex:LexicalConcept` as a subclass of `skos:Concept`. This gives ontoTF a clean way to make dictionary senses interoperable without asserting that dictionary senses themselves are identical:

```text
dictionary A sense ─┐
dictionary B sense ─┼─> shared/referenced ontolex:LexicalConcept
corpus lexeme sense ┘               │
                                    └─ SKOS broader/narrower/related or
                                       cross-scheme mappings where legal
```

A lexical sense, lexical concept, lexical entry, and canonical form remain distinct objects. This directly supports R-008 rather than collapsing `lemma`, `gloss`, `sense`, root, and lexeme identity.

### 3.4 CIDOC-family composition must be version-aware

Current LRMoo 1.1.1 and CRMinf 1.2.1 explicitly declare CIDOC CRM 7.1.3 dependencies. CRMtex 2.0 is the exception described in section 2. ontoTF should therefore expose the **effective ontology/profile bundle** used by a resolution, not merely seven independent URI strings and not a fiction that all current profiles share one import graph.

## 4. The semantic target cannot remain one opaque URI

The current v1 mapping shape's `external_target` is insufficient because the runtime and publication meaning of an IRI depends on what kind of semantic target it is.

At minimum ontoTF must distinguish two independent dimensions.

### 4.1 Formal target kind

A provisional research vocabulary is:

- ontology **class**;
- ontology **property/relation**;
- **SKOS concept**;
- named **resource/individual/authority resource**.

OntoLex entities require further care because a mapping may target either a class (e.g. “this native node type denotes lexical entries”) or a particular lexical-entry/sense/concept resource (e.g. “this native lexeme corresponds to this external dictionary entity”). Therefore RDF formal kind alone is not enough.

### 4.2 Semantic role

A separate semantic-role dimension is required. Provisional roles evidenced by the current corpus family include:

- entity/type;
- annotation category or category value;
- relation/path predicate;
- external authority value/identity;
- lexical-entry identity;
- lexical-form identity;
- lexical-sense identity;
- lexical-concept identity;
- written-text/writing-segment role;
- bibliographic/transmission level;
- proposition/inference/claim role.

R-013 #47 must close and empirically test this vocabulary before P-003 freezes schema enums. R-006's architectural conclusion is only that **target type/role must become first-class in canonical mapping/IR**.

## 5. Complementary projections are not ambiguity

A native concept may legitimately participate in more than one ontology because the models describe different aspects of it. The current P-001 ambiguity mechanism (`candidate_projections`) cannot represent this: ambiguity means “we do not know which target is justified”; complementary projection means “multiple reviewed targets are simultaneously justified for distinct semantic roles.”

Conceptually, a mapping needs:

```text
native assertion
  ├─ approved projection A
  │    target + kind/role + assessment + lock + optional publication relation
  ├─ approved projection B
  │    target + kind/role + assessment + lock + optional publication relation
  └─ optional ambiguity candidates
       (only when evidence does not justify one projection)
```

Examples requiring this distinction:

- A physical manuscript entity may support a CIDOC CRM physical-object classification and, when the native semantics warrant it, an LRMoo item/bibliographic role. Those are complementary; CRMtex written text on the carrier is a related but distinct physical writing entity and must not be asserted as the manuscript itself merely for convenience.
- A lexical entity may be represented through OntoLex while its grammatical category is projected through OLiA. Lexical identity and POS are different semantic dimensions.
- A cuneiform document may use CIDOC CRM for the physical object, CRMtex for written-text segments/glyphs, and CRMinf for a scholarly reconstruction claim. The reconstructed proposition is not another physical-object type.

Inheritance already present inside an ontology does not need to be redundantly materialized as multiple ontoTF projections. “Complementary” means a second profile conveys a genuinely different reviewed semantic role, not every superclass reachable by reasoning.

## 6. Conceptual semantic-profile / capability contract

The current free-string `profile.semantic_domains` is inadequate for agent discovery. It cannot tell an agent whether two corpora claim the same standardized capability, which ontology bundle defines that capability, or whether the profile contains executable common projections versus only native-only coverage.

R-006 recommends a controlled, versioned **semantic profile/capability contract**. Exact profile IDs are deferred to R-014 #48, but the empirically required families are already clear:

- linguistic annotation;
- lexical / lexical-semantic;
- written text;
- textual transmission / textology;
- heritage / physical object;
- scholarly inference;
- TF structural graph (to be defined by R-007);
- optional archaeology, scientific analysis, and lexicography profiles.

A profile is an activation/dependency boundary, not a claim that every ontology term is supported. Concept support remains per mapping/projection.

Conceptually:

```yaml
profile:
  id: <controlled-profile-id>
  version: <profile-contract-version>
  ontology_bundle: <locked composition identity>
  capabilities:
    - semantic_target: <IRI>
      target_kind: <controlled kind>
      semantic_role: <controlled role>
      corpus_bindings:
        - mapping_id: <reviewed mapping>
          assessment: exact|close|broader|narrower|related|ambiguous|native-only|unsupported
          execution: direct|explicit-approximation|informative-only|non-resolvable
```

This is deliberately conceptual. P-003 decides the canonical schema after R-012–R-017 and the domain research have been reconciled.

## 7. Canonical mapping examples from the corpus family

The following are **architecture examples/candidate mappings**, not production-approved ontology assertions. R-011 must validate the precise mapping strength against source definitions and ontology definitions.

### 7.1 BHSA / ExtraBiblical / Syriac: OLiA linguistic pivot

A prototypical positive query is a common OLiA POS/category request:

```text
request: olia:Noun
  ↓
BHSA reviewed binding          -> native word constraint, e.g. `sp=subs`
ExtraBiblical reviewed binding -> corresponding native `sp` value
Syriac reviewed binding        -> corresponding native `sp` value
```

The common target is an OLiA category; the executable artifacts are native TF constraints. The resolver does not ask the LLM to guess that `sp` means part of speech or that `subs` means noun.

A more demanding query such as `Noun AND Feminine AND Plural` is a useful positive R-011/P-003 test because each semantic atom must independently resolve and the conjunction must fail closed if one corpus lacks a required reviewed mapping.

### 7.2 BHSA syntax: preserve ETCBC-native relations

BHSA `mother`, `functional_parent`, and `distributional_parent` are semantic graph relations with ETCBC-specific interpretation. They must remain native until a reviewed OLiA/structural relation is justified. A generic “parent” label is not enough to make them the same relation.

This is a case where `native-only` may be correct for some edge/object combinations even when a broader syntactic capability is active.

### 7.3 CUC / TLHdig-TF / ORACC-TF: CRMtex written-text segmentation

CRMtex `TX7 Written Text Segment` explicitly covers scholarly text portions including columns, fragments, sections, paragraphs, words, and signs; `TXP4 has segment` explicitly includes lines and columns among its intended segmentations. That makes it a strong common **candidate** for appropriate physical written-text segment nodes in CUC, TLHdig-TF, and ORACC-TF.

However:

- a native sign must not be mapped blindly to `TX8 Grapheme`: CRMtex distinguishes the abstract grapheme (`TX8`) from the physical concrete glyph (`TX9`) and the abstract positioned grapheme occurrence/sequence (`TX11`/`TX12`);
- a TF slot is a storage/query anchor, not automatically a physical glyph;
- R-007 must decide how TF graph mechanics and `oslots` relate to these semantic entities.

This is precisely why target semantic role and native selector semantics are required.

### 7.4 TLHdig-TF lexical layer: OntoLex plus OLiA, not one flattened feature

At the pinned TLHdig-TF build, morphology lives on `analysis` nodes; alternatives remain separate; lexical nodes are reached through explicit `analysis -> lex` links. A ontoTF lexical profile can therefore project the lexical entity through OntoLex while linguistic features of each analysis project through OLiA. It must not pretend the `lex` node itself carries every analysis-level feature or infer that one ambiguous word has one selected analysis.

### 7.5 Pseudepigrapha-TF apparatus: separate witness facts, readings, and claims

The pinned Pseudepigrapha-TF apparatus requires explicit `reading_of`, `witness`, and `is_primary` semantics; explicit empty readings represent omissions. This is a strong test for composition among LRMoo/CRMtex/CRMinf, but R-006 deliberately does **not** invent a universal apparatus class simply to make the mapping convenient.

A future profile may use:

- CIDOC CRM/LRMoo for witness/item/textual-transmission entities;
- CRMtex where physical written text/reading activities are actually represented;
- CRMinf for scholarly propositions or inferred relationships;
- a tiny local apparatus vocabulary only if R-009 demonstrates a recurring gap.

Crucially, “witness has reading at locus” is not implied by generic witness metadata in another corpus.

### 7.6 ORACC-TF: object, lexical, and authority semantics are separate

ORACC source distributions separate catalogue/object metadata, corpus structures, glossaries, and per-text annotations. ontoTF should therefore permit distinct projections:

- physical object / production / place / identifier semantics → CIDOC CRM;
- written text/sign segmentation → CRMtex where source semantics fit;
- lexical identities/senses → OntoLex;
- material/period/place authority values → optional AAT/PeriodO/other authority resources after R-010/R-017.

A museum or period URI is not automatically a common ontology class merely because it is external and dereferenceable.

### 7.7 A true multiple-standard example

Suppose a native manuscript node is reviewed as denoting the physical manuscript item represented by the corpus. It may legitimately have two approved type projections:

```text
native manuscript node type
  ├─ CIDOC CRM physical-human-made-object role
  └─ LRMoo Item role
```

if and only if the native corpus definition satisfies both. These do not compete. If the same corpus also has a native written-text entity carried by the manuscript, that entity can separately map to CRMtex `TX1 Written Text`; ontoTF must not collapse carrier and writing merely to increase ontology coverage.

## 8. Common semantic request and runtime compilation

### 8.1 Semantic atoms

The stable cross-corpus address should be the reviewed semantic target itself plus enough type/profile information to prevent formalism confusion. Conceptually:

```text
semantic atom =
  profile identity
  + ontology target IRI
  + target formal kind
  + semantic role
  + requested operation/constraint
```

A human-friendly alias may exist for ergonomics, but it must resolve to this locked identity before planning.

### 8.2 Capability binding, not ontology inference

The resolver looks up an **explicit reviewed capability binding** for each corpus. It does not search the ontology graph for something that looks compatible at runtime.

```text
semantic atom
  ↓ lookup by locked semantic identity
corpus capability binding
  ↓
reviewed mapping projection
  ↓
native plan fragment
```

Ontology inheritance can support mapping research, validation, generated documentation, and perhaps explicitly reviewed derived indexes. It cannot silently turn an unmapped subclass/superclass into an executable constraint.

### 8.3 Bidirectional indexes required by the IR

P-003 needs an IR that can build both directions deterministically:

```text
native selector/value/path
  -> approved semantic projection(s)

semantic target + profile + role
  -> per-corpus approved native plan fragment(s)
```

`native-only` records live in the first/native index and have no common semantic reverse key. `unsupported` records are capability/gap facts, not fake targets.

### 8.4 Multi-corpus resolution

A single semantic request produces one plan per corpus, not one normalized corpus query language:

```text
olia:Noun
  ├─ BHSA        -> native plan A
  ├─ ExtraBiblical -> native plan B
  ├─ Syriac      -> native plan C
  └─ CUC         -> unsupported for that profile (if no reviewed noun mapping exists)
```

The response exposes the mapping assessment and native plan for each corpus. The common semantic identity is shared; the native execution remains corpus-specific.

## 9. Mapping assessment and execution policy

R-006 preserves all eight R-002 assessments. They are not replaced by SKOS relations.

| assessment | meaning for common-pivot resolution |
|---|---|
| `exact` | eligible for exact execution when parent/profile/lock compatibility is executable |
| `close` | may be eligible only under explicit approximate mode with disclosed non-coextensiveness |
| `broader` | native concept is narrower than requested target; using it can under-cover the request |
| `narrower` | native concept is broader than requested target; using it can over-cover the request |
| `related` | informative relation; not a substitute query constraint by default |
| `ambiguous` | no automatic target selection; non-executable until ambiguity is resolved/explicitly chosen under a future reviewed contract |
| `native-only` | legitimate native semantic support without common target; not reachable through common-pivot lookup |
| `unsupported` | active profile does not support a projection; non-executable |

The exact rules for whether particular `close`/`broader`/`narrower` mappings can execute under an explicit approximate mode require empirical testing; R-016 #50 owns that work. R-003's fail-closed rule remains in force meanwhile.

### 9.1 Publication relations remain independent

A ontoTF `exact` assessment does not imply `owl:equivalentClass`, `owl:sameAs`, or `skos:exactMatch`.

- SKOS mapping properties are concept-to-concept relations between SKOS concepts/concept schemes.
- OWL equivalence has formal class/property/individual semantics and requires stronger evidence.
- Some reviewed runtime mappings should publish no formal equivalence relation at all.

Publication relation therefore moves with the individual semantic projection if P-003 adopts multi-projection mappings; it cannot remain one scalar for the whole native mapping.

## 10. Controlled profiles are required; free semantic-domain strings are not sufficient

The profile contract must answer two different questions:

1. **Which semantic profile families are activated by this corpus/profile release?**
2. **Which concepts/relations inside those families are actually supported, at what assessment and execution level?**

A corpus can therefore truthfully advertise `linguistic` while marking some verbal categories native-only, or `written-text` while lacking glyph-level mapping.

This avoids two opposite errors:

- free strings that do not permit reliable cross-corpus capability comparison;
- ontology-level booleans such as `crmtex: true` that imply all CRMtex semantics are supported.

R-014 #48 owns the exact controlled identifiers and hierarchy.

## 11. Required provenance and explanation record

For every resolved semantic atom, an agent needs enough information to audit the full translation:

```text
requested semantic target/profile/role
  -> projection/mapping id
  -> mapping assessment
  -> ontology release/snapshot lock
  -> any required bridge/bundle identity
  -> native selector/value/edge/path
  -> parent component manifest identity + compatibility state
  -> evidence/review identity
  -> generated native query-plan fragment
```

For multi-corpus queries, this record is per corpus. Compact responses can use fingerprints/IDs, but full explanation must resolve them to the evidence above.

PROV-O remains available for publication/provenance representation; these fields are required even when runtime serialization is ordinary JSON rather than RDF.

## 12. P-001 / I-001 contracts to preserve

The ontology-pivot correction does **not** justify discarding the existing infrastructure. Preserve:

- native corpus semantics as authority;
- the eight mapping assessments;
- parent component manifest identity and four compatibility states;
- native selector/dependency closure;
- canonical source → validated normalized IR → generated artifacts;
- deterministic canonicalization and semantic digests;
- ontology snapshots/locks and offline reproducibility;
- content-addressed source evidence and independent review records;
- fail-closed validation/runtime behavior;
- separation of mapping assessment from publication relation;
- one-way generated RDF/Turtle, runtime indexes, docs, and other publication artifacts;
- thin Context-Fabric execution rather than a required RDF/SPARQL runtime.

## 13. P-001 / I-001 contracts P-003 must version or amend

The following current assumptions block the common pivot and cannot be treated as the final v2 semantic contract:

1. **One `external_target` per ordinary mapping.** Replace/version with one-or-more approved complementary projections while retaining a distinct ambiguity-candidate mechanism.
2. **One `ontology_lock` per mapping.** The lock belongs to the projection/target; a mapping can legitimately involve several locked models.
3. **One `publication_relation` per mapping.** Publication relation must be projection-specific because formal relation legality differs by target kind/formalism.
4. **Opaque target type.** Mapping/IR must carry controlled target formal kind and semantic role.
5. **Free-form `semantic_domains`.** Replace or constrain with a controlled profile/capability contract.
6. **IR centered mainly on artifact/mapping identity.** Add bidirectional semantic indexes from target/profile/role to native plan fragments and from native semantics to projections.
7. **No ontology-bundle/bridge identity.** Add a deterministic way to identify the effective versioned semantic composition when a query crosses models or bridge layers.
8. **Ambiguity conflated with “multiple possible targets.”** Preserve candidates for ambiguity but separately represent multiple simultaneously approved complementary projections.
9. **POC semantics too narrow if tested only on BHSA morphology.** The positive POC must execute at least one common semantic concept across 2+ independent corpora, and the broad suite must cover all seven required pilots plus negative cases, per #45/#43/#44.

Schema/digest migration must be versioned; existing v1 artifacts must not silently acquire new semantic identity.

## 14. Positive and adversarial query cases

### 14.1 Positive: reusable linguistic concept

Candidate test after value-level review:

```text
request: OLiA Noun
corpora: BHSA, ExtraBiblical, Syriac
expected:
  - each participating corpus resolves the same locked OLiA target;
  - each produces its own native TF selector/value;
  - execution succeeds in 2+ independent corpora;
  - explanation shows mapping strength and native selector;
  - no English feature-name guessing by the agent.
```

### 14.2 Positive: physical written-text segment

Candidate test after R-007/R-010 review:

```text
request: CRMtex Written Text Segment / line-like segment
corpora: CUC, TLHdig-TF, ORACC-TF
expected:
  - only nodes whose native semantics satisfy the CRMtex segment definition participate;
  - storage slot type (`sign`) is not itself enough;
  - native navigation remains corpus-specific.
```

### 14.3 Unsafe: Hebrew and Syriac verbal stems

`qal` and `peal` must not become aliases because they look structurally analogous. A higher-level reviewed verbal-stem/category projection may be possible, but exact cross-language value equivalence must not be inferred. Exact mode should refuse an unreviewed substitution.

### 14.4 Unsafe: false sentence equivalence

BHSA/ExtraBiblical linguistic sentence nodes and ORACC source `c type=sentence` chunks are not automatically the same semantic category. ORACC must not appear in a linguistic-sentence query solely because the source label says `sentence`.

### 14.5 Unsafe: witness label collision

Pseudepigrapha reading→manuscript `witness`, Peshitta A/B witness metadata, and TLH line→fragment witness relations concern witnesses but make different assertions. A broad witness-discovery profile may relate them; `witness has reading at locus` must execute only where that assertion exists.

### 14.6 Unsafe: grapheme vs glyph

CRMtex explicitly separates the abstract grapheme type from the physical concrete glyph. A cuneiform TF `sign` cannot be assigned one of those merely because both use the word “sign.” The native source/converter semantics decide which, if either, is justified.

### 14.7 Negative: native-only remains valid

A corpus-local clause type, editorial category, or syntactic relation with no defensible shared target remains a reviewed `native-only` mapping. It contributes to native inspection and coverage reporting but must not be injected into the semantic→native index under a fabricated broader concept.

## 15. Rejected alternatives

### A. One new universal ontoTF ontology

Rejected as the default. It would duplicate mature domain vocabularies, create a new maintenance authority, and invite lossy normalization. A tiny ontoTF-local vocabulary remains permissible only for recurring gaps empirically demonstrated by R-007–R-011.

### B. One generic `external_target` URI with ontology lock

Rejected as the final semantic contract. It cannot distinguish class/property/concept/resource semantics, complementary projections, publication legality, or executable capability.

### C. Use SKOS mapping predicates as the universal mapping-assessment vocabulary

Rejected. SKOS mapping predicates have SKOS concept domain/range semantics; ontoTF must also map OWL classes/properties and other resources. The eight ontoTF assessments remain formalism-independent runtime governance.

### D. Import all seven ontologies and let an OWL reasoner find the mapping

Rejected. Native mappings are scholarly assertions, ontology versions are independently locked, CRMtex has a real dependency-generation mismatch, and inferred hierarchy is not a substitute for reviewed query semantics.

### E. Materialize normalized semantic TF features into every parent corpus

Rejected as the default. It duplicates data, complicates release coupling, and makes the semantic layer harder to version independently. Materialized features may be optional generated artifacts after the mapping contract exists.

### F. Convert each corpus to an OLiA Annotation Model as the canonical ontoTF representation

Rejected as a universal requirement. The OLiA architecture is excellent prior art for the linguistic profile, but ontoTF spans lexical, manuscript, archaeological, and scholarly-inference semantics. Canonical ontoTF mappings must therefore be formalism-neutral enough to compose all seven models. Generated OLiA linking/annotation artifacts may still be useful publication outputs.

### G. Treat ontology hierarchy as automatic query widening

Rejected. A superclass/broader relation can change result extension and is not evidence that the corpus-native selector safely realizes the requested concept. Approximate execution must be explicitly reviewed and explicitly requested.

## 16. Research tickets opened by R-006

R-006 reached architectural conclusions but found several areas where freezing a production enum/bridge/execution policy now would outrun the evidence. These are separated into research tickets rather than hidden in P-003:

- **R-012 #46** — reconcile stable CRMtex 2.0 with current LRMoo/CRMinf versions and define reviewed bridges;
- **R-013 #47** — close the controlled target formal-kind and semantic-role vocabulary;
- **R-014 #48** — define controlled semantic profile/capability identifiers for agent discovery;
- **R-015 #49** — define ontology-bundle composition identity, bridge locks, provenance, and fail-closed version behavior;
- **R-016 #50** — empirically define approximate execution policy for `close` / `broader` / `narrower` mappings;
- **R-017 #51** — distinguish external authority/identity resources from common ontology-pivot targets.

These complement rather than replace R-007–R-011. R-007–R-010 remain the domain-specific semantic research; R-011 remains the cross-corpus empirical pilot.

## 17. Concrete inputs for P-003

P-003 should treat the following R-006 conclusions as design inputs unless later reviewed research supersedes them:

1. The seven-model basis remains the normative starting point.
2. The pivot is a composition of versioned semantic profiles, not one ontology and not one import closure.
3. OLiA's annotation/reference/linking/query-preprocessor architecture is the principal precedent for the ontoTF resolver pattern.
4. Native semantics and reviewed mappings, not ontology labels/hierarchy, control execution.
5. Target formal kind and semantic role must be first-class in canonical mapping/IR.
6. Multiple approved complementary projections must be representable separately from ambiguity candidates.
7. Assessment, publication relation, and ontology lock are projection-level concerns.
8. Controlled semantic profiles/capabilities are required; free strings are insufficient.
9. The normalized IR needs native→semantic and semantic→native indexes.
10. `native-only` remains first-class but has no semantic→native common-pivot key.
11. Ontology/profile composition and bridges need deterministic version identity and fail-closed validation.
12. Runtime semantic resolution compiles to native Context-Fabric plans; no RDF/SPARQL runtime is required.
13. Existing P-001 identity/provenance/digest/review/compatibility infrastructure should be preserved and version-migrated, not discarded.
14. The first positive semantic POC must actually execute one shared semantic target across 2+ independent corpora; negative cases are additional tests, not substitutes.

P-003 should not freeze final field names/enums until R-012–R-017 and R-007–R-011 have been reconciled.

## 18. Unresolved questions handed off

R-006 deliberately does not decide:

- the exact TF structural vocabulary around slots, `oslots`, valued/unvalued edges and discontinuous coverage — R-007;
- the exact OntoLex/LexInfo/Lexicog/VarTrans lexical mapping profile — R-008;
- the minimal critical-apparatus/textology vocabulary and SAWS/CAO relationship — R-009;
- archaeological vs heritage/object vs scientific-analysis activation — R-010;
- actual mapping coverage and strengths in all seven pilot corpora — R-011;
- CRMtex's cross-version bridge semantics — R-012;
- final target-kind/semantic-role enums — R-013;
- final capability/profile IDs — R-014;
- bundle/bridge-lock schema — R-015;
- approximate execution admissibility — R-016;
- external-authority identity semantics — R-017.

These are research dependencies, not reasons to revert to the generic v1 target shape.

## 19. Acceptance-criteria trace

- [x] **R-002 baseline preserved.** No ontology was replaced. The only evidence-based refinement is version-aware composition rather than a single import closure.
- [x] **Non-overlapping primary roles defined** for all seven models in section 3.
- [x] **Composition defined without one RDF relation formalism.** Sections 3–5 distinguish SKOS concepts, OWL/CRM classes/properties, OntoLex lexical entities, and complementary projections.
- [x] **Target role/type must be canonical.** Section 4 establishes this; R-013 closes the exact vocabulary.
- [x] **Controlled semantic profiles/capabilities are required.** Section 6 establishes this; R-014 closes the identifiers.
- [x] **RDF-runtime-independent execution route defined.** Sections 8–9 compile reviewed semantic atoms to native Context-Fabric plan fragments.
- [x] **Positive and unsafe/ambiguous examples included.** Sections 7 and 14 cover linguistic, written-text, witness, sentence, verbal-stem, glyph/grapheme, and native-only cases.
- [x] **P-001/I-001 preservation and required amendments identified.** Sections 12–13 enumerate both explicitly.
- [x] **Concrete P-003 inputs produced.** Section 17 lists the design requirements and section 16 creates research gates for unresolved details.

## Review gate

The exact final head of this research artifact requires a fresh logically-independent skeptical review against:

- R-002, R-003, R-005 and the merged #45 guardrail;
- the authoritative ontology specifications listed in section 1.2;
- the CRMtex/LRMoo/CRMinf version-dependency evidence;
- representative native corpus semantics, especially BHSA, CUC, Syriac, ExtraBiblical, Pseudepigrapha-TF, ORACC-TF, and TLHdig-TF.

A review that only agrees with the seven-ontology list is insufficient. It must actively challenge target-kind distinctions, complementary-vs-ambiguous projections, version composition, execution claims, and any corpus example that appears to overstate semantic equivalence.
