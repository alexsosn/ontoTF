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
