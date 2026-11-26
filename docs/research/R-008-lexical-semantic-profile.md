# R-008: lexical-semantic and dictionary interoperability profile

**Status:** research complete; pending fresh logically-independent adversarial review  
**Issue:** #40  
**Recorded:** 2026-09-07  
**Depends on:** accepted R-002/R-003/R-005, merged R-006 and R-007

## Decision

ontoTF should use a **depth-aware OntoLex/SKOS lexical profile** rather than treating every corpus `lex`, `lemma`, `gloss`, `root`, `base`, `stem`, or dictionary string as the same kind of semantic object.

The first interoperable lexical contract is:

1. **OntoLex-Lemon core is the only mandatory OntoLex module for the baseline lexical profile.** It supplies lexical-entry, form, sense, and lexical-concept identities.
2. **SKOS is mandatory non-OntoLex infrastructure** for shared concept schemes, semantic-domain taxonomies, and concept mappings. ontoTF mapping assessment remains independent of SKOS publication predicates.
3. **LexInfo 3.0 is a supported companion vocabulary**, activated where a native assertion belongs to lexical-resource grammatical/data-category semantics. It is not required merely to activate the baseline lexical profile.
4. **OntoLex VarTrans is capability-gated.** A profile that claims explicit lexical/sense translation or variation capability must activate VarTrans; a corpus with no such native relation does not need it.
5. **OntoLex Lexicog is capability-gated.** It is activated only when dictionary-specific structure such as sense ordering or lexicographic entry organization must be preserved.
6. **OntoLex SynSem / Decomp are optional, evidence-driven modules.** They activate only where the source actually models the corresponding lexical syntax/semantics or decomposition relation.
7. **OntoLex Morph and FrAC remain emerging/reference profiles** for this design until their publication status is separately accepted; no first-profile contract depends on them.
8. external WordNet-family resources may be reviewed authority/mapping targets, not the universal lexical-semantic backbone.

The central invariant is:

> **Native lexical identity, lexical form, lexical sense, root/base/stem structure, gloss/definition text, and shared semantic concept are distinct layers. Matching strings never collapse those identities.**

Consequently, a corpus may support lexical-entry lookup while legitimately reporting sense-level, translation-level, or concept-level queries as unsupported.

## 1. Standards evidence

### 1.1 OntoLex-Lemon core

The Ontology-Lexica Community Group published the OntoLex-Lemon core as a W3C Community Group Final Report in 2016. The core distinguishes at least:

- `ontolex:LexicalEntry` — a unit of lexical analysis grouping morphologically related forms;
- `ontolex:Form` — a form belonging to a lexical entry;
- `ontolex:LexicalSense` — a language-specific meaning of a lexical entry;
- `ontolex:LexicalConcept` — a conceptual meaning lexicalized by one or more entries/senses and modeled as a `skos:Concept`.

The classes are intentionally distinct. A form string is not a lexical entry; an entry is not a sense; a sense is not a shared concept.

Primary sources:

- <https://www.w3.org/community/ontolex/wiki/Final_Model_Specification>
- <https://www.w3.org/community/ontolex/wiki/Main_Page>

### 1.2 SKOS

Because `ontolex:LexicalConcept` is a SKOS concept, SKOS provides the generic machinery for shared semantic concepts and concept schemes. Semantic-domain taxonomies may also be represented as SKOS concept schemes without pretending that every domain category is itself a dictionary sense.

R-002's ontoTF mapping assessment remains the runtime/query contract; SKOS relations are publication semantics only where the mapped resources and relation justify them.

### 1.3 LexInfo 3.0

LexInfo is the data-category ontology for OntoLex-Lemon. The maintained project exposes the current ontology under `ontology/3.0/lexinfo.owl` and includes morphosyntactic properties/values, entry-definition properties, representations, usages, syntactic arguments/frames, and lexical relations.

Primary source: <https://github.com/ontolex/lexinfo>

ontoTF should use LexInfo for **lexical-resource grammatical semantics**. Corpus-token annotation remains primarily an OLiA responsibility under R-006. A source assertion may have complementary OLiA and LexInfo projections only after review; similarity of POS labels is not enough to duplicate mappings automatically.

