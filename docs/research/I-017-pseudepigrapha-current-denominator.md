# I-017 research — current Pseudepigrapha-TF semantic denominator

Issue: #206  
Parent: P-004 #202, Workstream A  
Status: research complete; ready for independently reviewed plan

## Question

Can the current Pseudepigrapha-TF denominator be regenerated from the exact
published materialized Text-Fabric artifact, replacing the historical
40-item curated R-011 stress-profile denominator without overstating
exhaustiveness?

Yes, if the claim is restricted to the schema-level semantic surface actually
materialized in the pinned TF 1.0 release. It must not be generalized to every
feature that the converter could emit for a different OCP snapshot.

## Authoritative release identity

The production evidence boundary is the published native Text-Fabric artifact,
not repository-head source code in the abstract and not the generated feature
documentation fixture.

- Repository: `alexsosn/Pseudepigrapha-TF`.
- Current repository head: `7c4b757bb543a110ae9a252d1281835859136852`.
- Tag `v1.0.0` resolves directly to the same commit.
- GitHub Release `v1.0.0` was published 2026-09-17.
- Native corpus asset: `tf-1.0.zip`.
- GitHub-recorded asset SHA-256:
  `d2dfad7e643699617a9493b9f5d724868f8027dd5f2e88bd558451e3e7819b7a`.
- Converter version: `1.0.0`.
- TF data version: `1.0`.
- Pinned OCP source commit:
  `c939dcbacad78c5d18d2c4282cad23c47e19ac07`.
- Canonical extracted TF-file digest recorded by the I-017 probe:
  `9b708add5b9f8ddbfdafa7dd61507956f7987ca6a70b2b9164342bd49003ec61`.

The release workflow materializes that exact OCP snapshot, validates the
generated graph, stages the native archive, loads it with stock Text-Fabric,
and binds the release commit/tag into the distribution manifest.

## Why the historical denominator is insufficient

The immutable I-016 historical manifest retains the R-011 40-item curated
denominator derived from Pseudepigrapha-TF commit
`d098845043897957efee7a42ae4854deddd5a1bd`. Its scope is correctly marked
`bounded-curated`; it cannot support a corpus-wide completion claim.

The current converter documentation advertises a wider supported contract, but
that contract intentionally contains optional corpus-dependent features. It is
therefore not evidence that a feature exists in the published TF 1.0 graph.

I-017 inventories the published archive itself.

## Machine inventory result

The pinned release contains:

- 13 materialized node types:
  `book`, `chapter`, `div`, `document_metadata`, `ellipsis`,
  `manuscript`, `orphan_reading`, `reading`, `unit`, `variant_word`,
  `verse`, `version_metadata`, `word`;
- 86 materialized non-warp node-feature files;
- 7 materialized non-warp edge features:
  `manuscript_of`, `parent`, `reading_of`, `translation_of`,
  `translation_unit_of`, `variant_word_of`, `witness`;
- the TF warp/support features `otype` and `oslots`, tracked separately as
  technical exclusions.

The compact evidence is committed at
`docs/research/data/generated/i017/pseudepigrapha-v1.0.0.json`. It records
node/edge counts, applicability, value types, descriptions, selected observed
domains, and release identity without copying the corpus payload.

## Semantic versus technical boundary

The denominator should treat every materialized node type and every
materialized non-technical relation as semantic/schema-bearing, even when a
particular semantic feature has no non-empty value in this release. Empty
serialized features such as `resource_name` can still express a stable
researcher-facing schema contract and must not disappear merely because the
current graph has zero values.

Five items are technical rather than semantic:

1. `node_feature:otype` — Text-Fabric node typing machinery; semantic node
   kinds are represented directly as `node_type:...` denominator items.
2. `edge_feature:oslots` — Text-Fabric support/anchoring relation. The
   converter explicitly marks it `technicalSupport=True` and warns that its
   anchors are not scholarly containment claims.
3. `node_feature:boundary_utf8` — deterministic separator inserted by the
   converter between OCP units, not source textual semantics.
4. `node_feature:reading_option` — converter-normalized integer used for
   ordering/query ergonomics; the literal upstream value is preserved
   separately in `reading_option_source`.
5. `node_feature:is_gap` — marker on the synthetic anchor slot created for
   an empty primary reading. The scholarly omission is represented on the
   reading by `is_omission`; the slot marker is support machinery.

Other positional/index, provenance, identifier, source-preservation,
apparatus, generated-translation, public-metadata and historical-classification
features remain semantic/native data for denominator purposes even when they
are derived or lack a shared ontology target. I-017 does not decide their
eventual ontology disposition.

## Closed value families

Observed small domains are not automatically bounded vocabularies. For
example, `language`, `ms_language`, `div_label`, `text_structure`,
`generated_language`, `ms_show`, `linebreak`, and similar features remain
feature-level items only.

The converter source gives positive closure evidence for these materialized
semantic families:

- `version_kind` = `source | generated_translation`; the converter stamps
  exactly these two classifications.
- `generation_marker` = `OCP-Trans`; the parser/model contract fixes the
  generated-translation provenance marker to this literal.
- sparse presence flags, whose positive value is exactly integer `1`:
  - `is_metadata_only`;
  - `is_missing_unit_id`;
  - `is_omission`;
  - `is_primary`;
  - `is_source_anomaly`;
  - `synthetic_witness`;
  - `undefined_manuscript`.

`is_gap=1` is not added because the entire feature is a technical exclusion.
No value expansion is justified for `reading_option`: its currently observed
0..6 range is data-dependent and the feature itself is technical.

This contributes 10 semantic `node_value` items.

## Proposed current denominator

For the exact TF 1.0 release:

- node types: 13;
- semantic node features: 83 (= 86 materialized non-warp features minus 3
  technical non-warp features);
- semantic edge features: 7;
- explicitly closed semantic node values: 10;
- **semantic denominator: 113 items**;
- **technical exclusions: 5 items**.

The denominator is therefore eligible for `scope_quality=machine-exhaustive`
within the declared release/schema scope.

“Machine-exhaustive” here means exhaustive over the pinned materialized TF
schema plus explicitly source-proven closed value families. It does not mean:

- every possible OCP XML attribute/value;
- every converter-supported optional feature absent from this corpus;
- every observed value of open-vocabulary features;
- complete ontology mapping coverage.

## Reproducibility method

The I-017 research CI:

1. downloads only the exact `v1.0.0` native release asset;
2. verifies the GitHub-recorded SHA-256 before inspection;
3. loads the archive with Text-Fabric 13.1.0;
4. runs the established R-005 exhaustive TF inventory machinery;
5. compares the generated compact inventory to the committed I-017 evidence.

TFont runtime remains network-free and does not acquire corpora.

## Plan handoff

The implementation plan should create a new immutable coverage-manifest
resource; it must not mutate `p004-r011-baseline-v1/pseudepigrapha.json`.

Required implementation properties:

- pin the release commit, tag, TF version, asset digest and inventory evidence;
- use `generated-r005-inventory` as the denominator basis;
- emit exactly the 113 semantic items and 5 technical exclusions above;
- expand only the 10 source-proven bounded values listed above;
- keep production semantic accounting unreviewed unless separately backed by
  reviewed production mappings;
- preserve historical R-011 research accounting only when an old item identity
  matches exactly and without upgrading its authority;
- require deterministic regeneration/checking from the committed compact
  evidence, with no network access in TFont runtime;
- prove that finite observed values outside the explicit closed-family policy
  are not expanded;
- retain the historical 40-item manifest unchanged for audit/history.

The plan must separately decide the immutable resource/version name and how the
new manifest is exposed alongside the historical baseline.
