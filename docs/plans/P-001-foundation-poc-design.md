# P-001: foundation POC semantic profile and compiler design

**Status:** design candidate; implementation blocked until exact-head review and merge  
**Issue:** #12  
**Recorded:** 2026-09-05  
**Scope:** design only; no production schemas, profiles, compiler, resolver, or MCP implementation

## 1. Decision

The first ontoTF POC uses a **validated canonical source bundle** compiled deterministically into a **normalized semantic IR**. Runtime, reference and publication artifacts are generated derivatives; compatibility evidence additionally depends on the concrete parent artifact being validated and is never inferred from IR alone.

The canonical source bundle contains:

1. a **profile manifest**;
2. an expected **parent component manifest**;
3. one or more **ontology lock** records;
4. one or more **canonical mapping source** YAML files;
5. content-addressed evidence records and review records referenced by stable IDs.

The build-time artifact flow is:

```text
canonical source bundle
  profile manifest
  + expected parent component manifest
  + ontology lock(s)
  + canonical mapping source
  + evidence/review records
            |
            v
parse + JSON Schema 2020-12 validation
            |
            v
cross-artifact semantic validation
            |
            v
normalized semantic IR
      |              |                    |
      v              v                    v
runtime sidecar  reference JSON      publication output
                    |                 RDF/OWL/SKOS
                    v
generated docs

validated IR + exact expected parent artifact
            |
            v
release compatibility validation
            |
            v
release-validation report (`verified-exact` required)
```

Runtime/load-time compatibility is a separate dataflow:

```text
validated IR + observed parent component manifest
            |
            v
compatibility evaluator
            |
            v
activation compatibility report
  (`verified-exact | verified-compatible | unverified | incompatible`)
```

Static runtime/reference/publication artifacts below normalized semantic IR are **generated derivatives**. Compatibility reports are deterministic evidence artifacts generated from validated IR plus a specific observed parent identity. The compiler/runtime must fail closed when source or compatibility contracts cannot be proved.

## 2. Accepted foundation dependencies

This design pins the accepted foundation state. Material changes require a new reviewed design change before implementation contracts move.

| research | reviewed exact head | merged main commit |
|---|---|---|
| R-005 | `48c8bd78d0c3a0501b2fdec6946db5df90517bdb` | `a9c4d74d4de2f9a15eb1464dce341ecd2f92f898` |
| R-001 | `68b88a820f5519ad65d46b732679a6278e9ca3c9` | `a22a95084a1518882d1e3e87d10e9757121f106d` |
| R-002 | `d82e6ef2726f149f903eb43ddbfb615faf399cd5` | `a554d4fdc36c8854519064f3a7611b80efa29622` |
| R-003 | `6747379a4aa68c17c156344f3ed3b0c2cb29d423` | `02abd89b5b7d4c83027e1e8503a02eef23cab91e` |
| R-004 | `3dcadc0b32aef95ecbf6ad94f6bbc062f8c6200f` | `00a5d6b7de777074b01bb70ac425d7f187781298` |

The accepted contracts preserved here are: R-001 component-aware parent identity and four compatibility states; R-002 mapping assessment governance and publication separation; R-003 fail-closed semantic resolver handoff and protocol independence; R-004 scoped documentation authority and generated-reference architecture; R-005 empirical edge cases and candidate-only evidence.

## 3. Future production layout

This design PR does **not** create these directories. Implementation tickets will create them after this plan is accepted.

```text
schemas/
  profile.schema.json
  parent-component-manifest.schema.json
  ontology-lock.schema.json
  evidence.schema.json
  mapping.schema.json
  semantic-ir.schema.json
  compatibility-report.schema.json

profiles/
  <profile-id>/
    profile.yaml
    parent/expected-components.json
    mappings/*.yaml
    evidence/*.yaml
    reviews/*.yaml
    tests/fixtures/*

ontology/locks/<lock-id>.yaml

build/<profile-id>/
  semantic-ir.json
  runtime-index.json
  release-validation-report.json
  reference/index.json
  publication/mapping.ttl

dist/<profile-id>/<profile-version>/...
```

Activation compatibility reports are not canonical source and are not committed as one mutable `build/.../compatibility-report.json`. They may be stored in a **runtime cache** keyed by profile semantic digest, observed parent-manifest digest and evaluator version. A cache entry is expendable because the immutable report ID/digest is reproducible from the same inputs.

The release boundary is one profile release, not the whole repository revision.

## 4. Validation and source parsing

Production schemas use **JSON Schema Draft 2020-12** and declare `https://json-schema.org/draft/2020-12/schema`.

Canonical YAML is an authoring surface, not a hashing format. Parsing must:

- decode UTF-8;
- reject duplicate keys;
- reject YAML constructs that cannot be represented losslessly in the JSON-compatible model;
- preserve authored Unicode strings without hidden normalization;
- convert to the JSON-compatible source model before cross-artifact validation.

Structural JSON Schema validation is followed by semantic validation of IDs, references, compatibility dependencies, ontology targets, review bindings, evidence bindings and native edge cases.

## 5. Profile manifest contract

The future `profile.yaml` minimally contains:

- `schema_version` — profile schema version;
- `profile_id` — stable logical profile ID;
- `profile_version` — immutable release-navigation label;
- `semantic_domains` — declared domains;
- `parent_component_manifest` — expected parent-manifest reference;
- `required_components` — authoritative set of semantically addressable native component IDs used by this released profile;
- `ontology_locks` — lock IDs used by mappings/publication;
- `mapping_sources` — canonical mapping source paths;
- `dependency_contract_version` — dependency-expression contract version;
- `minimum_ontotf_runtime` — minimum runtime contract;
- `license` — mapping/profile license metadata;
- `provenance` — non-volatile source provenance.

Example:

```yaml
schema_version: 1
profile_id: ontotf-bhsa
profile_version: 0.1.0
semantic_domains: [morphology]
parent_component_manifest: parent/expected-components.json
required_components: [bhsa-tf]
ontology_locks: [olia-2026-02-04]
mapping_sources: [mappings/morphology.yaml]
dependency_contract_version: 1
minimum_ontotf_runtime: 0.1.0
license: CC-BY-4.0
```

### 5.1 Required-component authority

`required_components` is authoritative for release activation. Component records do not carry an independent `required` flag.

The expected parent component manifest contains exactly the component records named by `required_components` for that released profile. Every active mapping dependency must reference one of those components. A mapping cannot depend on an undeclared optional component and still participate in the released executable profile.

If a future product needs optional feature packs, they are separate profile/module releases with their own manifests rather than hidden partial activation inside one profile.

## 6. Parent component manifest

The parent component manifest is the transport-independent exact-identity record for every **semantically addressable native component** used by the profile.

Supported POC component kinds include:

- **TF payload**;
- **external/native sidecar**;
- **catalogue**;
- **zero-span** entity store;
- **native-adapter** artifact.

Each component record contains:

- `component_id`;
- `kind`;
- `identity_algorithm`;
- `content_digest`;
- optional non-authoritative `logical_locator`;
- optional `license_ref`.

Conceptual shape:

```json
{
  "algorithm": "ontotf-parent-components-sha256-v1",
  "components": [
    {
      "component_id": "bhsa-tf",
      "kind": "tf-payload",
      "identity_algorithm": "ontotf-tf-files-sha256-v1",
      "content_digest": "sha256:..."
    }
  ]
}
```

Component records are sorted by `component_id`; the manifest identity is SHA-256 of canonical JSON over semantic identity fields. Absolute machine paths are excluded.

### 6.1 TF and sidecar identity

`ontotf-tf-files-sha256-v1` hashes a sorted list of `{relative_logical_path, sha256}` for the addressed TF payload files. Directory-like sidecars use the same sorted-path/per-file-digest pattern. A single-file sidecar uses SHA-256 of exact bytes.

Dense storage empties remain part of exact TF byte identity even though they are not semantic values.

### 6.2 Exact-identity negative invariant

If **TF bytes stay identical** but a required external/native sidecar, catalogue, zero-span store, or native-adapter component changes, the parent manifest changes and the profile **must not remain `verified-exact`**.

This is a mandatory negative regression.

## 7. Native dependency contract

Mappings reference stable dependency IDs through `native_dependencies`.

POC dependency kinds include:

- component present;
- node/entity type present;
- feature present on the expected native object kind;
- edge/path present with explicit direction;
- required native value present;
- value-domain invariant;
- extent interpretation (`semantic`, `anchor-only`, `source-span`, `sidecar-zero-span`);
- adapter capability/version invariant;
- sidecar field/path invariant.

The **complete dependency closure** is the union of profile-level dependencies plus every dependency of every active released mapping. The POC does not partially activate whichever mappings happen to validate.

Every dependency names a `component_id` from the authoritative `required_components` set.

## 8. Compatibility algorithm and evidence

The validator compares the expected and observed parent component manifests and, when they differ, validates the complete dependency closure.

- `verified-exact` — every required component identity matches the reviewed release target exactly and the release evidence already validates the complete dependency contract.
- `verified-compatible` — at least one component identity differs, but the complete dependency closure is successfully validated against the changed components.
- `unverified` — no known failure, but complete evidence cannot be established; non-executable.
- `incompatible` — at least one required dependency fails or required component is absent/invalid; non-executable.