### 1.4 OntoLex VarTrans

VarTrans is part of the published 2016 model and represents lexical and sense relations, including translation/variation patterns. It is appropriate for an **explicit relation between lexical entries or senses**.

A translation-like gloss string does not create a VarTrans relation because it does not identify the target lexical entry/sense and usually does not assert direction, scope, or equivalence.

VarTrans is therefore **mandatory only for a ontoTF lexical profile/capability that claims translation or variation support**, not for every lexical corpus.

### 1.5 OntoLex Lexicog

Lexicog was published as a W3C Community Group Final Report in 2019. Its specification explicitly recommends using ordinary OntoLex modules when they suffice and adding Lexicog only when lexicographic organization such as sense ordering is needed.

That rule fits ontoTF directly: a TF corpus with a repeated lemma/gloss feature does not become a dictionary merely because lexical strings exist.

Primary source: <https://www.w3.org/2019/09/lexicog/>

### 1.6 Optional / emerging modules

The current OntoLex project page distinguishes:

- published 2016 modules: SynSem, Decomp, VarTrans, LiMe;
- published 2019 Lexicog;
- **emerging** Morph and FrAC modules.

Therefore the first ontoTF lexical profile must not make Morph or FrAC normative dependencies. Their eventual fit for Semitic morphology and corpus attestations may be excellent, but version/publication governance belongs to a later accepted research change.

### 1.7 Module activation matrix

This is the explicit minimum-module answer required by #40:

| capability claimed by a ontoTF profile | OntoLex modules required | companion vocabularies |
|---|---|---|
| baseline entry/form/sense/concept interoperability | **core only** | SKOS mandatory; LexInfo optional by native semantics |
| explicit translation / lexical variation | **core + VarTrans** | SKOS; LexInfo when relevant |
| dictionary-specific entry/sense organization | **core + Lexicog**; VarTrans only if translations/relations also claimed | SKOS; LexInfo when relevant |
| lexical syntactic/semantic frames | **core + SynSem** | LexInfo may supply frames/data categories |
| explicit lexical decomposition | **core + Decomp** | language-specific mappings as reviewed |
| emerging morphology/attestation profile | not first-profile normative | Morph/FrAC remain reference until separately accepted |

A corpus does not load or advertise a module merely because ontoTF supports that module globally.

## 2. Native lexical layers that must not be collapsed

ontoTF needs explicit lexical **entity role/depth** in canonical mapping/IR.

| native/source evidence | semantic interpretation | OntoLex/SKOS candidate | executable capability |
|---|---|---|---|
| stable lexical object/key | lexical-entry identity | `ontolex:LexicalEntry` | entry lookup / occurrence association |
| canonical/lemma/headword representation | lexical form/representation | `ontolex:Form` or representation property, after source review | form filtering |
| inflected/orthographic form object | form identity | `ontolex:Form` | form lookup |
| explicit source sense object/key | source sense identity | `ontolex:LexicalSense` | sense-level query |
| gloss / guide word / translation-looking string | literal annotation only | **no automatic Sense or Concept** | display/filter only if native semantics support it |
| explicit definition text | definition literal on the source-defined object | publication property chosen by profile | definition lookup |
| shared cross-resource meaning | common semantic pivot | `ontolex:LexicalConcept` / `skos:Concept` | cross-corpus concept query when reviewed mapping exists |
| semantic-domain/category value | controlled concept/category | SKOS concept scheme | domain/category query |
| explicit translation/variation relation | relation between entries/senses | VarTrans | cross-language relation query |
| dictionary sense order / structural entry component | lexicographic organization | Lexicog | dictionary-order/structure query |
| root / base / stem assertion | source-specific lexical/morphological relation or value | native-only unless a reviewed module fits | native lookup; no automatic entry identity |

The same mapping package may contain several complementary projections for one native object, but they must keep these roles separate.

## 3. Identity policy

### 3.1 A TF node is not required for lexical identity

A corpus can express lexical identity as:

- a dedicated node;
- a sidecar/dictionary object with a stable native ID;
- a documented repeated feature value that acts as a stable corpus-wide key;
- a deterministic derived grouping explicitly defined by the converter/profile.

