# I-004 implementation plan: cross-artifact semantic validation

**Issue:** #36  
**Research:** `docs/research/I-004-cross-artifact-semantic-validation.md`  
**Architecture:** P-003 merged `fac75d5a251945653a7be585fa30eae34afd4693`

## 1. Goal

Implement a deterministic fail-closed semantic-source validator that runs after I-001 structural validation and before compatibility/IR compilation.

No filesystem/network/corpus query inspection is performed by this ticket.

## 2. Public API

Add `src/ontotf/semantic_validation.py` with public types equivalent to:

```python
@dataclass(frozen=True)
class SemanticArtifact:
    kind: str
    source_name: str
    data: dict[str, Any]

@dataclass(frozen=True)
class SemanticSourceBundle:
    profile: SemanticArtifact
    expected_parent_manifest: SemanticArtifact
    mappings: SemanticArtifact
    ontology_locks: tuple[SemanticArtifact, ...]
    evidences: tuple[SemanticArtifact, ...]
    ontology_bundle: SemanticArtifact | None = None
    bridges: tuple[SemanticArtifact, ...] = ()
    profile_catalog: SemanticArtifact | None = None
    reference_catalog: SemanticArtifact | None = None

@dataclass(frozen=True)
class SemanticValidationProblem:
    category: str
    message: str
    artifact_kind: str
    source_name: str
    path: tuple[str | int, ...] = ()
    related_id: str | None = None

class SemanticValidationError(ValueError): ...

@dataclass(frozen=True)
class ValidatedSemanticBundle:
    bundle: SemanticSourceBundle
    expected_parent_manifest_digest: str
    mapping_semantic_digests: tuple[tuple[str, str], ...]
    indexes: SemanticIndexes


def validate_semantic_bundle(bundle: SemanticSourceBundle) -> ValidatedSemanticBundle: ...
```

Exact names may be adjusted during RED only if tests pin the final public contract before GREEN.

The validator must not mutate input dictionaries.

## 3. Source schema migration owned by I-004

I-004 is the first production slice after P-003, so it owns the minimum schema changes required for semantic validation.

### 3.1 Mapping schema v2

Replace v1 one-target rows with closed v2 native-record objects containing:

```text
mapping_id
corpus_id
native_binding
native_dependencies
profiles
capabilities
native_state
projections
ambiguous_candidates
external_references
evidence
review
mapping_semantic_digest
rationale
```

The mapping document root becomes exact `schema_version: 2`.

All child objects are closed (`additionalProperties: false`).

### 3.2 Projection schema

Required fields:

```text
projection_id
target
reference_kind
query_role
formal_kind
semantic_role
profile_id
capability_id
assessment
ontology_lock
native_execution_binding
evidence
review
projection_semantic_digest
```

Optional fields:

```text
ontology_bundle_requirement
ontology_declaration_evidence
publication_relation
approximation
```

Approved projection assessments are exactly:

`exact | close | broader | narrower | related`.

### 3.3 Ambiguous candidate schema

Use the P-003 closed candidate envelope. No execution, approximation or positive publication authorization fields are allowed.

### 3.4 External reference schema

Closed kinds:

```text
entity-identity
catalogue-identifier
provenance-source
locator
```

Reference records must have stable `reference_id` so duplicate/reference diagnostics are deterministic.

Kind-specific required fields are pinned in RED.

### 3.5 Profile schema migration

Keep P-002 `schema_version: 2` dependency contract intact for this ticket unless changing the profile root is necessary to remove execution reliance on free-form `semantic_domains`.

Preferred minimal migration:

- retain `semantic_domains` temporarily as non-authoritative descriptive metadata if backwards-compatible packaging requires it;
- add exact `profile_catalog_version` and controlled `profiles` / `capabilities` declarations;
- semantic validator ignores `semantic_domains` for authority.

If JSON Schema cannot safely express this without changing source semantics, bump profile schema to v3. RED must decide before GREEN; do not silently reinterpret profile v2.

## 4. Canonical vocabulary constants

Add one production vocabulary module, e.g. `src/ontotf/semantic_vocabulary.py`, exporting frozen sets/tuples for P-003 v1:

- formal kinds;
- semantic roles;
- target-bearing reference/query-role pairs;
- non-projection reference/query-role pairs;
- mapping assessments;
- native no-target states;
- profile states;
- profile IDs;
- capability IDs;
- identity strengths;
- approximation modes/loss tokens.

Do not duplicate these strings independently across validator/compiler/resolver modules.

Unknown aliases/case variants fail closed.

## 5. Mapping-v2 semantic digests

Add new versioned constants/functions in `ontotf.digests`:

```text
PROJECTION_SEMANTIC_ALGORITHM = tfont-projection-semantic-sha256-v1
MAPPING_SEMANTIC_ALGORITHM_V2 = tfont-mapping-semantic-sha256-v2
```

Keep old `MAPPING_SEMANTIC_ALGORITHM` behavior available for v1 tests/releases unless explicit deprecation tests prove it can be renamed compatibly.

### 5.1 Projection digest

Projection semantic identity includes every field that can affect target resolution/execution/publication semantics:

- projection ID only if ID is semantically identity-bearing under the existing digest philosophy;
- target;
- routing kind/query role;
- formal kind/semantic role;
- profile/capability;
- assessment;
- ontology lock/bundle requirement;
- declaration evidence;
- publication relation;
- native execution binding;
- approximation contract;
- evidence bindings.

Exclude review wrapper, authored digest field and rationale/audit metadata.

### 5.2 Mapping-v2 digest

Mapping semantic identity includes normalized:

- mapping ID;
- corpus ID;
- native binding;
- dependency IDs as set-like strings;
- profiles/capabilities as set-like controlled IDs;
- native state;
- approved child projection semantic identities;
- typed ambiguous candidates;
- external references where they affect query/reference semantics;
- mapping-level evidence.

Child projection list ordering is non-semantic and normalized by stable identity/digest. Duplicate child IDs/digests fail closed rather than silently deduplicate.

Old v1 digest cannot validate v2.

## 6. Exact diagnostic categories

Freeze v1 categories now:

```text
unsupported_contract_version
duplicate_id
missing_reference
component_authority
unknown_vocabulary
invalid_record_state
invalid_projection
invalid_candidate
invalid_reference_routing
kind_role_conflict
unknown_ontology_target
bundle_closure
bridge_closure
evidence_digest_mismatch
stale_semantic_digest
stale_review_binding
native_semantics_unproven
invalid_approximation
invalid_publication_relation
```

I-001 structural/schema errors remain `SourceValidationError` and never get translated into I-004 semantic categories.

## 7. Deterministic validation order

Pin exact phase precedence:

1. supported semantic/profile/catalog contract versions;
2. duplicate ID indexing;
3. parent/profile component authority;
4. P-002 dependency closure;
5. controlled vocabulary membership;
6. native-record state consistency;
7. projection/candidate/reference cross-field legality;
8. ontology lock + `terms_used` target membership;
9. bundle/bridge source closure/content binding;
10. evidence binding/digest equality;
11. mapping/projection semantic digest + review binding;
12. P-002 dense-value/closed-domain semantic-source proof;
13. approximation contract validity;
14. publication relation legality;
15. result/index assembly.

Within a phase, iterate canonical UTF-16-sorted IDs, not authored list order.

First failure only is the v1 public behavior.

## 8. Required semantic checks

### 8.1 Components/dependencies

- every required component exists in expected parent manifest;
- dependency component belongs to required components;
- every mapping dependency resolves uniquely;
- dependency evidence resolves/digest matches;
- native binding component, where explicit, is authorized by dependency/component scope.

### 8.2 Record state

- `positive`: approved projections allowed; candidates forbidden unless a later explicit mixed state is versioned;
- `ambiguous`: zero approved projections, at least one typed candidate;
- `native-only`: zero projections/candidates;
- `unsupported`: zero projections/candidates.

Non-target external references may coexist with positive/native-only records where semantically valid.

### 8.3 Projection routing/kind/role

Enforce exact P-003 vocabulary pairs and R-013 matrix.

### 8.4 Candidate restrictions

Candidate requires full target identity/routing/kind/role/profile/capability/lock/evidence envelope and cannot contain:

- executable plan authorization;
- approximation authorization;
- positive publication relation.

### 8.5 External references

Enforce exact kind/query-role routing, identity-strength vocabulary and scoped identifier authority/value requirements.

