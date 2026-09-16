from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

from .digests import canonical_json_bytes
from .semantic_ir import (
    BundleVariantIR,
    BundleVariantKey,
    CapabilityFactsIR,
    CapabilityKey,
    CompiledSemanticIR,
    EdgeStepIR,
    EvidenceFingerprint,
    NativeBindingIR,
    OntologyBundleRequirementIR,
    OntologyLockFingerprint,
    ProfileReleaseKey,
    ProfileReleaseSignature,
    ReviewFingerprint,
    SemanticKey,
    TargetBindingIR,
    native_binding_identity,
)
from .semantic_vocabulary import CAPABILITY_IDS, FORMAL_KINDS, PROFILE_IDS, SEMANTIC_ROLES

EXACT_RESOLVER_CONTRACT = "tfont-exact-semantic-resolver-v1"
PROFILE_RELEASE_FINGERPRINT_ALGORITHM = "tfont-profile-release-signature-jcs-sha256-v1"
RUNTIME_PREREQUISITE_FINGERPRINT_ALGORITHM = "tfont-runtime-prerequisite-jcs-sha256-v1"
EXACT_PLAN_FINGERPRINT_ALGORITHM = "tfont-exact-native-plan-jcs-sha256-v1"
EXACT_RESOLUTION_FINGERPRINT_ALGORITHM = "tfont-exact-resolution-jcs-sha256-v1"


@dataclass(frozen=True)
class DependencyPrerequisiteResult:
    dependency_id: str
    result: str
    observed_evidence_digest: str | None
    evaluator_rule_version: str


@dataclass(frozen=True)
class RuntimePrerequisiteState:
    variant: BundleVariantKey
    profile_release_fingerprint: str
    observed_parent_manifest_digest: str
    parent_state: str
    dependency_results: tuple[DependencyPrerequisiteResult, ...]
    active_ontology_bundle_digest: str | None
    ontology_bundle_state: str
    source_contract: str


@dataclass(frozen=True)
class SemanticResolveRequest:
    key: SemanticKey
    corpora: tuple[str, ...]
    semantic_mode: str = "exact"


@dataclass(frozen=True)
class SemanticCapabilityView:
    corpus_id: str
    variant: BundleVariantKey
    profile_id: str
    capability_id: str
    state: str
    facts: CapabilityFactsIR
    executable_exact: bool
    prerequisite_fingerprint: str


@dataclass(frozen=True)
class ExactNativePlan:
    resolver_contract: str
    corpus_id: str
    semantic_key: SemanticKey
    reference_kind: str
    query_role: str
    semantic_mode: str
    capability_state: str
    variant: BundleVariantKey
    profile_release_fingerprint: str
    expected_parent_manifest_digest: str
    observed_parent_manifest_digest: str
    parent_state: str
    prerequisite_fingerprint: str
    prerequisite_source_contract: str
    mapping_id: str
    projection_id: str
    assessment: str
    native_execution_binding_identity: str
    native_execution_binding: NativeBindingIR
    native_dependencies: tuple[str, ...]
    mapping_semantic_digest: str
    projection_semantic_digest: str
    mapping_review: ReviewFingerprint
    projection_review: ReviewFingerprint
    ontology_lock: OntologyLockFingerprint
    ontology_bundle_digest: str | None
    mapping_evidence: tuple[EvidenceFingerprint, ...]
    projection_evidence: tuple[EvidenceFingerprint, ...]
    plan_fingerprint: str


@dataclass(frozen=True)
class SemanticResolutionResult:
    resolver_contract: str
    request: SemanticResolveRequest
    plans: tuple[ExactNativePlan, ...]
    comparison_state: str
    losses: tuple[str, ...]
    resolution_fingerprint: str


@dataclass(frozen=True)
class SemanticResolutionProblem:
    category: str
    message: str
    corpus_id: str | None = None
    related_id: str | None = None


class SemanticResolutionError(ValueError):
    def __init__(self, problem: SemanticResolutionProblem):
        self.problem = problem
        super().__init__(f"{problem.category}: {problem.message}")


def _fail(
    category: str,
    message: str,
    *,
    corpus_id: str | None = None,
    related_id: str | None = None,
) -> None:
    raise SemanticResolutionError(
        SemanticResolutionProblem(
            category,
            message,
            corpus_id=corpus_id,
            related_id=related_id,
        )
    )


def _utf16(value: str) -> bytes:
    return value.encode("utf-16be")


def _hash(projection: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(projection)).hexdigest()


def _variant_projection(value: BundleVariantKey) -> dict[str, Any]:
    return {
        "corpus_id": value.corpus_id,
        "authored_profile_id": value.authored_profile_id,
        "profile_version": value.profile_version,
        "expected_parent_manifest_digest": value.expected_parent_manifest_digest,
        "ontology_bundle_digest": value.ontology_bundle_digest,
    }


def _semantic_key_projection(value: SemanticKey) -> dict[str, Any]:
    return {
        "profile_id": value.profile_id,
        "capability_id": value.capability_id,
        "target": value.target,
        "formal_kind": value.formal_kind,
        "semantic_role": value.semantic_role,
    }


def _review_projection(value: ReviewFingerprint) -> dict[str, str]:
    if type(value) is not ReviewFingerprint:
        _fail("invalid_compiled_ir", "review fingerprint has the wrong type")
    fields = (value.review_id, value.status, value.reviewed_semantic_digest)
    if any(type(item) is not str or not item for item in fields):
        _fail("invalid_compiled_ir", "review fingerprint fields must be non-empty strings")
    return {
        "review_id": value.review_id,
        "status": value.status,
        "reviewed_semantic_digest": value.reviewed_semantic_digest,
    }


def _lock_projection(value: OntologyLockFingerprint) -> dict[str, str]:
    if type(value) is not OntologyLockFingerprint:
        _fail("invalid_compiled_ir", "ontology lock fingerprint has the wrong type")
    fields = (
        value.lock_id,
        value.ontology_id,
        value.release,
        value.content_digest,
        value.term_namespace,
    )
    if any(type(item) is not str or not item for item in fields):
        _fail("invalid_compiled_ir", "ontology lock fingerprint fields must be non-empty strings")
    return {
        "lock_id": value.lock_id,
        "ontology_id": value.ontology_id,
        "release": value.release,
        "content_digest": value.content_digest,
        "term_namespace": value.term_namespace,
    }


