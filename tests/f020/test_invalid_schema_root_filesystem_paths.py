from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ontotf.source_validation import SCHEMA_FILES, SourceValidationError, validate_source

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "src" / "ontotf" / "schemas"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


class InvalidSchemaRootFilesystemPathControls(unittest.TestCase):
    def assert_invalid_schema(self, root: str | Path) -> SourceValidationError:
        with self.assertRaises(SourceValidationError) as raised:
            validate_source({}, "profile", schema_root=root)
        self.assertEqual(raised.exception.problem.category, "invalid_schema")
        self.assertEqual(
            raised.exception.problem.source_name,
            str(Path(root) / SCHEMA_FILES["profile"]),
        )
        return raised.exception

    def test_missing_explicit_schema_remains_invalid_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "missing-root"
            self.assert_invalid_schema(root)

    def test_invalid_utf8_explicit_schema_remains_invalid_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / SCHEMA_FILES["profile"]).write_bytes(b"\xff")
            self.assert_invalid_schema(root)

    def test_malformed_json_explicit_schema_remains_invalid_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / SCHEMA_FILES["profile"]).write_text("{", encoding="utf-8")
            self.assert_invalid_schema(root)

    def test_invalid_draft_schema_remains_invalid_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / SCHEMA_FILES["profile"]).write_text(
                json.dumps({"$schema": DRAFT_2020_12, "type": 42}),
                encoding="utf-8",
            )
            self.assert_invalid_schema(root)

    def test_valid_explicit_schema_root_reaches_instance_validation(self):
        with self.assertRaises(SourceValidationError) as raised:
            validate_source({}, "profile", schema_root=SCHEMA_ROOT)
        self.assertEqual(raised.exception.problem.category, "schema_validation")
        self.assertEqual(raised.exception.problem.source_name, "profile")

    def test_packaged_schema_loading_reaches_instance_validation(self):
        with self.assertRaises(SourceValidationError) as raised:
            validate_source({}, "profile")
        self.assertEqual(raised.exception.problem.category, "schema_validation")
        self.assertEqual(raised.exception.problem.source_name, "profile")

    def test_out_of_contract_schema_root_type_is_not_reclassified(self):
        with self.assertRaises(TypeError):
            validate_source({}, "profile", schema_root=object())  # type: ignore[arg-type]


class InvalidSchemaRootFilesystemPathREDTests(unittest.TestCase):
    def invalid_root(self) -> str:
        return "bad\0schema-root"

    def expected_source_name(self) -> str:
        return str(Path(self.invalid_root()) / SCHEMA_FILES["profile"])

    def test_embedded_nul_explicit_schema_root_is_typed_invalid_schema(self):
        with self.assertRaises(SourceValidationError) as raised:
            validate_source({}, "profile", schema_root=self.invalid_root())
        self.assertEqual(raised.exception.problem.category, "invalid_schema")
        self.assertEqual(raised.exception.problem.source_name, self.expected_source_name())

    def test_invalid_schema_path_precedes_direct_instance_preflight(self):
        malformed_instance = {1: "non-string key"}  # type: ignore[dict-item]
        with self.assertRaises(SourceValidationError) as raised:
            validate_source(
                malformed_instance,  # type: ignore[arg-type]
                "profile",
                schema_root=self.invalid_root(),
                source_name="authored-instance",
            )
        self.assertEqual(raised.exception.problem.category, "invalid_schema")
        self.assertEqual(raised.exception.problem.source_name, self.expected_source_name())

    def test_embedded_nul_provenance_is_exact_not_normalized(self):
        authored = "parent/../bad\0schema-root"
        expected = str(Path(authored) / SCHEMA_FILES["profile"])
        with self.assertRaises(SourceValidationError) as raised:
            validate_source({}, "profile", schema_root=authored)
        self.assertEqual(raised.exception.problem.category, "invalid_schema")
        self.assertEqual(raised.exception.problem.source_name, expected)


if __name__ == "__main__":
    unittest.main()
