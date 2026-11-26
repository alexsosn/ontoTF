from __future__ import annotations

import copy
import unittest

from ontotf.digests import DigestError, evidence_record_digest
from ontotf.semantic_digest_v2 import projection_semantic_digest_v1
from ontotf.semantic_validation import (
    SemanticArtifact,
    SemanticSourceBundle,
    SemanticValidationError,
    validate_semantic_bundle,
)
from tests.i004.test_semantic_validation_phase1 import base_sources
from tests.i004.test_semantic_validation_phase3 import reviewed_sources


def evidence_record(evidence_id: str = "evidence:child") -> dict:
    record = {
        "evidence_id": evidence_id,
        "kind": "ontology-definition",
        "source_uri": "https://example.org/evidence",
        "source_revision": "rev",
        "content_mode": "normalized-record",
        "reviewed_content": {"statement": "reviewed"},
        "content_digest": "placeholder",
    }
    record["content_digest"] = evidence_record_digest(record)
    return record


def full_bundle(sources: dict) -> SemanticSourceBundle:
    return SemanticSourceBundle(
        profile=SemanticArtifact("profile", "profile.json", sources["profile"]),
        expected_parent_manifest=SemanticArtifact("parent-component-manifest", "parent.json", sources["parent"]),
        mappings=SemanticArtifact("mapping", "mappings.json", sources["mappings"]),
        ontology_locks=tuple(
            SemanticArtifact("ontology-lock", f"lock-{i}.json", lock)
            for i, lock in enumerate(sources["locks"])
        ),
        evidences=tuple(
            SemanticArtifact("evidence", f"evidence-{i}.json", evidence)
            for i, evidence in enumerate(sources.get("evidences", []))
        ),
    )


def bind_projection_review(projection: dict) -> None:
    projection["projection_semantic_digest"] = projection_semantic_digest_v1(projection)
    projection["review"]["reviewed_mapping_digest"] = projection["projection_semantic_digest"]


class I004Phase5Tests(unittest.TestCase):
    def assert_problem(self, category: str, sources: dict):
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(full_bundle(sources))
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception.problem

    def test_projection_semantic_edit_invalidates_projection_digest(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        bind_projection_review(projection)
        projection["assessment"] = "close"
        self.assert_problem("stale_semantic_digest", sources)

    def test_projection_review_must_bind_projection_digest(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        bind_projection_review(projection)
        projection["review"]["reviewed_mapping_digest"] = "sha256:stale"
        self.assert_problem("stale_review_binding", sources)

    def test_projection_audit_only_review_edit_keeps_digest_valid(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        bind_projection_review(projection)
        projection["review"]["reviewed_at"] = "2026-09-09T00:00:00Z"
        validate_semantic_bundle(full_bundle(sources))

    def test_candidate_evidence_must_resolve_and_match_digest(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        projection = mapping["projections"].pop()
        mapping["native_state"] = "ambiguous"
        evidence = evidence_record()
        sources["evidences"] = [evidence]
        mapping["ambiguous_candidates"] = [{
            "candidate_id": "candidate:noun",
            "target": projection["target"],
            "reference_kind": projection["reference_kind"],
            "query_role": projection["query_role"],
            "formal_kind": projection["formal_kind"],
            "semantic_role": projection["semantic_role"],
            "profile_id": projection["profile_id"],
            "capability_id": projection["capability_id"],
            "assessment_candidate": "close",
            "ontology_lock": projection["ontology_lock"],
            "evidence": [{"evidence_id": evidence["evidence_id"], "content_digest": "sha256:stale"}],
        }]
        self.assert_problem("evidence_digest_mismatch", sources)

    def test_external_reference_evidence_must_resolve(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["external_references"] = [{
            "reference_id": "ref:locator",
            "reference_kind": "locator",
            "query_role": "explanation-only",
            "external": "https://example.org/record/1",
            "evidence": [{"evidence_id": "evidence:missing", "content_digest": "sha256:missing"}],
        }]
        self.assert_problem("missing_reference", sources)

    def test_dependency_evidence_must_resolve_and_match_digest(self):
        sources = base_sources()
        sources["profile"]["dependencies"][0]["evidence"] = [
            {"evidence_id": "evidence:missing", "content_digest": "sha256:missing"}
        ]
        self.assert_problem("missing_reference", sources)

    def test_approximation_evidence_must_resolve_and_match_digest(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["assessment"] = "broader"
        projection["approximation"] = {
            "status": "reviewed",
            "eligible": True,
            "losses": ["undercoverage"],
            "rationale": "reviewed bounded subset",
            "review_id": "review:approx",
            "evidence": [
                {"evidence_id": "evidence:missing", "content_digest": "sha256:missing"}
            ],
        }
        self.assert_problem("missing_reference", sources)

    def test_mapping_native_binding_component_must_be_authorized_by_dependencies(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["native_binding"]["component_id"] = "other-tf"
        self.assert_problem("component_authority", sources)

    def test_projection_execution_component_must_be_authorized_by_dependencies(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["native_execution_binding"]["component_id"] = "other-tf"
        self.assert_problem("component_authority", sources)

    def test_semantic_digest_precedes_native_semantics_failure(self):
        sources = reviewed_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_binding"] = {
            "component_id": "test-tf",
            "node_type": "word",
            "feature": "gn",
            "value": "",
        }
        self.assert_problem("stale_semantic_digest", sources)

    def test_semantic_empty_value_requires_matching_native_value_dependency(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_binding"] = {"component_id": "test-tf", "node_type": "word", "feature": "gn", "value": ""}
        mapping["native_dependencies"] = ["dep:word-sp"]
        self.assert_problem("native_semantics_unproven", sources)

    def test_semantic_empty_value_is_allowed_with_explicit_dependency(self):
        sources = base_sources()
        sources["profile"]["dependencies"][0] = {
            "dependency_id": "dep:empty",
            "component_id": "test-tf",
            "kind": "native-value-present",
            "assertion": {
                "node_type": "word",
                "feature": "gn",
                "value": "",
                "value_semantics": "semantic",
            },
        }
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_dependencies"] = ["dep:empty"]
        mapping["native_binding"] = {"component_id": "test-tf", "node_type": "word", "feature": "gn", "value": ""}
        validate_semantic_bundle(full_bundle(sources))

    def test_closed_domain_claim_requires_closed_reviewed_value_domain_dependency(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_binding"] = {
            "component_id": "test-tf",
            "node_type": "word",
            "feature": "gn",
            "closed_values": ["m", "f"],
        }
        self.assert_problem("native_semantics_unproven", sources)

    def test_digest_v2_non_mapping_input_has_stable_digest_error(self):
        from ontotf.semantic_digest_v2 import mapping_semantic_digest_v2

        with self.assertRaises(DigestError) as raised:
            mapping_semantic_digest_v2([])  # type: ignore[arg-type]
        self.assertEqual(raised.exception.problem.category, "projection_error")

    def test_duplicate_id_precedes_native_semantics_failure(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_binding"] = {"component_id": "test-tf", "node_type": "word", "feature": "gn", "value": ""}
        sources["mappings"]["mappings"].append(copy.deepcopy(mapping))
        self.assert_problem("duplicate_id", sources)


if __name__ == "__main__":
    unittest.main()
