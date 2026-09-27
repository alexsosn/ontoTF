# I-016 research — seven-corpus semantic denominator and coverage manifests

**Issue:** #204  
**Parent:** P-004 #202, Workstream A  
**Baseline:** `main` `17a58ba09e5f0c9a9bf216d8a79face50312adca`  
**Status:** research

## 1. Question

P-004 defines completion as 100% reviewed/accounted semantic coverage inside a declared versioned denominator. The repository currently has two earlier mechanisms:

- R-005 generated TF inventories;
- R-011 raw-schema coverage over those inventories plus two curated manual denominators.

I-016 must determine whether those artifacts can support a production coverage claim and, if not, define the minimum versioned manifest/accounting contract needed before ontology-specific work continues.

## 2. Findings

### 2.1 The historical denominator is exactly reproducible

R-011's current raw-schema policy expands the five generated R-005 inventories as:

| corpus | node types | node features | edge features | bounded node-value items | denominator |
| --- | ---: | ---: | ---: | ---: | ---: |
| BHSA | 13 | 109 | 5 | 92 | 219 |
| CUC | 5 | 16 | 0 | 16 | 37 |
| Syriac | 4 | 31 | 0 | 39 | 74 |
| ExtraBiblical | 12 | 64 | 3 | 57 | 136 |
| TLHdig-TF | 16 | 107 | 9 | 5 | 137 |

R-011 additionally uses curated manual denominators:

- Pseudepigrapha-TF: 40 items;
- ORACC-TF: 42 items.

The total is therefore exactly **685** items, matching the accepted R-011 report.

This is useful as a historical baseline, but it is not yet a production coverage manifest.

### 2.2 Five denominators were machine-generated; two were curated

Current R-011 quality labels are:

- BHSA, CUC, Syriac, ExtraBiblical, TLHdig: `machine-exhaustive-for-r005-nonwarp-inventory`;
- Pseudepigrapha, ORACC: `curated-r005-baseline-not-exhaustive-generated-inventory`.

A curated denominator can measure progress inside its declared list. It cannot support a corpus-wide “100% covered” claim merely because every listed row has been reviewed.

This distinction must be machine-readable in the new contract.

### 2.3 The R-011 corpus pins are no longer uniformly current

Exact default-branch heads inspected during I-016 research:

| corpus | R-011 denominator/source pin | current default-branch head | state |
| --- | --- | --- | --- |
| BHSA | `4db00e2157915495e1a4d3d57e41223df24775da` | same | current |
| CUC | `ad69400f5446e1c8217af01659c7c10ab00c015b` | same | current |
| Syriac | `bb0eaa7e21b020a26b7566d2e495da9b1f84a919` | same | current |
| ExtraBiblical | `9a56288e6777bad6328856acf055c780e65dd5d9` | same | current |
| Pseudepigrapha-TF | `d098845043897957efee7a42ae4854deddd5a1bd` | `7c4b757bb543a110ae9a252d1281835859136852` | stale |
| ORACC-TF | `e8f2b160912e0adaa37b24e68384ac551077a440` | `85d2f131202882d40b05b65bfb4c83e8b1238426` | stale |
| TLHdig-TF | `4309cf3318c682282c1480b233786362a3083471` | `bc4a206690c1856d3cfde8b291f626c45a712640` | stale |

The drift is material:

- Pseudepigrapha is 200 commits ahead of the R-011 pin and now contains substantially expanded TF feature documentation/release machinery.
- ORACC is 280 commits ahead of the R-011 pin and now includes additional translation-related node/features and other model changes.
- TLHdig also has a different current head, so the old generated inventory cannot be called current without regeneration.

Therefore a single `revision` field is insufficient. A manifest must distinguish:

1. the exact corpus/source revision that the denominator describes;
2. the target corpus revision/release against which a coverage claim is being made.

When they differ, the manifest is stale for the target and must not report target-complete coverage.

### 2.4 R-005 inventory semantics remain useful but deliberately conservative

R-005 correctly distinguishes:

- observed small value domain;
- explicitly reviewed categorical/bounded domain.

Finite observed values are not automatically closed semantics. I-016 must preserve this rule. A denominator may expand values only when the manifest/policy explicitly declares the feature's semantic value family bounded for that release.

The same principle applies to valued edges.

### 2.5 R-011 mixes three concerns that should be separated

R-011 currently combines:

1. denominator construction;
2. mapping-to-denominator references;
3. historical weighted research metrics/query portability.

For P-004 these must be separate.

The new coverage contract should not depend on the R-011 weighted score and should not require a mapping row merely to say that an item has been reviewed as technical/non-semantic or intentionally unsupported.

### 2.6 “reviewed” and “common-target” are not the same axis

P-004 completion is accounting completion.

An item may be fully reviewed and end in:

- exact;
- close;
- broader;
- narrower;
- related;
- ambiguous;
- native-only;
- unsupported.

Only some of these carry a common target. Coverage reporting must therefore expose at least:

- total semantic denominator;
- reviewed/accounted semantic items;
- unreviewed semantic items;
- target-bearing reviewed items;
- assessment counts;
- technical exclusions outside the semantic denominator.

A corpus/profile is not complete while any in-scope semantic item is `unreviewed`.

### 2.7 Technical exclusions need positive records, not disappearance

R-005 excludes warp features at inventory generation time. P-004 additionally identifies synthetic/empty technical anchors and converter bookkeeping that may appear in current corpora.

For auditability, a production coverage release needs an explicit technical-exclusion record when an inventoried/native item is deliberately outside the semantic denominator. Otherwise denominator shrinkage could masquerade as progress.

