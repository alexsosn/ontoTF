from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

from .digests import (
    MAPPING_SEMANTIC_ALGORITHM_V2,
    PROJECTION_SEMANTIC_ALGORITHM,
    canonical_json_bytes,
)
from .semantic_validation import ValidatedSemanticBundle

NATIVE_BINDING_IDENTITY_ALGORITHM = "tfont-native-binding-jcs-sha256-v1"


@dataclass(frozen=True)
class SemanticIRProblem:
    category: str
    message: str
    corpus_id: str | None = None
    mapping_id: str | None = None
    related_id: str | None = None


class SemanticIRError(ValueError):
    def __init__(self, problem: SemanticIRProblem):
        self.problem = problem
        super().__init__(f"{problem.category}: {problem.message}")


@dataclass(frozen=True)
class EdgeStepIR:
    edge: str
    direction: str


@dataclass(frozen=True)
class NativeBindingIR:
    component_id: str | None
    node_type: str | None
    feature: str | None
    value_present: bool
    value: str | int | float | bool | None
    closed_values: tuple[str | int | float | bool | None, ...] | None
    edge: str | None
    direction: str | None
    steps: tuple[EdgeStepIR, ...] | None
    interpretation: str | None
    execution_shape: str | None
    values: tuple[str | int | float | bool | None, ...] | None = None


@dataclass(frozen=True)
class EvidenceFingerprint:
    evidence_id: str
    content_digest: str


@dataclass(frozen=True)
class ReviewFingerprint:
    review_id: str
    status: str
    reviewed_semantic_digest: str


@dataclass(frozen=True)
class OntologyLockFingerprint:
    lock_id: str
    ontology_id: str
    release: str
    content_digest: str
    term_namespace: str


@dataclass(frozen=True)
class OntologyBundleRequirementIR:
    bundle_digest: str
    required_profile_contracts: tuple[str, ...]


@dataclass(frozen=True)
class OntologyDeclarationIR:
    ontology_lock_id: str
    ontology_lock_content_digest: str
    rdf_types: tuple[str, ...]
    domain_iris: tuple[str, ...]
    range_iris: tuple[str, ...]
    value_kind: str | None


@dataclass(frozen=True)
class ApproximationIR:
    status: str
    eligible: bool
    losses: tuple[str, ...]
    rationale: str
    review_id: str
    evidence: tuple[EvidenceFingerprint, ...]


@dataclass(frozen=True)
class ProfileReleaseKey:
    corpus_id: str
    authored_profile_id: str
    profile_version: str


@dataclass(frozen=True)
class BundleVariantKey:
    corpus_id: str
    authored_profile_id: str
    profile_version: str
    expected_parent_manifest_digest: str
    ontology_bundle_digest: str | None


@dataclass(frozen=True)
class ProfileReleaseSignature:
    profile_schema_version: int
    profile_catalog_version: int
    dependency_contract_version: int
    mapping_schema_version: int
    minimum_tfont_runtime: str
    profiles: tuple[str, ...]
    capabilities: tuple[str, ...]
    dependency_records: tuple[tuple[str, str], ...]
    mapping_digests: tuple[tuple[str, str], ...]
    ontology_bundle_digest: str | None
    ontology_locks: tuple[OntologyLockFingerprint, ...]
    mapping_semantic_algorithm: str
    projection_semantic_algorithm: str
    mapping_reviews: tuple[tuple[str, ReviewFingerprint], ...]
    projection_reviews: tuple[tuple[str, str, ReviewFingerprint], ...]
    parent_compatibility: str = "exact-only"


@dataclass(frozen=True)
class BundleVariantIR:
    key: BundleVariantKey
    release_key: ProfileReleaseKey
    release_signature: ProfileReleaseSignature
    profile_schema_version: int
    profile_catalog_version: int
    dependency_contract_version: int
    mapping_schema_version: int
    mapping_semantic_algorithm: str
    projection_semantic_algorithm: str
    mapping_digests: tuple[tuple[str, str], ...]
    ontology_locks: tuple[OntologyLockFingerprint, ...]


