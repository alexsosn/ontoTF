# R-016: approximate semantic execution policy

**Status:** research/prototype complete; hardened after adversarial review; pending fresh exact-head review  
**Issue:** #50  
**Recorded:** 2026-09-07  
**Depends on:** accepted R-002/R-003/R-006/R-011 and merged R-015

## Decision

Approximate semantic execution must be **explicit, directional, per-mapping authorized, upstream-gated, and loss-visible**. `semantic_mode=approximate` is not permission to execute every non-exact mapping, and mapping-level approximation can never repair an unresolved parent/profile/ontology-bundle dependency.

The v1 policy is:

| assessment | exact mode | approximate mode | required loss disclosure |
|---|---|---|---|
| `exact` | executable only after upstream execution prerequisites pass | same | none |
| `broader` | refuse as substitute | executable only after upstream prerequisites pass, mapping is reviewed approximation-eligible, and caller accepts undercoverage | undercoverage |
| `narrower` | refuse as substitute | executable only after upstream prerequisites pass, mapping is reviewed approximation-eligible, and caller accepts overcoverage | overcoverage |
| `close` | refuse | informative-only by default; executable only with a separate reviewed loss contract plus caller acceptance | reviewed undercoverage, overcoverage, or both |
| `related` | refuse | refuse as substitute constraint | non-substitutive relation |
| `ambiguous` | refuse | refuse | unresolved target choice |
| `native-only` | no common-target reverse execution | no common-target reverse execution | no shared target |
| `unsupported` | refuse | refuse | unsupported |

The governing invariant is:

> **Assessment describes the reviewed semantic relation. Upstream execution validity, mapping-level approximation authorization, and caller loss acceptance are separate gates. Every gate must pass before a non-exact native plan may execute.**

## 1. Direction semantics

ontoTF assessment direction is fixed by R-002:

```text
native/source concept -> external/common target
```

Therefore:

### `broader`

The external target is broader than the native/source concept:

```text
native ⊂ target
```

When resolving the external target back to the native selector, the selector returns only a subset of what the common request denotes. The approximation has **undercoverage** / false-negative risk.

### `narrower`

The external target is narrower than the native/source concept:

```text
target ⊂ native
```

Reverse execution through the native selector returns a superset of the requested target. The approximation has **overcoverage** / false-positive risk.

### `close`

`close` establishes substantial overlap / near-equivalence but not coextensiveness. It does not establish which set difference dominates.

Consequently `close` is informative-only unless a separate review for the exact mapping/native selector records one of:

- `undercoverage`;
- `overcoverage`;
- both (`bidirectional` loss).

If that loss shape cannot be defended, the mapping remains informative-only even in approximate mode.

## 2. R-003/R-015 execution prerequisite

R-016 owns **only mapping-assessment approximation policy**. It does not supersede existing execution gates.

Before `exact`, `broader`, `narrower`, or reviewed `close` can execute, P-003/runtime must already have established the upstream prerequisites for that mapping/plan, including as applicable:

- executable parent/profile compatibility under the R-003/R-001 contract;
- a valid active semantic bundle under R-015;
- all required ontology locks present under the expected identities;
- every required R-015 bridge present, current, reviewed, compatible, and exact-executable;
- any other profile/dependency prerequisite required by the compiled plan.

R-016 consumes this as a **derived upstream execution gate**. It is not a caller-controlled opt-in and must default fail-closed when absent.

In the research prototype this appears as `prerequisites_executable`. It defaults to `False`; only exact boolean `True` permits further policy evaluation. This is deliberately an integration seam, not a second implementation of the R-015 validator.

Important consequence:

> A mapping may be approximation-eligible while its current semantic bundle is non-executable. Approximate mode must still refuse it.

In particular, R-016 cannot turn an R-015 `approximate`, `related`, stale, unreviewed, incompatible, or missing bridge into an executable bridge. The R-015 exact dependency/bridge gate remains authoritative for bundle composition.

## 3. Separate mapping approximation authorization

