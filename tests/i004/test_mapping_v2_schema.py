from __future__ import annotations

import copy
import unittest

from ontotf.source_validation import SourceValidationError, validate_source
from tests.i004.test_semantic_validation_phase1 import base_sources


def review() -> dict:
    return {
        "review_id": "review:test",
        "status": "reviewed",
        "reviewed_mapping_digest": "sha256:placeholder",
        "reviewer_id": "reviewer:test",
        "reviewed_at": "2026-09-08T00:00:00Z",
        "review_source": "test",
        "review_method": "independent-adversarial",
    }


def valid_mapping_document() -> dict:
    mapping = copy.deepcopy(base_sources()["mappings"]["mappings"][0])
    mapping["review"] = review()
    mapping["projections"][0]["review"] = review()
    return {"schema_version": 2, "mappings": [mapping]}


class MappingV2SchemaTests(unittest.TestCase):
    def assert_invalid(self, document: dict):
        with self.assertRaises(SourceValidationError) as raised:
            validate_source(document, "mapping")
        self.assertEqual(raised.exception.problem.category, "schema_validation")

    def test_mapping_v2_document_is_structurally_valid(self):
        validate_source(valid_mapping_document(), "mapping")

    def test_legacy_schema_version_one_is_rejected(self):
        document = valid_mapping_document()
        document["schema_version"] = 1
        self.assert_invalid(document)

    def test_legacy_single_target_fields_are_rejected(self):
        document = valid_mapping_document()
        mapping = document["mappings"][0]
        mapping["external_target"] = mapping["projections"][0]["target"]
        mapping["assessment"] = "exact"
        mapping["ontology_lock"] = "olia-test"
        mapping["candidate_projections"] = []
        self.assert_invalid(document)

    def test_positive_requires_projection_or_external_reference(self):
        document = valid_mapping_document()
        mapping = document["mappings"][0]
        mapping["projections"] = []
        self.assert_invalid(document)
        mapping["external_references"] = [
            {
                "reference_id": "ref:locator",
                "reference_kind": "locator",
                "query_role": "explanation-only",
                "external": "https://example.org/record/1",
            }
        ]
        validate_source(document, "mapping")

    def test_native_only_requires_zero_targets_and_candidates(self):
        document = valid_mapping_document()
        mapping = document["mappings"][0]
        mapping["native_state"] = "native-only"
        self.assert_invalid(document)
        mapping["projections"] = []
        validate_source(document, "mapping")

    def test_ambiguous_requires_typed_candidate_and_zero_projection(self):
        document = valid_mapping_document()
        mapping = document["mappings"][0]
        projection = mapping["projections"].pop()
        mapping["native_state"] = "ambiguous"
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
                "evidence": [],
            }
        ]
        validate_source(document, "mapping")

    def test_opaque_ambiguous_candidate_is_rejected(self):
        document = valid_mapping_document()
        mapping = document["mappings"][0]
        mapping["native_state"] = "ambiguous"
        mapping["projections"] = []
        mapping["ambiguous_candidates"] = [
            {"candidate_id": "candidate:noun", "target": "https://example.org/noun"}
        ]
        self.assert_invalid(document)

    def test_projection_routing_tokens_are_closed(self):
        document = valid_mapping_document()
        document["mappings"][0]["projections"][0]["reference_kind"] = "external"
        self.assert_invalid(document)

    def test_external_reference_cannot_be_target_bearing(self):
        document = valid_mapping_document()
        document["mappings"][0]["external_references"] = [
            {
                "reference_id": "ref:locator",
                "reference_kind": "locator",
                "query_role": "explanation-only",
                "external": "https://example.org/record/1",
                "target": "https://example.org/term",
            }
        ]
        self.assert_invalid(document)

    def test_approximation_loss_tokens_are_closed(self):
        document = valid_mapping_document()
        projection = document["mappings"][0]["projections"][0]
        projection["assessment"] = "broader"
        projection["approximation"] = {
            "status": "reviewed",
            "eligible": True,
            "losses": ["future-loss"],
            "rationale": "fixture",
            "review_id": "review:approx",
        }
        self.assert_invalid(document)


if __name__ == "__main__":
    unittest.main()
