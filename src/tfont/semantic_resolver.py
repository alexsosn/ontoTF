from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Iterable

from .digests import canonical_json_bytes
from .semantic_ir import (
    ApproximationIR,
    AuthorityKey,
    BundleVariantIR,
    BundleVariantKey,
    CapabilityFactsIR,
    CapabilityKey,
    CompiledSemanticIR,
    EdgeStepIR,
    EvidenceFingerprint,
    ExternalReferenceIR,
    IdentifierKey,
    IdentityKey,
    NativeBindingIR,
    NativeKey,
    NativeRecordIR,
    OntologyBundleRequirementIR,
    OntologyLockFingerprint,
    ProfileReleaseKey,
    ProfileReleaseSignature,
    ReviewFingerprint,
    SemanticKey,
    TargetBindingIR,
    native_binding_identity,
)
from .semantic_vocabulary import (
    CAPABILITY_IDS,
    FORMAL_KINDS,
    IDENTITY_STRENGTHS,
    LOSS_TOKENS,
    PROFILE_IDS,
    SEMANTIC_ROLES,
)

EXACT_RESOLVER_CONTRACT = "tfont-exact-semantic-resolver-v1"
PROFILE_RELEASE_FINGERPRINT_ALGORITHM = "tfont-profile-release-signature-jcs-sha256-v1"
RUNTIME_PREREQUISITE_FINGERPRINT_ALGORITHM = "tfont-runtime-prerequisite-jcs-sha256-v1"
EXACT_PLAN_FINGERPRINT_ALGORITHM = "tfont-exact-native-plan-jcs-sha256-v1"
EXACT_RESOLUTION_FINGERPRINT_ALGORITHM = "tfont-exact-resolution-jcs-sha256-v1"
APPROXIMATE_RESOLVER_CONTRACT = "tfont-approximate-semantic-resolver-v1"
APPROXIMATE_PLAN_FINGERPRINT_ALGORITHM = "tfont-approximate-native-plan-jcs-sha256-v1"
APPROXIMATE_RESOLUTION_FINGERPRINT_ALGORITHM = "tfont-approximate-resolution-jcs-sha256-v1"
APPROXIMATE_CONJUNCTION_RESOLVER_CONTRACT = "tfont-approximate-semantic-conjunction-resolver-v1"
APPROXIMATE_CONJUNCTION_RESOLUTION_FINGERPRINT_ALGORITHM = "tfont-approximate-conjunction-resolution-jcs-sha256-v1"

EXACT_AUTHORITY_RESOLVER_CONTRACT = "tfont-exact-authority-resolver-v1"
APPROXIMATE_AUTHORITY_RESOLVER_CONTRACT = "tfont-approximate-authority-resolver-v1"
IDENTITY_RESOLVER_CONTRACT = "tfont-identity-resolver-v1"
IDENTIFIER_RESOLVER_CONTRACT = "tfont-identifier-resolver-v1"
EXACT_AUTHORITY_PLAN_FINGERPRINT_ALGORITHM = "tfont-exact-authority-plan-jcs-sha256-v1"
EXACT_AUTHORITY_RESOLUTION_FINGERPRINT_ALGORITHM = "tfont-exact-authority-resolution-jcs-sha256-v1"
APPROXIMATE_AUTHORITY_PLAN_FINGERPRINT_ALGORITHM = "tfont-approximate-authority-plan-jcs-sha256-v1"
APPROXIMATE_AUTHORITY_RESOLUTION_FINGERPRINT_ALGORITHM = "tfont-approximate-authority-resolution-jcs-sha256-v1"
IDENTITY_PLAN_FINGERPRINT_ALGORITHM = "tfont-identity-plan-jcs-sha256-v1"
IDENTITY_RESOLUTION_FINGERPRINT_ALGORITHM = "tfont-identity-resolution-jcs-sha256-v1"
IDENTIFIER_PLAN_FINGERPRINT_ALGORITHM = "tfont-identifier-plan-jcs-sha256-v1"
IDENTIFIER_RESOLUTION_FINGERPRINT_ALGORITHM = "tfont-identifier-resolution-jcs-sha256-v1"
REFERENCE_FINGERPRINT_ALGORITHM = "tfont-reviewed-reference-jcs-sha256-v1"


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
class ApproximateSemanticResolveRequest:
    key: SemanticKey
    corpora: tuple[str, ...]
    semantic_mode: str = "approximate"
    accept_losses: tuple[str, ...] = ()


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
class ApproximationLossRecord:
    corpus_id: str
    semantic_key: SemanticKey
    mapping_id: str
    projection_id: str
    assessment: str
    native_execution_binding_identity: str
    losses: tuple[str, ...]
    effects: tuple[str, ...]
    approximation_review_id: str
    caller_accepted_losses: tuple[str, ...]
    mapping_semantic_digest: str
    projection_semantic_digest: str
    prerequisite_fingerprint: str
    prerequisite_source_contract: str


@dataclass(frozen=True)
class ApproximateNativePlan:
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
    approximation: ApproximationIR | None
    losses: tuple[str, ...]
    loss_record: ApproximationLossRecord | None
    plan_fingerprint: str


@dataclass(frozen=True)
class ApproximateSemanticResolutionResult:
    resolver_contract: str
    request: ApproximateSemanticResolveRequest
    plans: tuple[ApproximateNativePlan, ...]
    comparison_state: str
    losses: tuple[str, ...]
    loss_records: tuple[ApproximationLossRecord, ...]
    resolution_fingerprint: str


@dataclass(frozen=True)
class AuthorityResolveRequest:
    key: AuthorityKey
    corpora: tuple[str, ...]
    authority_mode: str = "exact"


@dataclass(frozen=True)
class ApproximateAuthorityResolveRequest:
    key: AuthorityKey
    corpora: tuple[str, ...]
    authority_mode: str = "approximate"
    accept_losses: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthorityLossRecord:
    corpus_id: str
    authority_key: AuthorityKey
    mapping_id: str
    projection_id: str
    assessment: str
    native_execution_binding_identity: str
    losses: tuple[str, ...]
    effects: tuple[str, ...]
    approximation_review_id: str
    caller_accepted_losses: tuple[str, ...]
    mapping_semantic_digest: str
    projection_semantic_digest: str
    prerequisite_fingerprint: str
    prerequisite_source_contract: str


@dataclass(frozen=True)
class AuthorityNativePlan:
    resolver_contract: str
    corpus_id: str
    authority_key: AuthorityKey
    query_role: str
    authority_mode: str
    variant: BundleVariantKey
    profile_release_fingerprint: str
    expected_parent_manifest_digest: str
    observed_parent_manifest_digest: str
    parent_state: str
    prerequisite_fingerprint: str
    prerequisite_source_contract: str
    mapping_id: str
    projection_id: str
    profile_id: str
    capability_id: str
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
    approximation: ApproximationIR | None
    losses: tuple[str, ...]
    loss_record: AuthorityLossRecord | None
    plan_fingerprint: str


@dataclass(frozen=True)
class AuthorityResolutionResult:
    resolver_contract: str
    request: AuthorityResolveRequest
    plans: tuple[AuthorityNativePlan, ...]
    comparison_state: str
    losses: tuple[str, ...]
    resolution_fingerprint: str


@dataclass(frozen=True)
class ApproximateAuthorityResolutionResult:
    resolver_contract: str
    request: ApproximateAuthorityResolveRequest
    plans: tuple[AuthorityNativePlan, ...]
    comparison_state: str
    losses: tuple[str, ...]
    loss_records: tuple[AuthorityLossRecord, ...]
    resolution_fingerprint: str


@dataclass(frozen=True)
class IdentityResolveRequest:
    authority_system: str
    external_entity_id: str
    corpora: tuple[str, ...]


@dataclass(frozen=True)
class IdentifierResolveRequest:
    key: IdentifierKey
    corpora: tuple[str, ...]


@dataclass(frozen=True)
class IdentityNativePlan:
    resolver_contract: str
    corpus_id: str
    variant: BundleVariantKey
    authority_system: str
    external_entity_id: str
    identity_strength: str
    mapping_id: str
    reference_id: str
    reference_kind: str
    query_role: str
    mapping_semantic_digest: str
    mapping_review: ReviewFingerprint
    reference_evidence: tuple[EvidenceFingerprint, ...]
    reference_fingerprint: str
    native_execution_binding_identity: str
    native_execution_binding: NativeBindingIR
    native_dependencies: tuple[str, ...]
    prerequisite_fingerprint: str
    prerequisite_source_contract: str
    profile_release_fingerprint: str
    expected_parent_manifest_digest: str
    observed_parent_manifest_digest: str
    parent_state: str
    plan_fingerprint: str


@dataclass(frozen=True)
class IdentifierNativePlan:
    resolver_contract: str
    corpus_id: str
    variant: BundleVariantKey
    key: IdentifierKey
    mapping_id: str
    reference_id: str
    reference_kind: str
    query_role: str
    mapping_semantic_digest: str
    mapping_review: ReviewFingerprint
    reference_evidence: tuple[EvidenceFingerprint, ...]
    reference_fingerprint: str
    native_execution_binding_identity: str
    native_execution_binding: NativeBindingIR
    native_dependencies: tuple[str, ...]
    prerequisite_fingerprint: str
    prerequisite_source_contract: str
    profile_release_fingerprint: str
    expected_parent_manifest_digest: str
    observed_parent_manifest_digest: str
    parent_state: str
    plan_fingerprint: str


@dataclass(frozen=True)
class IdentityResolutionResult:
    resolver_contract: str
    request: IdentityResolveRequest
    plans: tuple[IdentityNativePlan, ...]
    resolution_fingerprint: str


