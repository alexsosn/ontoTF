# I-034C: blocked real OLiA positive mapping publication — source analysis and TDD plan

Parent: #303 / #283 / PR #343. Protected run [38169884713](https://github.com/alexsosn/ontoTF/actions/runs/38169884713) authenticated all fifteen source-bound decisions including twelve real OLiA POS-class mappings but failed the accepted-only handoff with `REJECTED: unsealed new evidence path malformed`.

## Research grounded in production code

`build_overlay_handoff` pulls the real nine OLiA `owl:Class` records referenced by exact-mapping proposals. Since these are not part of either corpus's old v0.4.0 profile `base.evidences`, it correctly adds them to `corpora[].added_evidence` with paths such as `resources/ontologies/olia/<pinned-sha>/i034a-article-evidence.json`. Those immutable files were merged as real original-source records in PR #341: same OWL blob, exact class declaration line, valid `license_ref`-bound digest, and the broadened immutable terms_used lock now exist **on protected main**.

`verify_overlay_handoff_integrity` lines 263–270 erroneously restrict **all** added evidence to `resources/profiles/<corpus>/...`; this assumption held for prior native-only prototypes, but rejects source-authenticated ontology evidence. We must not suppress this validator or accept arbitrary PR-head ontology records.

## Minimal supported case and security

Continue allowing supplementary corpus source records only in their original corpus prefix. Also allow ontology class evidence **only in the exact directory of the verified, protected installed ontology lock**, and only when:
- resource name is a safe normalized `.json` path and already exists as an installed protected-main resource;
- record equals `packaged_resource(name)` byte-for-byte semantically (no candidate replacement);
- `kind=ontology-definition`, revision/source URI, snapshot digest and target agree with the already validated lock;
- original evidence digest matches the normalized record; the existing mapping validator separately requires one exact target from the same locked set and matching mapping/ontology evidence IDs.

A matching resource from an unrelated corpus, other ontology revision, nonexistent candidate path, or tampered/rehashed record must still fail closed. Do not add new workflow, review process, or per-entity ticket.

## TDD gates

1. Commit RED test using the **real 15-row BHSA/Syriac POS ledger** from #341 and pinned supplemental source records. Derive genuine packet from compiler; use an explicitly *unauthenticated* in-test synthetic review observation for 15 accepts, produce the pack, and demand that the existing verifier accepts the immutable class evidence. This test **currently fails** due to the path gate.
2. Negative cases mutate the added class resource path or record, recompute pack digest and ensure verifier rejects. Unrelated non-ontology candidate supplemental records remain valid as before. Test ensures 12 real positive projections, 3 native-only and 15 review rows, no invented signed release.
3. Change the existing validator narrowly. Run full exact-head Python 3.10/3.12 CI. Skeptical same-agent adversarial review must verify origin, namespace/path traversal, fake ontology record, class target/revision mismatch, and old native-only handoff nonregression. Merge only after exact-head checks green.
4. Re-run the pre-existing two-review protected GitHub handoff on still-open PR #343, **without** changing semantic review decisions. This is repair of blocked genuine positive mappings, not infrastructure proliferation.
