# I-028D — BHSA lexeme→derived Form: direct TF primary-data research

**Issue:** #352, child of #265/P-004 #202. **Requires:** #348 semantic dispositions; #351 pinned OntoLex Core ontology evidence before formal publication.

## Pinned actual Text-Fabric primary data (not only feature descriptions)

Repository `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da` (BHSA 2021):
- `tf/2021/otype.tf`, blob `ecc4d0ecd388bd673d0aebfa8ab2a81508bec23c`: word nodes **1–426590** and lex nodes **1437602–1446831** (**9,230**).
- `tf/2021/voc_lex_utf8.tf`, blob `d7fa9fde95d08a3fa05bcacbfaec43abfb688301`: exactly **435,820 source feature values**, first 426,590 on word nodes, last 9,230 on lex nodes. The TF feature jumps to `1437602\tבְּ`; all 9,230 lexeme records have **nonempty** vocalized Hebrew-script representation.
- `tf/2021/languageISO.tf`, blob `fca3749ffdc8c281fe2dc40b9fe33ef68c50af93`: same 435,820 record count, languages in lex-node slice `hbo` and `arc`, no missing entry in this slice.
- `tf/2021/lex.tf`, blob `234224440026af0b2da9ece3dbeebfbf8da9ad6c`, and `tf/2021/lex0.tf`, blob `fa2e0ae11bdb7707f4a1c8d63cd3e5385d2de3a6`: each has 435,820 populated values, including all 9,230 lex nodes.
- Concrete homograph/collision: node **1437649** `lex=DC>[`, `lex0=DC>`, `voc_lex_utf8=דשׁא`, `languageISO=hbo`; node **1437650** `lex=DC>/`, `lex0=DC>`, `voc_lex_utf8=דֶּשֶׁא`, `languageISO=hbo`. Their `lex0` equality cannot merge their entry or derived Form identity.

Source parser check: each of the four lexical feature files has exactly 435,820 logical node values and a single explicit node jump to 1437602 after the word values. `otype.tf` independently establishes that lex node range. This is considerably stronger than matching R-005 unique counts.

## OntoLex formal model and judgment

OntoLex Core original `ontolex/ontolex@d6f840f...` OWL: `LexicalEntry` has at least one `lexicalForm` pointing to `Form`; `Form` has `writtenRep` of `rdf:langString`. `canonicalForm` is a stricter functional subproperty of `lexicalForm`.

**Derived, not native:** BHSA does not expose a TF `Form` node or `lexicalForm` edge. The 9,230 source lex nodes each have a source-attested vocalized lexical representation. A TFont **preview projection** can derive exactly one virtual `Form` identity per source lex-node ID, attached by `lexicalForm`, with `writtenRep` taken from `voc_lex_utf8`, language tag from `languageISO`. This is an explicit modelling decision, **not** an assertion that BHSA authors published OntoLex forms.

- Synthetic entry/Form IRIs must include immutable source revision and exact lex node ID, never text; preserve collisions and cross-edition distinctions.
- Distinguish language-tagged lexical representation from English gloss, token word form, and inferred sense/meaning. Do not make a `canonicalForm` assertion: lexeme vocalization is source lexical representation, not independently reviewed as a lexicographic canonical lemma Form.
- Fail closed for a nonlex node, out-of-range ID, missing/empty vocalized value, missing/unsupported language code, or wrong pinned source revision. Verify literal runtime TF `F.otype.v`, `F.voc_lex_utf8.v`, `F.languageISO.v`. Keep read-only and TF-native.
- Return a reversible syntactic identifier view, no profile registration, source download, on-disk RDF export, or author-created review authority. Runtime packaging proves actual executable behaviour but **not a production mapping release**.

**Rejected:** identity by shared `lex0` (real collision), identity by shared vocalized spelling, treating TF word nodes as lexical entries, emitting `canonicalForm`, exposing an independently published ontology mapping from unreviewed runtime convenience code.
