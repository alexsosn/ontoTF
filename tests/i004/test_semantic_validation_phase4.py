from __future__ import annotations

import copy
import unittest

from ontotf.semantic_validation import SemanticValidationError, validate_semantic_bundle
from tests.i004.test_semantic_validation_phase1 import base_sources, bundle


def approximation(*, eligible: bool, losses: list[str]) -> dict:
    return {
        "status": "reviewed",
        "eligible": eligible,
        "losses": losses,
        "rationale": "reviewed approximation contract",
        "review_id": "review:approx",
    }


class I004Phase4Tests(unittest.TestCase):
    def assert_problem(self, category: str, sources: dict):
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(bundle(sources))
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception.problem

    def test_broader_reviewed_approximation_requires_undercoverage(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["assessment"] = "broader"
        projection["approximation"] = approximation(eligible=True, losses=["overcoverage"])
        self.assert_problem("invalid_approximation", sources)

    def test_narrower_reviewed_approximation_requires_overcoverage(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["assessment"] = "narrower"
        projection["approximation"] = approximation(eligible=True, losses=["undercoverage"])
        self.assert_problem("invalid_approximation", sources)

    def test_close_eligible_requires_nonempty_reviewed_losses(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["assessment"] = "close"
        projection["approximation"] = approximation(eligible=True, losses=[])
        self.assert_problem("invalid_approximation", sources)

    def test_unknown_loss_token_fails_closed(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["assessment"] = "broader"
        projection["approximation"] = approximation(eligible=True, losses=["future-loss"])
        self.assert_problem("unknown_vocabulary", sources)

    def test_truthy_non_boolean_eligibility_fails_closed(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["assessment"] = "broader"
        projection["approximation"] = {
            "status": "reviewed",
            "eligible": 1,
            "losses": ["undercoverage"],
            "rationale": "truthiness is forbidden",
            "review_id": "review:approx",
        }
        self.assert_problem("invalid_approximation", sources)

    def test_related_cannot_carry_approximation_even_when_ineligible(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["assessment"] = "related"
        projection["approximation"] = approximation(eligible=False, losses=[])
        self.assert_problem("invalid_approximation", sources)

    def test_exact_cannot_carry_approximation_even_when_ineligible(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["assessment"] = "exact"
        projection["approximation"] = approximation(eligible=False, losses=[])
        self.assert_problem("invalid_approximation", sources)

    def test_valid_broader_approximation_contract_is_structurally_accepted(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["assessment"] = "broader"
        projection["approximation"] = approximation(eligible=True, losses=["undercoverage"])
        validate_semantic_bundle(bundle(sources))

    def test_class_equivalent_property_publication_fails(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["formal_kind"] = "class"
        projection["publication_relation"] = "http://www.w3.org/2002/07/owl#equivalentProperty"
        self.assert_problem("invalid_publication_relation", sources)

    def test_class_equivalent_class_publication_is_accepted(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["publication_relation"] = "http://www.w3.org/2002/07/owl#equivalentClass"
        validate_semantic_bundle(bundle(sources))

    def test_skos_mapping_relation_requires_skos_concept(self):
        sources = base_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["publication_relation"] = "http://www.w3.org/2004/02/skos/core#exactMatch"
        self.assert_problem("invalid_publication_relation", sources)

    def test_external_reference_wrong_routing_fails(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["external_references"] = [
            {
                "reference_id": "ref:entity",
                "reference_kind": "entity-identity",
                "query_role": "identifier-filter",
                "external": "https://example.org/entity/1",
                "authority_system": "example",
                "identity_strength": "same-entity",
                "native_binding": {"component_id": "test-tf", "node_type": "word"},
            }
        ]
        self.assert_problem("invalid_reference_routing", sources)

    def test_external_reference_cannot_leak_target_projection_fields(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["external_references"] = [
            {
                "reference_id": "ref:locator",
                "reference_kind": "locator",
                "query_role": "explanation-only",
                "external": "https://example.org/record/1",
                "target": "http://purl.org/olia/olia.owl#Noun",
            }
        ]
        self.assert_problem("invalid_reference_routing", sources)

    def test_entity_identity_same_as_requires_same_entity_strength(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["external_references"] = [
            {
                "reference_id": "ref:entity",
                "reference_kind": "entity-identity",
                "query_role": "identity-filter",
                "external": "https://example.org/entity/1",
                "authority_system": "example",
                "identity_strength": "probable-same-entity",
                "native_binding": {"component_id": "test-tf", "node_type": "word"},
                "publication_relation": "http://www.w3.org/2002/07/owl#sameAs",
            }
        ]
        self.assert_problem("invalid_publication_relation", sources)

    def test_entity_identity_same_as_is_accepted_for_same_entity(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["external_references"] = [
            {
                "reference_id": "ref:entity",
                "reference_kind": "entity-identity",
                "query_role": "identity-filter",
                "external": "https://example.org/entity/1",
                "authority_system": "example",
                "identity_strength": "same-entity",
                "native_binding": {"component_id": "test-tf", "node_type": "word"},
                "publication_relation": "http://www.w3.org/2002/07/owl#sameAs",
            }
        ]
        validate_semantic_bundle(bundle(sources))

    def test_catalogue_identifier_requires_issuer_scope(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["external_references"] = [
            {
                "reference_id": "ref:cat",
                "reference_kind": "catalogue-identifier",
                "query_role": "identifier-filter",
                "external": "ABC-1",
                "native_binding": {"component_id": "test-tf", "feature": "catalogue_id"},
            }
        ]
        self.assert_problem("invalid_reference_routing", sources)


if __name__ == "__main__":
    unittest.main()
