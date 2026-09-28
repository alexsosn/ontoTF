from __future__ import annotations

import copy
import unittest

from tfont.coverage import (
    CoverageError,
    coverage_denominator_digest,
    coverage_report,
    load_p004_r011_baseline_manifests,
    validate_coverage_manifest,
)
from tfont.source_validation import SourceValidationError


def _baseline(corpus: str = "bhsa"):
    return copy.deepcopy(load_p004_r011_baseline_manifests()[corpus])


def _fill_production(manifest):
    for item in manifest["semantic_items"]:
        item["accounting"]["production"] = {
            "assessments": ["exact"],
            "common_target": True,
            "source_ids": [f"review:{item['item_id']}"],
        }
    manifest["accounting_gaps"] = []


class I016CoverageAdversarialTests(unittest.TestCase):
    def test_duplicate_semantic_item_fails_closed(self):
        manifest = _baseline()
        manifest["semantic_items"].append(copy.deepcopy(manifest["semantic_items"][0]))
        with self.assertRaises(CoverageError) as raised:
            validate_coverage_manifest(manifest)
        self.assertEqual(raised.exception.problem.category, "duplicate_id")

    def test_semantic_and_technical_overlap_fails_closed(self):
        manifest = _baseline()
        item = manifest["semantic_items"][0]
        manifest["technical_exclusions"].append(
            {
                "item_id": item["item_id"],
                "kind": item["kind"],
                "reason": "adversarial overlap",
                "authority": "production",
                "source_ids": ["review:technical"],
            }
        )
        manifest["denominator_digest"] = coverage_denominator_digest(manifest)
        with self.assertRaises(CoverageError) as raised:
            validate_coverage_manifest(manifest)
        self.assertEqual(raised.exception.problem.category, "denominator_overlap")

    def test_accounting_changes_do_not_change_denominator_digest(self):
        manifest = _baseline()
        before = coverage_denominator_digest(manifest)
        first = manifest["semantic_items"][0]
        first["accounting"]["production"] = {
            "assessments": ["native-only"],
            "common_target": False,
            "source_ids": ["review:new"],
        }
        self.assertEqual(coverage_denominator_digest(manifest), before)

    def test_generated_at_does_not_change_denominator_digest(self):
        manifest = _baseline()
        before = coverage_denominator_digest(manifest)
        manifest["generated_at"] = "2099-01-01T00:00:00Z"
        self.assertEqual(coverage_denominator_digest(manifest), before)

    def test_semantic_denominator_mutation_changes_digest(self):
        manifest = _baseline()
        before = coverage_denominator_digest(manifest)
        manifest["semantic_items"].append(
            {
                "item_id": "node_feature:new-semantic-item",
                "kind": "node_feature",
                "accounting": {"research": None, "production": None},
            }
        )
        self.assertNotEqual(coverage_denominator_digest(manifest), before)

    def test_invalid_revision_is_structurally_rejected(self):
        manifest = _baseline()
        manifest["target_corpus_revision"] = "not-a-git-sha"
        with self.assertRaises(SourceValidationError):
            validate_coverage_manifest(manifest)

    def test_digest_mismatch_fails_closed(self):
        manifest = _baseline()
        manifest["denominator_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(CoverageError) as raised:
            validate_coverage_manifest(manifest)
        self.assertEqual(raised.exception.problem.category, "denominator_digest_mismatch")

    def test_research_authority_never_counts_as_production(self):
        manifest = _baseline()
        item = next(
            row for row in manifest["semantic_items"]
            if row["accounting"]["research"] is not None
            and row["accounting"]["production"] is None
        )
        report = coverage_report(manifest)
        self.assertGreater(report.research_reviewed_items, report.production_reviewed_items)
        self.assertIsNotNone(item["accounting"]["research"])
        self.assertIsNone(item["accounting"]["production"])

    def test_bounded_curated_scope_never_claims_corpus_wide_completion(self):
        manifest = _baseline("oracc")
        _fill_production(manifest)
        manifest["target_corpus_revision"] = manifest["denominator_source_revision"]
        manifest["denominator_digest"] = coverage_denominator_digest(manifest)
        report = coverage_report(manifest)
        self.assertTrue(report.bounded_scope_complete)
        self.assertFalse(report.corpus_wide_completion_claim_eligible)

    def test_stale_machine_exhaustive_scope_never_claims_corpus_wide_completion(self):
        manifest = _baseline("tlhdig")
        _fill_production(manifest)
        manifest["denominator_digest"] = coverage_denominator_digest(manifest)
        report = coverage_report(manifest)
        self.assertTrue(report.bounded_scope_complete)
        self.assertEqual(report.freshness, "stale")
        self.assertFalse(report.corpus_wide_completion_claim_eligible)

    def test_research_only_technical_exclusion_blocks_corpus_wide_completion(self):
        manifest = _baseline("bhsa")
        _fill_production(manifest)
        manifest["technical_exclusions"].append(
            {
                "item_id": "node_feature:technical-only",
                "kind": "node_feature",
                "reason": "test technical exclusion",
                "authority": "research",
                "source_ids": ["research:test"],
            }
        )
        manifest["denominator_digest"] = coverage_denominator_digest(manifest)
        report = coverage_report(manifest)
        self.assertTrue(report.bounded_scope_complete)
        self.assertFalse(report.corpus_wide_completion_claim_eligible)

    def test_accounting_gap_is_not_denominator_coverage_and_blocks_completion(self):
        manifest = _baseline("syriac")
        _fill_production(manifest)
        manifest["accounting_gaps"] = [
            {
                "item_id": 'node_value:ls="prop"',
                "kind": "node_value",
                "authority": "production",
                "reason": "outside-denominator",
                "assessments": ["exact"],
                "common_target": True,
                "source_ids": ["mapping:syriac:olia-proper-noun"],
                "profiles": ["linguistic"],
                "capabilities": ["linguistic.part-of-speech"],
            }
        ]
        report = coverage_report(manifest)
        self.assertEqual(report.production_unreviewed_items, 0)
        self.assertEqual(report.production_outside_denominator_items, 1)
        self.assertFalse(report.bounded_scope_complete)

    def test_research_accounting_gap_is_reported_and_blocks_completion(self):
        manifest = _baseline("bhsa")
        _fill_production(manifest)
        manifest["accounting_gaps"] = [
            {
                "item_id": "node_feature:research-outside",
                "kind": "node_feature",
                "authority": "research",
                "reason": "outside-denominator",
                "assessments": ["native-only"],
                "common_target": False,
                "source_ids": ["research:test"],
            }
        ]
        report = coverage_report(manifest)
        self.assertEqual(report.research_outside_denominator_items, 1)
        self.assertEqual(
            report.research_outside_denominator_item_ids,
            ("node_feature:research-outside",),
        )
        self.assertFalse(report.bounded_scope_complete)
        self.assertFalse(report.corpus_wide_completion_claim_eligible)

    def test_accounting_gap_cannot_overlap_denominator(self):
        manifest = _baseline()
        item = manifest["semantic_items"][0]
        manifest["accounting_gaps"] = [
            {
                "item_id": item["item_id"],
                "kind": item["kind"],
                "authority": "production",
                "reason": "outside-denominator",
                "assessments": ["exact"],
                "common_target": True,
                "source_ids": ["mapping:test"],
            }
        ]
        with self.assertRaises(CoverageError) as raised:
            validate_coverage_manifest(manifest)
        self.assertEqual(raised.exception.problem.category, "denominator_overlap")

    def test_technical_exclusion_without_source_identity_is_rejected(self):
        manifest = _baseline()
        manifest["technical_exclusions"].append(
            {
                "item_id": "node_feature:technical-without-source",
                "kind": "node_feature",
                "reason": "missing review provenance",
                "authority": "production",
                "source_ids": [],
            }
        )
        manifest["denominator_digest"] = coverage_denominator_digest(manifest)
        with self.assertRaises(SourceValidationError):
            validate_coverage_manifest(manifest)

    def test_invalid_assessment_is_rejected(self):
        manifest = _baseline()
        item = manifest["semantic_items"][0]
        item["accounting"]["production"] = {
            "assessments": ["definitely-exact"],
            "common_target": True,
            "source_ids": ["review:test"],
        }
        with self.assertRaises(SourceValidationError):
            validate_coverage_manifest(manifest)

    def test_unreviewed_items_never_count_as_production_reviewed(self):
        manifest = _baseline("bhsa")
        report = coverage_report(manifest)
        self.assertEqual(
            report.production_unreviewed_items,
            report.semantic_items - report.production_reviewed_items,
        )
        self.assertGreater(report.production_unreviewed_items, 0)

    def test_common_target_must_match_assessment_strength(self):
        manifest = _baseline()
        item = manifest["semantic_items"][0]
        item["accounting"]["production"] = {
            "assessments": ["native-only"],
            "common_target": True,
            "source_ids": ["review:test"],
        }
        with self.assertRaises(CoverageError) as raised:
            validate_coverage_manifest(manifest)
        self.assertEqual(raised.exception.problem.category, "target_state_mismatch")


if __name__ == "__main__":
    unittest.main()
