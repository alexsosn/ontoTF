from __future__ import annotations

import unittest

from ontotf.semantic_digest_v2 import mapping_semantic_digest_v2, projection_semantic_digest_v1
from ontotf.semantic_ir import compile_semantic_ir
from ontotf.semantic_validation import validate_semantic_bundle
from tests.i005._fixtures import noun_sources, source_bundle, validate_structural_sources

OWL_CLASS = "http://www.w3.org/2002/07/owl#Class"
OWL_EQUIVALENT_CLASS = "http://www.w3.org/2002/07/owl#equivalentClass"


class I005SemanticIRMetadataContractTests(unittest.TestCase):
    def test_projection_declaration_and_publication_metadata_survive_compilation(self):
        sources = noun_sources("metadata", parent_char="a")
        lock = sources["locks"][0]
        mapping = sources["mappings"]["mappings"][0]
        projection = mapping["projections"][0]
        projection["ontology_declaration_evidence"] = {
            "ontology_lock_id": lock["lock_id"],
            "ontology_lock_content_digest": lock["content_digest"],
            "rdf_types": [OWL_CLASS],
            "value_kind": "resource",
        }
        projection["publication_relation"] = OWL_EQUIVALENT_CLASS
        projection["projection_semantic_digest"] = projection_semantic_digest_v1(projection)
        projection["review"]["reviewed_mapping_digest"] = projection["projection_semantic_digest"]
        mapping["mapping_semantic_digest"] = mapping_semantic_digest_v2(mapping)
        mapping["review"]["reviewed_mapping_digest"] = mapping["mapping_semantic_digest"]
        validate_structural_sources(sources)
        validated = validate_semantic_bundle(source_bundle(sources))

        row = next(iter(compile_semantic_ir((validated,)).semantic_index))[1][0]
        self.assertEqual(row.publication_relation, OWL_EQUIVALENT_CLASS)
        self.assertIsNotNone(row.ontology_declaration_evidence)
        self.assertEqual(row.ontology_declaration_evidence.ontology_lock_id, lock["lock_id"])
        self.assertEqual(row.ontology_declaration_evidence.rdf_types, (OWL_CLASS,))
        self.assertEqual(row.ontology_declaration_evidence.value_kind, "resource")


if __name__ == "__main__":
    unittest.main()
