from __future__ import annotations

import copy
from typing import Any

from ontotf.digests import evidence_record_digest
from ontotf.semantic_digest_v2 import mapping_semantic_digest_v2, projection_semantic_digest_v1
from ontotf.semantic_validation import (
    SemanticArtifact,
    SemanticSourceBundle,
    ValidatedSemanticBundle,
    validate_semantic_bundle,
)
from ontotf.source_validation import validate_source

OLIA_NOUN = "http://purl.org/olia/olia.owl#Noun"
AUTHORITY_NOUN = "https://example.org/authority/noun"


def _sha(ch: str) -> str:
    return "sha256:" + ch * 64


def _evidence(corpus_id: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "evidence_id": f"evidence:{corpus_id}:noun",
        "kind": "ontology-definition",
        "source_uri": "https://example.org/evidence/noun",
        "source_revision": "fixture-v1",
        "content_mode": "normalized-record",
        "reviewed_content": {"target": OLIA_NOUN, "native": "word.sp=subs"},
        "content_digest": "placeholder",
    }
    record["content_digest"] = evidence_record_digest(record)
    return record


def _review(review_id: str, status: str = "reviewed") -> dict[str, Any]:
    return {
        "review_id": review_id,
        "status": status,
        "reviewed_mapping_digest": "placeholder",
        "reviewer_id": "reviewer:i005-fixture",
        "reviewed_at": "2026-09-09T00:00:00Z",
        "review_source": "I-005 contract fixture",
        "review_method": "independent-adversarial",
        "notes": ["fixture audit metadata"],
    }


def _binding(evidence: dict[str, Any]) -> dict[str, str]:
    return {
        "evidence_id": evidence["evidence_id"],
        "content_digest": evidence["content_digest"],
    }


def noun_sources(
    corpus_id: str,
    *,
    parent_char: str,
    authored_profile_id: str | None = None,
    profile_version: str = "0.1.0",
    native_state: str = "positive",
    mapping_review_status: str = "reviewed",
    projection_review_status: str = "reviewed",
    native_value: str = "subs",
    projection_route: str = "semantic",
    external_references: list[dict[str, Any]] | None = None,
    candidate: bool = False,
    mapping_review_id: str | None = None,
    projection_review_id: str | None = None,
    audit_suffix: str = "",
) -> dict[str, Any]:
    authored_profile_id = authored_profile_id or f"ontotf-{corpus_id}"
    evidence = _evidence(corpus_id)
    evidence_binding = _binding(evidence)
    component_id = f"{corpus_id}-tf"
    lock_id = f"{corpus_id}-olia"

    dependency = {
        "dependency_id": f"dep:{corpus_id}:word-sp",
        "component_id": component_id,
        "kind": "native-value-present",
        "assertion": {
            "node_type": "word",
            "feature": "sp",
            "value": native_value,
            "value_semantics": "semantic",
        },
    }
    profile = {
        "schema_version": 2,
        "profile_id": authored_profile_id,
        "profile_version": profile_version,
        "semantic_domains": ["linguistic"],
        "profile_catalog_version": 1,
        "profiles": ["linguistic"],
        "capabilities": ["linguistic.part-of-speech"],
        "parent_component_manifest": "parent/expected-components.json",
        "required_components": [component_id],
        "ontology_locks": [lock_id],
        "mapping_sources": [f"mappings/{corpus_id}.json"],
        "dependency_contract_version": 1,
        "dependencies": [dependency],
        "minimum_tfont_runtime": "0.1.0",
        "license": "CC-BY-4.0",
    }
    parent = {
        "algorithm": "tfont-parent-components-sha256-v1",
        "components": [
            {
                "component_id": component_id,
                "kind": "tf-payload",
                "identity_algorithm": "tfont-tf-files-sha256-v1",
                "content_digest": _sha(parent_char),
            }
        ],
    }
    semantic_route = projection_route == "semantic"
    lock = {
        "lock_id": lock_id,
        "ontology_id": "olia" if semantic_route else "authority-test",
        "support_tier": "core",
        "term_namespace": (
            "http://purl.org/olia/olia.owl#"
            if semantic_route
            else "https://example.org/authority/"
        ),
        "release": "fixture-release",
        "source_uri": "https://example.org/ontology-fixture.ttl",
        "snapshot_artifact": "fixtures/ontology-fixture.ttl",
        "content_digest": _sha("f"),
        "license": "CC-BY-4.0",
        "terms_used": [OLIA_NOUN if semantic_route else AUTHORITY_NOUN],
    }

    mapping: dict[str, Any] = {
        "mapping_id": f"mapping:{corpus_id}:noun",
        "corpus_id": corpus_id,
        "native_binding": {
            "component_id": component_id,
            "node_type": "word",
            "feature": "sp",
            "value": native_value,
        },
        "native_dependencies": [dependency["dependency_id"]],
        "profiles": ["linguistic"],
        "capabilities": ["linguistic.part-of-speech"],
        "native_state": native_state,
        "projections": [],
        "ambiguous_candidates": [],
        "external_references": copy.deepcopy(external_references or []),
        "evidence": [copy.deepcopy(evidence_binding)],
        "review": _review(
            mapping_review_id or f"review:{corpus_id}:mapping:noun",
            mapping_review_status,
        ),
        "mapping_semantic_digest": "placeholder",
        "rationale": "I-005 contract fixture",
    }
    if audit_suffix:
        mapping["review"]["reviewer_id"] += audit_suffix
        mapping["review"]["reviewed_at"] = (
            f"2026-09-09T00:00:0{len(audit_suffix) % 9}Z"
        )
        mapping["review"]["notes"] = [f"fixture audit metadata {audit_suffix}"]

    if native_state == "positive":
        projection = {
            "projection_id": f"projection:{corpus_id}:noun",
            "target": OLIA_NOUN if semantic_route else AUTHORITY_NOUN,
            "reference_kind": "semantic-pivot" if semantic_route else "authority-value",
            "query_role": "semantic-constraint" if semantic_route else "authority-value-filter",
            "formal_kind": "class" if semantic_route else "skos-concept",
            "semantic_role": "annotation-value",
            "profile_id": "linguistic",
            "capability_id": "linguistic.part-of-speech",
            "assessment": "exact",
            "ontology_lock": lock_id,
            "native_execution_binding": {
                "component_id": component_id,
                "node_type": "word",
                "feature": "sp",
                "value": native_value,
            },
            "evidence": [copy.deepcopy(evidence_binding)],
            "review": _review(
                projection_review_id or f"review:{corpus_id}:projection:noun",
                projection_review_status,
            ),
            "projection_semantic_digest": "placeholder",
        }
        projection["projection_semantic_digest"] = projection_semantic_digest_v1(projection)
        projection["review"]["reviewed_mapping_digest"] = projection["projection_semantic_digest"]
        mapping["projections"] = [projection]
    elif native_state == "ambiguous" or candidate:
        mapping["native_state"] = "ambiguous"
        mapping["ambiguous_candidates"] = [
            {
                "candidate_id": f"candidate:{corpus_id}:noun",
                "target": OLIA_NOUN,
                "reference_kind": "semantic-pivot",
                "query_role": "semantic-constraint",
                "formal_kind": "class",
                "semantic_role": "annotation-value",
                "profile_id": "linguistic",
                "capability_id": "linguistic.part-of-speech",
                "assessment_candidate": "close",
                "ontology_lock": lock_id,
                "evidence": [copy.deepcopy(evidence_binding)],
            }
        ]

    mapping["mapping_semantic_digest"] = mapping_semantic_digest_v2(mapping)
    mapping["review"]["reviewed_mapping_digest"] = mapping["mapping_semantic_digest"]
    return {
        "profile": profile,
        "parent": parent,
        "mappings": {"schema_version": 2, "mappings": [mapping]},
        "locks": [lock],
        "evidences": [evidence],
    }


