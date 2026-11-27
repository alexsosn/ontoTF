# P-001 amendment: TF-native runtime boundary

**Authority:** A-001 #65  
**Recorded:** 2026-09-07  
**Applies to:** `docs/plans/P-001-foundation-poc-design.md`  
**Status:** normative amendment; historical P-001 remains unchanged

## Decision

P-001 remains the accepted historical foundation for component-aware parent identity, deterministic source/evidence handling, compatibility reporting, review binding and fail-closed activation. A-001 narrows one part of that design after later corpus evidence invalidated the original external-carrier rationale.

**P-001 sections 6 and 7 are superseded only where they treat external/native sidecars, zero-span stores, or `native-adapter` artifacts as executable native query carriers or define adapter/sidecar-specific query dependencies.**

Baseline executable resolution is now:

```text
reviewed common/native semantic request
        ↓
materialized Text-Fabric / Context-Fabric node, feature, edge and slot constraints
        ↓
native Context-Fabric execution
```

Corpus-specific materializers own source-format ingestion. Storage location or source format is not a semantic carrier type.

## 1. Identity compatibility is not query-carrier authority

P-001 originally used one component vocabulary for two concerns that must now be separated:

1. **parent/component identity compatibility** — identifying bytes or release artifacts that belonged to an older reviewed parent/profile contract;
2. **executable/query carrier semantics** — identifying the native structures to which a ontoTF semantic request may compile.

A component record can be retained while reading an old parent manifest without becoming an executable selector surface.

The current v1 parent-component schema structurally accepts `sidecar`, `catalogue`, `zero-span`, and `native-adapter`. For A-001 these are **legacy identity compatibility labels** when encountered in existing v1 artifacts. Their **structural acceptance does not authorize an executable/query carrier**, an adapter, a file/record/field selector, URI dereferencing, or external data fetching.

For new post-A-001 baseline designs, executable corpus constraints are TF/Context-Fabric-native. An external identifier, catalogue identifier, authority URI, evidence URI or provenance record may still be carried as a reviewed value/reference without becoming a storage backend.

## 2. P-001 section 6 supersession

The P-001 list of supported POC component kinds is no longer an executable-carrier enumeration.

Specifically:

- `native-adapter` is **not a baseline executable** carrier;
- `external/native sidecar`, `catalogue`, and `zero-span` labels in an old v1 manifest do not by themselves create a queryable native component;
- textual zero-span data does not use an external zero-span store in the current ORACC model merely because ordinary semantic slots are absent;
- independently positioned textual zero-span entities are materialized through explicit **synthetic/empty** TF slots under ORACC-TF ADR-0001;
- synthetic/empty slots are technical positional anchors and must not be published or counted as semantic source signs;
- genuinely non-textual TF nodes may use occurrence/locus or documented technical anchors without fabricating semantic textual extent.

P-001 section 6.1's byte-identity mechanics remain historical compatibility rules for artifacts that used those component labels. They do not define a runtime query API.

P-001 section 6.2's negative compatibility principle also remains valid in general: when an artifact is part of the declared reviewed parent identity, changing it can invalidate `verified-exact`. That identity consequence is distinct from permission to query the artifact directly.

## 3. P-001 section 7 supersession

The following P-001 dependency interpretations are superseded for baseline execution:

- `sidecar-zero-span` as an executable extent interpretation;
- `adapter capability/version invariant` as a baseline executable dependency kind;
- `sidecar field/path invariant` as a baseline executable dependency kind;
- any arbitrary external file/record/field/path selector introduced solely to address source storage outside materialized TF/Context-Fabric.

The phrase **adapter capability/version invariant** is retained here only to identify the superseded historical P-001 contract. The phrase **sidecar field/path invariant** is likewise historical and must not be implemented by P-002/I-004 as a baseline query dependency.

Still-valid TF-native dependency families include, subject to P-002/P-003 final versioning and shape decisions:

- component/profile identity needed for compatibility;
- node/entity type represented in TF;
- node feature/value represented in TF;
- edge/path represented in TF with explicit direction/value semantics;
- value-domain assertions that are reviewed rather than inferred from finite observation;
- TF structural extent/occurrence/technical-anchor semantics.

## 4. v1 source compatibility and versioned migration

A-001 is an architecture correction, not an unversioned rewrite of already-shipped v1 source acceptance. Therefore this PR does not mutate `src/ontotf/schemas/parent-component-manifest.schema.json` in place.

Until a reviewed migration lands:

- old v1 manifests remain structurally readable;
- their legacy component-kind labels carry identity/provenance compatibility only;
- no new mapping or dependency gains executable authority from `sidecar`, `catalogue`, `zero-span`, or `native-adapter` merely because the v1 schema accepts the string;
- downstream semantic/runtime work must fail closed rather than invent adapter behavior for such a label.

**P-002/P-003 own the versioned source-contract migration.** They must decide whether legacy labels are removed, replaced by explicitly non-executable identity/provenance roles, or isolated behind an old-version reader. They must not migrate those labels into a new generic external-storage query carrier.

Any I-004/P-003 resolver or validator work that would execute a legacy label before that migration is blocked.

## 5. Generated ontoTF runtime artifacts are not native sidecars

P-001 section 1 uses the phrase `runtime sidecar` for a **ontoTF-generated derivative** compiled from validated semantic IR. A-001 does not turn generated indexes/reference artifacts into corpus-native external query carriers.

That generated-artifact concept remains valid, though P-003 may rename it to avoid confusion with the superseded native-sidecar terminology. It is deterministic ontoTF output, not an arbitrary external source store.

## 6. Foundation contracts preserved

This amendment explicitly preserves:

- **component-aware parent identity**;
- **deterministic compatibility evidence** and report digests;
- **review/evidence binding** and stale-review invalidation;
- all four **compatibility states** (`verified-exact`, `verified-compatible`, `unverified`, `incompatible`);
- **fail-closed activation** and the rule that only sufficiently verified states execute;
- ontology locks and offline-reviewed evidence;
- deterministic source parsing/canonicalization contracts;
- protocol-independent semantic resolution;
- the distinction between technical anchors and semantic textual extent.

The correction removes unsupported external-data execution semantics; it does not weaken provenance, identity or compatibility validation.

## 7. Downstream consequence

P-002 #37 must implement only TF-native, semantic-shape-independent dependency plumbing and must remove `adapter-capability`, sidecar-field/path and equivalent external-record selector families from its current PR before merge.

P-003 #44 must compile shared semantic projections to already-materialized TF/Context-Fabric constraints. If future evidence demonstrates genuinely necessary outside-TF query semantics, a separate architecture ticket must satisfy the A-001 evidence threshold rather than reviving the P-001 adapter branch implicitly.
