# R-005: empirical semantic census of target Text-Fabric corpora

**Status:** research complete; implementation intentionally out of scope  
**Issue:** #5  
**Recorded:** 2026-09-05

## Recommendation

The POC must treat corpus semantics as versioned profiles over a small common structural vocabulary, not as one BHSA-shaped universal schema. The inspected corpora already require at least three distinct modelling regimes:

1. **word-slot linguistic corpora** — BHSA, `extrabiblical`, the ETCBC Syriac corpora and Pseudepigrapha-TF;
2. **sign-slot epigraphic/cuneiform corpora** — CUC, TLHdig-TF and the ORACC-TF target;
3. **non-textual or zero-span entities** — lexical anchors, witnesses, apparatus metadata, source anomalies, editorial events, catalogue records and ORACC zero-span entities whose Text-Fabric `oslots` are technical anchors or which must live outside the TF warp.

A later ontology mapping may share concepts such as `Word`, `LexicalEntry`, `Line`, `Witness`, `Gender` or `Damage`, but the mapping layer has to record relationship strength and native semantics. Identical feature names are not sufficient evidence of identity. The census found concrete counterexamples:

- BHSA `lex` nodes use corpus-wide occurrence extent, while TLHdig-TF `lex` nodes use a technical one-slot anchor and explicit `analysis -> lex` attestations.
- ORACC `c type=sentence` objects are all implicit source chunks and can contain thousands of words; mapping them to BHSA linguistic `sentence` would be false.
- Peshitta `witness=A/B`, TLHdig-TF line-to-fragment `witness`, and Pseudepigrapha-TF reading-to-manuscript `witness` all concern textual witnesses but have different domains and assertions.
- CUC `emen`/`cert`/`alt`, TLHdig-TF `cluster` ranges and ORACC `damage`/`missing` represent related editorial/material states with different granularity and evidence models.
- word-level verbal categories in Hebrew and Syriac are comparable only at selected abstract levels; values such as BHSA `qal` and SyrNT `peal` are language-specific conjugation systems, not aliases.

The POC should therefore expose **native facts first**, optional semantic projections second, and explicit `same | close | broader/narrower | related | unknown | local-only` mapping strength. No cross-corpus query should silently manufacture a feature, relation, span, witness state or alignment that the source corpus does not assert.

## 1. Method and reproducibility

This census inspected corpus data, generated TF feature files, generated census reports, converter contracts and feature documentation at exact Git commits. Repository front pages were used only as supplementary explanation. The reproducible pins are also recorded in [`data/R-005-corpus-pins.json`](data/R-005-corpus-pins.json).

For every released minimum corpus, `scripts/research/r005_inventory.py` loads the exact pinned TF artifact and preserves an exhaustive non-warp node/edge feature inventory under `docs/research/data/generated/r005/`. Those JSON artifacts record feature metadata/value types, empirical node-type applicability, observed non-empty domains or large-domain samples/cardinalities, edge direction/value status, corpus pins, and a deterministic digest over the inspected TF files. Dense empty-string/`None` records are counted diagnostically but are not semantic domain members or applicability evidence.

| corpus | repository | commit inspected | TF/schema version | slot type |
|---|---|---|---|---|
| BHSA | `ETCBC/bhsa` | `4db00e2157915495e1a4d3d57e41223df24775da` | `2021` | `word` |
| CUC | `DT-UCPH/cuc` | `ad69400f5446e1c8217af01659c7c10ab00c015b` | `0.2.8` | `sign` |
| Syriac | `ETCBC/syriac` | `bb0eaa7e21b020a26b7566d2e495da9b1f84a919` | `0.9` | `word` |
| Peshitta | `ETCBC/peshitta` | `9850f5addade26f681334aa475570bef9b0b440a` | `0.2` | `word` |
| SyrNT | `ETCBC/syrnt` | `dae3eb6ff62b9b272fb503646796c25d248175ce` | `0.1` | `word` |
| Extra-biblical | `ETCBC/extrabiblical` | `9a56288e6777bad6328856acf055c780e65dd5d9` | `0.2` | `word` |
| TLHdig-TF | `alexsosn/TLHdig-TF` | `4309cf3318c682282c1480b233786362a3083471` | TF `0.2.0`, upstream `0.3` | `sign` |
| Pseudepigrapha-TF | `alexsosn/Pseudepigrapha-TF` | `d098845043897957efee7a42ae4854deddd5a1bd` | converter output contract `0.1`; upstream pin `2d1d14d23434a784d377ff7f4409ccdb2d18aafb` | `word` |
| ORACC-TF stress target | `alexsosn/ORACC-TF` | `ab92001191844b1b0ee656490f0b5c8a66e65b4a` | current P-001 implementation schema | `sign` |

### Evidence hierarchy

For released/committed TF datasets the strongest evidence is `otype.tf`, `otext.tf`, feature-file metadata and generated corpus reports. For converters that intentionally do not commit generated data, the census uses the pinned converter contract, source-data measurements and parity/validation specifications. ORACC-TF is still an implementation target rather than a released TF corpus, so its findings below are labelled as **measured target schema**, not as a released ontology promise.

Datatype below means the TF feature datatype where known. Most TF node features are `str`; integer-valued flags/counts are called out explicitly. Edge features are unvalued unless stated otherwise.

## 2. Corpus inventories

### 2.1 ETCBC/BHSA 2021

#### Structure and counts

`word` is the slot type. `otype.tf` gives:

| node type | count | semantic role |
|---|---:|---|
| `word` | 426,590 | token/slot |
| `book` | 39 | section |
| `chapter` | 929 | section |
| `verse` | 23,213 | section |
| `half_verse` | 45,179 | masoretic/textual division |
| `sentence` | 63,717 | functional linguistic object |
| `sentence_atom` | 64,514 | continuous distributional atom |
| `clause` | 88,131 | functional clause |
| `clause_atom` | 90,704 | continuous clause atom |
| `phrase` | 253,203 | functional phrase |
| `phrase_atom` | 267,532 | continuous phrase atom |
| `subphrase` | 113,850 | subphrase structure |
| `lex` | 9,230 | lexical entity |

