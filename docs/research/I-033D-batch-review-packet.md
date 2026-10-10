# I-033D — source-locked batch review packet

**Issue:** #298 (parent #290). **Architecture:** ADR-001.

## Observed limitation in released code

`src/tfont/batch_proposals.py` already compiles four approved-shape-but-unapproved candidate Mapping v2 records from the compact POS ledger. The output includes exact native selectors, content-bound evidence, ontology class locks and correct semantic mapping/projection digests, but deliberately omits `review` fields and has `release_authorized=false`.

`semantic_digest_v2.py` excludes audit-only `rationale` and `review` from mapping semantic digests. A scholarly argument can change while the technical semantic projection hash remains identical. That is correct for runtime cache stability, but a new review gate **must** include the rationale in a separately versioned content commitment.

## Chosen design

One review *request* packet for up to 50 source-pinned proposals. For each row, bind the **entire original candidate object** including rationale and its computed Mapping V2 + Projection V1 digests, explicit corpus source revision and target TF revision, ontology model/snapshot, and the exact `node_value` coverage ID selected by `word.sp=value`. Hash via the repository's strict `rfc8785` canonical JSON bytes. The row digest must be computed, not accepted from ledger declarations.

Publish a separate batch commitment binding all row IDs/digests, batch identity, source registry, ontology revision and deterministic sorted order. This catches:
- rationale text changes invisible to the V2 semantic digest;
- source/target revision or evidence digest edits;
- mapping selector/assessment/target drift;
- moving decisions across packet identities or dropping one member.

The packet **never asserts a reviewer identity or successful review**. The only carried state is a fixed `release_authorized=false`. The packet is not a Mapping v2 production artifact, and no user-provided `review`, `reviewed`, `approved_by`, `review_receipt` fields are permitted. The next phase must verify external independent attestation against these exact commitments and emit immutable release deltas, not trust a handwritten flag.

## Corpus and ontology boundaries

Keep BHSA and Syriac independently bound to the real pinned source evidence; Syriac original `linksyr` grammar revision differs from target Text-Fabric revision. The pilot only builds existing 4 adjective/adverb positive candidates and changes no runtime profile or P-004 denominator. This narrow cohort tests the packet protocol; it does **not** confer new approvals or resolve non-OLiA adapter design.

## Outcome sought

One non-bespoke batch review artifact with every decision's source selector → ontology class, rationale, evidence and expected coverage ID, suitable for one skeptical reviewer. No per-mapping PR, workflow, hand-maintained digest, version bump, or profile copy.
