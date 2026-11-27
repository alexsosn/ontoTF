# A-001 post-review plan: reconcile P-001/I-001 with the TF-native runtime boundary

**Issue:** #65  
**Parent plan:** `docs/plans/A-001-tf-native-runtime-boundary-plan.md`  
**Recorded:** 2026-09-07  
**Gate:** post-review plan amendment before new RED tests or normative corrections

## 1. Review finding

The first A-001 head corrected R-005/R-007 and the open P-002/P-003 contracts, but it did not explicitly reconcile the already-accepted P-001/I-001 baseline.

Historical P-001 sections 6–7 still describe `external/native sidecar`, `zero-span` stores and `native-adapter` as semantically addressable component kinds, and describe `sidecar-zero-span`, adapter-capability/version and sidecar field/path dependency kinds. The current v1 parent-component schema still accepts legacy component-kind labels including `sidecar`, `catalogue`, `zero-span` and `native-adapter`.

Those facts must not be silently rewritten, but neither may they remain an alternative executable architecture after A-001.

## 2. Required distinction

A-001 must distinguish two roles that P-001 previously conflated:

1. **parent/component identity** — a compatibility manifest may identify an auxiliary corpus artifact whose bytes/version affect the reviewed parent identity or provenance;
2. **executable native query carrier** — the objects/selectors against which a ontoTF semantic request compiles and executes.

A non-TF artifact may remain represented for legacy/component identity without becoming a query carrier. Component identity does not authorize arbitrary file/record/field addressing, parsing, dereferencing, or adapter execution.

Baseline executable resolution after A-001 is TF/Context-Fabric-native.

## 3. P-001 supersession amendment

Add `docs/plans/P-001-tf-native-runtime-boundary-amendment.md` and preserve `P-001-foundation-poc-design.md` verbatim as historical accepted design evidence.

The amendment must explicitly supersede only the executable external-carrier conclusions in P-001 sections 6–7:

- `native-adapter` is not a baseline executable carrier;
- `adapter capability/version invariant` is not a baseline dependency kind;
- `sidecar field/path invariant` is not a baseline dependency kind;
- `sidecar-zero-span` is not a TF extent mode for current textual zero-span data;
- ORACC textual zero-span entities follow materializer-owned synthetic/empty TF-slot semantics.

The amendment must preserve still-valid P-001 contracts: component-aware parent identity, deterministic compatibility evidence, review/evidence binding, compatibility states, and fail-closed activation.

## 4. v1 schema migration boundary

Do not mutate the v1 parent-component schema in this architecture-only correction. Changing enum acceptance in place would be an unversioned source-contract break and would exceed the reviewed A-001 production scope.

Instead, the amendment must state that current v1 labels `sidecar`, `catalogue`, `zero-span` and `native-adapter` are **legacy identity compatibility labels** when old artifacts are read. Their structural acceptance does not authorize executable/query-carrier semantics.

For post-A-001 baseline design:

- no new profile/dependency contract may rely on `native-adapter` as an executable component;
- no mapping may gain executable authority from a sidecar/catalogue/zero-span component label alone;
- P-002/P-003 must decide the versioned schema migration/removal or replacement of legacy labels without treating them as runtime carriers.

This keeps old source artifacts readable while preventing schema permissiveness from becoming runtime permission.

## 5. RED contract

Before adding the P-001 amendment, extend `tests/architecture/test_tf_native_boundary.py` so current A-001 fails because the reconciliation is absent.

The regression must prove:

1. a P-001 TF-native supersession amendment exists and names sections 6–7;
2. `native-adapter`, adapter-capability/version, sidecar field/path and sidecar-zero-span executable interpretations are explicitly superseded;
3. legacy v1 component-kind acceptance is classified as identity compatibility only and explicitly does **not** authorize an executable/query carrier;
4. the versioned cleanup is delegated to P-002/P-003 rather than silently changing v1;
5. still-valid parent identity/compatibility contracts are preserved.

The test must inspect the actual production v1 parent-component schema so it cannot pass merely because new prose says “TF-native” while the existing source contract is ignored.

## 6. GREEN correction

Add only the P-001 supersession/migration amendment and any minimal A-001 prose needed to reference it. Do not modify production Python or v1 schema semantics in this PR.

Then run:

- focused A-001 architecture tests;
- the exact-head repository suite with packaging test frontend installed;
- all overlapping PR workflows triggered by the current integration head.

## 7. Final independent review

A new reviewer/context that did not author this correction must challenge:

- whether identity-only legacy component labels can still leak into executable selector/dependency semantics;
- whether the amendment accidentally prevents legitimate parent/provenance identity tracking;
- whether keeping v1 structurally backward-readable creates an undocumented runtime loophole;
- whether P-002/P-003 migration responsibility is explicit enough to be mechanically actionable;
- whether current-main integration remains exact after concurrent merges.