A non-exact mapping may conceptually carry:

```json
{
  "assessment": "broader",
  "approximation": {
    "status": "reviewed",
    "eligible": true,
    "losses": ["undercoverage"],
    "rationale": "...",
    "review_id": "..."
  }
}
```

P-003 owns final field names and digest/review binding. R-016 requires the semantic separation.

For `broader` and `narrower`, the assessment determines the possible loss direction, but does not itself authorize execution. A selector can remain informative-only because it is incomplete, unstable, not operationally available, or otherwise unsuitable as a query approximation.

For `close`, the reviewed loss contract is mandatory.

The boolean authorization itself is strict state. The prototype accepts only exact booleans for `approximation_eligible`; values such as `1`, `0`, `"yes"`, `"false"`, `null`, lists, or objects may not authorize approximate execution through host-language truthiness.

P-003 must content/review-bind approximation authorization and loss shape to the mapping semantic identity; a bare mutable boolean is not the final production provenance contract.

## 4. Caller authorization

Approximate execution also requires request-level acceptance of the actual loss vocabulary.

Conceptually:

```json
{
  "semantic_mode": "approximate",
  "accept_losses": ["undercoverage"]
}
```

The accepted-loss vocabulary is closed in v1:

- `undercoverage`;
- `overcoverage`.

Bidirectional loss is represented by accepting both tokens.

Unknown/future loss tokens fail closed rather than being ignored. This matters because a request such as `{"undercoverage", "future-loss-token"}` must not accidentally authorize execution under an older runtime that does not understand the future token.

Examples:

- accept undercoverage only -> reviewed eligible `broader` can execute; `narrower` cannot;
- accept overcoverage only -> reviewed eligible `narrower` can execute; `broader` cannot;
- accept both -> either directional mapping can execute, and reviewed bidirectional `close` can execute;
- approximate mode with no accepted concrete loss -> no non-exact atom executes.

## 5. Loss records

Every approximate executable atom must expose a loss record sufficient for agents to understand the semantic mismatch.

Minimum conceptual content:

```json
{
  "mapping_id": "...",
  "assessment": "broader",
  "requested_target": "...",
  "native_selector": "...",
  "losses": ["undercoverage"],
  "effect": "native selector may miss members of requested target",
  "authorization": {
    "mapping_review": "...",
    "caller_accepted": ["undercoverage"]
  },
  "upstream_prerequisites": "satisfied"
}
```

Loss/authorization state participates in the resolution fingerprint/provenance and survives into search results. A search must not return only the native result rows and discard the approximation explanation.

## 6. Conjunctions

Each required semantic atom resolves independently. No atom may be silently dropped.

A conjunction executes only when all required atoms are executable.

Loss composition is conservative set union:

- exact + exact -> exact;
- exact + undercoverage -> undercoverage;
- exact + overcoverage -> overcoverage;
- under + under -> undercoverage;
- over + over -> overcoverage;
- under + over -> bidirectional;
- bidirectional + anything -> bidirectional;
- any refused atom -> whole required conjunction non-executable.

For an intersection query this union records every direction in which any conjunct can distort the result. It does not claim a quantitative error bound.

## 7. Multi-corpus comparison

Each corpus retains its independent plan and loss set.

Comparison state:

- `exactly-comparable` — every participating executed plan has no semantic loss;
- `approximately-comparable` — plans execute and all non-empty loss sets have the same loss shape (exact corpora may coexist with them);
- `heterogeneous-loss` — executed corpora have different non-empty loss shapes;
- `partial/non-executable` — at least one required plan cannot execute, or no plans exist.

Cross-corpus aggregate counts/statistics are exact-only by default.

A generic approximate-aggregate opt-in is accepted only when:

1. it is exact boolean `true`; and
2. the plans are `approximately-comparable`, i.e. the non-empty loss shape is uniform.

Host-language truthiness is forbidden: `1`, `"true"`, `"false"`, lists/objects, etc. do not count as opt-in.