**Only `verified-exact` and `verified-compatible` are executable**.

Known failure dominates incomplete evidence: a proven false dependency yields `incompatible`, not `unverified`.

### 8.1 Compatibility report machine contract

Both report lifecycles use the **same report schema** and digest algorithm. Each report contains at minimum:

- `compatibility_report_id` — stable content-addressed report identifier;
- `report_digest` — SHA-256 over the versioned report digest projection below;
- `profile_id` / `profile_version`;
- `profile_semantic_digest`;
- `expected_parent_manifest_digest`;
- `observed_parent_manifest_digest`;
- `state` — exactly one of the four states above;
- `changed_components` — sorted component IDs whose observed identities differ from expected;
- `dependency_results` — complete sorted result set for every dependency in the required closure when closure evaluation is attempted;
- `evaluator_version` — compatibility/dependency evaluator contract version;
- `incomplete_reasons` — machine reason codes explaining `unverified`, otherwise empty;
- `failure_reasons` — failed dependency/component reason codes explaining `incompatible`, otherwise empty;
- optional non-semantic generated timestamp.

Each dependency result records dependency ID, component ID, result (`pass | fail | unknown`), observed evidence digest/summary and evaluator rule version.

The **report digest projection** `ontotf-compatibility-sha256-v1` is RFC 8785 canonical JSON over all non-volatile report semantics listed above, including profile identity, expected/observed manifest digests, state, changed components, dependency results, evaluator version, incomplete reasons and failure reasons. It explicitly **excludes `compatibility_report_id` and `report_digest`**, generated timestamps, local file paths, transport/session metadata and display-only presentation fields. `report_digest` is SHA-256 of that projection.

`compatibility_report_id` is deterministically **derived from `report_digest`** as `ontotf-compatibility-sha256-v1:<report-digest-hex>`. There is no fixed-point or recursive hashing step.

### 8.2 Report lifecycle

A **release-validation report** is produced during profile build from the **validated IR + exact expected parent artifact**. The release gate requires this report to be `verified-exact`; it is shipped with the release bundle as immutable evidence that the canonical profile was validated against its declared exact parent.

An **activation compatibility report** is produced at load/runtime from **validated IR + observed parent component manifest**. It may yield any of the four compatibility states. It is not canonical mapping source and can be recreated deterministically whenever the same profile semantic digest, observed manifest digest and evaluator version are available.

Activation reports may be held in a **runtime cache** keyed by those exact inputs. A cached report is reused only when all key inputs and the report digest verify; otherwise it is recomputed. Runtime provenance references the activation report actually used by `compatibility_report_id` and `report_digest`.

The release-validation report and activation compatibility report therefore share the same report schema, but have different observed-parent inputs and lifecycle. A static release report never substitutes for validation of a changed loaded parent.

## 9. Ontology lock contract

An ontology lock pins the exact external evidence used during review and compilation. Minimum fields are:

- `lock_id`;
- `ontology_id`;
- `support_tier`;
- `term_namespace`;
- `release` and upstream release status where applicable;
- `source_uri`;
- optional `source_revision`;
- `content_digest`;
- non-semantic `retrieved_at`;
- `license` / redistribution policy;
- `snapshot_artifact` locator;
- validated `terms_used` index.

Runtime query resolution never changes mappings from live ontology URLs. Existing profile semantics remain bound to their lock.

## 10. Content-addressed evidence contract

Evidence used to justify an executable mapping is not identified only by a mutable label. Each evidence record minimally contains:

- `evidence_id` — stable logical evidence ID;
- `kind` — e.g. native-doc, pinned-source, ontology-definition, corpus-inventory, scholarly-rationale;
- `source_uri` or repository/source locator;
- optional `source_revision` / release identifier;
- `content_mode` — `external-payload` or `normalized-record`;
- optional `reviewed_content` — required for `normalized-record`; a JSON-compatible structured statement/locator set that captures exactly what was reviewed;
- `content_digest` — digest produced by the versioned evidence rules below;
- `license_ref` where relevant;
- optional human citation metadata.

A mapping references normative evidence through normalized `(evidence_id, content_digest)` bindings. A source can retain the same `evidence_id` across revisions, but a changed reviewed payload or normalized reviewed content has a new `content_digest`.

### 10.1 Evidence digest projection

For `content_mode: external-payload`, `content_digest` uses `ontotf-evidence-payload-sha256-v1`: SHA-256 of the **exact external payload bytes** that were reviewed. Source URI, filename and retrieval time are not substituted for content bytes.

