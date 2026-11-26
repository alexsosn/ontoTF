from __future__ import annotations

import math
import unittest
from unittest.mock import patch

import ontotf.digests as digests
from ontotf.digests import DigestError, canonical_json_bytes, source_bundle_digest


EXPECTED_MAX_JSON_NESTING = 128


def nested_list(depth: int):
    value = 0
    for _ in range(depth):
        value = [value]
    return value


def nested_dict(depth: int):
    value = 0
    for _ in range(depth):
        value = {"x": value}
    return value


class DeepDigestNestingTests(unittest.TestCase):
    def assert_category(self, category: str, func, *args, **kwargs) -> DigestError:
        with self.assertRaises(DigestError) as raised:
            func(*args, **kwargs)
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception

    def test_public_nesting_contract_is_fixed_at_128(self):
        self.assertEqual(
            getattr(digests, "MAX_JSON_NESTING", None),
            EXPECTED_MAX_JSON_NESTING,
        )

    def test_list_boundary_128_is_accepted_byte_for_byte(self):
        value = nested_list(EXPECTED_MAX_JSON_NESTING)
        expected = b"[" * EXPECTED_MAX_JSON_NESTING + b"0" + b"]" * EXPECTED_MAX_JSON_NESTING
        self.assertEqual(canonical_json_bytes(value), expected)

    def test_list_boundary_plus_one_fails_with_stable_path(self):
        error = self.assert_category(
            "non_json_value",
            canonical_json_bytes,
            nested_list(EXPECTED_MAX_JSON_NESTING + 1),
        )
        self.assertEqual(error.problem.message, "JSON nesting exceeds maximum depth 128")
        self.assertEqual(error.problem.path, (0,) * EXPECTED_MAX_JSON_NESTING)

    def test_dict_boundary_128_is_accepted_byte_for_byte(self):
        value = nested_dict(EXPECTED_MAX_JSON_NESTING)
        expected = b'{"x":' * EXPECTED_MAX_JSON_NESTING + b"0" + b"}" * EXPECTED_MAX_JSON_NESTING
        self.assertEqual(canonical_json_bytes(value), expected)

    def test_dict_boundary_plus_one_fails_with_stable_path(self):
        error = self.assert_category(
            "non_json_value",
            canonical_json_bytes,
            nested_dict(EXPECTED_MAX_JSON_NESTING + 1),
        )
        self.assertEqual(error.problem.message, "JSON nesting exceeds maximum depth 128")
        self.assertEqual(error.problem.path, ("x",) * EXPECTED_MAX_JSON_NESTING)

    def test_recursive_container_diagnostic_keeps_precedence(self):
        value = []
        value.append(value)
        error = self.assert_category("non_json_value", canonical_json_bytes, value)
        self.assertIn("recursive list", error.problem.message)
        self.assertEqual(error.problem.path, (0,))

    def test_downstream_recursion_error_is_translated(self):
        with patch("ontotf.digests.rfc8785.dumps", side_effect=RecursionError("dependency recursion")):
            error = self.assert_category("non_json_value", canonical_json_bytes, {"ok": True})
        self.assertIn("recursion", error.problem.message.lower())

    def test_existing_domain_and_bundle_controls_are_unchanged(self):
        self.assert_category("float_domain", canonical_json_bytes, math.nan)
        self.assert_category("integer_domain", canonical_json_bytes, 9007199254740992)
        self.assert_category("unicode_domain", canonical_json_bytes, "\ud800")
        self.assert_category(
            "duplicate_logical_path",
            source_bundle_digest,
            [("a.yaml", b"a"), ("a.yaml", b"b")],
        )


if __name__ == "__main__":
    unittest.main()
