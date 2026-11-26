from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ontotf.source_validation import (  # noqa: E402
    SCHEMA_FILES,
    SourceValidationError,
    load_and_validate,
    load_source,
    validate_source,
)

SCHEMA_ROOT = ROOT / "src" / "ontotf" / "schemas"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


def invalid_profile() -> dict:
    return {
        "schema_version": "one",
        "profile_id": "ontotf-test",
        "profile_version": "0.2.0",
        "semantic_domains": ["morphology"],
        "parent_component_manifest": "parent/expected-components.json",
        "required_components": ["test-tf"],
        "ontology_locks": ["olia-test"],
        "mapping_sources": ["mappings/test.yaml"],
        "dependency_contract_version": 1,
        "dependencies": [
            {
                "dependency_id": "dep:test",
                "component_id": "test-tf",
                "kind": "component-present",
                "assertion": {},
            }
        ],
        "minimum_ontotf_runtime": "0.1.0",
        "license": "CC-BY-4.0",
    }


class SourceDiagnosticProvenanceTests(unittest.TestCase):
    def test_file_backed_schema_failure_names_source_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            path.write_text(json.dumps(invalid_profile()), encoding="utf-8")

            with self.assertRaises(SourceValidationError) as raised:
                load_and_validate(path, "profile", schema_root=SCHEMA_ROOT)

            problem = raised.exception.problem
            self.assertEqual(problem.category, "schema_validation")
            self.assertEqual(problem.source_name, str(path))
            self.assertIn("schema_version", problem.instance_path)
            self.assertTrue(problem.schema_path)

    def test_direct_validation_keeps_schema_name_as_default_identity(self):
        with self.assertRaises(SourceValidationError) as raised:
            validate_source(invalid_profile(), "profile", schema_root=SCHEMA_ROOT)

        problem = raised.exception.problem
        self.assertEqual(problem.category, "schema_validation")
        self.assertEqual(problem.source_name, "profile")
        self.assertIn("schema_version", problem.instance_path)
        self.assertTrue(problem.schema_path)

    def test_invalid_schema_failure_still_names_schema_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            schema_path = root / SCHEMA_FILES["profile"]
            schema_path.write_text(
                json.dumps({"$schema": DRAFT_2020_12, "type": 42}),
                encoding="utf-8",
            )

            with self.assertRaises(SourceValidationError) as raised:
                validate_source(invalid_profile(), "profile", schema_root=root)

        problem = raised.exception.problem
        self.assertEqual(problem.category, "invalid_schema")
        self.assertEqual(problem.source_name, str(schema_path))

    def test_decode_failure_still_names_source_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            path.write_bytes(b"\xff")

            with self.assertRaises(SourceValidationError) as raised:
                load_source(path)

        problem = raised.exception.problem
        self.assertEqual(problem.category, "decode_error")
        self.assertEqual(problem.source_name, str(path))


if __name__ == "__main__":
    unittest.main()