ontoTF therefore must not require `otype=lex` in order to support `LexicalEntry`.

However, a string named `lemma` or `lex` is **not sufficient evidence by itself**. The profile must record the identity rule and scope. For a feature-keyed or derived identity, canonical IR must expose that construction and its source/version provenance.

### 3.2 Identity never follows display strings

The following are prohibited identity shortcuts:

- same lemma spelling => same lexical entry;
- same gloss => same sense;
- same guide word => same sense;
- same translated English word => same concept;
- same root/base/stem spelling => same lexical entry;
- same local sense number in different entries/resources => same sense.

### 3.3 Source identity survives semantic mapping

Two source senses may both map `exact` to the same reviewed shared concept without becoming the same source sense. Conversely, one source sense may have several complementary or approximate concept projections without losing its source identity.

Mapping is a projection, not entity deduplication.

## 4. Gloss, sense, definition, and concept decision table

| observed source value | default ontoTF treatment | promotion allowed only when | unsafe promotion |
|---|---|---|---|
| `gloss="stone"` | source literal attached to the native object | source documentation explicitly defines it as something stronger | LexicalSense / LexicalConcept |
| ORACC `gw="stone"` | guide-word/disambiguator literal | source model defines a stronger relation | shared concept |
| ORACC sense `mng="hail"` | meaning/definition-like literal attached to explicit native sense ID | publication profile reviews exact property | new concept solely from string |
| BHSA `gloss` | lexeme-level native literal | source/profile provides independent sense identity | sense identity |
| TLH `gloss` used in `(lemma, gloss)` key | part of converter-defined lexical grouping and display literal | converter/profile separately models senses | sense identity |
| explicit native sense node/record with stable ID | source `LexicalSense` candidate | identity and parent entry relationship are reviewed | merge with another sense based on wording |
| semantic domain code | source category concept | bounded semantics and scheme are reviewed | dictionary sense |
| shared reviewed meaning URI | common `LexicalConcept` / SKOS concept | mapping evidence supports it | replacement of native source sense identity |

A literal can be useful evidence for human mapping review without becoming an executable semantic identity.

## 5. Corpus evidence

### 5.1 BHSA 2021

Pinned corpus: `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da`, TF version `2021`.

R-005 records 9,230 `lex` nodes. Relevant evidence includes:

- word-level `lex`, `lex_utf8`, `g_lex`, `g_lex_utf8`, `sp`, `pdp`, `ls`, language features;
- lex-node `lex`, `voc_lex`, `voc_lex_utf8`, `sp`, `ls`, `nametype`, `gloss`, language features;
- lex-node `oslots` represents the **occurrence set** of the lexeme, not a single text span.

R-008 interpretation:

- the `lex` node is a strong candidate for source lexical-entry identity;
- vocalized/consonantal lexical representations are **candidate** form/representation information pending field-level mapping review;
- `gloss` remains a literal, not a source sense;
- `sp`/other lexical grammatical categories may use LexInfo where they describe the lexical entry, while token/corpus annotation maps through OLiA as governed by R-006;
- `ls` must remain native until its exact lexical-set/category semantics are reviewed; if it forms a controlled category scheme, SKOS is the likely publication/query layer;
- BHSA cannot satisfy an arbitrary sense-level semantic-concept query merely because every lexeme has a gloss.

### 5.2 ETCBC Syriac 0.9

Pinned corpus: `ETCBC/syriac@bb0eaa7e21b020a26b7566d2e495da9b1f84a919`, TF `0.9`.

Relevant word features include `lex`, `g_lex`, `gloss`, `ls`, POS and morphology. There is no separate lexical node in this TF release.

R-008 interpretation:

- a repeated `lex` feature may be usable as a corpus-native lexical key **only if the profile records and verifies its source identity semantics**;
- absence of a dedicated node does not itself block lexical-entry interoperability;
- `g_lex`/other lexical representations are candidate form-level data, not automatically distinct Form identities;
- `gloss` does not create a sense;
- the profile must not fabricate stable sense IDs from `(lex, gloss)` merely to satisfy OntoLex;
- sense-level capability is unsupported unless a reviewed native identity construction exists.

