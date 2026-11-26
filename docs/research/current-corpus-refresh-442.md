# Refresh current corpus inventories (issue #442)

## Research and plan

The user needs coverage measurements and queries against current released data. 
As of 2026-11-26, the current catalog uses CUC 0.2.8, Syriac 0.9 and Pseudepigrapha TF 1.0. 
The latest data are 0.4.0, 0.92 and 1.1 respectively.

- [CUC 0.4.0 release](https://github.com/DT-UCPH/cuc/blob/81e20d7b164f31eb5135a265cb679d45facd39b2/docs/release-0.4.0.md) and [0.3.0 release](https://github.com/DT-UCPH/cuc/blob/81e20d7b164f31eb5135a265cb679d45facd39b2/docs/release-0.3.0.md): 279 to 453 tablets, new boundary and alias node types, changed language attribution, explicit sign/word type, surface replaces side, RIH metadata. No node-ID reuse or unqualified selector migration. Old sign guards may now include differently typed source units; review actual roles. Include newly documented categorical feature families in scoped census.
- [Syriac 0.92](https://github.com/ETCBC/syriac/tree/0b6ded2b369c7d81589a98c92325290e24b20af6/tf/0.92): TF file listing at pinned revisions shows all 34 old TF files changed and a new g_word feature. Upstream documentation describes merged split verses and new text material. Compare actual feature scopes and domains; review source meanings, not just label presence.
- [Pseudepigrapha v1.1.0](https://github.com/alexsosn/Pseudepigrapha-TF/releases/tag/v1.1.0): TF 1.1 has unchanged node totals but eight altered manuscript/metadata features; pinned archive SHA-256 88f23ac9106c6ea8b35f89b19d760cf5d4ee544a3f8d8262d6ed7e2092e447e9 is published in GitHub asset metadata. Separate corpus data version from converter release tag.

## Acceptance and sequence

1. Reuse scoped R-005 workflow and real pinned TF artifacts. Assert release-specific known data facts; keep historical R-005 census and historical mapping versions intact.
2. Compare generated artifacts against existing scoped evidence. Review existing maps, including active PRs #437 and #439, against new source meanings and observed scopes. Do not copy native-only or positive rows automatically. New mappings explicitly version scoped; old mappings remain available.
3. Reconcile applicability rules and new measured denominators with the current catalog, then refresh dashboard version evidence. Verify queries on loaded data and regressions in historical version support.
4. Adversarial review on final diff and successful exact-head CI before merge. Until the migration is validated, published coverage remains on the older version.

This draft starts with evidence generation only. It must not be merged as a migration while the catalog and committed current census still name the old data.

## Follow-up evidence from successful loaded-data census

CUC PR [#47](https://github.com/DT-UCPH/cuc/pull/47) changes TF 0.4.0 in place. Its candidate head 64c188da6d2dad0f2960769c40953994900e4571 has 177132 signs, 33012 words, 456 tablets, 1417 boundaries and 3 aliases. Keep current CUC 0.2.8 in the migration workflow until the upstream PR is merged and pinned. Do not mix the earlier 0.4.0 build's counts with that candidate.

The actual Syriac 0.92 loaded census (job 140013842855, run 45850080114) has 407319 words, 31 books, 807 chapters, 18132 verses. All selected finite observed grammatical and lexical-set domains retain the previous value sets. Unicode surfaces exist on 406610 words. The new g_word is an explicitly pointed ETCBC transcription, not a lemma or morphosyntactic category. The old 0.9 research census remains historical.

Pseudepigrapha TF 1.1 (job 140013843107, same run) preserves the node totals and every observed edge scope; exactly eight feature scopes change: bibliography, bibliography_xml, manuscript_index, ms_language, ms_name, ms_name_xml, ms_show, undefined_manuscript. The selected undefined_manuscript count changes 29→26 (actual scoped census; distinct from release prose's 30→27). Source files for the existing maps (graph.py and seven feature/architecture documents) are byte-identical across release commits. No changed selector semantics identified in those sources. Word anchors remain 2462; 920460 surface-bearing primary words and 7701 variant words; 231 book-level translation edges. This justifies version-scoped migration of reviewed selectors after tests, not identity of manuscript metadata.

PR #439 merged at 01986020af62247aab4cd1c1640b0c760c880203; migration must include its reviewed book and apparatus maps. New source versions require explicit version arguments when a selector has multiple version dispositions (existing MappingCatalog behavior). Regression tests must exercise both historical and new versions and reject unknown versions. No runtime redesign is needed.

### Additional acceptance check before migrating qualified Syriac categories

A complete value domain does not establish that the cross-feature linguistic predicates still hold. Re-run the eight prior ls→sp/lex/gloss joins on the loaded 0.92 corpus using the same scoped census workflow. Assert the eight uniform POS sets and the two exact lexical-label sets for quotation/existential categories. Inspect the printed lexeme and gloss distributions before transferring the qualified mappings. Do not copy previous counts into 0.92 evidence notes. The public API must keep version mismatch checks and require explicit source_version/corpus_version where a selector has multiple versions.

### Migration implementation

Syriac 0.92 lexical review passed in job 140018970413: cjad 1461 advb (four lexemes), demo 4537 pron (including 10 XDD>), gntl 1369 adjv (124 lexemes), pers 8489 pron (12 lexemes), pinr 20 advb (one lexeme), prin 2229 pron (six lexemes), quot 4818 verb (>MR), vbex 5154 verb (HWJ). All previous qualified relations remain qualified; no new exact inference. The new data has 709 word nodes without Unicode surface text. Version-scoped rows retain the historical evidence and update current counts. The current applicability and source status are updated together with the actual census. CUC remains on 0.2.8 until upstream #47 merges.
