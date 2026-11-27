from __future__ import annotations

from typing import Any, Callable

from .semantic_vocabulary import (
    EXTERNAL_REFERENCE_ROUTING,
    IDENTITY_STRENGTHS,
    LOSS_TOKENS,
)

OWL_EQUIVALENT_CLASS = "http://www.w3.org/2002/07/owl#equivalentClass"
OWL_EQUIVALENT_PROPERTY = "http://www.w3.org/2002/07/owl#equivalentProperty"
OWL_SAME_AS = "http://www.w3.org/2002/07/owl#sameAs"
RDFS_SUBCLASS = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
RDFS_SUBPROPERTY = "http://www.w3.org/2000/01/rdf-schema#subPropertyOf"
SKOS_MAPPING_RELATIONS = frozenset(
    {
        "http://www.w3.org/2004/02/skos/core#exactMatch",
        "http://www.w3.org/2004/02/skos/core#closeMatch",
        "http://www.w3.org/2004/02/skos/core#broadMatch",
        "http://www.w3.org/2004/02/skos/core#narrowMatch",
        "http://www.w3.org/2004/02/skos/core#relatedMatch",
    }
)

Fail = Callable[[str, str, tuple[str | int, ...], str | None], None]


def _nonempty_string(value: Any) -> bool:
    return type(value) is str and bool(value)


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


def _validate_projection_publication(
    projection: dict[str, Any],
    *,
    path: tuple[str | int, ...],
    fail: Fail,
) -> None:
    relation = projection.get("publication_relation")
    if relation is None:
        return
    if not _nonempty_string(relation):
        fail("invalid_publication_relation", "publication relation must be a non-empty canonical IRI", path + ("publication_relation",), projection.get("projection_id"))
    kind = projection.get("formal_kind")
    valid = (
        (relation == OWL_EQUIVALENT_CLASS and kind == "class")
        or (relation == OWL_EQUIVALENT_PROPERTY and kind == "property")
        or (relation == RDFS_SUBCLASS and kind == "class")
        or (relation == RDFS_SUBPROPERTY and kind == "property")
        or (relation in SKOS_MAPPING_RELATIONS and kind == "skos-concept")
    )
    if not valid:
        fail("invalid_publication_relation", f"publication relation {relation!r} is not legal for formal kind {kind!r}", path + ("publication_relation",), projection.get("projection_id"))


def _validate_approximation(
    projection: dict[str, Any],
    *,
    path: tuple[str | int, ...],
    fail: Fail,
) -> None:
    approximation = projection.get("approximation")
    if approximation is None:
        return
    if type(approximation) is not dict:
        fail("invalid_approximation", "approximation must be an object", path + ("approximation",), projection.get("projection_id"))

    assessment = projection.get("assessment")
    if assessment not in {"close", "broader", "narrower"}:
        fail(
            "invalid_approximation",
            f"assessment {assessment!r} cannot carry an approximation envelope",
            path + ("approximation",),
            projection.get("projection_id"),
        )

    required = {"status", "eligible", "losses", "rationale", "review_id"}
    allowed = required | {"evidence"}
    if set(approximation) - allowed or required - set(approximation):
        fail("invalid_approximation", "approximation envelope is incomplete or has unknown fields", path + ("approximation",), projection.get("projection_id"))
    if approximation.get("status") != "reviewed":
        fail("invalid_approximation", "approximation status must be reviewed", path + ("approximation", "status"), projection.get("projection_id"))
    eligible = approximation.get("eligible")
    if type(eligible) is not bool:
        fail("invalid_approximation", "approximation eligible must be an exact boolean", path + ("approximation", "eligible"), projection.get("projection_id"))
    losses = approximation.get("losses")
    if type(losses) is not list:
        fail("invalid_approximation", "approximation losses must be a list", path + ("approximation", "losses"), projection.get("projection_id"))
    seen: set[str] = set()
    ordered_losses = sorted(
        enumerate(losses),
        key=lambda pair: _utf16_key(pair[1]) if type(pair[1]) is str else b"",
    )
    for index, loss in ordered_losses:
        if type(loss) is not str or loss not in LOSS_TOKENS:
            fail("unknown_vocabulary", f"unknown approximation loss token: {loss!r}", path + ("approximation", "losses", index), projection.get("projection_id"))
        if loss in seen:
            fail("invalid_approximation", f"duplicate approximation loss token: {loss}", path + ("approximation", "losses", index), projection.get("projection_id"))
        seen.add(loss)
    if not _nonempty_string(approximation.get("rationale")) or not _nonempty_string(approximation.get("review_id")):
        fail("invalid_approximation", "approximation requires non-empty rationale and review_id", path + ("approximation",), projection.get("projection_id"))

    if not eligible:
        return
    if assessment == "broader" and seen != {"undercoverage"}:
        fail("invalid_approximation", "eligible broader mapping must disclose undercoverage only", path + ("approximation", "losses"), projection.get("projection_id"))
    if assessment == "narrower" and seen != {"overcoverage"}:
        fail("invalid_approximation", "eligible narrower mapping must disclose overcoverage only", path + ("approximation", "losses"), projection.get("projection_id"))
    if assessment == "close" and not seen:
        fail("invalid_approximation", "eligible close mapping requires a reviewed non-empty loss set", path + ("approximation", "losses"), projection.get("projection_id"))


