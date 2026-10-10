# I-027B3 research: pinned ExtraBiblical MQL POS evidence

**Issue:** #279 / parent #277, #274 and P-004 Workstream C #264.
**Source pin:** `ETCBC/extrabiblical@9a56288e6777bad6328856acf055c780e65dd5d9`.
**Artifact:** `source/0.2/extraBiblical.mql.bz2` — Git blob `4ba717b1716b747bb94d0359b950a55d8624b109`, compressed size 1,992,719 bytes.

## Research question

Does ExtraBiblical native `word.sp="verb"` denote the morphological/lexical part-of-speech class *verb*, suitable for a reviewed exact annotation-category projection to OLiA `Verb`?

The current pinned R-005 Text-Fabric inventory observes 6,100 `verb` records in the `sp` feature. R-011 calls this mapping exact at **research** authority only. Neither is sufficient to mint independent **production** ontology authority.

The pinned source repository does not include a human-readable `docs/features/sp.md`. The original MQL source is bzip2-compressed and cannot be read through the GitHub connector's UTF-8-only file fetch endpoint. The GitHub tree does expose an exact blob SHA and length. Avoid using BHSA or Syriac documentation as a substitute.

## Evidence acquisition decision

**GO** for reproducible, pinned source extraction through GitHub Actions:

1. Checkout *exact* `ETCBC/extrabiblical` commit into a separate read-only `upstream/` directory.
2. Verify the compressed bytes against the Git object blob SHA and committed file length before decompression.
3. Decode via Python's standard `bz2` module and identify context around `part_of_speech_t`, `sp`, and `verb` without printing or republishing the full source.
4. Emit a compact, deterministic evidence report with compressed/decompressed SHA256 hashes, UTF-8 integrity, relevant declaration excerpts and offsets.
5. Perform a **separate semantic review of the actual extracted declaration**. If the source does not clearly establish the native mapping, hold the production mapping; no source-code string matching is enough by itself.
6. Freeze only the approved short evidence (and its full-file digests) in a versioned corpus evidence record. Respect the source license and do not vendor the MQL blob.

This research phase is evidence acquisition and does not change runtime semantics, ontology locks, mappings, or production-accounted denominator rows.

## Later production release

After source verification, implement a separate immutable `extrabiblical/0.3.0` OLiA `Verb` profile with new mapping/projection review digests and a one-item coverage successor, preserving the 0.2.0 profile and current denominator. Do not infer tense, voice or Semitic verbal stems.

The source-extraction gate itself follows plan → TDD → implementation → exact-head CI → adversarial provenance review.