Sections are `book / chapter / verse`. BHSA supplies several text formats based on consonantal, pointed/transliterated and Unicode orthographies through the `g_*`, `qere*` and `trailer*` features.

#### Node features

The maintained BHSA feature reference groups the important native features as follows.

| domain | features | type / bounded values | applies mainly to |
|---|---|---|---|
| orthography | `g_cons`, `g_cons_utf8`, `g_word`, `g_word_utf8`, `trailer`, `trailer_utf8` | string/open | `word` |
| qere | `qere`, `qere_utf8`, `qere_trailer`, `qere_trailer_utf8` | string/open; absent when no qere | `word` |
| lexical identity | `lex`, `lex_utf8`, `g_lex`, `g_lex_utf8`, `language`, `languageISO`, `sp`, `pdp`, `ls` | strings; `sp`/`pdp` categorical | `word` |
| lexeme node | `lex`, `voc_lex`, `voc_lex_utf8`, `sp`, `ls`, `nametype`, `gloss`, `language`, `languageISO` | strings/categorical | `lex` |
| gender | `gn`, `prs_gn` | documented `m`, `f`, `NA`, `unknown` | `word` |
| number | `nu`, `prs_nu` | documented `sg`, `du`, `pl`, `NA`, `unknown` | `word` |
| person | `ps`, `prs_ps` | documented `p1`, `p2`, `p3`, `NA`, `unknown` | `word` |
| state | `st` | documented `a`, `c`, `e`; observed native `NA` also present | `word` |
| verbal stem | `vs` | Hebrew stem inventory (`qal`, `piel`, `nif`, `hif`, etc.) | verbal `word` |
| verbal tense/type | `vt` | BHSA inventory including `perf`, `impf`, `wayq`, etc. | verbal `word` |
| morphemes | `nme`, `g_nme`, `pfm`, `g_pfm`, `prs`, `g_prs`, `uvf`, `g_uvf`, `vbe`, `g_vbe`, `vbs`, `g_vbs` | string/categorical | `word` |
| clause analysis | `typ`, `kind`, `rela`, `domain`, `txt`, `code`, `is_root`, `tab`, `pargr`, `instruction` | mixed categorical/string/int | clause/atoms |
| phrase analysis | `typ`, `rela`, `function`, `det` | categorical/string | phrase/atoms |
| generic structural | `number`, `dist`, `dist_unit`, `mother_object_type`, `label` | int/string/categorical | several non-slot types |

The exact categorical domains are corpus-native. In particular, BHSA `NA` and `unknown` are native non-empty values where the pinned feature metadata documents them; they are not storage empties. A documented domain may be wider than the observed release subset: for example, `prs_nu` documents `sg/du/pl/NA/unknown` while the pinned 2021 artifact observes only `sg/pl/NA`, and `prs_ps` documents `p1/p2/p3/NA/unknown` while this release observes `p1/p2/p3/NA`. Conversely, `st` observes native `NA` even though its metadata description lists only `a/c/e`. The generated inventory remains authoritative for exact-release observations. A future ontology profile may project `gn=m` to a general masculine concept, but the raw native value remains authoritative and must be retained for reproducibility.

#### Edges

- `mother`: directed linguistic dependency from a node to its selected mother; BHSA documentation warns that the relation is not the same as textual embedding. In current TF each source node has zero or one selected mother, although the historical analysis workflow considered multiple candidates.
- `distributional_parent`: directed embedding in the continuous `*_atom` hierarchy.
- `functional_parent`: directed embedding in the potentially discontinuous functional hierarchy.

These are semantic edges, not aliases for `oslots` containment. They are unvalued TF edges.

#### Semantic coverage

BHSA is strongest in morphology and linguistic syntax. It also has lexical class/gloss information, limited discourse/text-type features (`domain`, `txt`), qere information and rich structural relations. It has no physical manuscript/tablet hierarchy, no apparatus of competing manuscript readings comparable to Pseudepigrapha-TF, and no cuneiform sign layer.

### 2.2 Copenhagen Ugaritic Corpus 0.2.8

#### Structure and counts

CUC deliberately uses `sign` slots; `word` is a higher-level object.

| node type | count |
|---|---:|
| `sign` | 146,017 |
| `word` | 27,770 |
| `line` | 7,616 |
| `column` | 334 |
| `tablet` | 279 |

Sections are `tablet / column / line`. `otext.tf` exposes transliteration/sign rendering formats. This physical hierarchy is native evidence, not a remapping of book/chapter/verse.

#### Node features

The committed `tf/0.2.8` feature inventory contains:

| feature | type | meaning / domain | applies to |
|---|---|---|---|
| `sign` | string | Latin/transliteration representation of the sign | `sign` |
| `usign` | string | Ugaritic Unicode representation when available | `sign` |
| `g_cons` | string | consonantal value | `word` |
| `trailer`, `utrailer`, `trailer_emen` | string | following spacing/punctuation/editorial rendering | `word` |
| `language` | string/categorical | encoded language | `word` |
| `tablet`, `tablet_info` | string | tablet identity and metadata | `tablet` |
| `column` | string/int-like | column label/number | `column` |
| `line` | string/int-like | line label/number | `line` |
| `side` | string/categorical | physical side | `line` |
| `emen` | string/categorical | emendation/editorial state; source documentation covers restoration, missing/excised/redundant material | `sign` |
| `cert` | string/categorical | certainty corresponding to KTU editorial typography | `sign` |
| `alt` | string | alternative reading | `sign` |
| `cont` | string/flag-like | line-continuation information | `sign` |

There are no corpus-specific semantic edge feature files in `0.2.8`; containment is represented through `oslots` and section hierarchy.

