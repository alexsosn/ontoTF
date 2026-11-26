# R-003: agentic and human ergonomics for semantic interoperability

**Status:** research complete; R-005 accepted; R-001 accepted; R-002 accepted; pending exact-head independent review  
**Issue:** #3  
**Recorded:** 2026-09-05

## Decision

ontoTF should expose a **hybrid semantic workflow** above native Context-Fabric:

1. `semantic_capabilities` — discover semantic profiles and concept support;
2. `semantic_resolve` — build an inspectable corpus-specific native query plan without executing it;
3. `semantic_search` — execute exactly the plan produced by the resolver and return that plan with results.

Native Context-Fabric `search()` remains native. It never silently interprets ontology aliases.

Semantic execution is fail-closed:

- unsupported required semantics are never dropped;
- approximate mappings are never silently promoted to exact;
- ambiguous mappings do not auto-select a target;
- `native-only` and `unsupported` have no external target;
- stale or unverified parent compatibility is non-executable;
- dense TF empty records are not ontology values;
- all execution exposes native constraints, mapping assessment, compatibility evidence, and provenance.

The human authoring model should use **one canonical declarative YAML source validated by JSON Schema**. RDF/Turtle, JSON, runtime indexes, tables, and documentation are generated one-way artifacts.

## 1. Research basis

### 1.1 Context-Fabric MCP

The inspected Context-Fabric source is the current repository head at research time:

- repository: `Context-Fabric/context-fabric`;
- revision: `3a38ca80e617d872ce1664e0f0740486d0e7e8ac`;
- `cfabric-mcp`: `0.1.7`;
- Context-Fabric core at the same revision: `0.5.7`.

The **current host implementation** is the pinned Context-Fabric MCP server above. Its package metadata declares `mcp>=1.0,<2`, and its server imports the v1 `FastMCP` API. That is evidence about the host implementation, not evidence that it already implements the newest protocol revision. Depending on the installed v1 SDK/client pair, the negotiated protocol may be a **handshake-era** revision. ontoTF therefore must not infer 2026 stateless-protocol capabilities merely from the fact that `cfabric-mcp 0.1.7` is current.

The existing MCP surface already provides corpus discovery, feature inspection, search, continuation/export, passage lookup, and node-feature access. ontoTF should not duplicate that API. It should add only semantic planning and execution above it.

The existing progressive-disclosure pattern is sound: inspect a corpus, inspect relevant features, then search. ontoTF compresses repeated semantic discovery when a reviewed mapping already exists.

### 1.2 MCP protocol assumptions

The **current protocol target** at research time is MCP `2026-07-28`. That protocol generation has a stateless core and differs materially from the handshake-era protocol family that a current v1-SDK host may negotiate.

The integration contract is therefore negotiation-aware rather than version-assumptive:

- a current Context-Fabric deployment may negotiate a handshake-era protocol through its v1 SDK;
- a future or updated host may negotiate the `2026-07-28` stateless protocol;
- structured tool output and schemas are used where supported by the negotiated protocol and host SDK;
- protocol-specific transport/session metadata may differ, but semantic resolution meaning may not;
- resolution fingerprints, compatibility evidence, provenance, and fail-closed execution **must not depend on MCP session state**.

The portable invariant is: **legacy/handshake host and 2026 stateless host produce equivalent semantic resolution semantics** for the same corpus/profile/request, apart from protocol-specific transport metadata. A protocol upgrade is therefore not a semantic migration.

ontoTF uses explicit resolution fingerprints rather than hidden session identity. On stateless `2026-07-28` transports this is mandatory; on handshake-era transports it remains the reproducible design. Read-only/idempotent annotations remain hints rather than correctness mechanisms, and model/server instructions never enforce semantic safety.

### 1.3 Accepted upstream contracts

R-005 accepted empirical evidence at reviewed head `48c8bd78d0c3a0501b2fdec6946db5df90517bdb`, merged as `a9c4d74d4de2f9a15eb1464dce341ecd2f92f898`.

R-001 accepted distribution/version-binding semantics at reviewed head `68b88a820f5519ad65d46b732679a6278e9ca3c9`, merged as `a22a95084a1518882d1e3e87d10e9757121f106d`.

