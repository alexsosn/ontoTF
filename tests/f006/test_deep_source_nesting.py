from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import ontotf.source_validation as source_validation  # noqa: E402
from ontotf.source_validation import SourceValidationError, loads_source  # noqa: E402

LIMIT = 128


def nested_flow_sequence(depth: int, scalar: str = "0") -> str:
    return "[" * depth + scalar + "]" * depth


class DeepSourceNestingTests(unittest.TestCase):
    def assert_depth_error(self, text: str, *, format: str, source_name: str):
        with self.assertRaises(SourceValidationError) as raised:
            loads_source(text, format=format, source_name=source_name)
        problem = raised.exception.problem
        self.assertEqual(problem.category, "decode_error")
        self.assertEqual(problem.source_name, source_name)
        self.assertEqual(
            problem.message,
            f"source nesting exceeds maximum depth {LIMIT}",
        )

    def test_public_limit_is_pinned(self):
        self.assertEqual(source_validation.MAX_SOURCE_NESTING, LIMIT)

    def test_json_boundary_accepts_limit(self):
        result = loads_source(nested_flow_sequence(LIMIT), format="json")
        for _ in range(LIMIT):
            self.assertIsInstance(result, list)
            result = result[0]
        self.assertEqual(result, 0)

    def test_json_boundary_rejects_limit_plus_one(self):
        self.assert_depth_error(
            nested_flow_sequence(LIMIT + 1),
            format="json",
            source_name="deep.json",
        )

    def test_yaml_boundary_accepts_limit(self):
        result = loads_source(nested_flow_sequence(LIMIT), format="yaml")
        for _ in range(LIMIT):
            self.assertIsInstance(result, list)
            result = result[0]
        self.assertEqual(result, 0)

    def test_yaml_boundary_rejects_limit_plus_one(self):
        self.assert_depth_error(
            nested_flow_sequence(LIMIT + 1),
            format="yaml",
            source_name="deep.yaml",
        )

    def test_extreme_json_never_leaks_recursion_error(self):
        self.assert_depth_error(
            nested_flow_sequence(4000),
            format="json",
            source_name="extreme.json",
        )

    def test_extreme_yaml_never_leaks_recursion_error(self):
        self.assert_depth_error(
            nested_flow_sequence(4000),
            format="yaml",
            source_name="extreme.yaml",
        )

    def test_moderate_nested_values_are_unchanged(self):
        json_value = loads_source('[[{"x": [1, true, null, "text"]}]]', format="json")
        yaml_value = loads_source('[[{x: [1, true, null, text]}]]', format="yaml")
        expected = [[{"x": [1, True, None, "text"]}]]
        self.assertEqual(json_value, expected)
        self.assertEqual(yaml_value, expected)

    def test_duplicate_key_categories_are_unchanged(self):
        for format, text in (
            ("json", '{"a": 1, "a": 2}'),
            ("yaml", "a: 1\na: 2\n"),
        ):
            with self.subTest(format=format), self.assertRaises(SourceValidationError) as raised:
                loads_source(text, format=format)
            self.assertEqual(raised.exception.problem.category, "duplicate_key")

    def test_non_finite_categories_are_unchanged(self):
        with self.assertRaises(SourceValidationError) as json_raised:
            loads_source('{"x": NaN}', format="json")
        self.assertEqual(json_raised.exception.problem.category, "decode_error")

        with self.assertRaises(SourceValidationError) as yaml_raised:
            loads_source("x: .nan\n", format="yaml")
        self.assertEqual(yaml_raised.exception.problem.category, "non_json_value")

    def test_recursive_yaml_alias_remains_non_json_value(self):
        with self.assertRaises(SourceValidationError) as raised:
            loads_source("a: &a [*a]\n", format="yaml")
        self.assertEqual(raised.exception.problem.category, "non_json_value")
        self.assertIn("recursive container alias", raised.exception.problem.message)


if __name__ == "__main__":
    unittest.main()