### 5.3 TLHdig-TF

Pinned evidence: `alexsosn/TLHdig-TF@4309cf3318c682282c1480b233786362a3083471`, TF `0.2.0`, upstream TLHdig `0.3`.

The pinned converter design states:

- each morphological candidate is an `analysis` node;
- `analysis -> lex` is the explicit lexical association;
- a `lex` node is keyed on `(lemma, gloss)`;
- stem class and determinative stay on analyses rather than lexeme identity;
- the `lex` node's slot is a technical anchor, not its semantic extent.

R-008 interpretation:

- the converter-defined `lex` node is a candidate lexical-entry object **with explicit provenance that its native identity key is `(lemma, gloss)`**;
- that derived grouping must not be claimed equivalent to BHSA lexical identity merely because both node types are named `lex`;
- the gloss's participation in the grouping key does not turn it into a `LexicalSense`;
- TLH therefore supports entry/analysis association but has no independent source sense object in this layer;
- `stemclass` remains analysis-level native morphology and is not OntoLex decomposition merely by name;
- a query for a shared lexical concept cannot silently use the gloss as its semantic selector.

### 5.4 ORACC-TF stress target / ORACC lexical model

Pinned repository target: `alexsosn/ORACC-TF@ab92001191844b1b0ee656490f0b5c8a66e65b4a`.

#### Pinned glossary evidence

The inspected pinned `data/adsd/adart1/gloss-akk.json` contains explicit glossary structure. A representative entry contains:

- native entry `id` such as `x000001590`;
- `headword`;
- `cf` citation form;
- `gw` guide word;
- POS;
- explicit form records with IDs;
- explicit sense records with IDs such as `x00000159.4` and `x00000159.8`;
- local `num` values `1.`, `2.` within an entry;
- `mng` meaning strings;
- norm/form/signature records.

The example `abnu[stone]N` has two source sense records, `hail` and `hailstone`, demonstrating that entry identity and source sense identity are separate even when the citation form is the same.

The pinned corpus JSON also exposes parsed lemmatization fields such as `cf`, `gw`, `sense`, `norm`, `pos`, and `epos` on occurrences.

#### Authoritative ORACC CBD/signature semantics

The absence of `root` or `bases` in this particular `adart1` Akkadian glossary sample is **sample-specific**, not a statement about the ORACC lexical model.

ORACC's authoritative Corpus-Based Dictionary and lemmatization documentation distinguishes:

- **CF (Citation Form)** — dictionary headword / fundamental entry form;
- **GW (Guide Word)** — a disambiguating label, often a basic meaning or hypernym, used to separate homophones; it is not a source sense identity;
- **SENSE** — an optional context/source sense distinct from GW;
- **`@root`** — optional entry-level Akkadian root annotation; ORACC policy ties it to a root list, but it remains a root assertion, not an entry identity;
- **`@bases`** — Sumerian entry-level inventory of bases, optionally associating stems with bases;
- **BASE** in a lemmatization/signature — the word base used in a particular writing, expected to correspond to an entry base where that language model uses bases;
- **STEM** in a signature — an occurrence/form-level stem field distinct from the lexical entry and from the entry's root/base inventory.

Primary ORACC sources:

- <https://oracc.museum.upenn.edu/doc/help/glossaries/>
- <https://oracc.museum.upenn.edu/doc/help/managingprojects/procedures/>
- <https://oracc.museum.upenn.edu/doc/help/lemmatising/syntax/>
- <https://oracc.museum.upenn.edu/ns/cbd/1.0/>

#### ontoTF interpretation