@dataclass(frozen=True)
class CandidateIR:
    variant: BundleVariantKey
    corpus_id: str
    mapping_id: str
    candidate_id: str
    target: str
    reference_kind: str
    query_role: str
    formal_kind: str
    semantic_role: str
    profile_id: str
    capability_id: str
    assessment_candidate: str
    ontology_lock: OntologyLockFingerprint
    ontology_declaration_evidence: OntologyDeclarationIR | None
    evidence: tuple[EvidenceFingerprint, ...]


@dataclass(frozen=True)
class ExternalReferenceIR:
    variant: BundleVariantKey
    corpus_id: str
    mapping_id: str
    reference_id: str
    reference_kind: str
    query_role: str
    external: str
    authority_system: str | None
    issuer_or_namespace: str | None
    identity_strength: str | None
    native_binding_identity: str | None
    native_binding: NativeBindingIR | None
    publication_relation: str | None
    evidence: tuple[EvidenceFingerprint, ...]


@dataclass(frozen=True)
class NativeRecordIR:
    variant: BundleVariantKey
    corpus_id: str
    mapping_id: str
    native_binding_identity: str
    native_binding: NativeBindingIR
    native_dependencies: tuple[str, ...]
    profiles: tuple[str, ...]
    capabilities: tuple[str, ...]
    native_state: str
    mapping_semantic_digest: str
    mapping_review: ReviewFingerprint
    evidence: tuple[EvidenceFingerprint, ...]
    projection_ids: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    reference_ids: tuple[str, ...]
    candidates: tuple[CandidateIR, ...]
    external_references: tuple[ExternalReferenceIR, ...]


@dataclass(frozen=True)
class TargetBindingIR:
    variant: BundleVariantKey
    corpus_id: str
    mapping_id: str
    projection_id: str
    target: str
    reference_kind: str
    query_role: str
    formal_kind: str
    semantic_role: str
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
    ontology_bundle_requirement: OntologyBundleRequirementIR | None
    ontology_declaration_evidence: OntologyDeclarationIR | None
    publication_relation: str | None
    approximation: ApproximationIR | None
    mapping_evidence: tuple[EvidenceFingerprint, ...]
    projection_evidence: tuple[EvidenceFingerprint, ...]


@dataclass(frozen=True)
class SemanticKey:
    profile_id: str
    capability_id: str
    target: str
    formal_kind: str
    semantic_role: str


@dataclass(frozen=True)
class AuthorityKey:
    authority_system: str
    authority_resource: str
    formal_kind: str
    semantic_role: str


@dataclass(frozen=True)
class IdentityKey:
    authority_system: str
    external_entity_id: str
    identity_strength: str


@dataclass(frozen=True)
class IdentifierKey:
    issuer_or_namespace: str
    literal_id: str


@dataclass(frozen=True)
class NativeKey:
    corpus_id: str
    native_binding_identity: str


@dataclass(frozen=True)
class CapabilityKey:
    variant: BundleVariantKey
    profile_id: str
    capability_id: str


@dataclass(frozen=True)
class CapabilityFactsIR:
    reviewed_native_support: int
    shared_projections: int
    exact: int
    close: int
    broader: int
    narrower: int
    related: int
    ambiguous: int
    native_only: int
    unsupported: int
    mapping_ids: tuple[str, ...]


@dataclass(frozen=True)
class CompiledSemanticIR:
    variants: tuple[BundleVariantIR, ...]
    native_index: tuple[tuple[NativeKey, tuple[NativeRecordIR, ...]], ...]
    semantic_index: tuple[tuple[SemanticKey, tuple[TargetBindingIR, ...]], ...]
    authority_index: tuple[tuple[AuthorityKey, tuple[TargetBindingIR, ...]], ...]
    identity_index: tuple[tuple[IdentityKey, tuple[ExternalReferenceIR, ...]], ...]
    identifier_index: tuple[tuple[IdentifierKey, tuple[ExternalReferenceIR, ...]], ...]
    capability_facts: tuple[tuple[CapabilityKey, CapabilityFactsIR], ...]


def _utf16(value: str) -> bytes:
    return value.encode("utf-16be")


def _nullable_utf16(value: str | None) -> tuple[int, bytes]:
    return (0, b"") if value is None else (1, _utf16(value))


def _strings(value: Any) -> tuple[str, ...]:
    if type(value) is not list:
        return ()
    return tuple(sorted((item for item in value if type(item) is str), key=_utf16))