**Heterogeneous-loss plans remain non-aggregatable in R-016 v1 even with the generic opt-in.** One corpus that under-covers while another over-covers does not form a bounded common approximation. A later statistical policy may define a stronger, explicitly reviewed aggregation mode if there is evidence for it; R-016 does not invent one.

Per-corpus result inspection remains allowed whenever each individual plan is executable.

## 8. Representative corpus cases

### 8.1 Exact linguistic controls

Current accepted R-011 contains exact OLiA controls across the linguistic pilots:

- noun across BHSA, Syriac, ExtraBiblical;
- plural-verb conjunctions across those corpora;
- first person across those corpora;
- masculine in BHSA and Syriac.

Approximate mode must not change their loss status or native plan. They still require ordinary upstream execution prerequisites.

### 8.2 Lexical-entry mixed-strength case

R-011 has an exact BHSA OntoLex `LexicalEntry` candidate while Syriac, ExtraBiblical, ORACC, and TLHdig candidates are `close` because their native lexical identity construction differs.

The four `close` rows are not executable just because the pilot compiler can produce native plans. Each needs a separate reviewed loss contract and approximation authorization.

### 8.3 CRMtex written-text lines

R-011 has `close` CRMtex TX7 candidates for CUC, ORACC, and TLHdig where native line semantics plausibly denote physical written-text segments.

Again, compileability does not imply substitutability. A specific line→TX7 projection remains informative-only until review states the extensional mismatch and approves approximate execution.

### 8.4 Physical/textological negative controls

Physical carrier vs written segment, textual witness vs physical manuscript, physical fragment vs symbolic fragment, and apparatus `reading` vs CRMtex `TX14 Reading` are object-kind/assertion-shape distinctions, not approximation opportunities.

R-016 must not rescue an incorrect mapping-strength decision. Such cases belong in `related`, `ambiguous`, `native-only`, or `unsupported` as appropriate.

## 9. Non-substitutive assessments

Even in approximate mode:

- `related` may be shown for discovery/explanation but is not a substitute constraint;
- `ambiguous` does not auto-select one candidate;
- `native-only` has no common semantic reverse target;
- `unsupported` refuses;
- unreviewed `close` refuses;
- a mapping with no executable native plan refuses;
- a mapping whose upstream execution prerequisites are blocked refuses.

## 10. Ontology hierarchy is not execution authorization

R-016 does not permit runtime widening/narrowing by traversing ontology structure and inventing a mapping assessment.

Forbidden examples:

- request a superclass and execute an arbitrary mapped subclass automatically;
- follow SKOS broader links until some native mapping is found;
- substitute a sibling/related class because labels look similar;
- derive executable `broader`/`narrower` from ontology graph edges when the native→target ontoTF mapping was not reviewed;
- use ontology hierarchy to bypass R-015 bridge/version rules.

Ontology structure can inform mapping research/validation/documentation. Runtime execution uses explicit reviewed mappings plus explicit policy only.

## 11. Prototype policy model

The non-production prototype consumes:

```text
mapping assessment
upstream execution-prerequisite gate
mapping approximation-eligible gate
reviewed loss set
native plan fragment
request semantic mode
request accepted loss set
```

Output is:

- `executable-exact`;
- `executable-approximate`;
- `informative-only` with refusal reason;
- conjunction `non-executable` where any required atom refuses.

It does not execute Text-Fabric and does not validate R-015 artifacts itself. It tests the policy layer P-003 must compose with those contracts.

## 12. Executable contract tests

The exact research suite covers:

