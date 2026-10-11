# I-028E — BHSA lexical Form reverse-index: primary corpus and runtime evidence

**Issue:** #358; child of I-028 #265. **Prerequisite:** merged #354 source-bound read-only BHSA lexical entry→virtual Form projection. This is executable native-index capability, NOT new ontology mapping authority.

## Research from original pinned BHSA TF

- **Corpus:** `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da`. Frozen `tf/2021/otype.tf` Git blob `ecc4d0ecd388bd673d0aebfa8ab2a81508bec23c` assigns real source lex nodes **1437602–1446831**.
- `tf/2021/voc_lex_utf8.tf` original blob `d7fa9fde95d08a3fa05bcacbfaec43abfb688301` contains **9,230** complete lex-node vocalized values, but only **8,091 distinct strings**. Repeated written representations therefore cannot be lexical-entry/Form identifiers.
- The first *verified same-vocalization, different-lexeme* counterexample is **1437729** with `lex=>P/` and **1437796** with `lex=>P`; both have `voc_lex_utf8=אַף` in the pinned original. The `lex` source file Git blob is `234224440026af0b2da9ece3dbeebfbf8da9ad6c`. Both original text and discrete node IDs must survive inverse lookup.
- The same feature `voc_lex_utf8` is present on **426,590 word nodes** and **9,230 lex nodes**. A native inverse index `F.voc_lex_utf8.s(value)` can return token nodes as well as lexemes; a query must filter by actual `F.otype.v(node)==lex` and independently revalidate each lexical record using the existing source-bound `project_bhsa_lexical_form`.
- The existing `parse_bhsa_lexical_uri` only checks syntactic source-edition node IDs. A forged but syntactically valid URN is **not** an authenticated source entity. A TF-backed inverse resolver must re-run all source invariants before yielding a projection.
- The 2016 OntoLex core supplies `LexicalEntry`/`Form`/`lexicalForm`/`writtenRep` semantics, now pinned by merged PR #351. This ticket does **not** assert BHSA has native Form nodes or issue protected workflow attestation.

## Choice and rejected alternatives

**Implement:** 1) validated `resolve_bhsa_lexical_uri(api, uri, *, source_revision)` returning the *kind of the requested URI* and a verified `DerivedBHSAForm`; 2) `find_bhsa_lexical_forms(api, written_rep, *, source_revision)` using the source feature's inverse `.s` index, returning a deterministic tuple of distinct lex-node projections. All calls remain bounded to pinned BHSA, query only already-materialized TF data, and never substitute a string for a source ID.

**Reject:** splitting normalized texts by `lex0`; assuming a writtenRep is unique; scanning all 426k word nodes; returning token nodes as OntoLex entries; minting a versionless ID; returning only one hit; reconstructing an RDF triplestore; treating a plain URN parse or arbitrary caller-supplied revision as cryptographic source attestation.

## Negative cases

Missing/unusable index, invalid literal type, nonlex matches, duplicate index nodes, malformed/out-of-range IDs, alien revision, mismatched feature value between index and `.v`, missing source text/language and forged source URI. Return empty tuple only when there genuinely are no qualifying lex nodes; fail closed on inconsistent claimed lex entries. Independently review code against the original TF feature/value boundaries.
