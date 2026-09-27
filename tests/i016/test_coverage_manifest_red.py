from __future__ import annotations

import importlib
import json
import unittest
from importlib.resources import files

from tfont import source_validation


EXPECTED_COUNTS = {
    "bhsa": 219,
    "cuc": 37,
    "syriac": 74,
    "extrabiblical": 136,
    "tlhdig": 137,
    "pseudepigrapha": 40,
    "oracc": 42,
}

EXPECTED_RESEARCH = {
    "bhsa": (34, 6),
    "cuc": (9, 3),
    "syriac": (11, 6),
    "extrabiblical": (22, 5),
    "tlhdig": (8, 3),
    "pseudepigrapha": (8, 1),
    "oracc": (7, 2),
}

EXPECTED_PRODUCTION = {
    "bhsa": 7,
    "syriac": 6,
    "extrabiblical": 7,
    "cuc": 0,
    "tlhdig": 0,
    "pseudepigrapha": 0,
    "oracc": 0,
}

EXPECTED_OUTSIDE = {
    "bhsa": 0,
    "cuc": 0,
    "syriac": 1,
    "extrabiblical": 0,
    "tlhdig": 0,
    "pseudepigrapha": 0,
    "oracc": 0,
}

EXPECTED_FRESHNESS = {
    "bhsa": "current",
    "cuc": "current",
    "syriac": "current",
    "extrabiblical": "current",
    "tlhdig": "stale",
    "pseudepigrapha": "stale",
    "oracc": "stale",
}

EXPECTED_SCOPE = {
    "bhsa": "machine-exhaustive",
    "cuc": "machine-exhaustive",
    "syriac": "machine-exhaustive",
    "extrabiblical": "machine-exhaustive",
    "tlhdig": "machine-exhaustive",
    "pseudepigrapha": "bounded-curated",
    "oracc": "bounded-curated",
}


class I016CoverageManifestRedTests(unittest.TestCase):
    def test_coverage_manifest_schema_is_registered(self):
        self.assertIn(
            "coverage-manifest",
            source_validation.SCHEMA_FILES,
            "RED: coverage manifest source contract is absent",
        )

    def test_coverage_public_api_exists(self):
        try:
            module = importlib.import_module("tfont.coverage")
        except ModuleNotFoundError as exc:
            self.fail(f"RED: tfont.coverage does not exist: {exc}")
        for name in (
            "CoverageError",
            "coverage_denominator_projection",
            "coverage_denominator_digest",
            "coverage_report",
            "load_coverage_manifest",
            "load_p004_r011_baseline_manifests",
            "validate_coverage_manifest",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(module, name), f"RED: missing coverage API {name}")

    def test_seven_baseline_resources_exist(self):
        root = files("tfont").joinpath("resources", "coverage", "p004-r011-baseline-v1")
        self.assertTrue(root.is_dir(), "RED: packaged P-004 baseline directory is absent")
        if not root.is_dir():
            return
        names = sorted(path.name for path in root.iterdir() if path.name.endswith(".json"))
        self.assertEqual(
            names,
            sorted(f"{corpus}.json" for corpus in EXPECTED_COUNTS),
        )

    def test_baseline_reports_preserve_historical_and_production_counts(self):
        module = importlib.import_module("tfont.coverage")
        manifests = module.load_p004_r011_baseline_manifests()
        self.assertEqual(set(manifests), set(EXPECTED_COUNTS))

        reports = {corpus: module.coverage_report(manifest) for corpus, manifest in manifests.items()}
        self.assertEqual(sum(row.semantic_items for row in reports.values()), 685)
        self.assertEqual(sum(row.research_reviewed_items for row in reports.values()), 99)
        self.assertEqual(sum(row.research_common_target_items for row in reports.values()), 26)
        self.assertEqual(sum(row.production_reviewed_items for row in reports.values()), 20)
        self.assertEqual(sum(row.production_outside_denominator_items for row in reports.values()), 1)

        for corpus, report in reports.items():
            with self.subTest(corpus=corpus):
                self.assertEqual(report.semantic_items, EXPECTED_COUNTS[corpus])
                self.assertEqual(
                    (report.research_reviewed_items, report.research_common_target_items),
                    EXPECTED_RESEARCH[corpus],
                )
                self.assertEqual(report.production_reviewed_items, EXPECTED_PRODUCTION[corpus])
                self.assertEqual(report.production_outside_denominator_items, EXPECTED_OUTSIDE[corpus])
                self.assertEqual(report.freshness, EXPECTED_FRESHNESS[corpus])
                self.assertEqual(report.scope_quality, EXPECTED_SCOPE[corpus])
                if corpus == "syriac":
                    self.assertEqual(report.production_outside_denominator_item_ids, (\'node_value:ls="prop"\',))
                else:
                    self.assertEqual(report.production_outside_denominator_item_ids, ())
                self.assertFalse(report.corpus_wide_completion_claim_eligible)

    def test_baseline_manifest_digests_validate(self):
        module = importlib.import_module("tfont.coverage")
        for corpus, manifest in module.load_p004_r011_baseline_manifests().items():
            with self.subTest(corpus=corpus):
                module.validate_coverage_manifest(manifest)
                self.assertEqual(
                    manifest["denominator_digest"],
                    module.coverage_denominator_digest(manifest),
                )


if __name__ == "__main__":
    unittest.main()
