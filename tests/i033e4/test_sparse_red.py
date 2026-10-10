"""TDD RED: frozen reviewed coverage sources compose from a sparse delta."""
from __future__ import annotations

import json
import unittest

from tfont.coverage import coverage_report, load_packaged_coverage_manifest
from tfont.coverage_deltas import (
    PublishedCoverageDeltaError,
    build_published_coverage_delta,
    load_published_coverage_delta,
)

CASES = (
    ("bhsa", "p004-i027a-bhsa-stems-v1", "p004-i027b1-bhsa-verb-v1", 1),
    ("bhsa", "p004-i027b1-bhsa-verb-v1", "p004-i027c2-bhsa-adj-adv-v1", 2),
    ("syriac", "p004-i027b2-syriac-verb-v1", "p004-i027c2-syriac-adj-adv-v1", 2),
    ("extrabiblical", "p004-r011-baseline-v1", "p004-i027b4-extrabiblical-verb-v1", 1),
)


class SparsePublishedCoverageRed(unittest.TestCase):
    def test_exact_composition_for_reviewed_original_snapshots(self):
        for corpus, before, after, count in CASES:
            with self.subTest(corpus=corpus, base=before, target=after):
                delta = build_published_coverage_delta(corpus, before, after)
                self.assertEqual(delta["schema_version"], 1)
                self.assertEqual(delta["authority"], "published-registry-parity-only")
                self.assertEqual((delta["corpus_id"], delta["base_resource_set"], delta["target_resource_set"]),
                                 (corpus, before, after))
                self.assertEqual(len(delta["added_production"]), count)
                self.assertTrue(all("production" in row and "item_id" in row
                                    for row in delta["added_production"]))
                self.assertNotIn("semantic_items", delta)
                self.assertNotIn("reviewed", delta)
                self.assertLess(len(json.dumps(delta)), 2500)
                target = load_packaged_coverage_manifest(after, corpus)
                self.assertEqual(load_published_coverage_delta(delta), target)
                self.assertEqual(
                    coverage_report(load_published_coverage_delta(delta)),
                    coverage_report(target),
                )

    def test_exact_repeatability_and_source_bounded_selectors(self):
        for corpus, before, after, _ in CASES:
            with self.subTest(corpus=corpus, target=after):
                delta=build_published_coverage_delta(corpus,before,after)
                self.assertEqual(delta,build_published_coverage_delta(corpus,before,after))
                self.assertTrue(all(row["production"]["source_ids"] for row in delta["added_production"]))
        for bad in ("../data", "", "current", "p004-invalid/version"):
            with self.subTest(bad=bad),self.assertRaises(PublishedCoverageDeltaError):
                build_published_coverage_delta("bhsa","p004-i027b1-bhsa-verb-v1",bad)

    def test_native_only_history_is_not_mislabeled_as_exact(self):
        base=load_packaged_coverage_manifest("p004-i027a-bhsa-stems-v1","bhsa")
        latest=load_published_coverage_delta(build_published_coverage_delta(
            "bhsa", "p004-i027a-bhsa-stems-v1", "p004-i027b1-bhsa-verb-v1"
        ))
        for original in base["semantic_items"]:
            if original["accounting"]["production"] is not None:
                new=next(x for x in latest["semantic_items"] if x["item_id"]==original["item_id"])
                self.assertEqual(new["accounting"]["production"],original["accounting"]["production"])
        old_report=coverage_report(base)
        new_report=coverage_report(latest)
        self.assertEqual(new_report.production_reviewed_items-old_report.production_reviewed_items,1)
        self.assertEqual(new_report.production_common_target_items-old_report.production_common_target_items,1)
        self.assertEqual(
            dict(new_report.production_assessment_counts)["native-only"],
            dict(old_report.production_assessment_counts)["native-only"],
        )


if __name__=="__main__":
    unittest.main()
