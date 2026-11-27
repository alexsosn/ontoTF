from __future__ import annotations

import unittest

from ontotf.digests import (
    MAX_JSON_NESTING,
    DigestError,
    mapping_semantic_digest_v2,
    projection_semantic_digest_v1,
)


def nested_object_chain(container_count: int):
    if container_count < 1:
        raise ValueError("container_count must be positive")
    value = {"leaf": "ok"}
    for _ in range(container_count - 1):
        value = {"next": value}
    return value


class SemanticDigestJsonBoundaryTests(unittest.TestCase):
    def assert_non_json(self, func, value) -> DigestError:
        with self.assertRaises(DigestError) as raised:
            func(value)
        self.assertEqual(raised.exception.problem.category, "non_json_value")
        return raised.exception

    def test_mapping_included_recursive_object_uses_owned_digest_error(self):
        recursive = {}
        recursive["self"] = recursive
        mapping = {
            "mapping_id": "mapping:test",
            "included": recursive,
        }

        exc = self.assert_non_json(mapping_semantic_digest_v2, mapping)
        self.assertEqual(exc.problem.message, "recursive object is outside the ontoTF JSON model")
        self.assertEqual(exc.problem.path, ("included", "self"))

    def test_projection_included_recursive_list_uses_owned_digest_error(self):
        recursive = []
        recursive.append(recursive)
        projection = {
            "projection_id": "projection:test",
            "included": recursive,
        }

        exc = self.assert_non_json(projection_semantic_digest_v1, projection)
        self.assertEqual(exc.problem.message, "recursive list is outside the ontoTF JSON model")
        self.assertEqual(exc.problem.path, ("included", 0))

    def test_included_depth_128_remains_accepted(self):
        # Root mapping object counts as container depth 1, so 127 included
        # object containers make the deepest accepted container depth 128.
        mapping = {
            "mapping_id": "mapping:test",
            "included": nested_object_chain(MAX_JSON_NESTING - 1),
        }

        digest = mapping_semantic_digest_v2(mapping)
        self.assertTrue(digest.startswith("sha256:"))

    def test_included_depth_129_is_rejected_at_first_over_limit_path(self):
        mapping = {
            "mapping_id": "mapping:test",
            "included": nested_object_chain(MAX_JSON_NESTING),
        }

        exc = self.assert_non_json(mapping_semantic_digest_v2, mapping)
        self.assertEqual(
            exc.problem.message,
            f"JSON nesting exceeds maximum depth {MAX_JSON_NESTING}",
        )
        self.assertEqual(exc.problem.path[0], "included")
        self.assertEqual(len(exc.problem.path), MAX_JSON_NESTING)

    def test_top_level_excluded_review_is_not_traversed_or_digest_authoritative(self):
        semantic = {
            "mapping_id": "mapping:test",
            "included": {"value": "x"},
        }
        without_audit = mapping_semantic_digest_v2(dict(semantic))

        recursive_review = {}
        recursive_review["self"] = recursive_review
        with_audit = dict(semantic)
        with_audit["review"] = recursive_review

        self.assertEqual(mapping_semantic_digest_v2(with_audit), without_audit)

    def test_top_level_excluded_rationale_is_not_traversed_or_digest_authoritative(self):
        semantic = {
            "mapping_id": "mapping:test",
            "included": {"value": "x"},
        }
        without_audit = mapping_semantic_digest_v2(dict(semantic))

        recursive_rationale = []
        recursive_rationale.append(recursive_rationale)
        with_audit = dict(semantic)
        with_audit["rationale"] = recursive_rationale

        self.assertEqual(mapping_semantic_digest_v2(with_audit), without_audit)

    def test_nested_excluded_review_and_authored_digest_are_not_traversed(self):
        semantic = {
            "projection_id": "projection:test",
            "included": {"value": "x"},
        }
        without_audit = projection_semantic_digest_v1(dict(semantic))

        recursive_review = {}
        recursive_review["self"] = recursive_review
        recursive_authored_digest = []
        recursive_authored_digest.append(recursive_authored_digest)
        with_audit = dict(semantic)
        with_audit["review"] = recursive_review
        with_audit["projection_semantic_digest"] = recursive_authored_digest

        self.assertEqual(projection_semantic_digest_v1(with_audit), without_audit)


if __name__ == "__main__":
    unittest.main()
