# R-007: common structural semantics for Text-Fabric

**Status:** research complete; pending fresh logically-independent review  
**Issue:** #39  
**Recorded:** 2026-09-07  
**Depends on:** accepted R-002/R-003/R-005, merged R-006 #52, and merged roadmap guardrail #45

## Decision

ontoTF should **not** replace Text-Fabric's native graph with POWLA, Web Annotation, RDF-star, or another RDF runtime model. The faithful common structural layer is:

1. **native TF warp and feature semantics remain executable truth**;
2. domain-semantic nodes and edges are projected to the seven-model ontology profiles only where their native meaning warrants it;
3. POWLA is an optional alignment/publication vocabulary for selected linguistic graph structures, not the TF warp itself;
4. Web Annotation is optional publication/targeting infrastructure, not the canonical representation of `oslots` or arbitrary TF slot sets;
5. a deliberately tiny local structural vocabulary is justified only for TF-specific mechanics not named precisely by maintained open standards: a neutral `Slot`, a neutral `slotLink` corresponding to native `oslots`, and a controlled **TF-node extent/anchor interpretation**;
6. **carrier kind is a separate dimension**: a semantic native entity is realized either by a TF node or by a sidecar/native-adapter selector. Sidecar entities have no `oslots` interpretation;
7. valued/unvalued edge mechanics, direction, feature applicability, section configuration, and sidecar paths belong in canonical mapping/IR rather than a new domain ontology.

The governing invariant is:

> **TF slot-set coverage/anchoring is structural evidence, not automatically linguistic constituency, physical containment, mereology, or semantic extent.**

TF computes native structural embedding from `oslots` slot-set inclusion. ontoTF may expose that as native TF structural behavior, but must not silently publish or query it as `partOf`, POWLA `hasParent`, CRM containment, syntactic constituency, witness attestation, or another domain relation unless a reviewed semantic mapping establishes the stronger meaning.

## 1. Primary evidence

### 1.1 Text-Fabric data model

The inspected Text-Fabric documentation is `annotation/text-fabric` at commit `1079c68e051947efd955b61ad499e3a9beb03b09`, especially `tf/docs/about/datamodel.md`.

The TF model states that:

- slots are ordered textual positions occupying the first `maxSlot` nodes;
- all slots share one corpus-defined slot type;
- non-slot text objects are nodes;
- text objects may occupy arbitrary compositions of slots;
- nodes may link to one slot, many slots, or no slots;
- `otype` assigns native object-type labels;
- `oslots` is the mandatory valueless edge from non-slot nodes to slots;
- node features map nodes to string/number values;
- edge features map ordered source-target pairs to optional string/number values;
- the edge-feature name is already an implicit relation label;
- `otext` optionally declares sectioning and text-format configuration;
- embedding can be derived from slot-set relationships.

Primary source: <https://github.com/annotation/text-fabric/blob/1079c68e051947efd955b61ad499e3a9beb03b09/tf/docs/about/datamodel.md>

### 1.2 POWLA

POWLA is inspected from `acoli-repo/powla`. Its maintained README explicitly says POWLA represents linguistic annotation structures and **does not aim to model textual data or the anchoring of annotations in textual data**; anchoring is delegated to complementary vocabularies.

POWLA nevertheless provides useful publication/alignment constructs:

- `Node`, `Terminal`, `Nonterminal`, `Root`;
- reified `Relation` with source and target;
- `hasParent` / `hasChild`;
- ordering via `next`;
- annotation layers.

Crucially, POWLA documents `hasParent` as hierarchical annotation with **coverage inheritance**. Phrase structure is a typical case; dependency syntax is explicitly a counterexample. This is stronger than generic TF `oslots`.

Primary sources:
- <https://github.com/acoli-repo/powla/blob/main/Readme.md>
- <https://github.com/acoli-repo/powla/blob/main/owl/powla.owl>

### 1.3 Web Annotation

The W3C Web Annotation Data Model provides annotation targets and selectors for externally addressable resources. The standard Text Position Selector is a contiguous character interval in a normalized character stream. That is useful publication infrastructure but not equivalent to arbitrary TF word/sign slot sets, discontinuous objects, occurrence sets, or technical anchors.

Primary source: <https://www.w3.org/TR/annotation-model/>

### 1.4 OLiA System/annotation-model layer

OLiA is useful for describing corpus annotation schemes and linking them to linguistic reference concepts. It does not provide the missing TF warp semantics: arbitrary slot-set anchoring, technical anchors, zero-slot nodes, valued TF edges, or component-aware sidecars. R-006 therefore keeps OLiA in the semantic pivot while R-007 keeps TF structural mechanics separate.