For `content_mode: normalized-record`, `content_digest` uses `ontotf-evidence-record-sha256-v1`: SHA-256 of RFC 8785 canonical JSON over the **evidence digest projection** containing `evidence_id`, `kind`, pinned `source_uri`/`source_revision` where present, `reviewed_content`, and any license/source fields declared normative by the schema. The projection explicitly **excludes `content_digest`**, generated/retrieval timestamps, local paths, human citation formatting and other **display-only metadata**. There is no recursive hash input.

Evidence content changes therefore change the mapping evidence binding and **invalidates review** until the mapping is reviewed against the new evidence digest. Pure display/citation formatting stored outside the content-addressed reviewed evidence projection may remain prose-only.

## 11. Canonical mapping source contract

Every mapping object minimally contains:

- `mapping_id` — stable mapping lineage ID;
- `profile_id` — owning profile;
- `native_selector` — declarative native selector/path;
- `native_dependencies` — dependency IDs;
- `external_target` — approved external URI/CURIE or null;
- `candidate_projections` — ambiguity candidates only;
- `assessment` — runtime/query assessment;
- `publication_relation` — optional separately justified formal relation;
- `applicability` — object/domain/precondition constraints;
- `ontology_lock` — approved lock for external semantics, or null for no-target/ambiguous states;
- `evidence` — content-addressed `(evidence_id, content_digest)` bindings;
- `review` — review status/provenance plus reviewed digest;
- `mapping_semantic_digest` — machine identity of the reviewed mapping semantics;
- `rationale` — non-executable explanation;
- `introduced_in` / `changed_in` — release-navigation metadata.

A normal reviewed mapping shape is conceptually:

```yaml
mapping_id: bhsa.word.gn.m-to-olia-masculine
profile_id: ontotf-bhsa
native_selector:
  kind: feature-value
  component_id: bhsa-tf
  node_type: word
  feature: gn
  operator: eq
  value: m
  extent: semantic
native_dependencies: [bhsa.word.gn.m]
external_target: http://purl.org/olia/olia.owl#Masculine
candidate_projections: []
assessment: exact
publication_relation: null
applicability:
  node_type: word
ontology_lock: olia-2026-02-04
evidence:
  - evidence_id: bhsa-doc:gn
    content_digest: sha256:...
mapping_semantic_digest: sha256:...
review:
  review_id: review:2026-09-bhsa-gn-m
  status: reviewed
  reviewed_mapping_digest: sha256:...
  reviewer_id: reviewer:opaque-project-id
  reviewed_at: 2026-09-05T21:00:00Z
  review_source: offline-bundle-or-pr-reference
  review_method: independent-skeptical
rationale: Reviewed native and ontology definitions support this projection.
```

## 12. Native selector model

`native_selector` may represent `feature-value`, `node-kind`, directed `edge`, ordered `path`, `sidecar-field`, `zero-span-entity`, or `source-span`.

Edges and paths record direction explicitly. A shared feature/edge label never proves shared meaning.

`extent` is one of:

- `semantic`;
- `anchor-only` for a technical anchor;
- `source-span`;
- `sidecar-zero-span`.

This prevents technical TF anchors from masquerading as semantic extent.

## 13. R-002 mapping assessment contract

Assessment direction is always **native/source → external target**.

- `exact` — external target and native/source concept are judged coextensive.
- `close` — substantial overlap without established coextensiveness.
- `broader` — external target is broader than native/source.
- `narrower` — external target is narrower than native/source.
- `related` — related, not a substitute constraint.
- `ambiguous` — evidence does not justify one target/assessment projection.
- `native-only` — native/source concept is supported with no external projection.
- `unsupported` — profile provides no supported semantic projection.

The **assessment and publication relation are independent**. `assessment: exact` does not imply any OWL/SKOS equivalence assertion.

Validation rules:

- `exact | close | broader | narrower | related` require one `external_target` and one valid top-level `ontology_lock`;
- `native-only` and `unsupported` have no external target and require top-level `external_target: null`, `ontology_lock: null`, and `publication_relation: null`;
- `ambiguous` is non-executable and requires top-level `external_target: null`, top-level `ontology_lock: null`, and top-level `publication_relation: null` until ambiguity is resolved;
- `publication_relation` is null unless independently reviewed for the approved target formalism;
- R-005 candidate codes never populate `assessment` automatically.

### 13.1 Ambiguity representation

Each candidate projection contains at least:

```yaml
external_target: <candidate URI or CURIE>
ontology_lock: <lock for that candidate target>
assessment_candidate: exact | close | broader | narrower | related
evidence:
  - evidence_id: <evidence ID>
    content_digest: sha256:...
```

This represents both target ambiguity and relation ambiguity. Two entries may use the **same external target** with **different candidate assessments**. Candidate targets from different ontology locks are valid because each candidate owns its explicit `ontology_lock` binding rather than borrowing an unresolved top-level lock.

