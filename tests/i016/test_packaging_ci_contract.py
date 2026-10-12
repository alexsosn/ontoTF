from __future__ import annotations

import unittest
from pathlib import Path

import tfont


ROOT = Path(__file__).resolve().parents[2]


class I016PackagingAndCIContractTests(unittest.TestCase):
    def test_coverage_api_is_exported_from_package_root(self):
        for name in (
            "CoverageError",
            "CoverageReport",
            "coverage_denominator_digest",
            "coverage_denominator_projection",
            "coverage_report",
            "load_coverage_manifest",
            "load_p004_r011_baseline_manifests",
            "validate_coverage_manifest",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(tfont, name), f"RED: tfont root does not export {name}")

    def test_wheel_package_data_includes_coverage_resources(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn(
            '"resources/coverage/*/*.json"',
            pyproject,
            "RED: generated coverage manifests are absent from wheel package-data",
        )

    def test_i016_coverage_is_owned_by_one_exact_head_workflow(self):
        workflows = ROOT / ".github" / "workflows"
        self.assertFalse((workflows / "i016-coverage.yml").exists())
        text = (workflows / "full-suite.yml").read_text(encoding="utf-8")
        for required in (
            "github.event.pull_request.head.sha || github.sha",
            'python-version: ["3.10", "3.12"]',
            "python -m unittest discover -s tests -v",
            "python scripts/coverage/build_p004_r011_baseline.py --check",
            "tfont/resources/coverage/p004-r011-baseline-v1/",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)



if __name__ == "__main__":
    unittest.main()