def _evidence(value: Any) -> tuple[EvidenceFingerprint, ...]:
    if type(value) is not list:
        return ()
    rows = [
        EvidenceFingerprint(item["evidence_id"], item["content_digest"])
        for item in value
        if type(item) is dict
    ]
    rows.sort(key=lambda item: (_utf16(item.evidence_id), _utf16(item.content_digest)))
    return tuple(rows)


def _review(value: dict[str, Any]) -> ReviewFingerprint:
    return ReviewFingerprint(
        review_id=value["review_id"],
        status=value["status"],
        reviewed_semantic_digest=value["reviewed_mapping_digest"],
    )


def _lock(value: dict[str, Any]) -> OntologyLockFingerprint:
    return OntologyLockFingerprint(
        lock_id=value["lock_id"],
        ontology_id=value["ontology_id"],
        release=value["release"],
        content_digest=value["content_digest"],
        term_namespace=value["term_namespace"],
    )


def _ontology_bundle_requirement(value: Any) -> OntologyBundleRequirementIR | None:
    if type(value) is not dict:
        return None
    return OntologyBundleRequirementIR(
        bundle_digest=value["bundle_digest"],
        required_profile_contracts=_strings(value.get("required_profile_contracts", [])),
    )


def _ontology_declaration(value: Any) -> OntologyDeclarationIR | None:
    if type(value) is not dict:
        return None
    return OntologyDeclarationIR(
        ontology_lock_id=value["ontology_lock_id"],
        ontology_lock_content_digest=value["ontology_lock_content_digest"],
        rdf_types=_strings(value.get("rdf_types", [])),
        domain_iris=_strings(value.get("domain_iris", [])),
        range_iris=_strings(value.get("range_iris", [])),
        value_kind=value.get("value_kind"),
    )


def _approximation(value: Any) -> ApproximationIR | None:
    if type(value) is not dict:
        return None
    return ApproximationIR(
        status=value["status"],
        eligible=value["eligible"],
        losses=_strings(value.get("losses", [])),
        rationale=value["rationale"],
        review_id=value["review_id"],
        evidence=_evidence(value.get("evidence", [])),
    )


def _lock_sort_key(value: OntologyLockFingerprint) -> tuple[bytes, ...]:
    return tuple(
        _utf16(item)
        for item in (
            value.lock_id,
            value.ontology_id,
            value.release,
            value.content_digest,
            value.term_namespace,
        )
    )


def _variant_sort_key(value: BundleVariantKey) -> tuple[Any, ...]:
    return (
        _utf16(value.corpus_id),
        _utf16(value.authored_profile_id),
        _utf16(value.profile_version),
        _utf16(value.expected_parent_manifest_digest),
        _nullable_utf16(value.ontology_bundle_digest),
    )


def _native_key_sort(value: NativeKey) -> tuple[bytes, bytes]:
    return (_utf16(value.corpus_id), _utf16(value.native_binding_identity))


def _semantic_key_sort(value: SemanticKey) -> tuple[bytes, ...]:
    return tuple(
        _utf16(item)
        for item in (
            value.profile_id,
            value.capability_id,
            value.target,
            value.formal_kind,
            value.semantic_role,
        )
    )


def _authority_key_sort(value: AuthorityKey) -> tuple[bytes, ...]:
    return tuple(
        _utf16(item)
        for item in (
            value.authority_system,
            value.authority_resource,
            value.formal_kind,
            value.semantic_role,
        )
    )


def _identity_key_sort(value: IdentityKey) -> tuple[bytes, ...]:
    return tuple(
        _utf16(item)
        for item in (value.authority_system, value.external_entity_id, value.identity_strength)
    )


def _identifier_key_sort(value: IdentifierKey) -> tuple[bytes, bytes]:
    return (_utf16(value.issuer_or_namespace), _utf16(value.literal_id))


def _capability_key_sort(value: CapabilityKey) -> tuple[Any, ...]:
    return (_variant_sort_key(value.variant), _utf16(value.profile_id), _utf16(value.capability_id))


def _binding_sort(value: TargetBindingIR) -> tuple[Any, ...]:
    return (
        _variant_sort_key(value.variant),
        _utf16(value.corpus_id),
        _utf16(value.mapping_id),
        _utf16(value.projection_id),
        _utf16(value.native_execution_binding_identity),
    )