### 1.5 R-005 corpus evidence

R-005 establishes that the same native TF mechanism can serve materially different purposes:

- ordinary textual extent;
- corpus-wide occurrence extent of an abstract lexeme;
- a technical one-slot anchor whose real semantic relations are explicit edges;
- zero-slot/non-textual nodes;
- semantically addressable entities outside the warp in sidecar/native components.

Therefore `oslots` cannot be treated as a universal domain-containment predicate.

## 2. Structural dimensions ontoTF must preserve

### 2.1 Native identity

A TF node number is meaningful only inside one particular warp/component. Mapping and result provenance must therefore scope every native selector to parent component identity. Integer node IDs are not global semantic identifiers.

### 2.2 Native object type

`otype` is a native structural label. A value such as `word`, `line`, `lex`, `sentence`, or `fragment` is not itself a cross-corpus mapping. Semantic type projection to OLiA, OntoLex, CRMtex, CIDOC CRM, LRMoo, etc. remains separately reviewed.

### 2.3 Slot

A TF slot is an atomic ordered position in the warp. The slot type is corpus-defined:

- BHSA / ExtraBiblical / Syriac / Pseudepigrapha-TF use word slots;
- CUC / TLHdig-TF / the ORACC-TF target use sign slots.

A common structural `Slot` term must therefore carry **no implication** of Word, Sign, Grapheme, Glyph, Character, or Token.

### 2.4 Neutral slot link

`oslots` is the mandatory valueless edge linking non-slot TF nodes to slots. ontoTF needs a neutral public identity for this link because its interpretation varies by native object family. It must not globally be named `hasChild`, `partOf`, `containsWord`, `hasGlyph`, or another domain predicate.

### 2.5 Native carrier kind

Carrier kind and TF extent mode are independent dimensions.

Initial conceptual carrier kinds required by current evidence are:

- **`tf-node`** — semantic entity is realized/addressed as a node in a TF warp;
- **`sidecar` / `native-adapter`** — semantic entity is realized outside the warp and addressed by component-native identity/path.

A sidecar/native-adapter entity has **no `slotLink` and no TF-node extent mode**. It must not receive fake slots simply to fit a structural ontology.

### 2.6 TF-node extent/anchor interpretation

For `carrier=tf-node`, the resolver needs a controlled interpretation of the node's relationship to slots whenever that relationship could affect semantic planning.

R-007 recommends exactly four initial modes:

| mode | meaning | domain reasoning rule |
|---|---|---|
| **`textualExtent`** | the node's slot set is the represented textual/inscriptional extent of the native object | may support separately reviewed containment/segment semantics; discontinuity is allowed |
| **`occurrenceSet`** | the slot set enumerates occurrences/attestations of an abstract entity | do not treat as one text span or ordinary containment hierarchy |
| **`technicalAnchor`** | one or more slots exist only to make the node addressable in the TF warp | never infer semantic extent/containment from the slot link |
| **`noSlot`** | a TF node is intentionally linked to no slots | entity and semantic edges remain valid; no textual extent is implied |

These are structural realization states, not ontology mapping assessments (`exact`, `close`, etc.).

Defaulting every non-slot TF node to `textualExtent` is unsafe.

### 2.7 Node features

A node feature maps nodes to strings/numbers. ontoTF must preserve reviewed applicability and value semantics. Dense empty/`None` storage records are not semantic values and cannot establish feature applicability by themselves.

### 2.8 Directed and valued edge features

A TF edge feature maps an **ordered source-target pair** to either no additional value or a string/number value. ontoTF mapping/IR must preserve at least:

```text
source selector/type
edge feature name
target selector/type
native direction
valued vs unvalued
value semantics when valued
```

A mapping may preserve direction, map to an ontology inverse property, map an edge value to a category, or preserve it as a literal. Those are reviewed decisions, not generic RDF conversion rules.

### 2.9 Section configuration

`otext` can identify configured section levels and text formats, but `book`, `chapter`, `verse`, `tablet`, `column`, `line`, etc. remain corpus-native semantic concepts. Matching section level numbers do not establish equivalence.

### 2.10 Discontinuous objects

TF objects may occupy arbitrary slot sets. A discontinuous object must preserve its exact slot set; ontoTF must never canonicalize it to a bounding contiguous interval merely for publication convenience.

## 3. Corpus stress cases

### 3.1 BHSA

R-005 records word slots; phrase/clause/sentence and distributional atom layers; `lex` nodes; and semantic edges `mother`, `functional_parent`, and `distributional_parent`.