#### Semantic coverage and uncertainty

CUC supplies physical tablet structure, sign-level text, editorial uncertainty and alternative readings. It does not currently provide the BHSA-style morphology/syntax layer. `emen`, `cert` and `alt` should remain separate ontology assertions: emendation state, confidence/certainty and an alternative reading are not the same proposition.

### 2.3 ETCBC Syriac corpus 0.9

#### Structure and counts

`word` slots; only textual sections above them:

| node type | count |
|---|---:|
| `word` | 360,193 |
| `book` | 29 |
| `chapter` | 676 |
| `verse` | 16,072 |

Sections are `book / chapter / verse`; there are no clause/phrase/sentence nodes in the committed schema.

#### Node features

The `tf/0.9` inventory contains `book`, `chapter`, `verse`, warp/text features and the following linguistic families:

| domain | features | type / bounded values | applies to |
|---|---|---|---|
| orthography | `g_cons`, `g_cons_utf8`, `trailer` | string | `word` |
| lexical | `lex`, `g_lex`, `gloss`, `ls` | string/open | `word` |
| POS | `sp` | categorical, Syriac corpus-native | `word` |
| verbal morphology | `vs`, `vt`, `vo`, `vpm` | categorical/string | verbal `word` |
| agreement | `gn`, `nu`, `ps` | categorical | `word` |
| state | `st` | categorical | `word` |
| morphemes | `emf`, `g_emf`, `nme`, `g_nme`, `pfm`, `g_pfm`, `pfx`, `g_pfx`, `vbe`, `g_vbe`, `vbs`, `g_vbs` | string/categorical | `word` |

The repository describes the dataset as derived from a morphologically parsed Syriac source and explicitly notes that the Peshitta subset is not accompanied by a critical apparatus here.

There are no custom semantic edge features in the committed `0.9` TF directory.

### 2.4 ETCBC Peshitta 0.2

#### Structure and counts

| node type | count |
|---|---:|
| `word` | 426,835 |
| `book` | 65 |
| `chapter` | 1,269 |
| `verse` | 31,341 |

`word` is the slot; sections are `book / chapter / verse`.

#### Node features

The committed feature set is intentionally small: section features, `word`/`word_etcbc`, `trailer`/`trailer_etcbc`, and `witness` in addition to warp/text data. `witness` is a string feature documented as **book witness A or B**. It is not a reading-to-manuscript graph edge and should not be mapped as though it asserted a critical apparatus reading.

No morphology or BHSA-style syntactic features are present in this TF version. No custom semantic edge features are present.

### 2.5 ETCBC SyrNT 0.1

#### Structure and counts

| node type | count |
|---|---:|
| `word` | 109,640 |
| `book` | 27 |
| `chapter` | 260 |
| `verse` | 7,957 |
| `lexeme` | 3,038 |

`word` is the slot. Sections are `book / chapter / verse`. `lexeme` is a separate node type, unlike current `ETCBC/syriac` 0.9.

#### Node features and bounded domains

The corpus documentation gives unusually explicit domains:

| feature | type | bounded/documented values | meaning |
|---|---|---|---|
| `word`, `word_etcbc`, `word_sedra` | string | open | surface word encodings |
| `lexeme`, `lexeme_etcbc`, `lexeme_sedra` | string | open | lexeme encodings |
| `root`, `root_etcbc`, `root_sedra` | string | open | lexical root |
| `stem`, `stem_etcbc`, `stem_sedra` | string | open | stem |
| `prefix*`, `suffix*` | string | open | affix strings |
| `demcat` | string | `far`, `near`, `NA` | demonstrative category |
| `fmhdot` | int | `0`, `1` | feminine-he dot present |
| `gn` | string | `f`, `m`, `c`, `NA` | gender |
| `nmtyp` | string | `cardinal`, `NA` (documented table) | numeral type |
| `ntyp` | string | `common`, `proper`, `NA` | noun type |
| `nu` | string | `s`, `p`, `NA` | number |
| `prtyp` | string | pronoun categories including `personal`, `interrogative` | pronoun type |
| `ps` | string | `1`, `2`, `3`, `NA` | person |
| `ptctyp` | string | `active`, `passive`, `NA` | participle type |
| `seyame` | int | `0`, `1` | seyame present |
| `sfcontract` | string | `suffix`, `contraction`, `NA` | suffix contraction |
| `sfgn` | string | `f`, `m`, `NA` | suffix gender |
| `sfnu` | string | `p`, `NA` | suffix number |
| `sfps` | string | `1`, `2`, `3`, `NA` | suffix person |
| `sp` | string | `noun`, `verb`, `particle`, `pronoun`, `adjective`, `numeral`, `adverb`, `idiom` | POS |
| `st` | string | `absolute`, `construct`, `emphatic`, `NA` | state |
| `vs` | string | Syriac conjugations including `peal`, `pael`, `paiel`, `ethpael`, ... | verbal stem/conjugation |
| `vt` | string | `perfect`, `participle`, `imperfect`, `imperative`, `infinitive`, `NA` | verbal aspect/tense |

There are no custom semantic edge features. The documentation says some books occur in several witnesses and are represented as separate books with suffixed names; this is again distinct from Peshitta's `witness` feature and Pseudepigrapha-TF's apparatus graph.

### 2.6 Syriac compatibility decision

The POC should use **`ETCBC/syriac` 0.9 as the primary modern Syriac representative for broad morphological coverage, while maintaining independent corpus profiles and compatibility tests for `peshitta` 0.2 and `syrnt` 0.1**.

Reasons:

