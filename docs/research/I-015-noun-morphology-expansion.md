# I-015 research — production noun morphology expansion

**Issue:** #196  
**Baseline:** `main` `3f67c56d9d578e28aacbc545e2279f45a7ba785f`  
**Scope:** pinned BHSA 2021, Syriac 0.9, ExtraBiblical 0.2, pinned OLiA reference snapshot

## Decision

Expand the production linguistic slice beyond broad `olia:Noun` with six exact semantic atoms that are source-backed in all three pinned corpora:

- `http://purl.org/olia/olia.owl#ProperNoun`
- `http://purl.org/olia/olia.owl#Masculine`
- `http://purl.org/olia/olia.owl#Feminine`
- `http://purl.org/olia/olia.owl#Singular`
- `http://purl.org/olia/olia.owl#Plural`
- `http://purl.org/olia/olia.owl#Dual`

Keep the current broad `olia:Noun` mapping.

Add production exact conjunction execution for **different SemanticKeys** so callers can ask for noun-restricted morphology, e.g. `Noun AND Plural` or `Noun AND Feminine`. A conjunction is the deterministic node-set intersection of independently resolved exact atoms. Every atom remains independently reviewed and retains its provenance.

This does not authorize R-018 same-semantic-key multi-binding composition. The current `multiple_exact_bindings` failure remains unchanged.

## Native evidence

### BHSA

Pinned BHSA feature documentation defines:

- `sp=nmpr` = proper noun;
- `sp=subs` = noun;
- `gn=m` = masculine, `gn=f` = feminine;
- `nu=sg` = singular, `nu=du` = dual, `nu=pl` = plural.

The generated R-005 inventory for the same pinned TF version independently observes those values on word nodes.

Production selectors:

| target | selector |
| --- | --- |
| ProperNoun | `word.sp=nmpr` |
| Masculine | `word.gn=m` |
| Feminine | `word.gn=f` |
| Singular | `word.nu=sg` |
| Plural | `word.nu=pl` |
| Dual | `word.nu=du` |

### Syriac

Pinned `ETCBC/linksyr@3ba42432…/data/lib/syriac/word_grammar` explicitly defines:

- `gn: gender = f: feminine, m: masculine`;
- `nu: number = sg: singular, du: dual, pl: plural`;
- `ls: lexical set = prop: proper noun`;
- `sp=subs` = substantive.

The source lexicon contains ordinary proper-name entries as `sp=subs:ls=prop`, confirming that properness is represented through `ls=prop` rather than a separate POS value. The pinned Syriac 0.9 R-005 inventory observes `gn={f,m,unknown}`, `nu={sg,du,pl,unknown}`, and `ls=prop`.

Production selectors:

| target | selector |
| --- | --- |
| ProperNoun | `word.ls=prop` |
| Masculine | `word.gn=m` |
| Feminine | `word.gn=f` |
| Singular | `word.nu=sg` |
| Plural | `word.nu=pl` |
| Dual | `word.nu=du` |

A conjunction such as `Noun AND ProperNoun` is therefore valid but redundant for Syriac; the independent ProperNoun mapping itself uses `ls=prop`.

### ExtraBiblical

The pinned ExtraBiblical repository identifies itself as an ETCBC/BHSA-family conversion and points to BHSA core feature documentation as its feature authority. Its pinned TF 0.2 payload independently observes:

- `sp=nmpr` and `sp=subs`;
- `gn=m/f`;
- `nu=sg/du/pl`.

Production selectors therefore mirror the reviewed BHSA feature semantics:

| target | selector |
| --- | --- |
| ProperNoun | `word.sp=nmpr` |
| Masculine | `word.gn=m` |
| Feminine | `word.gn=f` |
| Singular | `word.nu=sg` |
| Plural | `word.nu=pl` |
| Dual | `word.nu=du` |

## OLiA evidence

The exact bundled OLiA snapshot at `acoli-repo/olia@d3bd4f1…` contains:

- `ProperNoun` as an OWL class and subclass of `Noun`;
- `Masculine` and `Feminine` as OWL classes under `olia-top:GenderFeature`;
- `Singular`, `Plural`, and `Dual` as OWL classes under `olia-top:NumberFeature`.

The existing production ontology lock already pins the exact bytes and revision. I-015 should extend the lock's `terms_used` and add normalized reviewed evidence records for these target declarations rather than introducing a new ontology source.

## Capability model

- `ProperNoun` remains under `linguistic.part-of-speech`.
- gender and number targets use the already-defined `linguistic.morphology` capability.
- no new controlled vocabulary is required.

## Exact conjunction semantics

The current production resolver accepts one `SemanticKey` per request. R-016 already established the policy for conjunctions of independently required semantic atoms: every atom must execute and no atom may be dropped.

I-015 productionizes the exact-only subset:

1. request contains two or more unique SemanticKeys and one or more corpora;
2. each atom is resolved using the existing exact resolver contract and the same fresh prerequisite state;
3. failure of any atom fails the whole conjunction;
4. per corpus, execute every atom independently using the existing typed native bindings;
5. result nodes are the sorted intersection of all atom result sets;
6. retain every constituent exact plan, mapping/projection review, evidence and prerequisite fingerprint;
7. conjunction and execution fingerprints are canonical and key-order independent;
8. no generic boolean tree, OR, NOT, query string or ontology-derived substitution is introduced.

This is semantically distinct from R-018 multi-binding composition because the members have different semantic keys and are explicitly required by the caller.

## Deliberate exclusions

### CommonNoun

BHSA and ExtraBiblical can plausibly use `sp=subs`, but Syriac broad `sp=subs` includes proper nouns and exact CommonNoun would require a negative/composite condition such as `sp=subs AND ls!=prop`. I-015 does not introduce negation merely to fill the table.

### State

BHSA itself documents that a better definition of `st` and its values is needed. Syriac has a different state vocabulary (`abs`, `cst`, `emph`, plus observed `c`/unknown states). No exact common-state production claim is authorized here.

### Person

R-011 contains exact first-person pilot rows, but person is not needed to make the noun layer materially useful and remains outside this bounded change.

## Acceptance

A production user with verified pinned corpus contexts must be able to:

- resolve and execute each of the six new atoms cross-corpus where requested;
- execute `Noun AND Masculine`, `Noun AND Feminine`, `Noun AND Singular`, `Noun AND Plural`, and `Noun AND Dual` across all three production corpora;
- execute combinations such as `ProperNoun AND Feminine`;
- receive deterministic node intersections and complete constituent provenance;
- observe failure if any requested atom/corpus prerequisite or mapping is unavailable;
- retain the existing fail-closed behavior for multiple exact bindings under one SemanticKey.

## Implementation direction

Keep the mapping schema unchanged. Add the new reviewed mappings to the existing production linguistic mapping artifact, add the required profile dependencies/evidence, extend the OLiA lock/evidence, and generalize the production loader name/API so the public surface no longer pretends that the bundle contains only Noun.

Add a separate exact-conjunction request/result API rather than changing `SemanticResolveRequest.key` from singular to polymorphic. This preserves the existing v0.1 exact single-atom contract and makes conjunction semantics explicit.
