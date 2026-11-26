from __future__ import annotations

import unittest

from ontotf.digests import DigestError, source_bundle_digest


class SourceBundleDiagnosticPathTests(unittest.TestCase):
    def assert_problem_path(self, files, *, category: str, expected_path: tuple[str | int, ...]) -> DigestError:
        with self.assertRaises(DigestError) as raised:
            source_bundle_digest(files)
        self.assertEqual(raised.exception.problem.category, category)
        self.assertEqual(raised.exception.problem.path, expected_path)
        return raised.exception

    def test_traversal_path_identifies_logical_path_field(self):
        self.assert_problem_path(
            [("../a.yaml", b"a")],
            category="projection_error",
            expected_path=(0, 0),
        )

    def test_absolute_path_identifies_logical_path_field(self):
        self.assert_problem_path(
            [("/a.yaml", b"a")],
            category="projection_error",
            expected_path=(0, 0),
        )

    def test_backslash_path_identifies_logical_path_field(self):
        self.assert_problem_path(
            [("a\\b.yaml", b"a")],
            category="projection_error",
            expected_path=(0, 0),
        )

    def test_wrong_logical_path_type_identifies_field(self):
        self.assert_problem_path(
            [(1, b"a")],
            category="projection_error",
            expected_path=(0, 0),
        )

    def test_later_invalid_entry_preserves_entry_index(self):
        self.assert_problem_path(
            [("a.yaml", b"a"), ("b.yaml", b"b"), ("../c.yaml", b"c")],
            category="projection_error",
            expected_path=(2, 0),
        )

    def test_empty_segment_path_identifies_logical_path_field(self):
        self.assert_problem_path(
            [("a//b.yaml", b"a")],
            category="projection_error",
            expected_path=(0, 0),
        )

    def test_duplicate_path_control_remains_logical_path_field(self):
        self.assert_problem_path(
            [("a.yaml", b"a"), ("a.yaml", b"b")],
            category="duplicate_logical_path",
            expected_path=(1, 0),
        )

    def test_payload_type_control_remains_payload_field(self):
        self.assert_problem_path(
            [("a.yaml", "not-bytes")],
            category="projection_error",
            expected_path=(0, 1),
        )

    def test_malformed_tuple_control_remains_entry_path(self):
        self.assert_problem_path(
            [("a.yaml",)],
            category="projection_error",
            expected_path=(0,),
        )

    def test_valid_bundle_fixed_vector_is_unchanged(self):
        bom_crlf = b"\xef\xbb\xbfalpha: 1\r\nbeta: 2\r\n"
        bare_cr = b"alpha\rbravo\r"
        self.assertEqual(
            source_bundle_digest([("b.yaml", bare_cr), ("a.yaml", bom_crlf)]),
            "sha256:57ab8e39e7a3f8966362892d47b3e63a6c6db6b4f843949b2808907fbed191f7",
        )


if __name__ == "__main__":
    unittest.main()