- `syriac` 0.9 is current and morphologically rich, but has no `lexeme` nodes and no critical apparatus.
- `peshitta` 0.2 has a much thinner textual schema and a native A/B `witness` feature that would disappear if it were treated as a schema alias of `syriac`.
- `syrnt` 0.1 has separate `lexeme` nodes, roots/stems/affixes and several SEDRA-specific categorical features absent or differently encoded in `syriac` 0.9.
- value domains differ even when labels look comparable. A safe shared projection can cover concepts such as POS/gender/number/person/state, but native values and versioned mappings must remain corpus-specific.

Therefore the three datasets are **not** one ontology adapter with three data locations. They may share a Syriac profile module internally, but each corpus requires its own compatibility manifest and mapping assertions.

### 2.7 ETCBC Extra-biblical 0.2

#### Structure and counts

This corpus shares much of the older ETCBC linguistic object model with BHSA but is not identical.

| node type | count |
|---|---:|
| `word` | 39,862 |
| `book` | 13 |
| `chapter` | 79 |
| `verse` | 1,800 |
| `half_verse` | 1,800 |
| `clause` | 8,908 |
| `clause_atom` | 9,160 |
| `phrase` | 22,770 |
| `phrase_atom` | 23,370 |
| `sentence` | 6,429 |
| `sentence_atom` | 6,665 |
| `subphrase` | 15,351 |

It has no separate `lex` node type in `otype.tf`.

#### Features and edges

The committed `0.2` directory includes the BHSA-family morphology (`gn`, `nu`, `ps`, `st`, `vs`, `vt`, pronominal/morpheme features), lexical/string features (`lex`, `g_lex`, `ls`, `language`), phrase/clause features (`function`, `det`, `domain`, `code`, `kind`, `is_root`) and generic distance/parent metadata. Unicode and transliteration variants are preserved separately.

It also contains the same three major custom edge families as BHSA:

- `mother` — linguistic dependency;
- `distributional_parent` — distributional embedding;
- `functional_parent` — functional embedding.

This is the strongest candidate for high-confidence BHSA-family syntactic interoperability. Even here, mappings must be per feature/version because lexical node structure and some inventories differ.

### 2.8 TLHdig-TF 0.2.0

#### Structure and counts

TLHdig-TF is the strongest counterexample to a word-centric POC. `sign` is the slot because editorial markers can occur within signs and cross word/line boundaries.

| node type | count |
|---|---:|
| `sign` | 3,386,344 |
| `word` | 1,234,497 |
| `analysis` | 1,626,932 |
| `lex` | 28,282 |
| `cluster` | 656,389 |
| `line` | 412,637 |
| `layout` | 407,762 |
| `edit` | 170,955 |
| `paragraph` | 108,466 |
| `colon` | 98,008 |
| `column` | 43,434 |
| `surface` | 32,909 |
| `document` | 23,884 |
| `docgroup` | 23,734 |
| `fragment` | 23,150 |
| `note` | 12,152 |

The physical spine is `sign -> word -> line -> column -> surface -> document`; paragraphs/colons and analytical/editorial layers overlap it. TF sections are `document / column / line`.

The generated census records **107 node features and 9 custom edge features**.

#### Feature families

| domain | representative/native features | type / semantics | main nodes |
|---|---|---|---|
| sign text | `sym`, `after`, `type`, `corr`, `subscr`, `materlect`, `surplus`, `symmark`, `othertags` | string/categorical | `sign` |
| cuneiform alignment | `cu_sign`, `cu_aligned`, `cu_method`, `cu_nsigns`, `cu_undecided`, `cu_unrendered`, `cu_pua`, `cu_broken` | string/int; absence means unresolved/not asserted | sign/line |
| damage flags | `missing`, `laes`, `ras`, `add`, `quot` | int flags induced from range nodes | `sign` |
| word morphology | selection metadata `nanalyses`, `mrpsel`, `mrpsel_kind`, `nselected`, `sel_base`, `sel_clitic`, `sel_group` | int/string | `word` |
| analysis | `lemma`, `gloss`, `morph`, `stemclass_raw`, `stemclass`, `pos`, `field4_kind`, `det_hint`, clitic fields, `parse_ok`, `raw`, `index`, `sep` | mixed string/int; alternatives remain separate nodes | `analysis` |
| lexicon | `lemma`, `gloss`, `noccs` | string/int | `lex` |
| damage/editorial range | `type`, `width`, `start_offset`, `end_offset`, `orphan`, `crossesline`, `nested`, `from_open_marker`, `from_close_marker` | categorical/int | `cluster` |
| physical structure | `lnr`, `lnno`, `ln`, `prime`, `linetail`, `collabel`, `column`, `surface`, `frag`, `txtid` | string/int | line/column/surface |
| document/provenance identity | `docid`, `docid_raw`, `cth`, `project`, `subcorpus`, `src_file`, `source_subdir`, `source_stem`, `lang`, `lang_raw`, `invnr`, `directjoin`, `indirectjoin` | string | `document` |
| editorial history | `kind`, `order`, `editor`, `date`, `part`, `src`, `frgm`, `docs`, `comment`, `author`, `alt`, `neu` | string/int | `edit` |
| witness fragment | `frag`, `txtpubl` | string | `fragment` |
| grouping | `docid`, `nrecords` | string/int | `docgroup` |

The dataset-level TF metadata independently records `sourceVersion=0.3`, `version=0.2.0`, source DOI, source licence, derived-data licence and language.

#### Edge semantics

All directions below are source -> target. Eight are unvalued; `selected` is valued.

| edge | direction | value | assertion |
|---|---|---|---|
| `analyses` | `word -> analysis` | none | candidate morphological analysis belongs to word |
| `selected` | `word -> analysis` | selector token string | source/editor explicitly selected this analysis/alternative |
| `lexeme` | `analysis -> lex` | none | analysis resolves to lexical `(lemma, gloss)` entity |
| `startsAt` | `cluster -> sign` | none | exact boundary sign for editorial/damage range |
| `endsAt` | `cluster -> sign` | none | exact boundary sign for range |
| `witness` | `line -> fragment` | none | line cites/is witnessed by manuscript fragment siglum |
| `noteref` | `note -> sign` | none | editorial note anchored at sign |
| `edits` | `edit -> document` | none | editorial history event belongs to document record |
| `edition` | `document -> docgroup` | none | document record claims same manuscript identity/group; does not assert edition equivalence |

