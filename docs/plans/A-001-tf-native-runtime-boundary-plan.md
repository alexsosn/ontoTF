# A-001 plan: pin the TF-native ontoTF runtime boundary

**Issue:** #65  
**Research:** `docs/research/A-001-tf-native-runtime-boundary.md`  
**Gate:** plan before contract tests or normative edits

## 1. Goal

Prevent ontoTF from growing a generic external-storage/data-format runtime surface that no current pilot needs.

The baseline contract is:

```text
source formats -> corpus-specific materializer -> TF/Context-Fabric -> ontoTF semantic adapter
```

ontoTF owns semantic interoperability over materialized corpus structure. It does not own generic ingestion/query adapters for arbitrary external records.

## 2. Normative scope

This workstream changes only architecture/research documentation, agent guardrails, issue contracts, and static contract tests.

No production Python runtime, schema loader, external fetcher, parser, storage abstraction, or adapter implementation is added.

Repository normative edits are limited to:

1. `AGENTS.md` — add the baseline TF-native/materializer boundary and future-extension threshold;
2. `docs/research/A-001-r005-oracc-zero-span-supersession.md` — preserve R-005 verbatim while explicitly superseding its old ORACC sidecar/zero-span architectural inference;
3. `docs/research/A-001-r007-external-carrier-supersession.md` — preserve the reviewed R-007 artifact verbatim while superseding only its generic `sidecar/native-adapter` carrier conclusions and ORACC example;
4. A-001 research/plan documents;
5. static architecture tests and a focused workflow.

R-005 and R-007 remain immutable historical research records. The A-001 supersession amendments are the authoritative current interpretation where those documents conflict with the TF-native runtime boundary.

Issue contracts #37 and #44 are updated in GitHub so open downstream work cannot continue against stale adapter assumptions.

## 3. Baseline architecture contract

### 3.1 ontoTF runtime inputs

Baseline ontoTF may consume:

- TF/Context-Fabric nodes, slots, node features and edge features;
- parent corpus/component identity;
- ontoTF mapping/profile/ontology/bridge/provenance artifacts;
- external identifiers/URIs as reviewed values/references.

### 3.2 Baseline exclusions

Baseline ontoTF must not define:

- `native-adapter` / `sidecar` as a generic runtime carrier;
- arbitrary file/path/field selectors outside the materialized TF graph;
- JSON/XML/CSV/SQLite/database/API query adapters;
- network dereferencing implied merely by an external URI;
- adapter caching/authentication/synchronization semantics.

### 3.3 Materializer responsibility

Corpus-specific converters/materializers own ingestion of source representations and should materialize query-relevant corpus semantics into TF/Context-Fabric where appropriate.

ontoTF does not need to know whether those semantics originated in JSON, XML, TEI, CSV, a database, PDF extraction, or another source representation.

## 4. TF structural contract retained from R-007

Keep the useful reviewed structural distinctions:

- neutral TF slot/`oslots` semantics;
- ordinary textual extent;
- occurrence-set interpretation;
- technical anchors;
- exact preservation of discontinuous slot sets;
- no inference of stronger domain relations from `oslots` alone.

Reconcile synthetic/empty slots explicitly:

- a synthetic/empty slot is still a TF slot;
- it preserves source position/order without asserting a semantic sign/glyph/token;
- semantic/source slot counts remain distinguishable from synthetic/technical slot counts;
- technical anchoring must not be published as semantic textual content.

Do not replace `native-adapter` with another generic carrier name.

## 5. R-005/R-007 migration wording

R-005 and R-007 are accepted research artifacts and should not be falsified retroactively. Preserve both unchanged and add dated supersession amendments.

The R-005 amendment states that its earlier ORACC sidecar/zero-span architectural inference was later replaced by ORACC-TF ADR-0001.

The R-007 amendment supersedes only these conclusions:

- `sidecar/native-adapter` as an initial/native carrier dimension;
- ORACC catalogue/object semantics as evidence for adapter-side runtime addressing;
- P-003 requirements to preserve/add generic sidecar/native-adapter carrier mechanics;
- RED cases that require sidecar entities to resolve through ontoTF runtime.

The R-007 conclusions that remain valid include neutral `oslots`, `Slot`, `slotLink`, TF-node extent/anchor interpretations, discontinuous slot-set preservation, native edge direction/value semantics, and the rule that stronger domain semantics cannot be inferred from TF structure alone.

The supersession amendment must state that current pilot evidence is materialized in TF and that future genuinely outside-graph data is out of baseline scope pending a separate architecture extension.

## 6. P-002 migration requirement

Open P-002 #37 / PR #64 must not merge with:

- `adapter-capability`;
- `sidecar-field`;
- `native-adapter` carrier semantics;
- adapter-side `native-field` / `native-entity` selector families introduced solely to support external storage.

P-002 may retain TF-native dependency kinds such as component/node/feature/edge/path/value-domain and TF structural interpretation where justified.

The profile-v2 dependency mechanism itself is not rejected by A-001; only the unsupported external-storage branch of that contract is removed.

## 7. P-003 boundary

P-003 #44 must explicitly state that the common semantic adapter compiles to already-materialized native Context-Fabric/TF constraints.

No generic external storage/format abstraction belongs in the POC acceptance surface. A future external-data extension requires a separate ticket and evidence threshold.

## 8. Future-extension threshold

A generic outside-TF runtime abstraction is not considered for baseline inclusion until at least two independent real corpus cases demonstrate:

1. query-relevant semantics must remain outside TF/Context-Fabric;
2. materialization is inappropriate, not merely inconvenient;
3. both cases share enough execution/storage semantics for a common abstraction;
4. materializer-side alternatives were compared;
5. provenance, packaging, synchronization, security and failure contracts are designed.

## 9. TDD contract

### RED

Add static architecture tests before normative edits. They must fail against the current branch because the supersession amendments do not yet exist and `AGENTS.md` lacks the boundary guardrail.

Required assertions:

1. `AGENTS.md` contains the TF-native/materializer boundary and extension threshold;
2. the R-005 supersession amendment explicitly marks the old ORACC sidecar/zero-span design as superseded by ADR-0001 without modifying R-005 historical content;
3. the R-007 supersession amendment explicitly rejects generic `sidecar/native-adapter` as a baseline carrier and preserves the still-valid TF structural conclusions;
4. the R-007 amendment reconciles ORACC with TF synthetic/empty-slot semantics and current materialized pilot evidence;
5. the R-007 amendment states that storage location/source format is not a semantic carrier type;
6. A-001 plan/research do not introduce a replacement generic adapter API.

Record a failing focused run before normative edits.

### GREEN

Add only the guardrail/supersession documentation above, then run:

- focused A-001 static contract tests;
- the existing repository test suite if CI ownership permits.

## 10. Review gate

Fresh logically-independent adversarial review of the exact final head must attack:

- whether generic adapter semantics survived under another name;
- whether the correction accidentally forbids legitimate external identifiers/provenance;
- whether R-005/R-007 historical evidence was rewritten rather than superseded;
- whether ORACC synthetic slots are incorrectly treated as semantic signs;
- whether the two-corpus extension threshold can be bypassed by hypothetical extensibility;
- whether any production/runtime change exceeds this architecture-correction scope.

Any blocker requires fix -> exact-head retest -> fresh re-review.
