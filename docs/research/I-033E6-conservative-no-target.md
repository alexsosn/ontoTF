# I-033E6 — native-only batch proposal and review semantics

Ticket #312; parents #300, #303, #290. Research grounded in `main@0df31a5`, pinned BHSA `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da/docs/features/sp.md` and source/coverage records.

## Observed bottleneck and critical distinction

`batch_proposals.compile_candidate_batch()` requires `term_key` and exact class for every decision; `review_packets.build_review_packet()` requires exactly one projection, so a source-reviewed decision to **not** attach an ontology target cannot be captured and independently adjudicated. Current Mapping v2, however, explicitly allows `native_state=native-only` and zero projections. Historically BHSA 27 verbal-stem `node_value:vs=...` and parent feature were **coverage-only** native-only dispositions, not Mapping v2 records. They cannot be reinterpreted as 27 already-published mappings.

## Boundary and chosen option

Support a narrowly scoped *unreviewed* `native-only` **word-level POS value** proposal in v2 ledger and packet. The decision is a new Mapping v2-shaped proposal with `native_state=native-only`, empty `projections`, `ambiguous_candidates` and `external_references`, one source-evidence binding, digest-bound rationale and a stable native selector ID (`mapping:{corpus}:native-sp-{value}`). It creates no OLiA target, ontology evidence, common-target authority or publication right. It is **not** a conversion of historic BHSA verbal-stem accounting. That legacy cohort stays immutable and can be imported into a separate accounting-only decision pipeline later.

Versioning: existing ledger/packet schema v1 and its four exact pilot rows remain byte-identical. New ledger v2 permits either `{corpus_id,value,term_key,assessment=exact,rationale}` OR `{corpus_id,value,assessment=native-only,rationale}`; no `term_key` key (even null) is allowed in no-target rows. Packet schema v2 includes `ontology_target=null`, `formal_kind=null`, `projection_semantic_digest=null` for native-only (all keys present), a native feature/value binding, and the source-only evidence; its decision digest binds the full candidate, corpus source pin, batch identity and coverage item. No change to reviewer protocol: independent GitHub approvals refer to packet + row digests, not targets.

The proposal source is the same closed, normalized and digest-checked POS evidence as exact rows; candidate supplemental evidence may provide additional original-source definitions, with `CandidateEvidenceResources` checking installed corpus pins and the external protected ingestion. The first real example is BHSA `sp=prps` = personal pronoun at pinned source line 24, 5,035 feature observations in R-005 (feature also applies to lex, so not automatically word-token count). Selecting native-only **does not assert** no possible OLiA pronoun class; it records a conservative pending disposition requiring independent scholarly review. Never promote this as current production coverage without the protected publisher.

## Threat model

- A ledger or recomputed packet digest cannot inject a target/projection into native-only or self-review it.
- A target synonym inferred from the abbreviation `prps` cannot count as exact.
- No-target decision must retain corpus identity, native binding, verified source digest and scholarly rationale.
- Review must use same packet schema v2 through locally reproducible and protected live second-pass revalidation; v1 fixture unchanged.
- External `reject` and `needs-evidence` are not release acceptance. Existing approval evaluator only returns eligibility, not a publication receipt.
- Existing historical native-only coverage cannot be deleted/reclassified through this candidate compiler; this PR does not mutate production coverage or releases.
- No per-item workflow, no copied profile tree. The existing consolidated release pipeline tests both schemas.

## Alternative rejected

A zero-projection mapping with `assessment=exact`, a synthetic ontology class, or invented ontology evidence misstates scholarly authority. A coverage-only row inside the candidate compiler would duplicate accounting logic with no native execution binding. A full generic native-feature/addressing abstraction would be premature and bypass pinned POS-specific evidence gates.

Acceptance: v2 mixed exact/native-only batch, stable source-bound independent packet, preserved v1 artifacts, negative and mocked protected-gate tests, final-head Python 3.10/3.12 full CI and skeptical PR review. No production coverage growth claim.
