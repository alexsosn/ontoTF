from __future__ import annotations

import copy
import unittest

from ontotf.semantic_digest_v2 import projection_semantic_digest_v1
from ontotf.source_validation import SourceValidationError, validate_source
from ontotf.semantic_validation import SemanticValidationError, validate_semantic_bundle
from tests.i004.test_mapping_v2_schema import valid_mapping_document
from tests.i004.test_semantic_validation_phase1 import base_sources, bundle


class I004DeclarationContractTests(unittest.TestCase):
    def assert_problem(self, category: str, sources: dict):
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(bundle(sources))
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception.problem

    def declaration(self, *, value_kind: str) -> dict:
        return {
            "ontology_lock_id": "olia-test",
            "ontology_lock_content_digest": "sha256:ontology",
            "rdf_types": ["http://www.w3.org/1999/02/22-rdf-syntax-ns#Property"],
            "domain_iris": ["http://example.org/ontology#Subject"],
            "range_iris": ["http://www.w3.org/2001/XMLSchema#string"],
            "value_kind": value_kind,
        }

    def property_projection(self, *, role: str, value_kind: str) -> dict:
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["target"] = "http://example.org/ontology#property"
        projection["formal_kind"] = "property"
        projection["semantic_role"] = role
        projection["ontology_declaration_evidence"] = self.declaration(value_kind=value_kind)
        sources["locks"][0]["terms_used"].append(projection["target"])
        return sources

    def structural_property_document(self, *, role: str, value_kind: str) -> dict:
        document = valid_mapping_document()
        projection = document["mappings"][0]["projections"][0]
        projection["target"] = "http://example.org/ontology#property"
        projection["formal_kind"] = "property"
        projection["semantic_role"] = role
        projection["ontology_declaration_evidence"] = self.declaration(value_kind=value_kind)
        return document

    def test_declaration_evidence_schema_is_closed(self):
        document = self.structural_property_document(role="attribute", value_kind="literal")
        declaration = document["mappings"][0]["projections"][0]["ontology_declaration_evidence"]
        declaration["unreviewed_guess"] = True
        with self.assertRaises(SourceValidationError):
            validate_source(document, "mapping")

    def test_declaration_evidence_accepts_controlled_locked_facts(self):
        document = self.structural_property_document(role="attribute", value_kind="literal")
        validate_source(document, "mapping")

    def test_declaration_evidence_requires_lock_content_binding(self):
        document = self.structural_property_document(role="attribute", value_kind="literal")
        declaration = document["mappings"][0]["projections"][0]["ontology_declaration_evidence"]
        declaration.pop("ontology_lock_id")
        declaration.pop("ontology_lock_content_digest")
        with self.assertRaises(SourceValidationError):
            validate_source(document, "mapping")

    def test_declaration_lock_id_must_match_projection_lock(self):
        sources = self.property_projection(role="attribute", value_kind="literal")
        declaration = sources["mappings"]["mappings"][0]["projections"][0]["ontology_declaration_evidence"]
        declaration["ontology_lock_id"] = "other-lock"
        self.assert_problem("bundle_closure", sources)

    def test_declaration_lock_digest_must_match_resolved_lock(self):
        sources = self.property_projection(role="attribute", value_kind="literal")
        declaration = sources["mappings"]["mappings"][0]["projections"][0]["ontology_declaration_evidence"]
        declaration["ontology_lock_content_digest"] = "sha256:stale"
        self.assert_problem("bundle_closure", sources)

    def test_untrusted_declaration_is_rejected_before_role_semantics(self):
        sources = self.property_projection(role="relation", value_kind="literal")
        declaration = sources["mappings"]["mappings"][0]["projections"][0]["ontology_declaration_evidence"]
        declaration["ontology_lock_content_digest"] = "sha256:stale"
        self.assert_problem("bundle_closure", sources)

    def test_declaration_binding_is_semantic_digest_input(self):
        sources = self.property_projection(role="attribute", value_kind="literal")
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        before = projection_semantic_digest_v1(projection)
        projection["ontology_declaration_evidence"]["ontology_lock_content_digest"] = "sha256:other"
        after = projection_semantic_digest_v1(projection)
        self.assertNotEqual(before, after)

    def test_declaration_evidence_remains_optional(self):
        validate_semantic_bundle(bundle(base_sources()))

    def test_relation_rejects_explicit_literal_range(self):
        sources = self.property_projection(role="relation", value_kind="literal")
        self.assert_problem("kind_role_conflict", sources)

    def test_attribute_rejects_explicit_resource_range(self):
        sources = self.property_projection(role="attribute", value_kind="resource")
        declaration = sources["mappings"]["mappings"][0]["projections"][0]["ontology_declaration_evidence"]
        declaration["range_iris"] = ["http://example.org/ontology#Entity"]
        self.assert_problem("kind_role_conflict", sources)

    def test_candidate_rejects_explicit_literal_range_for_relation(self):
        sources = self.property_projection(role="relation", value_kind="literal")
        mapping = sources["mappings"]["mappings"][0]
        projection = mapping["projections"].pop()
        mapping["native_state"] = "ambiguous"
        mapping["ambiguous_candidates"] = [{
            "candidate_id": "candidate:property",
            "target": projection["target"],
            "reference_kind": projection["reference_kind"],
            "query_role": projection["query_role"],
            "formal_kind": projection["formal_kind"],
            "semantic_role": projection["semantic_role"],
            "profile_id": projection["profile_id"],
            "capability_id": projection["capability_id"],
            "assessment_candidate": "close",
            "ontology_lock": projection["ontology_lock"],
            "ontology_declaration_evidence": copy.deepcopy(projection["ontology_declaration_evidence"]),
            "evidence": [],
        }]
        self.assert_problem("kind_role_conflict", sources)

    def test_candidate_declaration_binding_has_same_lock_contract(self):
        sources = self.property_projection(role="attribute", value_kind="literal")
        mapping = sources["mappings"]["mappings"][0]
        projection = mapping["projections"].pop()
        candidate = {
            "candidate_id": "candidate:property",
            "target": projection["target"],
            "reference_kind": projection["reference_kind"],
            "query_role": projection["query_role"],
            "formal_kind": projection["formal_kind"],
            "semantic_role": projection["semantic_role"],
            "profile_id": projection["profile_id"],
            "capability_id": projection["capability_id"],
            "assessment_candidate": "close",
            "ontology_lock": projection["ontology_lock"],
            "ontology_declaration_evidence": copy.deepcopy(projection["ontology_declaration_evidence"]),
            "evidence": [],
        }
        candidate["ontology_declaration_evidence"]["ontology_lock_content_digest"] = "sha256:stale"
        mapping["native_state"] = "ambiguous"
        mapping["ambiguous_candidates"] = [candidate]
        self.assert_problem("bundle_closure", sources)

    def test_external_reference_cannot_expose_unbound_child_review(self):
        document = valid_mapping_document()
        mapping = document["mappings"][0]
        mapping["external_references"] = [{
            "reference_id": "ref:locator",
            "reference_kind": "locator",
            "query_role": "explanation-only",
            "external": "https://example.org/source",
            "review": {
                "review_id": "review:reference",
                "status": "reviewed",
                "reviewed_mapping_digest": "sha256:not-validated-here",
                "reviewer_id": "reviewer:test",
                "reviewed_at": "2026-09-08T00:00:00Z",
                "review_source": "test",
                "review_method": "independent-adversarial",
            },
        }]
        with self.assertRaises(SourceValidationError):
            validate_source(document, "mapping")


if __name__ == "__main__":
    unittest.main()