def entity_identity_reference(corpus_id: str) -> dict[str, Any]:
    return {
        "reference_id": f"reference:{corpus_id}:identity",
        "reference_kind": "entity-identity",
        "query_role": "identity-filter",
        "external": f"https://example.org/entity/{corpus_id}",
        "authority_system": "fixture-authority",
        "identity_strength": "same-entity",
        "native_binding": {
            "component_id": f"{corpus_id}-tf",
            "node_type": "word",
            "feature": "sp",
            "value": "subs",
        },
        "evidence": [],
    }


def catalogue_reference(corpus_id: str) -> dict[str, Any]:
    return {
        "reference_id": f"reference:{corpus_id}:catalogue",
        "reference_kind": "catalogue-identifier",
        "query_role": "identifier-filter",
        "external": f"ID-{corpus_id}",
        "issuer_or_namespace": "fixture-catalogue",
        "native_binding": {
            "component_id": f"{corpus_id}-tf",
            "node_type": "word",
            "feature": "sp",
            "value": "subs",
        },
        "evidence": [],
    }


def locator_reference(corpus_id: str) -> dict[str, Any]:
    return {
        "reference_id": f"reference:{corpus_id}:locator",
        "reference_kind": "locator",
        "query_role": "explanation-only",
        "external": f"https://example.org/locator/{corpus_id}",
        "evidence": [],
    }


def provenance_reference(corpus_id: str) -> dict[str, Any]:
    return {
        "reference_id": f"reference:{corpus_id}:source",
        "reference_kind": "provenance-source",
        "query_role": "explanation-only",
        "external": f"https://example.org/source/{corpus_id}",
        "evidence": [],
    }


def source_bundle(sources: dict[str, Any]) -> SemanticSourceBundle:
    return SemanticSourceBundle(
        profile=SemanticArtifact("profile", "profile.json", sources["profile"]),
        expected_parent_manifest=SemanticArtifact(
            "parent-component-manifest", "parent.json", sources["parent"]
        ),
        mappings=SemanticArtifact("mapping", "mappings.json", sources["mappings"]),
        ontology_locks=tuple(
            SemanticArtifact("ontology-lock", f"lock-{index}.json", lock)
            for index, lock in enumerate(sources["locks"])
        ),
        evidences=tuple(
            SemanticArtifact("evidence", f"evidence-{index}.json", evidence)
            for index, evidence in enumerate(sources["evidences"])
        ),
    )


def validate_structural_sources(sources: dict[str, Any]) -> None:
    validate_source(sources["profile"], "profile", source_name="profile.json")
    validate_source(
        sources["parent"], "parent-component-manifest", source_name="parent.json"
    )
    validate_source(sources["mappings"], "mapping", source_name="mappings.json")
    for index, lock in enumerate(sources["locks"]):
        validate_source(lock, "ontology-lock", source_name=f"lock-{index}.json")
    for index, evidence in enumerate(sources["evidences"]):
        validate_source(evidence, "evidence", source_name=f"evidence-{index}.json")


def validated_noun_bundle(
    corpus_id: str,
    *,
    parent_char: str,
    **kwargs: Any,
) -> ValidatedSemanticBundle:
    sources = noun_sources(corpus_id, parent_char=parent_char, **kwargs)
    validate_structural_sources(sources)
    return validate_semantic_bundle(source_bundle(sources))
