# I-033E3 / #303 — ten-source-row candidate authoring

**Issue:** #303
**Research:** `docs/research/I-033E3-ten-source-pos-cohort.md`

1. **RED:** Add a repository regression asserting an actual candidate v2 manifest, a 10-row ledger, two non-shadowing supplemental native evidence records, a deterministic generated `review-request` packet, exact primary-source coordinates, no invented ontology projections and `release_authorized=false`. The first test is deliberately RED until all data files are committed.
2. **GREEN:** Author the ten distinct candidate dispositions and rationales; freeze new source evidence with valid normalized-record digest; build the review packet exclusively with the already-reviewed generic writer (`python scripts/mappings/build_candidate_review_packet.py --write`); commit packet bytes and then check with `--check`. Never recalculate or override an independent GitHub approval.
3. **Negative gates:** Check that mutating a line, rationale, source revision, packet digest, or external-review requirement invalidates the packet, evidence or published handoff. Old 0.4.0 profiles, mappings and coverage snapshots unchanged.
4. **Skeptical review:** Separate source-level audit of **every** selector, pinned URL and line, individual rationale, source evidence identity, candidate-only authority, and verifier compatibility. Fix material defects and repeat on exact head. Green two-version PR CI is required before merging any *non-attested tooling* but candidate release approval **still requires an independent authorized GitHub review and protected workflow attestation**.
5. **Do not conflate:** This PR can complete reproducible *input preparation* for 10 native selectors, but cannot close #303's independently approved publication and runtime/wheel demonstration merely by merging an unapproved packet. The batch PR should remain available for actual protected approval; no local reviewer impersonation.