@dataclass(frozen=True)
class IdentifierResolutionResult:
    resolver_contract: str
    request: IdentifierResolveRequest
    plans: tuple[IdentifierNativePlan, ...]
    resolution_fingerprint: str


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
        steps: list[dict[str, Any]] = []
        for step in binding.steps:
            if type(step) is not EdgeStepIR:
                _fail("invalid_compiled_ir", "native binding contains an invalid edge step")
            common_valid = (
                type(step.edge) is str
                and bool(step.edge)
                and type(step.direction) is str
                and step.direction in {"outgoing", "incoming"}
                and type(step.result_node_type) is str
                and bool(step.result_node_type)
                and type(step.valued) is bool
            )
            if step.valued is True:
                value_contract_valid = (
                    type(step.value_type) is str
                    and step.value_type in {"str", "int"}
                    and type(step.value_role) is str
                    and step.value_role
                    in {"semantic-qualifier", "source-evidence", "technical"}
                )
            else:
                value_contract_valid = (
                    step.valued is False
                    and step.value_type is None
                    and step.value_role is None
                )
            if not common_valid or not value_contract_valid:
                _fail(
                    "invalid_compiled_ir",
                    "native binding edge step has an invalid typed valuedness contract",
                )
            row = {
                "edge": step.edge,
                "direction": step.direction,
                "result_node_type": step.result_node_type,
                "valued": step.valued,
            }
            if step.valued:
                row["value_type"] = step.value_type
                row["value_role"] = step.value_role
            steps.append(row)
        result["steps"] = steps
    if binding.execution_shape == "edge-path":
        valid = (
            type(binding.component_id) is str
            and bool(binding.component_id)
            and type(binding.node_type) is str
            and bool(binding.node_type)
            and binding.feature is None
            and binding.value_present is False
            and binding.value is None
            and binding.closed_values is None
            and binding.values is None
            and binding.edge is None
            and binding.direction is None
            and type(binding.steps) is tuple
            and bool(binding.steps)
            and binding.interpretation is None
        )
        if not valid:
            _fail("invalid_compiled_ir", "edge-path binding has an invalid mixed shape")
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
    if state.parent_state == "verified-compatible" and variant.release_signature.parent_compatibility != "dependency-verified":
        return "parent_incompatible"

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


_APPROXIMATION_EFFECTS = {
    "undercoverage": "native selector may miss members of the requested semantic target",
    "overcoverage": "native selector may include members outside the requested semantic target",
}


def _validate_approximate_request(
    request: ApproximateSemanticResolveRequest,
) -> ApproximateSemanticResolveRequest:
    if type(request) is not ApproximateSemanticResolveRequest:
        raise TypeError("request must be ApproximateSemanticResolveRequest")
    if request.semantic_mode != "approximate":
        _fail(
            "unsupported_semantic_mode",
            "approximate resolver requires semantic_mode='approximate'",
        )
    accepted = request.accept_losses
    if type(accepted) is not tuple:
        _fail(
            "invalid_loss_acceptance",
            "accept_losses must be an exact tuple",
        )
    if any(type(item) is not str for item in accepted):
        _fail(
            "invalid_loss_acceptance",
            "accepted losses must be exact strings",
        )
    if len(set(accepted)) != len(accepted):
        _fail(
            "invalid_loss_acceptance",
            "accepted losses contain duplicates",
        )
    unknown = [item for item in accepted if item not in LOSS_TOKENS]
    if unknown:
        _fail(
            "unknown_loss_token",
            f"unknown accepted loss token: {sorted(unknown, key=_utf16)[0]!r}",
        )

    exact = _validate_request(
        SemanticResolveRequest(
            key=request.key,
            corpora=request.corpora,
            semantic_mode="exact",
        )
    )
    return ApproximateSemanticResolveRequest(
        key=exact.key,
        corpora=exact.corpora,
        semantic_mode="approximate",
        accept_losses=tuple(sorted(accepted, key=_utf16)),
    )


