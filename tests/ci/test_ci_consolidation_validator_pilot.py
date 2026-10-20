"""F-030 validator foundation CI consolidation must preserve executable coverage."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "workflows"

RETIRED = (
    "i001-validation.yml",
    "i002-validation.yml",
    "i003-validation.yml",
    "i004-semantic-validation.yml",
    "i005-semantic-ir.yml",
    "i006-semantic-resolver.yml",
    "i007-runtime-prerequisites.yml",
    "i015-noun-morphology.yml",
    "f003-digest-projection-key-errors.yml",
    "f004-source-bundle-diagnostic-paths.yml",
    "f005-utf16-diagnostic-paths.yml",
)

PACKAGES = ("i001", "i002", "i003", "i004", "i005", "i006", "i007", "i015",
            "packaging", "p002")

FOCUSED_I002 = (
    "test_projection_key_error_boundary.py",
    "test_source_bundle_diagnostic_paths.py",
    "test_utf16_diagnostic_paths.py",
)

PRESERVED_SPECIAL = (
    "i008-exact-execution.yml",         # Real Context-Fabric integration on 3.13.
    "i027b3-extrabiblical-source.yml", # Original corpus MQL checkout.
    "i027c1-native-pos.yml",            # Exact-pinned upstream source checks.
)


class ValidatorConsolidationContracts(unittest.TestCase):
    def test_historical_only_unittest_workflows_are_retired(self):
        for workflow in RETIRED:
            with self.subTest(workflow=workflow):
                self.assertFalse((CI / workflow).exists())

    def test_regression_test_packages_and_focused_modules_are_preserved(self):
        for package in PACKAGES:
            directory = ROOT / "tests" / package
            with self.subTest(package=package):
                self.assertTrue((directory / "__init__.py").is_file(),
                                f"unittest discover would skip tests/{package}")
                self.assertTrue(tuple(directory.glob("test_*.py")),
                                f"tests/{package} lost its tests")
        for name in FOCUSED_I002:
            with self.subTest(module=name):
                self.assertTrue((ROOT / "tests" / "i002" / name).is_file())

    def test_one_exact_head_owning_regression_and_package_gate(self):
        text = (CI / "full-suite.yml").read_text(encoding="utf-8")
        for name in (
            "  pull_request:\n  workflow_dispatch:",
            "github.event.pull_request.head.sha || github.sha",
            'python-version: ["3.10", "3.12"]',
            "python -m unittest discover -s tests -v",
            "python -m pytest tests/research -q",
            "python scripts/coverage/build_p004_r011_baseline.py --check",
            "python scripts/coverage/build_i026_work_queue.py --check",
            "python -m build --wheel --outdir dist",
            "Install reviewed profile wheel in isolated environment",
        ):
            with self.subTest(contract=name):
                self.assertIn(name, text)

    def test_unique_source_jobs_remain_separate(self):
        for name in PRESERVED_SPECIAL:
            with self.subTest(workflow=name):
                self.assertTrue((CI / name).is_file())
        i008 = (CI / PRESERVED_SPECIAL[0]).read_text(encoding="utf-8")
        self.assertIn("context-fabric==0.5.7", i008)
        self.assertIn("3.13", i008)
        for name in PRESERVED_SPECIAL[1:3]:
            text = (CI / name).read_text(encoding="utf-8")
            self.assertIn("repository: ETCBC/", text)
            self.assertIn("persist-credentials: false", text)
        self.assertFalse((CI / "i033e3-protected-batch-review.yml").exists())


if __name__ == "__main__":
    unittest.main()