R-002 accepted ontology-governance semantics at reviewed head `d82e6ef2726f149f903eb43ddbfb615faf399cd5`, merged as `a554d4fdc36c8854519064f3a7611b80efa29622`.

R-003 treats these as fixed dependencies unless a later reviewed research change explicitly reopens them.

## 2. Parent compatibility and execution gate

R-001 defines four evidence states:

- `verified-exact`;
- `verified-compatible`;
- `unverified`;
- `incompatible`.

Only `verified-exact` and `verified-compatible` are executable in the ordinary semantic API.

### 2.1 Component-aware exact identity

Exact compatibility is based on a transport-independent **parent component manifest**, not on one TF digest or a repository/version string.

The manifest covers every **semantically addressable native component** used by the profile, including where applicable:

- TF payload files;
- external/native sidecars;
- catalogue or zero-span entity stores;
- native-adapter artifacts.

A capability or resolution record exposes the parent component manifest identity and the relevant component identities. TF bytes are one possible component, not the universal parent identity.

`verified-exact` requires every declared semantically addressable native component to match the tested component manifest.

### 2.2 Compatible changed parents

`verified-compatible` exists for a changed component set whose exact identity differs from the tested target but whose **complete dependency closure** has been validated against the changed components.

This is intentionally not a schema-name heuristic.

- **changed component set + complete dependency closure** validated successfully → `verified-compatible` → executable;
- **changed component set without complete validated dependency closure** → `unverified` → non-executable;
- changed component set with a required dependency that fails validation → `incompatible` → non-executable.

Feature names, node-type names, metadata, or unchanged TF bytes are insufficient by themselves. For example, if TF bytes stay identical but a required external sidecar changes, the profile cannot remain `verified-exact`.

### 2.3 Compatibility evidence in responses

Compact responses carry at least:

- compatibility state;
- parent component manifest identity;
- identities of components on which the current profile depends;
- dependency evidence/fingerprint sufficient to explain `verified-compatible`;
- profile identity/version.

Full explanation exposes the validated dependency closure and the failed dependency if the state is `incompatible`.

## 3. Mapping-assessment semantics

R-002 owns the governance meanings below. R-003 defines how agents see and execute them.

- **`exact` — the external target and native/source concept are semantically coextensive** under the reviewed mapping.
- **`close` — the external target and native/source concept substantially overlap or are near-equivalent**, but coextensiveness is not established.
- **`broader` — the external target is broader than the native/source concept**.
- **`narrower` — the external target is narrower than the native/source concept**.
- **`related` — the external target is related but is not a substitute constraint**.
- **`ambiguous` — evidence does not justify one unambiguous target assessment**.
- **`native-only` — the native/source concept is intentionally supported without an external target**.
- **`unsupported` — the active profile has no supported semantic projection** for the requested native/source concept.

Mapping-level `exact` is distinct from parent compatibility `verified-exact`.

`native-only` and `unsupported` have no external target and cannot carry an external publication mapping relation. `ambiguous` does not authorize automatic projection or automatic target choice.

R-005 `S/C/B/N/R/U/L` classifications remain research-stage evidence. They cannot activate a runtime mapping assessment. In particular, R-005 `S` cannot compile directly into executable `exact`.

### 3.1 Assessment versus publication relation

The ontoTF **mapping assessment** controls runtime/query planning. An optional **publication relation** records a formal RDF/OWL/SKOS relation only when the target formalism justifies it.

The two fields are independent. An OLiA OWL class may have an approved ontoTF assessment while `publication_relation` remains absent because no OWL/RDFS relation has been independently justified.

SKOS mapping predicates are not the generic runtime assessment vocabulary.

### 3.2 Query effects of directional assessments

Direction is always native/source concept → external target.

When an agent requests an external concept and ontoTF realizes it through a native concept:

- `broader` can under-cover the external request because the native/source concept is narrower than the external target;
- `narrower` can over-cover the external request because the native/source concept is broader than the external target;
- `close` can differ extensionally in either direction;
- `related` is never a substitute constraint by default.

Therefore there is **no automatic widening** and no automatic narrowing. Any approximate execution must be explicitly allowed and its semantic effect must be visible in the returned plan.

## 4. Minimum agent workflow

### 4.1 One corpus

