# I-026 plan — deterministic P-004 semantic accounting work queue

**Issue:** #263  
**Parent:** P-004 #202  
**Research:** `docs/research/I-026-semantic-accounting-work-queue.md`  
**Baseline:** `main` `cf292481c67b798d4485c0e178b2e2fb83340cbd`

## 1. Exit condition

A repository-local deterministic builder expands the seven current immutable coverage manifests into an item-level queue with:

- exactly 934 semantic rows;
- exactly one primary C-H owner for every row;
- no technical exclusions in the semantic queue;
- exact denominator digest/revision binding;
- preserved prior production/research accounting;
- a separately routed Syriac `ls="prop"` outside-denominator gap;
- deterministic per-corpus/workstream counts;
- zero orphans and zero duplicate owners.

The artifact is governance/accounting data only. It creates no ontology mapping authority.

## 2. Files

Add:

- `docs/research/data/i026/p004-routing-policy.json`
- `scripts/coverage/build_i026_work_queue.py`
- `docs/research/data/generated/i026/p004-work-queue.json`
- `tests/i026/test_work_queue_red.py`
- `tests/i026/test_work_queue_adversarial.py`
- `.github/workflows/i026-work-queue.yml`

No production package module or public API is required.

## 3. Policy contract

The routing policy pins, per corpus:

- manifest path;
- corpus repository;
- denominator digest;
- denominator source revision;
- target revision;
- evidence source path;
- exact route allowlists by native item family;
- H sub-bucket allowlists where evidence justifies them;
- expected per-workstream counts.

Global policy pins:

- schema version;
- expected aggregate semantic count = 934;
- expected aggregate technical exclusions = 15;
- workstream → owner issue/profile mapping;
- corpus processing order;
- explicitly routed accounting gaps.

Only base native identities appear in allowlists:

- node type name;
- node feature name;
- edge feature name.

Values inherit the route of their feature/edge. This prevents hundreds of duplicated policy entries and guarantees that a closed value family cannot accidentally diverge from its feature owner.

## 4. Generated row contract

Each semantic row contains:

- `corpus_id`;
- `item_id`;
- `kind`;
- `workstream`;
- `owner_issue`;
- `candidate_profiles` using only controlled R-014 profile IDs;
- `candidate_capabilities` using only controlled R-014 capability IDs;
- `routing_bucket`;
- `routing_basis`;
- `evidence_source`;
- `evidence_pointer`;
- `existing_accounting` copied from the manifest.

The profile/capability lists are review ownership envelopes: they identify the controlled semantic contracts the downstream workstream must consider. They do not activate a profile/capability and do not assert that every row belongs positively to every listed capability. H `cross-model` word-domain rows use the controlled `structural.entity-kind` envelope; H `native-only-candidate` rows deliberately use empty profile/capability lists rather than falsely classifying source/provenance metadata as structural semantics.

No row contains a newly invented mapping assessment.

The top-level artifact contains:

- schema version;
- policy identity;
- exact manifest bindings;
- rows;
- per-corpus and aggregate counts;
- technical-exclusion counts/IDs;
- separately routed accounting gaps;
- invariant summary.

## 5. Evidence pointers

Builder derives evidence pointers mechanically:

- node type → `/node_types/<name>`;
- node feature → `/node_features/<name>` where the evidence object exposes node-feature records;
- TLHdig node feature → exact index in `/core_node_features/<n>`;
- edge feature → `/edge_features/<name>`;
- node/edge value → parent feature/edge evidence plus the denominator-policy source when closure is policy-backed.

The pointer is traceability, not a semantic proof.

## 6. H bucket assignment

Policy may mark exact H identities/families as `cross-model` or `native-only-candidate`.

Otherwise H defaults to `needs-focused-research`.

If prior selected accounting already has exactly one assessment in `native-only|unsupported|ambiguous`, the generated H bucket may reflect that prior reviewed state, but the existing accounting object remains authoritative and unchanged.

## 7. Syriac gap

The policy carries the exact current manifest gap object for `node_value:ls="prop"` plus:

- C / #264 ownership;
- evidence pointer to Syriac `ls`;
- `outside-denominator` reason;
- no addition to the 934 semantic-row total.

Any unexpected additional accounting gap fails the build until explicitly routed.

## 8. TDD sequence

### RED 1 — artifact shape

Tests require policy, builder and generated artifact and assert:

- seven corpus bindings;
- 934 semantic rows;
- 15 technical exclusions;
- exact expected C-H aggregate counts;
- exact per-corpus counts.

### RED 2 — ownership integrity

Tests assert:

- unique `(corpus_id,item_id)`;
- exactly one owner/workstream per row;
- no workstream outside C-H;
- no semantic/technical overlap;
- all manifest semantic IDs represented exactly once.

### RED 3 — adversarial drift

Mutation tests must reject:

- changed denominator digest/revision;
- duplicate/removed row;
- absent route allowlist member;
- feature-value inheritance without parent feature;
- technical item injected into semantic rows;
- missing Syriac accounting-gap route;
- duplicate primary route for one base identity.

### GREEN

Implement the smallest offline builder satisfying those contracts. It reads committed JSON only and never accesses the network.

## 9. CI

Add a focused workflow triggered by I-026 policy/builder/generated/test/manifests changes:

1. checkout exact PR head;
2. setup Python 3.10 and 3.12;
3. run `python scripts/coverage/build_i026_work_queue.py --check`;
4. run `python -m unittest tests.i026.test_work_queue_red tests.i026.test_work_queue_adversarial`.

The existing full repository suite remains the merge gate.

## 10. Review gate

Fresh independent review must challenge:

- whether routing accidentally asserts ontology equivalence;
- whether source evidence supports the *ownership* assignment;
- whether any corpus-specific semantic family is routed to the wrong layer;
- whether H hides work rather than making residual work explicit;
- whether counts can stay green after denominator drift;
- whether the Syriac gap can disappear silently;
- whether technical exclusions can inflate completion.

Material route-policy changes after review require a fresh review.

## 11. Handoff

After merge:

- #264 and #265 become the next actionable P-004 tickets;
- C and D may proceed in parallel;
- #266 waits on their required semantic boundaries;
- no R-021–R-026 exploratory research is selected unless an actual P-004 blocker requires reopening it.
