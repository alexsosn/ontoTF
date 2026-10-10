# I-033E2: immutable published-release deltas, parity before new authority

Parent #300 and #290. This is **phase-2 foundation**, not a claimed release of any unapproved POS candidate.

## Observed duplication and needed boundary
The published BHSA 0.3.0→0.4.0 transition added two source-reviewed mappings (adjective/adverb) but copied noun, noun-morphology, verb mapping files and parent-component manifest into another full version directory. The existing registry can load *both* immutable bundles and their real evidence; it does not yet express `base release + additions` without copied JSON.

The available `review_packets.py` produces unreviewed, rationale-bound candidate packets; `external_review_gate.py` validates **caller-supplied review snapshots only** and `check_external_review.py` can fetch live GitHub state from a protected context. Neither a packet checksum nor JSON flags constitute independent approval. No *new* mapping may enter production through this migration parity step.

## Minimal architecture slice
Build an **offline delta compiler for already published, validated** registry releases. Start with BHSA and Syriac 0.3.0→0.4.0: identify only newly added mapping IDs and native dependencies, new evidence references and new ontology lock, while strictly comparing unchanged inherited mapping records and their source authority. Emit a compact immutable overlay manifest (one per cohort), not another clone of 200+ coverage rows, and reproduce the validated final SemanticSourceBundle from the published target. Provide a reader that verifies the overlay against the approved published source/target release resources every time; fail if a "new mapping" has no published target attestation.

This establishes the delta format and deterministic proof of parity. It does **not** authenticate new PR approvals, mint a signed release receipt, enable arbitrary local reviewer JSON to publish, or silently change `load_profile` aliases. Those remain mandatory separate release-gate responsibilities for #300.

## Threats
- Base catalogue drift and cross-corpus references; mapping substitution under an identical ID; silent deletion of a prior review; stale or forged digest; dependency de-scoping or source-evidence removal; unsupported new ontology model.
- Treating native-only dispositions as OLiA exact or counting unchanged rows as new production coverage.
- Declaring an unreviewed I-033C candidate "published" because its JSON resembles a reviewed Mapping V2 file.

## Acceptance
One deterministic generic module and focused adversarial tests, no new per-feature workflow, immutable published v0.1.0–v0.4.0 behavior preserved. A 2-row adj/adv delta is representable as a handful of references plus only changed records; reconstructed semantic indexes equal the target historical release and historical base remains unchanged. Full exact-head CI plus independent skeptical review.

**Deliberate constraint:** This compiler can emit only from two *existing published releases* validated against the installed registry; new independently attested release publishing (accepted 10–50 row cohorts) is the next gated phase and cannot be forged by supplying a local review JSON.
