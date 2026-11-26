from __future__ import annotations

import copy
import unittest

from ontotf.digests import evidence_record_digest
from ontotf.semantic_validation import (
    SemanticArtifact,
    SemanticSourceBundle,
    SemanticValidationError,
    validate_semantic_bundle,
)

try:
    from test_semantic_validation_phase1 import base_sources, bundle
except ModuleNotFoundError:
    from i004.test_semantic_validation_phase1 import base_sources, bundle


def _bundle_with_evidence(sources: dict) -> SemanticSourceBundle:
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


class I004Phase2Tests(unittest.TestCase):
    def assert_problem(self, category: str, sources: dict):
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(bundle(sources))
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception.problem

    def test_native_only_cannot_carry_projection(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_state"] = "native-only"
        self.assert_problem("invalid_record_state", sources)

    def test_unsupported_cannot_carry_projection(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_state"] = "unsupported"
        self.assert_problem("invalid_record_state", sources)

    def test_ambiguous_requires_typed_candidate_and_no_projection(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        projection = mapping["projections"].pop()
        mapping["native_state"] = "ambiguous"
        evidence = {
            "evidence_id": "evidence:candidate",
            "kind": "ontology-definition",
            "source_uri": "https://example.org/evidence/candidate",
            "source_revision": "test-rev",
            "content_mode": "normalized-record",
            "reviewed_content": {"statement": "candidate evidence"},
            "content_digest": "placeholder",
        }
        evidence["content_digest"] = evidence_record_digest(evidence)
        sources["evidences"] = [evidence]
        mapping["ambiguous_candidates"] = [
            {
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
                "evidence": [{"evidence_id": evidence["evidence_id"], "content_digest": evidence["content_digest"]}],
            }
        ]
        result = validate_semantic_bundle(_bundle_with_evidence(sources))
        self.assertEqual(dict(result.indexes.candidates).keys(), {"candidate:noun"})

    def test_ambiguous_without_candidate_fails(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_state"] = "ambiguous"
        mapping["projections"] = []
        self.assert_problem("invalid_record_state", sources)

    def test_ambiguous_candidate_cannot_be_under_typed(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_state"] = "ambiguous"
        mapping["projections"] = []
        mapping["ambiguous_candidates"] = [
            {
                "candidate_id": "candidate:noun",
                "target": "http://purl.org/olia/olia.owl#Noun",
                "ontology_lock": "olia-test",
                "evidence": [],
            }
        ]
        self.assert_problem("invalid_candidate", sources)

    def test_ambiguous_candidate_must_not_carry_approximation(self):
        sources = base_sources()
        mapping = sources["mappings"]["mappings"][0]
        projection = copy.deepcopy(mapping["projections"][0])
        mapping["native_state"] = "ambiguous"
        mapping["projections"] = []
        projection.pop("projection_id")
        projection.pop("assessment")
        projection.pop("native_execution_binding")
        projection.pop("review")
        projection.pop("projection_semantic_digest")
        projection["candidate_id"] = "candidate:noun"
        projection["assessment_candidate"] = "close"
        projection["approximation"] = {"eligible": True, "losses": ["undercoverage"]}
        mapping["ambiguous_candidates"] = [projection]
        self.assert_problem("invalid_candidate", sources)

    def test_class_relation_kind_role_conflict_fails(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["formal_kind"] = "class"
        projection["semantic_role"] = "relation"
        self.assert_problem("kind_role_conflict", sources)

    def test_property_entity_type_kind_role_conflict_fails(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["formal_kind"] = "property"
        projection["semantic_role"] = "entity-type"
        self.assert_problem("kind_role_conflict", sources)

    def test_projection_target_must_belong_to_exact_lock_terms_used(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["target"] = "http://purl.org/olia/olia.owl#Verb"
        self.assert_problem("unknown_ontology_target", sources)

    def test_projection_lock_must_resolve(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["ontology_lock"] = "missing-lock"
        self.assert_problem("missing_reference", sources)


if __name__ == "__main__":
    unittest.main()
