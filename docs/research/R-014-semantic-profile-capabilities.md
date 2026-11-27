# R-014: controlled semantic profile and capability identifiers

**Status:** research complete; revised against merged R-011/R-013 and adversarial review; pending final exact-head review  
**Issue:** #48  
**Recorded:** 2026-09-07  
**Depends on:** accepted R-003/R-005 and merged R-006/R-007/R-008/R-009/R-010/R-011/R-012/R-013

## Decision

Replace free-form `profile.semantic_domains` with three controlled layers:

1. **profile** — stable ontoTF interoperability domain;
2. **capability** — profile-scoped agent-discovery ability;
3. **concept/projection** — exact reviewed semantic target/native binding.

Only layer 3 can authorize semantic query compilation.

Profile and capability operational state is:

`active | absent | unavailable`

R-002 concept/projection assessment remains separately:

`exact | close | broader | narrower | related | ambiguous | native-only | unsupported`

`unsupported` is negative concept knowledge. It never activates a capability or profile.

The governing invariant is:

> A profile is active only when at least one capability is active. A capability is active only when at least one reviewed positive native semantic record actually instantiates that capability's meaning. Profile/capability activation never implies a shared ontology projection, whole-ontology support, or execution of an arbitrary requested concept.

This last clause is important: a `native-only` record may activate a capability only when its reviewed native semantics really belong to that capability family. A broader or merely related native object must not activate a narrower capability label.

## 1. Why controlled discovery is required

Free strings cannot safely answer whether:

- `linguistic`, `morphology`, and `OLiA` mean the same thing;
- a `crmtex` label means line segmentation, glyphs, writing systems, or reading activity;
- `archaeology` means physical ancient objects or actual excavation/stratigraphy;
- `lexical` means lemma lookup, entry identity, source senses, shared concepts, or dictionary structure;
- `manuscript` means textual witness identity or physical carrier.

Ontology namespaces are also the wrong discovery vocabulary. A ontoTF profile may compose several ontologies, and one ontology may participate in several profiles.

## 2. Profile catalog

The first catalog contains seven recurring profiles:

- `structural`
- `linguistic`
- `lexical`
- `written-text`
- `textology`
- `heritage`
- `scholarly-inference`

and three optional evidence-gated profiles:

- `archaeology`
- `scientific-analysis`
- `lexicography`

Profile IDs are flat in activation semantics. Dependencies are explicit and versioned; activation never inherits.

Examples:

- `textology` does not imply `written-text`;
- `heritage` does not imply `archaeology`;
- `lexical` does not imply `lexicography`;
- `written-text` does not imply `scholarly-inference`.

### `structural`

Native graph mechanics used to compose queries.

Capabilities:

- `structural.entity-kind`
- `structural.slot-coverage`
- `structural.edge-traversal`
- `structural.section-navigation`

This is intentionally native discovery. It does not assert a shared structural ontology or turn `oslots` into constituency/containment.

### `linguistic`

Capabilities:

- `linguistic.part-of-speech`
- `linguistic.morphology`
- `linguistic.syntax`
- `linguistic.discourse`

Native linguistic support may activate a capability even without an R-011 OLiA projection.

### `lexical`

Capabilities:

- `lexical.entry`
- `lexical.form`
- `lexical.sense`
- `lexical.concept`
- `lexical.relation`

Entry support does not imply sense/concept support.

### `written-text`

Capabilities:

- `written-text.segment`
- `written-text.sign`
- `written-text.writing-system`
- `written-text.transcription-recognition`

Storage shape alone (`sign`, `line`, `surface`) never activates these capabilities.

### `textology`

Capabilities:

- `textology.textual-version`
- `textology.witness`
- `textology.fragment-transmission`
- `textology.apparatus-reading`
- `textology.witness-attestation`
- `textology.explicit-omission`

Native-only apparatus/witness records may legitimately activate textology capabilities.

### `heritage`

Capabilities:

- `heritage.physical-object`
- `heritage.physical-part`
- `heritage.identifier`
- `heritage.material`
- `heritage.place-provenance`
- `heritage.custody-location`

Authority references remain distinct under R-017.

### `scholarly-inference`

Capabilities:

- `scholarly-inference.claim`
- `scholarly-inference.inference`
- `scholarly-inference.meaning-comprehension`
- `scholarly-inference.provenance-assessment`

Flat source facts, catalogue fields, damage flags, and editor codes do not activate this profile.

### Optional profiles

`archaeology` requires actual excavation/stratigraphic/find-context assertions. A `provenience` string is insufficient.

`scientific-analysis` requires explicit observation/measurement/sampling/analysis process or result semantics. Material labels or coordinates are insufficient.

`lexicography` requires reviewed dictionary-specific organization such as entry components or ordered senses. Lemma/gloss/entry presence alone is insufficient.

## 3. Operational state and activation

### 3.1 Positive native semantic record

For activation, a positive native semantic record is a reviewed native assertion whose semantics exist in the corpus and actually instantiate the named capability.

Potential assessments are:

- `exact`
- `close`
- `broader`
- `narrower`
- `related`
- `ambiguous`, when the native semantics exist but target choice is unresolved
- `native-only`

But assessment alone is insufficient. Capability membership is separately reviewed. A `native-only` document identity that is broader than physical-carrier identity does **not** activate `heritage.physical-object` merely because it lives in the heritage domain.

`unsupported` is excluded from the positive set.

### 3.2 Capability state

A capability is `active` only when:

1. its ID is recognized by the profile contract;
2. at least one reviewed positive native record actually instantiates that capability;
3. parent/profile components are compatible enough for inspection;
4. required artifacts can be loaded, or native-only content remains safely inspectable without fabricating a target.

A capability with only negative `unsupported` knowledge is `absent`.

If positive records exist but dependencies are currently incompatible/unloadable, state is `unavailable`.

### 3.3 Profile state

A profile is `active` only if at least one capability is active.

It is `absent` if no positive reviewed capability exists.

It is `unavailable` if positive reviewed capability content exists but operational dependencies block safe use.

This prevents a negative-control record such as “BHSA archaeology unsupported” from activating archaeology.

## 4. Capability summaries

Capability summaries are discovery aids, not mapping assessments:

```yaml
capability: lexical.sense
state: active
records: 12
shared_projections: 8
exact: 5
approximate: 3
ambiguous: 0
native_only: 4
unsupported: 2
executable_exact: true
```

Rules:

- `state` is only `active|absent|unavailable`;
- `shared_projections` counts target-bearing reviewed projections;
- `approximate` aggregates `close|broader|narrower|related` for discovery only;
- `native_only` is positive native support but never shared-target coverage;
- `unsupported` is negative concept knowledge and never activates the capability;
- `executable_exact` means at least one exact concept binding is executable, not that the capability is exact.

No profile/capability-level `exact`, `close`, `partial`, or `unsupported` state exists.

## 5. Concept-level support is authoritative

For a requested target, report separately:

- profile state;
- capability state and ID;
- target identity;
- R-013 formal kind and semantic role;
- R-002 mapping assessment;
- operational availability/compatibility;
- executable/non-executable status under the requested semantic mode;
- compact native binding;
- profile/catalog and parent/ontology provenance fingerprints.

Matching profile/capability IDs across corpora never authorize a cross-corpus plan by themselves.

## 6. Compact `semantic_capabilities`

R-003 progressive disclosure remains the API model: summaries by default; requested concept rows on demand; full mappings only by explicit drill-down.

Correct ORACC example:

```json
{
  "oracc": {
    "profiles": {
      "heritage": {
        "state": "active",
        "capabilities": {
          "heritage.physical-object": {
            "state": "absent",
            "shared_projections": 0,
            "native_only": 0
          },
          "heritage.material": {
            "state": "active",
            "shared_projections": 0,
            "native_only": 1
          },
          "heritage.place-provenance": {
            "state": "active",
            "shared_projections": 0,
            "native_only": 1
          }
        }
      }
    }
  }
}
```

