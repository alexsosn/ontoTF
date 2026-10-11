# I-033E7 — protected handoff design

1. Pure deterministic assembler takes a reproducible packet/ledger/resource
context and a review **observation**, never treating supplied JSON as authority.
Require 10–50 accept rows. Rebuild packet, check exact row digest set, reference
immutable current installed base versions and frozen pilot coverage. Reject
already reviewed selectors/items, missing denominator IDs, source identity drift
and inherited dependency/evidence replacement. Emit only additions and references,
not cloned parent/profile/old mappings or full denominator. Content digest binds
all data including all reviewer dispositions. Separate exact/native-only counts.
2. Handoff mappings remain unreviewed; no arbitrary handoff loader or reviewed
flags. authority is requires-workflow-attestation-and-registry-validation and
release_authorized false. Evidence and dependencies are deduplicated per corpus.
Base digest uses existing canonical published-bundle digest function; coverage
reference binds whole immutable manifest digest and denominator digest.
3. Protected CLI --publish-handoff only with --from-pr-head. Fetch source DATA,
evaluate live review, assemble, evaluate live review again and require identical
observation. Exclusively create fixed batch-review-pack.json with no caller path;
no write if any gate fails; no overwrite/symlink following. Normal CLI unchanged.
4. Existing protected workflow gets an opt-in publish job requiring both
ontology-batch-review and ontology-batch-publish labels. Pin protected-base event
commit github.sha so executed code matches signing source provenance;
fresh live gate in that job, job-scoped id-token/attestations write only. Attest
exact fixed pack bytes with pinned official action, then immutable upload.
No contents-write, PR checkout, new workflow, local receipt or token forwarding.
5. RED→GREEN actual-source tests: ten new conservative categories, partial
acceptance, minimum bound, inherited exact/native-only protection, deterministic
compact additions, forged observation/packet, source drift, no overwrite, head
or review revocation at final check, offline option refusal and workflow boundary.
Existing historical suites plus exact-head 3.10/3.12 full/wheel gates. Fresh
independent adversarial review before expected-head merge.
