# Applicability research: remaining converter families

This extends the integrated #431/#432 policy using the pinned nine-corpus
scoped inventories. The objective is to determine a defensible granularity
and area of review for observed native entities. It does not assert ontology
equivalence, change the TF data or introduce a mapping registry.

## Source-specific findings

### TLHdig

The pinned [feature metadata implementation](https://github.com/alexsosn/TLHdig-TF/blob/e954600d9f9cc7f16570729813cf6bf3954b8f6d/programs/tlhdig/featuremeta.py)
is the source of the generated feature descriptions, supplemented by
[editorial markup](https://github.com/alexsosn/TLHdig-TF/blob/e954600d9f9cc7f16570729813cf6bf3954b8f6d/docs/editorial.md)
and [data model](https://github.com/alexsosn/TLHdig-TF/blob/e954600d9f9cc7f16570729813cf6bf3954b8f6d/docs/data-model.md).

- `crossesline` and `nested` describe source editorial span structure;
  `width=0` means a point statement, not damage to an anchored sign.
  Review the structural and textual extent semantics in CRMtex without
  asserting physical extent. 74,890 clusters carry crossesline=1 and 589
  carry nested=1 in the measured artifact.
- `from_open_marker` and `from_close_marker` distinguish real source
  boundaries from synthesized bounds. Of 656,389 clusters, 64,703 opening
  and 113,476 closing bounds are synthesized. `orphan` describes missing
  partner markers. These warrant source-evidence review in CRMinf, not
  equivalence to a belief or truth value.
- `parse_ok` (507 failing analyses) and `field4_kind` describe converter
  parsing/discrimination. `join_encoding` distinguishes XML/text
  serialization. Their native values remain queryable but are not historical
  or morphological semantic categories. `mrpsel_kind` is a heterogeneous
  source selection status, including language-like codes and deletion;
  do not map it as grammatical POS. Review the source-selection/evidence
  semantics instead. `sel_group` is explicitly not fully documented
  upstream (all=1,385, pl=382, sg=1,038 observations), so do not equate
  sg/pl with grammatical number.
- Apparatus entry kind (`fragment_kind`: invnr 3,061 / plain 17 / txtpubl
  24,937) warrants identifier/source record review, not physical-object
  class equivalence. Raw siglum candidates and join context retain
  unresolved evidence. Editorial-event scope, source, fragment and document
  associations merit CRM and CRMinf review; old/new CTH labels warrant
  SKOS review without inventing concept identities.
- `docid_raw` is documented as identical to docid today; `collabel`
  is a composed navigation label. Local order/offset fields and derived
  counts (analyses, selections, records, codepoints, PUA diagnostics)
  are preserved native data, without extra ontology-category obligations.
  The source path is release-scoped provenance, not persistent identity.
  `cu_undecided` is unresolved alignment evidence, distinct from a
  probability. Use actual census counts: the source description of
  cu_unrendered mentions 2,347 aligned signs, while the verified snapshot
  contains 2,229. No physical-glyph identity is inferred.
- `cudirty`, `mrp_control`, `othertags`, and `sel_group` remain
  unclassified. The first is only described as a source flag; the second
  is explicitly opaque; the third retains heterogeneous source tags
  without dedicated semantics; the fourth lacks full upstream definition.

### ORACC

The pinned [generated feature reference](https://github.com/alexsosn/ORACC-TF/blob/60db4b724a687c0f425e78eae924fce89454e106/docs/reference/features.md),
[model](https://github.com/alexsosn/ORACC-TF/blob/60db4b724a687c0f425e78eae924fce89454e106/docs/reference/model.md),
[identity](https://github.com/alexsosn/ORACC-TF/blob/60db4b724a687c0f425e78eae924fce89454e106/docs/reference/identity.md),
and [translations](https://github.com/alexsosn/ORACC-TF/blob/60db4b724a687c0f425e78eae924fce89454e106/docs/reference/translations.md)
distinguish source data from converter projections.

- Qualified document keys, source node identifiers and archive/rights
  provenance are property-review candidates in CIDOC CRM. A source
  identifier, including a propagated document key, never by itself
  establishes physical identity or cross-corpus equivalence. The section
  document key and documented readingu/lnno aliases do not require a second
  mapping obligation.
- Source chunk type/subtype and implicit marker belong to textual structure
  review. The observed 5,221 implicit=yes chunks are not the converter's
  synthetic anchors. 689 synthetic empty sign slots and 14 synthetic face
  nodes are technical guards. Catalogue presence, populated status and
  lemmaknown (31,770 false / 289,205 true) are availability flags, not
  semantic source categories; preserve them for guarded queries.
- The language code property includes special source codes; no independent
  grammatical class for every literal. Source TEI translation ranges and
  identifiers require review of textual references/alignment. All 6,792
  aligned translation units in the verified artifact have subtype tr;
  a documented but unobserved alternative is not added to the observed
  denominator.
- Raw catalogue/GDL/sign JSON and TEI serialization are composite source
  representations, not single ontology-category obligations. Excluding
  that wrapper does not classify the nested information. Source paths and
  row counts remain native. All currently inventoried units have a
  research route or explicit granularity exclusion.

### Pseudepigrapha

The pinned [feature reference](https://github.com/alexsosn/Pseudepigrapha-TF/blob/7c4b757bb543a110ae9a252d1281835859136852/docs/features/0_home.md),
[source identity/anomalies](https://github.com/alexsosn/Pseudepigrapha-TF/blob/7c4b757bb543a110ae9a252d1281835859136852/docs/source-identity-and-anomalies.md),
[apparatus](https://github.com/alexsosn/Pseudepigrapha-TF/blob/7c4b757bb543a110ae9a252d1281835859136852/docs/apparatus.md)
and [README](https://github.com/alexsosn/Pseudepigrapha-TF/blob/7c4b757bb543a110ae9a252d1281835859136852/README.md)
document generated translations, source witnesses, and exact citations.

- The 2,462 is_gap=1 word anchors exist for empty primary readings and
  are not historical lacunae. Converter identity/anomaly and metadata-only
  flags stay as native guards. Explicit omission and absence of witness
  attestation remain distinct; generated witness provenance remains
  separate from historical witnesses.
- Actual source references, version language, textual division declarations,
  original reading-option labels, introduction/edition metadata and
  unit identifiers merit textual/property review. The 231 OCP-Trans marker
  occurrences indicate generated provenance; review the property instead
  of mapping this source literal as a class. Historical themes and rights
  warrant SKOS/CRM review; source editorial corrections warrant CRMinf
  assessment, not an asserted inference.
- Deterministically inserted boundary separators, sequence indices,
  numeric reading option normalization, token counts and the manuscript
  show/display attribute are not independent ontology categories. Preserve
  literal witness lists and rich XML content, but assess the explicit
  graph relations and semantic properties rather than requiring a second
  mapping of the whole serialization. Nested markup is not thereby
  semantically classified.
- Source literal div_fragment, unit group and intro_status_json lack
  adequate semantic definitions in the pinned feature descriptions;
  leave them unresolved rather than assume a fragment relation,
  group identity or scholarly status.

## Reconciled scope counts

Independent enumeration of the nine pinned snapshots gives:

| Observed unit | Total | Routed | Explicitly excluded | Unclassified |
| --- | ---: | ---: | ---: | ---: |
| Node type | 83 | 83 | 0 | 0 |
| Scoped feature | 739 | 483 | 248 | 8 |
| Selected node value | 1,317 | 1,046 | 268 | 3 |
| Directed local edge pair | 73 | 73 | 0 | 0 |
| Selected edge value | 4 | 4 | 0 | 0 |

All rules intersect actual observed units, no routed/excluded overlap.
The three unclassified values are all sel_group on TLHdig word nodes.
The eight feature scopes are listed above (four TLHdig, three
Pseudepigrapha) plus ExtraBiblical word.lexeme_count.

These numbers count the scope of research, not mappings or proven
ontology applicability. Candidate domains overlap across models.
Closed value sets were only selected for some families in the existing
census; other families (for example ORACC chunk_type/chunk_subtype,
TLHdig morph/stemclass and source layout tags) may require an expanded
domain inventory. No claim is made about every uncollected value,
conditional node guard, entity identity, or cross-version node map.
No new positive mappings are introduced in this research batch.
Continue target-level evaluation and XML mapping, and only expand census
selection where the source defines a meaningful category family.
