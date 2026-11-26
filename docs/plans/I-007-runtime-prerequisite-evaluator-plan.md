# I-007 plan — runtime prerequisite evaluator

**Issue:** #130  
**Research authority:** `docs/research/I-007-runtime-prerequisite-evaluator.md`  
**Gate:** plan only; no production implementation in this branch

## Goal

Implement the production boundary that derives the I-006 `RuntimePrerequisiteState` from a currently observed, already-materialized Text-Fabric / Context-Fabric corpus and one current I-005 `BundleVariantIR`, without performing semantic resolution, query execution, corpus loading, network access, or ontology dereferencing.

The implementation must preserve this authority flow:

`trusted compiled variant + observed materialized TF state + observed parent identity + selected local ontology-bundle identity -> deterministic observation facts -> pure dependency evaluation -> runtime report -> I-006 prerequisite projection`

The report is content identity, not producer authentication. Across an untrusted serialization/process boundary it must not become execution authority merely because its public digest recomputes.

## Preconditions

1. Research for I-007 is merged and reviewed.
2. I-006 public prerequisite dataclasses/constants must be merged before I-007 production code begins. The implementation must import/reuse them; it must not duplicate a competing prerequisite type.
3. I-005 `BundleVariantIR` / `ProfileReleaseSignature` remain compile-time authority for release identity and canonical dependency records.
4. I-003 remains the parent/component content-identity authority. I-007 does not invent another filesystem identity algorithm.

If I-006 is not merged when this plan is accepted, only tests/fixtures that do not duplicate production types may be prepared; GREEN production waits.

## Production module boundary

Add one focused module, tentatively `src/ontotf/runtime_prerequisites.py`.

Public surface should remain small:

- `evaluate_runtime_prerequisites(variant, observation, *, source_contract, active_ontology_bundle_digest=...) -> RuntimeEvaluationReport`
- `RuntimeEvaluationReport`
- one narrow observation protocol/type suitable for synthetic tests and an already-loaded TF adapter
- a helper/property that projects the report to the exact I-006 `RuntimePrerequisiteState`
- versioned report/observation fingerprint constants.

Do not add resolver functions, execution functions, query-string builders, MCP/session APIs, generic source adapters, network loaders, or ontology clients.

## Observation model

Separate observation from evaluation.

The pure evaluator consumes deterministic facts through a narrow observation interface. The concrete TF adapter translates an already-loaded TF/Context-Fabric API into those facts but owns no compatibility policy.

The observation interface must support only facts required by the eight P-002 dependency kinds:

- current component presence/identity;
- node-type occurrence/presence;
- node-feature availability scoped to node type/component;
- edge-feature availability for requested direction;
- ordered edge-step availability for path shape;
- complete observed scalar values for a node feature when enumeration is supported;
- explicit extent-interpretation metadata.

The adapter must distinguish:

- known present/pass evidence;
- known absent/fail evidence;
- inability to establish a fact or completeness (`unknown`).

It must not silently convert API exceptions, unloaded feature state, missing adapter metadata, or incomplete enumeration into positive evidence.

## Exact dependency semantics

Parse every `ProfileReleaseSignature.dependency_records` canonical JSON record. All release dependencies participate; target-local partial activation is out of scope.

### `component-present`

`pass` iff the dependency component is known present in the observed current parent manifest. Known absence is `fail`; inability to establish the component manifest is `unknown`.

### `node-type-present`

`pass` iff at least one node of the authored type is deterministically observed in the dependency component. A known inspected component with zero nodes of that type is `fail`; inability to inspect is `unknown`.

The plan intentionally treats this as occurrence/presence, not merely existence of an `otype` label in metadata.

### `feature-present`

`pass` iff the authored node feature is deterministically available for the declared node type/component under the loaded TF contract. Same-named metadata elsewhere does not count. Unreadable/unloaded state is `unknown`, not pass.

### `edge-present`

`pass` iff the edge feature is available and the requested direction can be represented by the loaded TF graph API. Because Text-Fabric normally permits reverse traversal of an edge feature, direction must be tested as traversal capability rather than invented as an independent stored feature. If the adapter cannot establish directional traversal capability, return `unknown`.

### `path-present`

Evaluate ordered edge/direction steps as **execution-shape availability**, not extensional existence of a result path. Every step must be representable; known missing step is `fail`; inability to establish any step is `unknown` unless another step already deterministically fails. Do not run corpus-wide path searches merely to prove occurrence.

### `native-value-present`

Enumerate the complete observed feature values for the declared node type/component. `pass` iff the exact authored JSON scalar occurs; `fail` iff complete enumeration succeeds and the value is absent; otherwise `unknown`.

Scalar identity is JSON identity, not Python loose equality. In particular:

- `null` is distinct from missing/unavailable;
- `false` is distinct from `0`;
- `true` is distinct from `1`;
- strings are never coerced to numbers/booleans;
- only finite JSON numbers are valid.

Use a tagged canonical scalar key internally if needed; do not rely on Python set equality for bool/int.

### `value-domain: observed`