def _validate_external_reference(
    reference: dict[str, Any],
    *,
    path: tuple[str | int, ...],
    fail: Fail,
) -> None:
    ref_id = reference.get("reference_id")
    kind = reference.get("reference_kind")
    role = reference.get("query_role")
    if (kind, role) not in EXTERNAL_REFERENCE_ROUTING:
        fail("invalid_reference_routing", f"invalid external-reference routing pair: {(kind, role)!r}", path, ref_id if type(ref_id) is str else None)

    forbidden_projection_fields = {
        "target", "formal_kind", "semantic_role", "profile_id", "capability_id",
        "assessment", "assessment_candidate", "ontology_lock", "approximation",
    }
    leaked = sorted(forbidden_projection_fields & set(reference))
    if leaked:
        fail("invalid_reference_routing", f"external reference leaks target-projection fields: {', '.join(leaked)}", path, ref_id if type(ref_id) is str else None)

    external = reference.get("external")
    if not _nonempty_string(external):
        fail("invalid_reference_routing", "external reference requires a non-empty external value", path + ("external",), ref_id if type(ref_id) is str else None)

    if kind == "entity-identity":
        if not _nonempty_string(reference.get("authority_system")):
            fail("invalid_reference_routing", "entity identity requires authority_system", path + ("authority_system",), ref_id if type(ref_id) is str else None)
        strength = reference.get("identity_strength")
        if type(strength) is not str or strength not in IDENTITY_STRENGTHS:
            fail("unknown_vocabulary", f"unknown identity strength: {strength!r}", path + ("identity_strength",), ref_id if type(ref_id) is str else None)
        relation = reference.get("publication_relation")
        if relation is not None and not (relation == OWL_SAME_AS and strength == "same-entity"):
            fail("invalid_publication_relation", "entity identity publication is limited to owl:sameAs for same-entity", path + ("publication_relation",), ref_id if type(ref_id) is str else None)
        if role == "identity-filter" and type(reference.get("native_binding")) is not dict:
            fail("invalid_reference_routing", "identity-filter requires reviewed native_binding", path + ("native_binding",), ref_id if type(ref_id) is str else None)

    elif kind == "catalogue-identifier":
        if not _nonempty_string(reference.get("issuer_or_namespace")):
            fail("invalid_reference_routing", "catalogue identifier requires issuer_or_namespace", path + ("issuer_or_namespace",), ref_id if type(ref_id) is str else None)
        if type(reference.get("native_binding")) is not dict:
            fail("invalid_reference_routing", "identifier-filter requires reviewed native_binding", path + ("native_binding",), ref_id if type(ref_id) is str else None)
        if reference.get("publication_relation") is not None:
            fail("invalid_publication_relation", "catalogue identifier has no v1 publication relation", path + ("publication_relation",), ref_id if type(ref_id) is str else None)

    elif kind == "provenance-source":
        if role == "metadata-filter" and type(reference.get("native_binding")) is not dict:
            fail("invalid_reference_routing", "metadata-filter requires reviewed native_binding", path + ("native_binding",), ref_id if type(ref_id) is str else None)
        if reference.get("publication_relation") is not None:
            fail("invalid_publication_relation", "provenance source has no v1 publication relation", path + ("publication_relation",), ref_id if type(ref_id) is str else None)

    elif kind == "locator":
        if reference.get("publication_relation") is not None:
            fail("invalid_publication_relation", "locator has no v1 publication relation", path + ("publication_relation",), ref_id if type(ref_id) is str else None)


def validate_mapping_policies(
    mappings: tuple[tuple[str, dict[str, Any]], ...],
    *,
    fail: Fail,
) -> None:
    for mapping_id, mapping in mappings:
        for projection in _sorted_records(mapping.get("projections", []), "projection_id"):
            projection_id = projection.get("projection_id")
            path = ("mappings", mapping_id, "projections", projection_id)
            _validate_approximation(projection, path=path, fail=fail)
            _validate_projection_publication(projection, path=path, fail=fail)
        for reference in _sorted_records(mapping.get("external_references", []), "reference_id"):
            reference_id = reference.get("reference_id")
            path = ("mappings", mapping_id, "external_references", reference_id)
            _validate_external_reference(reference, path=path, fail=fail)