Candidate ordering, labels, result counts and first-match behavior must not make `ambiguous` automatically executable.

## 14. Review binding and readiness

Review states are:

- `reviewed` — may participate in released executable behavior if all other gates pass;
- `provisional` — diagnostic/authoring only;
- `disputed` — audit/research only.

### 14.1 Review record machine contract

Every mapping review record has at least:

- `review_id` — stable logical review-record ID;
- `status` — `reviewed | provisional | disputed`;
- `reviewed_mapping_digest` — the exact mapping semantic digest seen by the reviewer;
- `reviewer_id` — project-controlled provenance identifier; it may link externally to a person/agent identity but a **forge username** is not required;
- `reviewed_at` — timestamp for audit chronology;
- `review_source` — immutable/offline-resolvable review artifact reference or external reference plus bundled summary;
- `review_method` — review class such as `independent-skeptical`;
- optional note/evidence references.

For **executable readiness**, only `status` and the equality of `reviewed_mapping_digest` to the current recomputed mapping digest are behavior gates in the first POC. Those readiness facts participate in the profile semantic projection.

`review_id`, `reviewer_id`, `reviewed_at`, `review_source`, `review_method`, notes and display labels are **audit-only** provenance and are not part of semantic identity or `mapping_semantic_digest`; changing them alone does not alter mapping behavior. They remain in the released source/IR provenance and therefore remain covered by source/bundle integrity. In particular, a **forge username** is **not part of semantic identity**.

The project/PR process decides whether a submitted review is legitimately independent; the compiler verifies the machine binding and readiness state rather than pretending to cryptographically infer reviewer independence from a username.

### 14.2 Per-mapping semantic digest

`mapping_semantic_digest` is SHA-256 of RFC 8785 canonical JSON over behavior/publication-affecting mapping fields, including:

- `mapping_id` and owning `profile_id`;
- `native_selector`;
- `native_dependencies`;
- `external_target` or ambiguity `candidate_projections`;
- `assessment`;
- `publication_relation`;
- `applicability`;
- approved `ontology_lock` or per-candidate locks;
- the normalized `(evidence_id, content_digest)` evidence bindings.

It excludes the **review record itself**, rationale prose, release-navigation fields and the digest field itself, avoiding self-reference.

For `review.status: reviewed`, `review.reviewed_mapping_digest` **must match** the recomputed `mapping_semantic_digest`. A mismatch is a **stale review** and is non-executable/non-releasable. Changing selector, target, candidate projection, assessment, publication relation, applicability, ontology binding, or reviewed evidence content therefore invalidates review automatically.

This rule is checked by the compiler; a contributor cannot preserve `status: reviewed` across a material mapping or evidence edit without a new review binding.

## 15. Normalized semantic IR

The **normalized semantic IR** is the only compiler input to generated runtime/reference/publication artifacts. It is deterministic and JSON-compatible.

It contains:

- normalized profile metadata;
- expected parent component manifest identity and component identities;
- dependency definitions;
- ontology locks/term pins;
- content-addressed evidence bindings used by mappings;
- normalized mappings including `mapping_semantic_digest` and review readiness/provenance;
- generated lookup indexes;
- explicit IR format version.

Behavior-affecting fields are separated from prose/display metadata.

Normalization rules:

- documented field names/types only;
- identifiers validated but not silently case-folded;
- set-like collections **sorted** by stable IDs;
- semantically ordered arrays preserve order;
- no build-machine absolute paths;
- no generated timestamps in behavior identity;
- authored Unicode strings are preserved.

## 16. Canonicalization and digest rules

All semantic hashes use **SHA-256** with versioned algorithms.

### 16.1 Source digest

For each canonical UTF-8 source file:

1. reject invalid UTF-8;
2. remove an optional UTF-8 BOM;
3. normalize CRLF/CR **line endings** to LF;
4. preserve all other characters and whitespace;
5. hash the resulting bytes.

The bundle `source_digest` hashes a **sorted** list of `{logical_path, file_sha256}` encoded as canonical JSON. Source formatting/comments can therefore change `source_digest` without changing runtime meaning.

### 16.2 Canonical JSON

JSON-compatible normalized objects use RFC 8785 JSON Canonicalization Scheme semantics: deterministic property ordering, no insignificant whitespace, UTF-8 output and preserved JSON string values. The design calls this **canonical JSON**.

### 16.3 Profile semantic digest

`semantic_digest` is SHA-256 of canonical JSON over the behavior/publication-affecting **profile semantic projection**. It includes:

- stable `profile_id` and semantic contract/schema versions;
- expected parent component-manifest semantic identity;
- dependency definitions;
- ontology locks/target pins;
- mapping semantic records/digests;
- executable/review readiness state (`status` plus reviewed-digest match), not audit-only reviewer provenance;
- applicability and publication semantics.

`profile_version` must not affect `semantic_digest`. Release-navigation labels, rationale prose, local paths, CI IDs, build **timestamps**, generated-at fields, audit-only review provenance and MCP transport/session metadata also **must not affect** it.

Exact bundle identity is the tuple **profile_id + profile_version + semantic_digest** plus the release artifact digests. Thus two release labels can refer to identical semantic content while remaining distinct immutable release artifacts.

A separate `ir_digest` may cover non-volatile evidence/documentation/reviewer provenance for exact build reproduction.

## 17. Versioning and exact-parent rebase

SemVer is a release-navigation convention; `semantic_digest` is exact semantic identity.

A changed `semantic_digest` can never be a patch.

- **patch** — release/tooling/rationale correction with unchanged `semantic_digest` and unchanged supported runtime behavior;
- **minor** — additive/backward-compatible semantic or compatibility change that changes `semantic_digest` but does not remove previously supported behavior;
- **major** — removes previously supported behavior or changes the meaning/execution contract of an existing released mapping in a backward-incompatible way.

An **exact-parent rebase** publishes a new exact tested parent component manifest while mapping/dependency semantics remain unchanged and the complete dependency closure validates on the new parent. Because the expected parent identity is behavior-affecting, the rebase changes `semantic_digest`. If it adds/rebases exact support without removing previously supported behavior, the exact-parent rebase **is a minor release**. If it removes previously supported behavior or makes a previously supported parent/profile contract unavailable, it is major.

This deterministic rule eliminates patch/minor ambiguity while satisfying the accepted R-001 requirement that a **changed exact parent need not automatically force major versioning**.

An ontology-lock update also changes semantic digest; it is minor if backward-compatible/additive and major if it changes/removes previously supported semantics.

Stable `mapping_id` identifies mapping lineage; released meaning is reconstructed from the profile release plus semantic digest and mapping record.

## 18. Compiler pipeline and failures

The deterministic compiler stages are:

1. **parse** — UTF-8 YAML/JSON, reject duplicate/unsupported structures;
2. **schema validation** — JSON Schema 2020-12;
3. **cross-artifact semantic validation**;
4. **exact parent release validation**;
5. **IR normalization/canonicalization**;
6. **generated static derivatives + release-validation report**;
7. **determinism/drift verification**.

Cross-artifact validation fails on at least:

- duplicate IDs;
- missing component/dependency/lock/evidence/review references;
- evidence digest mismatch;
- any active mapping dependency outside authoritative `required_components`;
- illegal assessment/external-target/ontology-lock or ambiguity combinations;
- illegal publication relation for target formalism;
- unknown ontology target;
- explicit semantic use of dense storage empty without native evidence;
- contradictory selector/applicability metadata;
- `reviewed_mapping_digest` mismatch;
- profile data violating accepted normative ontoTF rules.

Release validation recomputes the exact tested parent component manifest and requires a `verified-exact` release-validation report for the release target.

## 19. Runtime sidecar and compatibility handoff

The first POC runtime derivative is deterministic JSON `runtime-index.json`, containing indexes such as:

- external target → approved mapping IDs;
- native selector key → mapping IDs;
- assessment → mapping IDs;
- dependency → affected mapping IDs;
- semantic domain → capability summary;
- compact provenance IDs;
- expected parent manifest/compatibility metadata.

The runtime consumes a validated bundle and loaded parent components:

```text
compute observed parent component manifest
  -> exact match: verified-exact
  -> changed identity: evaluate complete dependency closure
       -> all pass: verified-compatible
       -> incomplete: unverified
       -> known fail: incompatible
```

Every activation creates or validates the activation compatibility report from §8.2. Runtime never rewrites canonical mappings from live ontology lookup.

## 20. Capability and resolution plan contracts

A capability record includes:

- `profile_id` / `profile_version` / `semantic_digest`;
- compatibility state;
- activation `compatibility_report_id` / `report_digest`;
- expected and observed component-manifest identities;
- semantic domains;
- mapping assessment support;
- ontology lock IDs;
- explicit `native-only`, `unsupported` and `ambiguous` states;
- bounded provenance/detail IDs.

A **resolution plan** contains:

- normalized-request fingerprint;
- profile identity and semantic digest;
- compatibility state and immutable activation compatibility report identity;
- requested external concepts;
- selected mapping IDs;
- per-mapping `assessment`;
- `native_constraints` and explicit native edge/path steps;
- approximation/loss annotations;
- executability + reason codes;
- compact `provenance`;
- **resolution fingerprint**.