1. exact execution after upstream prerequisites;
2. broader/narrower exact-mode refusal;
3. broader reviewed eligibility + undercoverage acceptance;
4. narrower reviewed eligibility + overcoverage acceptance;
5. close without loss review refusal;
6. directional and bidirectional close caller acceptance;
7. unknown/contradictory reviewed loss rejection;
8. all four non-substitutive assessments;
9. missing native plan refusal;
10. unknown semantic mode refusal;
11. conjunction loss union and all-atoms-required behavior;
12. exact multi-corpus aggregation;
13. approximate aggregation disabled by default;
14. uniform-loss approximate aggregation only after exact-boolean opt-in;
15. heterogeneous-loss detection and forced aggregate refusal;
16. compileable native plan not sufficient for close execution;
17. exact-boolean `approximation_eligible` gate;
18. closed caller accepted-loss vocabulary;
19. missing/blocked/non-boolean upstream prerequisite gate;
20. non-boolean aggregate opt-in rejection.

Adversarial RED after R-015 merge: **23 passed / 5 expected failures**, precisely on truthy approximation authorization, unknown accepted-loss token, missing upstream dependency gate, truthy aggregate opt-in, and heterogeneous aggregate opt-in.

GREEN after the policy fix: **30 passed**.

## 13. P-003 inputs

P-003 must preserve separate concepts for:

- mapping assessment;
- derived upstream execution prerequisite state (not caller-supplied);
- mapping approximation eligibility/review;
- reviewed loss directions;
- request semantic mode;
- caller-accepted loss directions;
- atom execution status and refusal reason;
- conjunction aggregate loss;
- per-corpus comparison state;
- exact native plan fragment;
- explanation/provenance/fingerprint.

Specific integration requirements:

1. evaluate R-003 parent/profile compatibility and R-015 semantic bundle/bridge dependencies **before** R-016 mapping policy;
2. approximation authorization cannot weaken R-015 bridge runtime strength or stale/missing/unreviewed dependency failures;
3. content/review-bind approximation eligibility and reviewed loss set to mapping semantic identity;
4. validate boolean authorization fields as exact booleans;
5. validate request loss tokens against the closed supported vocabulary/version;
6. generic aggregate opt-in never authorizes heterogeneous-loss aggregation.

Do not encode approximation as one request boolean or one mapping boolean.

## 14. Non-goals

R-016 does not:

- change mapping assessments;
- automatically infer mappings from ontology hierarchy;
- define production field names;
- implement R-003 parent compatibility;
- implement R-015 ontology bundle/bridge validation;
- make a non-exact R-015 bridge executable;
- execute Context-Fabric queries;
- authorize invalid object-kind substitutions;
- claim approximate results are statistically equivalent;
- define a statistical correction model for heterogeneous loss;
- define external authority-reference semantics (R-017).

## 15. Acceptance trace

- [x] executable/non-executable rules defined for every non-exact assessment;
- [x] direction-specific under/over/bidirectional loss semantics grounded in R-002 direction;
- [x] mapping assessment separated from reviewed approximation authorization;
- [x] R-003/R-015 upstream execution gates preserved and represented fail-closed;
- [x] caller accepted-loss vocabulary fail-closed;
- [x] representative R-011 exact/close corpus cases included;
- [x] conjunction loss composition defined;
- [x] multi-corpus exact/uniform/heterogeneous behavior defined;
- [x] approximate aggregation requires exact-boolean opt-in and is forbidden for heterogeneous loss in v1;
- [x] related/ambiguous/native-only/unsupported negative controls preserved;
- [x] ontology hierarchy kept separate from runtime authorization;
- [x] executable RED/GREEN contract supplied for P-003.

## 16. Final review targets

A fresh logically-independent reviewer should challenge especially:

1. broader/narrower direction against R-002 native→external semantics;
2. whether separate mapping eligibility is necessary in addition to assessment direction;
3. whether `close` is too permissive or too restrictive;
4. whether caller loss acceptance is sufficiently explicit and version/fail-closed safe;
5. whether R-016 can bypass R-003/R-015 anywhere;
6. whether conjunction loss union is conservative and valid;
7. whether uniform-loss approximate aggregate opt-in is acceptable while heterogeneous loss is refused;
8. whether boolean/state inputs can be coerced by host-language truthiness;
9. whether any corpus example is really a mapping-quality defect rather than an approximation case;
10. whether production P-003 review/digest binding is sufficiently specified without being implemented here.