def _evidence_projection(value: EvidenceFingerprint) -> dict[str, str]:
    if type(value) is not EvidenceFingerprint:
        _fail("invalid_compiled_ir", "evidence row has the wrong type")
    if (
        type(value.evidence_id) is not str
        or not value.evidence_id
        or type(value.content_digest) is not str
        or not value.content_digest
    ):
        _fail("invalid_compiled_ir", "evidence fingerprint fields must be non-empty strings")
    return {
        "evidence_id": value.evidence_id,
        "content_digest": value.content_digest,
    }


def _validate_release_signature_rows(signature: ProfileReleaseSignature) -> None:
    if type(signature.parent_compatibility) is not str or signature.parent_compatibility not in {"exact-only", "dependency-verified"}:
        _fail("invalid_compiled_ir", "release parent compatibility policy is invalid")
    vocabulary_specs = (
        ("profiles", signature.profiles, PROFILE_IDS),
        ("capabilities", signature.capabilities, CAPABILITY_IDS),
    )
    for label, values, allowed in vocabulary_specs:
        if type(values) is not tuple:
            _fail("invalid_compiled_ir", f"release {label} must be an exact tuple")
        if any(type(item) is not str or not item for item in values):
            _fail("invalid_compiled_ir", f"release {label} must contain non-empty strings")
        if len(set(values)) != len(values):
            _fail("invalid_compiled_ir", f"release {label} contain duplicate entries")
        if any(item not in allowed for item in values):
            _fail("invalid_compiled_ir", f"release {label} contain unknown vocabulary")
    release_profiles = set(signature.profiles)
    if any(capability.split(".", 1)[0] not in release_profiles for capability in signature.capabilities):
        _fail("invalid_compiled_ir", "release capability is not scoped by a release profile")

    row_specs = (
        ("dependency_records", signature.dependency_records, 2),
        ("mapping_digests", signature.mapping_digests, 2),
        ("mapping_reviews", signature.mapping_reviews, 2),
        ("projection_reviews", signature.projection_reviews, 3),
    )
    for label, rows, arity in row_specs:
        if type(rows) is not tuple:
            _fail("invalid_compiled_ir", f"release {label} must be an exact tuple")
        for row in rows:
            if type(row) is not tuple or len(row) != arity:
                _fail("invalid_compiled_ir", f"release {label} contains an invalid row shape")
            id_fields = row[:-1] if label in {"mapping_reviews", "projection_reviews"} else row
            if any(type(item) is not str or not item for item in id_fields):
                _fail("invalid_compiled_ir", f"release {label} IDs must be non-empty strings")
            if label == "mapping_reviews":
                _review_projection(row[1])
            elif label == "projection_reviews":
                _review_projection(row[2])
    if type(signature.ontology_locks) is not tuple:
        _fail("invalid_compiled_ir", "release ontology_locks must be an exact tuple")
    for lock in signature.ontology_locks:
        _lock_projection(lock)


def _profile_release_projection(signature: ProfileReleaseSignature) -> dict[str, Any]:
    return {
        "algorithm": PROFILE_RELEASE_FINGERPRINT_ALGORITHM,
        "profile_schema_version": signature.profile_schema_version,
        "profile_catalog_version": signature.profile_catalog_version,
        "dependency_contract_version": signature.dependency_contract_version,
        "mapping_schema_version": signature.mapping_schema_version,
        "minimum_tfont_runtime": signature.minimum_tfont_runtime,
        "parent_compatibility": signature.parent_compatibility,
        "profiles": list(signature.profiles),
        "capabilities": list(signature.capabilities),
        "dependency_records": [list(item) for item in signature.dependency_records],
        "mapping_digests": [list(item) for item in signature.mapping_digests],
        "ontology_bundle_digest": signature.ontology_bundle_digest,
        "ontology_locks": [_lock_projection(item) for item in signature.ontology_locks],
        "mapping_semantic_algorithm": signature.mapping_semantic_algorithm,
        "projection_semantic_algorithm": signature.projection_semantic_algorithm,
        "mapping_reviews": [
            [mapping_id, _review_projection(review)]
            for mapping_id, review in signature.mapping_reviews
        ],
        "projection_reviews": [
            [mapping_id, projection_id, _review_projection(review)]
            for mapping_id, projection_id, review in signature.projection_reviews
        ],
    }


def profile_release_fingerprint(signature: ProfileReleaseSignature) -> str:
    if type(signature) is not ProfileReleaseSignature:
        raise TypeError("signature must be ProfileReleaseSignature")
    _validate_release_signature_rows(signature)
    return _hash(_profile_release_projection(signature))


def _validate_dependency_result(value: DependencyPrerequisiteResult) -> None:
    if type(value) is not DependencyPrerequisiteResult:
        raise TypeError("dependency result must be DependencyPrerequisiteResult")
    if type(value.dependency_id) is not str or not value.dependency_id:
        _fail("invalid_prerequisite", "dependency_id must be a non-empty string")
    if value.result not in {"pass", "fail", "unknown"}:
        _fail(
            "invalid_prerequisite",
            "dependency result is not recognized",
            related_id=value.dependency_id,
        )
    if type(value.evaluator_rule_version) is not str or not value.evaluator_rule_version:
        _fail(
            "invalid_prerequisite",
            "evaluator_rule_version must be non-empty",
            related_id=value.dependency_id,
        )
    if (
        value.observed_evidence_digest is not None
        and type(value.observed_evidence_digest) is not str
    ):
        _fail(
            "invalid_prerequisite",
            "observed evidence digest must be a string or null",
            related_id=value.dependency_id,
        )


def _canonical_dependency_results(
    values: tuple[DependencyPrerequisiteResult, ...],
) -> tuple[DependencyPrerequisiteResult, ...]:
    if type(values) is not tuple:
        _fail("invalid_prerequisite", "dependency_results must be a tuple")
    seen: set[str] = set()
    rows: list[DependencyPrerequisiteResult] = []
    for value in values:
        _validate_dependency_result(value)
        if value.dependency_id in seen:
            _fail(
                "invalid_prerequisite",
                "duplicate dependency result",
                related_id=value.dependency_id,
            )
        seen.add(value.dependency_id)
        rows.append(value)
    rows.sort(key=lambda row: _utf16(row.dependency_id))
    return tuple(rows)