A key modelling detail is that `oslots` on `lex`, `edit`, note-like and other non-textual objects can be a TF technical anchor rather than semantic extent. Consumers must use the declared semantic edge for meaning. This distinction has to be expressible in ontoTF.

#### Explicit uncertainty

Morphological alternatives are separate `analysis` nodes; source selection is a valued `selected` edge. Cuneiform alignment carries levels/mechanisms and leaves unresolved assignments absent. Damage is represented both by `cluster` range objects and derived sign flags. Crossing-tag repairs and excluded source files are documented separately and must not be turned into ontology facts.

### 2.9 Pseudepigrapha-TF stress profile

Pseudepigrapha-TF intentionally does not commit OCP XML or generated TF data, so this section inventories the pinned converter contract and its independent raw-XML parity audit rather than claiming a released corpus census.

`word` is the primary slot. Standard sections are `book / chapter / verse`, but the source hierarchy and apparatus require additional nodes:

- `div` — literal source hierarchy;
- `unit` — textual apparatus locus;
- `reading` — one reading/alternative;
- `variant_word` — token belonging to a non-primary reading;
- `manuscript` — witness entity;
- `resource` — bibliographic/source resource;
- `version_metadata` — source version with metadata but no textual units;
- `ellipsis` — upstream `<elipsis>` structural marker;
- `orphan_reading` — malformed direct-`div` reading preserved without inventing a unit;
- ordinary section nodes/slots.

Important node features include exact `source_ref` and structured `source_ref_parts`; stable `version_id`; `reading_text`, `reading_xml`, option/primary/gap flags; manuscript abbreviation/name/language/show metadata and `undefined_manuscript`; version title/language/author; lexical `lex`, `morph`, `style`, effective language and literal `w_lang`; anomaly/empty-division flags; source child ordering; exact OCP book/work identity.

Custom edges include:

- `parent`: source hierarchy ownership;
- `reading_of`: reading -> apparatus unit;
- `witness`: reading/orphan reading -> manuscript;
- `variant_word_of`: alternative token -> reading;
- `manuscript_of`: manuscript -> exact version owner;
- `resource_of`: resource -> exact version owner.

The converter preserves explicit omissions separately from unattested witnesses. A missing witness assignment is not inferred to mean an omission or lacuna. Metadata-only versions remain metadata-only rather than receiving fabricated text. Duplicate human-readable version titles are disambiguated by stable `version_id`. Exact duplicate source citations are retained with technical section suffixes while the source reference remains unchanged.

This stress profile establishes that a ontoTF witness ontology must support **witness entity + reading assertion + locus + version ownership + explicit absence state**, not just a `witness` string.

### 2.10 ORACC-TF stress profile

At the inspected commit the joined RIAO+RINAP target is still an implementation schema. The counts below come from measured source data and the current P-001 whole-corpus TDD gates.

`sign` is the slot type. The physical/textual model uses `document`, `face`, `column`, `line`, generic `chunk`, real `phrase`, `word`, `lex`, and sign slots. The planned translation layer adds range-spanning `translation_unit`/`translation_note` nodes rather than forcing translations onto individual lines.

| type | source entities | TF warp | zero-span sidecar |
|---|---:|---:|---:|
| `document` | 2,078 | 1,842 | 236 |
| `face` | 2,312 | 2,036 | 276 |
| `column` | 758 | 723 | 35 |
| `line` | 56,226 | 56,084 | 142 |
| `chunk` | 13,644 | 13,388 | 256 |
| `phrase` | 4,499 | 4,499 | 0 |
| `word` | 320,975 | 320,680 | 295 |
| `lex` | 8,025 | 8,023 | 2 |
| `sign` | 792,651 | 792,651 | — |

There are 1,242 zero-span entities in the sidecar. This is a direct constraint on ontoTF architecture: a semantic entity cannot be required to be a TF node with a meaningful textual extent.

#### Sign/token features

The target reuses existing cuneiform feature names where the domains match: `reading`, `readingu`, `grapheme`, `lnno`, `period`, `genre`, `material`, `collection`, `damage`, `missing`, `det`. ORACC lexical/grammatical data adds `cf`, `gw`, `sense`, `norm`, `pos`, `epos`, `lang`, `sig`, `discourse` and a lexical entity layer. Each sign retains a source path into the GDL structure; each source word retains canonical GDL serialization because a flat sign sequence cannot reconstruct all ORACC operators/qualifications.

ORACC GDL itself contains semantically different structures: syllabic signs, sign-name children, logogram/determinative wrappers, unreadable stretches, numeral parents that carry the real Unicode sign, qualified signs, compounds, rendering references and operators. The census therefore rejects a generic rule that every GDL leaf is a sign.

#### Lexical relations

A source word may correspond to multiple lexical analyses/entries, including compound forms. The measured maximum `word -> lex` degree is three even though raw `inst` can contain up to fourteen repeated slots. Lexical identity is keyed by native `(lang, cf, gw, pos)` in the current design, not merely by normalized spelling.

#### Discourse/syntax caution

ORACC source `c type=sentence` chunks are **all implicit** in the measured target and can be extremely large (maximum 6,303 words). The converter deliberately names them generic `chunk` with `chunk_type=sentence`; it does not expose them as linguistic `sentence` nodes. `c type=phrase` is separately exposed because measured spans are genuinely phrase-sized. A cross-corpus `Sentence` mapping is therefore `unknown`/unsupported until a stronger source assertion exists.

#### Object/material/provenance metadata