The resolution fingerprint is **protocol-independent** and derives from semantic request + profile semantic identity + observed compatibility evidence + native plan. It never derives from **MCP session state**, negotiated protocol, connection ID or timestamp.

## 21. Runtime execution gate

Exact-mode execution requires:

1. compatibility is `verified-exact` or `verified-compatible`;
2. every required mapping is `reviewed` and its reviewed digest matches current mapping/evidence content;
3. every required assessment is `exact`;
4. no requested constraint is ambiguous/native-only/unsupported/unavailable;
5. generated native plan validates against the active adapter.

Approximate mode may explicitly allow `close`, `broader`, or `narrower` and must report loss direction:

- `broader` may under-cover the external request;
- `narrower` may over-cover the external request;
- `close` may differ extensionally either way.

`related` is not an executable substitute in the first POC. `ambiguous` must not auto-select. `unverified` and `incompatible` compatibility remain fail closed.

Stable error/result categories include `profile_not_found`, `parent_unverified`, `parent_incompatible`, `ontology_lock_missing`, `term_unknown`, `unsupported`, `ambiguous`, `approximation_required`, `unsafe_relaxation`, `native_query_invalid`, and `internal_inconsistency`.

## 22. Native-data edge cases

### 22.1 Zero-span/catalogue/native sidecar

A `zero-span-entity` / `sidecar-zero-span` selector explicitly names its non-TF component. No fake TF slot is invented. The component participates in exact identity and dependency validation.

### 22.2 Technical anchor versus semantic extent

A selector uses `extent: anchor-only` for a **technical anchor**. Semantic occurrence queries follow reviewed paths rather than pretending the anchor is full **semantic extent**.

TLHdig `lex.oslots` is the mandatory stress example.

### 22.3 Dense TF empty

A **dense TF empty** `""`/`None` storage record is non-semantic by default. The inventory/IR distinguishes raw records, non-empty nodes, empty observation count and semantic observed values.

A dense empty cannot become **explicit absence**, omission, non-attestation, damage, unknown or uncertainty unless the native source explicitly asserts that meaning.

### 22.4 Observed versus closed domain

Domain metadata distinguishes:

- **observed small domain** — finite non-empty observations in one exact release;
- **documented bounded** vocabulary — source evidence establishes bounded categories;
- closed vocabulary — only where explicit source semantics establishes closure;
- open/large domain;
- unknown closure.

A finite observed release inventory is never silently promoted to permanent closure.

## 23. Generated documentation and semantic diff

The IR/source fields must generate all R-004 reference directions:

- **native -> semantic** reference;
- **semantic -> corpora** reference;
- mapping-detail pages;
- compatibility/provenance pages;
- explicit negative capability states;
- compact agent reference JSON.

Semantic diff dimensions include at least:

- **mapping assessment changed**;
- **publication relation changed**;
- **native selector/path changed**;
- ontology lock changed;
- **parent compatibility evidence changed**;
- required component/dependency change;
- evidence digest change;
- review binding/readiness change;
- audit-only review provenance change;
- ambiguity candidate-projection change;
- **prose-only** change.

Generated docs expose source/profile/ontology/parent identities and never infer semantic values from dense empties.

## 24. POC fixture matrix

The first implementation fixtures must include positive and adversarial cases.

| fixture | purpose | mandatory assertion |
|---|---|---|
| BHSA positive morphology | happy path | reviewed exact `sp`/`gn`/`nu` style mapping compiles and resolves |
| changed-parent | compatibility | changed component set with complete closure → `verified-compatible` plus activation report |
| changed sidecar with unchanged TF | identity negative | must not remain `verified-exact` |
| ORACC-like zero-span | non-TF semantics | zero-span component is addressed without fake slots |
| TLHdig technical-anchor | extent semantics | anchor-only does not become semantic occurrence extent |
| dense-empty | storage negative | empty record does not become semantic value/applicability |
| native-only | no-target state | no external target/lock/publication relation |
| unsupported | negative capability | explicit unsupported result, no blank/guess |
| ambiguous relation | ambiguity | same target with different candidate assessments remains non-executable |
| ambiguous cross-lock | ambiguity | candidate targets from different ontology locks retain candidate-specific lock binding |
| stale-review | review binding | material mapping edit with old reviewed digest becomes non-executable |
| changed-evidence | evidence binding | changed evidence content digest invalidates review |
| audit-only review edit | identity negative | reviewer display/provenance edit does not change semantic digest |
| activation report | lifecycle | changed observed parent produces reproducible runtime compatibility report, not a rewritten release report |

## 25. Reproducible build and CI contract

For every future profile change CI must eventually:

1. validate canonical sources against schemas;
2. validate cross-artifact references and authority rules;
3. validate content-addressed evidence bindings;
4. recompute mapping semantic digests and review bindings;
5. validate exact release parent manifest;
6. compile normalized IR;
7. generate release-validation report and static runtime/reference/publication derivatives;
8. run generation twice or otherwise verify deterministic canonical digests;
9. fail stale committed generated artifacts;
10. execute positive and negative fixtures;
11. produce semantic diff dimensions from §23;
12. fail on unreviewed/stale-review executable mappings;
13. preserve explicit four-state compatibility evidence and report shape;
14. test activation compatibility report reproducibility against changed-parent fixtures.

Source digest and semantic digest are both reported so formatting-only source changes are distinguishable from semantic behavior changes.

## 26. Implementation ticket decomposition

Every ticket below follows **research -> plan -> implement -> test** as applicable, with explicit **RED -> GREEN -> independent review** before merge. A ticket that changes public semantics requires a design amendment first rather than silently changing this contract.

### `I-001` — structural schemas and source validator

**Dependency order:** first.  
Create JSON Schema 2020-12 contracts for profile, parent components, ontology lock, evidence, review, mapping source and compatibility report plus parser/structural validator. Include duplicate-key, no-independent-`required`, evidence-shape, review-shape and candidate-lock regressions.

### `I-002` — canonicalization and digest library

Depends on `I-001`.  
Implement UTF-8 source digest, RFC 8785 canonical JSON, evidence content digest helpers, `mapping_semantic_digest`, profile `semantic_digest`, source digest and test vectors proving `profile_version` and audit-only review provenance exclusion.

### `I-003` — parent component identity

Depends on `I-001`, `I-002`.  
Implement TF/file/directory component identity and parent manifest composition. Mandatory negative: TF unchanged + required sidecar changed.

### `I-004` — cross-artifact semantic validator

Depends on `I-001`..`I-003`.  
Validate required-component authority, all eight assessment shapes, candidate-specific ontology locks, ontology targets, native dependencies, evidence digests, dense-empty assertions and review-digest binding.

### `I-005` — compatibility validator/report

Depends on `I-003`, `I-004`.  
Implement `verified-exact | verified-compatible | unverified | incompatible`, shared immutable report schema/digest, release-validation report, activation compatibility report, runtime-cache keys, complete dependency closure and changed-parent fixtures.

### `I-006` — normalized IR compiler

Depends on `I-002`, `I-004`, `I-005`.  
Compile deterministic semantic IR and semantic/source digests; reject stale review/evidence and nondeterministic ordering.

### `I-007` — runtime sidecar and capability index

Depends on `I-006`.  
Generate deterministic runtime index plus capability records including negative states, activation compatibility report identity and provenance.

### `I-008` — semantic resolver core

Depends on `I-005`, `I-007`.  
Implement protocol-independent resolution plans and fail-closed exact/approximate gating; no MCP transport implementation yet.

### `I-009` — generated reference and semantic diff

Depends on `I-006`, `I-007`.  
Generate native -> semantic / semantic -> corpora reference JSON/Markdown and structured semantic diff.

After each ticket: focused RED/GREEN tests, relevant full suite, then a fresh independent review of the exact head. A head change invalidates that review.

## 27. Test strategy

Tests should be contract-oriented, not implementation snapshots.

Required layers:

- schema validation positives/negatives;
- canonicalization/digest fixed vectors;
- evidence content-addressing and changed-evidence stale-review regression;
- mapping digest/review-binding stale-review regression;
- audit-only review-provenance semantic-digest negative regression;
- component-manifest fixed vectors;
- exact/compatible/unverified/incompatible compatibility matrix plus immutable report vectors;
- release-validation vs activation-report lifecycle and cache-key regressions;
- ambiguous same-target/different-assessment regression;
- ambiguous candidate targets from different ontology locks;
- no-target native-only/unsupported regressions;
- exact-parent rebase version-classification regression;
- zero-span/sidecar and technical-anchor fixtures;
- dense-empty and observed-vs-closed-domain negatives;
- deterministic compile: same semantic inputs => same semantic IR/runtime/reference digests;
- protocol-independent resolver plans.

No test may treat a repository version string, feature-name coincidence, TF-only digest or author confidence as proof of semantic compatibility.

## 28. Non-goals and implementation boundary

P-001 creates no production schemas, no `profiles/`, no compiler/runtime implementation, no final corpus mapping release and no MCP code changes.

After this plan is reviewed and merged, `I-001` becomes the first production ticket. Any implementation uncertainty that would change fields, authority, digest semantics, compatibility behavior or execution policy must return through a design change rather than be guessed in code.
