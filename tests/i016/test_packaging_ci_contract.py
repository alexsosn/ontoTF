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

    def test_i016_exact_head_workflow_exists_and_checks_resources(self):
        path = ROOT / ".github" / "workflows" / "i016-coverage.yml"
        self.assertTrue(path.is_file(), "RED: I-016 focused workflow is absent")
        if not path.is_file():
            return
        text = path.read_text(encoding="utf-8")
        self.assertIn("github.event.pull_request.head.sha || github.sha", text)
        self.assertIn("tests/i016", text)
        self.assertIn("build_p004_r011_baseline.py --check", text)
        self.assertIn("python-version: [\"3.10\", \"3.12\"]", text)


if __name__ == "__main__":
    unittest.main()
