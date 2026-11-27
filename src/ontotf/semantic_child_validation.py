from __future__ import annotations

from typing import Any, Callable

from .semantic_digest_v2 import projection_semantic_digest_v1

Fail = Callable[[str, str, tuple[str | int, ...], str | None], None]


def _utf16_key(value: str) -> bytes:
    return value.encode("utf-16be")


def _sorted_records(value: Any, id_field: str) -> list[dict[str, Any]]:
    if type(value) is not list:
        return []
    rows = [row for row in value if type(row) is dict]
    return sorted(
        rows,
        key=lambda row: _utf16_key(row.get(id_field))
        if type(row.get(id_field)) is str
        else b"",
    )


def _scalar_identity(value: Any) -> tuple[str, Any] | None:
    if value is None:
        return ("null", None)
    if type(value) is bool:
        return ("boolean", value)
    if type(value) is int:
        return ("integer", value)
    if type(value) is float:
        return ("number", value)
    if type(value) is str:
        return ("string", value)
    return None


def _validate_value_set_dependency_coverage(
    binding: dict[str, Any],
    *,
    resolved_dependencies: list[dict[str, Any]],
    path: tuple[str | int, ...],
    related_id: str,
    fail: Fail,
) -> None:
    if binding.get("execution_shape") != "value-set-predicate":
        return
    selected = binding.get("values")
    if type(selected) is not list or not selected:
        fail(
            "native_semantics_unproven",
            "value-set-predicate requires a non-empty selected value set",
            path + ("values",),
            related_id,
        )
        return

    authorized: set[tuple[str, str, str, tuple[str, Any]]] = set()
    for dependency in resolved_dependencies:
        assertion = dependency.get("assertion")
        if (
            dependency.get("kind") != "native-value-present"
            or type(assertion) is not dict
            or assertion.get("value_semantics") != "semantic"
        ):
            continue
        identity = _scalar_identity(assertion.get("value"))
        component_id = dependency.get("component_id")
        node_type = assertion.get("node_type")
        feature = assertion.get("feature")
        if (
            identity is not None
            and type(component_id) is str
            and type(node_type) is str
            and type(feature) is str
        ):
            authorized.add((component_id, node_type, feature, identity))

    component_id = binding.get("component_id")
    node_type = binding.get("node_type")
    feature = binding.get("feature")
    for value in selected:
        identity = _scalar_identity(value)
        required = (component_id, node_type, feature, identity)
        if (
            identity is None
            or type(component_id) is not str
            or type(node_type) is not str
            or type(feature) is not str
            or required not in authorized
        ):
            fail(
                "native_semantics_unproven",
                "value-set-predicate requires a matching semantic native-value-present dependency for every selected value",
                path + ("values",),
                related_id,
            )


def check_evidence_bindings(
    bindings: Any,
    *,
    evidences: dict[str, dict[str, Any]],
    path: tuple[str | int, ...],
    fail: Fail,
) -> None:
    if type(bindings) is not list:
        fail("missing_reference", "evidence bindings must be a list", path, None)
    indexed = list(enumerate(bindings))
    indexed.sort(
        key=lambda pair: _utf16_key(pair[1].get("evidence_id"))
        if type(pair[1]) is dict and type(pair[1].get("evidence_id")) is str
        else b""
    )
    for index, binding in indexed:
        item_path = path + (index,)
        if type(binding) is not dict:
            fail("missing_reference", "evidence binding must be an object", item_path, None)
        evidence_id = binding.get("evidence_id")
        if type(evidence_id) is not str or evidence_id not in evidences:
            fail(
                "missing_reference",
                f"missing evidence: {evidence_id!r}",
                item_path + ("evidence_id",),
                evidence_id if type(evidence_id) is str else None,
            )
        if binding.get("content_digest") != evidences[evidence_id].get("content_digest"):
            fail(
                "evidence_digest_mismatch",
                f"evidence digest mismatch: {evidence_id}",
                item_path + ("content_digest",),
                evidence_id,
            )


def validate_child_evidence(
    mappings: tuple[tuple[str, dict[str, Any]], ...],
    *,
    evidences: dict[str, dict[str, Any]],
    fail: Fail,
) -> None:
    for mapping_id, mapping in mappings:
        for candidate in _sorted_records(mapping.get("ambiguous_candidates", []), "candidate_id"):
            candidate_id = candidate.get("candidate_id")
            bindings = candidate.get("evidence", [])
            if bindings:
                check_evidence_bindings(
                    bindings,
                    evidences=evidences,
                    path=("mappings", mapping_id, "ambiguous_candidates", candidate_id, "evidence"),
                    fail=fail,
                )
        for reference in _sorted_records(mapping.get("external_references", []), "reference_id"):
            reference_id = reference.get("reference_id")
            bindings = reference.get("evidence", [])
            if bindings:
                check_evidence_bindings(
                    bindings,
                    evidences=evidences,
                    path=("mappings", mapping_id, "external_references", reference_id, "evidence"),
                    fail=fail,
                )