Required distinctions:

- ordinary textual objects can use `textualExtent` where native semantics warrant it;
- BHSA `lex` nodes use **`occurrenceSet`**: their slot set represents lexeme occurrences, not one lexical text span;
- `mother`, `functional_parent`, and `distributional_parent` are explicit semantic edges and must not be reconstructed from or replaced by generic `oslots` embedding;
- functional and distributional atom layers must not be collapsed into one hierarchy.

POWLA `hasParent` is only a candidate for a separately reviewed relation whose native semantics actually satisfy POWLA's coverage-inheritance contract.

### 3.2 CUC

Pinned CUC uses sign slots with word, line, column, and tablet structures and no corpus-specific semantic edge features.

This is a useful case where TF structural navigation can coexist with CRMtex/CRM semantic projections, but:

- a sign slot is not automatically a CRMtex Grapheme or Glyph;
- line/column can be candidate written-text segments only after domain review;
- editorial features such as `emen`, `cert`, and `alt` remain separate assertions.

### 3.3 TLHdig-TF

Pinned TLHdig-TF uses sign slots and a document hierarchy plus `analysis`, `lex`, `cluster`, `fragment`, `note`, `edit`, and `docgroup` overlays.

Critical structural case:

- morphology lives on `analysis` nodes;
- `analysis -> lex` is the explicit lexical relation;
- TLH `lex` nodes use a **`technicalAnchor`**, unlike BHSA `lex` occurrence sets;
- damage/editorial clusters can have range or zero-width semantics;
- sign-level cuneiform is available only when alignment evidence supports it.

Thus two native node types named `lex` may share an eventual OntoLex semantic projection while requiring different TF structural realization metadata.

### 3.4 Pseudepigrapha-TF

The pinned apparatus contract uses explicit `unit`, reading, manuscript/witness structures and directed relations such as `reading_of` and `witness`. Empty readings can explicitly encode omissions; orphan readings can intentionally lack a locus.

The apparatus graph cannot be reconstructed from slot inclusion. Absence of an edge or empty TF storage must never be interpreted as omission.

### 3.5 ORACC-TF target

R-005 treats ORACC-TF as a conversion/stress target. It requires document/text structures, lexical relations, catalogue/object metadata, and zero-span/sidecar cases.

A source label such as `c type=sentence` is not sufficient to make the object a linguistic sentence. Catalogue/object entities may resolve through `carrier=sidecar/native-adapter` rather than TF nodes.

### 3.6 Simple control: ETCBC Syriac

The pinned Syriac control has word slots, book/chapter/verse sections, morphology as node features, and no custom semantic edge features. It demonstrates that a simple profile need not instantiate every structural mechanism.

## 4. Mapping matrix to existing open models

Legend: **direct** = strong fit after native review; **conditional** = useful only after stronger domain semantics are established; **publication** = useful serialization/targeting; **gap** = not faithful enough for canonical TF structural meaning.

| TF structural concept | POWLA | OLiA System | Web Annotation | domain ontologies | decision |
|---|---|---|---|---|---|
| neutral atomic TF slot | `Terminal` is linguistically oriented and anchoring is external | gap | source-selector positions are not TF slot identity | CRMtex types represented signs/glyphs, not TF mechanics | local `Slot` justified |
| exact native `oslots` link | `hasParent/hasChild` is too strong | gap | can select source segments but not generic arbitrary slot-link semantics | domain containment only conditionally | local neutral `slotLink` justified |
| `textualExtent` | suitable POWLA hierarchy only for reviewed linguistic structures | gap | useful publication targeting where lossless | CRMtex segment/CRM containment may apply after review | local mode + domain projection |
| `occurrenceSet` | no direct generic equivalent | gap | multiple source targets are not the same semantic assertion | OntoLex handles lexical entity semantics, not TF warp realization | local mode required |
| `technicalAnchor` | no suitable semantic relation | gap | selector would falsely imply targeted-source meaning | no domain relation should be inferred | local mode required |
| `noSlot` TF node | graph node possible, anchoring outside POWLA scope | gap | resource can exist, but not as TF warp semantics | domain ontology may type the entity | local mode required |
| sidecar/native-adapter entity | outside TF warp | gap | may identify external resource for publication | CRM/LRMoo/OntoLex/etc. can type entity | **carrier kind in IR; not slot-link mode** |
| arbitrary directed edge | reified `Relation` is useful publication form | gap | not a generic graph-edge model | map semantics where justified | keep native edge; optional publication |
| valued directed edge | relation + annotation can publish it | gap | can annotate a relation resource | ontology may model value differently | keep native source/target/value tuple |
| discontinuous slot set | can model discontinuous linguistic structures | gap | standard text-position selector is contiguous | semantic segment mapping is separate | preserve exact TF slot set |
| configured section hierarchy | partial document/layer fit | gap | can target resource segments | CRMtex/LRMoo/CRM may type actual units | preserve `otext` + semantic mapping |
| explicit omission vs storage absence | possible only when explicitly modeled | annotation categories only | can publish explicit state | textology profile handles semantics | never infer from missing/empty data |

