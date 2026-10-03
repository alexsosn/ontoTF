from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .parent_identity import parent_manifest_digest
from .semantic_bundle_validation import validate_bundle_source_closure
from .semantic_child_validation import (
    check_evidence_bindings,
    validate_child_evidence,
    validate_native_semantics,
    validate_projection_reviews,
)
from .semantic_digest_v2 import mapping_semantic_digest_v2
from .semantic_policy_validation import validate_mapping_policies
from .semantic_vocabulary import (
    CANDIDATE_ASSESSMENTS,
    CAPABILITY_IDS,
    FORMAL_KINDS,
    NATIVE_STATES,
    PROFILE_IDS,
    PROJECTION_ASSESSMENTS,
    SEMANTIC_ROLES,
    TARGET_ROUTING,
)

_PROFILE_SCHEMA_VERSION = 2
_MAPPING_SCHEMA_VERSION = 2
_DEPENDENCY_CONTRACT_VERSION = 1
_PROFILE_CATALOG_VERSION = 1

_PUBLIC_CATEGORY_ALIASES = {
    "semantic_digest_mismatch": "stale_semantic_digest",
    "review_digest_mismatch": "stale_review_binding",
}


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
    ontology_locks: tuple[SemanticArtifact, ...] = ()
    evidences: tuple[SemanticArtifact, ...] = ()
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


class SemanticValidationError(ValueError):
    def __init__(self, problem: SemanticValidationProblem):
        self.problem = problem
        super().__init__(f"{problem.category}: {problem.message}")


@dataclass(frozen=True)
class SemanticIndexes:
    components: tuple[tuple[str, dict[str, Any]], ...] = ()
    dependencies: tuple[tuple[str, dict[str, Any]], ...] = ()
    mappings: tuple[tuple[str, dict[str, Any]], ...] = ()
    projections: tuple[tuple[str, dict[str, Any]], ...] = ()
    candidates: tuple[tuple[str, dict[str, Any]], ...] = ()
    references: tuple[tuple[str, dict[str, Any]], ...] = ()
    ontology_locks: tuple[tuple[str, dict[str, Any]], ...] = ()
    evidences: tuple[tuple[str, dict[str, Any]], ...] = ()


@dataclass(frozen=True)
class ValidatedSemanticBundle:
    bundle: SemanticSourceBundle
    expected_parent_manifest_digest: str
    mapping_semantic_digests: tuple[tuple[str, str], ...]
    ontology_bundle_digest: str | None
    indexes: SemanticIndexes


def _fail(
    artifact: SemanticArtifact,
    category: str,
    message: str,
    *,
    path: tuple[str | int, ...] = (),
    related_id: str | None = None,
) -> None:
    public_category = _PUBLIC_CATEGORY_ALIASES.get(category, category)
    raise SemanticValidationError(
        SemanticValidationProblem(
            category=public_category,
            message=message,
            artifact_kind=artifact.kind,
            source_name=artifact.source_name,
            path=path,
            related_id=related_id,
        )
    )


def _utf16_key(value: str) -> bytes:
    return value.encode("utf-16be")


def _sorted_strings(value: Any) -> list[str]:
    if type(value) is not list:
        return []
    result = [item for item in value if type(item) is str]
    result.sort(key=_utf16_key)
    return result


def _sorted_children(value: Any, id_field: str) -> list[dict[str, Any]]:
    if type(value) is not list:
        return []
    rows = [row for row in value if type(row) is dict]
    rows.sort(
        key=lambda row: _utf16_key(row.get(id_field))
        if type(row.get(id_field)) is str
        else b""
    )
    return rows


def _validate_contract_versions(bundle: SemanticSourceBundle) -> None:
    checks = (
        (bundle.profile, ("schema_version",), bundle.profile.data.get("schema_version"), _PROFILE_SCHEMA_VERSION, "profile schema_version"),
        (bundle.profile, ("dependency_contract_version",), bundle.profile.data.get("dependency_contract_version"), _DEPENDENCY_CONTRACT_VERSION, "dependency contract version"),
        (bundle.profile, ("profile_catalog_version",), bundle.profile.data.get("profile_catalog_version"), _PROFILE_CATALOG_VERSION, "profile catalog version"),
        (bundle.mappings, ("schema_version",), bundle.mappings.data.get("schema_version"), _MAPPING_SCHEMA_VERSION, "mapping schema_version"),
    )
    for artifact, path, value, expected, label in checks:
        if type(value) is not int or value != expected:
            _fail(
                artifact,
                "unsupported_contract_version",
                f"{label} must be exact integer {expected}",
                path=path,
            )

    if bundle.profile_catalog is not None:
        _fail(
            bundle.profile_catalog,
            "unsupported_contract_version",
            "standalone profile_catalog artifacts are not supported by I-004 v1; use profile_catalog_version plus inline controlled declarations",
            path=("profile_catalog",),
        )
    if bundle.reference_catalog is not None:
        _fail(
            bundle.reference_catalog,
            "unsupported_contract_version",
            "standalone reference_catalog artifacts are not supported by I-004 v1; reference vocabulary is frozen by the v1 contract",
            path=("reference_catalog",),
        )