The catalogue layer commonly supplies `designation`, `genre`, `subgenre`, `period`, `provenience`, `language`, `supergenre`, `ruler`, `object_type`, `material`, `script`, `exemplars`, `primary_publication`, `pleiades_id`, `pleiades_coord`, and `cdli_id`. Document identity is qualified by subproject because bare Q numbers collide across editions. Raw per-document licence fields are preserved; the converter does not infer an absent `license_type`.

The ORACC case establishes first-class archaeological/material/provenance concepts that are absent from BHSA and the simple Syriac corpora.

## 3. Cross-corpus semantic clusters

The classifications in this section are **candidate relationship strengths**, not final ontology mappings.

### 3.1 Compact matrix

Legend: **S** candidate `same`; **C** `close`; **B/N** broader/narrower; **R** related; **U** unknown/unsupported; **L** local-only/native specialization. Cells describe the corpus-native evidence available for the cluster.

| semantic cluster | BHSA | CUC | Syriac 0.9 | Peshitta | SyrNT | ExtraBiblical | TLHdig-TF | Pseudepigrapha-TF | ORACC-TF target |
|---|---|---|---|---|---|---|---|---|---|
| TF slot | word | sign | word | word | word | word | sign | word | sign |
| word/token | S word slot | S word over signs | S word slot | S word slot | S word slot | S word slot | S word over signs | S word slot / variant token overlay | S word over signs |
| sign/grapheme | U | C primary alphabetic sign | U | U | U | U | C primary cuneiform sign + alignment | U | C semantic GDL sign |
| lexical entry | `lex` node | U | word feature | word text only | `lexeme` node | word feature | `lex` node anchored + edge | word `lex` feature | `lex` node + many-to-many edge |
| lemma/root/gloss | rich lexical features | U | lex/gloss | U | lexeme/root/stem | lex/ls | lemma/gloss on analysis+lex | lexical annotation on `<w>` where present | cf/gw/sense/norm/sig |
| POS | rich | U | `sp` | U | `sp` SEDRA values | rich | `pos` on analysis | source annotation where present | `pos`/`epos` |
| gender/number/person | S native morphology | U | C native morphology | U | C native morphology | C BHSA-family | analysis morphology, requires parsing profile | source annotation dependent | corpus lexical morphology dependent |
| verbal stem/tense | native Hebrew L/C | U | native Syriac L/C | U | native Syriac L/C | Hebrew-family C | Hittite analysis L/C | language dependent | Akkadian/ORACC L/C |
| phrase | S linguistic | U | U | U | U | S/C ETCBC | no BHSA phrase ontology | source hierarchy/apparatus, not syntax | C only explicit `phrase`; generic chunks separate |
| clause | S linguistic | U | U | U | U | S/C ETCBC | U | U | U |
| sentence | S linguistic | U | U | U | U | S/C ETCBC | U | U | **U for ORACC implicit sentence chunks** |
| syntactic dependency | S `mother` | U | U | U | U | S `mother` | U | R source `parent` is structural, not syntax | U |
| hierarchical parent relation | S `functional_parent` + `distributional_parent` | U | U | U | U | S `functional_parent` + `distributional_parent` | U | C source structural `parent`; semantics differ from ETCBC hierarchy | U |
| discourse/text category | domain/txt | U | U | U | U | domain/code/kind | project/structural metadata | version/source hierarchy | generic chunk/discourse source category |
| book/chapter/verse | S | U | S | S | S | S | U | S interface + exact source refs | U |
| tablet/document | U | tablet | textual work only | textual book | textual book | textual book | document | version/work/source hierarchy | document |
| surface/column/line | U | tablet-column-line; side | U | U | U | U | surface-column-line | source refs/divs, not physical default | face-column-line |
| witness entity | U | U | U | A/B feature only | multi-witness books | U | fragment node | manuscript node | edition/catalogue concepts; not same as apparatus witness |
| reading/variant | qere R | `alt` R | U | U | U | limited | analysis is morphology, not textual reading | full reading/unit graph | source text editions; translation layer separate |
| omission/unattested | U | editorial signs only | U | U | U | U | damage ranges, not witness state | explicit omission vs unattested | U unless source asserts |
| damage/restoration | U | emen/cert R | U | U | U | U | cluster + induced flags S/C | reading/source markup, source-specific | damage/missing C |
| uncertainty | analyst/source categories | cert/alt | missing morphology remains absent | sparse | `NA` and source categories | source categories | multiple analyses, selected edge, alignment levels, orphan ranges | explicit anomalies/readings/no inference | sign classification, zero-span/source anomalies |
| material/object | U | tablet identity/side | U | U | U | U | document/inventory/join metadata | manuscript/resources | rich catalogue material/object metadata |
| geographic/archaeological provenance | U | tablet metadata limited | U | U | U | U | project/CTH/source provenance | version/resource provenance | provenience + Pleiades/CDLI/ruler/period |
| scholarly/editorial event | analyst features | emendation | U | U | U | analyst encoding | explicit `edit` nodes + notes | apparatus/source anomalies | translation/editorial catalogue/source metadata |

### 3.2 High-confidence recurring concepts

Candidates for a small shared core because the native assertions are sufficiently close at an abstract level:

- Text-Fabric `Node`, `Slot`, node type and slot-span membership, while retaining the corpus slot type;
- textual `Word`/token as an abstract class, with explicit relation to sign slots in sign-based corpora;
- `Line` where the source actually has line structure;
- `LexicalEntity` / lexical occurrence relation, but without forcing one extent convention;
- general grammatical categories `PartOfSpeech`, `Gender`, `Number`, `Person` where a corpus explicitly annotates them;
- `Document/TextualWork` at a broad level, with subtypes for book/tablet/manuscript record/edition;
- `SourceIdentifier`, corpus version, upstream version and provenance metadata;
- a general `ScholarlyAssertion`/annotation concept capable of carrying source, confidence and mapping strength.

### 3.3 Concepts requiring profiles or language-specific terms