The heritage profile is active because ORACC has reviewed native material/provenience/catalogue semantics. `heritage.physical-object` remains absent because accepted R-011 found generic `otype=document` broader than a reproducibly demonstrated physical-carrier selector. A future separately reviewed object-bearing selector can activate that capability without changing the profile model.

Optional filters:

```text
corpora
profiles
capabilities
concepts
compare
verbosity=compact|full
```

No default call enumerates all ontology terms or mapping rows.

## 7. Accepted seven-pilot evidence

The following classification consumes merged R-005 and R-011. `active/shared` means at least one accepted common projection exists; `active/native` means the profile has reviewed native capability but the cited semantics are not established as a shared pivot in R-011. These are explanatory evidence labels, not extra production states.

| corpus | structural | linguistic | lexical | written-text | textology | heritage | scholarly-inference |
|---|---|---|---|---|---|---|---|
| BHSA | active/native | active/shared | active/shared | absent | absent | absent | absent |
| ETCBC Syriac | active/native | active/shared | active/shared | absent | absent | absent | absent |
| ETCBC ExtraBiblical | active/native | active/shared | active/shared | absent | absent | absent | absent |
| CUC 0.2.8 | active/native | absent | absent | active/shared | absent | active/shared | absent |
| Pseudepigrapha-TF | active/native | absent | absent | absent | active/shared+native | absent without carrier evidence | absent |
| ORACC-TF | active/native | active/native from R-005 POS/morphology; no R-011 OLiA projection | active/shared+native | active/shared | absent for current transmission profile | active/native via material/place-provenance; `heritage.physical-object` absent; generic E22 fails closed | absent |
| TLHdig-TF | active/native | active/native from R-005 analysis/POS/morphology; no R-011 OLiA projection | active/shared+native | active/shared | active/native for witness/fragment/editorial subset | active/shared | absent |

Accepted boundaries:

- shared OLiA reuse: BHSA, Syriac, ExtraBiblical;
- shared OntoLex lexical-entry reuse: BHSA, Syriac, ExtraBiblical, ORACC, TLH;
- CRMtex TX7: CUC, ORACC, TLH;
- CRM E22: CUC and TLH only;
- ORACC generic `otype=document` does not establish `heritage.physical-object`;
- Pseudepigrapha manuscript identity does not establish physical carrier;
- Pseudepigrapha textology includes native apparatus/witness semantics plus conservative F2 textual-version candidate;
- TLH `surface` remains native physical support, not TX7;
- no current pilot activates scholarly-inference merely from ordinary source/editorial facts.

Native-only capability is first-class discovery information only when the reviewed native semantics actually match the capability definition.

## 8. Comparison semantics

Profile comparison reports only:

`active | absent | unavailable`

Capability comparison reports capability state plus counts.

Concept comparison reports exact R-002 assessment and execution state and is the only level that can justify cross-corpus semantic planning.

A requested unsupported concept may still be reported explicitly even when its capability is absent. That is concept-level negative knowledge, not a capability state.

## 9. Optional-profile policy

Current seven-pilot R-014 classification does not activate archaeology, scientific-analysis, or lexicography.

ORACC glossary structure may justify a later explicit lexicography-profile review, but R-011 did not establish that optional contract and R-014 does not retroactively claim it.

## 10. Fail-closed rules

