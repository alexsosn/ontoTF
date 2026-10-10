# I-027C2 — BHSA/Syriac exact Adjective and Adverb review

**Issue:** #288, child of #283 and #264. **No automatic ExtraBiblical semantic transfer.**

## Native-source evidence

- BHSA: `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da:docs/features/sp.md`. The explicit table describes `adjv` as *adjective* and `advb` as *adverb*. `sp` is defined at `word` and `lex` levels; this production mapping is limited to `word`, not the union.
- Syriac: `ETCBC/linksyr@3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6:data/lib/syriac/word_grammar`: independently defines `sp: "part of speech"` with `adjv:"adjective"` and `advb:"adverb"`. The target TF parent remains `ETCBC/syriac@bb0eaa7e21b020a26b7566d2e495da9b1f84a919`.
- Original-source POS evidence matrix from #285: `docs/research/data/generated/i027c1/native-pos-matrix.json`. BHSA: 10,141 adjective, 4,603 adverb `sp` feature observations (word+lex combined); Syriac: 9,001 adjective and 5,290 adverb word-level `sp` records. These are feature counts; the exact mapping is `word` scoped.

## Target ontology evidence

Pinned OLiA source `acoli-repo/olia@d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6:owl/core/olia.owl`, Git blob `5c5e8bda93eaeab2940472a167ff8d3107be8d43`, independently read from real snapshot:

- `http://purl.org/olia/olia.owl#Adjective` declared `owl:Class`, subordinate to `olia-top.owl#MorphosyntacticCategory`; source describes nominal property modifiers.
- `http://purl.org/olia/olia.owl#Adverb` declared `owl:Class`; source describes modifiers of verbal, adjectival, clausal and other non-nominal domains.

The classes are morphosyntactic annotation categories, not claims of lexical identity, valency, tense, syntactic dependency relation, agreement or phrase-level semantics.

## Review verdict

GO for exact *annotation-category* correspondence, and only these four POS-category selectors:

- `BHSA word.sp=adjv → OLiA Adjective`
- `BHSA word.sp=advb → OLiA Adverb`
- `Syriac word.sp=adjv → OLiA Adjective`
- `Syriac word.sp=advb → OLiA Adverb`

ExtraBiblical original MQL contains enum ids `adjv=13`, `advb=4` but no independently verified English glosses; no ExtraBiblical mapping in this release. `pdp` and verbal-stem `vs` are not substitutes for native `sp`.

## Release and conservation

Use new immutable `0.4.0` profiles, retain and explicitly load all historical `0.1.0`/ `0.2.0` / `0.3.0` ones, extend a versioned existing pinned-ontology lock terms list with Adjective and Adverb (same source snapshot). BHSA 35→37 reviewed and shared target 8→10, Syriac 7→9 reviewed/shared 7→9, subject to independent exact-head review/CI. Do not mutate current `p004-current-v1` queue snapshot (#287), which is versioned provenance; publish another selector successor later.
