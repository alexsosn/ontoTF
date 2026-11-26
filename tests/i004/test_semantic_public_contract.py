from __future__ import annotations

import unittest

import ontotf
import ontotf.digests as digests
import ontotf.semantic_vocabulary as semantic_vocabulary
from ontotf.semantic_validation import SemanticValidationError, validate_semantic_bundle
from tests.i004.test_semantic_validation_phase1 import base_sources, bundle as phase1_bundle
from tests.i004.test_semantic_validation_phase3 import bundle, reviewed_sources


FROZEN_I004_CATEGORIES = frozenset(
    {
        "unsupported_contract_version",
        "duplicate_id",
        "missing_reference",
        "component_authority",
        "unknown_vocabulary",
        "invalid_record_state",
        "invalid_projection",
        "invalid_candidate",
        "invalid_reference_routing",
        "kind_role_conflict",
        "unknown_ontology_target",
        "bundle_closure",
        "bridge_closure",
        "evidence_digest_mismatch",
        "stale_semantic_digest",
        "stale_review_binding",
        "native_semantics_unproven",
        "invalid_approximation",
        "invalid_publication_relation",
    }
)


class I004PublicContractTests(unittest.TestCase):
    def test_mapping_v2_digest_api_is_available_from_ontotf_digests(self):
        self.assertEqual(
            getattr(digests, "MAPPING_SEMANTIC_ALGORITHM_V2", None),
            "tfont-mapping-semantic-sha256-v2",
        )
        self.assertTrue(callable(getattr(digests, "mapping_semantic_digest_v2", None)))

    def test_projection_digest_api_uses_planned_public_name(self):
        self.assertEqual(
            getattr(digests, "PROJECTION_SEMANTIC_ALGORITHM", None),
            "tfont-projection-semantic-sha256-v1",
        )
        self.assertTrue(callable(getattr(digests, "projection_semantic_digest_v1", None)))

    def test_package_root_exports_i004_validator_surface(self):
        for name in (
            "SemanticArtifact",
            "SemanticSourceBundle",
            "SemanticValidationProblem",
            "SemanticValidationError",
            "SemanticIndexes",
            "ValidatedSemanticBundle",
            "validate_semantic_bundle",
        ):
            self.assertTrue(hasattr(ontotf, name), name)

    def test_production_exposes_exact_frozen_diagnostic_categories(self):
        self.assertEqual(
            getattr(semantic_vocabulary, "SEMANTIC_VALIDATION_CATEGORIES", None),
            FROZEN_I004_CATEGORIES,
        )

    def test_structurally_valid_external_reference_envelope_uses_frozen_category(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["external_references"] = [
            {
                "reference_id": "ref:provenance",
                "reference_kind": "provenance-source",
                "query_role": "metadata-filter",
                "external": "https://example.org/source",
            }
        ]
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(phase1_bundle(sources))
        self.assertEqual(raised.exception.problem.category, "invalid_reference_routing")

    def test_stale_mapping_digest_uses_frozen_category(self):
        sources = reviewed_sources()
        sources["mappings"]["mappings"][0]["native_binding"]["node_type"] = "phrase"
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(bundle(sources))
        self.assertEqual(raised.exception.problem.category, "stale_semantic_digest")

    def test_stale_review_binding_uses_frozen_category(self):
        sources = reviewed_sources()
        sources["mappings"]["mappings"][0]["review"]["reviewed_mapping_digest"] = "sha256:stale"
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(bundle(sources))
        self.assertEqual(raised.exception.problem.category, "stale_review_binding")


if __name__ == "__main__":
    unittest.main()