1. Unknown profile ID -> contract error; no free-string fallback.
2. Unknown capability ID -> contract error/unsupported-extension diagnostic; no fuzzy matching.
3. Profile/capability `absent` -> required query non-executable; no similar-label fallback.
4. Profile/capability `unavailable` -> non-executable even if stale cached bindings exist.
5. `unsupported` records never activate profile/capability state.
6. A positive native record activates a capability only if reviewed semantics actually instantiate that capability.
7. A broader/different `native-only` record cannot activate a narrower capability by label/domain association.
8. Active profile never implies every capability active.
9. Active capability never implies every concept executable.
10. Missing target binding never falls back to ontology hierarchy/label similarity.
11. `native-only` never contributes to shared-target coverage.
12. `ambiguous` never becomes executable shared support without reviewed resolution/mode.
13. Optional profiles never auto-activate from domain labels, corpus age/type, or authority literals.
14. Profile dependency/hierarchy never auto-activates another profile.
15. Same profile/capability across corpora never authorizes execution without matching requested concept bindings.

## 11. RED-style contract cases for P-003/TDD

Future production validation must reject at least:

1. free-form semantic-domain/profile IDs;
2. profile inferred from ontology namespace;
3. implicit profile inheritance (`heritage -> archaeology`, `lexical -> lexicography`, etc.);
4. active profile with zero active capabilities;
5. active capability with zero positive native semantic records;
6. activation from `unsupported` records only;
7. `unsupported` used as capability state;
8. active profile treated as whole-ontology support;
9. active capability treated as every target executable;
10. `native-only` counted as shared projection;
11. capability activation from a native-only record whose reviewed semantics are broader/different than the capability definition;
12. ORACC generic `otype=document` activating `heritage.physical-object` or shared E22;
13. Pseudepigrapha `manuscript` automatically activating physical heritage;
14. TLH `surface` advertised as CRMtex TX7;
15. TLH edit/damage records activating CRMinf scholarly-inference without attributed proposition/process evidence;
16. absent/unavailable profile or capability executing through stale/fuzzy/native fallback;
17. archaeology from `provenience` literal alone;
18. scientific-analysis from material/coordinate literals alone;
19. lexicography from lemma/gloss alone;
20. profile/capability-level mapping-strength state (`exact|close|partial|unsupported`);
21. cross-corpus execution merely because profile/capability IDs match;
22. compact discovery dumping all mapping rows by default;
23. ontology release silently changing profile identity.

## 12. Versioning and P-003 inputs

Identity layers remain separate:

1. `catalog_version` — controlled profile/capability catalog;
2. per-profile `contract_version`;
3. R-015 ontology bundle/bridge identity;
4. corpus mapping release and parent component identity.

Do not put ontology versions into profile IDs.

Conceptual indexes:

```text
(corpus, profile-id)
  -> profile operational state + active capability IDs

(corpus, profile-id, capability-id)
  -> capability operational state + summary counts + record IDs

(corpus, profile-id, capability-id, target, formal-kind, semantic-role)
  -> reviewed concept binding(s)
```

The third index is authoritative for execution. The first two are discovery accelerators.

For `native-only`, capability summaries include native support only when capability membership is semantically reviewed; target-keyed reverse indexes never fabricate a semantic target.

## 13. Acceptance closure

- controlled, extensible profile/capability vocabulary replaces unconstrained strings;
- profile activation, capability activation, and concept assessment are separate;
- all seven R-011 pilots are represented without forcing empty archaeology/science/lexicography claims;
- native-only support remains discoverable without inflating shared coverage;
- accepted ORACC carrier failure is preserved at both concept and capability layers;
- compact agent comparison follows R-003 progressive disclosure and fails closed;
- P-003 receives exact catalog/state/index/versioning inputs.

## 14. Remaining boundaries

R-014 does not decide:

- final public URI spelling of profile/capability IDs — P-003/public vocabulary packaging;
- R-013 target kind/role spellings — already accepted, production naming in P-003;
- ontology bundle/bridge identity — R-015;
- approximate execution authorization — R-016;
- external-authority query semantics — R-017;
- production schema/runtime/API implementation — P-003 and later implementation tickets.

Future profile/capability additions require recurring, demonstrated agent-query semantics, not labels copied from an ontology or corpus schema.