## 5. POWLA decision

POWLA remains valuable for actual linguistic graph semantics: annotation layers, explicit hierarchical annotation, reified relations, and ordering.

The global mapping

```text
TF oslots == POWLA hasChild
```

is rejected because POWLA `hasParent/hasChild` carries coverage-inheriting hierarchy semantics while TF `oslots` also supports occurrence sets, technical anchors, and zero-slot nodes.

A separately reviewed explicit constituent relation may still map to POWLA independently of `oslots`.

POWLA should not be a runtime dependency because Context-Fabric already executes exact TF node/edge/slot semantics without lossy reserialization.

## 6. Web Annotation decision

Web Annotation remains optional publication/targeting infrastructure. It is useful for linking evidence or mappings to stable source resources/segments.

It is not canonical TF structure because:

- standard text position selectors are character-offset based and contiguous;
- TF slots may be words or signs;
- TF objects may be discontinuous;
- occurrence sets and technical anchors are not equivalent to source-selection semantics;
- native graph-edge direction/value/applicability is outside selector semantics.

A future publication adapter may define a TF-specific selector for stable slot sets, but R-007 does not require one for runtime or canonical mapping source.

## 7. Explicit absence is not storage absence

The following fail-closed rules are mandatory:

- missing node-feature value does not mean `Unknown`, `Absent`, `Omitted`, `Unattested`, or `Damaged`;
- absent edge does not mean an explicit negative relation;
- no `oslots` edge does not mean omitted text;
- a `noSlot` TF node can be a valid semantic entity;
- an explicit omission must come from a native assertion whose semantics actually mean omission.

## 8. Minimal local structural vocabulary

The initial public vocabulary ceiling justified by current evidence is:

1. **`Slot`** — atomic ordered position in a particular TF warp, with no domain-type implication;
2. **`slotLink`** — neutral public identity corresponding exactly to native `oslots`, with no immediate-child, part, containment, or constituency implication;
3. **`TFNodeExtentMode`** — controlled concept scheme with exactly:
   - `textualExtent`;
   - `occurrenceSet`;
   - `technicalAnchor`;
   - `noSlot`.

`sidecar` / `native-adapter` is **not** a `TFNodeExtentMode`. It belongs exclusively to the canonical IR's native-carrier dimension.

The following should not become ontology terms unless later evidence demonstrates an interoperability requirement:

- NodeFeature;
- EdgeFeature;
- ValuedEdgeFeature;
- edge source/target/value;
- direction flags;
- node integer identity;
- section level number;
- sidecar selector/path.

Those are mapping/IR mechanics. Creating RDF classes for all of them would rebuild Text-Fabric's implementation metamodel without improving semantic interoperability.

## 9. Structural query-planning contract

Conceptually:

```text
semantic request
   ↓
reviewed semantic mapping
   + native structural realization
       carrier: tf-node | sidecar/native-adapter
       if tf-node:
         native node type
         TFNodeExtentMode
         feature/value or edge path
         edge direction/value semantics
       if sidecar/native-adapter:
         component id
         component-native selector/path
   ↓
Context-Fabric native plan
```

### Example: written-text lines

A reviewed CRMtex line/segment mapping identifies the common semantic target. The structural binding identifies CUC/TLH native `otype` and `textualExtent`; Context-Fabric performs native navigation.

### Example: witness reading

The textology profile maps the semantic relation. The Pseudepigrapha binding supplies the directed `reading -> witness` native edge path. Another corpus with a feature named `witness` does not participate unless its reviewed semantic mapping asserts the same relation.

### Example: discontinuous BHSA object

Result identity remains the native object and its exact slot set. Rendering may expose multiple ranges, but must not fabricate one contiguous semantic span.

### Example: ORACC catalogue object

The semantic target can resolve through a sidecar/native-adapter selector with a required component dependency. No fake TF node or slot anchor is introduced.

## 10. P-003 contract requirements

### Preserve

