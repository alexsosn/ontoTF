"""Non-production R-017 external-reference policy prototype.

R-017 classifies external-reference roles and index families. It consumes an
upstream execution-prerequisite gate for any native filter it marks resolvable;
it does not replace R-003/R-015 validation or the R-016 approximation policy.
Positive publication legality is delegated to the R-013/P-003 formal-kind
validator because reference role alone cannot prove RDF/OWL/SKOS operand kinds.
The sole locally decidable publication special case is same-entity identity via
``owl:sameAs`` (compact or canonical W3C IRI spelling).
"""

from __future__ import annotations

from dataclasses import dataclass

SEMANTIC_ASSESSMENTS = {
    "exact",
    "close",
    "broader",
    "narrower",
    "related",
    "ambiguous",
    "native-only",
    "unsupported",
}
SKOS_MAPPING_RELATIONS = {
    "skos:exactMatch",
    "skos:closeMatch",
    "skos:broadMatch",
    "skos:narrowMatch",
    "skos:relatedMatch",
    "http://www.w3.org/2004/02/skos/core#exactMatch",
    "http://www.w3.org/2004/02/skos/core#closeMatch",
    "http://www.w3.org/2004/02/skos/core#broadMatch",
    "http://www.w3.org/2004/02/skos/core#narrowMatch",
    "http://www.w3.org/2004/02/skos/core#relatedMatch",
}
OWL_SAME_AS_RELATIONS = {
    "owl:sameAs",
    "http://www.w3.org/2002/07/owl#sameAs",
}
REFERENCE_KINDS = {
    "semantic-pivot",
    "authority-value",
    "entity-identity",
    "catalogue-identifier",
    "provenance-source",
    "locator",
}
NON_EXACT_EXECUTION_ASSESSMENTS = {"close", "broader", "narrower"}
NO_TARGET_ASSESSMENTS = {"native-only", "unsupported"}


@dataclass(frozen=True)
class ExternalReference:
    reference_id: str
    kind: str
    external: str = ""
    native_selector: str = ""
    authority: str = ""
    assessment: str = ""
    identity_strength: str = ""
    issuer: str = ""
    value: str = ""
    publication_relation: str = ""
    # Derived by P-003/runtime after R-003 parent/profile compatibility and the
    # active R-015 semantic bundle/dependency closure are validated. Never a
    # caller-controlled authorization switch.
    prerequisites_executable: bool = False


@dataclass(frozen=True)
class Resolution:
    status: str
    query_role: str
    native_selector: str = ""
    reason: str = ""


def validate(ref: ExternalReference) -> list[str]:
    errors: list[str] = []
    if ref.kind not in REFERENCE_KINDS:
        return ["reference kind must be explicit and controlled"]

    if ref.kind in {"semantic-pivot", "authority-value"}:
        if ref.assessment not in SEMANTIC_ASSESSMENTS:
            errors.append("semantic/authority reference requires ontoTF mapping assessment")
        if ref.assessment in NO_TARGET_ASSESSMENTS:
            errors.append(
                f"{ref.assessment} is a no-target state and cannot be represented as an external semantic/authority reference"
            )
        if not ref.external:
            errors.append("semantic/authority reference requires external resource identity")

    if ref.kind == "authority-value" and not ref.authority:
        errors.append("authority-value requires authority identity")

    if ref.kind == "entity-identity":
        if not ref.external:
            errors.append("entity-identity requires external entity reference")
        if ref.identity_strength not in {
            "same-entity",
            "probable-same-entity",
            "related-record",
            "ambiguous-identity",
        }:
            errors.append("entity-identity requires controlled identity strength")

    if ref.kind == "catalogue-identifier":
        if not ref.issuer:
            errors.append("catalogue identifier requires issuer/namespace")
        if not ref.value:
            errors.append("catalogue identifier requires scoped value")

    if ref.kind in {"provenance-source", "locator"} and not ref.external:
        errors.append(f"{ref.kind} requires explicit external reference")

    relation = ref.publication_relation
    if relation in OWL_SAME_AS_RELATIONS:
        if not (ref.kind == "entity-identity" and ref.identity_strength == "same-entity"):
            errors.append("owl:sameAs requires same-entity identity reference")
    elif relation in SKOS_MAPPING_RELATIONS:
        # R-017 knows the external-reference role, but not whether the native
        # publication subject and target are both SKOS concepts. Accepted R-013
        # makes formal target kind independent from semantic/reference role, so
        # positive SKOS publication must be decided by that formal-kind-aware
        # validator rather than inferred here.
        errors.append(
            "SKOS mapping publication relation requires R-013 formal-kind validation"
        )
    elif relation:
        # R-017 has no formal-kind information with which to prove arbitrary
        # RDF/RDFS/OWL predicate legality. Unknown/non-local positive relations
        # therefore fail closed and are delegated to R-013/P-003 rather than
        # becoming an open-ended escape hatch based on spelling.
        errors.append(
            "publication relation requires R-013 formal-kind validation"
        )

    return errors