Declared values are required observed support facts. `pass` iff complete enumeration proves each declared scalar occurs. Additional observed values are allowed. Known complete absence of a required scalar is `fail`; incomplete enumeration is `unknown` unless a deterministic failure is otherwise established.

### `value-domain: closed-reviewed`

The reviewed declaration is the allowed closed domain. After complete enumeration, `pass` iff every observed non-missing scalar is a member of the reviewed domain. Any observed out-of-domain scalar is `fail`. A reviewed allowed scalar need not occur in the current release. Incomplete enumeration is `unknown`.

### `extent-interpretation`

Never infer this from `oslots`, node counts, zero length, or topology. Require an explicit deterministic local adapter/corpus metadata fact for the node type/component. Exact match is `pass`, known conflicting explicit interpretation is `fail`, absence/unavailability is `unknown`.

## Canonical dependency-record validation

Before evaluation, validate release input fail-closed:

1. variant must be exact `BundleVariantIR` and internally coherent enough for the I-006/I-005 release fingerprint contract;
2. every dependency record must be a two-item `(dependency_id, canonical_json_string)` tuple;
3. IDs must be unique and non-empty;
4. canonical JSON must decode to an exact object whose `dependency_id` matches the tuple key;
5. record must use dependency contract version 1 and one of the eight P-002 kinds;
6. kind-specific assertion must match the already-frozen P-002 shape;
7. malformed release records are typed evaluator/compiled-input errors, never dependency `unknown`.

Do not reimplement the whole source schema validator if a small reusable validated parser can safely reuse existing source/schema helpers. But evaluation must not trust arbitrary hand-built malformed `ProfileReleaseSignature` rows just because the dataclass type matches.

Deterministic malformed-input precedence: variant/type/coherence -> duplicate/malformed dependency envelope -> malformed assertion -> observation input shape -> compatibility evaluation.

## Dependency result aggregation

Return exactly one deterministic result per release dependency, canonically ordered by UTF-16 key order consistent with existing ontoTF deterministic ordering.

Each result carries:

- `dependency_id`;
- `result = pass | fail | unknown`;
- versioned evaluator rule identifier;
- `observed_evidence_digest` when a deterministic observation projection exists.

Overall state:

- any deterministic `fail` => `incompatible` (fail dominates unknown);
- else any `unknown` => `unverified`;
- else exact observed parent digest => `verified-exact`;
- else changed observed parent digest => `verified-compatible`.

`verified-compatible` therefore means changed parent plus complete deterministic passing closure, never digest similarity.

## Evidence fingerprints

Add a versioned observation-fingerprint algorithm over stable canonical JSON projections. Include only the fact actually used to decide the dependency, such as component digest/presence, node/feature/edge capability fact, tagged scalar/domain observation, or explicit extent interpretation.

Do not hash:

- local filesystem paths;
- host/user/PID/session identifiers;
- object repr/address;
- timestamps;
- display/log strings.

For `unknown`, `observed_evidence_digest` may be `None` when there is no deterministic observation to bind. For deterministic `pass` or `fail`, prefer a non-null observation digest and pin this in RED tests.

## Parent and bundle state

The evaluator receives the observed parent manifest digest from the I-003-compatible observation boundary. It does not recompute a second parent identity algorithm.

Bundle handling:

- release requires no ontology bundle -> resolver-facing state exactly `not-required`, active digest `None`;
- required digest selected locally and equal -> `verified` with exact digest;
- required bundle unavailable -> `unavailable`, non-executable;
- a different explicitly selected active digest -> stale/mismatched runtime input, not corpus semantic incompatibility;
- malformed/empty digest -> typed invalid input.

No live ontology fetching or bridge re-evaluation. I-004/I-005 already bind reviewed bridge/lock closure into release identity.

## Runtime report

`RuntimeEvaluationReport` must bind at least:

- report contract/version;
- full `BundleVariantKey`;
- I-006 `profile_release_fingerprint` of current release signature;
- observed parent manifest digest;
- aggregate compatibility state;
- canonical dependency results;
- active ontology-bundle digest/state;
- source/evaluator contract;
- deterministic report fingerprint.

Its projection to I-006 must preserve these facts exactly and construct the existing `RuntimePrerequisiteState`, not a lookalike type.

Old `compatibility-report.schema.json` / `profile_semantic_digest` data is historical only. There is no converter that can emit executable current prerequisite state solely from those fields.

## Trust boundary

The public report/prerequisite fingerprint is cache/content identity only.

Tests and docs must reject the claim that a serialized report becomes trusted because its hash recomputes. Same-process execution can trust a report because trusted code just evaluated current trusted inputs. A remote/untrusted serialized report must be re-established locally or carried by a separately authenticated channel outside I-007.

No signing/MAC/key-management feature is added here.

## TDD RED sequence

The implementation branch begins from current main after I-006 merge.

Commit tests before production code. Required RED matrix:

1. module/public evaluator sentinel missing;
2. exact parent + all pass -> `verified-exact`;
3. changed parent + all pass -> `verified-compatible`;
4. fail -> `incompatible`;
5. unknown -> `unverified`;
6. fail + unknown -> `incompatible` independent of dependency order;
7. every release dependency appears exactly once in canonical output;
8. malformed/duplicate dependency record fails before observation evaluation;
9. stale release fingerprint/variant reuse is rejected rather than reclassified as corpus incompatibility;
10. bundle no-required/exact/unavailable/wrong/empty states;
11. report/prerequisite fingerprints change under parent, dependency observation/result, evaluator rule/source contract, bundle and release changes;
12. timestamps/local paths/object identities cannot affect fingerprints;
13. each of all eight dependency kinds has pass/fail/unknown cases where meaningful;
14. path semantics prove ordered step capability, not incidental corpus path occurrence;
15. JSON scalar tests distinguish `None`, missing, `False`, `0`, `True`, `1`, numeric and string forms;
16. `observed` value-domain allows extras but requires declared observations;
17. `closed-reviewed` rejects extras outside closure but permits allowed values absent from current release;
18. absent explicit extent metadata -> unknown; conflicting explicit metadata -> fail; matching -> pass;
19. observation adapter exception/unloaded/incomplete states fail closed to unknown, never positive evidence;
20. deterministic observation digest exists for known pass/fail and is stable under irrelevant ordering;
21. old v1 compatibility-report-shaped data cannot produce executable current prerequisite state;
22. no call path performs semantic resolution, Context-Fabric search/query execution, network fetch, or ontology dereference;
23. exact projection is accepted by merged I-006 resolver for a valid exact mapping fixture;
24. serialized/reconstructed report is not exposed/documented as authenticated authority.

The RED commit must be run on Python 3.10 and 3.12. Fixture/control tests must first prove the synthetic observation harness itself is valid. Only expected missing evaluator/behavior assertions may fail; existing I-006/I-005/I-004 suites must remain green.

## Minimal GREEN sequence

1. immutable result/report/observation types and version constants;
2. strict canonical dependency record parser;
3. JSON-scalar identity helper;
4. pure per-kind dependency evaluator;
5. deterministic observation/result/report fingerprinting;
6. aggregate compatibility-state evaluator;
7. exact I-006 prerequisite projection;
8. narrow concrete adapter for already-loaded TF API, with unsupported facts returning unknown;
9. package-root exports only after focused API contract is green.

Do not add optimization/cache persistence until behavior is green. In-memory memoization is unnecessary for the first implementation unless profiling proves a material issue.

## TF adapter proof

Core contract tests use synthetic observations only. Add at most a small local fake/minimal TF API shape to prove the concrete adapter uses the expected public access pattern. Do not download BHSA or another corpus in CI.

If the Text-Fabric package itself is not already a runtime dependency, do not add it merely for import-time typing. The adapter should use structural duck typing / a narrow protocol and import no notebook/app layer. A separate integration environment can later test against a real corpus.

## CI

Add a dedicated I-007 focused workflow after RED is established. Python 3.10/3.12 matrix. Trigger on:

- `src/ontotf/runtime_prerequisites.py`;
- I-006 resolver/prerequisite public module if relevant;
- I-005 semantic IR;
- dependency/profile schema and P-002 contract paths;
- `tests/i007/**`;
- I-007 research/plan/workflow.

Focused workflow runs:

- I-007 tests;
- I-006 resolver regressions;
- I-005 semantic IR regressions;
- P-002 dependency contract tests;
- I-004 semantic validation regressions if runtime remains reasonable.

Do not duplicate the authoritative full-suite command inside the focused workflow; repository full-suite remains a separate exact-head required gate.

## Documentation sub-gate

Only after behavior is GREEN, add a documentation RED requiring contributor/user-facing documentation to state:

- runtime prerequisite evaluator derives state from observed materialized TF state;
- exact vs compatible vs unverified vs incompatible semantics;
- closed-reviewed domain is an allowed closure, not an occurrence checklist;
- extent interpretation is explicit, never topology-inferred;
- old v1 compatibility reports are not execution authority;
- report fingerprints do not authenticate producers.

Then update documentation minimally to satisfy that RED.

## Independent adversarial review before merge

Fresh review must be anchored to the final exact head and attack at least:

- duplicate/malformed release dependency rows;
- bool/int and null/missing scalar confusion;
- false positive feature/edge/path availability;
- incomplete enumeration accidentally becoming pass/fail instead of unknown;
- closed-domain equality regression;
- extent inference from topology;
- fail-vs-unknown precedence;
- stale report/variant/bundle reuse;
- deterministic ordering/fingerprint instability;
- volatile deployment data entering identity;
- old compatibility report privilege escalation;
- report-hash authentication overclaim;
- accidental resolver/query/network/ontology execution;
- duplicated I-006 prerequisite type;
- CI trigger gaps and full-suite duplication.

Any material review finding gets a tests-only RED first, then minimal GREEN, followed by new exact-head CI and a fresh final review. Head movement invalidates the previous final review.

## Exit condition

I-007 is complete only when ontoTF can take one current compiled variant plus deterministic observations of an already-materialized corpus and produce a current fail-closed prerequisite state that the I-006 resolver accepts, with all release dependencies evaluated, exact parent/bundle/release identity preserved, unknown evidence non-executable, and no trust or execution capability inferred from a public report hash.