```text
semantic_capabilities(corpus, concepts=optional)
        ↓
semantic_resolve(expression, corpus, semantic_mode="exact")
        ↓
semantic_search(expression, corpus, semantic_mode="exact")
```

Capability discovery can be skipped when the client has a fresh cached summary for the exact profile and parent component manifest.

### 4.2 Multiple corpora

```text
semantic_capabilities(corpora=[...], concepts=[...], compare=true)
        ↓
semantic_resolve(expression, corpora=[...], semantic_mode="exact")
        ↓
inspect per-corpus mapping assessments, compatibility states, and losses
        ↓
execute only accepted plans
```

The resolver, not the LLM, decides whether each requested semantic unit is supported by each active profile.

## 5. Capability reporting

`semantic_capabilities` answers:

- whether each corpus has a ontoTF profile;
- compatibility state and its component-aware evidence;
- active ontology locks/profiles;
- semantic domains covered;
- requested concept support and mapping assessment;
- native-only and unsupported distinctions;
- diagnostic coverage counts.

Default output is compact and does not dump all mapping rows.

Concept-level entries contain at least:

- external target URI/label when one exists;
- ontoTF mapping assessment;
- optional publication relation;
- native node type and native feature/value or path;
- applicability conditions;
- review status;
- ontology lock/release;
- parent component manifest binding;
- mapping/profile version.

`native-only` and `unsupported` entries omit an external target.

### 5.1 Dense TF records

Dense Text-Fabric features can expose empty-string/`None` storage records. These have **no semantic value** unless a source explicitly defines the literal as meaningful.

Consequences:

- empty-string/`None` records are excluded from semantic value domains;
- empty records do not make a feature applicable to a node type by themselves;
- capability metrics distinguish `nodes_with_value` from raw/storage records;
- empty records cannot become `Absent`, `Unknown`, `Omitted`, `Unattested`, damage, or another explicit absence assertion without reviewed source semantics.

Diagnostic output may report raw empty-record counts separately.

## 6. Resolution contract

`semantic_resolve` returns a plan without corpus results.

The initial expression model supports:

- semantic concept/category constraints;
- conjunction;
- explicit disjunction where needed;
- target object kind where needed;
- corpus selection;
- explicit semantic mode / allowed assessments.

Structural ordering and containment remain native Context-Fabric search syntax. The resolver supplies the native constraints that instantiate semantic concepts.

Example compact plan:

```json
{
  "resolution_id": "r_01...",
  "requested": ["olia:Noun", "olia:Feminine", "olia:Plural"],
  "semantic_mode": "exact",
  "corpora": {
    "bhsa": {
      "compatibility": "verified-exact",
      "status": "resolvable",
      "native_target": "word",
      "native_constraints": [
        {"feature": "sp", "operator": "=", "value": "subs"},
        {"feature": "gn", "operator": "=", "value": "f"},
        {"feature": "nu", "operator": "=", "value": "pl"}
      ],
      "template": "word sp=subs gn=f nu=pl",
      "losses": []
    }
  }
}
```

The agent never invents plausible English feature names such as `gender=feminine`.

### 6.1 Unit and aggregate statuses

Per requested semantic unit, the response exposes the approved assessment (`exact`, `close`, `broader`, `narrower`, `related`, `ambiguous`, `native-only`, `unsupported`) plus operational availability.

`unavailable` is an operational state for a missing/unloadable profile, ontology lock, or compatible parent; it is not an R-002 mapping assessment.

Aggregate plan states are:

- `resolvable` — all required constraints are executable under requested semantic mode;
- `partial` — at least one required constraint is unavailable under the requested mode; not executable by default;
- `ambiguous` — unresolved alternatives remain; not executable;
- `incompatible` — parent/profile compatibility failed; not executable;
- `unsupported` — requested semantics cannot be represented by the active profile.

### 6.2 No silent relaxation

If a request is `Noun AND Feminine AND Plural` and one corpus supports only noun and plural, ontoTF does not execute the surviving conjunction.

An approximate/relaxed request must be submitted explicitly. The plan records which assessment or dropped condition the caller chose to permit.

## 7. Semantic search

`semantic_search` is convenience execution of the same resolver.

Required invariant:

```text
semantic_search(inputs).resolution == semantic_resolve(inputs)
```

apart from ephemeral identifiers/timestamps.