def _runtime_projection(state: RuntimePrerequisiteState) -> dict[str, Any]:
    dependencies = _canonical_dependency_results(state.dependency_results)
    return {
        "algorithm": RUNTIME_PREREQUISITE_FINGERPRINT_ALGORITHM,
        "variant": _variant_projection(state.variant),
        "profile_release_fingerprint": state.profile_release_fingerprint,
        "observed_parent_manifest_digest": state.observed_parent_manifest_digest,
        "parent_state": state.parent_state,
        "dependency_results": [
            {
                "dependency_id": item.dependency_id,
                "result": item.result,
                "observed_evidence_digest": item.observed_evidence_digest,
                "evaluator_rule_version": item.evaluator_rule_version,
            }
            for item in dependencies
        ],
        "active_ontology_bundle_digest": state.active_ontology_bundle_digest,
        "ontology_bundle_state": state.ontology_bundle_state,
        "source_contract": state.source_contract,
    }


def _validate_prerequisite_shape(state: RuntimePrerequisiteState) -> None:
    if type(state) is not RuntimePrerequisiteState:
        raise TypeError("state must be RuntimePrerequisiteState")
    if type(state.variant) is not BundleVariantKey:
        _fail("invalid_prerequisite", "variant must be BundleVariantKey")
    variant_fields = (
        state.variant.corpus_id,
        state.variant.authored_profile_id,
        state.variant.profile_version,
        state.variant.expected_parent_manifest_digest,
    )
    if any(type(item) is not str or not item for item in variant_fields):
        _fail("invalid_prerequisite", "variant fields must be non-empty strings")
    if state.variant.ontology_bundle_digest is not None and (
        type(state.variant.ontology_bundle_digest) is not str
        or not state.variant.ontology_bundle_digest
    ):
        _fail(
            "invalid_prerequisite",
            "variant ontology bundle digest must be a non-empty string or null",
        )
    if (
        type(state.profile_release_fingerprint) is not str
        or not state.profile_release_fingerprint
    ):
        _fail("invalid_prerequisite", "profile release fingerprint must be non-empty")
    if (
        type(state.observed_parent_manifest_digest) is not str
        or not state.observed_parent_manifest_digest
    ):
        _fail("invalid_prerequisite", "observed parent manifest digest must be non-empty")
    if type(state.parent_state) is not str:
        _fail("invalid_prerequisite", "parent state must be a string")
    if type(state.ontology_bundle_state) is not str:
        _fail("invalid_prerequisite", "ontology bundle state must be a string")
    if (
        state.active_ontology_bundle_digest is not None
        and (
            type(state.active_ontology_bundle_digest) is not str
            or not state.active_ontology_bundle_digest
        )
    ):
        _fail(
            "invalid_prerequisite",
            "active ontology bundle digest must be a non-empty string or null",
        )
    if type(state.source_contract) is not str or not state.source_contract:
        _fail("invalid_prerequisite", "source_contract must be a non-empty string")
    _canonical_dependency_results(state.dependency_results)


def runtime_prerequisite_fingerprint(state: RuntimePrerequisiteState) -> str:
    _validate_prerequisite_shape(state)
    return _hash(_runtime_projection(state))


def _native_binding_projection(binding: NativeBindingIR) -> dict[str, Any]:
    if type(binding) is not NativeBindingIR:
        _fail("invalid_compiled_ir", "native binding has the wrong type")
    if type(binding.value_present) is not bool:
        _fail("invalid_compiled_ir", "native binding value_present must be boolean")
    result: dict[str, Any] = {}
    for field in (
        "component_id",
        "node_type",
        "feature",
        "edge",
        "direction",
        "interpretation",
        "execution_shape",
    ):
        value = getattr(binding, field)
        if value is not None:
            result[field] = value
    if binding.value_present:
        result["value"] = binding.value
    if binding.values is not None:
        if type(binding.values) is not tuple or not binding.values:
            _fail("invalid_compiled_ir", "native binding values must be a non-empty exact tuple")
        encoded_values: list[bytes] = []
        for value in binding.values:
            if not (value is None or type(value) in {str, int, float, bool}):
                _fail("invalid_compiled_ir", "native binding values must contain JSON scalars")
            try:
                encoded_values.append(canonical_json_bytes(value))
            except Exception:
                _fail("invalid_compiled_ir", "native binding values contain a non-canonical JSON scalar")
        if len(set(encoded_values)) != len(encoded_values):
            _fail("invalid_compiled_ir", "native binding values contain canonical duplicates")
        if tuple(encoded_values) != tuple(sorted(encoded_values)):
            _fail("invalid_compiled_ir", "native binding values are not canonically ordered")
        result["values"] = list(binding.values)
    if binding.closed_values is not None:
        if type(binding.closed_values) is not tuple:
            _fail("invalid_compiled_ir", "native binding closed_values must be an exact tuple")
        result["closed_values"] = list(binding.closed_values)
    if binding.steps is not None:
        if type(binding.steps) is not tuple:
            _fail("invalid_compiled_ir", "native binding steps must be an exact tuple")
        steps: list[dict[str, str]] = []
        for step in binding.steps:
            if type(step) is not EdgeStepIR:
                _fail("invalid_compiled_ir", "native binding contains an invalid edge step")
            if (
                type(step.edge) is not str
                or not step.edge
                or type(step.direction) is not str
                or not step.direction
            ):
                _fail("invalid_compiled_ir", "native binding edge step fields must be non-empty strings")
            steps.append({"edge": step.edge, "direction": step.direction})
        result["steps"] = steps
    if binding.execution_shape == "value-set-predicate":
        valid = (
            type(binding.component_id) is str
            and bool(binding.component_id)
            and type(binding.node_type) is str
            and bool(binding.node_type)
            and type(binding.feature) is str
            and bool(binding.feature)
            and binding.value_present is False
            and binding.value is None
            and binding.values is not None
            and binding.closed_values is None
            and binding.edge is None
            and binding.direction is None
            and binding.steps is None
            and binding.interpretation is None
        )
        if not valid:
            _fail("invalid_compiled_ir", "value-set-predicate binding has an invalid mixed shape")
    if binding.execution_shape == "value-predicate" and binding.values is not None:
        _fail("invalid_compiled_ir", "value-predicate binding cannot carry selected values")
    return result


def _has_duplicate_ids(values: Iterable[Any]) -> bool:
    seen: set[Any] = set()
    for value in values:
        if value in seen:
            return True
        seen.add(value)
    return False


