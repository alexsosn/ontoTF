# I-028A — BHSA/Syriac lexical-depth evidence (Workstream D)

**Issue:** #340; child of #265 / #202. **Authority:** source-grounded research and *unapproved mapping candidates*, not production review.

## Research gate: actual corpus data

- Frozen routing: `docs/research/data/generated/i026/p004-work-queue.json`, `workstream=D` has exactly 22 BHSA and five Syriac native item identities. The total P-004 Workstream D denominator is 67, so this batch is 27/67 **researched** (not 27/67 released).
- BHSA: `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da`, `docs/research/data/generated/r005/bhsa.json`, TF files SHA256 `5b179e543d9ce17f59c2902afdf3736d3803777f518ec92dd5f19fc14a96496d`. R-005 observes 9,230 genuine `lex` nodes, while `lex`, `lex0`, `lex_utf8`, and `voc_lex*` are **string-valued features** on lex and/or word nodes.
- Syriac: `ETCBC/syriac@bb0eaa7e21b020a26b7566d2e495da9b1f84a919`, `docs/research/data/generated/r005/syriac.json`, TF files SHA256 `eca80cb23fc2cea0b55381d9cea0cc313eeccd42879a2d686e769145a8ada2eb`. Its five Workstream D features are word-level **strings**; R-008 found no independent lexeme node. The Syriac `gloss` metadata explicitly says it is *not intended for translation purposes*.
- Ontology research: `docs/research/R-008-lexical-semantic-profile.md` evaluates W3C OntoLex-Lemon and SKOS and keeps `LexicalEntry`, `Form`, `LexicalSense`, `LexicalConcept`, root, gloss and token text distinct. No OntoLex/SKOS source snapshot is yet vendored under `src/tfont/resources/ontologies`; candidate targets must therefore remain unapproved and unpublishable.

## Semantic distinctions to preserve

1. BHSA `otype=lex` is a **candidate source lexical-entry identity**. It is *not* a literal lexical spelling; promotion requires a pinned OntoLex class target and a separate review.
2. BHSA `lex` is a disambiguated lexeme string; `lex0` explicitly strips disambiguation. R-005 observes 8,769 different `lex` values but only 6,461 different `lex0` values. **Never** build lexical-entry identity from `lex0` or merge entries by displayed spelling.
3. `g_cons*` and `g_word*` describe the surface **word**; `g_lex*` and `voc_lex*` describe lexical representation or vocalization. A string attached to a word is not proof of a separately identified `ontolex:Form` resource.
4. BHSA `gloss` is English translation-of-lexeme metadata; Syriac `gloss` is an English lexical gloss *not intended for translation*. Neither supplies sense identity, a cross-language equivalence, a lexical concept URI or a SKOS concept.
5. BHSA `root` is a source-defined morphological root string, including the literal `<unknown>` in the observed inventory. It is neither a lexical entry nor reviewed OntoLex decomposition.
6. Frequency, rank and lexeme-count metrics are source corpus statistics; `language`/`languageISO` are lexical-language metadata, and `nametype` is a source named-entity category. An ontology model may eventually represent these, but no equivalence follows from their feature names.
7. Syriac `lex` is a word-level lexical label. A repeated label could support a **reviewed constructed identity rule**, but lexical-entry identity has not been verified just from repeated strings.

## Chosen bounded output

A 27-row `research-proposal-only` ledger, each row binding exact source metadata description, applies-to node types, observed distinct count and feature value type to a denominator identity, lexical layer, assessment question and evidence-based per-item rationale. No `target`, `mapping_id`, review receipt or released coverage mutation is allowed. Separately-reviewed ontology and source-identity evidence is necessary before promotion. The batch is partitioned by corpus and uses no code or file touched by pending PR #339.

**Rejected:** map all strings as OntoLex Forms; label all glosses LexicalSenses; treat `lex0` as a universal entry ID; identify BHSA/Syriac entries by string equality; claim production `native-only` where an OntoLex representation property might eventually be defensible.

## Review challenges

Independent reviewer should falsify lexical scope (word versus lex node), distinguish form **representation** from Form **identity**, check duplicate descriptions and denominator drift, inspect gloss provenance, and challenge the tentative entry classification against R-008. A vetted 27-row batch is evidence preparation for promotion, **not** an increase in current P-004 production-reviewed counts.