The native Context-Fabric query executed by `semantic_search` must be structurally identical to the plan it returns.

A non-executable plan under the requested semantic mode yields a tool error rather than partial results.

Where feasible, semantic search reuses native result modes such as count, statistics, results, and passages.

## 8. Explainability and provenance

Every executable plan exposes enough evidence to reproduce and audit the projection.

Compact provenance includes:

- parent component manifest;
- component identities used by the profile;
- compatibility state and dependency evidence;
- ontoTF profile/mapping version;
- mapping assertion ID;
- external target URI when one exists;
- ontology lock/release;
- mapping assessment;
- optional publication relation;
- native feature/value/edge/path;
- resolution fingerprint.

Full explanation adds:

- rationale and source evidence;
- mapping author/reviewer provenance where recorded;
- applicability conditions;
- transformation chain to the native template;
- approximation/loss explanation;
- component, mapping, and ontology digests;
- dependency closure details for `verified-compatible`.

Results never erase the plan. Pagination carries a stable resolution fingerprint and cannot switch profile, ontology lock, or parent component manifest mid-result.

## 9. Human authoring strategy

### 9.1 Canonical YAML

Turtle alone is not the canonical authoring UI. Reviewers need native constraints, assessment, provenance, applicability, rationale, and evidence in readable diffs.

Conceptual YAML:

```yaml
id: bhsa.word.gn.m
corpus: bhsa
native:
  node_type: word
  feature: gn
  value: m
semantic:
  target: http://purl.org/olia/olia.owl#Masculine
  assessment: exact
  publication_relation: null
applicability:
  profile: ontotf-bhsa@0.1.0
review:
  status: reviewed
rationale: >-
  Native and external definitions were reviewed at the pinned corpus and ontology revisions.
sources:
  - docs/features/gn.md
```

`assessment` is ontoTF runtime governance. `publication_relation` is independent and may be null.

### 9.2 Generated formats

Canonical YAML may generate:

- runtime sidecar/index;
- JSON API fixtures;
- RDF/Turtle publication;
- Markdown/HTML reference tables;
- coverage/gap reports;
- optional TF modules where R-001 permits them.

Generated artifacts carry the canonical source digest and a visible generated marker.

The POC has no bidirectional YAML↔RDF editing path.

## 10. Human inspection and CLI behavior

Later implementation should provide behavior equivalent to:

```text
ontotf validate
ontotf coverage bhsa
ontotf explain bhsa native:word.gn=m
ontotf explain bhsa ontology:http://purl.org/olia/...
ontotf diff --from ontotf-bhsa@0.1.0 --to ontotf-bhsa@0.2.0
```

`validate` checks schema, ontology locks, component-aware parent compatibility, mapping assessments, duplicate/conflicting IDs, ambiguities, and generated-artifact drift.

`coverage` reports mapped native semantics, assessments, native-only/unsupported gaps, and explicit denominators.

`explain` works native→semantic and semantic→native/corpora using the same provenance model as MCP.

`diff` distinguishes:

- mapping added/removed;
- mapping assessment changed;
- publication relation changed;
- native constraint/path changed;
- ontology target/lock changed;
- parent compatibility evidence changed;
- rationale-only change.

Assessment or native-constraint changes are material semantic API changes.

## 11. Error model

Suggested stable machine categories:

| code | meaning | default behavior |
|---|---|---|
| `ONTOTF_PROFILE_NOT_FOUND` | corpus has no profile | tool error; suggest native discovery |
| `ONTOTF_PARENT_UNVERIFIED` | exact identity absent and complete compatibility not established | diagnostic capability result; resolution non-executable |
| `ONTOTF_PARENT_INCOMPATIBLE` | at least one required parent dependency failed | tool error; no semantic execution |
| `ONTOTF_ONTOLOGY_LOCK_MISSING` | pinned ontology snapshot unavailable | tool error |
| `ONTOTF_TERM_UNKNOWN` | requested external term unknown in active locks | tool error/capability miss |
| `ONTOTF_UNSUPPORTED` | active profile cannot express required semantics | non-executable resolution; search tool error |
| `ONTOTF_AMBIGUOUS` | no single reviewed target/assessment | non-executable resolution |
| `ONTOTF_APPROXIMATION_REQUIRED` | exact mode would require approximate assessment | non-executable in exact mode |
| `ONTOTF_UNSAFE_RELAXATION` | execution would drop or silently widen/narrow a required constraint | tool error |
| `ONTOTF_NATIVE_QUERY_INVALID` | generated native query rejected | profile/internal defect |
| `ONTOTF_INTERNAL_INCONSISTENCY` | search plan differs from resolver plan | hard error; never return results |