- Hebrew vs Syriac vs Hittite vs Akkadian verbal stems and tense/aspect systems;
- lexical state/conjugation inventories;
- BHSA clause/phrase codes and dependency semantics;
- SEDRA-specific noun/pronoun/participle categories;
- ORACC GDL object kinds/operators;
- TLHdig morphology selection syntax and Hittite stem classes;
- KTU/CUC editorial conventions;
- archaeological object/material/provenience vocabularies.

These should map upward to shared abstractions only when the broader assertion is defensible. The native term/value must remain available.

### 3.4 Distinctions the POC must preserve

#### Extent vs anchor

`oslots` is not always semantic extent. TLHdig-TF lexical nodes and Pseudepigrapha metadata/anomaly nodes may use technical anchors because TF requires non-slot nodes to be linked to slots. ORACC-TF additionally demonstrates genuine source entities that cannot be safely represented as TF nodes at all. The ontology layer needs an explicit way to say whether a span is `extent`, `anchor`, `locus`, `derived extent`, or unavailable.

#### Containment vs dependency

BHSA `mother` is a linguistic dependency; `functional_parent`/`distributional_parent` are hierarchical relations; Pseudepigrapha `parent` is source-structural ownership; `oslots` is textual coverage. They cannot share one generic `parent` predicate without a typed subrelation.

#### Entity vs feature

The same broad concept appears as a node in one corpus and a feature in another: SyrNT has `lexeme` nodes, Syriac has lexical features on words; Pseudepigrapha has `manuscript` nodes, Peshitta has a `witness` string; TLHdig has `fragment` nodes while CUC keeps much editorial information on signs. The POC cannot require representation-shape identity.

#### Assertion vs inferred convenience

Several source models deliberately preserve ambiguity: TLHdig morphological alternatives, CUC alternative readings/certainty, OCP competing readings and unattested witnesses, ORACC ambiguous GDL structures. ontoTF must never turn absence into a negative assertion or choose one alternative silently.

## 4. Candidate cross-corpus interoperability queries

These are acceptance probes for the later POC. Each query must return native provenance and mapping strength, and must report unsupported dimensions rather than dropping corpora silently.

1. **POS distribution across morphologically annotated word corpora.** Query nouns/verbs across BHSA, ExtraBiblical, Syriac 0.9, SyrNT, TLHdig-TF and ORACC-TF. Expected: use corpus-specific POS mappings; Peshitta and CUC report POS unsupported.
2. **Gender/number/person comparison.** Query explicit masculine/feminine and singular/plural/person annotations across BHSA-family and Syriac corpora. Expected: exact source values returned alongside projected category; no value is invented for unannotated words.
3. **Verbal-stem exploration without false equivalence.** Request verbs grouped by native conjugation/stem, then optionally by a broader `VerbalStemCategory`. Expected: Hebrew `qal`, Syriac `peal`, Hittite morphology and Akkadian values remain distinct unless a mapping profile explicitly relates them.
4. **Lexical entity lookup.** Search a lexical identity and retrieve occurrence relations in BHSA `lex`, SyrNT `lexeme`, TLHdig `analysis -> lex`, and ORACC `word -> lex`. Expected: consumer can inspect whether `oslots` is semantic extent or technical anchor.
5. **Syntactic dependency query.** Ask for clauses dependent on a mother clause across BHSA and ExtraBiblical. Expected: those corpora participate; Syriac/CUC/TLHdig/Peshitta report unsupported, not empty-result-as-if-no-dependencies.
6. **Physical document navigation.** Retrieve document/tablet -> surface/side -> column -> line across CUC, TLHdig-TF and ORACC-TF. Expected: related physical predicates can be queried while preserving CUC `tablet` versus TLH/ORACC `document` identity.
7. **Damage/restoration filter.** Find signs affected by missing/restored/damaged material across CUC, TLHdig-TF and ORACC-TF. Expected: result records native state and whether mapping is `same`, `close` or `related`; certainty is not collapsed into damage.
8. **Explicit uncertainty.** Find tokens/signs with more than one analysis/reading or low certainty. Expected: TLH morphological alternatives, CUC `alt`/`cert`, OCP readings and ORACC source ambiguity are returned as distinct assertion types under a broader uncertainty query.
9. **Witness reading query.** For a passage/locus, retrieve explicit readings and manuscript witnesses in Pseudepigrapha-TF. Compare Peshitta A/B metadata and TLH line-fragment witness links. Expected: broad `TextualWitness` discovery works, but only OCP results satisfy `witness has reading at locus` unless another corpus provides that assertion.
10. **Omission versus unattested.** Request explicit witness omissions. Expected: Pseudepigrapha-TF returns source omissions; absence elsewhere is `unsupported/unknown`, never inferred omission.
11. **Editorial event provenance.** Retrieve source/editor/date/comment for explicit TLHdig `edit` nodes and related CUC emendation annotations. Expected: preserve event-vs-state distinction.
12. **Material and archaeological metadata.** Query clay/tablet/object material, provenience or Pleiades/CDLI identity in ORACC; expose whatever tablet metadata CUC/TLH provides; BHSA/Syriac explicitly report unsupported.
13. **Corpus/source version trace.** For every result return corpus repository, corpus/TF version, upstream version/commit/DOI where available, native node/id and mapping version. This is mandatory for every semantic query, not an optional debug mode.
14. **Zero-span entity retrieval.** Query ORACC metadata-only/zero-span entities and Pseudepigrapha metadata-only versions. Expected: they remain discoverable even when no meaningful `oslots` extent exists.
15. **No-false-sentence test.** Query linguistic sentences across BHSA/ExtraBiblical and ORACC. Expected: ORACC implicit `chunk_type=sentence` does not appear as a linguistic sentence unless explicitly requested as a source chunk.
16. **No-false-alignment test.** Query the same normalized chapter/verse across multiple Pseudepigrapha versions. Expected: normalized section coincidence does not assert textual alignment; exact source refs/version status are returned.

