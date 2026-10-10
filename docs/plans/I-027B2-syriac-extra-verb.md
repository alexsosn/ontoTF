# I-027B2 plan — Syriac then ExtraBiblical exact OLiA Verb

**Issue:** #277  
**Research:** `docs/research/I-027B2-syriac-extra-verb.md`

## Stage S: Syriac production release

- Research pinned ETCBC/linksyr word grammar `sp=verb` and the exact current Syriac TF `sp` inventory. Verify source relation and exact value selector, no broadening to `lex`/phrase nodes.
- Clone 0.2.0 reviewed noun/morphology resources into immutable 0.3.0 *without mutating originals*, add new `native-value-present` dependency, explicit reviewed exact Verb mapping and ontology evidence (reusing the same OLiA core snapshot/versioned Verb lock).
- Add version-explicit loader; preserve default `load_production_linguistic_bundle("syriac")` = 0.2.0.
- Create successor coverage manifest based on current pinned Syriac denominator; add new production accounting only to `node_value:sp="verb"`. Preserve `node_value:ls="prop"` accounting gap unchanged.
- TDD + positive exact query with pinned word-level semantics; negative controls include wrong POS, invented stem equivalence and denial that the Syriac gap has disappeared.
- Full CI and genuinely independent skeptical review.

## Stage E: ExtraBiblical evidence and production release

- First inspect `ETCBC/extrabiblical@9a562...:source/0.2/extraBiblical.mql.bz2` (or a verified source-derived grammar) to establish what its `word.sp=verb` is. The R-005 observation and R-011 historical pilot do not provide production authority by themselves.
- Then replicate the versioned release and one-item immutable coverage approach with its own source evidence/review ID.
- Do not collapse cross-language value meanings or infer verbal morphology from POS labels.

## Completion

For each stage, only merge on a green exact-head focused/full suite and a fresh independent adversarial review. Leave parent #274/#264 open until their remaining work is done.
