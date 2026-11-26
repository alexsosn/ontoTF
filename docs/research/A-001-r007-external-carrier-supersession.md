# A-001 amendment: R-007 external-carrier supersession

**Issue:** #65  
**Recorded:** 2026-09-07  
**Applies to:** `docs/research/R-007-tf-structural-semantics.md`

R-007 remains unchanged as the reviewed historical research artifact merged in PR #53. This amendment is authoritative for the narrower runtime-boundary conclusions below.

## Decision

The generic `sidecar/native-adapter` carrier is superseded as a baseline ontoTF runtime concept.

It is not a baseline ontoTF runtime carrier, and ontoTF must not replace it with another generic external-storage carrier name.

**Storage location or source format is not a semantic carrier type.** Baseline ontoTF resolves semantic requests against already-materialized Text-Fabric / Context-Fabric corpus structure plus ontoTF semantic/provenance artifacts. Corpus-specific materializers own JSON/XML/CSV/TEI/database/API or other source ingestion.

External identifiers and URIs remain legitimate semantic, authority, identity, evidence, and provenance references. Their presence does not imply runtime dereferencing, arbitrary record addressing, or an external data-access adapter.

## R-007 conclusions retained

The following R-007 findings remain valid and are not weakened by this amendment:

- native TF warp and feature/edge semantics remain executable truth;
- `oslots` is neutral structural slot coverage/anchoring, not automatically constituency, containment, mereology, witness attestation, or semantic extent;
- `Slot` is a neutral TF structural concept without Word/Sign/Grapheme/Glyph implications;
- `slotLink` is the neutral public identity of native `oslots`;
- TF structural interpretation must distinguish ordinary textual extent, abstract occurrence sets, and technical anchors;
- `technicalAnchor` means a slot relationship used for graph addressability rather than semantic textual extent;
- exact discontinuous slot sets must be preserved;
- directed and valued TF edge semantics must preserve source, target, direction, and values;
- explicit omission/absence cannot be inferred from missing storage;
- POWLA and Web Annotation remain optional alignment/publication tools rather than TF runtime replacements.

The name `TFNodeExtentMode` and its precise final serialization remain P-003 design concerns; this amendment only removes the unsupported external-storage carrier branch.

## ORACC correction

R-007 section 3.5 and its later ORACC catalogue example were based on the earlier ORACC-TF sidecar-first zero-span assumption. Current ORACC-TF `docs/reference/architecture/ADR-0001-empty-slots-not-sidecars.md` supersedes that assumption.

The current ORACC model keeps independently positioned zero-span textual entities in the TF warp through explicit synthetic/empty slots. A synthetic/empty slot is a real TF positional slot but not a semantic cuneiform sign. Its rendering/content semantics must remain distinguishable from source signs.

Current merged R-011 pilot evidence is likewise materialized and TF-native: ORACC corpus plans use normal TF node/feature selectors, including catalogue-derived features such as `material` and `period`, rather than a ontoTF-side external-record selector.

Therefore ORACC provides no current evidence for generic adapter-side runtime addressing in ontoTF.

## Specific R-007 conclusions superseded

Where R-007 says any of the following, A-001 replaces that conclusion:

1. semantic entities are baseline-realized as either `tf-node` or `sidecar/native-adapter`;
2. sidecar/native-adapter is a required canonical IR carrier dimension;
3. ORACC catalogue/object entities should resolve through `carrier=sidecar/native-adapter`;
4. P-003 should preserve/add sidecar/native-adapter components or adapter-specific schema rules;
5. later TDD must prove sidecar entities resolve through ontoTF without fake `oslots`;
6. forcing current ORACC zero-span data into TF is rejected merely because earlier sidecars existed.

The replacement contract is simpler:

```text
semantic request
    ↓
reviewed ontoTF semantic mapping
    ↓
materialized TF / Context-Fabric node, feature, edge, slot-set constraint
    ↓
native Context-Fabric execution
```

Synthetic/empty technical slots and other corpus-specific anchoring choices are materializer outputs whose semantics ontoTF may preserve, not reasons to add a storage adapter.

## What remains outside baseline

Data genuinely outside a TF/Context-Fabric graph/API contract is not automatically a ontoTF runtime concern. It may remain source/provenance/publication material owned by the corpus or materializer.

A generic outside-TF query/storage abstraction requires a separate architecture ticket and at least two independent real corpus cases showing that:

- required queryable semantics genuinely must stay outside TF/Context-Fabric;
- materializing them is technically or semantically inappropriate rather than merely inconvenient;
- both cases justify one common abstraction;
- materializer-side alternatives were evaluated;
- failure, provenance, packaging, synchronization and security contracts are defined.

No current seven-pilot ontoTF evidence meets that threshold.