## 5. Consequences for R-001 through R-004

### For R-001: distribution/version binding

A mapping artifact must bind to an exact corpus/schema version. Feature presence, node representation and even slot type change independently across corpora and versions. Compatibility cannot be inferred from repository family name. The distribution model must also support semantic modules that refer to sidecar entities or technical-anchor nodes, not only standard TF feature modules.

### For R-002: ontology governance

The governance model needs a small stable core plus optional linguistic, textual-critical, manuscript/codicological, cuneiform/epigraphic and archaeological profiles. Corpus-local concepts must remain legal first-class terms. Mapping strength and provenance must be versioned data, not comments in documentation.

### For R-003: agent and human ergonomics

Capability discovery must distinguish at least `supported`, `supported through broader/close mapping`, `native-only`, and `unsupported`. Query results need native feature/value, projected term, mapping strength, source corpus/version and assertion provenance. An empty result must not be used to encode unsupported semantics.

Agents also need representation information: whether an entity is a slot, ordinary node, anchored node, sidecar entity, or derived projection; whether a relation is containment, dependency, witness attestation, lexical membership or editorial linkage; and whether uncertainty is explicit.

### For R-004: documentation architecture

Generated per-corpus reference should include pins, slot type, node types/counts, features and categorical domains, edge direction/value semantics, text formats/sections, mapping table with strength, unsupported concepts and example cross-corpus queries. Handwritten prose should explain decisions and known uncertainties; machine-readable manifests should drive the exhaustive tables to avoid drift.

## 6. Rejected assumptions

1. **“Start from BHSA and add aliases.”** Rejected: sign-slot corpora, witness graphs, physical manuscript structure and zero-span entities do not fit that model.
2. **“Same feature name means same ontology predicate.”** Rejected: `witness`, sentence-like objects, lexical nodes and parent relations provide direct counterexamples.
3. **“Same node shape means same semantics.”** Rejected: a TF node's `oslots` may be semantic extent or a technical anchor.
4. **“All Syriac ETCBC corpora can use one mapping unchanged.”** Rejected: current Syriac, Peshitta and SyrNT have materially different schemas and value inventories.
5. **“Absence can be treated as false.”** Rejected: absence often means unsupported, unannotated, unknown or unattested; these are distinct states.
6. **“One universal sentence/phrase hierarchy is safe.”** Rejected: ORACC implicit chunks and BHSA linguistic objects have different source semantics.
7. **“Ontology normalization can discard native values once mapped.”** Rejected: later re-mapping, reproducibility and philological audit require the native assertion and version.
8. **“Every semantic entity must be representable as a normal TF node.”** Rejected: ORACC zero-span entities and technical-anchor patterns show the opposite.

## 7. Open uncertainties to carry forward

- BHSA documentation itself notes that the full linguistic interpretation/domain of `mother` for all object-type combinations needs further explanation. ontoTF should preserve the native relation and avoid stronger universal semantics until profiled.
- CUC's exact-release observed feature domains are generated and preserved by R-005 in `docs/research/data/generated/r005/cuc.json`. At pinned 0.2.8, the non-empty `cert` values are `False` and `True`; the non-empty `emen` values are `excised`, `missing`, `redundant`, `remark`, and `restored`. The generator records these as an observed small domain rather than claiming permanent categorical closure. A later production mapping must separately justify domain closure and ontology relations while preserving the native release values.
- `ETCBC/syriac` 0.9 and SyrNT 0.1 use different generations of Syriac morphology. Similar categories require value-level philological review before `same` claims.
- Pseudepigrapha-TF does not commit generated corpus data, so node counts are deliberately not invented here. The converter's parity audit and pinned upstream checkout make the schema inspectable; a later integration test should generate the corpus and freeze counts for the exact upstream pin.
- ORACC-TF is still under active implementation. Its measured P-001 schema is valuable stress evidence but should not be registered as a released ontoTF profile until its own release/schema version is final.
- Archaeological/object ontologies will need controlled-vocabulary research beyond this census. ORACC source strings such as material, period, genre and provenience should remain native until R-002 decides ontology sources and governance.

## 8. Acceptance-criteria trace

- [x] Used actual TF files/generated reports/source-data measurements, not repository descriptions alone.
- [x] Recorded exact commits and TF/schema versions.
- [x] Generated exhaustive node/edge feature inventories for every released minimum corpus at the pinned revisions, including metadata/value type, empirical applicability, observed non-empty domains/cardinalities, and edge direction/value status.
- [x] Classified every relevant apparent cross-corpus match explicitly in `R-005-candidate-strength-matrix.md` using the required candidate relationship vocabulary.
- [x] Covered BHSA, CUC, Syriac, Peshitta, SyrNT, ExtraBiblical and TLHdig-TF.
- [x] Covered Pseudepigrapha-TF and ORACC-TF as secondary stress profiles with their release/implementation status stated explicitly.
- [x] Compared all three ETCBC Syriac schemas and chose `syriac` as primary representative with independent compatibility profiles.
- [x] Inventoried recurring and corpus-local semantic concepts without declaring premature equivalence.
- [x] Included custom edge direction, valued/unvalued status and native semantics where present.
- [x] Included physical document, editorial, witness, uncertainty, object/material/provenance and zero-span structures.
- [x] Included a compact cross-corpus matrix for R-001/R-002/R-003/R-004.
- [x] Included a representative interoperability-query suite with negative/unsupported cases.
- [x] Recorded unresolved or insufficiently documented semantics rather than filling gaps by inference.

## 9. Research gate result

R-005 supplies enough empirical evidence for R-001 through R-004 to finalize recommendations against the actual target-family diversity. It does **not** authorize production mappings yet: the repository-wide research gate still requires R-001, R-002, R-003 and R-004 to complete and then be reconciled into an approved POC design before TDD implementation begins.