def _native_record_sort(value: NativeRecordIR) -> tuple[Any, ...]:
    return (
        _variant_sort_key(value.variant),
        _utf16(value.corpus_id),
        _utf16(value.mapping_id),
        _utf16(value.native_binding_identity),
    )


def _reference_sort(value: ExternalReferenceIR) -> tuple[Any, ...]:
    return (
        _variant_sort_key(value.variant),
        _utf16(value.corpus_id),
        _utf16(value.mapping_id),
        _utf16(value.reference_id),
    )


def native_binding_identity(binding: dict[str, Any]) -> str:
    if type(binding) is not dict:
        raise TypeError("native binding must be an exact dict")
    normalized = dict(binding)
    selected_values = normalized.get("values")
    if type(selected_values) is list:
        normalized["values"] = sorted(selected_values, key=canonical_json_bytes)
    payload = canonical_json_bytes(normalized)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _native_binding(binding: dict[str, Any]) -> NativeBindingIR:
    steps_value = binding.get("steps")
    steps = None
    if type(steps_value) is list:
        steps = tuple(EdgeStepIR(step["edge"], step["direction"]) for step in steps_value)
    closed_value = binding.get("closed_values")
    closed_values = tuple(closed_value) if type(closed_value) is list else None
    selected_value = binding.get("values")
    selected_values = (
        tuple(sorted(selected_value, key=canonical_json_bytes))
        if type(selected_value) is list
        else None
    )
    return NativeBindingIR(
        component_id=binding.get("component_id"),
        node_type=binding.get("node_type"),
        feature=binding.get("feature"),
        value_present="value" in binding,
        value=binding.get("value"),
        closed_values=closed_values,
        edge=binding.get("edge"),
        direction=binding.get("direction"),
        steps=steps,
        interpretation=binding.get("interpretation"),
        execution_shape=binding.get("execution_shape"),
        values=selected_values,
    )


def _normalize_dependency(value: Any, *, field: str | None = None) -> Any:
    if type(value) is dict:
        return {key: _normalize_dependency(item, field=key) for key, item in value.items()}
    if type(value) is list:
        rows = [_normalize_dependency(item) for item in value]
        if field in {"evidence", "values"}:
            rows.sort(key=canonical_json_bytes)
        return rows
    return value