def _upstream_execution_gate(ref: ExternalReference, query_role: str) -> Resolution | None:
    """Return a fail-closed refusal unless the derived upstream gate is exactly true."""

    if type(ref.prerequisites_executable) is not bool:
        return Resolution(
            "informative-only",
            query_role,
            reason="upstream execution prerequisite gate must be an exact boolean",
        )
    if not ref.prerequisites_executable:
        return Resolution(
            "informative-only",
            query_role,
            reason="upstream execution prerequisites are not executable",
        )
    return None


def _resolve_semantic_or_authority(ref: ExternalReference, query_role: str) -> Resolution:
    if ref.assessment in NON_EXACT_EXECUTION_ASSESSMENTS:
        return Resolution(
            "informative-only",
            query_role,
            reason="non-exact execution requires R-016 approximation policy authorization",
        )
    if ref.assessment in {"ambiguous", "related"}:
        return Resolution("informative-only", query_role, reason=ref.assessment)
    if ref.assessment != "exact":
        # NO_TARGET_ASSESSMENTS have already failed validation. Keep this branch
        # fail-closed if the assessment vocabulary changes independently.
        return Resolution("informative-only", query_role, reason="assessment is not executable in R-017")
    if not ref.native_selector:
        reason = (
            "no reviewed authority-value binding"
            if ref.kind == "authority-value"
            else "no reviewed native selector"
        )
        return Resolution("informative-only", query_role, reason=reason)
    upstream_refusal = _upstream_execution_gate(ref, query_role)
    if upstream_refusal is not None:
        return upstream_refusal
    return Resolution("resolvable", query_role, ref.native_selector)


def resolve(ref: ExternalReference) -> Resolution:
    errors = validate(ref)
    if errors:
        return Resolution("invalid", "none", reason="; ".join(errors))

    if ref.kind == "semantic-pivot":
        return _resolve_semantic_or_authority(ref, "semantic-constraint")

    if ref.kind == "authority-value":
        return _resolve_semantic_or_authority(ref, "authority-value-filter")

    if ref.kind == "entity-identity":
        if ref.identity_strength != "same-entity":
            return Resolution("informative-only", "identity-filter", reason=ref.identity_strength)
        if not ref.native_selector:
            return Resolution("informative-only", "identity-filter", reason="no reviewed native identity selector")
        upstream_refusal = _upstream_execution_gate(ref, "identity-filter")
        if upstream_refusal is not None:
            return upstream_refusal
        return Resolution("resolvable", "identity-filter", ref.native_selector)

    if ref.kind == "catalogue-identifier":
        if not ref.native_selector:
            return Resolution("informative-only", "identifier-filter", reason="identifier not queryable in native corpus")
        upstream_refusal = _upstream_execution_gate(ref, "identifier-filter")
        if upstream_refusal is not None:
            return upstream_refusal
        return Resolution("resolvable", "identifier-filter", ref.native_selector)

    if ref.kind == "provenance-source":
        return Resolution("informative-only", "metadata/explanation", reason="source/provenance reference")

    return Resolution("informative-only", "explanation-only", reason="locator reference")


def identifier_key(ref: ExternalReference) -> tuple[str, str]:
    if ref.kind != "catalogue-identifier":
        raise ValueError("identifier_key requires catalogue-identifier")
    errors = validate(ref)
    if errors:
        raise ValueError("; ".join(errors))
    return (ref.issuer, ref.value)


def reverse_index_bucket(ref: ExternalReference) -> str:
    """Return the logically separate reverse-index family for a reference."""
    errors = validate(ref)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "semantic-pivot": "semantic",
        "authority-value": "authority",
        "entity-identity": "identity",
        "catalogue-identifier": "identifier",
        "provenance-source": "provenance",
        "locator": "locator",
    }[ref.kind]
