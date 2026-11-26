from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ontotf.source_validation import SourceValidationError, load_and_validate, load_source


class InvalidSourceFilesystemPathControls(unittest.TestCase):
    def assert_load_error(self, path: str | Path) -> SourceValidationError:
        with self.assertRaises(SourceValidationError) as raised:
            load_source(path)
        self.assertEqual(raised.exception.problem.category, "decode_error")
        self.assertEqual(raised.exception.problem.source_name, str(Path(path)))
        return raised.exception

    def test_missing_json_preserves_file_error_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            error = self.assert_load_error(path)
        self.assertNotIn("unsupported source suffix", error.problem.message)

    def test_invalid_utf8_json_remains_decode_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.json"
            path.write_bytes(b"\xff")
            error = self.assert_load_error(path)
        self.assertNotIn("unsupported source suffix", error.problem.message)

    def test_readable_valid_utf8_txt_reaches_suffix_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.txt"
            path.write_text("plain text\n", encoding="utf-8")
            error = self.assert_load_error(path)
        self.assertIn("unsupported source suffix: .txt", error.problem.message)

    def test_missing_txt_fails_before_suffix_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.txt"
            error = self.assert_load_error(path)
        self.assertNotIn("unsupported source suffix", error.problem.message)

    def test_invalid_utf8_txt_fails_before_suffix_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.txt"
            path.write_bytes(b"\xff")
            error = self.assert_load_error(path)
        self.assertNotIn("unsupported source suffix", error.problem.message)

    def test_valid_json_and_yaml_load_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_path = root / "source.json"
            yaml_path = root / "source.yaml"
            json_path.write_text('{"a": 1}\n', encoding="utf-8")
            yaml_path.write_text("a: 1\n", encoding="utf-8")
            self.assertEqual(load_source(json_path), {"a": 1})
            self.assertEqual(load_source(yaml_path), {"a": 1})

    def test_out_of_contract_input_type_is_not_reclassified(self):
        with self.assertRaises(TypeError):
            load_source(object())  # type: ignore[arg-type]


class InvalidSourceFilesystemPathREDTests(unittest.TestCase):
    def assert_embedded_nul_is_contained(self, suffix: str) -> None:
        authored_path = "bad\0" + suffix
        with self.assertRaises(SourceValidationError) as raised:
            load_source(authored_path)
        self.assertEqual(raised.exception.problem.category, "decode_error")
        self.assertEqual(raised.exception.problem.source_name, str(Path(authored_path)))

    def test_embedded_nul_json_is_typed_decode_error(self):
        self.assert_embedded_nul_is_contained(".json")

    def test_embedded_nul_yaml_is_typed_decode_error(self):
        self.assert_embedded_nul_is_contained(".yaml")

    def test_embedded_nul_yml_is_typed_decode_error(self):
        self.assert_embedded_nul_is_contained(".yml")

    def test_load_and_validate_propagates_typed_invalid_path_error(self):
        authored_path = "bad\0.json"
        with self.assertRaises(SourceValidationError) as raised:
            load_and_validate(authored_path, "profile")
        self.assertEqual(raised.exception.problem.category, "decode_error")
        self.assertEqual(raised.exception.problem.source_name, str(Path(authored_path)))


if __name__ == "__main__":
    unittest.main()