Expected semantic domain failures use MCP tool-error signaling. Protocol errors remain for malformed/unsupported MCP requests.

## 12. Agent efficiency

Default responses use progressive disclosure.

POC targets:

- one-corpus capability summary ≤ **8 KiB serialized JSON** by default;
- requested concept lookup ≤ **20 mapping candidates** per concept unless explicitly expanded/paginated;
- after corpus/profile discovery, an ordinary exact query requires at most **two semantic calls** (`semantic_resolve` + `semantic_search`);
- multi-corpus comparison requires one capability call + one resolver call before execution;
- pagination refers to resolution identity instead of repeating full rationale;
- no default tool returns a whole ontology or whole mapping bundle.

Structured fields include `status`, `assessment`, `publication_relation`, `native_constraints`, `profile`, `compatibility`, `provenance`, and `errors`.

Read-only/idempotent annotations may be advertised where the negotiated MCP version supports them, but correctness is enforced by the resolver.

## 13. Adversarial cases

### 13.1 Plausible native names

Request: feminine plural nouns in BHSA.

Required behavior: return reviewed native `sp`/`gn`/`nu` constraints and never invent English feature names.

### 13.2 False stem equivalence

Request: compare Hebrew `qal` and Syriac `peal` as the same stem.

Required behavior: preserve native categories; expose only reviewed assessment; exact mode refuses substitution unless an approved exact mapping exists.

### 13.3 Silent constraint dropping

Request: `Noun AND Feminine AND Plural` across BHSA and Peshitta 0.2.

Required behavior: BHSA may resolve; Peshitta reports unsupported/partial; no unconstrained fallback.

### 13.4 Changed parent components

Case A: a required native sidecar changes, but every profile dependency over the **changed component set + complete dependency closure** validates. Result: `verified-compatible`; execution is allowed and provenance records the changed component identities and dependency evidence.

Case B: the component set changes with a **changed component set without complete validated dependency closure**. Result: `unverified`; inspection is allowed but semantic execution is not.

Case C: dependency validation proves a required invariant/value/path failed. Result: `incompatible`; no semantic execution.

A revision, digest, or schema change alone is not synonymous with incompatibility.

### 13.5 Missing ontology term

A required term is absent from the pinned ontology snapshot. Profile validation fails; the resolver does not fetch a newer live ontology and continue silently.

### 13.6 ORACC sentence-label trap

An ORACC `c type=sentence` implicit source chunk is not automatically a BHSA linguistic sentence.

### 13.7 Lexeme extent trap

BHSA lexeme occurrence extent and TLHdig technical `lex.oslots` anchors require different native paths. The resolver exposes those paths instead of assuming containment equivalence.

### 13.8 Witness trap

Pseudepigrapha reading→manuscript attestation, Peshitta A/B witness metadata, and TLHdig line→fragment witness edges remain distinct native assertions unless independently reviewed mappings establish a common queryable concept.

### 13.9 Empty-record trap

An empty dense TF record cannot satisfy explicit omission, absence, unknown, non-attestation, damage, or uncertainty semantics.

## 14. Required corpus/task matrix

### BHSA vs ETCBC ExtraBiblical

Exercise shared high-level morphology while keeping corpus-specific lexical-node differences visible.

### BHSA vs Syriac

Exercise `Noun + Feminine + Plural`, lexical identity, and a language-specific stem case that has no automatic exact equivalence.

### CUC vs TLHdig-TF

Exercise sign/document structure and damage/editorial semantics without flattening higher-level structures into name matches.

### ORACC-TF vs TLHdig-TF vs biblical lexical layer

Exercise lexical entries/attestations where native node/edge paths differ.

### Pseudepigrapha-TF witness semantics

Exercise reading-to-manuscript attestation and verify that Peshitta/TLHdig witness-like assertions do not substitute automatically.

## 15. Documentation and contribution workflow

Generated documentation provides:

1. native → semantic;
2. semantic → corpora;
3. coverage/gaps;
4. mapping detail with assessment, provenance, compatibility evidence, tests, and history.

Color is never the only carrier of mapping status.

A mapping PR includes:

1. source/research evidence for new or contested semantics;
2. canonical YAML change;
3. regression/characterization fixture;
4. generated artifact check;
5. semantic diff;
6. author-side validation;
7. independent skeptical review of the final exact head.

## 16. Measurable POC criteria

These are the canonical implementation-test seeds.

### Discovery

1. One capability call reports corpus/profile, parent component manifest, compatibility state, ontology locks, and semantic domains.
2. Corpus without a profile returns `profile_not_found` without invented mappings.
3. Multi-corpus concept comparison reports independent status per corpus.
4. Default one-corpus capability summary is ≤ 8 KiB serialized JSON.

### Resolution

5. Exact `Noun + Feminine + Plural` fixture resolves to expected native constraints/template.
6. Plausible wrong native feature names are never generated when reviewed mappings exist.
7. Unsupported required constraints make the plan non-executable.
8. Approximate assessments are not executable in exact mode.
9. `related` is never an automatic substitute constraint.
10. `ambiguous` returns alternatives and no executable plan.
11. Resolver output is deterministic for identical request/profile/ontology-lock/parent-component inputs.

### Execution

12. `semantic_search` executes exactly the resolver plan.
13. Results include compact resolution provenance.
14. Count/statistics/result modes preserve resolution identity.
15. Pagination cannot switch profile, ontology lock, or parent component manifest.
16. Native Context-Fabric `search()` remains unchanged by installing ontoTF.

### Compatibility and failure behavior

17. A changed component set with complete validated dependency closure may be `verified-compatible` and executable.
18. Different parent component set cannot become executable merely because feature names, metadata, or TF bytes appear compatible; complete dependency validation is required.
19. `unverified` profiles can be inspected but cannot be passed to normal semantic execution.
20. `incompatible` profiles cannot execute and identify the failed required dependency.
21. Missing ontology-lock term prevents profile activation/resolution.
22. Peshitta morphology request fails unsupported rather than widening to unconstrained words.
23. ORACC sentence labels do not automatically satisfy BHSA linguistic-sentence semantics.
24. TLHdig lexical occurrence queries do not use technical `lex.oslots` as occurrence extent.
25. Peshitta/TLHdig witness-like assertions cannot satisfy Pseudepigrapha reading-attestation semantics without reviewed mapping.
26. Expected semantic domain failures use MCP tool-error state rather than successful error prose.

### Explainability and mapping governance

27. Every executable plan exposes parent component manifest, component identities, dependency evidence, profile/mapping version, ontology lock, mapping assessment, and native constraint path.
28. Full explanation retrieves rationale/source/review metadata for each mapping assertion.
29. Mapping assessment and publication relation are separate machine fields.
30. Mapping-level `exact` never implies parent `verified-exact`, OWL equivalence, or `owl:sameAs`.
31. `broader` and `narrower` expose their under-coverage/over-coverage effect before approximate execution.
32. `native-only` and `unsupported` expose no external target; ambiguous mappings do not auto-project.
33. Research-stage R-005 `S` classification alone cannot compile into an executable `exact` mapping.

### Human authoring and generated artifacts

34. Canonical mapping YAML validates against schema.
35. Generated RDF/JSON/docs/runtime index are reproducible and carry source digest.
36. Editing generated artifact without canonical source update fails generation/check gate.
37. No reverse-generation path silently modifies canonical YAML from RDF/Turtle.
38. Coverage reports state explicit denominators and count native-only/unsupported states.
39. Semantic diff separates assessment, publication relation, native constraint, ontology lock, parent evidence, and prose-only changes.

### Dense-record semantics

40. Empty-string/`None` dense TF records are excluded from semantic capability domains.
41. Empty dense records do not expand a feature's advertised applicable node types.
42. Empty native values cannot satisfy an explicit absence, omission, non-attestation, unknown, damage, or uncertainty constraint without reviewed source assertion.
43. Capability/coverage output may report raw empty-record counts diagnostically without counting them as mapped semantic values.

### Agent and MCP efficiency

