# I-027C1 — native POS evidence matrix

**Ticket:** #284, child of #283 / OLiA Workstream C #264 / P-004 #202.

## Question

How can ontoTF review the remaining POS values without copying semantic authority from a similarly named code in another corpus?

**Answer:** mechanically extract the *native source declarations* from each exact upstream revision, reconcile every source code against the pinned Text-Fabric R-005 `word.sp` inventory, and publish one stable review row per (corpus, native POS code). **Do not infer an OLiA mapping from any of these rows**. A future POS mapping reviewer must consult the candidate ontology class and native semantics separately.

## Evidence pins

1. BHSA `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da`, `docs/features/sp.md`, explicitly lists 14 `code | description` entries, and the source notes that `sp` also occurs on `lex` nodes. For this work, only `word.sp` semantics are being compared.
2. Syriac native grammar `ETCBC/linksyr@3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6`, `data/lib/syriac/word_grammar`, defines `sp: "part of speech"` with 10 explicitly glossed values. Its target TF corpus revision, **a separate identity**, is `ETCBC/syriac@bb0eaa7e21b020a26b7566d2e495da9b1f84a919`.
3. ExtraBiblical `ETCBC/extrabiblical@9a56288e6777bad6328856acf055c780e65dd5d9`, `source/0.2/extraBiblical.mql.bz2`, compressed Git blob `4ba717b1716b747bb94d0359b950a55d8624b109`, 1,992,719 bytes. Reproducibly decoded evidence in merged #280: `CREATE ENUMERATION part_of_speech_t` (line 163), `verb = 1` (165), `sp : part_of_speech_t` (501), with real `sp:=verb` assignments. The original MQL enum provides **numeric IDs, not an English definition for every category**: record `enum-only` instead of forging glosses.
4. Existing inventories `docs/research/data/generated/r005/{bhsa,syriac,extrabiblical}.json`. They count feature observations, not necessarily word-only token counts if `sp` also applies to lexeme nodes.

## Known review hazards

- BHSA `prps/prde/prin` versus Syriac `pron` are different native classifications: overlap is not identity.
- BHSA `sp=verb` and ExtraBiblical `sp=verb` have independent source authority. Syriac native grammar defines another independently reviewed category.
- ExtraBiblical source MQL `part_of_speech_t` names (e.g. `prep`) may *suggest* meanings but MQL enum alone does not justify a gloss. Match to OLiA only after further linguistic/source review.
- Native `sp` differs from `pdp` (phrase-dependent POS) and `vs` (verbal stem). None of these fields are interchangeable.

## Deliverable and semantic gate

An offline generator and frozen source-backed matrix with one row per corpus/value, observed TF frequency, source revision/path/line, and an explicit `source_definition_kind` distinguishing `explicit-gloss` from `enum-only`. No source corpus files are redistributed. All 38 currently observed rows must be accounted for; errors fail closed rather than silently skipping a row.

Only after this evidence matrix has independent review may #283 publish additional `exact/close/.../native-only` dispositions. **The matrix itself grants no production authority.**