- ORACC glossary entry IDs are strong source `LexicalEntry` candidates, version-scoped to the pinned glossary;
- form IDs are strong `Form` candidates where the exact form semantics are reviewed;
- sense IDs are strong `LexicalSense` candidates;
- `num` is local ordering metadata, not global sense identity;
- `cf` is citation-form information, not the whole lexical-entry identity;
- `gw` is a disambiguator/guide word, not a shared concept;
- `mng` is sense-attached meaning/definition text, not a concept identifier;
- entry `ROOT`, entry `BASE` inventory, occurrence/signature `BASE`, and occurrence/signature `STEM` are **four different semantic roles** and must be preserved separately;
- none of ROOT/BASE/STEM becomes `LexicalEntry` merely because it can be used in lexicographic organization;
- Decomp may be considered only for a source relation that actually has decomposition semantics; ORACC BASE/STEM strings do not activate Decomp automatically;
- Lexicog becomes useful if ontoTF needs to preserve/query explicit sense ordering and dictionary structure.

This resolves the #40 root/base requirement without claiming that every ORACC project/language instantiates every field.

ORACC-TF remains a stress/conversion target rather than a released ontoTF profile; final mappings belong to R-011/P-003.

### 5.5 CUC 0.2.8

Pinned corpus: `DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`, TF `0.2.8`.

The released TF directory contains sign/text/document/editorial features such as `sign`, `usign`, `g_cons`, `language`, `alt`, `cert`, `emen`, tablet/column/line metadata, and warp/text features. It does **not** contain a lexical-entry, lemma, gloss, sense, or semantic-domain feature in that released TF layer.

The repository contains separate/ongoing lexical and morphology tooling, including DULAT-assisted agent material, but that is not evidence that TF `0.2.8` exposes a released lexical-semantic capability.

Therefore the R-008 profile must report lexical entry/sense/concept queries as unsupported for CUC `0.2.8`; it must not infer them from external tooling or from word forms.

### 5.6 External resource control: Open English WordNet / WordNet family

Open English WordNet is an open lexical network with explicitly identified lexical/synset structure and CC-BY-4.0 licensing. Open Multilingual Wordnet/CILI can be useful external multilingual alignment infrastructure, but constituent resources and versions must remain separately governed rather than becoming an implicit universal authority.

Use in ontoTF:

- optional authority/mapping target for reviewed lexical concepts/senses;
- never the definition of ontoTF's common lexical schema;
- no automatic mapping from English gloss text to WordNet synset;
- exact external IDs and resource release/license must be locked when used in a released profile.

## 6. Root, base, stem, lemma, and entry

The first profile uses conservative rules.

### Lemma / citation form

A lemma or citation-form string is normally a **representation/form**, not lexical-entry identity by itself. It can participate in a source identity rule only when the native resource defines that rule explicitly.

### Root

A root is a lexical/morphological abstraction that may relate several lexical entries or forms. It is not automatically an OntoLex LexicalEntry, Form, or LexicalConcept.

### Base

`base` is source-model-specific. ORACC's Sumerian CBD `@bases` inventory belongs to an entry, while signature BASE records the base used in a particular writing. Those two roles must not be collapsed even when their strings match.

### Stem

A stem or stem class may be occurrence-/analysis-level morphology. TLH `stemclass` and ORACC signature STEM are not entry identities and do not activate OntoLex Decomp automatically.

### First-profile rule

- do not map root/base/stem to `LexicalEntry` merely because it indexes or helps disambiguate a dictionary;
- do not model a stem class as lexical decomposition merely because the string resembles a morpheme;
- use Decomp only when the source provides a reviewed decomposition relation whose semantics match the module;
- keep language-specific root/stem/base systems native or profile-local until a maintained profile models the exact distinction;
- OntoLex Morph may later provide a better shared model, but R-008 does not depend on an emerging module.

This avoids building a comparative Semitic or cuneiform morphology theory into the lexical adapter.

## 7. Shared lexical concepts

### 7.1 Purpose

`ontolex:LexicalConcept` is the preferred lexical-semantic pivot when the reviewed common meaning is specifically a lexical concept. It is also a `skos:Concept`, so it can participate in concept schemes and SKOS hierarchy/mapping relations.

Concept identity is **independent** of native source sense identity.

```text
ORACC source sense S1 ----\
BHSA reviewed lexical unit -- mapping assertions --> shared LexicalConcept C
Dictionary sense D3 ------/
```

The mapping assertions retain source identity, assessment, evidence, ontology/resource locks, and applicability.

### 7.2 Semantic domain concepts