def _sequence(value: Any, *, artifact: SemanticArtifact, path: tuple[str | int, ...]) -> list[Any]:
    if type(value) is not list:
        _fail(artifact, "missing_reference", "expected list", path=path)
    return value


def _index_records(
    records: list[dict[str, Any]],
    id_field: str,
    *,
    artifact: SemanticArtifact,
    path_prefix: tuple[str | int, ...],
) -> tuple[tuple[str, dict[str, Any]], ...]:
    seen: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if type(record) is not dict:
            _fail(artifact, "missing_reference", "record must be an object", path=path_prefix + (index,))
        identifier = record.get(id_field)
        if type(identifier) is not str or not identifier:
            _fail(artifact, "missing_reference", f"{id_field} must be a non-empty string", path=path_prefix + (index, id_field))
        if identifier in seen:
            _fail(artifact, "duplicate_id", f"duplicate {id_field}: {identifier}", path=path_prefix + (index, id_field), related_id=identifier)
        seen[identifier] = record
    return tuple(sorted(seen.items(), key=lambda item: _utf16_key(item[0])))


def _index_artifacts(
    artifacts: tuple[SemanticArtifact, ...],
    id_field: str,
) -> tuple[tuple[str, dict[str, Any]], ...]:
    seen: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        record = artifact.data
        if type(record) is not dict:
            _fail(artifact, "missing_reference", "record must be an object")
        identifier = record.get(id_field)
        if type(identifier) is not str or not identifier:
            _fail(artifact, "missing_reference", f"{id_field} must be a non-empty string", path=(id_field,))
        if identifier in seen:
            _fail(
                artifact,
                "duplicate_id",
                f"duplicate {id_field}: {identifier}",
                path=(id_field,),
                related_id=identifier,
            )
        seen[identifier] = record
    return tuple(sorted(seen.items(), key=lambda item: _utf16_key(item[0])))


def _build_indexes(bundle: SemanticSourceBundle) -> SemanticIndexes:
    parent = bundle.expected_parent_manifest
    profile = bundle.profile
    mappings_artifact = bundle.mappings

    components = _index_records(
        _sequence(parent.data.get("components"), artifact=parent, path=("components",)),
        "component_id",
        artifact=parent,
        path_prefix=("components",),
    )
    dependencies = _index_records(
        _sequence(profile.data.get("dependencies"), artifact=profile, path=("dependencies",)),
        "dependency_id",
        artifact=profile,
        path_prefix=("dependencies",),
    )
    mappings = _index_records(
        _sequence(mappings_artifact.data.get("mappings"), artifact=mappings_artifact, path=("mappings",)),
        "mapping_id",
        artifact=mappings_artifact,
        path_prefix=("mappings",),
    )

    projections_raw: list[dict[str, Any]] = []
    candidates_raw: list[dict[str, Any]] = []
    references_raw: list[dict[str, Any]] = []
    for _, mapping in mappings:
        projections_raw.extend(mapping.get("projections", []))
        candidates_raw.extend(mapping.get("ambiguous_candidates", []))
        references_raw.extend(mapping.get("external_references", []))

    projections = _index_records(projections_raw, "projection_id", artifact=mappings_artifact, path_prefix=("projections",)) if projections_raw else ()
    candidates = _index_records(candidates_raw, "candidate_id", artifact=mappings_artifact, path_prefix=("ambiguous_candidates",)) if candidates_raw else ()
    references = _index_records(references_raw, "reference_id", artifact=mappings_artifact, path_prefix=("external_references",)) if references_raw else ()

    ontology_locks = _index_artifacts(bundle.ontology_locks, "lock_id") if bundle.ontology_locks else ()
    evidences = _index_artifacts(bundle.evidences, "evidence_id") if bundle.evidences else ()

    return SemanticIndexes(
        components=components,
        dependencies=dependencies,
        mappings=mappings,
        projections=projections,
        candidates=candidates,
        references=references,
        ontology_locks=ontology_locks,
        evidences=evidences,
    )


def _require_vocab(value: Any, allowed: frozenset[str], *, artifact: SemanticArtifact, path: tuple[str | int, ...], label: str) -> str:
    if type(value) is not str or value not in allowed:
        _fail(artifact, "unknown_vocabulary", f"unknown {label}: {value!r}", path=path)
    return value