_CAPABILITY_COUNT_FIELDS = (
    "reviewed_native_support",
    "shared_projections",
    "exact",
    "close",
    "broader",
    "narrower",
    "related",
    "ambiguous",
    "native_only",
    "unsupported",
)


def _validate_capability_facts(facts: CapabilityFactsIR, *, corpus_id: str | None) -> None:
    counts = {field: getattr(facts, field) for field in _CAPABILITY_COUNT_FIELDS}
    if any(type(value) is not int or value < 0 for value in counts.values()):
        _fail(
            "invalid_compiled_ir",
            "capability fact counters must be non-negative exact integers",
            corpus_id=corpus_id,
        )
    if type(facts.mapping_ids) is not tuple:
        _fail(
            "invalid_compiled_ir",
            "capability mapping_ids must be an exact tuple",
            corpus_id=corpus_id,
        )
    if any(type(item) is not str or not item for item in facts.mapping_ids):
        _fail(
            "invalid_compiled_ir",
            "capability mapping_ids must contain non-empty strings",
            corpus_id=corpus_id,
        )
    if len(set(facts.mapping_ids)) != len(facts.mapping_ids):
        _fail(
            "invalid_compiled_ir",
            "capability mapping_ids contain duplicates",
            corpus_id=corpus_id,
        )
    if facts.shared_projections != facts.exact + facts.close + facts.broader + facts.narrower + facts.related:
        _fail(
            "invalid_compiled_ir",
            "capability shared projection counts are incoherent",
            corpus_id=corpus_id,
        )
    if facts.ambiguous + facts.native_only > facts.reviewed_native_support:
        _fail(
            "invalid_compiled_ir",
            "capability native support counts are incoherent",
            corpus_id=corpus_id,
        )


def _validate_compiled_variant_key(value: BundleVariantKey) -> None:
    if type(value) is not BundleVariantKey:
        _fail("invalid_compiled_ir", "variant key has the wrong type")
    fields = (
        value.corpus_id,
        value.authored_profile_id,
        value.profile_version,
        value.expected_parent_manifest_digest,
    )
    if any(type(item) is not str or not item for item in fields):
        _fail("invalid_compiled_ir", "variant key fields must be non-empty strings")
    if value.ontology_bundle_digest is not None and (
        type(value.ontology_bundle_digest) is not str or not value.ontology_bundle_digest
    ):
        _fail("invalid_compiled_ir", "variant ontology bundle digest must be a non-empty string or null")


def _validate_compiled_semantic_key(value: SemanticKey) -> None:
    if type(value) is not SemanticKey:
        _fail("invalid_compiled_ir", "semantic index key has the wrong type")
    fields = (
        value.profile_id,
        value.capability_id,
        value.target,
        value.formal_kind,
        value.semantic_role,
    )
    if any(type(item) is not str or not item for item in fields):
        _fail("invalid_compiled_ir", "semantic index key fields must be non-empty strings")


def _validate_variant(variant: BundleVariantIR) -> None:
    if type(variant) is not BundleVariantIR:
        _fail("invalid_compiled_ir", "variant row has the wrong type")
    _validate_compiled_variant_key(variant.key)
    key = variant.key
    if type(variant.release_key) is not ProfileReleaseKey:
        _fail(
            "invalid_compiled_ir",
            "variant release key has the wrong type",
            corpus_id=key.corpus_id,
        )
    if type(variant.release_signature) is not ProfileReleaseSignature:
        _fail(
            "invalid_compiled_ir",
            "variant release signature has the wrong type",
            corpus_id=key.corpus_id,
        )
    signature = variant.release_signature
    _validate_release_signature_rows(signature)
    release_key = variant.release_key
    if (
        release_key.corpus_id != key.corpus_id
        or release_key.authored_profile_id != key.authored_profile_id
        or release_key.profile_version != key.profile_version
    ):
        _fail(
            "invalid_compiled_ir",
            "variant release key does not match variant key",
            corpus_id=key.corpus_id,
        )
    if signature.ontology_bundle_digest != key.ontology_bundle_digest:
        _fail(
            "invalid_compiled_ir",
            "variant ontology bundle digest disagrees with release signature",
            corpus_id=key.corpus_id,
        )
    if variant.mapping_digests != signature.mapping_digests:
        _fail(
            "invalid_compiled_ir",
            "variant mapping digests disagree with release signature",
            corpus_id=key.corpus_id,
        )
    if variant.ontology_locks != signature.ontology_locks:
        _fail(
            "invalid_compiled_ir",
            "variant ontology locks disagree with release signature",
            corpus_id=key.corpus_id,
        )
    repeated = (
        (variant.profile_schema_version, signature.profile_schema_version),
        (variant.profile_catalog_version, signature.profile_catalog_version),
        (variant.dependency_contract_version, signature.dependency_contract_version),
        (variant.mapping_schema_version, signature.mapping_schema_version),
        (variant.mapping_semantic_algorithm, signature.mapping_semantic_algorithm),
        (variant.projection_semantic_algorithm, signature.projection_semantic_algorithm),
    )
    if any(left != right for left, right in repeated):
        _fail(
            "invalid_compiled_ir",
            "variant contract fields disagree with release signature",
            corpus_id=key.corpus_id,
        )
    uniqueness_checks = (
        (
            "dependency",
            (dependency_id for dependency_id, _ in signature.dependency_records),
        ),
        (
            "mapping digest",
            (mapping_id for mapping_id, _ in signature.mapping_digests),
        ),
        (
            "mapping review",
            (mapping_id for mapping_id, _ in signature.mapping_reviews),
        ),
        (
            "projection review",
            (
                (mapping_id, projection_id)
                for mapping_id, projection_id, _ in signature.projection_reviews
            ),
        ),
        (
            "ontology lock",
            (lock.lock_id for lock in signature.ontology_locks),
        ),
    )
    for label, ids in uniqueness_checks:
        if _has_duplicate_ids(ids):
            _fail(
                "invalid_compiled_ir",
                f"release signature contains duplicate {label} IDs",
                corpus_id=key.corpus_id,
            )