A semantic-domain category may be a plain SKOS concept instead of a LexicalConcept when it classifies senses/entries rather than denoting the lexicalized meaning itself.

```text
LexicalConcept: HAILSTONE
  classifiedBy -> semantic-domain concept WEATHER
```

ontoTF must not collapse the lexical concept and its domain category merely because both are SKOS concepts.

### 7.3 Mapping strengths

R-002's eight assessments remain authoritative:

`exact | close | broader | narrower | related | ambiguous | native-only | unsupported`

For lexical concepts:

- `exact` is a reviewed coextensiveness claim for ontoTF query projection, not source-sense identity;
- `close` does not authorize silent interchangeability;
- `broader` / `narrower` preserve direction from native/source semantics to target concept;
- `related` is informative-only by default;
- `ambiguous` never auto-selects a concept;
- `native-only` can preserve a source sense/entry without a common concept;
- `unsupported` reports absent capability.

Approximate execution behavior remains governed by R-016.

## 8. Translation and variation

VarTrans should represent only **explicit reviewed lexical/sense relations**.

Safe cases:

- dictionary source explicitly identifies translation equivalent A ↔ B;
- a reviewed lexicon links a source sense to a target-language sense;
- source explicitly marks lexical variants.

Unsafe shortcuts:

- `BHSA gloss="stone"` => English lexical entry `stone`;
- ORACC `gw="destroy"` => English sense identity;
- two entries share the same English gloss => translation relation;
- translation relation => semantic identity/exact concept mapping.

A source can translate another expression approximately or contextually; translation must remain separate from ontoTF's mapping assessment.

A corpus with no explicit translation/variation relation can use the baseline lexical profile without VarTrans.

## 9. Dictionary structure and Lexicog

Lexicog is activated only when the lexicographic view itself matters.

Strong candidate: ORACC glossary, because it contains explicit entries, forms, multiple sense records and local sense ordering.

Weak/non-candidate cases:

- BHSA lexeme nodes with one gloss field;
- TLH derived lexeme groupings;
- Syriac repeated lexical feature values;
- CUC 0.2.8 with no released lexical layer.

ontoTF must not manufacture sense ordering or dictionary-entry components in corpora that do not assert them.

## 10. LexInfo and OLiA composition

R-006 assigns OLiA the primary role for corpus linguistic annotations. R-008 assigns LexInfo a complementary lexical-resource role.

```text
word/token POS annotation -> OLiA mapping
lexical-entry grammatical category -> LexInfo mapping
```

If one native field serves both functions, ontoTF may publish complementary projections only after reviewing both meanings. It must not create two mappings solely because `Noun` exists in both ontologies.

This distinction keeps the lexical profile composable with the seven-model pivot rather than making LexInfo a competing universal grammar ontology.

## 11. Agent/query contract

### 11.1 Capability depth

A lexical profile must expose independent capabilities for:

- lexical-entry identity;
- form/representation;
- occurrence/attestation association;
- source-sense identity;
- shared lexical-concept mapping;
- semantic-domain/category mapping;
- root/base/stem structure where natively present;
- translation/variation relation;
- lexicographic structure.

Profile activation does not imply all depths or modules are supported.

Illustrative capability matrix:

| corpus | entry | form | source sense | root/base/stem | shared concept | dictionary structure |
|---|---:|---:|---:|---:|---:|---:|
| BHSA | strong candidate | **candidate** | no independent sense in inspected layer | local/native morphology | only reviewed mappings | no |
| Syriac 0.9 | conditional feature-key identity | candidate | unsupported | local/native morphology | only reviewed mappings | no |
| TLHdig-TF | converter-defined candidate | candidate | unsupported | analysis-level stem class | only reviewed mappings | no |
| ORACC glossary/model | explicit entry records | explicit/candidate forms | explicit | model supports distinct ROOT/BASE/STEM roles; project-dependent | only reviewed mappings | candidate Lexicog |
| CUC 0.2.8 | unsupported | no lexical-form capability | unsupported | unsupported | unsupported | unsupported |

### 11.2 Query planning

Example common concept request:

