# I-027B4 source-verified exact OLiA Verb for ExtraBiblical

**Implementation ticket:** #281 (under #279, #277, #274, #264 and P-004 #202).

## Reconciled source evidence

The exact original `ETCBC/extrabiblical@9a56288e6777bad6328856acf055c780e65dd5d9` source file `source/0.2/extraBiblical.mql.bz2` was extracted in CI #280, from blob `4ba717b1716b747bb94d0359b950a55d8624b109`.

- Compressed SHA256: `9b60ef03d18785257e80bc199acb7f348c20177b273e9c47b20a868ab7e07073`.
- Decompressed SHA256: `62540c8b4682121dd002f4c234c693259fb494c439ddfc06574537e5e398790e`.
- Lines 163/165: `CREATE ENUMERATION part_of_speech_t` contains `verb = 1`.
- Line 501: native feature `sp : part_of_speech_t`.
- Lines 269073/269212: actual `sp:=verb` assignments.
- Exact TF pin R-005 inventory: `sp` applies to `word`; value `verb` observed 6,100 times.
- Vendored OLiA `Verb`: `http://purl.org/olia/olia.owl#Verb`, OWL Class in exact OLiA lock `d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6`.

The native POS enum and value are **independently corroborated by original MQL**, not transferred by a spelling coincidence with BHSA or Syriac. Exact correspondence is limited to annotation-category membership, not to verbal stem, voice, tense or lemma/word equivalence.

The source extraction `docs/research/data/i027b3/extrabiblical-mql-pos-evidence.json` deliberately sets `exact_mapping_authorized=false`: it is *research provenance*, not a production mapping record. A new normalized `evidence:extrabiblical:word-sp-verb-source` record and a fresh reviewed mapping/projection with content-bound digests are required.

## Version / accounting boundary

- Historical `extrabiblical/0.1.0` and `0.2.0` resources must not change. Preserve their existing content-bound reviews.
- Write a new `0.3.0` profile, using existing `0.2.0` mapping content unchanged plus one new `word.sp="verb"` exact projection.
- The `0.3.0` profile uses the already-vendored OLiA `Verb` evidence and immutable `lock-linguistic-0.3.0.json`, without changing the prior lock.
- Preserve original parent component identity (source TF parent manifest).
- Publish an immutable `p004-i027b4-extrabiblical-verb-v1` successor: 136 existing semantic denominator rows; exactly one production delta at `node_value:sp="verb"`. Production reviewed 7→8, shared exact 7→8, unreviewed 129→128; no new gaps/exclusions.
- Keep research authority unchanged, never mass-promote R-011 dispositions.

## Research verdict

GO for this narrow positive class projection subject to the independent final code/data review and exact-head CI. Other morphological values require separate review; this is not full Workstream C coverage.
