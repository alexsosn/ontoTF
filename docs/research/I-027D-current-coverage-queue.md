# I-027D research — current production accounting without rewriting history

**Issue:** #286; Workstream C #264; P-004 #202.

## Verified failure mode

`docs/research/data/i026/p004-routing-policy.json` is a frozen `p004-routing-v1` research/review contract. Its `corpora[corpus].manifest` fields still select historical baseline manifests for BHSA, Syriac and ExtraBiblical. The supposedly authoritative `docs/research/data/generated/i026/p004-work-queue.json` therefore embeds old `existing_accounting` layers, not newer reviewed dispositions. Historic reporting is internally consistent, but it is **not** a reliable current-production progress source.

The actual source manifests have been independently inspected:

| Corpus | Original reviewed / semantic | Latest reviewed / semantic | Shared OLiA exact target | Denominator |
|:--|--:|--:|--:|:--|
| BHSA | 7/219 | 35/219 | 8 | sha256:0b260e21... |
| Syriac | 6/74 | 7/74 | 7 | sha256:33ea9d6c... |
| ExtraBiblical | 7/136 | 8/136 | 8 | sha256:58bdaddd... |

BHSA latest includes **27** I-027A reviewed `vs` native-only dispositions; these are not OLiA common targets. `sp=verb` adds one exact common target per corpus, not one for every word node.

Latest packaged successor paths:
- `src/tfont/resources/coverage/p004-i027b1-bhsa-verb-v1/bhsa.json`
- `src/tfont/resources/coverage/p004-i027b2-syriac-verb-v1/syriac.json`
- `src/tfont/resources/coverage/p004-i027b4-extrabiblical-verb-v1/extrabiblical.json` (pending PR #282 until merged)
Other four corpora should retain the exact manifest paths selected by original I-026 policy.

## Architectural choice

**Do not replace** the I-026 output or its routing policy. Publish a separately versioned `p004-current-v1` progress view built from an **explicit reviewed manifest selector**. Reuse `scripts/coverage/build_i026_work_queue.py::build_queue(policy=...)` to preserve existing routing semantics, counts, orphan checks, evidence pointers and context. Its policy_id still validates as `p004-routing-v1`: that is the underlying *routing rules version*, not the freshness claim.

The new wrapper owns:
- explicit source manifest references for all seven corpora, the historical policy digest/provenance and immutable routing semantics;
- strict baseline-vs-selected corpus revision and denominator identity equality, exact unchanged semantic item IDs/kinds, technical exclusions, research accounting, outside-denominator accounting gaps and reviewed-production monotonicity;
- static per-corpus expected production counts and the three-corpus `exact` Verb + BHSA `vs` family review pins;
- a `current_coverage_version` and an output path separate from `i026/p004-work-queue.json`, so historical evaluations never change as review progresses;
- no semantic pivot inference. Counts distinguish reviewed native-only production dispositions and reviewed shared/common-target exact pivots.

The three chosen manifests should be treated as explicit release decisions: don't lexically guess a successor by filename or timestamp.

## Important test risks

A naive count-based reconciliation is vulnerable to losing one previously approved source binding and adding a different one, or escalating `native-only` to `exact` without separate new review. Require per-item monotonic accounting and fixed semantic item identity sets across every published successor. A hash identical to the baseline denominator does **not** alone guarantee equal research/evidence metadata; compare the actual rows and gap lists.

A selected manifest must not silently acquire an out-of-denominator gap or technical exclusion, even if per-corpus number of semantic rows still matches. Routing counts must remain C 380, D 67, E 153, F 161, G 39, H 134; 934 semantic rows and 15 technical exclusions overall.

## Research conclusion

GO for an opt-in, explicitly versioned *current* queue once PR #282 is merged and its source manifests are actually present on `main`. Do not assert current progress before exact-head CI on this new queue. Keep I-026 historical queue reproducible.