def _validate_ir_shape(
    ir: CompiledSemanticIR,
) -> tuple[
    dict[BundleVariantKey, BundleVariantIR],
    dict[SemanticKey, tuple[TargetBindingIR, ...]],
    dict[CapabilityKey, CapabilityFactsIR],
]:
    if type(ir) is not CompiledSemanticIR:
        raise TypeError("ir must be CompiledSemanticIR")
    variants: dict[BundleVariantKey, BundleVariantIR] = {}
    for variant in ir.variants:
        _validate_variant(variant)
        if variant.key in variants:
            _fail(
                "invalid_compiled_ir",
                "duplicate variant key",
                corpus_id=variant.key.corpus_id,
            )
        variants[variant.key] = variant

    semantic: dict[SemanticKey, tuple[TargetBindingIR, ...]] = {}
    for key, rows in ir.semantic_index:
        _validate_compiled_semantic_key(key)
        if type(rows) is not tuple:
            _fail("invalid_compiled_ir", "semantic index has an invalid row shape")
        if any(type(row) is not TargetBindingIR for row in rows):
            _fail("invalid_compiled_ir", "semantic index contains an invalid binding row")
        if key in semantic:
            _fail("invalid_compiled_ir", "duplicate semantic index key")
        for row in rows:
            _validate_compiled_variant_key(row.variant)
            variant = variants.get(row.variant)
            if variant is None:
                _fail(
                    "invalid_compiled_ir",
                    "semantic binding references a variant outside compiled variants",
                    corpus_id=row.corpus_id,
                    related_id=row.mapping_id,
                )
            signature = variant.release_signature
            if (
                row.corpus_id != variant.key.corpus_id
                or row.profile_id not in signature.profiles
                or row.capability_id not in signature.capabilities
                or not row.capability_id.startswith(row.profile_id + ".")
            ):
                _fail(
                    "invalid_compiled_ir",
                    "semantic binding is not declared by selected release",
                    corpus_id=variant.key.corpus_id,
                    related_id=row.mapping_id,
                )
            if (
                key.profile_id != row.profile_id
                or key.capability_id != row.capability_id
                or key.target != row.target
                or key.formal_kind != row.formal_kind
                or key.semantic_role != row.semantic_role
            ):
                _fail(
                    "invalid_compiled_ir",
                    "semantic index key disagrees with binding",
                    corpus_id=variant.key.corpus_id,
                    related_id=row.mapping_id,
                )
        semantic[key] = rows

    capabilities: dict[CapabilityKey, CapabilityFactsIR] = {}
    for key, facts in ir.capability_facts:
        if type(key) is not CapabilityKey or type(facts) is not CapabilityFactsIR:
            _fail("invalid_compiled_ir", "capability facts have an invalid row shape")
        _validate_compiled_variant_key(key.variant)
        variant = variants.get(key.variant)
        if variant is None:
            _fail(
                "invalid_compiled_ir",
                "capability key references a variant outside compiled variants",
                corpus_id=key.variant.corpus_id,
            )
        signature = variant.release_signature
        if (
            key.profile_id not in signature.profiles
            or key.capability_id not in signature.capabilities
            or not key.capability_id.startswith(key.profile_id + ".")
        ):
            _fail(
                "invalid_compiled_ir",
                "capability key is not declared by selected release",
                corpus_id=variant.key.corpus_id,
            )
        _validate_capability_facts(facts, corpus_id=variant.key.corpus_id)
        release_mapping_ids = {
            mapping_id for mapping_id, _ in signature.mapping_digests
        }
        if any(mapping_id not in release_mapping_ids for mapping_id in facts.mapping_ids):
            _fail(
                "invalid_compiled_ir",
                "capability facts reference mapping IDs outside selected release",
                corpus_id=variant.key.corpus_id,
            )
        if key in capabilities:
            _fail(
                "invalid_compiled_ir",
                "duplicate capability key",
                corpus_id=variant.key.corpus_id,
            )
        capabilities[key] = facts
    return variants, semantic, capabilities


def _validate_request(request: SemanticResolveRequest) -> SemanticResolveRequest:
    if type(request) is not SemanticResolveRequest:
        raise TypeError("request must be SemanticResolveRequest")
    if type(request.key) is not SemanticKey:
        _fail("invalid_request", "request key must be SemanticKey")
    if request.semantic_mode != "exact":
        _fail("unsupported_semantic_mode", "only exact semantic resolution is supported")
    if type(request.corpora) is not tuple or not request.corpora:
        _fail("invalid_corpus_selection", "corpora must be a non-empty tuple")
    if any(type(item) is not str or not item for item in request.corpora):
        _fail("invalid_corpus_selection", "corpus IDs must be non-empty strings")
    if len(set(request.corpora)) != len(request.corpora):
        _fail("invalid_corpus_selection", "duplicate corpus selection")
    key = request.key
    vocabulary_fields = (
        key.profile_id,
        key.capability_id,
        key.formal_kind,
        key.semantic_role,
    )
    if any(type(item) is not str for item in vocabulary_fields):
        _fail(
            "unknown_request_vocabulary",
            "request uses unknown or inconsistent semantic vocabulary",
        )
    if (
        key.profile_id not in PROFILE_IDS
        or key.capability_id not in CAPABILITY_IDS
        or not key.capability_id.startswith(key.profile_id + ".")
        or key.formal_kind not in FORMAL_KINDS
        or key.semantic_role not in SEMANTIC_ROLES
    ):
        _fail(
            "unknown_request_vocabulary",
            "request uses unknown or inconsistent semantic vocabulary",
        )
    if type(key.target) is not str or not key.target:
        _fail("invalid_request", "semantic target must be a non-empty string")
    return SemanticResolveRequest(
        key=key,
        corpora=tuple(sorted(request.corpora, key=_utf16)),
        semantic_mode="exact",
    )


