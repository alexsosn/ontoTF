# I-034F — ExtraBiblical's eleven unmapped native POS values → OLiA

**Issue:** #283 / #264 (real production coverage). Base `551788625a28703610585b2dea666047590014f9`.

## Primary evidence and the decisive missing fact

The **actual** ETCBC ExtraBiblical TF `0.2` inventory at `ETCBC/extrabiblical@9a56288e6777bad6328856acf055c780e65dd5d9`, `docs/research/data/generated/r005/extrabiblical.json`, reports precisely **39,862 words with `sp`** and 14 values: adjv=969, advb=1201, art=1746, conj=5219, inrg=87, intj=83, nega=509, nmpr=723, prde=173, prep=6255, prin=197, prps=4375, subs=12225, verb=6100. Only `nmpr`, `subs`, `verb` are currently active OLiA POS selectors in the immutable ExtraBiblical `0.3.0` release (installed package). **Eleven native POS classes remain.**

Unlike BHSA, ExtraBiblical **does not publish a readable `sp.md` vocabulary**. The original MQL `source/0.2/extraBiblical.mql.bz2` is a compressed 41MB text encoded as a 2MB Git blob `4ba717b1716b747bb94d0359b950a55d8624b109`; its actual bytes have been verified in [Actions run 38039463508](https://github.com/alexsosn/ontoTF/actions/runs/38039463508) and frozen research `docs/research/data/i027b3/extrabiblical-mql-pos-evidence.json`:
- source SHA `9a56288e6777bad6328856acf055c780e65dd5d9`,
- compressed SHA256 `9b60ef03d18785257e80bc199acb7f348c20177b273e9c47b20a868ab7e07073`,
- decompressed SHA256 `62540c8b4682121dd002f4c234c693259fb494c439ddfc06574537e5e398790e`,
- MQL `part_of_speech_t` declared at line 163, `verb = 1,` at line 165, `sp : part_of_speech_t;` at line 501.

The [successful original-source verifier run 38039463508](https://github.com/alexsosn/ontoTF/actions/runs/38039463508), job 114176641170, also exposes the *original neighboring declaration*: `CREATE ENUMERATION part_of_speech_t = {` at line 163, **`art = 0,` at line 164**, `verb = 1,` at line 165 and `subs = 2,` at line 166. Zero is a legitimate original enum discriminant; source parsers and candidate checks must accept nonnegative integers and may not treat `0` as “missing”. This is a partial original-source fact, **not** proof of the remaining ten unobserved codes or all eleven semantic correspondences.

The existing extractor `scripts/research/i027b3_extract_mql.py` only captured `verb`. **Do not invent line numbers or POS classes by borrowing the BHSA document**, even though ExtraBiblical shares ETCBC heritage. Before projecting these eleven categories we must inspect the **entire original `CREATE ENUMERATION part_of_speech_t`**: exact identifiers, discriminants and one-based declaration lines, and bind them to the already pinned original MQL bytes and independently observed TF domain.

## OLiA choices (only after source validation)

The vendored immutable OLiA source `acoli-repo/olia@d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/owl/core/olia.owl` already locks the classes in `lock-linguistic-i034a-pos.json` added for BHSA/Syriac and backed by one RDF evidence file for each. Candidate source-code values likely support direct class projections for adjv=Adjective, advb=Adverb, art=Article, conj=Conjunction, intj=Interjection, prde=DemonstrativePronoun, prep=Preposition, prin=InterrogativePronoun; **only where the original enum source actually supports their semantics**. Even if `inrg`, `nega`, `prps` appear as source enum values, a source enum alone may not distinguish particles from broad interrogatives/negatives or personal pronouns from the narrower OLiA `PersonalPronoun` (which defines irreflexivity). Keep unresolved statuses rather than overclaim.

ExtraBiblical `README.md` explicitly refers to BHSA family feature documentation, but that is *supporting interpretation*, not a replacement for direct MQL source review. The R005 TF observed frequencies prove that category values occur in the actual pinned converted Text-Fabric corpus; they do not themselves prove RDF semantic equivalence.

## Immediate experiment and release intent

Reuse the **existing, read-only, no-secret** `i027b3-extrabiblical-source.yml` source-validation workflow, which checks out exact pinned upstream Git revision and runs `i027b3_extract_mql.py`. Extend the deterministic offline extractor to return a bounded 14-value declaration-only record with code and actual source line; test parser with malicious/truncated fixtures **before implementation**, then run it on real pinned original 2MB source under GitHub CI. Do not vendor the MQL data (upstream repository CC-BY-NC-4.0). The resulting original-source proof must precede exact mappings and dedicated candidate evidence.

After extracting and verifying, commit **one** data-first corpus POS candidate batch for eleven native selectors, using already vetted OLiA target locks and source evidence, a logically independent skeptical mapping review, and a single batch PR/release path. Do not open eleven per-entity issues, duplicate old mappings, or spend time on generic release tooling. New installed OLiA mappings count stays zero until installed release verification.


## Completed original enumeration research (2026-10-12)

The pinned ETCBC repository was checked out at `9a56288e6777bad6328856acf055c780e65dd5d9`; the compressed Git blob was verified against `4ba717b1716b747bb94d0359b950a55d8624b109` *before* listing the following declaration-only metadata. The [original-source job 114784826913](https://github.com/alexsosn/ontoTF/actions/runs/38241464739) completed successfully with the corrected multiline MQL header parser. Independent source diagnostic output from [job 114783210754](https://github.com/alexsosn/ontoTF/actions/runs/38240977724) enumerated all fourteen values:

| MQL line | Value | Integer code | Planned disposition |
| ---: | --- | ---: | --- |
| 164 | `art` | 0 | Proposed exact OLiA Article |
| 165 | `verb` | 1 | Already installed in 0.3.0 |
| 166 | `subs` | 2 | Already installed in 0.3.0 |
| 167 | `nmpr` | 3 | Already installed in 0.3.0 |
| 168 | `advb` | 4 | Proposed exact OLiA Adverb |
| 169 | `prep` | 5 | Proposed exact OLiA Preposition |
| 170 | `conj` | 6 | Proposed exact OLiA Conjunction |
| 171 | `prps` | 7 | Native-only (OLiA irreflexivity not proved) |
| 172 | `prde` | 8 | Proposed exact OLiA DemonstrativePronoun |
| 173 | `prin` | 9 | Proposed exact OLiA InterrogativePronoun |
| 174 | `intj` | 10 | Proposed exact OLiA Interjection |
| 175 | `nega` | 11 | Native-only (particle subtype not proved) |
| 176 | `inrg` | 12 | Native-only (particle subtype not proved) |
| 177 | `adjv` | 13 | Proposed exact OLiA Adjective |

The original enum header is line 163 and the `word.sp : part_of_speech_t` feature's declaration is line 501. The corresponding 14 TF observed-value frequencies sum to **39,862** words. These are **value declaration coordinates**, not MQL corpus-example token references. A zero-valued `art` is a legitimate enumerator, not a null/missing value.

**Independent category interpretation:** The pinned BHSA family `docs/features/sp.md` directly supplies ETCBC glosses for these same fourteen codes, and ExtraBiblical's pinned README explicitly identifies the corpus as part of the BHSA family with BHSA as its core feature documentation. That family relationship supports, but cannot by itself prove, the OLiA equivalence of every ExtraBiblical token. The pinned RDF class identities are independently backed by the installed 19-term OLiA lock. The eight mappings are therefore **proposal-only** until reviewed per-row and formally published; the three conservative native-only cases remain without shared targets.

The machine-verifiable minimal record is `docs/research/data/i034f/extrabiblical-mql-pos-enum.json` (14 original category values/codes/lines) and the digest-bound candidate native source evidence is `docs/research/data/batch_review/evidence/i034f-extrabiblical-pos.json`. Neither metadata file redistributes original 41 MB MQL corpus content.