44. Exact one-corpus query plans and executes in at most two semantic calls after discovery.
45. Typical multi-corpus comparison needs one capability call and one resolution call before execution.
46. Default concept lookup is bounded to 20 candidates per concept and paginates beyond that.
47. No default tool returns a whole ontology/mapping bundle; structured output fields are schema-defined.
48. Tool/schema validation errors, semantic-domain errors, `unverified`, and `incompatible` states are machine-distinguishable.
49. **Legacy/handshake host and 2026 stateless host produce equivalent semantic resolution semantics** for the same corpus/profile/request; negotiated-protocol transport/session metadata may differ, but resolution meaning, compatibility state, assessment, provenance, and native plan do not.

## 17. Rejected alternatives

### Semantic aliases inside native `search()`

Rejected because it hides projection/provenance and makes native syntax unstable when mappings change.

### Resolver only

Rejected because agents would copy and potentially mutate plans between calls.

### Semantic search without resolver

Rejected because cross-corpus and approximate semantics need inspectable planning before execution.

### Turtle as sole canonical source

Rejected because mapping review needs readable native constraints, applicability, rationale, and evidence.

### Multiple co-equal editable formats

Rejected because round-trip ambiguity produces competing sources of truth.

### Parent compatibility from repository/version/schema labels

Rejected. R-001 requires component identities and complete dependency validation.

### Assume the current host implements the newest protocol revision

Rejected. Context-Fabric `cfabric-mcp 0.1.7` currently pins `mcp>=1.0,<2`, while the current protocol target is `2026-07-28`. ontoTF must work according to the actually negotiated protocol and keep semantic behavior independent of protocol-era session mechanics.

## 18. Unresolved implementation questions

Later design work must choose:

1. exact expression syntax;
2. exact JSON Schemas and error-code namespace;
3. whether semantic tools live inside Context-Fabric MCP or a composed adapter/server;
4. resolution fingerprint lifetime/caching under each negotiated MCP transport/protocol era;
5. exact YAML schema and file granularity;
6. multi-corpus result grouping/pagination;
7. whether a dedicated explanation tool becomes justified after payload benchmarking;
8. reviewer-provenance representation independent of one forge identity;
9. final token/payload limits after real full-profile benchmarks.

These questions do not reopen the hybrid workflow, component-aware compatibility gate, assessment/publication split, protocol-portable semantic behavior, fail-closed behavior, or one-way authoring model.

## 19. Acceptance trace

- Minimum workflow: explicit capability discovery → resolution → execution, with cached discovery allowed.
- Native/semantic boundary: native search stays native; semantic tools expose deterministic projection.
- Capability reporting: bounded per-corpus/per-concept structured data.
- Mapping semantics: all R-002 assessments remain formalism-neutral and separate from publication relations.
- Compatibility: R-001 component manifest and complete dependency closure determine executability.
- Provenance: every plan exposes native constraints, component identity/evidence, mapping version, ontology lock, and assessment.
- Protocol portability: semantic resolution meaning is invariant across negotiated handshake-era and `2026-07-28` stateless hosts; only protocol/transport metadata may vary.
- Human authoring: schema-validated YAML is canonical; derived forms are one-way generated.
- Safety: no silent widening/narrowing, no candidate auto-promotion, no dense-empty semantic invention.
- Efficiency: bounded payloads and tool calls.
- TDD: the 49 criteria above are the single canonical implementation-test seed list.

## 20. Sources

Primary inspected sources:

- Context-Fabric repository and MCP implementation at `Context-Fabric/context-fabric@3a38ca80e617d872ce1664e0f0740486d0e7e8ac`;
- `cfabric-mcp` package metadata at version `0.1.7`, including its `mcp>=1.0,<2` dependency;
- Model Context Protocol `2026-07-28` specification/release material at `https://modelcontextprotocol.io/` and `https://blog.modelcontextprotocol.io/posts/2026-07-28/`;
- official MCP Python SDK version/revision documentation distinguishing the v1 maintenance line from the v2 `2026-07-28` implementation line;
- accepted R-001 distribution architecture / PR #8;
- accepted R-002 ontology governance / PR #9;
- accepted R-005 empirical corpus census / PR #7.

Any future material change to R-001, R-002, R-005, or the host/protocol compatibility premise requires a new R-003 reconciliation and fresh exact-head review.
