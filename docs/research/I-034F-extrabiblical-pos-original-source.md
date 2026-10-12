# I-034F — ExtraBiblical's eleven unmapped native POS values → OLiA

**Issue:** #283 / #264 (real production coverage). Base `551788625a28703610585b2dea666047590014f9`.

## Primary evidence and the decisive missing fact

The **actual** ETCBC ExtraBiblical TF `0.2` inventory at `ETCBC/extrabiblical@9a56288e6777bad6328856acf055c780e65dd5d9`, `docs/research/data/generated/r005/extrabiblical.json`, reports precisely **39,862 words with `sp`** and 14 values: adjv=969, advb=1201, art=1746, conj=5219, inrg=87, intj=83, nega=509, nmpr=723, prde=173, prep=6255, prin=197, prps=4375, subs=12225, verb=6100. Only `nmpr`, `subs`, `verb` are currently active OLiA POS selectors in the immutable ExtraBiblical `0.3.0` release (installed package). **Eleven native POS classes remain.**

Unlike BHSA, ExtraBiblical **does not publish a readable `sp.md` vocabulary**. The original MQL `source/0.2/extraBiblical.mql.bz2` is a compressed 41MB text encoded as a 2MB Git blob `4ba717b1716b747bb94d0359b950a55d8624b109`; its actual bytes have been verified in [Actions run 38039463508](https://github.com/alexsosn/ontoTF/actions/runs/38039463508) and frozen research `docs/research/data/i027b3/extrabiblical-mql-pos-evidence.json`:
- source SHA `9a56288e6777bad6328856acf055c780e65dd5d9`,
- compressed SHA256 `9b60ef03d18785257e80bc199acb7f348c20177b273e9c47b20a868ab7e07073`,
- decompressed SHA256 `62540c8b4682121dd002f4c234c693259fb494c439ddfc06574537e5e398790e`,
- MQL `part_of_speech_t` declared at line 163, `verb = 1,` at line 165, `sp : part_of_speech_t;` at line 501.

The existing extractor `scripts/research/i027b3_extract_mql.py` only captured `verb`. **Do not invent line numbers or POS classes by borrowing the BHSA document**, even though ExtraBiblical shares ETCBC heritage. Before projecting these eleven categories we must inspect the **entire original `CREATE ENUMERATION part_of_speech_t`**: exact identifiers, discriminants and one-based declaration lines, and bind them to the already pinned original MQL bytes and independently observed TF domain.

## OLiA choices (only after source validation)

The vendored immutable OLiA source `acoli-repo/olia@d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/owl/core/olia.owl` already locks the classes in `lock-linguistic-i034a-pos.json` added for BHSA/Syriac and backed by one RDF evidence file for each. Candidate source-code values likely support direct class projections for adjv=Adjective, advb=Adverb, art=Article, conj=Conjunction, intj=Interjection, prde=DemonstrativePronoun, prep=Preposition, prin=InterrogativePronoun; **only where the original enum source actually supports their semantics**. Even if `inrg`, `nega`, `prps` appear as source enum values, a source enum alone may not distinguish particles from broad interrogatives/negatives or personal pronouns from the narrower OLiA `PersonalPronoun` (which defines irreflexivity). Keep unresolved statuses rather than overclaim.

ExtraBiblical `README.md` explicitly refers to BHSA family feature documentation, but that is *supporting interpretation*, not a replacement for direct MQL source review. The R005 TF observed frequencies prove that category values occur in the actual pinned converted Text-Fabric corpus; they do not themselves prove RDF semantic equivalence.

## Immediate experiment and release intent

Reuse the **existing, read-only, no-secret** `i027b3-extrabiblical-source.yml` source-validation workflow, which checks out exact pinned upstream Git revision and runs `i027b3_extract_mql.py`. Extend the deterministic offline extractor to return a bounded 14-value declaration-only record with code and actual source line; test parser with malicious/truncated fixtures **before implementation**, then run it on real pinned original 2MB source under GitHub CI. Do not vendor the MQL data (upstream repository CC-BY-NC-4.0). The resulting original-source proof must precede exact mappings and dedicated candidate evidence.

After extracting and verifying, commit **one** data-first corpus POS candidate batch for eleven native selectors, using already vetted OLiA target locks and source evidence, a logically independent skeptical mapping review, and a single batch PR/release path. Do not open eleven per-entity issues, duplicate old mappings, or spend time on generic release tooling. New installed OLiA mappings count stays zero until installed release verification.