- parent component identity;
- sidecar/native-adapter components;
- explicit native selectors and dependency closure;
- fail-closed compatibility;
- native Context-Fabric execution;
- dense-empty non-semantic rule;
- inspectable native plan/provenance.

### Add/version

1. **native carrier kind**: at minimum `tf-node` versus `sidecar/native-adapter`;
2. **TF-node extent mode** only when `carrier=tf-node`, with the four modes in section 8;
3. schema rules forbidding extent mode on sidecar/native-adapter carriers;
4. exact preservation of discontinuous slot sets;
5. first-class directed edge selector/path semantics;
6. explicit valued/unvalued edge distinction;
7. value-role metadata for valued edges where needed;
8. reviewed feature applicability rather than inference from dense storage records;
9. support for valid `noSlot` TF nodes;
10. optional POWLA/Web Annotation/RDF publication adapters outside runtime execution.

## 11. TDD implications for later implementation

After P-003, structural implementation tickets should start with RED tests for false assumptions:

1. BHSA `lex` occurrence sets are not treated as one text span.
2. TLH `lex` technical anchors are not treated as lexical semantic extents.
3. identical `witness` names across corpora do not create a common relation.
4. an ORACC source `sentence` label does not satisfy linguistic-sentence capability without a reviewed mapping.
5. discontinuous nodes preserve exact slot sets.
6. `noSlot` TF nodes remain addressable.
7. sidecar entities resolve without fake `oslots` and cannot carry `TFNodeExtentMode`.
8. valued-edge direction and value survive native plan compilation.
9. empty/absent storage never becomes explicit omission/absence.
10. a reviewed domain relation may compile to a native edge/path, but `oslots` alone never fabricates it.

## 12. Rejected alternatives

### POWLA as canonical TF structural ontology

Rejected: it is linguistic, delegates textual anchoring, and gives `hasParent/hasChild` stronger coverage-inheritance semantics than generic `oslots`.

### `oslots` as semantic containment

Rejected by concrete occurrence-set and technical-anchor counterexamples.

### Web Annotation selectors as canonical TF extents

Rejected because standard selectors do not losslessly model arbitrary TF slot sets and anchor interpretations.

### Reify the full TF metamodel in a new ontology

Rejected: node-feature/edge-feature/direction/value/component mechanics belong in IR.

### Force sidecar entities into the warp

Rejected: this changes native identity/extent semantics and conflicts with the component-aware P-001 architecture.

### Treat sidecar as a slot-link interpretation

Rejected by adversarial review of the first R-007 head. A sidecar/native-adapter entity is a different **carrier**, not a TF node with a special `oslots` interpretation.

## 13. Remaining boundaries owned elsewhere

R-007 deliberately does not freeze:

- exact OLiA linguistic relation mappings;
- OntoLex lexical/attestation semantics (R-008);
- witness/apparatus semantics (R-009);
- heritage/archaeological semantics (R-010);
- empirical cross-corpus mapping strengths (R-011);
- final target formal kinds/roles (R-013);
- final semantic capability identifiers (R-014).

The exact namespace/serialization of the tiny structural vocabulary is a P-003 design concern after accepted research is reconciled.

## 14. Acceptance-criteria trace

- [x] **Slot coverage vs constituency/containment distinguished.** `oslots` is explicitly kept neutral.
- [x] **Valued edges and direction covered.** Native source/target/direction/value are first-class IR requirements.
- [x] **Discontinuous, zero-span and sidecar semantics covered.** TF-node `noSlot` and sidecar carrier are explicitly separate.
- [x] **POWLA tested against actual TF structures.** BHSA, TLH, Pseudepigrapha, ORACC and CUC provide counterexamples.
- [x] **No RDF/SPARQL runtime requirement.** Native Context-Fabric remains executor.
- [x] **Local vocabulary justified and bounded.** It is capped at `Slot`, `slotLink`, and four `TFNodeExtentMode` concepts; sidecar mechanics stay in IR.
- [x] **Concrete P-003/TDD requirements produced.** Sections 10–11 provide schema and RED-test inputs.

## Review gate

The exact final head requires a fresh logically-independent skeptical review against:

- Text-Fabric's authoritative data-model documentation;
- POWLA's maintained README and OWL semantics;
- W3C Web Annotation selector semantics;
- R-005 pinned corpus evidence;
- R-001/P-001 component-aware sidecar semantics;
- the adversarial-review correction separating carrier kind from TF-node extent mode.

The reviewer should still try to falsify the tiny local-vocabulary recommendation: if a maintained open standard precisely represents `Slot`, neutral `slotLink`, or the four TF-node extent modes without stronger semantics, the local terms should be removed rather than duplicated.
