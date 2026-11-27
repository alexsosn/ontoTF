# A-001 research: TF-native runtime boundary

**Issue:** #65  
**Recorded:** 2026-09-07  
**Status:** research complete; design/contract correction pending

## Question

Does baseline ontoTF need a generic `sidecar` / `native-adapter` runtime abstraction for queryable corpus data, or should source-format ingestion remain entirely upstream in corpus-specific materializers?

## Conclusion

Baseline ontoTF should be **TF-native**.

ontoTF consumes already-materialized Text-Fabric / Context-Fabric corpus structures plus ontoTF semantic artifacts. It should not define a generic external-storage carrier, adapter capability, sidecar field/path selector, arbitrary source-record addressing API, or runtime fetch layer.

No current seven-pilot evidence requires such a runtime abstraction. The only concrete rationale that had entered R-005/R-007/P-002 came from an older ORACC-TF zero-span/sidecar design, and that design has been explicitly superseded by ORACC-TF ADR-0001.

The correction is therefore scope reduction, not replacement with a differently named adapter framework.

## 1. Product boundary

The architecture boundary should be:

```text
source formats
(JSON / XML / CSV / TEI / PDFs / databases / upstream APIs / etc.)
        ↓
corpus-specific materializer / converter
        ↓
materialized TF / Context-Fabric corpus
        ↓
ontoTF semantic mapping/profile/ontology layer
        ↓
Context-Fabric native query execution
```

ontoTF should know the native TF graph semantics it resolves against. It should not know which source format, database, archive, or transport produced that graph.

This is also a responsibility boundary: ORACC-TF owns ORACC ingestion, CUC conversion owns CUC source ingestion, and other materializers own their own source representations.

## 2. ORACC-TF invalidates the original sidecar rationale

Accepted ORACC-TF `docs/reference/architecture/ADR-0001-empty-slots-not-sidecars.md` states:

- textual source entities with an independent source position/order and no ordinary semantic slot remain inside the TF warp;
- explicit empty/synthetic slots are technical positional anchors, not fabricated cuneiform signs;
- ancestors reuse descendant anchors;
- zero span alone is not sufficient reason for a sidecar;
- the earlier `zero-span.json` / sidecar approach for ORACC textual nodes is superseded;
- any remaining sidecar must be justified by data genuinely outside the TF graph/API contract.

ORACC-TF issue #37 likewise says the earlier sidecar-first treatment was replaced with explicit empty/synthetic slot anchoring.

Therefore ontoTF must not cite ORACC zero-span mechanics as evidence for a generic external carrier.

## 3. Current ontoTF pilot evidence is already TF-native

Merged R-011's current ORACC pilot pin explicitly records that it was refreshed against the active ORACC-TF contract after ADR-0001 and that R-005 is historical input rather than the current zero-span architecture.

The R-011 pilot mappings resolve through ordinary TF selectors/features/edges. Representative examples include:

- BHSA `F.sp`, `F.nu`, `F.otype`, `F.gloss`;
- CUC `F.otype`, `F.usign`, `F.cert`;
- Pseudepigrapha TF nodes/features/edges for versions, manuscripts, readings and witness relations;
- ORACC `F.otype` plus TF catalogue features such as `material` and `period`;
- TLHdig TF node/feature/edge selectors.

The ORACC pilot specifically models catalogue `material` and `period` as native TF node features, not external-record adapter lookups.

R-011 therefore supplies no empirical requirement for ontoTF-side arbitrary JSON/XML/database/API addressing.

## 4. Where the unsupported abstraction entered ontoTF

### R-005

R-005 was recorded before the current ORACC-TF empty-slot decision and describes a modelling regime containing `non-textual or zero-span entities` that may live outside the TF warp. That statement is useful as historical census context but is no longer sufficient architectural evidence for current ORACC zero-span handling.

The correction should not rewrite history as though R-005 never observed the earlier design. It should clearly mark the relevant ORACC sidecar inference as superseded by the later accepted ORACC-TF ADR.

### R-007

R-007 currently promotes a separate carrier dimension:

```text
tf-node
sidecar / native-adapter
```

and says ORACC catalogue/object entities may resolve through `carrier=sidecar/native-adapter` rather than TF nodes.

