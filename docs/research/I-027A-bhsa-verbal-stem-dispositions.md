# I-027A research — BHSA verbal-stem production accounting

**Issue:** #272 (child of I-027 #264 / P-004 #202)  
**Baseline:** `main` `2dafb9573ec5eaeb7a677b47340bd3066530e2f8`  
**Status:** source reconciliation completed; mapping authority deliberately not promoted

## Question

Can the BHSA verbal-stem (`word.vs`) family receive a production-reviewed **native-only** disposition without inventing an exact OLiA equivalent for Qal, Piel, Hiphil, Hitpael, etc.?

**Yes, as a versioned accounting successor to the existing coverage manifest.** This is an explicit decision not to assert a common ontology target at the current profile revision, not a claim that deeper semantic decomposition could never support future mappings.

## Pinned evidence

- Corpus: `ETCBC/bhsa` at `4db00e2157915495e1a4d3d57e41223df24775da`, TF version `2021`.
- Machine inventory: `docs/research/data/generated/r005/bhsa.json`, especially `/node_features/vs`.
- Denominator: `src/tfont/resources/coverage/p004-r011-baseline-v1/bhsa.json`, SHA-256/JCS denominator digest `sha256:0b260e21a1ebdb771f3d9975cb3e7b2560261dd99d9bd14d0eeabbb566852a03`.
- Routing: `docs/research/data/generated/i026/p004-work-queue.json` (merged #271); 149 BHSA items belong to C, including all 27 `vs` family rows.
- Historical R-011 pilot mapping `bhsa-verbal-stem` has `native-only` research authority; it is used as a hypothesis to re-evaluate, never as production authority.
- Current OLiA snapshot lock: `olia-reference-model` at source revision `d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6`.

The source inventory describes `vs` as *verbal stem* and records the exact 26 values:

`NA, afel, etpa, etpe, haf, hif, hit, hof, hotp, hsht, htpa, htpe, htpo, nif, nit, pael, pasq, peal, peil, piel, poal, poel, pual, qal, shaf, tif`.

These are observed on `word` nodes with 426,590 records. The largest codes include `NA` (352,880), `qal` (50,205), `hif` (9,407), `piel` (6,811), `nif` (4,145). The denominator already explicitly treats `vs` as a bounded semantic value family; **I-027A is not deriving closedness merely from the finite snapshot**.

## Semantic assessment

1. The native feature records a Hebrew/Aramaic verbal stem classification; individual codes have language-specific analysis and are meaningful in their corpus.
2. Similar traditional labels across Semitic languages do **not** establish one exact cross-language OLiA class. A causative-like stem also cannot be substituted blindly for a generic causative voice, aspect, or derivation.
3. The locked production OLiA profile `0.2.0` has reviewed noun/POS/gender/number projections. It contains no reviewed `vs` projection or stem-specific native binding.
4. The `NA` code is a corpus-native lack-of-applicable-stem marker; it is retained as native-only **accounting** in this first review. It never authorizes a positive OLiA stem query or active capability in isolation.
5. All 27 rows can therefore be reviewed as `native-only` for this release, with `common_target=false`. No new OLiA mapping or query substitution is authorized.

Potential later decomposition into voice, valency, reflexivity, derivation, etc. requires category-by-category evidence and another reviewed profile release.

## Accounting boundary

- Starting manifest: 219 semantic items; 7 production-reviewed, 34 research-reviewed; no accounting gaps.
- Selected delta: exactly `node_feature:vs` plus 26 `node_value:vs=...` rows. Each currently has research-only `native-only`, none production.
- Result: 34 production-reviewed; 185 remaining unreviewed across BHSA, of which 115 of 149 BHSA Workstream-C items remain unreviewed (7 previous + 27 new).
- Research accounting must stay byte-for-byte unchanged on all rows.
- Denominator/source identity must not change, including technical exclusions and the canonical denominator digest.
- The new manifest receives its own immutable `manifest_id` and resource directory. The historical baseline remains unchanged.

## Alternatives rejected

- Copy R-011 research assessments into production without source review: **reject**; forbidden authority promotion.
- Add fabricated OLiA mappings for Qal/Hiphil/Piel by matching labels to generic Voice/Verb classes: **reject**; semantic equivalence unproven.
- Delete `NA` from the denominator for cleaner metrics: **reject**; historical bounded denominator would silently change.
- Edit the packaged historical coverage manifest in place: **reject**; release history must remain reproducible.
- Treat production `native-only` as a promise that no future OLiA decomposition is possible: **reject**.

## Decision

GO for a **bounded I-027A coverage accounting successor**, with explicit evidence, deterministic building, TDD, and independent semantic review. No runtime/ontology release mutation.
