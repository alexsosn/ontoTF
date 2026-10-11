# I-028B — 27 lexical ontology dispositions: independent source and model audit

**Issue:** #347, under I-028 #265 / P-004 #202. **Source evidence:** merged #342 / #340, frozen I-028A 27-row ledger and R-005 BHSA/Syriac inventories. **Status:** proposed semantics; no ontology lock, no production release authority.

## Original, independently inspected evidence

- `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da`: R-005 reports **9,230** TF `otype=lex` nodes. They are separately addressable node identities; their `lex`, `lex_utf8`, `lex0`, `voc_lex*` and other annotations are feature *values*. R-005 observes `lex0` has 6,461 distinct spellings versus `lex` with 8,769 distinct values, so deduplication by `lex0` would collapse corpus distinctions.
- `ETCBC/syriac@bb0eaa7e21b020a26b7566d2e495da9b1f84a919`: all five Workstream D features are word-attached strings. R-005 does **not** identify a dedicated lexical-entry node, source-stable lexeme ID or word→lexeme identity relation.
- Final OntoLex-Lemon **W3C Community Group Report** (10 May 2016), https://www.w3.org/2016/05/ontolex/ , §3.1, defines `http://www.w3.org/ns/lemon/ontolex#LexicalEntry` as an entry-level lexical resource. Its Forms (§3.2), Senses (§3.4), lexical concepts (§3.6) and language-tagged written representations are separate kinds. This report is **not a W3C Recommendation**. The previous project R-008 research linked an older *incomplete draft wiki*; this batch uses the actual published final report.
- The published OntoLex Core ontology is **not yet pinned as an installed ontology snapshot/lock** in ontoTF. Citing a community report URI is reviewable semantic evidence, **not** sufficient production release authority.
- Frozen `src/tfont/resources/coverage/p004-r011-baseline-v1/bhsa.json` records the BHSA `node_type:lex` **research** assessment `exact` with source `bhsa-lex-entry`, and `.../syriac.json` records `node_feature:lex` as **research** `close` with source `syriac-lex-entry`. Both are historical research records, not production approvals; the Syriac entry analogy is challenged by current pinned node-scope evidence. Never rewrite historical manifests.

## Proposed disposition and counterexamples

- Only **BHSA `node_type:lex`** may be a candidate `exact` **class** projection to OntoLex `LexicalEntry`; the underlying identity is the actual TF `lex` **node id**, not the `lex` or `lex0` text field. This is a proposal, not an approved per-node RDF publication.
- All remaining 26 features are `native-only` **at this source/ontology evidence level**, i.e. keep queryable in TF, without a reviewed common-target projection *yet*. This is not a claim that no OntoLex, SKOS or complementary vocabulary property exists.
- BHSA `lex_utf8`/`voc_lex_utf8` and other lexical spelling fields might later feed an identified OntoLex Form with `writtenRep`; first identify the Form and canonical/otherForm relationship. Rendering strings alone do not prove either.
- Do not confuse BHSA `g_cons`/`g_word*` token surfaces with entry Forms, and do not identify lexical entries by normalized `lex0`.
- Neither corpus's `gloss` provides lexical sense/concept identity or translation equivalence; **Syriac** metadata explicitly says its English gloss is **not intended for translation**.
- Morphological `root`, English language labels/ISO codes, local frequency/rank and native `nametype` categories remain preserved as source annotations, not invented SKOS ConceptSchemes, LexicalSenses or common pivots.
- Specifically **reject the historical Syriac research-level `close` entry suggestion as unsupported for production** given absence of an independent lexical-entry entity. Retain the original historical record untouched; a future Syriac lexeme construction rule needs explicit source evidence and identity-collision policy.

## Scope and decision

Provide 27/27 individual, original-rationale-linked proposed dispositions keyed to the frozen Workstream D queue, with one source node-class positive candidate and 26 conservative native-only dispositions; no production coverage metric changes. No new runtime abstraction, workflow or per-item PR. A future OntoLex source lock, explicit lexical-element projection contract, and protected reviewed batch publish gate (#303) are required before any candidate becomes installed production coverage.

**Rejected alternatives:** string-equality BHSA↔Syriac lexeme equivalence; minting a Form/Sense/Concept from every feature string; reporting 27 production mappings from source-only evidence; retroactively changing immutable research manifests; treating W3C Community Report as a normative W3C Standard.
