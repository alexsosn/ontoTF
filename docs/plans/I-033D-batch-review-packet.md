# I-033D plan: content-bound batch review requests

**Issue:** #298. **Research:** `docs/research/I-033D-batch-review-packet.md`.

1. Research: inspect `batch_proposals.py`, the canonical JCS digest implementation, ADR-001 and four real source-backed POS candidates. Confirm Mapping V2 intentionally ignores rationale.
2. TDD RED: require `tfont.review_packets.build_review_packet`, `verify_review_packet`, reproducible frozen fixture and an offline `scripts/mappings/build_review_packet.py --check`; tests fail first.
3. GREEN: produce a deterministically sorted packet of digest-bound row summaries with source pins/evidence/selector/target/relation/rationale and coverage intent, plus individual full-candidate commitments and a batch digest; compute with `canonical_json_bytes`.
4. Threat checks: rationale edits change review digest (mapping semantic digest remains identical); source evidence substitution, altered native selector/ontology class, duplicate row, unrecognized/forged review flags fail; reordering ledger decisions leaves output unchanged; forged packet hashes and altered packet rows fail verification.
5. Authority boundary: `release_authorized=false`; no reviews, receipts, tokens or reviewer identity emitted; candidate packet cannot pass production Mapping v2 validation, no coverage/profiles edited.
6. Full repo discovery/pytest/wheel exact-head CI and independent skeptical source/code review, then expected-head merge. No new workflow YAML.
7. Follow-on: independently authenticated GitHub/PR-level per-row review receipts and a declarative incremental pack writer must *consume* this packet, never be bypassed by candidate self-declarations.