```text
request: shared lexical concept C
   ↓
semantic->native lexical binding index
   ↓
per corpus:
  ORACC -> reviewed source sense/entry IDs -> native word/lex association
  BHSA  -> reviewed lexeme mapping if available -> lex occurrences
  TLH   -> reviewed lex mapping if available -> analysis -> lex -> word
  Syriac -> only if a reviewed lexical-key mapping exists
  CUC 0.2.8 -> unsupported
```

A missing sense layer cannot be substituted by a gloss comparison.

A root/base/stem query likewise requires the exact native role. A request for ORACC entry ROOT must not silently match occurrence BASE or STEM values.

### 11.3 Explanation

Every lexical resolution should expose:

- requested shared concept/relation;
- source lexical role used (`entry`, `sense`, `form`, `root`, `base`, `stem`, category, etc.);
- native identity rule/selector;
- native path to occurrences/results;
- activated OntoLex module/capability where relevant;
- ontoTF mapping assessment;
- ontology/resource lock;
- profile/mapping version;
- parent component identity/compatibility;
- explicit loss or unsupported depth.

## 12. P-003 schema/IR requirements

### Preserve

- P-001 component-aware parent identity;
- ontology/resource locks;
- mapping assessment independent of publication relation;
- content-addressed evidence/review;
- native selector/path provenance;
- fail-closed execution;
- `native-only` / `unsupported` no-target states.

### Add/version

1. **target semantic role/type** capable of distinguishing lexical entry, form, sense, lexical concept, category concept, and relation target;
2. **native lexical role** independent of feature/node names, including root/base/stem distinctions;
3. **native identity construction** for node-, sidecar-, feature-key-, and derived-grouping lexical entities;
4. **lexical depth capabilities** at profile/concept level;
5. **module activation/capability declaration**: baseline core vs VarTrans/Lexicog/SynSem/Decomp extensions;
6. projection-level ontology/resource lock and mapping assessment as required by R-006;
7. explicit parent-entry relation for source senses;
8. explicit source sense ID distinct from display/order strings;
9. literal fields (`gloss`, `guide_word`, `definition`, etc.) kept distinct from semantic targets;
10. explicit concept-scheme membership for semantic-domain categories;
11. explicit VarTrans relation binding rather than translation inference from strings;
12. optional Lexicog activation/capability state;
13. deterministic semantic->native indexes for entry/sense/concept resolution;
14. unsupported-depth reason codes so an agent can distinguish `no lexical profile` from `entry supported, sense unsupported` or `baseline lexical profile, translation module inactive`.

## 13. RED/TDD contract cases for later implementation

P-003/later production tickets should begin with failing tests for at least:

1. **identical glosses do not merge senses.** Two native senses with `gloss="stone"` retain separate identities.
2. **lemma string is not automatic entry identity.** A feature called `lemma` without a reviewed identity rule cannot satisfy entry lookup.
3. **ORACC guide word is not a concept.** `gw="stone"` cannot resolve a shared concept without a reviewed mapping.
4. **ORACC sense number is local.** `num="1."` in two entries is not a shared sense ID.
5. **ORACC root/base/stem roles stay distinct.** An entry ROOT request cannot compile to signature BASE/STEM or Sumerian entry BASE solely because strings match.
6. **TLH gloss is not a sense.** `(lemma, gloss)` lexical grouping can support entry association while sense-level query remains unsupported.
7. **BHSA gloss is not a sense.** A lexeme with a gloss cannot satisfy an arbitrary LexicalSense query.
8. **root/stem is not entry.** Source root/base/stem fields never compile to LexicalEntry solely by name.
9. **translation is not identity.** VarTrans relation does not create `exact` ontoTF mapping or `owl:sameAs`.
10. **same concept does not collapse native senses.** Two source senses mapped exact to one shared concept remain two source identities/results when queried natively.
11. **one source sense may have multiple projections.** Complementary/approximate concept mappings are not treated as ambiguity unless the mapping says `ambiguous`.
12. **CUC 0.2.8 fails closed.** Sense/concept request reports unsupported rather than lexicalizing word strings.
13. **module activation is fail-closed.** Translation query fails with `module/capability inactive` when core is active but VarTrans is not.
14. **Lexicog is profile-gated.** Sense order/entry-structure queries fail closed when Lexicog capability is inactive.
15. **resource version matters.** Changing an external lexical authority lock invalidates reviewed semantic projection until revalidated.
16. **cross-language gloss coincidence is inert.** Matching translated literals across languages creates no relation without explicit mapping evidence.

