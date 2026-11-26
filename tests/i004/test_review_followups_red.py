from __future__ import annotations

import copy
import unittest

from ontotf.semantic_digest_v2 import projection_semantic_digest_v1
from ontotf.semantic_validation import SemanticValidationError, validate_semantic_bundle
from tests.i004.test_semantic_validation_phase1 import base_sources, bundle
from tests.i004.test_semantic_validation_phase3 import reviewed_sources
from tests.i004.test_semantic_validation_phase5 import evidence_record, full_bundle


class I004ReviewFollowupRedTests(unittest.TestCase):
    def assert_problem(self, category: str, semantic_bundle):
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(semantic_bundle)
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception.problem

    def test_duplicate_lock_reports_actual_second_source_file(self):
        sources = base_sources()
        duplicate = copy.deepcopy(sources["locks"][0])
        sources["locks"].append(duplicate)
        problem = self.assert_problem("duplicate_id", bundle(sources))
        self.assertEqual(problem.related_id, "olia-test")
        self.assertEqual(problem.source_name, "lock-1.json")

    def test_duplicate_evidence_reports_actual_second_source_file(self):
        sources = base_sources()
        first = evidence_record("evidence:duplicate")
        second = copy.deepcopy(first)
        sources["evidences"] = [first, second]
        problem = self.assert_problem("duplicate_id", full_bundle(sources))
        self.assertEqual(problem.related_id, "evidence:duplicate")
        self.assertEqual(problem.source_name, "evidence-1.json")

    def test_mapping_review_evidence_reference_must_resolve(self):
        sources = reviewed_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["review"]["evidence"] = ["evidence:missing"]
        self.assert_problem("missing_reference", full_bundle(sources))

    def test_projection_review_evidence_reference_must_resolve(self):
        sources = reviewed_sources()
        projection = sources["mappings"]["mappings"][0]["projections"][0]
        projection["projection_semantic_digest"] = projection_semantic_digest_v1(projection)
        projection["review"] = {
            "review_id": "review:projection-noun",
            "status": "reviewed",
            "reviewed_mapping_digest": projection["projection_semantic_digest"],
            "reviewer_id": "reviewer:test",
            "reviewed_at": "2026-09-08T00:00:00Z",
            "review_source": "test",
            "review_method": "independent-adversarial",
            "evidence": ["evidence:missing"],
        }
        self.assert_problem("missing_reference", full_bundle(sources))


if __name__ == "__main__":
    unittest.main()