def validate_projection_reviews(
    mappings: tuple[tuple[str, dict[str, Any]], ...],
    *,
    fail: Fail,
) -> None:
    for mapping_id, mapping in mappings:
        for projection in _sorted_records(mapping.get("projections", []), "projection_id"):
            review = projection.get("review")
            if not review:
                continue
            projection_id = projection.get("projection_id")
            path = ("mappings", mapping_id, "projections", projection_id)
            computed = projection_semantic_digest_v1(projection)
            stored = projection.get("projection_semantic_digest")
            if stored != computed:
                fail(
                    "semantic_digest_mismatch",
                    f"projection semantic digest is stale: {projection_id}",
                    path + ("projection_semantic_digest",),
                    projection_id,
                )
            if type(review) is not dict or review.get("reviewed_mapping_digest") != computed:
                fail(
                    "review_digest_mismatch",
                    f"projection review does not bind current semantics: {projection_id}",
                    path + ("review", "reviewed_mapping_digest"),
                    projection_id,
                )


def validate_native_semantics(
    mappings: tuple[tuple[str, dict[str, Any]], ...],
    *,
    dependencies: dict[str, dict[str, Any]],
    fail: Fail,
) -> None:
    for mapping_id, mapping in mappings:
        binding = mapping.get("native_binding")
        if type(binding) is not dict:
            continue
        dependency_ids = [
            item for item in mapping.get("native_dependencies", []) if type(item) is str
        ]
        dependency_ids.sort(key=_utf16_key)
        resolved = [dependencies[dependency_id] for dependency_id in dependency_ids if dependency_id in dependencies]

        _validate_value_set_dependency_coverage(
            binding,
            resolved_dependencies=resolved,
            path=("mappings", mapping_id, "native_binding"),
            related_id=mapping_id,
            fail=fail,
        )
        for projection in _sorted_records(mapping.get("projections", []), "projection_id"):
            projection_id = projection.get("projection_id")
            execution = projection.get("native_execution_binding")
            if type(execution) is dict:
                _validate_value_set_dependency_coverage(
                    execution,
                    resolved_dependencies=resolved,
                    path=(
                        "mappings",
                        mapping_id,
                        "projections",
                        projection_id,
                        "native_execution_binding",
                    ),
                    related_id=projection_id if type(projection_id) is str else mapping_id,
                    fail=fail,
                )

        if "value" in binding and binding.get("value") in {"", None}:
            required = (binding.get("node_type"), binding.get("feature"), binding.get("value"))
            proven = False
            for dependency in resolved:
                assertion = dependency.get("assertion")
                if dependency.get("kind") == "native-value-present" and type(assertion) is dict:
                    actual = (
                        assertion.get("node_type"),
                        assertion.get("feature"),
                        assertion.get("value"),
                    )
                    if actual == required and assertion.get("value_semantics") == "semantic":
                        proven = True
                        break
            if not proven:
                fail(
                    "native_semantics_unproven",
                    "empty/null native value requires matching semantic native-value-present dependency",
                    ("mappings", mapping_id, "native_binding", "value"),
                    mapping_id,
                )

        if "closed_values" in binding:
            values = binding.get("closed_values")
            if type(values) is not list or not values:
                fail(
                    "native_semantics_unproven",
                    "closed_values must be a non-empty reviewed domain claim",
                    ("mappings", mapping_id, "native_binding", "closed_values"),
                    mapping_id,
                )
            required_values = set(values)
            proven = False
            for dependency in resolved:
                assertion = dependency.get("assertion")
                if dependency.get("kind") == "value-domain" and type(assertion) is dict:
                    if (
                        assertion.get("node_type") == binding.get("node_type")
                        and assertion.get("feature") == binding.get("feature")
                        and assertion.get("domain_semantics") == "closed-reviewed"
                        and type(assertion.get("values")) is list
                        and set(assertion.get("values")) == required_values
                        and assertion.get("evidence")
                    ):
                        proven = True
                        break
            if not proven:
                fail(
                    "native_semantics_unproven",
                    "closed domain claim requires matching closed-reviewed value-domain dependency with evidence",
                    ("mappings", mapping_id, "native_binding", "closed_values"),
                    mapping_id,
                )


def validate_child_semantics(
    mappings: tuple[tuple[str, dict[str, Any]], ...],
    *,
    dependencies: dict[str, dict[str, Any]],
    evidences: dict[str, dict[str, Any]],
    fail: Fail,
) -> None:
    """Compatibility composition; the I-004 orchestrator invokes the phases separately."""

    validate_child_evidence(mappings, evidences=evidences, fail=fail)
    validate_projection_reviews(mappings, fail=fail)
    validate_native_semantics(mappings, dependencies=dependencies, fail=fail)
