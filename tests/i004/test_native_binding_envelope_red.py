from __future__ import annotations

import unittest

from ontotf.source_validation import SourceValidationError, validate_source
from tests.i004.test_mapping_v2_schema import valid_mapping_document


class NativeBindingEnvelopeRedTests(unittest.TestCase):
    def assert_invalid(self, document: dict) -> None:
        with self.assertRaises(SourceValidationError) as raised:
            validate_source(document, "mapping")
        self.assertEqual(raised.exception.problem.category, "schema_validation")

    def test_mapping_native_binding_rejects_sidecar_selector(self):
        document = valid_mapping_document()
        document["mappings"][0]["native_binding"] = {
            "component_id": "test-tf",
            "sidecar_path": "records.sqlite",
        }
        self.assert_invalid(document)

    def test_projection_execution_binding_rejects_backend_selector(self):
        document = valid_mapping_document()
        document["mappings"][0]["projections"][0]["native_execution_binding"] = {
            "component_id": "test-tf",
            "database": "postgres://example",
        }
        self.assert_invalid(document)

    def test_external_reference_native_binding_rejects_source_file_selector(self):
        document = valid_mapping_document()
        document["mappings"][0]["external_references"] = [
            {
                "reference_id": "ref:entity",
                "reference_kind": "entity-identity",
                "query_role": "identity-filter",
                "external": "https://example.org/entity/1",
                "authority_system": "example",
                "identity_strength": "same-entity",
                "native_binding": {
                    "component_id": "test-tf",
                    "file_path": "raw/source.json",
                },
            }
        ]
        self.assert_invalid(document)

    def test_tf_native_binding_shapes_remain_valid(self):
        document = valid_mapping_document()
        validate_source(document, "mapping")


if __name__ == "__main__":
    unittest.main()