That is now too strong. The structural lesson that storage shape must not fabricate semantic extent remains valid, but the generic external carrier does not follow from it.

R-007 should retain TF-node structural distinctions such as ordinary textual extent, occurrence sets, and technical anchors, while removing the baseline `sidecar/native-adapter` carrier requirement.

### P-002 #37 / PR #64

The open P-002 research/plan goes further and would freeze the abstraction into a future validator contract:

- dependency kinds `adapter-capability` and `native-field` / `sidecar-field`;
- carrier kind `tf-node | native-adapter`;
- selector families for adapter-side `native-field` / `native-entity` addressing.

These are not projection-neutral facts if baseline ontoTF does not own external storage. They create a new runtime/data-access surface without a demonstrated pilot requirement.

P-002 should remove these kinds and keep only TF/materialized-corpus dependency mechanics.

## 5. Correct structural distinctions

The useful distinction is not `TF vs sidecar`; it is semantic interpretation of materialized TF structure.

For TF-native entities ontoTF may need to preserve reviewed distinctions such as:

- ordinary textual/inscriptional extent;
- occurrence sets for abstract nodes such as corpus lexemes;
- technical anchors whose slots exist only for graph addressability;
- synthetic/empty slots representing a source position without a semantic sign;
- nodes with no semantic textual extent where the TF corpus model still represents them as graph nodes.

A synthetic empty slot is still a TF slot. It must be distinguishable from a semantic source sign, but it does not require an external carrier abstraction.

Storage location is not a semantic carrier type.

## 6. External identifiers and authorities are not adapters

R-017-style identifiers remain legitimate:

- source identifiers;
- catalogue identifiers;
- ontology IRIs;
- authority URIs such as AAT/PeriodO where reviewed;
- provenance/evidence URIs.

Their presence does not authorize ontoTF to fetch or parse the referenced resource at runtime.

A mapping can use an external URI as identity/provenance/semantic reference while execution still resolves entirely to native TF constraints.

## 7. Why generic adapter support is a poor baseline default

Adding generic external-record support would require decisions unrelated to ontoTF's core semantic-compatibility mission:

- source protocols and transports;
- JSON/XML/CSV/database parsing;
- record identity/path syntax;
- caching and invalidation;
- network failure semantics;
- authentication/credentials;
- schema drift;
- packaging/distribution of auxiliary stores;
- synchronization between TF and external records;
- provenance of fetched bytes.

Those concerns belong to materializers or dedicated data-access systems unless real corpus evidence proves otherwise.

Introducing the abstraction pre-emptively would increase validation, IR, resolver, packaging and security complexity for a feature no current pilot needs.

## 8. Extension threshold

Baseline ontoTF should include no generic external-storage runtime abstraction.

A future extension may be researched only when at least **two independent real corpus cases** demonstrate all of the following:

1. query-relevant semantics genuinely must remain outside TF/Context-Fabric;
2. materializing those semantics into TF is technically or semantically inappropriate;
3. the two cases share enough execution/storage semantics to justify a common abstraction;
4. materializer-side alternatives have been compared;
5. the extension has explicit failure, provenance, security and packaging contracts.

One corpus-specific convenience or a zero-span workaround is insufficient.

## 9. Required architecture corrections

1. Mark the superseded ORACC sidecar inference in R-005 as historical/non-normative.
2. Amend R-007 to remove `sidecar/native-adapter` as a baseline structural carrier and update its ORACC stress case to the accepted synthetic-empty-slot architecture.
3. Amend P-002 #37 / PR #64 so dependency kinds and selector contracts do not contain adapter/sidecar-specific mechanics.
4. Add the TF-native boundary to P-003 #44 non-goals/design constraints before final architecture is frozen.
5. Add contract tests preventing generic adapter/storage semantics from re-entering baseline architecture without a separate reviewed extension.

## 10. Non-goals

A-001 does not forbid:

- corpus repositories from containing auxiliary files;
- converters/materializers from reading any source formats they need;
- external identifiers/URIs as semantic/provenance values;
- publication/export artifacts outside TF;
- a future evidence-backed external-data extension.

It forbids treating those possibilities as a baseline ontoTF runtime responsibility without evidence.