def _dependency_records(profile: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    rows = [
        (
            dependency["dependency_id"],
            canonical_json_bytes(_normalize_dependency(dependency)).decode("utf-8"),
        )
        for dependency in profile.get("dependencies", [])
    ]
    rows.sort(key=lambda item: _utf16(item[0]))
    return tuple(rows)


def _participating_lock_ids(bundle: ValidatedSemanticBundle) -> set[str]:
    ids: set[str] = set()
    for mapping in dict(bundle.indexes.mappings).values():
        for projection in mapping.get("projections", []):
            ids.add(projection["ontology_lock"])
        for candidate in mapping.get("ambiguous_candidates", []):
            ids.add(candidate["ontology_lock"])
    ontology_bundle = bundle.bundle.ontology_bundle
    if ontology_bundle is not None:
        for lock in ontology_bundle.data.get("ontology_locks", []):
            if type(lock) is dict and type(lock.get("lock_id")) is str:
                ids.add(lock["lock_id"])
        for bridge in ontology_bundle.data.get("bridge_locks", []):
            if type(bridge) is dict:
                for field in ("source_lock_id", "target_lock_id"):
                    if type(bridge.get(field)) is str:
                        ids.add(bridge[field])
    return ids


def _bundle_context(
    bundle: ValidatedSemanticBundle,
) -> tuple[str, ProfileReleaseKey, BundleVariantKey, ProfileReleaseSignature, BundleVariantIR]:
    mappings = dict(bundle.indexes.mappings)
    corpus_ids = {mapping["corpus_id"] for mapping in mappings.values()}
    if len(corpus_ids) != 1:
        raise SemanticIRError(
            SemanticIRProblem(
                category="invalid_bundle_scope",
                message="validated bundle must contain exactly one corpus_id",
            )
        )
    corpus_id = next(iter(corpus_ids))
    profile = bundle.bundle.profile.data
    mapping_root = bundle.bundle.mappings.data
    release_key = ProfileReleaseKey(corpus_id, profile["profile_id"], profile["profile_version"])
    variant = BundleVariantKey(
        corpus_id=corpus_id,
        authored_profile_id=profile["profile_id"],
        profile_version=profile["profile_version"],
        expected_parent_manifest_digest=bundle.expected_parent_manifest_digest,
        ontology_bundle_digest=bundle.ontology_bundle_digest,
    )

    locks = dict(bundle.indexes.ontology_locks)
    lock_fingerprints = tuple(
        sorted(
            (_lock(locks[lock_id]) for lock_id in _participating_lock_ids(bundle)),
            key=_lock_sort_key,
        )
    )
    mapping_digests = tuple(
        sorted(bundle.mapping_semantic_digests, key=lambda item: _utf16(item[0]))
    )
    mapping_reviews: list[tuple[str, ReviewFingerprint]] = []
    projection_reviews: list[tuple[str, str, ReviewFingerprint]] = []
    for mapping_id, mapping in sorted(mappings.items(), key=lambda item: _utf16(item[0])):
        mapping_reviews.append((mapping_id, _review(mapping["review"])))
        for projection in sorted(
            mapping.get("projections", []), key=lambda item: _utf16(item["projection_id"])
        ):
            projection_reviews.append(
                (mapping_id, projection["projection_id"], _review(projection["review"]))
            )

    signature = ProfileReleaseSignature(
        profile_schema_version=profile["schema_version"],
        profile_catalog_version=profile["profile_catalog_version"],
        dependency_contract_version=profile["dependency_contract_version"],
        mapping_schema_version=mapping_root["schema_version"],
        minimum_tfont_runtime=profile["minimum_tfont_runtime"],
        profiles=_strings(profile.get("profiles", [])),
        capabilities=_strings(profile.get("capabilities", [])),
        dependency_records=_dependency_records(profile),
        mapping_digests=mapping_digests,
        ontology_bundle_digest=bundle.ontology_bundle_digest,
        ontology_locks=lock_fingerprints,
        mapping_semantic_algorithm=MAPPING_SEMANTIC_ALGORITHM_V2,
        projection_semantic_algorithm=PROJECTION_SEMANTIC_ALGORITHM,
        mapping_reviews=tuple(mapping_reviews),
        projection_reviews=tuple(projection_reviews),
        parent_compatibility=profile.get("parent_compatibility", "exact-only"),
    )
    variant_ir = BundleVariantIR(
        key=variant,
        release_key=release_key,
        release_signature=signature,
        profile_schema_version=profile["schema_version"],
        profile_catalog_version=profile["profile_catalog_version"],
        dependency_contract_version=profile["dependency_contract_version"],
        mapping_schema_version=mapping_root["schema_version"],
        mapping_semantic_algorithm=MAPPING_SEMANTIC_ALGORITHM_V2,
        projection_semantic_algorithm=PROJECTION_SEMANTIC_ALGORITHM,
        mapping_digests=mapping_digests,
        ontology_locks=lock_fingerprints,
    )
    return corpus_id, release_key, variant, signature, variant_ir


def _candidate_ir(
    candidate: dict[str, Any],
    *,
    variant: BundleVariantKey,
    corpus_id: str,
    mapping_id: str,
    locks: dict[str, dict[str, Any]],
) -> CandidateIR:
    return CandidateIR(
        variant=variant,
        corpus_id=corpus_id,
        mapping_id=mapping_id,
        candidate_id=candidate["candidate_id"],
        target=candidate["target"],
        reference_kind=candidate["reference_kind"],
        query_role=candidate["query_role"],
        formal_kind=candidate["formal_kind"],
        semantic_role=candidate["semantic_role"],
        profile_id=candidate["profile_id"],
        capability_id=candidate["capability_id"],
        assessment_candidate=candidate["assessment_candidate"],
        ontology_lock=_lock(locks[candidate["ontology_lock"]]),
        ontology_declaration_evidence=_ontology_declaration(
            candidate.get("ontology_declaration_evidence")
        ),
        evidence=_evidence(candidate.get("evidence", [])),
    )


def _external_reference_ir(
    reference: dict[str, Any],
    *,
    variant: BundleVariantKey,
    corpus_id: str,
    mapping_id: str,
) -> ExternalReferenceIR:
    binding = reference.get("native_binding")
    return ExternalReferenceIR(
        variant=variant,
        corpus_id=corpus_id,
        mapping_id=mapping_id,
        reference_id=reference["reference_id"],
        reference_kind=reference["reference_kind"],
        query_role=reference["query_role"],
        external=reference["external"],
        authority_system=reference.get("authority_system"),
        issuer_or_namespace=reference.get("issuer_or_namespace"),
        identity_strength=reference.get("identity_strength"),
        native_binding_identity=native_binding_identity(binding) if type(binding) is dict else None,
        native_binding=_native_binding(binding) if type(binding) is dict else None,
        publication_relation=reference.get("publication_relation"),
        evidence=_evidence(reference.get("evidence", [])),
    )


def _target_ir(
    projection: dict[str, Any],
    *,
    variant: BundleVariantKey,
    corpus_id: str,
    mapping: dict[str, Any],
    lock: dict[str, Any],
) -> TargetBindingIR:
    execution = projection["native_execution_binding"]
    return TargetBindingIR(
        variant=variant,
        corpus_id=corpus_id,
        mapping_id=mapping["mapping_id"],
        projection_id=projection["projection_id"],
        target=projection["target"],
        reference_kind=projection["reference_kind"],
        query_role=projection["query_role"],
        formal_kind=projection["formal_kind"],
        semantic_role=projection["semantic_role"],
        profile_id=projection["profile_id"],
        capability_id=projection["capability_id"],
        assessment=projection["assessment"],
        native_execution_binding_identity=native_binding_identity(execution),
        native_execution_binding=_native_binding(execution),
        native_dependencies=_strings(mapping.get("native_dependencies", [])),
        mapping_semantic_digest=mapping["mapping_semantic_digest"],
        projection_semantic_digest=projection["projection_semantic_digest"],
        mapping_review=_review(mapping["review"]),
        projection_review=_review(projection["review"]),
        ontology_lock=_lock(lock),
        ontology_bundle_digest=variant.ontology_bundle_digest,
        ontology_bundle_requirement=_ontology_bundle_requirement(
            projection.get("ontology_bundle_requirement")
        ),
        ontology_declaration_evidence=_ontology_declaration(
            projection.get("ontology_declaration_evidence")
        ),
        publication_relation=projection.get("publication_relation"),
        approximation=_approximation(projection.get("approximation")),
        mapping_evidence=_evidence(mapping.get("evidence", [])),
        projection_evidence=_evidence(projection.get("evidence", [])),
    )


def compile_semantic_ir(bundles: Iterable[ValidatedSemanticBundle]) -> CompiledSemanticIR:
    try:
        materialized = tuple(bundles)
    except TypeError as exc:
        raise TypeError("bundles must be iterable") from exc
    if not materialized:
        raise SemanticIRError(
            SemanticIRProblem(
                category="invalid_bundle_scope",
                message="semantic IR compilation requires at least one validated bundle",
            )
        )
    for bundle in materialized:
        if type(bundle) is not ValidatedSemanticBundle:
            raise TypeError("compiler inputs must be exact ValidatedSemanticBundle objects")

    contexts: list[
        tuple[
            ValidatedSemanticBundle,
            str,
            ProfileReleaseKey,
            BundleVariantKey,
            ProfileReleaseSignature,
            BundleVariantIR,
        ]
    ] = []
    seen_variants: set[BundleVariantKey] = set()
    release_signatures: dict[ProfileReleaseKey, ProfileReleaseSignature] = {}
    for bundle in materialized:
        corpus_id, release_key, variant, signature, variant_ir = _bundle_context(bundle)
        if variant in seen_variants:
            raise SemanticIRError(
                SemanticIRProblem(
                    category="duplicate_bundle_variant",
                    message="duplicate exact bundle variant",
                    corpus_id=corpus_id,
                )
            )
        seen_variants.add(variant)
        existing = release_signatures.get(release_key)
        if existing is not None and existing != signature:
            raise SemanticIRError(
                SemanticIRProblem(
                    category="profile_release_conflict",
                    message="profile release has conflicting semantic or review authority",
                    corpus_id=corpus_id,
                )
            )
        release_signatures[release_key] = signature
        contexts.append((bundle, corpus_id, release_key, variant, signature, variant_ir))
    contexts.sort(key=lambda item: _variant_sort_key(item[3]))

    native_groups: dict[NativeKey, list[NativeRecordIR]] = {}
    semantic_groups: dict[SemanticKey, list[TargetBindingIR]] = {}
    authority_groups: dict[AuthorityKey, list[TargetBindingIR]] = {}
    identity_groups: dict[IdentityKey, list[ExternalReferenceIR]] = {}
    identifier_groups: dict[IdentifierKey, list[ExternalReferenceIR]] = {}
    capability_acc: dict[CapabilityKey, dict[str, Any]] = {}

    for bundle, corpus_id, _release_key, variant, _signature, _variant_ir in contexts:
        mappings = dict(bundle.indexes.mappings)
        locks = dict(bundle.indexes.ontology_locks)
        for mapping_id, mapping in sorted(mappings.items(), key=lambda item: _utf16(item[0])):
            mapping_review = _review(mapping["review"])
            mapping_reviewed = mapping_review.status == "reviewed"
            binding = mapping["native_binding"]
            binding_identity = native_binding_identity(binding)
            candidates = tuple(
                _candidate_ir(
                    candidate,
                    variant=variant,
                    corpus_id=corpus_id,
                    mapping_id=mapping_id,
                    locks=locks,
                )
                for candidate in sorted(
                    mapping.get("ambiguous_candidates", []),
                    key=lambda item: _utf16(item["candidate_id"]),
                )
            )
            references = tuple(
                _external_reference_ir(
                    reference,
                    variant=variant,
                    corpus_id=corpus_id,
                    mapping_id=mapping_id,
                )
                for reference in sorted(
                    mapping.get("external_references", []),
                    key=lambda item: _utf16(item["reference_id"]),
                )
            )
            native_record = NativeRecordIR(
                variant=variant,
                corpus_id=corpus_id,
                mapping_id=mapping_id,
                native_binding_identity=binding_identity,
                native_binding=_native_binding(binding),
                native_dependencies=_strings(mapping.get("native_dependencies", [])),
                profiles=_strings(mapping.get("profiles", [])),
                capabilities=_strings(mapping.get("capabilities", [])),
                native_state=mapping["native_state"],
                mapping_semantic_digest=mapping["mapping_semantic_digest"],
                mapping_review=mapping_review,
                evidence=_evidence(mapping.get("evidence", [])),
                projection_ids=_strings(
                    [item["projection_id"] for item in mapping.get("projections", [])]
                ),
                candidate_ids=_strings(
                    [item["candidate_id"] for item in mapping.get("ambiguous_candidates", [])]
                ),
                reference_ids=_strings(
                    [item["reference_id"] for item in mapping.get("external_references", [])]
                ),
                candidates=candidates,
                external_references=references,
            )
            native_groups.setdefault(NativeKey(corpus_id, binding_identity), []).append(native_record)

            profile_capabilities = [
                (profile_id, capability_id)
                for profile_id in mapping.get("profiles", [])
                for capability_id in mapping.get("capabilities", [])
                if capability_id.startswith(profile_id + ".")
            ]
            for profile_id, capability_id in profile_capabilities:
                cap_key = CapabilityKey(variant, profile_id, capability_id)
                acc = capability_acc.setdefault(
                    cap_key,
                    {
                        "reviewed_native_support": 0,
                        "shared_projections": 0,
                        "exact": 0,
                        "close": 0,
                        "broader": 0,
                        "narrower": 0,
                        "related": 0,
                        "ambiguous": 0,
                        "native_only": 0,
                        "unsupported": 0,
                        "mapping_ids": set(),
                    },
                )
                if mapping_reviewed:
                    acc["mapping_ids"].add(mapping_id)
                    state = mapping["native_state"]
                    if state == "unsupported":
                        acc["unsupported"] += 1
                    else:
                        acc["reviewed_native_support"] += 1
                        if state == "ambiguous":
                            acc["ambiguous"] += 1
                        elif state == "native-only":
                            acc["native_only"] += 1

            for projection in mapping.get("projections", []):
                projection_review = _review(projection["review"])
                if not (mapping_reviewed and projection_review.status == "reviewed"):
                    continue
                target_ir = _target_ir(
                    projection,
                    variant=variant,
                    corpus_id=corpus_id,
                    mapping=mapping,
                    lock=locks[projection["ontology_lock"]],
                )
                if (
                    projection["reference_kind"] == "semantic-pivot"
                    and projection["query_role"] == "semantic-constraint"
                ):
                    semantic_groups.setdefault(
                        SemanticKey(
                            projection["profile_id"],
                            projection["capability_id"],
                            projection["target"],
                            projection["formal_kind"],
                            projection["semantic_role"],
                        ),
                        [],
                    ).append(target_ir)
                elif (
                    projection["reference_kind"] == "authority-value"
                    and projection["query_role"] == "authority-value-filter"
                ):
                    lock = locks[projection["ontology_lock"]]
                    authority_groups.setdefault(
                        AuthorityKey(
                            lock["ontology_id"],
                            projection["target"],
                            projection["formal_kind"],
                            projection["semantic_role"],
                        ),
                        [],
                    ).append(target_ir)

                cap_key = CapabilityKey(
                    variant, projection["profile_id"], projection["capability_id"]
                )
                acc = capability_acc.get(cap_key)
                if acc is not None:
                    acc["shared_projections"] += 1
                    acc[projection["assessment"]] += 1

            if mapping_reviewed:
                for reference in references:
                    if reference.reference_kind == "entity-identity":
                        identity_groups.setdefault(
                            IdentityKey(
                                reference.authority_system,  # type: ignore[arg-type]
                                reference.external,
                                reference.identity_strength,  # type: ignore[arg-type]
                            ),
                            [],
                        ).append(reference)
                    elif reference.reference_kind == "catalogue-identifier":
                        identifier_groups.setdefault(
                            IdentifierKey(
                                reference.issuer_or_namespace,  # type: ignore[arg-type]
                                reference.external,
                            ),
                            [],
                        ).append(reference)

    native_index = tuple(
        (key, tuple(sorted(rows, key=_native_record_sort)))
        for key, rows in sorted(native_groups.items(), key=lambda item: _native_key_sort(item[0]))
    )
    semantic_index = tuple(
        (key, tuple(sorted(rows, key=_binding_sort)))
        for key, rows in sorted(
            semantic_groups.items(), key=lambda item: _semantic_key_sort(item[0])
        )
    )
    authority_index = tuple(
        (key, tuple(sorted(rows, key=_binding_sort)))
        for key, rows in sorted(
            authority_groups.items(), key=lambda item: _authority_key_sort(item[0])
        )
    )
    identity_index = tuple(
        (key, tuple(sorted(rows, key=_reference_sort)))
        for key, rows in sorted(
            identity_groups.items(), key=lambda item: _identity_key_sort(item[0])
        )
    )
    identifier_index = tuple(
        (key, tuple(sorted(rows, key=_reference_sort)))
        for key, rows in sorted(
            identifier_groups.items(), key=lambda item: _identifier_key_sort(item[0])
        )
    )

    capability_facts_rows: list[tuple[CapabilityKey, CapabilityFactsIR]] = []
    for key, acc in capability_acc.items():
        capability_facts_rows.append(
            (
                key,
                CapabilityFactsIR(
                    reviewed_native_support=acc["reviewed_native_support"],
                    shared_projections=acc["shared_projections"],
                    exact=acc["exact"],
                    close=acc["close"],
                    broader=acc["broader"],
                    narrower=acc["narrower"],
                    related=acc["related"],
                    ambiguous=acc["ambiguous"],
                    native_only=acc["native_only"],
                    unsupported=acc["unsupported"],
                    mapping_ids=tuple(sorted(acc["mapping_ids"], key=_utf16)),
                ),
            )
        )
    capability_facts_rows.sort(key=lambda item: _capability_key_sort(item[0]))

    return CompiledSemanticIR(
        variants=tuple(item[5] for item in contexts),
        native_index=native_index,
        semantic_index=semantic_index,
        authority_index=authority_index,
        identity_index=identity_index,
        identifier_index=identifier_index,
        capability_facts=tuple(capability_facts_rows),
    )
