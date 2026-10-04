# TFont agent instructions

TFont is a semantic interoperability layer for Text-Fabric / Context-Fabric corpora. It must preserve corpus-native scholarly semantics while providing explicit mappings to shared ontologies and controlled vocabularies.

## Non-negotiable principles

1. **Native corpus semantics remain authoritative.** Never rewrite or simplify an upstream annotation merely to make two corpora look equivalent.
2. **Mappings are explicit and qualified.** `exact`, `close`, `broader`, `narrower`, `related`, `ambiguous`, `native-only`, and `unsupported` correspondences must remain distinguishable. A reviewed `native-only` mapping is a legitimate no-target state and must not be deleted or weakened merely to increase shared-ontology coverage.
3. **No silent inference.** A semantic adapter may expose mappings and capabilities; it must not fabricate missing annotations or convert scholarly uncertainty into fact.
4. **Open-by-default.** Dependencies, ontology terms, mapping artifacts, and generated compatibility metadata should be redistributable under documented terms. Exceptions require an explicit architecture decision.
5. **Runtime stays thin.** Prefer schema/value resolution and native Context-Fabric execution over converting corpora into a separate RDF/triplestore runtime.
6. **Versioned compatibility.** Every mapping must identify the parent corpus and the corpus versions/schema versions it supports.
7. **Common ontology pivot is the interoperability contract for shared projections.** A pinned arbitrary external URI is not sufficient evidence of semantic interoperability. Mappings/capabilities that claim a shared semantic projection must connect native corpus semantics to reviewed shared ontology/profile concepts in a form that supports both native -> semantic lookup and semantic -> corpus-native resolution. `native-only` entries may remain in released profiles without an external target; they are not resolvable through the common pivot and must be reported as such. Do not derive new semantic compiler/resolver/profile work from the current single-`external_target` v1 shape while P-003 #44 is pending.
8. **TF-native runtime boundary.** Baseline TFont operates on already-materialized Text-Fabric / Context-Fabric corpus nodes, slots, features, edges, and TFont semantic/provenance artifacts. Source-format ingestion belongs to corpus-specific materializers/converters. Do not add a generic `sidecar`, `native-adapter`, arbitrary file/record/field addressing layer, external database/API query adapter, or implicit URI dereferencing to baseline TFont. External identifiers and URIs may be reviewed semantic, authority, identity, or provenance references without becoming fetch/storage capabilities. Storage location or source format is not a semantic carrier type. A generic outside-TF runtime abstraction may be researched only under a separate evidence-backed architecture ticket after at least two independent real corpus cases show that required queryable semantics genuinely must remain outside TF/Context-Fabric, materialization is inappropriate rather than merely inconvenient, and the cases justify a shared abstraction over materializer-side alternatives.

For zero-span textual data, follow the materialized corpus model rather than inventing a TFont storage workaround. In particular, current ORACC-TF architecture keeps independently positioned zero-span textual entities in the TF warp through explicit synthetic/empty slots. Such slots are technical positional anchors, not semantic cuneiform signs, and do not justify a TFont sidecar abstraction.

## Backlog selection and program priority

The autonomous development loop must optimize for completion of the active project program, not for the mere existence of an open issue.

Priority rules:

1. An explicit user instruction about what to work on next always wins.
2. Otherwise, follow the active roadmap/program's declared execution order and dependency graph before unrelated backlog items.
3. For P-004 (#202), until the completion gate #269 is closed, the default queue is:
   - #263 I-026 accounting work queue;
   - #264 I-027 OLiA linguistic coverage and #265 I-028 OntoLex-Lemon/SKOS lexical coverage after #263, with #264/#265 allowed in parallel;
   - #266 I-029 CIDOC CRM/CRMtex;
   - #267 I-030 LRMoo;
   - #268 I-031 CRMinf;
   - #269 I-032 residual accounting and completion release.
4. Do not select deferred/exploratory research ahead of an actionable active-program ticket. In particular, R-021 through R-026 are post-P-004-core research unless explicitly reopened because a concrete P-004 blocker requires them.
5. A large roadmap ticket with unfinished acceptance criteria does not count as “no tickets left”. If its next workstream lacks a suitably scoped implementation ticket, decompose that workstream into evidence-grounded tickets and continue within the same program.
6. If the earliest queued ticket is genuinely blocked, work on the next dependency-safe ticket within the same active program. Leave the active program only when all dependency-safe work is blocked or the user explicitly changes priority.
7. Performance, stability, ergonomics, documentation, and edge-case fallback work comes after actionable active-program work, not before it.
8. Issue number, creation time, ease of completion, or the fact that a research issue is unblocked are not priority signals by themselves.

When work is deferred for prioritization rather than rejected on substance, record that explicitly so it can be reopened after the active program completes.

## Required development loop

Every ticket moves through the relevant gates below. Do not skip a gate because the implementation appears obvious.

### 1. Research gate

Before architectural or semantic decisions:

- inspect the actual upstream corpus/schema and authoritative ontology specifications;
- compare viable alternatives, licensing, maintenance status, identifiers, and versioning;
- record evidence, unresolved questions, rejected alternatives, and a recommendation in `docs/research/`;
- do not add production code in a research-only ticket.

A research ticket is complete only when its acceptance criteria can be answered from the committed research artifact.

### 2. Design gate

For implementation work that changes architecture or a public mapping contract:

- derive a design/plan from completed research;
- specify inputs, outputs, invariants, compatibility/versioning rules, failure behavior, and test strategy;
- state which semantics are corpus-native, standardized, inferred, or intentionally unsupported;
- record the plan in `docs/plans/` before implementation.

The first POC architecture and any later change to distribution, manifest/schema shape, mapping semantics, or MCP-facing behavior always require this gate.

### 3. TDD implementation gate

Implementation tickets follow test-driven development:

1. write a failing test for the next externally meaningful behavior;
2. confirm the failure is for the intended reason;
3. implement the smallest change that makes it pass;
4. run focused tests, then the relevant full suite;
5. refactor only while tests stay green.

Do not use tests that merely mirror implementation internals. Prefer contract tests over snapshotting incidental serialization details.

### 4. Independent review gate

Every PR that changes research conclusions, architecture, mappings, schemas, runtime behavior, or public documentation requires an independent skeptical review before merge.

**Independent means the final review is performed by a different person or a separately instantiated review agent/context that did not author the PR changes.** The authoring agent must not count its own reread or self-audit as the required independent review.

The reviewer must check the PR against:

- the parent issue acceptance criteria;
- completed research/design artifacts;
- upstream corpus semantics;
- ontology specifications and licensing/version assumptions;
- backward compatibility and provenance;
- tests and negative cases;
- agent and human ergonomics.

A review that only summarizes the PR is insufficient. The reviewer should actively look for semantic overclaiming, lossy mappings, accidental ontology equivalence, unsupported inferences, stale upstream assumptions, and coupling that makes corpus modules hard to distribute independently.

If review finds a material defect, revise and repeat independent review until the PR is mergeable. Any material change after the final independent review invalidates that review and requires another independent pass over the new head.

## Phase discipline

The initial phase is **research only**. Do not open or implement production ontology/mapping code until research tickets R-001 through R-005 (distribution, ontology governance, ergonomics, documentation, and empirical corpus census) have been completed and reconciled into an approved design ticket.

The current common-ontology reconciliation is governed by `docs/plans/P-001-common-ontology-roadmap-amendment.md`: R-006 through R-011 (#38–#43) feed P-003 #44. Until P-003 is accepted, generic infrastructure work may proceed only when it does not freeze the current single-target ontology shape as the final semantic contract.

## Artifact conventions

- `docs/research/R-XXX-*.md` — evidence and conclusions from research tickets.
- `docs/plans/P-XXX-*.md` — implementation/design plans derived from completed research.
- `mappings/` — future corpus-specific mapping packages; format and layout are intentionally undecided until distribution research completes.
- `schemas/` — future machine-readable contracts; do not create until design establishes them.

Research documents should distinguish:

- observed facts;
- external standard requirements;
- project decisions;
- assumptions still requiring validation.

## Initial interoperability scope

At minimum, research and later POC tests must cover structurally and linguistically different members of the TF family:

- ETCBC/BHSA;
- DT-UCPH/CUC;
- Syriac TF corpora (evaluate ETCBC `syriac`, `peshitta`, and `syrnt` and choose representative targets explicitly);
- ETCBC `extrabiblical`;
- TLHdig-TF.

Pseudepigrapha-TF and ORACC-TF are secondary stress corpora for textological/codicological and archaeological/lexical-semantic coverage respectively. For the P-003 common-ontology POC they are promoted to required heterogeneous pilots. The required P-003/R-011 pilot set is therefore BHSA, CUC, one ETCBC Syriac corpus, ETCBC `extrabiblical`, TLHdig-TF, Pseudepigrapha-TF, and ORACC-TF.

Do not assume that identical feature names have identical semantics, or that different feature names imply different semantics.
