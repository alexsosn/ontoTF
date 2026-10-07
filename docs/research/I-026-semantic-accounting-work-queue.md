# I-026 research — authoritative P-004 semantic accounting work queue

**Issue:** #263  
**Parent:** P-004 #202, Workstream A  
**Baseline:** `main` `cf292481c67b798d4485c0e178b2e2fb83340cbd`  
**Status:** research complete; ready for plan/TDD

## 1. Question

Can the seven current machine-exhaustive coverage manifests be turned into one deterministic item-level development queue without promoting unreviewed ontology mappings, losing technical exclusions, or allowing exploratory research to outrank P-004 coverage work?

Yes. The queue should be a governance/accounting artifact derived from the existing immutable denominators, not a new semantic authority layer.

## 2. Current denominator

The current production-target manifests contain exactly **934 semantic items**:

| corpus | semantic items | technical exclusions | denominator source |
| --- | ---: | ---: | --- |
| BHSA | 219 | 0 | R-005 generated inventory |
| CUC | 37 | 0 | R-005 generated inventory |
| Syriac | 74 | 0 | R-005 generated inventory |
| ExtraBiblical | 136 | 0 | R-005 generated inventory |
| Pseudepigrapha-TF | 113 | 5 | I-017 current release inventory |
| ORACC-TF | 99 | 6 | I-018 current materialized inventory |
| TLHdig-TF | 256 | 4 | I-019 current shipped inventory |

All seven manifests are `machine-exhaustive` and current for their declared target revision. The queue must bind their existing `denominator_digest`, repository, source revision and target revision. It must not recompute or silently mutate those denominators.

Existing selected accounting is sparse:

- 20 current items have production accounting;
- 76 item/accounting records have research accounting;
- 88 unique denominator items have at least one selected production/research accounting record;
- therefore 846 denominator items have no selected accounting yet.

The work queue is responsible for ownership of all 934, not for pretending the 846 are already semantically reviewed.

## 3. Routing is not mapping

An I-026 route means:

> this later P-004 workstream owns the final reviewed disposition of this native semantic item.

It does **not** mean:

> the item already maps to that workstream's ontology.

For example, routing a Semitic verbal-stem feature to Workstream C means I-027 must review it against OLiA and may ultimately produce `native-only`, `ambiguous` or `unsupported`. It does not assert an OLiA correspondence.

This distinction is required because P-004 completion is 100% reviewed/accounted coverage, not 100% shared-target coverage.

## 4. Authoritative owner classes

The queue needs exactly one primary final-disposition owner per denominator item:

| code | owner issue | responsibility |
| --- | --- | --- |
| C | #264 | OLiA / linguistic |
| D | #265 | OntoLex-Lemon + SKOS / lexical |
| E | #266 | CIDOC CRM + CRMtex / heritage + written text |
| F | #267 | LRMoo / textology + transmission |
| G | #268 | CRMinf / explicit scholarly/editorial inference audit |
| H | #269 | cross-model, structural/native-only, residual/ambiguous completion |

A row may mention complementary future profiles, but it must still have one primary owner. True complementary projection is marked explicitly and is completed in H after the primary owner establishes its semantic layer.

## 5. Evidence policy

Every route must carry a repository-local evidence pointer.

Primary evidence is the denominator's own `denominator_basis.source`:

- R-005 inventories expose native node types, node/edge feature metadata, applicability and source descriptions;
- I-017/I-018 current inventories expose the materialized Pseudepigrapha/ORACC schema;
- I-019 exposes the exact TLHdig shipped schema projection.

For a node value, routing inherits the owning feature's evidence and never treats the observed literal alone as semantic evidence. For TLHdig closed values, the current I-019 denominator policy remains the authority for closure; I-026 only routes the item.

Existing R-011 or production accounting is retained verbatim in the queue row as prior evidence, never upgraded.

## 6. Conservative routing policy

Routing should use explicit corpus-specific allowlists derived from the pinned inventory descriptions and the already accepted P-004/R-008/R-009/R-010 profile boundaries.

General rules:

1. `node_value` inherits the route of its `node_feature`.
2. `edge_value` inherits the route of its `edge_feature`.
3. Linguistic categories, morphology and syntax route to C.
4. Lexeme/form/sense/gloss/language identity and lexical representation route to D.
5. Physical carriers, written-text segmentation, signs, lines, columns, material/provenience and carrier metadata route to E.
6. Versions, witnesses, readings, translations, textual joins and transmission structures route to F.
7. Explicit certainty/correction/editorial-activity candidates route to G for a CRMinf audit; routing does not assert that CRMinf applies.
8. Structural navigation, source/provenance bookkeeping with retained scholarly meaning, cross-model node domains, and unclear residual semantics route to H.
9. Unmatched items fail **into H / needs-focused-research**, never into an inferred ontology workstream.

This is intentionally conservative. It is safer to put an unclear item into H than to create ontology authority from a feature name.

## 7. Expected first-pass distribution

The reviewed routing policy developed against the exact current manifests yields:

| corpus | C | D | E | F | G | H | total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BHSA | 147 | 21 | 0 | 6 | 0 | 45 | 219 |
| CUC | 0 | 2 | 23 | 1 | 10 | 1 | 37 |
| Syriac | 61 | 5 | 0 | 0 | 0 | 8 | 74 |
| ExtraBiblical | 111 | 10 | 0 | 2 | 0 | 13 | 136 |
| Pseudepigrapha-TF | 0 | 8 | 0 | 79 | 0 | 26 | 113 |
| ORACC-TF | 11 | 13 | 40 | 18 | 0 | 17 | 99 |
| TLHdig-TF | 46 | 7 | 90 | 51 | 29 | 33 | 256 |
| **total** | **376** | **66** | **153** | **157** | **39** | **143** | **934** |

These are workload-routing counts, not ontology coverage percentages.

## 8. H sub-buckets

H must not be a semantic trash bin. Each H row is additionally classified as one of:

- `cross-model` — native domain/entity needed by multiple semantic profiles;
- `native-only-candidate` — source/structural/provenance semantics likely to remain native but still require review;
- `needs-focused-research` — semantics cannot safely be assigned to C-G from current evidence;
- `unsupported-candidate` — an explicit native item whose requested common semantics are expected to be unsupported; final review is still required.

Existing accounting assessments can strengthen the bucket choice but cannot be overwritten by I-026.

## 9. Syriac `ls="prop"` accounting gap

The current Syriac manifest records one production accounting gap:

`node_value:ls="prop"`

The current denominator does contain `node_feature:ls`, but `ls` is not declared as a closed bounded value family in that denominator, so the production value-specific mapping cannot be imported as a denominator value item without changing denominator policy/digest.

I-026 should **not silently expand the denominator**. Instead it must emit a separate gap route:

- owner: C / #264;
- native feature: `ls`;
- requested value: `prop`;
- reason: `outside-denominator`;
- required action: I-027 must either justify a new versioned denominator policy/value item or account the mapping at an accepted feature-level boundary without falsifying denominator arithmetic.

This keeps the 934-item denominator stable while making the gap impossible to lose.

## 10. Technical exclusions

The queue must carry technical exclusions only in a separate per-corpus section/count. They do not receive C-H routes and never increase routed semantic-item totals.

Expected current technical exclusions are 15 total:

- Pseudepigrapha: 5;
- ORACC: 6;
- TLHdig: 4;
- historical R-005 manifests used here: 0 committed technical-exclusion rows.

## 11. Determinism and failure modes

The builder must fail closed on:

- missing or duplicate semantic item identity;
- duplicate primary route;
- route policy references absent native feature/type/edge;
- inherited value whose parent feature is absent;
- manifest denominator digest drift;
- source/target revision drift from the pinned policy;
- any semantic item left without an owner;
- any technical exclusion entering the semantic queue;
- aggregate routed count other than 934;
- unrepresented accounting gap;
- policy order changing output bytes.

Output order is canonical corpus order then UTF-16-compatible item-ID ordering used by the project.

## 12. Artifact boundary

I-026 should add:

- reviewed routing policy: `docs/research/data/i026/p004-routing-policy.json`;
- deterministic builder: `scripts/coverage/build_i026_work_queue.py`;
- frozen generated queue/report: `docs/research/data/generated/i026/p004-work-queue.json`;
- focused tests under `tests/i026/`;
- this research document and a reviewed implementation plan.

No TFont runtime mapping, resolver, ontology lock or production profile behavior changes in I-026.

## 13. Decision

**GO.**

The repository now has sufficient current denominator evidence to create an authoritative work queue. The next semantic work after I-026 should be #264 and #265, not additional formal-semantics research.
