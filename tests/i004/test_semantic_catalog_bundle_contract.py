from __future__ import annotations

import copy
import unittest

from ontotf.source_validation import SourceValidationError, validate_source
from ontotf.semantic_validation import SemanticArtifact, SemanticSourceBundle, SemanticValidationError, validate_semantic_bundle
from tests.i004.test_semantic_bundle_closure import bundle_sources, semantic_bundle
from tests.i004.test_semantic_validation_phase1 import base_sources, bundle


def catalog_sources() -> dict:
    sources = base_sources()
    sources["profile"]["profile_catalog_version"] = 1
    sources["profile"]["profiles"] = ["linguistic"]
    sources["profile"]["capabilities"] = ["linguistic.part-of-speech"]
    return sources


class I004CatalogBundleContractTests(unittest.TestCase):
    def assert_problem(self, category: str, semantic_bundle_value: SemanticSourceBundle):
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(semantic_bundle_value)
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception.problem

    def test_profile_schema_accepts_controlled_catalog_declarations(self):
        validate_source(catalog_sources()["profile"], "profile")

    def test_missing_profile_catalog_version_fails_closed(self):
        sources = base_sources()
        sources["profile"].pop("profile_catalog_version")
        self.assert_problem("unsupported_contract_version", bundle(sources))

    def test_mapping_profile_must_be_declared_by_profile_artifact(self):
        sources = catalog_sources()
        sources["profile"]["profiles"] = ["lexical"]
        self.assert_problem("unknown_vocabulary", bundle(sources))

    def test_mapping_capability_must_be_declared_by_profile_artifact(self):
        sources = catalog_sources()
        sources["profile"]["capabilities"] = ["linguistic.morphology"]
        self.assert_problem("unknown_vocabulary", bundle(sources))

    def test_projection_profile_and_capability_must_belong_to_mapping_declarations(self):
        sources = catalog_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["profiles"] = ["linguistic", "lexical"]
        mapping["capabilities"] = ["linguistic.part-of-speech", "lexical.entry"]
        projection = mapping["projections"][0]
        projection["profile_id"] = "lexical"
        projection["capability_id"] = "lexical.entry"
        sources["profile"]["profiles"].append("lexical")
        sources["profile"]["capabilities"].append("lexical.entry")
        # Remove the projection declarations from the mapping while leaving them catalog-valid.
        mapping["profiles"] = ["linguistic"]
        mapping["capabilities"] = ["linguistic.part-of-speech"]
        self.assert_problem("invalid_projection", bundle(sources))

    def test_capability_prefix_must_match_projection_profile(self):
        sources = catalog_sources()
        sources["profile"]["profiles"].append("lexical")
        sources["profile"]["capabilities"].append("lexical.entry")
        mapping = sources["mappings"]["mappings"][0]
        mapping["profiles"].append("lexical")
        mapping["capabilities"].append("lexical.entry")
        projection = mapping["projections"][0]
        projection["profile_id"] = "linguistic"
        projection["capability_id"] = "lexical.entry"
        self.assert_problem("invalid_projection", bundle(sources))

    def test_mapping_schema_closes_ontology_bundle_requirement_shape(self):
        sources = catalog_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["ontology_bundle_requirement"] = {
            "bundle_digest": "sha256:" + "a" * 64,
            "required_profile_contracts": ["profile:linguistic-v1"],
            "unexpected": True,
        }
        with self.assertRaises(SourceValidationError):
            validate_source(sources["mappings"], "mapping")

    def test_projection_bundle_requirement_digest_must_match_validated_bundle(self):
        sources = bundle_sources()
        sources["profile"]["profile_catalog_version"] = 1
        sources["profile"]["profiles"] = ["linguistic"]
        sources["profile"]["capabilities"] = ["linguistic.part-of-speech"]
        sources["mappings"]["mappings"][0]["projections"][0]["ontology_bundle_requirement"] = {
            "bundle_digest": "sha256:" + "f" * 64,
            "required_profile_contracts": ["profile:lexical-v1"],
        }
        self.assert_problem("bundle_closure", semantic_bundle(sources))


if __name__ == "__main__":
    unittest.main()