def _materialize_prerequisites(
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> tuple[RuntimePrerequisiteState, ...]:
    try:
        rows = tuple(prerequisites)
    except TypeError:
        raise TypeError("prerequisites must be iterable") from None
    seen: set[BundleVariantKey] = set()
    for row in rows:
        if type(row) is not RuntimePrerequisiteState:
            raise TypeError("prerequisite items must be RuntimePrerequisiteState")
        _validate_prerequisite_shape(row)
        if row.variant in seen:
            _fail(
                "invalid_prerequisite",
                "duplicate prerequisite for the same variant",
                corpus_id=row.variant.corpus_id,
            )
        seen.add(row.variant)
    return rows


def _select_prerequisite(
    corpus_id: str,
    rows: tuple[RuntimePrerequisiteState, ...],
    variants: dict[BundleVariantKey, BundleVariantIR],
) -> tuple[RuntimePrerequisiteState, BundleVariantIR]:
    selected = [row for row in rows if row.variant.corpus_id == corpus_id]
    if not selected:
        _fail(
            "missing_prerequisite",
            "no runtime prerequisite for requested corpus",
            corpus_id=corpus_id,
        )

    fresh: list[tuple[RuntimePrerequisiteState, BundleVariantIR]] = []
    saw_stale = False
    for row in selected:
        variant = variants.get(row.variant)
        if variant is None:
            saw_stale = True
            continue
        if row.profile_release_fingerprint != profile_release_fingerprint(
            variant.release_signature
        ):
            saw_stale = True
            continue
        fresh.append((row, variant))

    if not fresh:
        if saw_stale:
            _fail(
                "stale_prerequisite",
                "prerequisite does not match current compiled release",
                corpus_id=corpus_id,
            )
        _fail(
            "missing_prerequisite",
            "no current runtime prerequisite for requested corpus",
            corpus_id=corpus_id,
        )
    if len(fresh) > 1:
        _fail(
            "ambiguous_prerequisite_variant",
            "multiple current variants have prerequisites",
            corpus_id=corpus_id,
        )
    return fresh[0]


def _prerequisite_problem(
    state: RuntimePrerequisiteState,
    variant: BundleVariantIR,
) -> str | None:
    if type(state.source_contract) is not str or not state.source_contract:
        return "invalid_prerequisite"
    if state.parent_state not in {
        "verified-exact",
        "verified-compatible",
        "unverified",
        "incompatible",
    }:
        return "invalid_prerequisite"
    if state.parent_state == "unverified":
        return "parent_unverified"
    if state.parent_state == "incompatible":
        return "parent_incompatible"
    if state.parent_state == "verified-compatible" and variant.release_signature.parent_compatibility != "dependency-verified":
        return "parent_incompatible"

    expected_parent = variant.key.expected_parent_manifest_digest
    if (
        state.parent_state == "verified-exact"
        and state.observed_parent_manifest_digest != expected_parent
    ):
        return "stale_prerequisite"
    if (
        state.parent_state == "verified-compatible"
        and state.observed_parent_manifest_digest == expected_parent
    ):
        return "invalid_prerequisite"

    try:
        dependencies = _canonical_dependency_results(state.dependency_results)
    except SemanticResolutionError as error:
        return error.problem.category
    expected_dependencies = {
        dependency_id for dependency_id, _ in variant.release_signature.dependency_records
    }
    actual_dependencies = {row.dependency_id for row in dependencies}
    if actual_dependencies != expected_dependencies:
        return "stale_prerequisite"
    if any(row.result != "pass" for row in dependencies):
        return "dependency_unavailable"

    required_bundle = variant.key.ontology_bundle_digest
    if required_bundle is None:
        if (
            state.ontology_bundle_state != "not-required"
            or state.active_ontology_bundle_digest is not None
        ):
            return "invalid_prerequisite"
    else:
        if state.ontology_bundle_state == "unavailable":
            return "ontology_bundle_unavailable"
        if state.ontology_bundle_state != "verified":
            return "invalid_prerequisite"
        if not state.active_ontology_bundle_digest:
            return "invalid_prerequisite"
        if state.active_ontology_bundle_digest != required_bundle:
            return "stale_prerequisite"
    return None


def _zero_capability_facts() -> CapabilityFactsIR:
    return CapabilityFactsIR(
        reviewed_native_support=0,
        shared_projections=0,
        exact=0,
        close=0,
        broader=0,
        narrower=0,
        related=0,
        ambiguous=0,
        native_only=0,
        unsupported=0,
        mapping_ids=(),
    )


def _capability_view(
    variant: BundleVariantIR,
    state: RuntimePrerequisiteState,
    profile_id: str,
    capability_id: str,
    capabilities: dict[CapabilityKey, CapabilityFactsIR],
) -> SemanticCapabilityView:
    facts = capabilities.get(
        CapabilityKey(
            variant=variant.key,
            profile_id=profile_id,
            capability_id=capability_id,
        )
    )
    if facts is None:
        facts = _zero_capability_facts()
    prerequisite_problem = _prerequisite_problem(state, variant)
    if facts.reviewed_native_support == 0:
        status = "absent"
    elif prerequisite_problem is None:
        status = "active"
    else:
        status = "unavailable"
    return SemanticCapabilityView(
        corpus_id=variant.key.corpus_id,
        variant=variant.key,
        profile_id=profile_id,
        capability_id=capability_id,
        state=status,
        facts=facts,
        executable_exact=status == "active" and facts.exact > 0,
        prerequisite_fingerprint=runtime_prerequisite_fingerprint(state),
    )


def semantic_capabilities(
    ir: CompiledSemanticIR,
    prerequisites: Iterable[RuntimePrerequisiteState],
    *,
    corpora: Iterable[str] | None = None,
) -> tuple[SemanticCapabilityView, ...]:
    variants, _semantic, capabilities = _validate_ir_shape(ir)
    rows = _materialize_prerequisites(prerequisites)
    if corpora is None:
        selected_corpora = tuple(
            sorted({variant.key.corpus_id for variant in ir.variants}, key=_utf16)
        )
    else:
        try:
            selected_corpora = tuple(corpora)
        except TypeError:
            raise TypeError("corpora must be iterable") from None
        if any(type(item) is not str or not item for item in selected_corpora):
            _fail("invalid_corpus_selection", "invalid capability corpus selection")
        if len(set(selected_corpora)) != len(selected_corpora):
            _fail("invalid_corpus_selection", "duplicate capability corpus selection")
        selected_corpora = tuple(sorted(selected_corpora, key=_utf16))

    result: list[SemanticCapabilityView] = []
    for corpus_id in selected_corpora:
        state, variant = _select_prerequisite(corpus_id, rows, variants)
        prerequisite_problem = _prerequisite_problem(state, variant)
        if prerequisite_problem in {"invalid_prerequisite", "stale_prerequisite"}:
            _fail(
                prerequisite_problem,
                "runtime prerequisite attestation is incoherent",
                corpus_id=corpus_id,
            )
        for profile_id in sorted(variant.release_signature.profiles, key=_utf16):
            for capability_id in sorted(
                variant.release_signature.capabilities,
                key=_utf16,
            ):
                if capability_id.startswith(profile_id + "."):
                    result.append(
                        _capability_view(
                            variant,
                            state,
                            profile_id,
                            capability_id,
                            capabilities,
                        )
                    )
    return tuple(result)


def _validate_binding_against_release(
    binding: TargetBindingIR,
    variant: BundleVariantIR,
    request_key: SemanticKey,
) -> None:
    corpus_id = variant.key.corpus_id
    if type(binding) is not TargetBindingIR:
        _fail("invalid_compiled_ir", "semantic index contains an invalid binding row")
    if type(binding.native_dependencies) is not tuple:
        _fail(
            "invalid_compiled_ir",
            "native dependencies must be an exact tuple",
            corpus_id=corpus_id,
            related_id=binding.mapping_id,
        )
    if any(type(item) is not str or not item for item in binding.native_dependencies):
        _fail(
            "invalid_compiled_ir",
            "native dependency IDs must be non-empty strings",
            corpus_id=corpus_id,
            related_id=binding.mapping_id,
        )
    if type(binding.mapping_evidence) is not tuple or type(binding.projection_evidence) is not tuple:
        _fail(
            "invalid_compiled_ir",
            "binding evidence collections must be exact tuples",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )
    if any(type(item) is not EvidenceFingerprint for item in binding.mapping_evidence + binding.projection_evidence):
        _fail(
            "invalid_compiled_ir",
            "binding evidence contains an invalid row",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )
    for item in binding.mapping_evidence + binding.projection_evidence:
        _evidence_projection(item)
    if (
        binding.ontology_bundle_requirement is not None
        and type(binding.ontology_bundle_requirement) is not OntologyBundleRequirementIR
    ):
        _fail(
            "invalid_compiled_ir",
            "ontology bundle requirement has the wrong type",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )
    if (
        binding.ontology_bundle_requirement is not None
        and type(binding.ontology_bundle_requirement.required_profile_contracts) is not tuple
    ):
        _fail(
            "invalid_compiled_ir",
            "ontology bundle required profile contracts must be an exact tuple",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )
    if (
        binding.variant != variant.key
        or binding.corpus_id != corpus_id
        or binding.profile_id != request_key.profile_id
        or binding.capability_id != request_key.capability_id
        or binding.target != request_key.target
        or binding.formal_kind != request_key.formal_kind
        or binding.semantic_role != request_key.semantic_role
        or binding.reference_kind != "semantic-pivot"
        or binding.query_role != "semantic-constraint"
    ):
        _fail(
            "invalid_compiled_ir",
            "semantic index binding is incoherent",
            corpus_id=corpus_id,
            related_id=binding.mapping_id,
        )

    signature = variant.release_signature
    if (binding.mapping_id, binding.mapping_semantic_digest) not in signature.mapping_digests:
        _fail(
            "invalid_compiled_ir",
            "mapping digest is not part of selected release",
            corpus_id=corpus_id,
            related_id=binding.mapping_id,
        )
    if (binding.mapping_id, binding.mapping_review) not in signature.mapping_reviews:
        _fail(
            "invalid_compiled_ir",
            "mapping review is not selected release authority",
            corpus_id=corpus_id,
            related_id=binding.mapping_id,
        )
    if (
        binding.mapping_id,
        binding.projection_id,
        binding.projection_review,
    ) not in signature.projection_reviews:
        _fail(
            "invalid_compiled_ir",
            "projection review is not selected release authority",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )
    if (
        binding.mapping_review.status != "reviewed"
        or binding.projection_review.status != "reviewed"
    ):
        _fail(
            "invalid_compiled_ir",
            "semantic binding is not review-authorized",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )
    if binding.mapping_review.reviewed_semantic_digest != binding.mapping_semantic_digest:
        _fail(
            "invalid_compiled_ir",
            "mapping review semantic digest is incoherent",
            corpus_id=corpus_id,
            related_id=binding.mapping_id,
        )
    if (
        binding.projection_review.reviewed_semantic_digest
        != binding.projection_semantic_digest
    ):
        _fail(
            "invalid_compiled_ir",
            "projection review semantic digest is incoherent",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )
    if binding.ontology_lock not in signature.ontology_locks:
        _fail(
            "invalid_compiled_ir",
            "ontology lock is not part of selected release",
            corpus_id=corpus_id,
            related_id=binding.ontology_lock.lock_id,
        )
    release_dependencies = {
        dependency_id for dependency_id, _ in signature.dependency_records
    }
    if any(
        dependency_id not in release_dependencies
        for dependency_id in binding.native_dependencies
    ):
        _fail(
            "invalid_compiled_ir",
            "native dependency is not part of selected release",
            corpus_id=corpus_id,
            related_id=binding.mapping_id,
        )
    if binding.ontology_bundle_digest != variant.key.ontology_bundle_digest:
        _fail(
            "invalid_compiled_ir",
            "binding ontology bundle digest disagrees with variant",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )
    if (
        binding.ontology_bundle_requirement is not None
        and binding.ontology_bundle_requirement.bundle_digest
        != variant.key.ontology_bundle_digest
    ):
        _fail(
            "invalid_compiled_ir",
            "projection bundle requirement disagrees with variant",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )

    try:
        reconstructed = _native_binding_projection(binding.native_execution_binding)
        reconstructed_identity = native_binding_identity(reconstructed)
    except SemanticResolutionError:
        raise
    except Exception:
        _fail(
            "invalid_compiled_ir",
            "native execution binding cannot be reconstructed",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )
    if reconstructed_identity != binding.native_execution_binding_identity:
        _fail(
            "invalid_compiled_ir",
            "native execution binding identity mismatch",
            corpus_id=corpus_id,
            related_id=binding.projection_id,
        )


def _plan_projection(plan: ExactNativePlan) -> dict[str, Any]:
    return {
        "algorithm": EXACT_PLAN_FINGERPRINT_ALGORITHM,
        "resolver_contract": plan.resolver_contract,
        "corpus_id": plan.corpus_id,
        "semantic_key": _semantic_key_projection(plan.semantic_key),
        "reference_kind": plan.reference_kind,
        "query_role": plan.query_role,
        "semantic_mode": plan.semantic_mode,
        "capability_state": plan.capability_state,
        "variant": _variant_projection(plan.variant),
        "profile_release_fingerprint": plan.profile_release_fingerprint,
        "expected_parent_manifest_digest": plan.expected_parent_manifest_digest,
        "observed_parent_manifest_digest": plan.observed_parent_manifest_digest,
        "parent_state": plan.parent_state,
        "prerequisite_fingerprint": plan.prerequisite_fingerprint,
        "prerequisite_source_contract": plan.prerequisite_source_contract,
        "mapping_id": plan.mapping_id,
        "projection_id": plan.projection_id,
        "assessment": plan.assessment,
        "native_execution_binding_identity": plan.native_execution_binding_identity,
        "native_dependencies": list(plan.native_dependencies),
        "mapping_semantic_digest": plan.mapping_semantic_digest,
        "projection_semantic_digest": plan.projection_semantic_digest,
        "mapping_review": _review_projection(plan.mapping_review),
        "projection_review": _review_projection(plan.projection_review),
        "ontology_lock": _lock_projection(plan.ontology_lock),
        "ontology_bundle_digest": plan.ontology_bundle_digest,
        "mapping_evidence": [
            _evidence_projection(item) for item in plan.mapping_evidence
        ],
        "projection_evidence": [
            _evidence_projection(item) for item in plan.projection_evidence
        ],
    }


def _make_plan(
    binding: TargetBindingIR,
    variant: BundleVariantIR,
    state: RuntimePrerequisiteState,
    semantic_key: SemanticKey,
) -> ExactNativePlan:
    prerequisite_fingerprint = runtime_prerequisite_fingerprint(state)
    values = dict(
        resolver_contract=EXACT_RESOLVER_CONTRACT,
        corpus_id=binding.corpus_id,
        semantic_key=semantic_key,
        reference_kind="semantic-pivot",
        query_role="semantic-constraint",
        semantic_mode="exact",
        capability_state="active",
        variant=variant.key,
        profile_release_fingerprint=state.profile_release_fingerprint,
        expected_parent_manifest_digest=variant.key.expected_parent_manifest_digest,
        observed_parent_manifest_digest=state.observed_parent_manifest_digest,
        parent_state=state.parent_state,
        prerequisite_fingerprint=prerequisite_fingerprint,
        prerequisite_source_contract=state.source_contract,
        mapping_id=binding.mapping_id,
        projection_id=binding.projection_id,
        assessment=binding.assessment,
        native_execution_binding_identity=binding.native_execution_binding_identity,
        native_execution_binding=binding.native_execution_binding,
        native_dependencies=binding.native_dependencies,
        mapping_semantic_digest=binding.mapping_semantic_digest,
        projection_semantic_digest=binding.projection_semantic_digest,
        mapping_review=binding.mapping_review,
        projection_review=binding.projection_review,
        ontology_lock=binding.ontology_lock,
        ontology_bundle_digest=binding.ontology_bundle_digest,
        mapping_evidence=binding.mapping_evidence,
        projection_evidence=binding.projection_evidence,
    )
    provisional = ExactNativePlan(plan_fingerprint="", **values)
    return ExactNativePlan(
        plan_fingerprint=_hash(_plan_projection(provisional)),
        **values,
    )


def semantic_resolve(
    ir: CompiledSemanticIR,
    request: SemanticResolveRequest,
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> SemanticResolutionResult:
    if type(ir) is not CompiledSemanticIR:
        raise TypeError("ir must be CompiledSemanticIR")
    canonical_request = _validate_request(request)
    variants, semantic_index, capabilities = _validate_ir_shape(ir)
    prerequisite_rows = _materialize_prerequisites(prerequisites)
    plans: list[ExactNativePlan] = []
    bindings_for_key = semantic_index.get(canonical_request.key)

    for corpus_id in canonical_request.corpora:
        state, variant = _select_prerequisite(
            corpus_id,
            prerequisite_rows,
            variants,
        )
        prerequisite_problem = _prerequisite_problem(state, variant)
        if prerequisite_problem is not None:
            _fail(
                prerequisite_problem,
                "runtime prerequisite is not executable",
                corpus_id=corpus_id,
            )

        capability = _capability_view(
            variant,
            state,
            canonical_request.key.profile_id,
            canonical_request.key.capability_id,
            capabilities,
        )
        if capability.state == "absent":
            _fail(
                "capability_absent",
                "requested capability is absent",
                corpus_id=corpus_id,
            )
        if capability.state != "active":
            _fail(
                "capability_unavailable",
                "requested capability is unavailable",
                corpus_id=corpus_id,
            )

        if bindings_for_key is None:
            _fail(
                "semantic_tuple_absent",
                "semantic tuple is absent",
                corpus_id=corpus_id,
            )
        candidates = [
            row
            for row in bindings_for_key
            if row.corpus_id == corpus_id and row.variant == variant.key
        ]
        if not candidates:
            _fail(
                "semantic_tuple_absent",
                "semantic tuple is absent for selected corpus variant",
                corpus_id=corpus_id,
            )
        for candidate in candidates:
            _validate_binding_against_release(
                candidate,
                variant,
                canonical_request.key,
            )
        exact = [row for row in candidates if row.assessment == "exact"]
        if not exact:
            _fail(
                "non_exact_mapping",
                "semantic tuple has no exact mapping",
                corpus_id=corpus_id,
            )
        if len(exact) > 1:
            _fail(
                "multiple_exact_bindings",
                "multiple exact bindings require explicit composition semantics",
                corpus_id=corpus_id,
            )
        plans.append(
            _make_plan(
                exact[0],
                variant,
                state,
                canonical_request.key,
            )
        )

    plans.sort(key=lambda plan: _utf16(plan.corpus_id))
    plan_tuple = tuple(plans)
    result_projection = {
        "algorithm": EXACT_RESOLUTION_FINGERPRINT_ALGORITHM,
        "resolver_contract": EXACT_RESOLVER_CONTRACT,
        "request": {
            "key": _semantic_key_projection(canonical_request.key),
            "corpora": list(canonical_request.corpora),
            "semantic_mode": canonical_request.semantic_mode,
        },
        "comparison_state": "exactly-comparable",
        "losses": [],
        "plan_fingerprints": [plan.plan_fingerprint for plan in plan_tuple],
    }
    return SemanticResolutionResult(
        resolver_contract=EXACT_RESOLVER_CONTRACT,
        request=canonical_request,
        plans=plan_tuple,
        comparison_state="exactly-comparable",
        losses=(),
        resolution_fingerprint=_hash(result_projection),
    )