def _validate_component_authority(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> None:
    profile = bundle.profile
    component_ids = set(dict(indexes.components))
    required = profile.data.get("required_components")
    if type(required) is not list:
        _fail(profile, "component_authority", "required_components must be a list", path=("required_components",))
    required_ids = set(required)
    for component_id in _sorted_strings(required):
        if component_id not in component_ids:
            _fail(profile, "component_authority", f"required component is not present in expected parent: {component_id!r}", path=("required_components", component_id), related_id=component_id)
    for dependency_id, dependency in indexes.dependencies:
        component_id = dependency.get("component_id")
        if component_id not in required_ids or component_id not in component_ids:
            _fail(profile, "component_authority", f"dependency {dependency_id} uses unauthorized component {component_id!r}", path=("dependencies", dependency_id, "component_id"), related_id=component_id if type(component_id) is str else None)


def _validate_dependency_closure_and_mapping_scope(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> None:
    artifact = bundle.mappings
    dependencies = dict(indexes.dependencies)
    for mapping_id, mapping in indexes.mappings:
        dependency_ids = mapping.get("native_dependencies")
        if type(dependency_ids) is not list:
            _fail(artifact, "missing_reference", "native_dependencies must be a list", path=("mappings", mapping_id, "native_dependencies"))
        ordered_dependency_ids = _sorted_strings(dependency_ids)
        for dependency_id in ordered_dependency_ids:
            if dependency_id not in dependencies:
                _fail(artifact, "missing_reference", f"missing dependency: {dependency_id!r}", path=("mappings", mapping_id, "native_dependencies", dependency_id), related_id=dependency_id)

        authorized_components = {dependencies[dependency_id].get("component_id") for dependency_id in ordered_dependency_ids if dependency_id in dependencies}
        binding_rows: list[tuple[tuple[str | int, ...], Any, str | None]] = [
            (("mappings", mapping_id, "native_binding", "component_id"), mapping.get("native_binding", {}).get("component_id") if type(mapping.get("native_binding")) is dict else None, mapping_id)
        ]
        for projection in _sorted_children(mapping.get("projections", []), "projection_id"):
            projection_id = projection.get("projection_id")
            execution = projection.get("native_execution_binding")
            binding_rows.append((("mappings", mapping_id, "projections", projection_id, "native_execution_binding", "component_id"), execution.get("component_id") if type(execution) is dict else None, projection_id if type(projection_id) is str else None))
        for reference in _sorted_children(mapping.get("external_references", []), "reference_id"):
            reference_id = reference.get("reference_id")
            native = reference.get("native_binding")
            if native is not None:
                binding_rows.append((("mappings", mapping_id, "external_references", reference_id, "native_binding", "component_id"), native.get("component_id") if type(native) is dict else None, reference_id if type(reference_id) is str else None))
        for path, component_id, related_id in binding_rows:
            if component_id is not None and component_id not in authorized_components:
                _fail(artifact, "component_authority", f"native binding component is not authorized by mapping dependencies: {component_id!r}", path=path, related_id=related_id or (component_id if type(component_id) is str else None))


def _validate_membership_dependency_authority(
    bundle: SemanticSourceBundle,
    indexes: SemanticIndexes,
) -> None:
    artifact = bundle.mappings
    dependencies = dict(indexes.dependencies)
    for mapping_id, mapping in indexes.mappings:
        dependency_ids = _sorted_strings(mapping.get("native_dependencies", []))
        dependency_rows = [
            dependencies[dependency_id]
            for dependency_id in dependency_ids
            if dependency_id in dependencies
        ]
        binding_rows: list[tuple[tuple[str | int, ...], Any, str | None]] = [
            (
                ("mappings", mapping_id, "native_binding"),
                mapping.get("native_binding"),
                mapping_id,
            )
        ]
        for projection in _sorted_children(mapping.get("projections", []), "projection_id"):
            projection_id = projection.get("projection_id")
            binding_rows.append(
                (
                    (
                        "mappings", mapping_id, "projections", projection_id,
                        "native_execution_binding",
                    ),
                    projection.get("native_execution_binding"),
                    projection_id if type(projection_id) is str else None,
                )
            )
        for reference in _sorted_children(mapping.get("external_references", []), "reference_id"):
            reference_id = reference.get("reference_id")
            native = reference.get("native_binding")
            if native is not None:
                binding_rows.append(
                    (
                        (
                            "mappings", mapping_id, "external_references", reference_id,
                            "native_binding",
                        ),
                        native,
                        reference_id if type(reference_id) is str else None,
                    )
                )

        for binding_path, binding, related_id in binding_rows:
            if type(binding) is not dict or binding.get("execution_shape") != "membership":
                continue
            component_id = binding.get("component_id")
            node_type = binding.get("node_type")
            authorized = any(
                dependency.get("kind") == "node-type-present"
                and dependency.get("component_id") == component_id
                and type(dependency.get("assertion")) is dict
                and dependency["assertion"].get("node_type") == node_type
                for dependency in dependency_rows
            )
            if not authorized:
                _fail(
                    artifact,
                    "dependency_authority",
                    "membership binding requires a matching reviewed node-type-present dependency",
                    path=binding_path,
                    related_id=related_id,
                )


def _validate_edge_path_dependency_authority(
    bundle: SemanticSourceBundle,
    indexes: SemanticIndexes,
) -> None:
    artifact = bundle.mappings
    dependencies = dict(indexes.dependencies)
    for mapping_id, mapping in indexes.mappings:
        dependency_ids = _sorted_strings(mapping.get("native_dependencies", []))
        dependency_rows = [
            dependencies[dependency_id]
            for dependency_id in dependency_ids
            if dependency_id in dependencies
        ]
        binding_rows: list[tuple[tuple[str | int, ...], Any, str | None]] = [
            (
                ("mappings", mapping_id, "native_binding"),
                mapping.get("native_binding"),
                mapping_id,
            )
        ]
        for projection in _sorted_children(mapping.get("projections", []), "projection_id"):
            projection_id = projection.get("projection_id")
            binding_rows.append(
                (
                    (
                        "mappings", mapping_id, "projections", projection_id,
                        "native_execution_binding",
                    ),
                    projection.get("native_execution_binding"),
                    projection_id if type(projection_id) is str else None,
                )
            )
        for reference in _sorted_children(mapping.get("external_references", []), "reference_id"):
            reference_id = reference.get("reference_id")
            native = reference.get("native_binding")
            if native is not None:
                binding_rows.append(
                    (
                        (
                            "mappings", mapping_id, "external_references", reference_id,
                            "native_binding",
                        ),
                        native,
                        reference_id if type(reference_id) is str else None,
                    )
                )

        for binding_path, binding, related_id in binding_rows:
            if type(binding) is not dict or binding.get("execution_shape") != "edge-path":
                continue
            component_id = binding.get("component_id")
            start_node_type = binding.get("node_type")
            steps = binding.get("steps")
            if type(steps) is not list or not steps:
                _fail(
                    artifact,
                    "dependency_authority",
                    "edge-path binding requires a non-empty reviewed step sequence",
                    path=binding_path,
                    related_id=related_id,
                )

            required_node_types = {start_node_type}
            required_node_types.update(
                step.get("result_node_type")
                for step in steps
                if type(step) is dict
            )
            for node_type in sorted(
                required_node_types,
                key=lambda value: _utf16_key(value) if type(value) is str else b"",
            ):
                authorized = any(
                    dependency.get("kind") == "node-type-present"
                    and dependency.get("component_id") == component_id
                    and type(dependency.get("assertion")) is dict
                    and dependency["assertion"].get("node_type") == node_type
                    for dependency in dependency_rows
                )
                if not authorized:
                    _fail(
                        artifact,
                        "dependency_authority",
                        "edge-path binding requires matching reviewed node-type-present dependencies for every traversal domain",
                        path=binding_path,
                        related_id=related_id,
                    )

            projected_steps = [
                {
                    "edge": step.get("edge"),
                    "direction": step.get("direction"),
                }
                for step in steps
                if type(step) is dict
            ]
            path_authorized = any(
                dependency.get("kind") == "path-present"
                and dependency.get("component_id") == component_id
                and type(dependency.get("assertion")) is dict
                and dependency["assertion"].get("steps") == projected_steps
                for dependency in dependency_rows
            )
            if not path_authorized:
                _fail(
                    artifact,
                    "dependency_authority",
                    "edge-path binding requires a matching reviewed ordered path-present dependency",
                    path=binding_path,
                    related_id=related_id,
                )


def _validate_vocabulary(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> None:
    artifact = bundle.mappings
    profile_artifact = bundle.profile

    declared_profiles_value = profile_artifact.data.get("profiles")
    if type(declared_profiles_value) is not list or not declared_profiles_value:
        _fail(profile_artifact, "unknown_vocabulary", "profile catalog declarations require a non-empty profiles list", path=("profiles",))
    declared_capabilities_value = profile_artifact.data.get("capabilities")
    if type(declared_capabilities_value) is not list or not declared_capabilities_value:
        _fail(profile_artifact, "unknown_vocabulary", "profile catalog declarations require a non-empty capabilities list", path=("capabilities",))

    declared_profiles: set[str] = set()
    for profile_id in _sorted_strings(declared_profiles_value):
        declared_profiles.add(_require_vocab(profile_id, PROFILE_IDS, artifact=profile_artifact, path=("profiles", profile_id), label="profile"))

    declared_capabilities: set[str] = set()
    for capability_id in _sorted_strings(declared_capabilities_value):
        capability = _require_vocab(capability_id, CAPABILITY_IDS, artifact=profile_artifact, path=("capabilities", capability_id), label="capability")
        capability_profile = capability.split(".", 1)[0]
        if capability_profile not in declared_profiles:
            _fail(profile_artifact, "unknown_vocabulary", f"capability {capability!r} is not scoped by a declared profile", path=("capabilities", capability), related_id=capability)
        declared_capabilities.add(capability)

    for mapping_id, mapping in indexes.mappings:
        mapping_profiles: set[str] = set()
        for profile_id in _sorted_strings(mapping.get("profiles", [])):
            profile = _require_vocab(profile_id, PROFILE_IDS, artifact=artifact, path=("mappings", mapping_id, "profiles", profile_id), label="profile")
            if profile not in declared_profiles:
                _fail(artifact, "unknown_vocabulary", f"mapping profile is not declared by profile artifact: {profile!r}", path=("mappings", mapping_id, "profiles", profile), related_id=profile)
            mapping_profiles.add(profile)

        mapping_capabilities: set[str] = set()
        for capability_id in _sorted_strings(mapping.get("capabilities", [])):
            capability = _require_vocab(capability_id, CAPABILITY_IDS, artifact=artifact, path=("mappings", mapping_id, "capabilities", capability_id), label="capability")
            if capability not in declared_capabilities:
                _fail(artifact, "unknown_vocabulary", f"mapping capability is not declared by profile artifact: {capability!r}", path=("mappings", mapping_id, "capabilities", capability), related_id=capability)
            if capability.split(".", 1)[0] not in mapping_profiles:
                _fail(artifact, "unknown_vocabulary", f"mapping capability is not scoped by a mapping profile: {capability!r}", path=("mappings", mapping_id, "capabilities", capability), related_id=capability)
            mapping_capabilities.add(capability)

        for projection in _sorted_children(mapping.get("projections", []), "projection_id"):
            projection_id = projection.get("projection_id")
            prefix = ("mappings", mapping_id, "projections", projection_id)
            _require_vocab(projection.get("formal_kind"), FORMAL_KINDS, artifact=artifact, path=prefix + ("formal_kind",), label="formal kind")
            _require_vocab(projection.get("semantic_role"), SEMANTIC_ROLES, artifact=artifact, path=prefix + ("semantic_role",), label="semantic role")
            _require_vocab(projection.get("profile_id"), PROFILE_IDS, artifact=artifact, path=prefix + ("profile_id",), label="profile")
            _require_vocab(projection.get("capability_id"), CAPABILITY_IDS, artifact=artifact, path=prefix + ("capability_id",), label="capability")
            _require_vocab(projection.get("assessment"), PROJECTION_ASSESSMENTS, artifact=artifact, path=prefix + ("assessment",), label="projection assessment")
            routing = (projection.get("reference_kind"), projection.get("query_role"))
            if routing not in TARGET_ROUTING:
                _fail(artifact, "invalid_reference_routing", f"invalid target routing pair: {routing!r}", path=prefix, related_id=projection_id if type(projection_id) is str else None)


def _validate_record_states(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> None:
    artifact = bundle.mappings
    for mapping_id, mapping in indexes.mappings:
        state = mapping.get("native_state")
        projections = mapping.get("projections", [])
        candidates = mapping.get("ambiguous_candidates", [])
        references = mapping.get("external_references", [])
        if state in {"native-only", "unsupported"} and (projections or candidates):
            _fail(artifact, "invalid_record_state", f"{state} record cannot carry target projections or candidates", path=("mappings", mapping_id, "native_state"), related_id=mapping_id)
        if state == "ambiguous" and (projections or not candidates):
            _fail(artifact, "invalid_record_state", "ambiguous record requires candidates and zero approved projections", path=("mappings", mapping_id), related_id=mapping_id)
        if state == "positive":
            if candidates:
                _fail(artifact, "invalid_record_state", "positive record cannot carry unresolved ambiguous candidates", path=("mappings", mapping_id, "ambiguous_candidates"), related_id=mapping_id)
            if not projections and not references:
                _fail(artifact, "invalid_record_state", "positive record requires an approved projection or external reference", path=("mappings", mapping_id), related_id=mapping_id)


def _kind_role_allowed(formal_kind: str, semantic_role: str) -> bool:
    if formal_kind == "class":
        return semantic_role in {"entity-type", "annotation-category", "annotation-value"}
    if formal_kind == "property":
        return semantic_role in {"relation", "attribute", "annotation-category"}
    if formal_kind == "skos-concept":
        return semantic_role in {"annotation-value", "lexical-concept-identity", "authority-reference"}
    if formal_kind == "named-resource":
        return semantic_role in {"lexical-entry-identity", "lexical-form-identity", "lexical-sense-identity", "lexical-concept-identity", "authority-reference", "claim-proposition", "inference-activity"}
    return False


def _validate_declaration_role(
    row: dict[str, Any],
    *,
    artifact: SemanticArtifact,
    path: tuple[str | int, ...],
    related_id: str | None,
) -> None:
    declaration = row.get("ontology_declaration_evidence")
    if type(declaration) is not dict:
        return
    value_kind = declaration.get("value_kind")
    semantic_role = row.get("semantic_role")
    if semantic_role == "relation" and value_kind == "literal":
        _fail(
            artifact,
            "kind_role_conflict",
            "relation role conflicts with explicit literal-valued ontology declaration",
            path=path + ("ontology_declaration_evidence", "value_kind"),
            related_id=related_id,
        )
    if semantic_role == "attribute" and value_kind == "resource":
        _fail(
            artifact,
            "kind_role_conflict",
            "attribute role conflicts with explicit resource-valued ontology declaration",
            path=path + ("ontology_declaration_evidence", "value_kind"),
            related_id=related_id,
        )


def _validate_projection_and_candidate_legality(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> None:
    artifact = bundle.mappings
    candidate_required = {"candidate_id", "target", "reference_kind", "query_role", "formal_kind", "semantic_role", "profile_id", "capability_id", "assessment_candidate", "ontology_lock", "evidence"}
    candidate_forbidden = {"native_execution_binding", "approximation", "publication_relation", "review", "projection_semantic_digest"}
    for mapping_id, mapping in indexes.mappings:
        mapping_profiles = set(mapping.get("profiles", []))
        mapping_capabilities = set(mapping.get("capabilities", []))
        for projection in _sorted_children(mapping.get("projections", []), "projection_id"):
            projection_id = projection.get("projection_id")
            prefix = ("mappings", mapping_id, "projections", projection_id)
            if not _kind_role_allowed(projection.get("formal_kind"), projection.get("semantic_role")):
                _fail(artifact, "kind_role_conflict", "formal kind and semantic role are incompatible", path=prefix, related_id=projection_id if type(projection_id) is str else None)
            profile_id = projection.get("profile_id")
            capability_id = projection.get("capability_id")
            if profile_id not in mapping_profiles or capability_id not in mapping_capabilities:
                _fail(artifact, "invalid_projection", "projection profile/capability must be declared by its mapping", path=prefix, related_id=projection_id if type(projection_id) is str else None)
            if type(capability_id) is not str or capability_id.split(".", 1)[0] != profile_id:
                _fail(artifact, "invalid_projection", "projection capability must be scoped by projection profile", path=prefix + ("capability_id",), related_id=projection_id if type(projection_id) is str else None)

        for candidate in _sorted_children(mapping.get("ambiguous_candidates", []), "candidate_id"):
            candidate_id = candidate.get("candidate_id")
            prefix = ("mappings", mapping_id, "ambiguous_candidates", candidate_id)
            missing = candidate_required - candidate.keys()
            illegal = candidate_forbidden & candidate.keys()
            if missing or illegal:
                _fail(artifact, "invalid_candidate", f"invalid candidate envelope; missing={sorted(missing)}, forbidden={sorted(illegal)}", path=prefix, related_id=candidate_id if type(candidate_id) is str else None)
            _require_vocab(candidate.get("formal_kind"), FORMAL_KINDS, artifact=artifact, path=prefix + ("formal_kind",), label="formal kind")
            _require_vocab(candidate.get("semantic_role"), SEMANTIC_ROLES, artifact=artifact, path=prefix + ("semantic_role",), label="semantic role")
            _require_vocab(candidate.get("profile_id"), PROFILE_IDS, artifact=artifact, path=prefix + ("profile_id",), label="profile")
            _require_vocab(candidate.get("capability_id"), CAPABILITY_IDS, artifact=artifact, path=prefix + ("capability_id",), label="capability")
            _require_vocab(candidate.get("assessment_candidate"), CANDIDATE_ASSESSMENTS, artifact=artifact, path=prefix + ("assessment_candidate",), label="candidate assessment")
            routing = (candidate.get("reference_kind"), candidate.get("query_role"))
            if routing not in TARGET_ROUTING:
                _fail(artifact, "invalid_reference_routing", f"invalid candidate routing pair: {routing!r}", path=prefix, related_id=candidate_id if type(candidate_id) is str else None)
            if not _kind_role_allowed(candidate.get("formal_kind"), candidate.get("semantic_role")):
                _fail(artifact, "kind_role_conflict", "candidate formal kind and semantic role are incompatible", path=prefix, related_id=candidate_id if type(candidate_id) is str else None)
            profile_id = candidate.get("profile_id")
            capability_id = candidate.get("capability_id")
            if profile_id not in mapping_profiles or capability_id not in mapping_capabilities:
                _fail(artifact, "invalid_candidate", "candidate profile/capability must be declared by its mapping", path=prefix, related_id=candidate_id if type(candidate_id) is str else None)
            if type(capability_id) is not str or capability_id.split(".", 1)[0] != profile_id:
                _fail(artifact, "invalid_candidate", "candidate capability must be scoped by candidate profile", path=prefix + ("capability_id",), related_id=candidate_id if type(candidate_id) is str else None)


def _validate_target_locks(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> None:
    artifact = bundle.mappings
    locks = dict(indexes.ontology_locks)
    for mapping_id, mapping in indexes.mappings:
        rows: list[tuple[str, str | None, dict[str, Any]]] = []
        rows.extend(("projections", row.get("projection_id"), row) for row in _sorted_children(mapping.get("projections", []), "projection_id"))
        rows.extend(("ambiguous_candidates", row.get("candidate_id"), row) for row in _sorted_children(mapping.get("ambiguous_candidates", []), "candidate_id"))
        rows.sort(key=lambda item: _utf16_key(item[1]) if type(item[1]) is str else b"")
        for collection, row_id, row in rows:
            prefix = ("mappings", mapping_id, collection, row_id)
            lock_id = row.get("ontology_lock")
            if type(lock_id) is not str or lock_id not in locks:
                _fail(artifact, "missing_reference", f"missing ontology lock: {lock_id!r}", path=prefix + ("ontology_lock",), related_id=lock_id if type(lock_id) is str else None)
            target = row.get("target")
            if type(target) is not str or target not in locks[lock_id].get("terms_used", []):
                _fail(artifact, "unknown_ontology_target", f"target not present in lock terms_used: {target!r}", path=prefix + ("target",), related_id=target if type(target) is str else None)

            declaration = row.get("ontology_declaration_evidence")
            if type(declaration) is dict:
                declaration_lock_id = declaration.get("ontology_lock_id")
                if declaration_lock_id != lock_id:
                    _fail(
                        artifact,
                        "bundle_closure",
                        "ontology declaration evidence lock does not match projection/candidate ontology lock",
                        path=prefix + ("ontology_declaration_evidence", "ontology_lock_id"),
                        related_id=row_id if type(row_id) is str else None,
                    )
                declaration_digest = declaration.get("ontology_lock_content_digest")
                if declaration_digest != locks[lock_id].get("content_digest"):
                    _fail(
                        artifact,
                        "bundle_closure",
                        "ontology declaration evidence digest does not match resolved ontology lock content",
                        path=prefix + ("ontology_declaration_evidence", "ontology_lock_content_digest"),
                        related_id=row_id if type(row_id) is str else None,
                    )
                _validate_declaration_role(
                    row,
                    artifact=artifact,
                    path=prefix,
                    related_id=row_id if type(row_id) is str else None,
                )


def _validate_bundle_source(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> str | None:
    artifact = bundle.ontology_bundle or (bundle.bridges[0] if bundle.bridges else bundle.mappings)

    def fail(category: str, message: str, path: tuple[str | int, ...], related_id: str | None) -> None:
        _fail(artifact, category, message, path=path, related_id=related_id)

    return validate_bundle_source_closure(
        bundle.ontology_bundle.data if bundle.ontology_bundle is not None else None,
        canonical_locks=dict(indexes.ontology_locks),
        bridge_artifacts=tuple(item.data for item in bundle.bridges),
        evidences=dict(indexes.evidences),
        fail=fail,
    )


def _validate_projection_bundle_requirements(
    bundle: SemanticSourceBundle,
    indexes: SemanticIndexes,
    ontology_bundle_digest: str | None,
) -> None:
    artifact = bundle.mappings
    active_profile_contracts = set()
    if bundle.ontology_bundle is not None:
        value = bundle.ontology_bundle.data.get("profile_contracts", [])
        if type(value) is list:
            active_profile_contracts = {item for item in value if type(item) is str}

    for mapping_id, mapping in indexes.mappings:
        for projection in _sorted_children(mapping.get("projections", []), "projection_id"):
            requirement = projection.get("ontology_bundle_requirement")
            if requirement is None:
                continue
            projection_id = projection.get("projection_id")
            prefix = ("mappings", mapping_id, "projections", projection_id, "ontology_bundle_requirement")
            if type(requirement) is not dict:
                _fail(artifact, "bundle_closure", "ontology bundle requirement must be an object", path=prefix, related_id=projection_id if type(projection_id) is str else None)
            if set(requirement) != {"bundle_digest", "required_profile_contracts"}:
                _fail(artifact, "bundle_closure", "ontology bundle requirement has incomplete or unknown fields", path=prefix, related_id=projection_id if type(projection_id) is str else None)
            if ontology_bundle_digest is None or requirement.get("bundle_digest") != ontology_bundle_digest:
                _fail(artifact, "bundle_closure", "projection ontology bundle digest does not match validated active bundle", path=prefix + ("bundle_digest",), related_id=projection_id if type(projection_id) is str else None)
            required_contracts = requirement.get("required_profile_contracts")
            if type(required_contracts) is not list or not required_contracts or any(type(item) is not str or not item for item in required_contracts):
                _fail(artifact, "bundle_closure", "required_profile_contracts must be a non-empty string list", path=prefix + ("required_profile_contracts",), related_id=projection_id if type(projection_id) is str else None)
            missing = [item for item in _sorted_strings(required_contracts) if item not in active_profile_contracts]
            if missing:
                _fail(artifact, "bundle_closure", f"projection requires inactive profile contracts: {missing!r}", path=prefix + ("required_profile_contracts",), related_id=projection_id if type(projection_id) is str else None)


def _validate_evidence_bindings(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> None:
    artifact = bundle.mappings
    evidences = dict(indexes.evidences)

    def fail(category: str, message: str, path: tuple[str | int, ...], related_id: str | None) -> None:
        _fail(artifact, category, message, path=path, related_id=related_id)

    def check_review_evidence(review: Any, *, path: tuple[str | int, ...]) -> None:
        if type(review) is not dict or "evidence" not in review:
            return
        evidence_ids = review.get("evidence")
        if type(evidence_ids) is not list:
            fail("missing_reference", "review evidence must be a list", path + ("evidence",), None)
        for evidence_id in _sorted_strings(evidence_ids):
            if evidence_id not in evidences:
                fail(
                    "missing_reference",
                    f"missing review evidence: {evidence_id!r}",
                    path + ("evidence", evidence_id),
                    evidence_id,
                )

    for dependency_id, dependency in indexes.dependencies:
        bindings = dependency.get("evidence")
        if bindings:
            check_evidence_bindings(bindings, evidences=evidences, path=("dependencies", dependency_id, "evidence"), fail=fail)

    for mapping_id, mapping in indexes.mappings:
        if mapping.get("evidence"):
            check_evidence_bindings(mapping["evidence"], evidences=evidences, path=("mappings", mapping_id, "evidence"), fail=fail)
        check_review_evidence(mapping.get("review"), path=("mappings", mapping_id, "review"))
        for projection in _sorted_children(mapping.get("projections", []), "projection_id"):
            projection_id = projection.get("projection_id")
            projection_path = ("mappings", mapping_id, "projections", projection_id)
            if projection.get("evidence"):
                check_evidence_bindings(projection["evidence"], evidences=evidences, path=projection_path + ("evidence",), fail=fail)
            check_review_evidence(projection.get("review"), path=projection_path + ("review",))
            approximation = projection.get("approximation")
            if type(approximation) is dict and approximation.get("evidence"):
                check_evidence_bindings(approximation["evidence"], evidences=evidences, path=projection_path + ("approximation", "evidence"), fail=fail)

    validate_child_evidence(indexes.mappings, evidences=evidences, fail=fail)


def _validate_digests_and_reviews(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> tuple[tuple[str, str], ...]:
    artifact = bundle.mappings

    def fail(category: str, message: str, path: tuple[str | int, ...], related_id: str | None) -> None:
        _fail(artifact, category, message, path=path, related_id=related_id)

    validate_projection_reviews(indexes.mappings, fail=fail)
    result: list[tuple[str, str]] = []
    for mapping_id, mapping in indexes.mappings:
        review = mapping.get("review")
        if not review:
            continue
        computed = mapping_semantic_digest_v2(mapping)
        stored = mapping.get("mapping_semantic_digest")
        if stored != computed:
            _fail(artifact, "semantic_digest_mismatch", f"mapping semantic digest is stale: {mapping_id}", path=("mappings", mapping_id, "mapping_semantic_digest"), related_id=mapping_id)
        if type(review) is not dict or review.get("reviewed_mapping_digest") != computed:
            _fail(artifact, "review_digest_mismatch", f"review does not bind current mapping semantics: {mapping_id}", path=("mappings", mapping_id, "review", "reviewed_mapping_digest"), related_id=mapping_id)
        result.append((mapping_id, computed))
    return tuple(sorted(result, key=lambda item: _utf16_key(item[0])))


def _validate_native_semantics(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> None:
    artifact = bundle.mappings

    def fail(category: str, message: str, path: tuple[str | int, ...], related_id: str | None) -> None:
        _fail(artifact, category, message, path=path, related_id=related_id)

    validate_native_semantics(indexes.mappings, dependencies=dict(indexes.dependencies), fail=fail)


def _validate_policies(bundle: SemanticSourceBundle, indexes: SemanticIndexes) -> None:
    artifact = bundle.mappings

    def fail(category: str, message: str, path: tuple[str | int, ...], related_id: str | None) -> None:
        _fail(artifact, category, message, path=path, related_id=related_id)

    validate_mapping_policies(indexes.mappings, fail=fail)


def validate_semantic_bundle(bundle: SemanticSourceBundle) -> ValidatedSemanticBundle:
    if not isinstance(bundle, SemanticSourceBundle):
        raise TypeError("bundle must be SemanticSourceBundle")

    _validate_contract_versions(bundle)
    indexes = _build_indexes(bundle)
    _validate_component_authority(bundle, indexes)
    _validate_dependency_closure_and_mapping_scope(bundle, indexes)
    _validate_membership_dependency_authority(bundle, indexes)
    _validate_edge_path_dependency_authority(bundle, indexes)
    _validate_vocabulary(bundle, indexes)
    _validate_record_states(bundle, indexes)
    _validate_projection_and_candidate_legality(bundle, indexes)
    _validate_target_locks(bundle, indexes)
    ontology_bundle_digest = _validate_bundle_source(bundle, indexes)
    _validate_projection_bundle_requirements(bundle, indexes, ontology_bundle_digest)
    _validate_evidence_bindings(bundle, indexes)
    mapping_digests = _validate_digests_and_reviews(bundle, indexes)
    _validate_native_semantics(bundle, indexes)
    _validate_policies(bundle, indexes)

    return ValidatedSemanticBundle(
        bundle=bundle,
        expected_parent_manifest_digest=parent_manifest_digest(bundle.expected_parent_manifest.data),
        mapping_semantic_digests=mapping_digests,
        ontology_bundle_digest=ontology_bundle_digest,
        indexes=indexes,
    )