### 8.6 Target membership

Approved projection/candidate target must be in exact referenced lock `terms_used`.

No URI syntax inference.

### 8.7 Evidence/review

Every evidence binding resolves by ID and exact digest.

Projection review must bind projection semantic digest. Mapping review must bind mapping-v2 semantic digest.

Audit-only review provenance changes do not change semantic digest.

### 8.8 Dense empty/domain semantics

A semantic empty/null mapping requires matching P-002 `native-value-present` dependency with exact value and `value_semantics=semantic`.

Closed-domain use requires `value-domain` with `closed-reviewed` + evidence; `observed` is insufficient.

### 8.9 Approximation

Only `close|broader|narrower` may carry approximation authorization.

- broader eligible -> losses exactly `{undercoverage}`;
- narrower eligible -> losses exactly `{overcoverage}`;
- close eligible -> non-empty subset of `{undercoverage, overcoverage}`;
- related/exact cannot use non-exact approximation authorization.

### 8.10 Publication

Do not derive predicates from assessment.

Locally validate only relations provable from formal kind/reference identity. Unknown/custom/noncanonical spellings fail closed.

## 9. RED sequence

Commit RED tests before production code.

### RED-A: schema/vocabulary setup

Tests assert that the intended v2 fixture shapes are structurally valid against **test-local provisional schemas/fixtures** or deliberately construct objects after I-001 setup so failures target missing I-004 API, not an accidental v1 schema rejection.

Then import `ontotf.semantic_validation`; RED must fail because module/API does not exist.

### RED-B: valid bundle and deterministic index

One minimal valid bundle with:

- one component;
- one P-002 dependency;
- one exact semantic-pivot projection;
- one authority-value projection;
- one non-projection provenance reference;
- one ontology lock containing both target terms;
- evidence and review bindings.

Expected: validated result + deterministic indexes/fingerprints.

### RED-C: adversarial matrix

Cover the 24+ research cases plus exact category/path assertions.

### RED-D: digest migration

Pin fixed vectors for projection-v1 and mapping-v2 digests.

- object/list authored order controls;
- audit-only review edit unchanged;
- target/routing/kind/role/capability/approximation edit changes digest;
- old v1 digest rejected as mapping-v2 digest.

## 10. GREEN implementation order

1. semantic vocabulary constants;
2. mapping-v2 digest projection/functions + tests;
3. mapping-v2/profile source schema amendments + packaging tests;
4. semantic validation dataclasses/error/result types;
5. deterministic index builder;
6. phases 1-5;
7. record/projection/candidate/reference rules;
8. lock/target/bundle/bridge closure;
9. evidence/review/digest binding;
10. dense-value/domain checks;
11. approximation/publication checks;
12. validated result assembly.

Do not build semantic reverse indexes beyond source ID indexes in this ticket.

## 11. Focused and full test gates

Exact-head CI must include Python 3.10 and 3.12 for:

- I-004 focused suite;
- I-001 structural/source schema suite;
- I-002 digest suite;
- P-002 profile dependency suite;
- I-003 parent identity suite;
- packaging wheel/sdist schema resources;
- full repository unittest discovery.

## 12. Non-goals

- compatibility-state evaluation;
- parent TF filesystem inspection;
- ontology network fetch/dereference;
- SPARQL/RDF reasoner execution;
- semantic IR reverse-index compiler;
- Context-Fabric query execution;
- request-time semantic mode/loss acceptance;
- final seven-corpus mapping release;
- fuzzy/label/namespace inference.

## 13. Independent adversarial review gate

Fresh exact-head review must try to falsify:

- v1 single-target semantics leaking through migration;
- duplicate/reference nondeterminism;
- profile/capability acting as execution authority;
- ambiguous candidate accidentally becoming approved/executable;
- authority-value leaking into semantic target space;
- provenance/locator becoming query target by URI presence;
- old mapping digest accepting new semantics;
- audit metadata incorrectly affecting semantic identity;
- dense empty or observed finite domain being promoted silently;
- bundle/bridge source closure being confused with runtime compatibility;
- approximation bypassing upstream validity;
- publication relation derived mechanically from assessment;
- any filesystem/network/outside-TF runtime surface added.

Merge only with exact-head focused/full CI green and no blocker.