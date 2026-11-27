from __future__ import annotations

import math
from pathlib import Path
import tempfile
import unittest

from ontotf.source_validation import MAX_SOURCE_NESTING, SourceValidationError, validate_source


def normalized_evidence(reviewed_content):
    return {
        "evidence_id": "evidence:test",
        "kind": "native-doc",
        "source_uri": "https://example.org/native-doc",
        "content_mode": "normalized-record",
        "reviewed_content": reviewed_content,
        "content_digest": "sha256:evidence",
    }


def nested_dict_chain(container_count: int):
    value = "leaf"
    for _ in range(container_count):
        value = {"next": value}
    return value


class DirectValidationSourceBoundaryTests(unittest.TestCase):
    def assert_category(self, expected: str, data, *, source_name: str = "direct.evidence.json") -> SourceValidationError:
        with self.assertRaises(SourceValidationError) as raised:
            validate_source(data, "evidence", source_name=source_name)
        self.assertEqual(raised.exception.problem.category, expected)
        return raised.exception

    def test_public_source_nesting_contract_is_128(self):
        self.assertEqual(MAX_SOURCE_NESTING, 128)

    def test_direct_total_depth_128_is_accepted(self):
        # Evidence root is depth 1; reviewed_content contributes 127 containers.
        validate_source(normalized_evidence(nested_dict_chain(MAX_SOURCE_NESTING - 1)), "evidence")

    def test_direct_total_depth_129_is_rejected_before_schema_validation(self):
        error = self.assert_category(
            "decode_error",
            normalized_evidence(nested_dict_chain(MAX_SOURCE_NESTING)),
            source_name="deep-direct.json",
        )
        self.assertEqual(error.problem.source_name, "deep-direct.json")
        self.assertIn("source nesting exceeds maximum depth 128", error.problem.message)
        self.assertEqual(error.problem.instance_path, ())
        self.assertEqual(error.problem.schema_path, ())

    def test_direct_recursive_dict_alias_is_non_json_value(self):
        recursive = {}
        recursive["self"] = recursive
        error = self.assert_category("non_json_value", normalized_evidence(recursive))
        self.assertIn("recursive container alias", error.problem.message)

    def test_direct_recursive_list_alias_is_non_json_value(self):
        recursive = []
        recursive.append(recursive)
        error = self.assert_category("non_json_value", normalized_evidence(recursive))
        self.assertIn("recursive container alias", error.problem.message)

    def test_direct_non_string_nested_key_is_non_json_value(self):
        error = self.assert_category("non_json_value", normalized_evidence({1: "value"}))
        self.assertIn("mapping keys must be strings", error.problem.message)

    def test_direct_non_finite_nested_float_is_non_json_value(self):
        error = self.assert_category("non_json_value", normalized_evidence({"value": math.nan}))
        self.assertIn("non-finite numeric value", error.problem.message)

    def test_direct_unsupported_nested_value_is_non_json_value(self):
        error = self.assert_category("non_json_value", normalized_evidence({"value": (1, 2)}))
        self.assertIn("unsupported value type: tuple", error.problem.message)

    def test_shallow_valid_normalized_evidence_remains_valid(self):
        validate_source(normalized_evidence({"statement": "reviewed"}), "evidence", source_name="shallow.json")

    def test_shallow_schema_error_keeps_paths_and_provenance(self):
        data = normalized_evidence({"statement": "reviewed"})
        del data["evidence_id"]
        error = self.assert_category("schema_validation", data, source_name="broken.json")
        self.assertEqual(error.problem.source_name, "broken.json")
        self.assertEqual(error.problem.instance_path, ())
        self.assertTrue(error.problem.schema_path)

    def test_default_source_identity_remains_schema_name(self):
        data = normalized_evidence({"statement": "reviewed"})
        del data["evidence_id"]
        with self.assertRaises(SourceValidationError) as raised:
            validate_source(data, "evidence")
        self.assertEqual(raised.exception.problem.category, "schema_validation")
        self.assertEqual(raised.exception.problem.source_name, "evidence")

    def test_invalid_schema_precedes_direct_source_preflight(self):
        recursive = {}
        recursive["self"] = recursive
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            schema_path = root / "evidence.schema.json"
            schema_path.write_text(
                '{"$schema":"https://json-schema.org/draft/2020-12/schema","type":42}',
                encoding="utf-8",
            )
            with self.assertRaises(SourceValidationError) as raised:
                validate_source(
                    normalized_evidence(recursive),
                    "evidence",
                    schema_root=root,
                    source_name="bad-instance.json",
                )
        self.assertEqual(raised.exception.problem.category, "invalid_schema")
        self.assertEqual(raised.exception.problem.source_name, str(schema_path))


if __name__ == "__main__":
    unittest.main()
