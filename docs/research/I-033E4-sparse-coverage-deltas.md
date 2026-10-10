# I-033E4 — sparse *already published* coverage release parity

**Issue:** #306 (child #303 / #300 / #290).

## Code/data findings

Historical immutable manifests under `src/tfont/resources/coverage` copy complete denominator accounting documents to publish one or two additional POS reviewed decisions. Meanwhile `src/tfont/published_deltas.py` already proves **mapping-release** parity on installed historical sources but explicitly does not authorize unreviewed proposals. The missing complementary operation is a **sparse coverage diff** that references an installed source snapshot and adds only genuinely new production accounting on existing semantic item IDs.

Reviewed source families to use as real evidence:
- BHSA `p004-i027a-bhsa-stems-v1` → `p004-i027b1-bhsa-verb-v1`: 27 `native-only` morphological stem decisions retained and one new `sp=verb` exact pivot.
- BHSA `p004-i027b1-bhsa-verb-v1` → `p004-i027c2-bhsa-adj-adv-v1`: 2 new exact class pivots; no regression to earlier stem decisions.
- Syriac `p004-i027b2-syriac-verb-v1` → `p004-i027c2-syriac-adj-adv-v1`: 2 new exact class pivots, preserve `ls="prop"` outside-denominator gap.
- ExtraBiblical `p004-r011-baseline-v1` → `p004-i027b4-extrabiblical-verb-v1`: 1 new source-reviewed `Verb`, 136 semantic denominator identities unchanged.

## Trust model

`load_packaged_coverage_manifest` validates installed, explicitly named source resources. An ordinary JSON proposal, report or `status=reviewed` field is **not** an authenticated external review. The composer can only prove equality to two independently packaged historical releases, so `authority="published-registry-parity-only"`. It must not be surfaced as a publish credential. Future protected #303 pipeline will use **a different, separately verified** external-review data path.

## Invariants

- Existing item IDs/kinds/metadata and research layer stay unchanged.
- Corpus identity, source revision, denominator digest and basis, scope, gaps and exclusions stay unchanged.
- Previously reviewed production objects are immutable (including audit-only source and review fields).
- Every changed item goes `production:null → production:reviewed`; never replace/drop/escalate an old disposition. Empty or massive unexplained changes fail.
- Compact output includes only new full production records, exact source/target JCS SHA256 identities and manifest resource names. Recompose in memory from immutable base and assert exact equality with packaged target under strict validation.
- No per-mapping generated Python file, workflow, profile or copied denominator manifest.