def _validate_approximation_ir(
    binding: TargetBindingIR,
) -> ApproximationIR | None:
    assessment = binding.assessment
    approximation = binding.approximation

    if assessment not in {"exact", "close", "broader", "narrower", "related"}:
        _fail(
            "invalid_compiled_ir",
            "semantic binding assessment is not recognized",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )

    if assessment in {"exact", "related"}:
        if approximation is not None:
            _fail(
                "invalid_compiled_ir",
                f"{assessment} binding cannot carry approximation authority",
                corpus_id=binding.corpus_id,
                related_id=binding.projection_id,
            )
        return None

    if approximation is None:
        return None
    if type(approximation) is not ApproximationIR:
        _fail(
            "invalid_compiled_ir",
            "approximation authority has the wrong type",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if approximation.status != "reviewed":
        _fail(
            "invalid_compiled_ir",
            "approximation authority is not reviewed",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if type(approximation.eligible) is not bool:
        _fail(
            "invalid_compiled_ir",
            "approximation eligibility must be an exact boolean",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if type(approximation.losses) is not tuple:
        _fail(
            "invalid_compiled_ir",
            "approximation losses must be an exact tuple",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if any(type(item) is not str or item not in LOSS_TOKENS for item in approximation.losses):
        _fail(
            "invalid_compiled_ir",
            "approximation losses contain unknown vocabulary",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if len(set(approximation.losses)) != len(approximation.losses):
        _fail(
            "invalid_compiled_ir",
            "approximation losses contain duplicates",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if approximation.losses != tuple(sorted(approximation.losses, key=_utf16)):
        _fail(
            "invalid_compiled_ir",
            "approximation losses are not canonically ordered",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if (
        type(approximation.rationale) is not str
        or not approximation.rationale
        or type(approximation.review_id) is not str
        or not approximation.review_id
    ):
        _fail(
            "invalid_compiled_ir",
            "approximation rationale and review ID must be non-empty strings",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if type(approximation.evidence) is not tuple:
        _fail(
            "invalid_compiled_ir",
            "approximation evidence must be an exact tuple",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    evidence_keys: list[tuple[bytes, bytes]] = []
    for item in approximation.evidence:
        _evidence_projection(item)
        evidence_keys.append((_utf16(item.evidence_id), _utf16(item.content_digest)))
    if tuple(evidence_keys) != tuple(sorted(evidence_keys)):
        _fail(
            "invalid_compiled_ir",
            "approximation evidence is not canonically ordered",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )

    if approximation.eligible:
        if assessment == "broader" and approximation.losses != ("undercoverage",):
            _fail(
                "invalid_compiled_ir",
                "eligible broader binding must disclose undercoverage only",
                corpus_id=binding.corpus_id,
                related_id=binding.projection_id,
            )
        if assessment == "narrower" and approximation.losses != ("overcoverage",):
            _fail(
                "invalid_compiled_ir",
                "eligible narrower binding must disclose overcoverage only",
                corpus_id=binding.corpus_id,
                related_id=binding.projection_id,
            )
        if assessment == "close" and not approximation.losses:
            _fail(
                "invalid_compiled_ir",
                "eligible close binding must disclose at least one loss",
                corpus_id=binding.corpus_id,
                related_id=binding.projection_id,
            )
    return approximation


def _approximation_from_payload(
    value: Any,
    *,
    binding: TargetBindingIR,
) -> ApproximationIR | None:
    if value is None:
        return None
    if type(value) is not dict:
        _fail(
            "invalid_compiled_ir",
            "reviewed projection approximation payload is malformed",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    required = {"status", "eligible", "losses", "rationale", "review_id"}
    allowed = required | {"evidence"}
    if required - set(value) or set(value) - allowed:
        _fail(
            "invalid_compiled_ir",
            "reviewed projection approximation payload has invalid fields",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if (
        value.get("status") != "reviewed"
        or type(value.get("eligible")) is not bool
        or type(value.get("rationale")) is not str
        or not value["rationale"]
        or type(value.get("review_id")) is not str
        or not value["review_id"]
    ):
        _fail(
            "invalid_compiled_ir",
            "reviewed projection approximation scalar fields are malformed",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    losses = value.get("losses")
    evidence = value.get("evidence", [])
    if type(losses) is not list or type(evidence) is not list:
        _fail(
            "invalid_compiled_ir",
            "reviewed projection approximation payload has invalid collections",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if (
        any(type(item) is not str or item not in LOSS_TOKENS for item in losses)
        or len(set(losses)) != len(losses)
    ):
        _fail(
            "invalid_compiled_ir",
            "reviewed projection approximation losses are malformed",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    evidence_rows: list[EvidenceFingerprint] = []
    for row in evidence:
        if (
            type(row) is not dict
            or set(row) != {"evidence_id", "content_digest"}
            or type(row.get("evidence_id")) is not str
            or not row["evidence_id"]
            or type(row.get("content_digest")) is not str
            or not row["content_digest"]
        ):
            _fail(
                "invalid_compiled_ir",
                "reviewed projection approximation evidence is malformed",
                corpus_id=binding.corpus_id,
                related_id=binding.projection_id,
            )
        evidence_rows.append(
            EvidenceFingerprint(
                evidence_id=row["evidence_id"],
                content_digest=row["content_digest"],
            )
        )
    evidence_rows.sort(
        key=lambda item: (_utf16(item.evidence_id), _utf16(item.content_digest))
    )
    loss_rows = sorted(losses, key=_utf16)
    return ApproximationIR(
        status=value["status"],
        eligible=value["eligible"],
        losses=tuple(loss_rows),
        rationale=value["rationale"],
        review_id=value["review_id"],
        evidence=tuple(evidence_rows),
    )


def _validate_reviewed_projection_payload(
    binding: TargetBindingIR,
) -> ApproximationIR | None:
    payload = binding.projection_semantic_payload
    if type(payload) is not str or not payload:
        _fail(
            "invalid_compiled_ir",
            "reviewed projection semantic payload is unavailable",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    try:
        decoded = json.loads(payload)
    except (TypeError, ValueError, RecursionError):
        _fail(
            "invalid_compiled_ir",
            "reviewed projection semantic payload is invalid JSON",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if type(decoded) is not dict:
        _fail(
            "invalid_compiled_ir",
            "reviewed projection semantic payload must decode to an object",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    try:
        canonical = canonical_json_bytes(decoded).decode("utf-8")
    except Exception:
        _fail(
            "invalid_compiled_ir",
            "reviewed projection semantic payload is outside canonical JSON",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if canonical != payload:
        _fail(
            "invalid_compiled_ir",
            "reviewed projection semantic payload is not canonical",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if _hash(decoded) != binding.projection_semantic_digest:
        _fail(
            "invalid_compiled_ir",
            "reviewed projection semantic payload digest mismatch",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if (
        decoded.get("projection_id") != binding.projection_id
        or decoded.get("assessment") != binding.assessment
    ):
        _fail(
            "invalid_compiled_ir",
            "reviewed projection semantic payload identity mismatch",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )

    compiled = _validate_approximation_ir(binding)
    if "approximation" in decoded and decoded["approximation"] is None:
        _fail(
            "invalid_compiled_ir",
            "reviewed projection approximation envelope cannot be null",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    if binding.assessment in {"exact", "related"} and "approximation" in decoded:
        _fail(
            "invalid_compiled_ir",
            f"{binding.assessment} reviewed projection cannot carry approximation",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    payload_approximation = _approximation_from_payload(
        decoded.get("approximation"),
        binding=binding,
    )
    if payload_approximation != compiled:
        _fail(
            "invalid_compiled_ir",
            "compiled approximation disagrees with reviewed projection semantics",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    return compiled


def _approximation_projection(value: ApproximationIR | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "status": value.status,
        "eligible": value.eligible,
        "losses": list(value.losses),
        "rationale": value.rationale,
        "review_id": value.review_id,
        "evidence": [_evidence_projection(item) for item in value.evidence],
    }


def _loss_record_projection(record: ApproximationLossRecord) -> dict[str, Any]:
    return {
        "corpus_id": record.corpus_id,
        "semantic_key": _semantic_key_projection(record.semantic_key),
        "mapping_id": record.mapping_id,
        "projection_id": record.projection_id,
        "assessment": record.assessment,
        "native_execution_binding_identity": record.native_execution_binding_identity,
        "losses": list(record.losses),
        "effects": list(record.effects),
        "approximation_review_id": record.approximation_review_id,
        "caller_accepted_losses": list(record.caller_accepted_losses),
        "mapping_semantic_digest": record.mapping_semantic_digest,
        "projection_semantic_digest": record.projection_semantic_digest,
        "prerequisite_fingerprint": record.prerequisite_fingerprint,
        "prerequisite_source_contract": record.prerequisite_source_contract,
    }


def _approximate_plan_projection(plan: ApproximateNativePlan) -> dict[str, Any]:
    return {
        "algorithm": APPROXIMATE_PLAN_FINGERPRINT_ALGORITHM,
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
        "approximation": _approximation_projection(plan.approximation),
        "losses": list(plan.losses),
        "loss_record": (
            None
            if plan.loss_record is None
            else _loss_record_projection(plan.loss_record)
        ),
    }


def _make_approximate_plan(
    binding: TargetBindingIR,
    variant: BundleVariantIR,
    state: RuntimePrerequisiteState,
    semantic_key: SemanticKey,
    accepted_losses: tuple[str, ...],
) -> ApproximateNativePlan:
    approximation = binding.approximation
    losses: tuple[str, ...] = ()
    loss_record: ApproximationLossRecord | None = None
    prerequisite_fingerprint = runtime_prerequisite_fingerprint(state)

    if binding.assessment != "exact":
        if type(approximation) is not ApproximationIR:
            _fail(
                "invalid_compiled_ir",
                "selected approximate binding lacks approximation authority",
                corpus_id=binding.corpus_id,
                related_id=binding.projection_id,
            )
        losses = approximation.losses
        effects = tuple(_APPROXIMATION_EFFECTS[item] for item in losses)
        loss_record = ApproximationLossRecord(
            corpus_id=binding.corpus_id,
            semantic_key=semantic_key,
            mapping_id=binding.mapping_id,
            projection_id=binding.projection_id,
            assessment=binding.assessment,
            native_execution_binding_identity=binding.native_execution_binding_identity,
            losses=losses,
            effects=effects,
            approximation_review_id=approximation.review_id,
            caller_accepted_losses=accepted_losses,
            mapping_semantic_digest=binding.mapping_semantic_digest,
            projection_semantic_digest=binding.projection_semantic_digest,
            prerequisite_fingerprint=prerequisite_fingerprint,
            prerequisite_source_contract=state.source_contract,
        )

    values = dict(
        resolver_contract=APPROXIMATE_RESOLVER_CONTRACT,
        corpus_id=binding.corpus_id,
        semantic_key=semantic_key,
        reference_kind="semantic-pivot",
        query_role="semantic-constraint",
        semantic_mode="approximate",
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
        approximation=approximation if binding.assessment != "exact" else None,
        losses=losses,
        loss_record=loss_record,
    )
    provisional = ApproximateNativePlan(plan_fingerprint="", **values)
    return ApproximateNativePlan(
        plan_fingerprint=_hash(_approximate_plan_projection(provisional)),
        **values,
    )


def _comparison_state_from_plans(
    plans: tuple[ApproximateNativePlan, ...],
) -> str:
    nonempty = {plan.losses for plan in plans if plan.losses}
    if not nonempty:
        return "exactly-comparable"
    if len(nonempty) == 1:
        return "approximately-comparable"
    return "heterogeneous-loss"


def _union_losses(
    rows: Iterable[tuple[str, ...]],
) -> tuple[str, ...]:
    values: set[str] = set()
    for row in rows:
        values.update(row)
    return tuple(sorted(values, key=_utf16))


def semantic_resolve_approximate(
    ir: CompiledSemanticIR,
    request: ApproximateSemanticResolveRequest,
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> ApproximateSemanticResolutionResult:
    canonical_request = _validate_approximate_request(request)
    if type(ir) is not CompiledSemanticIR:
        raise TypeError("ir must be CompiledSemanticIR")

    variants, semantic_index, capabilities = _validate_ir_shape(ir)
    prerequisite_rows = _materialize_prerequisites(prerequisites)
    bindings_for_key = semantic_index.get(canonical_request.key)
    plans: list[ApproximateNativePlan] = []

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
            _validate_reviewed_projection_payload(candidate)

        exact = [row for row in candidates if row.assessment == "exact"]
        if len(exact) > 1:
            _fail(
                "multiple_exact_bindings",
                "multiple exact bindings require explicit composition semantics",
                corpus_id=corpus_id,
            )
        if len(exact) == 1:
            selected = exact[0]
        else:
            substitutive = [
                row
                for row in candidates
                if row.assessment in {"close", "broader", "narrower"}
            ]
            if not substitutive:
                if any(row.assessment == "related" for row in candidates):
                    _fail(
                        "non_substitutive_mapping",
                        "semantic tuple has only non-substitutive related mappings",
                        corpus_id=corpus_id,
                    )
                _fail(
                    "approximation_not_authorized",
                    "semantic tuple has no approximation-authorized mapping",
                    corpus_id=corpus_id,
                )

            authorized = [
                row
                for row in substitutive
                if row.approximation is not None
                and row.approximation.eligible is True
            ]
            if not authorized:
                _fail(
                    "approximation_not_authorized",
                    "semantic tuple has no reviewed eligible approximation",
                    corpus_id=corpus_id,
                )
            if len(authorized) > 1:
                _fail(
                    "multiple_approximate_bindings",
                    "multiple eligible approximate bindings require explicit composition semantics",
                    corpus_id=corpus_id,
                )
            selected = authorized[0]
            approximation = selected.approximation
            if type(approximation) is not ApproximationIR:
                _fail(
                    "invalid_compiled_ir",
                    "selected approximate binding has invalid authority",
                    corpus_id=corpus_id,
                    related_id=selected.projection_id,
                )
            missing = [
                loss
                for loss in approximation.losses
                if loss not in canonical_request.accept_losses
            ]
            if missing:
                _fail(
                    "approximation_loss_not_accepted",
                    f"caller did not accept required approximation loss: {missing[0]}",
                    corpus_id=corpus_id,
                    related_id=selected.projection_id,
                )

        plans.append(
            _make_approximate_plan(
                selected,
                variant,
                state,
                canonical_request.key,
                canonical_request.accept_losses,
            )
        )

    plans.sort(key=lambda plan: _utf16(plan.corpus_id))
    plan_tuple = tuple(plans)
    losses = _union_losses(plan.losses for plan in plan_tuple)
    loss_records = tuple(
        plan.loss_record
        for plan in plan_tuple
        if plan.loss_record is not None
    )
    comparison_state = _comparison_state_from_plans(plan_tuple)
    projection = {
        "algorithm": APPROXIMATE_RESOLUTION_FINGERPRINT_ALGORITHM,
        "resolver_contract": APPROXIMATE_RESOLVER_CONTRACT,
        "request": {
            "key": _semantic_key_projection(canonical_request.key),
            "corpora": list(canonical_request.corpora),
            "semantic_mode": canonical_request.semantic_mode,
            "accept_losses": list(canonical_request.accept_losses),
        },
        "comparison_state": comparison_state,
        "losses": list(losses),
        "loss_records": [
            _loss_record_projection(record) for record in loss_records
        ],
        "plan_fingerprints": [plan.plan_fingerprint for plan in plan_tuple],
    }
    return ApproximateSemanticResolutionResult(
        resolver_contract=APPROXIMATE_RESOLVER_CONTRACT,
        request=canonical_request,
        plans=plan_tuple,
        comparison_state=comparison_state,
        losses=losses,
        loss_records=loss_records,
        resolution_fingerprint=_hash(projection),
    )


EXACT_CONJUNCTION_RESOLVER_CONTRACT = "tfont-exact-semantic-conjunction-resolver-v1"
EXACT_CONJUNCTION_RESOLUTION_FINGERPRINT_ALGORITHM = "tfont-exact-conjunction-resolution-jcs-sha256-v1"


@dataclass(frozen=True)
class SemanticConjunctionRequest:
    keys: tuple[SemanticKey, ...]
    corpora: tuple[str, ...]
    semantic_mode: str = "exact"


@dataclass(frozen=True)
class SemanticConjunctionResolutionResult:
    resolver_contract: str
    request: SemanticConjunctionRequest
    resolutions: tuple[SemanticResolutionResult, ...]
    comparison_state: str
    losses: tuple[str, ...]
    resolution_fingerprint: str


def _validate_conjunction_request(
    request: SemanticConjunctionRequest,
) -> SemanticConjunctionRequest:
    if type(request) is not SemanticConjunctionRequest:
        raise TypeError("request must be SemanticConjunctionRequest")
    if type(request.keys) is not tuple or len(request.keys) < 2:
        _fail(
            "invalid_semantic_conjunction",
            "exact conjunction requires at least two SemanticKey atoms",
        )
    if any(type(key) is not SemanticKey for key in request.keys):
        _fail(
            "invalid_semantic_conjunction",
            "conjunction atoms must be SemanticKey values",
        )
    if len(set(request.keys)) != len(request.keys):
        _fail(
            "invalid_semantic_conjunction",
            "conjunction atoms must be unique",
        )

    validated = tuple(
        _validate_request(
            SemanticResolveRequest(
                key=key,
                corpora=request.corpora,
                semantic_mode=request.semantic_mode,
            )
        )
        for key in request.keys
    )
    keys = tuple(
        sorted(
            (row.key for row in validated),
            key=lambda key: canonical_json_bytes(_semantic_key_projection(key)),
        )
    )
    return SemanticConjunctionRequest(
        keys=keys,
        corpora=validated[0].corpora,
        semantic_mode="exact",
    )


def semantic_resolve_conjunction(
    ir: CompiledSemanticIR,
    request: SemanticConjunctionRequest,
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> SemanticConjunctionResolutionResult:
    canonical_request = _validate_conjunction_request(request)
    if type(ir) is not CompiledSemanticIR:
        raise TypeError("ir must be CompiledSemanticIR")
    prerequisite_rows = _materialize_prerequisites(prerequisites)

    resolutions = tuple(
        semantic_resolve(
            ir,
            SemanticResolveRequest(
                key=key,
                corpora=canonical_request.corpora,
                semantic_mode="exact",
            ),
            prerequisite_rows,
        )
        for key in canonical_request.keys
    )
    projection = {
        "algorithm": EXACT_CONJUNCTION_RESOLUTION_FINGERPRINT_ALGORITHM,
        "resolver_contract": EXACT_CONJUNCTION_RESOLVER_CONTRACT,
        "request": {
            "keys": [
                _semantic_key_projection(key) for key in canonical_request.keys
            ],
            "corpora": list(canonical_request.corpora),
            "semantic_mode": "exact",
        },
        "comparison_state": "exactly-comparable",
        "losses": [],
        "constituent_resolution_fingerprints": [
            row.resolution_fingerprint for row in resolutions
        ],
    }
    return SemanticConjunctionResolutionResult(
        resolver_contract=EXACT_CONJUNCTION_RESOLVER_CONTRACT,
        request=canonical_request,
        resolutions=resolutions,
        comparison_state="exactly-comparable",
        losses=(),
        resolution_fingerprint=_hash(projection),
    )


@dataclass(frozen=True)
class ApproximateSemanticConjunctionRequest:
    keys: tuple[SemanticKey, ...]
    corpora: tuple[str, ...]
    semantic_mode: str = "approximate"
    accept_losses: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApproximateSemanticConjunctionResolutionResult:
    resolver_contract: str
    request: ApproximateSemanticConjunctionRequest
    resolutions: tuple[ApproximateSemanticResolutionResult, ...]
    comparison_state: str
    losses: tuple[str, ...]
    loss_records: tuple[ApproximationLossRecord, ...]
    resolution_fingerprint: str


def _validate_approximate_conjunction_request(
    request: ApproximateSemanticConjunctionRequest,
) -> ApproximateSemanticConjunctionRequest:
    if type(request) is not ApproximateSemanticConjunctionRequest:
        raise TypeError("request must be ApproximateSemanticConjunctionRequest")
    if type(request.keys) is not tuple or len(request.keys) < 2:
        _fail(
            "invalid_semantic_conjunction",
            "approximate conjunction requires at least two SemanticKey atoms",
        )
    if any(type(key) is not SemanticKey for key in request.keys):
        _fail(
            "invalid_semantic_conjunction",
            "conjunction atoms must be SemanticKey values",
        )
    if len(set(request.keys)) != len(request.keys):
        _fail(
            "invalid_semantic_conjunction",
            "conjunction atoms must be unique",
        )

    validated = tuple(
        _validate_approximate_request(
            ApproximateSemanticResolveRequest(
                key=key,
                corpora=request.corpora,
                semantic_mode=request.semantic_mode,
                accept_losses=request.accept_losses,
            )
        )
        for key in request.keys
    )
    keys = tuple(
        sorted(
            (row.key for row in validated),
            key=lambda key: canonical_json_bytes(_semantic_key_projection(key)),
        )
    )
    return ApproximateSemanticConjunctionRequest(
        keys=keys,
        corpora=validated[0].corpora,
        semantic_mode="approximate",
        accept_losses=validated[0].accept_losses,
    )


def _loss_record_sort_key(
    record: ApproximationLossRecord,
) -> tuple[bytes, bytes, bytes, bytes]:
    return (
        canonical_json_bytes(_semantic_key_projection(record.semantic_key)),
        _utf16(record.corpus_id),
        _utf16(record.mapping_id),
        _utf16(record.projection_id),
    )


def _conjunction_comparison_state(
    request: ApproximateSemanticConjunctionRequest,
    resolutions: tuple[ApproximateSemanticResolutionResult, ...],
) -> str:
    shapes: list[tuple[str, ...]] = []
    for corpus_id in request.corpora:
        corpus_losses: list[tuple[str, ...]] = []
        for resolution in resolutions:
            plan = next(
                (row for row in resolution.plans if row.corpus_id == corpus_id),
                None,
            )
            if plan is None:
                _fail(
                    "invalid_compiled_ir",
                    "conjunction constituent is missing a requested corpus plan",
                    corpus_id=corpus_id,
                )
            corpus_losses.append(plan.losses)
        shapes.append(_union_losses(corpus_losses))
    nonempty = {shape for shape in shapes if shape}
    if not nonempty:
        return "exactly-comparable"
    if len(nonempty) == 1:
        return "approximately-comparable"
    return "heterogeneous-loss"


def semantic_resolve_approximate_conjunction(
    ir: CompiledSemanticIR,
    request: ApproximateSemanticConjunctionRequest,
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> ApproximateSemanticConjunctionResolutionResult:
    canonical_request = _validate_approximate_conjunction_request(request)
    if type(ir) is not CompiledSemanticIR:
        raise TypeError("ir must be CompiledSemanticIR")
    prerequisite_rows = _materialize_prerequisites(prerequisites)

    resolutions = tuple(
        semantic_resolve_approximate(
            ir,
            ApproximateSemanticResolveRequest(
                key=key,
                corpora=canonical_request.corpora,
                semantic_mode="approximate",
                accept_losses=canonical_request.accept_losses,
            ),
            prerequisite_rows,
        )
        for key in canonical_request.keys
    )
    losses = _union_losses(row.losses for row in resolutions)
    records = tuple(
        sorted(
            (
                record
                for resolution in resolutions
                for record in resolution.loss_records
            ),
            key=_loss_record_sort_key,
        )
    )
    comparison_state = _conjunction_comparison_state(
        canonical_request,
        resolutions,
    )
    projection = {
        "algorithm": APPROXIMATE_CONJUNCTION_RESOLUTION_FINGERPRINT_ALGORITHM,
        "resolver_contract": APPROXIMATE_CONJUNCTION_RESOLVER_CONTRACT,
        "request": {
            "keys": [
                _semantic_key_projection(key) for key in canonical_request.keys
            ],
            "corpora": list(canonical_request.corpora),
            "semantic_mode": canonical_request.semantic_mode,
            "accept_losses": list(canonical_request.accept_losses),
        },
        "comparison_state": comparison_state,
        "losses": list(losses),
        "loss_records": [_loss_record_projection(record) for record in records],
        "constituent_resolution_fingerprints": [
            row.resolution_fingerprint for row in resolutions
        ],
    }
    return ApproximateSemanticConjunctionResolutionResult(
        resolver_contract=APPROXIMATE_CONJUNCTION_RESOLVER_CONTRACT,
        request=canonical_request,
        resolutions=resolutions,
        comparison_state=comparison_state,
        losses=losses,
        loss_records=records,
        resolution_fingerprint=_hash(projection),
    )


# I-021 authority / identity / identifier resolution.

def _canonical_corpora(corpora: tuple[str, ...]) -> tuple[str, ...]:
    if type(corpora) is not tuple or not corpora:
        _fail("invalid_corpus_selection", "corpora must be a non-empty exact tuple")
    if any(type(item) is not str or not item for item in corpora):
        _fail("invalid_corpus_selection", "corpus IDs must be non-empty strings")
    if len(set(corpora)) != len(corpora):
        _fail("invalid_corpus_selection", "duplicate corpus selection")
    return tuple(sorted(corpora, key=_utf16))


def _authority_key_projection(key: AuthorityKey) -> dict[str, str]:
    if type(key) is not AuthorityKey:
        _fail("invalid_request", "authority key must be AuthorityKey")
    fields = (
        key.authority_system,
        key.authority_resource,
        key.formal_kind,
        key.semantic_role,
    )
    if any(type(item) is not str or not item for item in fields):
        _fail("invalid_request", "authority key fields must be non-empty strings")
    if key.formal_kind not in FORMAL_KINDS or key.semantic_role not in SEMANTIC_ROLES:
        _fail("unknown_request_vocabulary", "authority key uses unknown formal vocabulary")
    return {
        "authority_system": key.authority_system,
        "authority_resource": key.authority_resource,
        "formal_kind": key.formal_kind,
        "semantic_role": key.semantic_role,
    }


def _identifier_key_projection(key: IdentifierKey) -> dict[str, str]:
    if type(key) is not IdentifierKey:
        _fail("invalid_request", "identifier key must be IdentifierKey")
    if (
        type(key.issuer_or_namespace) is not str
        or not key.issuer_or_namespace
        or type(key.literal_id) is not str
        or not key.literal_id
    ):
        _fail("invalid_request", "identifier key fields must be non-empty strings")
    return {
        "issuer_or_namespace": key.issuer_or_namespace,
        "literal_id": key.literal_id,
    }


def _validate_authority_request(request: AuthorityResolveRequest) -> AuthorityResolveRequest:
    if type(request) is not AuthorityResolveRequest:
        raise TypeError("request must be AuthorityResolveRequest")
    if request.authority_mode != "exact":
        _fail("unsupported_semantic_mode", "exact authority resolver requires authority_mode='exact'")
    _authority_key_projection(request.key)
    return AuthorityResolveRequest(
        key=request.key,
        corpora=_canonical_corpora(request.corpora),
        authority_mode="exact",
    )


def _validate_approximate_authority_request(
    request: ApproximateAuthorityResolveRequest,
) -> ApproximateAuthorityResolveRequest:
    if type(request) is not ApproximateAuthorityResolveRequest:
        raise TypeError("request must be ApproximateAuthorityResolveRequest")
    if request.authority_mode != "approximate":
        _fail(
            "unsupported_semantic_mode",
            "approximate authority resolver requires authority_mode='approximate'",
        )
    _authority_key_projection(request.key)
    accepted = request.accept_losses
    if type(accepted) is not tuple:
        _fail("invalid_loss_acceptance", "accept_losses must be an exact tuple")
    if any(type(item) is not str for item in accepted):
        _fail("invalid_loss_acceptance", "accepted losses must be exact strings")
    if len(set(accepted)) != len(accepted):
        _fail("invalid_loss_acceptance", "accepted losses contain duplicates")
    unknown = [item for item in accepted if item not in LOSS_TOKENS]
    if unknown:
        _fail(
            "unknown_loss_token",
            f"unknown accepted loss token: {sorted(unknown, key=_utf16)[0]!r}",
        )
    return ApproximateAuthorityResolveRequest(
        key=request.key,
        corpora=_canonical_corpora(request.corpora),
        authority_mode="approximate",
        accept_losses=tuple(sorted(accepted, key=_utf16)),
    )


def _validate_identity_request(request: IdentityResolveRequest) -> IdentityResolveRequest:
    if type(request) is not IdentityResolveRequest:
        raise TypeError("request must be IdentityResolveRequest")
    if (
        type(request.authority_system) is not str
        or not request.authority_system
        or type(request.external_entity_id) is not str
        or not request.external_entity_id
    ):
        _fail("invalid_request", "identity request fields must be non-empty strings")
    return IdentityResolveRequest(
        authority_system=request.authority_system,
        external_entity_id=request.external_entity_id,
        corpora=_canonical_corpora(request.corpora),
    )


def _validate_identifier_request(request: IdentifierResolveRequest) -> IdentifierResolveRequest:
    if type(request) is not IdentifierResolveRequest:
        raise TypeError("request must be IdentifierResolveRequest")
    _identifier_key_projection(request.key)
    return IdentifierResolveRequest(
        key=request.key,
        corpora=_canonical_corpora(request.corpora),
    )


def _validate_reference_ir(
    ir: CompiledSemanticIR,
) -> tuple[
    dict[BundleVariantKey, BundleVariantIR],
    dict[CapabilityKey, CapabilityFactsIR],
    dict[tuple[BundleVariantKey, str], NativeRecordIR],
    dict[AuthorityKey, tuple[TargetBindingIR, ...]],
    dict[IdentityKey, tuple[ExternalReferenceIR, ...]],
    dict[IdentifierKey, tuple[ExternalReferenceIR, ...]],
]:
    variants, _semantic, capabilities = _validate_ir_shape(ir)

    parents: dict[tuple[BundleVariantKey, str], NativeRecordIR] = {}
    for key, rows in ir.native_index:
        if type(key) is not NativeKey or type(rows) is not tuple:
            _fail("invalid_compiled_ir", "native index has an invalid row shape")
        if (
            type(key.corpus_id) is not str
            or not key.corpus_id
            or type(key.native_binding_identity) is not str
            or not key.native_binding_identity
        ):
            _fail("invalid_compiled_ir", "native index key fields are invalid")
        for row in rows:
            if type(row) is not NativeRecordIR:
                _fail("invalid_compiled_ir", "native index contains an invalid record")
            _validate_compiled_variant_key(row.variant)
            variant = variants.get(row.variant)
            if variant is None:
                _fail(
                    "invalid_compiled_ir",
                    "native record references a variant outside compiled variants",
                    corpus_id=row.corpus_id,
                    related_id=row.mapping_id,
                )
            if (
                row.corpus_id != variant.key.corpus_id
                or row.corpus_id != key.corpus_id
                or row.native_binding_identity != key.native_binding_identity
            ):
                _fail(
                    "invalid_compiled_ir",
                    "native index key disagrees with native record",
                    corpus_id=variant.key.corpus_id,
                    related_id=row.mapping_id,
                )
            pair = (row.variant, row.mapping_id)
            if pair in parents:
                _fail(
                    "invalid_compiled_ir",
                    "duplicate native parent mapping record",
                    corpus_id=row.corpus_id,
                    related_id=row.mapping_id,
                )
            parents[pair] = row

    authority: dict[AuthorityKey, tuple[TargetBindingIR, ...]] = {}
    for key, rows in ir.authority_index:
        _authority_key_projection(key)
        if type(rows) is not tuple or any(type(row) is not TargetBindingIR for row in rows):
            _fail("invalid_compiled_ir", "authority index has an invalid row shape")
        if key in authority:
            _fail("invalid_compiled_ir", "duplicate authority index key")
        for row in rows:
            variant = variants.get(row.variant)
            if variant is None or row.corpus_id != row.variant.corpus_id:
                _fail(
                    "invalid_compiled_ir",
                    "authority row references an invalid variant",
                    corpus_id=row.corpus_id,
                    related_id=row.mapping_id,
                )
            if (
                row.reference_kind != "authority-value"
                or row.query_role != "authority-value-filter"
                or row.target != key.authority_resource
                or row.formal_kind != key.formal_kind
                or row.semantic_role != key.semantic_role
                or row.ontology_lock.ontology_id != key.authority_system
            ):
                _fail(
                    "invalid_compiled_ir",
                    "authority index key disagrees with binding",
                    corpus_id=row.corpus_id,
                    related_id=row.projection_id,
                )
        authority[key] = rows

    identity: dict[IdentityKey, tuple[ExternalReferenceIR, ...]] = {}
    for key, rows in ir.identity_index:
        if type(key) is not IdentityKey:
            _fail("invalid_compiled_ir", "identity index key has the wrong type")
        if (
            type(key.authority_system) is not str
            or not key.authority_system
            or type(key.external_entity_id) is not str
            or not key.external_entity_id
            or key.identity_strength not in IDENTITY_STRENGTHS
        ):
            _fail("invalid_compiled_ir", "identity index key fields are invalid")
        if type(rows) is not tuple or any(type(row) is not ExternalReferenceIR for row in rows):
            _fail("invalid_compiled_ir", "identity index has an invalid row shape")
        if key in identity:
            _fail("invalid_compiled_ir", "duplicate identity index key")
        for row in rows:
            if variants.get(row.variant) is None or row.corpus_id != row.variant.corpus_id:
                _fail(
                    "invalid_compiled_ir",
                    "identity row references an invalid variant",
                    corpus_id=row.corpus_id,
                    related_id=row.reference_id,
                )
            if (
                row.reference_kind != "entity-identity"
                or row.query_role != "identity-filter"
                or row.authority_system != key.authority_system
                or row.external != key.external_entity_id
                or row.identity_strength != key.identity_strength
            ):
                _fail(
                    "invalid_compiled_ir",
                    "identity index key disagrees with reference",
                    corpus_id=row.corpus_id,
                    related_id=row.reference_id,
                )
        identity[key] = rows

    identifier: dict[IdentifierKey, tuple[ExternalReferenceIR, ...]] = {}
    for key, rows in ir.identifier_index:
        _identifier_key_projection(key)
        if type(rows) is not tuple or any(type(row) is not ExternalReferenceIR for row in rows):
            _fail("invalid_compiled_ir", "identifier index has an invalid row shape")
        if key in identifier:
            _fail("invalid_compiled_ir", "duplicate identifier index key")
        for row in rows:
            if variants.get(row.variant) is None or row.corpus_id != row.variant.corpus_id:
                _fail(
                    "invalid_compiled_ir",
                    "identifier row references an invalid variant",
                    corpus_id=row.corpus_id,
                    related_id=row.reference_id,
                )
            if (
                row.reference_kind != "catalogue-identifier"
                or row.query_role != "identifier-filter"
                or row.issuer_or_namespace != key.issuer_or_namespace
                or row.external != key.literal_id
            ):
                _fail(
                    "invalid_compiled_ir",
                    "identifier index key disagrees with reference",
                    corpus_id=row.corpus_id,
                    related_id=row.reference_id,
                )
        identifier[key] = rows
    return variants, capabilities, parents, authority, identity, identifier


def _reviewed_mapping_payload(
    parent: NativeRecordIR,
    variant: BundleVariantIR,
) -> dict[str, Any]:
    payload = parent.mapping_semantic_payload
    if type(payload) is not str or not payload:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping semantic payload is unavailable",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    try:
        decoded = json.loads(payload)
    except (TypeError, ValueError, RecursionError):
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping semantic payload is invalid JSON",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if type(decoded) is not dict:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping semantic payload must be an object",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    try:
        canonical = canonical_json_bytes(decoded).decode("utf-8")
    except Exception:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping semantic payload is outside canonical JSON",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if canonical != payload:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping semantic payload is not canonical",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if _hash(decoded) != parent.mapping_semantic_digest:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping semantic payload digest mismatch",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    signature = variant.release_signature
    if (parent.mapping_id, parent.mapping_semantic_digest) not in signature.mapping_digests:
        _fail(
            "invalid_compiled_ir",
            "parent mapping digest is not part of selected release",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if (parent.mapping_id, parent.mapping_review) not in signature.mapping_reviews:
        _fail(
            "invalid_compiled_ir",
            "parent mapping review is not selected release authority",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if (
        parent.mapping_review.status != "reviewed"
        or parent.mapping_review.reviewed_semantic_digest != parent.mapping_semantic_digest
    ):
        _fail(
            "invalid_compiled_ir",
            "parent mapping review does not bind current semantics",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if (
        decoded.get("mapping_id") != parent.mapping_id
        or decoded.get("corpus_id") != parent.corpus_id
        or decoded.get("native_state") != parent.native_state
    ):
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping payload identity mismatch",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if tuple(decoded.get("native_dependencies", [])) != parent.native_dependencies:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping dependencies disagree with compiled record",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if tuple(decoded.get("profiles", [])) != parent.profiles or tuple(
        decoded.get("capabilities", [])
    ) != parent.capabilities:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping profile scope disagrees with compiled record",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    native = decoded.get("native_binding")
    if type(native) is not dict:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping native binding is unavailable",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    try:
        source_identity = native_binding_identity(native)
        compiled_identity = native_binding_identity(
            _native_binding_projection(parent.native_binding)
        )
    except Exception:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping native binding is invalid",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if (
        source_identity != parent.native_binding_identity
        or compiled_identity != parent.native_binding_identity
    ):
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping native binding identity mismatch",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    if decoded.get("evidence", []) != [
        _evidence_projection(item) for item in parent.evidence
    ]:
        _fail(
            "invalid_compiled_ir",
            "reviewed parent mapping evidence disagrees with compiled record",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    collections = (
        ("projections", "projection_id", parent.projection_ids),
        ("ambiguous_candidates", "candidate_id", parent.candidate_ids),
        ("external_references", "reference_id", parent.reference_ids),
    )
    for field, id_field, compiled_ids in collections:
        rows = decoded.get(field, [])
        if type(rows) is not list or any(type(row) is not dict for row in rows):
            _fail(
                "invalid_compiled_ir",
                f"reviewed parent mapping {field} is invalid",
                corpus_id=parent.corpus_id,
                related_id=parent.mapping_id,
            )
        payload_ids = tuple(sorted((row.get(id_field) for row in rows), key=_utf16))
        if payload_ids != compiled_ids:
            _fail(
                "invalid_compiled_ir",
                f"reviewed parent mapping {field} IDs disagree with compiled record",
                corpus_id=parent.corpus_id,
                related_id=parent.mapping_id,
            )

    payload_references = decoded.get("external_references", [])
    compiled_reference_ids = tuple(
        sorted((row.reference_id for row in parent.external_references), key=_utf16)
    )
    if compiled_reference_ids != parent.reference_ids:
        _fail(
            "invalid_compiled_ir",
            "compiled parent external-reference tuple disagrees with reference IDs",
            corpus_id=parent.corpus_id,
            related_id=parent.mapping_id,
        )
    for reference in parent.external_references:
        matches = [
            row
            for row in payload_references
            if row.get("reference_id") == reference.reference_id
        ]
        if len(matches) != 1:
            _fail(
                "invalid_compiled_ir",
                "compiled parent external reference is not uniquely present in reviewed payload",
                corpus_id=parent.corpus_id,
                related_id=reference.reference_id,
            )
        _validate_external_reference_payload_child(reference, matches[0])
    return decoded


def _validate_external_reference_payload_child(
    reference: ExternalReferenceIR,
    child: dict[str, Any],
) -> None:
    if type(child) is not dict:
        _fail(
            "invalid_compiled_ir",
            "reviewed external reference payload child is malformed",
            corpus_id=reference.corpus_id,
            related_id=reference.reference_id,
        )
    scalar_pairs = (
        ("reference_id", reference.reference_id),
        ("reference_kind", reference.reference_kind),
        ("query_role", reference.query_role),
        ("external", reference.external),
        ("authority_system", reference.authority_system),
        ("issuer_or_namespace", reference.issuer_or_namespace),
        ("identity_strength", reference.identity_strength),
        ("publication_relation", reference.publication_relation),
    )
    for field, compiled in scalar_pairs:
        if child.get(field) != compiled:
            _fail(
                "invalid_compiled_ir",
                "compiled external reference disagrees with reviewed parent payload",
                corpus_id=reference.corpus_id,
                related_id=reference.reference_id,
            )
    if child.get("evidence", []) != [
        _evidence_projection(item) for item in reference.evidence
    ]:
        _fail(
            "invalid_compiled_ir",
            "compiled external reference evidence disagrees with reviewed payload",
            corpus_id=reference.corpus_id,
            related_id=reference.reference_id,
        )
    source_binding = child.get("native_binding")
    if source_binding is None:
        if reference.native_binding is not None or reference.native_binding_identity is not None:
            _fail(
                "invalid_compiled_ir",
                "compiled external reference invents a native binding",
                corpus_id=reference.corpus_id,
                related_id=reference.reference_id,
            )
        return
    if (
        type(source_binding) is not dict
        or type(reference.native_binding) is not NativeBindingIR
        or type(reference.native_binding_identity) is not str
        or not reference.native_binding_identity
    ):
        _fail(
            "invalid_compiled_ir",
            "compiled external reference native binding is invalid",
            corpus_id=reference.corpus_id,
            related_id=reference.reference_id,
        )
    try:
        source_identity = native_binding_identity(source_binding)
        compiled_identity = native_binding_identity(
            _native_binding_projection(reference.native_binding)
        )
    except Exception:
        _fail(
            "invalid_compiled_ir",
            "compiled external reference native binding cannot be reconstructed",
            corpus_id=reference.corpus_id,
            related_id=reference.reference_id,
        )
    if (
        source_identity != reference.native_binding_identity
        or compiled_identity != reference.native_binding_identity
    ):
        _fail(
            "invalid_compiled_ir",
            "compiled external reference native binding identity mismatch",
            corpus_id=reference.corpus_id,
            related_id=reference.reference_id,
        )


def _authoritative_reference_child(
    reference: ExternalReferenceIR,
    parent: NativeRecordIR,
    variant: BundleVariantIR,
) -> dict[str, Any]:
    if (
        reference.variant != parent.variant
        or reference.corpus_id != parent.corpus_id
        or reference.mapping_id != parent.mapping_id
    ):
        _fail(
            "invalid_compiled_ir",
            "external reference is not scoped by its parent mapping",
            corpus_id=reference.corpus_id,
            related_id=reference.reference_id,
        )
    payload = _reviewed_mapping_payload(parent, variant)
    payload_rows = [
        row
        for row in payload.get("external_references", [])
        if row.get("reference_id") == reference.reference_id
    ]
    compiled_rows = [
        row
        for row in parent.external_references
        if row.reference_id == reference.reference_id
    ]
    if len(payload_rows) != 1 or len(compiled_rows) != 1 or compiled_rows[0] != reference:
        _fail(
            "invalid_compiled_ir",
            "external reference is not uniquely bound by reviewed parent mapping",
            corpus_id=reference.corpus_id,
            related_id=reference.reference_id,
        )
    child = payload_rows[0]
    _validate_external_reference_payload_child(reference, child)
    return child


def _reference_fingerprint(child: dict[str, Any]) -> str:
    return _hash(child)


def _validate_authority_binding_against_release(
    binding: TargetBindingIR,
    variant: BundleVariantIR,
    key: AuthorityKey,
) -> None:
    if (
        binding.reference_kind != "authority-value"
        or binding.query_role != "authority-value-filter"
        or binding.target != key.authority_resource
        or binding.formal_kind != key.formal_kind
        or binding.semantic_role != key.semantic_role
        or binding.ontology_lock.ontology_id != key.authority_system
    ):
        _fail(
            "invalid_compiled_ir",
            "authority binding disagrees with requested authority key",
            corpus_id=binding.corpus_id,
            related_id=binding.projection_id,
        )
    shadow = replace(
        binding,
        reference_kind="semantic-pivot",
        query_role="semantic-constraint",
    )
    _validate_binding_against_release(
        shadow,
        variant,
        SemanticKey(
            profile_id=binding.profile_id,
            capability_id=binding.capability_id,
            target=key.authority_resource,
            formal_kind=key.formal_kind,
            semantic_role=key.semantic_role,
        ),
    )
    _validate_reviewed_projection_payload(binding)


def _authority_loss_record_projection(record: AuthorityLossRecord) -> dict[str, Any]:
    return {
        "corpus_id": record.corpus_id,
        "authority_key": _authority_key_projection(record.authority_key),
        "mapping_id": record.mapping_id,
        "projection_id": record.projection_id,
        "assessment": record.assessment,
        "native_execution_binding_identity": record.native_execution_binding_identity,
        "losses": list(record.losses),
        "effects": list(record.effects),
        "approximation_review_id": record.approximation_review_id,
        "caller_accepted_losses": list(record.caller_accepted_losses),
        "mapping_semantic_digest": record.mapping_semantic_digest,
        "projection_semantic_digest": record.projection_semantic_digest,
        "prerequisite_fingerprint": record.prerequisite_fingerprint,
        "prerequisite_source_contract": record.prerequisite_source_contract,
    }


def _authority_plan_projection(plan: AuthorityNativePlan) -> dict[str, Any]:
    algorithm = (
        EXACT_AUTHORITY_PLAN_FINGERPRINT_ALGORITHM
        if plan.authority_mode == "exact"
        else APPROXIMATE_AUTHORITY_PLAN_FINGERPRINT_ALGORITHM
    )
    return {
        "algorithm": algorithm,
        "resolver_contract": plan.resolver_contract,
        "corpus_id": plan.corpus_id,
        "authority_key": _authority_key_projection(plan.authority_key),
        "query_role": plan.query_role,
        "authority_mode": plan.authority_mode,
        "variant": _variant_projection(plan.variant),
        "profile_release_fingerprint": plan.profile_release_fingerprint,
        "expected_parent_manifest_digest": plan.expected_parent_manifest_digest,
        "observed_parent_manifest_digest": plan.observed_parent_manifest_digest,
        "parent_state": plan.parent_state,
        "prerequisite_fingerprint": plan.prerequisite_fingerprint,
        "prerequisite_source_contract": plan.prerequisite_source_contract,
        "mapping_id": plan.mapping_id,
        "projection_id": plan.projection_id,
        "profile_id": plan.profile_id,
        "capability_id": plan.capability_id,
        "assessment": plan.assessment,
        "native_execution_binding_identity": plan.native_execution_binding_identity,
        "native_dependencies": list(plan.native_dependencies),
        "mapping_semantic_digest": plan.mapping_semantic_digest,
        "projection_semantic_digest": plan.projection_semantic_digest,
        "mapping_review": _review_projection(plan.mapping_review),
        "projection_review": _review_projection(plan.projection_review),
        "ontology_lock": _lock_projection(plan.ontology_lock),
        "ontology_bundle_digest": plan.ontology_bundle_digest,
        "mapping_evidence": [_evidence_projection(item) for item in plan.mapping_evidence],
        "projection_evidence": [
            _evidence_projection(item) for item in plan.projection_evidence
        ],
        "approximation": _approximation_projection(plan.approximation),
        "losses": list(plan.losses),
        "loss_record": (
            None
            if plan.loss_record is None
            else _authority_loss_record_projection(plan.loss_record)
        ),
    }


def _make_authority_plan(
    binding: TargetBindingIR,
    variant: BundleVariantIR,
    state: RuntimePrerequisiteState,
    key: AuthorityKey,
    *,
    mode: str,
    accepted_losses: tuple[str, ...] = (),
) -> AuthorityNativePlan:
    prerequisite_fingerprint = runtime_prerequisite_fingerprint(state)
    approximation = binding.approximation if binding.assessment != "exact" else None
    losses: tuple[str, ...] = ()
    loss_record: AuthorityLossRecord | None = None
    if binding.assessment != "exact":
        if type(approximation) is not ApproximationIR:
            _fail(
                "invalid_compiled_ir",
                "selected approximate authority binding lacks approximation authority",
                corpus_id=binding.corpus_id,
                related_id=binding.projection_id,
            )
        losses = approximation.losses
        loss_record = AuthorityLossRecord(
            corpus_id=binding.corpus_id,
            authority_key=key,
            mapping_id=binding.mapping_id,
            projection_id=binding.projection_id,
            assessment=binding.assessment,
            native_execution_binding_identity=binding.native_execution_binding_identity,
            losses=losses,
            effects=tuple(_APPROXIMATION_EFFECTS[item] for item in losses),
            approximation_review_id=approximation.review_id,
            caller_accepted_losses=accepted_losses,
            mapping_semantic_digest=binding.mapping_semantic_digest,
            projection_semantic_digest=binding.projection_semantic_digest,
            prerequisite_fingerprint=prerequisite_fingerprint,
            prerequisite_source_contract=state.source_contract,
        )
    contract = (
        EXACT_AUTHORITY_RESOLVER_CONTRACT
        if mode == "exact"
        else APPROXIMATE_AUTHORITY_RESOLVER_CONTRACT
    )
    values = dict(
        resolver_contract=contract,
        corpus_id=binding.corpus_id,
        authority_key=key,
        query_role="authority-value-filter",
        authority_mode=mode,
        variant=variant.key,
        profile_release_fingerprint=state.profile_release_fingerprint,
        expected_parent_manifest_digest=variant.key.expected_parent_manifest_digest,
        observed_parent_manifest_digest=state.observed_parent_manifest_digest,
        parent_state=state.parent_state,
        prerequisite_fingerprint=prerequisite_fingerprint,
        prerequisite_source_contract=state.source_contract,
        mapping_id=binding.mapping_id,
        projection_id=binding.projection_id,
        profile_id=binding.profile_id,
        capability_id=binding.capability_id,
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
        approximation=approximation,
        losses=losses,
        loss_record=loss_record,
    )
    provisional = AuthorityNativePlan(plan_fingerprint="", **values)
    return AuthorityNativePlan(
        plan_fingerprint=_hash(_authority_plan_projection(provisional)),
        **values,
    )


def _require_authority_capability(
    binding: TargetBindingIR,
    variant: BundleVariantIR,
    state: RuntimePrerequisiteState,
    capabilities: dict[CapabilityKey, CapabilityFactsIR],
) -> None:
    view = _capability_view(
        variant,
        state,
        binding.profile_id,
        binding.capability_id,
        capabilities,
    )
    if view.state == "absent":
        _fail(
            "capability_absent",
            "authority binding capability is absent",
            corpus_id=binding.corpus_id,
        )
    if view.state != "active":
        _fail(
            "capability_unavailable",
            "authority binding capability is unavailable",
            corpus_id=binding.corpus_id,
        )


def authority_resolve_exact(
    ir: CompiledSemanticIR,
    request: AuthorityResolveRequest,
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> AuthorityResolutionResult:
    canonical = _validate_authority_request(request)
    variants, capabilities, _parents, authority, _identity, _identifier = _validate_reference_ir(ir)
    prerequisite_rows = _materialize_prerequisites(prerequisites)
    rows_for_key = authority.get(canonical.key)
    plans: list[AuthorityNativePlan] = []
    for corpus_id in canonical.corpora:
        state, variant = _select_prerequisite(corpus_id, prerequisite_rows, variants)
        problem = _prerequisite_problem(state, variant)
        if problem is not None:
            _fail(problem, "runtime prerequisite is not executable", corpus_id=corpus_id)
        candidates = [] if rows_for_key is None else [
            row
            for row in rows_for_key
            if row.corpus_id == corpus_id and row.variant == variant.key
        ]
        if not candidates:
            _fail(
                "authority_reference_absent",
                "authority reference is absent for selected corpus variant",
                corpus_id=corpus_id,
            )
        for row in candidates:
            _validate_authority_binding_against_release(row, variant, canonical.key)
        exact = [row for row in candidates if row.assessment == "exact"]
        if len(exact) > 1:
            _fail(
                "multiple_authority_bindings",
                "multiple exact authority bindings require explicit composition",
                corpus_id=corpus_id,
            )
        if not exact:
            if any(row.assessment in {"close", "broader", "narrower"} for row in candidates):
                _fail(
                    "non_exact_authority_mapping",
                    "authority reference has no exact mapping",
                    corpus_id=corpus_id,
                )
            if any(row.assessment == "related" for row in candidates):
                _fail(
                    "non_substitutive_authority_mapping",
                    "authority reference has only related mapping",
                    corpus_id=corpus_id,
                )
            _fail(
                "authority_reference_absent",
                "authority reference has no executable exact mapping",
                corpus_id=corpus_id,
            )
        selected = exact[0]
        _require_authority_capability(selected, variant, state, capabilities)
        plans.append(
            _make_authority_plan(
                selected,
                variant,
                state,
                canonical.key,
                mode="exact",
            )
        )
    plans.sort(key=lambda row: _utf16(row.corpus_id))
    plan_tuple = tuple(plans)
    projection = {
        "algorithm": EXACT_AUTHORITY_RESOLUTION_FINGERPRINT_ALGORITHM,
        "resolver_contract": EXACT_AUTHORITY_RESOLVER_CONTRACT,
        "request": {
            "key": _authority_key_projection(canonical.key),
            "corpora": list(canonical.corpora),
            "authority_mode": "exact",
        },
        "comparison_state": "exactly-comparable",
        "losses": [],
        "plan_fingerprints": [row.plan_fingerprint for row in plan_tuple],
    }
    return AuthorityResolutionResult(
        resolver_contract=EXACT_AUTHORITY_RESOLVER_CONTRACT,
        request=canonical,
        plans=plan_tuple,
        comparison_state="exactly-comparable",
        losses=(),
        resolution_fingerprint=_hash(projection),
    )


def authority_resolve_approximate(
    ir: CompiledSemanticIR,
    request: ApproximateAuthorityResolveRequest,
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> ApproximateAuthorityResolutionResult:
    canonical = _validate_approximate_authority_request(request)
    variants, capabilities, _parents, authority, _identity, _identifier = _validate_reference_ir(ir)
    prerequisite_rows = _materialize_prerequisites(prerequisites)
    rows_for_key = authority.get(canonical.key)
    plans: list[AuthorityNativePlan] = []
    for corpus_id in canonical.corpora:
        state, variant = _select_prerequisite(corpus_id, prerequisite_rows, variants)
        problem = _prerequisite_problem(state, variant)
        if problem is not None:
            _fail(problem, "runtime prerequisite is not executable", corpus_id=corpus_id)
        candidates = [] if rows_for_key is None else [
            row
            for row in rows_for_key
            if row.corpus_id == corpus_id and row.variant == variant.key
        ]
        if not candidates:
            _fail(
                "authority_reference_absent",
                "authority reference is absent for selected corpus variant",
                corpus_id=corpus_id,
            )
        for row in candidates:
            _validate_authority_binding_against_release(row, variant, canonical.key)
        exact = [row for row in candidates if row.assessment == "exact"]
        if len(exact) > 1:
            _fail(
                "multiple_authority_bindings",
                "multiple exact authority bindings require explicit composition",
                corpus_id=corpus_id,
            )
        if exact:
            selected = exact[0]
        else:
            substitutive = [
                row
                for row in candidates
                if row.assessment in {"close", "broader", "narrower"}
            ]
            if not substitutive:
                if any(row.assessment == "related" for row in candidates):
                    _fail(
                        "non_substitutive_authority_mapping",
                        "authority reference has only related mappings",
                        corpus_id=corpus_id,
                    )
                _fail(
                    "approximation_not_authorized",
                    "authority reference has no approximation-authorized mapping",
                    corpus_id=corpus_id,
                )
            authorized = [
                row
                for row in substitutive
                if row.approximation is not None and row.approximation.eligible is True
            ]
            if not authorized:
                _fail(
                    "approximation_not_authorized",
                    "authority reference has no reviewed eligible approximation",
                    corpus_id=corpus_id,
                )
            if len(authorized) > 1:
                _fail(
                    "multiple_approximate_authority_bindings",
                    "multiple eligible approximate authority bindings require explicit composition",
                    corpus_id=corpus_id,
                )
            selected = authorized[0]
            approximation = selected.approximation
            if type(approximation) is not ApproximationIR:
                _fail(
                    "invalid_compiled_ir",
                    "selected approximate authority binding has invalid authority",
                    corpus_id=corpus_id,
                    related_id=selected.projection_id,
                )
            missing = [
                loss for loss in approximation.losses if loss not in canonical.accept_losses
            ]
            if missing:
                _fail(
                    "approximation_loss_not_accepted",
                    f"caller did not accept required approximation loss: {missing[0]}",
                    corpus_id=corpus_id,
                    related_id=selected.projection_id,
                )
        _require_authority_capability(selected, variant, state, capabilities)
        plans.append(
            _make_authority_plan(
                selected,
                variant,
                state,
                canonical.key,
                mode="approximate",
                accepted_losses=canonical.accept_losses,
            )
        )
    plans.sort(key=lambda row: _utf16(row.corpus_id))
    plan_tuple = tuple(plans)
    losses = _union_losses(row.losses for row in plan_tuple)
    nonempty = {row.losses for row in plan_tuple if row.losses}
    comparison = (
        "exactly-comparable"
        if not nonempty
        else "approximately-comparable"
        if len(nonempty) == 1
        else "heterogeneous-loss"
    )
    loss_records = tuple(row.loss_record for row in plan_tuple if row.loss_record is not None)
    projection = {
        "algorithm": APPROXIMATE_AUTHORITY_RESOLUTION_FINGERPRINT_ALGORITHM,
        "resolver_contract": APPROXIMATE_AUTHORITY_RESOLVER_CONTRACT,
        "request": {
            "key": _authority_key_projection(canonical.key),
            "corpora": list(canonical.corpora),
            "authority_mode": "approximate",
            "accept_losses": list(canonical.accept_losses),
        },
        "comparison_state": comparison,
        "losses": list(losses),
        "loss_records": [
            _authority_loss_record_projection(row) for row in loss_records
        ],
        "plan_fingerprints": [row.plan_fingerprint for row in plan_tuple],
    }
    return ApproximateAuthorityResolutionResult(
        resolver_contract=APPROXIMATE_AUTHORITY_RESOLVER_CONTRACT,
        request=canonical,
        plans=plan_tuple,
        comparison_state=comparison,
        losses=losses,
        loss_records=loss_records,
        resolution_fingerprint=_hash(projection),
    )


def _reference_plan_common(
    reference: ExternalReferenceIR,
    parent: NativeRecordIR,
    variant: BundleVariantIR,
    state: RuntimePrerequisiteState,
    child: dict[str, Any],
) -> dict[str, Any]:
    if (
        type(reference.native_binding) is not NativeBindingIR
        or type(reference.native_binding_identity) is not str
        or not reference.native_binding_identity
    ):
        _fail(
            "invalid_compiled_ir",
            "reviewed external reference lacks explicit native binding",
            corpus_id=reference.corpus_id,
            related_id=reference.reference_id,
        )
    return {
        "corpus_id": reference.corpus_id,
        "variant": variant.key,
        "mapping_id": reference.mapping_id,
        "reference_id": reference.reference_id,
        "reference_kind": reference.reference_kind,
        "query_role": reference.query_role,
        "mapping_semantic_digest": parent.mapping_semantic_digest,
        "mapping_review": parent.mapping_review,
        "reference_evidence": reference.evidence,
        "reference_fingerprint": _reference_fingerprint(child),
        "native_execution_binding_identity": reference.native_binding_identity,
        "native_execution_binding": reference.native_binding,
        "native_dependencies": parent.native_dependencies,
        "prerequisite_fingerprint": runtime_prerequisite_fingerprint(state),
        "prerequisite_source_contract": state.source_contract,
        "profile_release_fingerprint": state.profile_release_fingerprint,
        "expected_parent_manifest_digest": variant.key.expected_parent_manifest_digest,
        "observed_parent_manifest_digest": state.observed_parent_manifest_digest,
        "parent_state": state.parent_state,
    }


def _identity_plan_projection(plan: IdentityNativePlan) -> dict[str, Any]:
    return {
        "algorithm": IDENTITY_PLAN_FINGERPRINT_ALGORITHM,
        "resolver_contract": plan.resolver_contract,
        "corpus_id": plan.corpus_id,
        "variant": _variant_projection(plan.variant),
        "authority_system": plan.authority_system,
        "external_entity_id": plan.external_entity_id,
        "identity_strength": plan.identity_strength,
        "mapping_id": plan.mapping_id,
        "reference_id": plan.reference_id,
        "reference_kind": plan.reference_kind,
        "query_role": plan.query_role,
        "mapping_semantic_digest": plan.mapping_semantic_digest,
        "mapping_review": _review_projection(plan.mapping_review),
        "reference_evidence": [
            _evidence_projection(item) for item in plan.reference_evidence
        ],
        "reference_fingerprint": plan.reference_fingerprint,
        "native_execution_binding_identity": plan.native_execution_binding_identity,
        "native_dependencies": list(plan.native_dependencies),
        "prerequisite_fingerprint": plan.prerequisite_fingerprint,
        "prerequisite_source_contract": plan.prerequisite_source_contract,
        "profile_release_fingerprint": plan.profile_release_fingerprint,
        "expected_parent_manifest_digest": plan.expected_parent_manifest_digest,
        "observed_parent_manifest_digest": plan.observed_parent_manifest_digest,
        "parent_state": plan.parent_state,
    }


def _identifier_plan_projection(plan: IdentifierNativePlan) -> dict[str, Any]:
    return {
        "algorithm": IDENTIFIER_PLAN_FINGERPRINT_ALGORITHM,
        "resolver_contract": plan.resolver_contract,
        "corpus_id": plan.corpus_id,
        "variant": _variant_projection(plan.variant),
        "key": _identifier_key_projection(plan.key),
        "mapping_id": plan.mapping_id,
        "reference_id": plan.reference_id,
        "reference_kind": plan.reference_kind,
        "query_role": plan.query_role,
        "mapping_semantic_digest": plan.mapping_semantic_digest,
        "mapping_review": _review_projection(plan.mapping_review),
        "reference_evidence": [
            _evidence_projection(item) for item in plan.reference_evidence
        ],
        "reference_fingerprint": plan.reference_fingerprint,
        "native_execution_binding_identity": plan.native_execution_binding_identity,
        "native_dependencies": list(plan.native_dependencies),
        "prerequisite_fingerprint": plan.prerequisite_fingerprint,
        "prerequisite_source_contract": plan.prerequisite_source_contract,
        "profile_release_fingerprint": plan.profile_release_fingerprint,
        "expected_parent_manifest_digest": plan.expected_parent_manifest_digest,
        "observed_parent_manifest_digest": plan.observed_parent_manifest_digest,
        "parent_state": plan.parent_state,
    }


def identity_resolve(
    ir: CompiledSemanticIR,
    request: IdentityResolveRequest,
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> IdentityResolutionResult:
    canonical = _validate_identity_request(request)
    variants, _capabilities, parents, _authority, identity, _identifier = _validate_reference_ir(ir)
    prerequisite_rows = _materialize_prerequisites(prerequisites)
    plans: list[IdentityNativePlan] = []
    for corpus_id in canonical.corpora:
        state, variant = _select_prerequisite(corpus_id, prerequisite_rows, variants)
        problem = _prerequisite_problem(state, variant)
        if problem is not None:
            _fail(problem, "runtime prerequisite is not executable", corpus_id=corpus_id)
        candidates: list[tuple[ExternalReferenceIR, NativeRecordIR, dict[str, Any]]] = []
        for key, rows in identity.items():
            if (
                key.authority_system != canonical.authority_system
                or key.external_entity_id != canonical.external_entity_id
            ):
                continue
            for row in rows:
                if row.corpus_id != corpus_id or row.variant != variant.key:
                    continue
                parent = parents.get((row.variant, row.mapping_id))
                if parent is None:
                    _fail(
                        "invalid_compiled_ir",
                        "identity reference has no parent mapping record",
                        corpus_id=corpus_id,
                        related_id=row.reference_id,
                    )
                child = _authoritative_reference_child(row, parent, variant)
                candidates.append((row, parent, child))
        if not candidates:
            _fail(
                "identity_reference_absent",
                "identity reference is absent for selected corpus variant",
                corpus_id=corpus_id,
            )
        exact = [item for item in candidates if item[0].identity_strength == "same-entity"]
        if len(exact) > 1:
            _fail(
                "multiple_identity_bindings",
                "multiple same-entity bindings require explicit composition",
                corpus_id=corpus_id,
            )
        if not exact:
            _fail(
                "identity_not_exact",
                "reviewed identity exists but no same-entity authority is available",
                corpus_id=corpus_id,
            )
        reference, parent, child = exact[0]
        common = _reference_plan_common(reference, parent, variant, state, child)
        values = dict(
            resolver_contract=IDENTITY_RESOLVER_CONTRACT,
            authority_system=canonical.authority_system,
            external_entity_id=canonical.external_entity_id,
            identity_strength="same-entity",
            **common,
        )
        provisional = IdentityNativePlan(plan_fingerprint="", **values)
        plans.append(
            IdentityNativePlan(
                plan_fingerprint=_hash(_identity_plan_projection(provisional)),
                **values,
            )
        )
    plans.sort(key=lambda row: _utf16(row.corpus_id))
    plan_tuple = tuple(plans)
    projection = {
        "algorithm": IDENTITY_RESOLUTION_FINGERPRINT_ALGORITHM,
        "resolver_contract": IDENTITY_RESOLVER_CONTRACT,
        "request": {
            "authority_system": canonical.authority_system,
            "external_entity_id": canonical.external_entity_id,
            "corpora": list(canonical.corpora),
        },
        "plan_fingerprints": [row.plan_fingerprint for row in plan_tuple],
    }
    return IdentityResolutionResult(
        resolver_contract=IDENTITY_RESOLVER_CONTRACT,
        request=canonical,
        plans=plan_tuple,
        resolution_fingerprint=_hash(projection),
    )


def identifier_resolve(
    ir: CompiledSemanticIR,
    request: IdentifierResolveRequest,
    prerequisites: Iterable[RuntimePrerequisiteState],
) -> IdentifierResolutionResult:
    canonical = _validate_identifier_request(request)
    variants, _capabilities, parents, _authority, _identity, identifier = _validate_reference_ir(ir)
    prerequisite_rows = _materialize_prerequisites(prerequisites)
    rows_for_key = identifier.get(canonical.key)
    plans: list[IdentifierNativePlan] = []
    for corpus_id in canonical.corpora:
        state, variant = _select_prerequisite(corpus_id, prerequisite_rows, variants)
        problem = _prerequisite_problem(state, variant)
        if problem is not None:
            _fail(problem, "runtime prerequisite is not executable", corpus_id=corpus_id)
        rows = [] if rows_for_key is None else [
            row
            for row in rows_for_key
            if row.corpus_id == corpus_id and row.variant == variant.key
        ]
        if not rows:
            _fail(
                "identifier_reference_absent",
                "identifier reference is absent for selected corpus variant",
                corpus_id=corpus_id,
            )
        candidates: list[tuple[ExternalReferenceIR, NativeRecordIR, dict[str, Any]]] = []
        for row in rows:
            parent = parents.get((row.variant, row.mapping_id))
            if parent is None:
                _fail(
                    "invalid_compiled_ir",
                    "identifier reference has no parent mapping record",
                    corpus_id=corpus_id,
                    related_id=row.reference_id,
                )
            candidates.append((row, parent, _authoritative_reference_child(row, parent, variant)))
        if len(candidates) > 1:
            _fail(
                "multiple_identifier_bindings",
                "multiple identifier bindings require explicit composition",
                corpus_id=corpus_id,
            )
        reference, parent, child = candidates[0]
        common = _reference_plan_common(reference, parent, variant, state, child)
        values = dict(
            resolver_contract=IDENTIFIER_RESOLVER_CONTRACT,
            key=canonical.key,
            **common,
        )
        provisional = IdentifierNativePlan(plan_fingerprint="", **values)
        plans.append(
            IdentifierNativePlan(
                plan_fingerprint=_hash(_identifier_plan_projection(provisional)),
                **values,
            )
        )
    plans.sort(key=lambda row: _utf16(row.corpus_id))
    plan_tuple = tuple(plans)
    projection = {
        "algorithm": IDENTIFIER_RESOLUTION_FINGERPRINT_ALGORITHM,
        "resolver_contract": IDENTIFIER_RESOLVER_CONTRACT,
        "request": {
            "key": _identifier_key_projection(canonical.key),
            "corpora": list(canonical.corpora),
        },
        "plan_fingerprints": [row.plan_fingerprint for row in plan_tuple],
    }
    return IdentifierResolutionResult(
        resolver_contract=IDENTIFIER_RESOLVER_CONTRACT,
        request=canonical,
        plans=plan_tuple,
        resolution_fingerprint=_hash(projection),
    )