## 14. Rejected alternatives

### One generic `lexical` target type

Rejected because entries, forms, senses, concepts, categories and relations have different identity and query semantics.

### Gloss normalization as semantic interoperability

Rejected. It is linguistically lossy, language-dependent, polysemy-blind, and cannot preserve provenance.

### WordNet as universal concept ontology

Rejected. WordNet-family resources are useful reviewed authorities but do not cover all ancient-language lexical theories, domain schemes, proper names, roots, technical glosses, or corpus-specific senses.

### Generate a LexicalSense for every `(lemma, gloss)` pair

Rejected. TLH shows a real derived grouping keyed that way, but the source does not thereby assert an independent lexical sense. BHSA/Syriac glosses provide additional counterexamples.

### Require dedicated lexeme nodes

Rejected. Native lexical identity may be sidecar- or key-based if the source contract makes it stable and reviewable.

### Treat all POS through LexInfo

Rejected. OLiA remains the primary corpus-annotation layer; LexInfo is used where lexical-resource semantics warrant it.

### Make VarTrans mandatory for all lexical profiles

Rejected. VarTrans is required when a profile claims translation/variation capability, not when a corpus has no such source relation.

### Make Lexicog mandatory

Rejected by its own best-practice guidance and by the corpus evidence: most TF corpora are not dictionaries.

### Depend on emerging OntoLex Morph/FrAC now

Rejected for the first profile. Their future fit should be revisited after stable publication/version governance is accepted.

## 15. Unresolved questions owned by later work

R-008 deliberately does not freeze:

- exact lexical concept mappings for BHSA/ORACC/TLH/Syriac (R-011);
- exact target formal-kind/semantic-role enum names (R-013);
- exact profile/capability IDs (R-014);
- approximate execution policy (R-016);
- external authority identity semantics (R-017);
- final OntoLex Morph/FrAC support after their status changes;
- a universal model for Semitic/cuneiform roots, bases, and stems, which current evidence does not justify.

## 16. Acceptance-criteria trace

- [x] **Gloss strings are not promoted to senses/concepts.** Sections 2 and 4 make this a fail-closed invariant.
- [x] **Reusable common lexical concepts defined.** `ontolex:LexicalConcept` + SKOS is the shared semantic pivot.
- [x] **Multiple source sense inventories preserve identity.** Mapping never deduplicates native senses.
- [x] **Cross-language relations covered.** VarTrans is capability-gated and used only for explicit reviewed translation/variation relations.
- [x] **Root/base/stem distinguished from entry identity.** ORACC CBD/signature semantics and TLH analysis evidence are explicitly separated.
- [x] **BHSA, ORACC-TF, TLHdig-TF, Syriac and CUC tested.** Section 5 records depth-specific evidence and negative capability cases.
- [x] **Minimum OntoLex module set frozen.** Core is the only mandatory baseline module; VarTrans/Lexicog/SynSem/Decomp activate only with their claimed capability; Morph/FrAC remain reference.
- [x] **P-003 machine-contract inputs produced.** Sections 11–13 define capability, IR and RED-test requirements.

## Review gate

The exact final head requires a fresh logically-independent skeptical review against:

- OntoLex-Lemon 2016 core and VarTrans;
- OntoLex Lexicog 2019;
- LexInfo 3.0;
- R-002/R-006 ontology-role governance;
- R-005 pinned corpus evidence;
- pinned ORACC glossary/TLH converter structures and authoritative ORACC CBD/signature semantics;
- the CUC 0.2.8 negative capability case;
- the first-head adversarial corrections for ORACC root/base/stem coverage and module activation.

The reviewer should actively challenge whether any corpus field has been over-promoted to an OntoLex entity, whether the capability-gated module contract is genuinely minimal, and whether the proposed depth model can distinguish shallow lexical annotation from true source-sense/root/base/stem identity without fabricating semantics.