Technical exclusions must have:

- stable item identity;
- reason/category;
- evidence/source;
- review state or equivalent content-bound authority.

They are counted separately and never improve semantic mapped-target percentages.

## 3. Required canonical item identities

The historical R-011 string keys are good enough as human-readable seed syntax but need a versioned canonical model.

Minimum item kinds evidenced by the current seven-corpus family:

- `node_type`;
- `node_feature`;
- `node_value`;
- `edge_feature`;
- `edge_value` for explicitly bounded valued-edge domains;
- `external_reference` for source authority/identity/identifier semantics not reducible to one feature name;
- `assertion_shape` for reviewed graph/assertion semantics such as apparatus reading-at-locus where one feature key is insufficient.

The first implementation may import current R-011 keys for the first four kinds while making the schema forward-compatible for the last three. It must not invent external-reference/assertion-shape records without evidence.

Canonical identity must include enough native scope to prevent collisions; at minimum corpus + item kind + native identifier, and feature values must use canonical JSON scalar encoding.

## 4. Denominator identity and digest

A production denominator is content-addressed.

The semantic digest must bind at least:

- manifest schema/algorithm version;
- corpus ID;
- corpus repository;
- denominator source revision;
- target corpus revision;
- TF/data version if applicable;
- scope quality;
- denominator-basis kind;
- canonical included semantic item identities;
- canonical technical exclusions.

It must **not** include volatile audit timestamps.

JCS/RFC 8785 + SHA-256 should be reused from TFont rather than inventing another canonicalization algorithm.

## 5. Scope/freshness states

The minimum machine-readable quality axes should be separate:

### Scope quality

- `machine-exhaustive` — the inventory generator has enumerated the declared native semantic surface for that pinned artifact under the documented inclusion policy;
- `bounded-curated` — explicit curated denominator, not corpus-exhaustive.

Do not use “machine-exhaustive” to claim semantic interpretation is complete; it refers only to the inventory denominator.

### Freshness

Derived by exact revision identity:

- `current` — denominator source revision equals the target corpus revision;
- `stale` — both exact revisions are known and differ.

A future unsupported/unknown identity state may be added only if needed. The first contract should fail structurally if either required revision is missing.

### Completion claim eligibility

`corpus_wide_completion_claim_eligible` is true only when:

1. scope quality is `machine-exhaustive`;
2. freshness is `current`;
3. unreviewed semantic item count is zero.

A bounded-curated manifest can become complete **within its declared scope**, but never corpus-wide complete.

## 6. Relationship to production profile releases

I-016 should not mutate current 0.1.0/0.2.0 semantic profiles.

The first coverage manifest is a separate release/accounting artifact. Later P-004 work may bind its digest into new profile releases once the contract has proven stable.

This avoids retroactively changing the already-reviewed I-015 profile identities.

## 7. Initial baseline strategy

The implementation should create a baseline manifest set from the accepted R-011 denominator without pretending it is current everywhere.

Expected initial states:

- BHSA: machine-exhaustive + current;
- CUC: machine-exhaustive + current;
- Syriac: machine-exhaustive + current;
- ExtraBiblical: machine-exhaustive + current;
- TLHdig: machine-exhaustive but stale;
- Pseudepigrapha: bounded-curated + stale;
- ORACC: bounded-curated + stale.

The aggregate baseline remains 685 semantic denominator items, but the report must explicitly state that this is the **historical R-011 accounting baseline**, not current seven-corpus exhaustive coverage.

Current I-015 production mappings may be reflected as already-reviewed items only where a deterministic item→mapping accounting bridge is added and independently reviewed. I-016 does not need to inflate the baseline reviewed count merely to include I-015; correctness of the accounting contract is the first goal.

## 8. Follow-up inventory work

P-004 cannot reach its final coverage criterion until fresh denominators exist for the changed corpora.

Separate follow-up tickets are justified for:

- Pseudepigrapha-TF current machine inventory/denominator;
- ORACC-TF current materialized-TF/model inventory/denominator;
- TLHdig-TF current generated inventory refresh.

Those tickets should update I-016 manifests by exact revision/digest, not edit historical baseline files in place.

## 9. Implementation boundary for I-016

I-016 should implement only:

1. a strict coverage-manifest schema/source contract;
2. deterministic item/manifest canonicalization and SHA-256 semantic digest;
3. builder/importer for the accepted R-011 denominator inputs;
4. deterministic coverage report with scope/freshness/completion-eligibility;
5. seven baseline manifests with explicit quality/freshness;
6. focused tests and CI.

No ontology mappings, corpus downloads, resolver behavior, or approximation logic belong here.

## 10. Required adversarial cases

The plan/tests must reject or detect:

1. duplicate denominator item identities;
2. missing exact source/target revision;
3. a stale denominator reported as current;
4. bounded-curated scope claiming corpus-wide completion;
5. technical exclusion counted as semantic reviewed coverage;
6. assessment outside the accepted eight states;
7. unreviewed item counted as reviewed;
8. target-bearing count greater than reviewed count;
9. observed small domain auto-promoted without explicit bounded policy;
10. denominator digest unchanged after semantic item mutation;
11. volatile timestamp changing semantic digest;
12. historical R-011 total drifting from 685 without an explicit versioned denominator change.

## 11. Decision

**GO** for an I-016 production coverage-accounting contract.

Do not begin large ontology mapping promotion until the denominator contract exists. Otherwise P-004 would have no stable meaning for “100% coverage”.
