"""F-030: historical R-series test ownership cannot disappear after workflow retirement."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
RESEARCH_TESTS = ROOT / "tests" / "research"

RETIRED = (
    "r001-report-validation.yml",
    "r002-report-validation.yml",
    "r003-report-validation.yml",
    "r004-report-validation.yml",
    "r005-generated-validation.yml",
    "r015-bundle-research.yml",
    "r016-approximate-policy.yml",
    "r017-reference-policy.yml",
)

PRESERVED_TESTS = (
    "test_r001_report.py",
    "test_r002_report.py",
    "test_r003_report.py",
    "test_r004_report.py",
    "test_r005_generated.py",
    "test_r015_bundle_id.py",
    "test_r015_bridge_provenance.py",
    "test_r015_jcs_contract.py",
    "test_r015_lock_identity.py",
    "test_r015_active_flag.py",
    "test_r016_policy.py",
    "test_r017_reference_policy.py",
    "test_r017_post_r016_contract.py",
)

ORIGINAL_SOURCE_AND_REVIEW = (
    "r005-research-inventory.yml",
    "r011-report-validation.yml",
    "r020-denotational-semantics.yml",
    "i027b3-extrabiblical-source.yml",
    "i027c1-native-pos.yml",
)


class ResearchWorkflowRetirementContracts(unittest.TestCase):
    def test_redundant_historical_research_workflows_are_retired(self):
        for name in RETIRED:
            with self.subTest(workflow=name):
                self.assertFalse((WORKFLOWS / name).exists())

    def test_all_original_research_tests_remain_discoverable(self):
        self.assertTrue((RESEARCH_TESTS / "__init__.py").is_file())
        for name in PRESERVED_TESTS:
            with self.subTest(test=name):
                source = RESEARCH_TESTS / name
                self.assertTrue(source.is_file(), f"lost historical research contract: {name}")
                self.assertIn("def test_", source.read_text(encoding="utf-8"))

    def test_unconditional_exact_head_suite_owns_unittest_pytest_and_wheel(self):
        ci = (WORKFLOWS / "full-suite.yml").read_text(encoding="utf-8")
        for required in (
            "  push:\n    branches: [main]",
            "  pull_request:\n  workflow_dispatch:",
            "github.event.pull_request.head.sha || github.sha",
            'python-version: ["3.12", "3.13", "3.14", "3.15"]',
            "python -m unittest discover -s tests -v",
            "python -m pytest tests/research -q",
            "python scripts/coverage/build_p004_r011_baseline.py --check",
            "python scripts/coverage/build_i027d_current_queue.py --check",
            "python -m build --wheel --outdir dist",
        ):
            with self.subTest(required=required):
                self.assertIn(required, ci)

    def test_unique_original_corpus_measurement_jobs_stay_active(self):
        for name in ORIGINAL_SOURCE_AND_REVIEW:
            with self.subTest(workflow=name):
                self.assertTrue((WORKFLOWS / name).is_file())
        source = (WORKFLOWS / "r005-research-inventory.yml").read_text(encoding="utf-8")
        for required in (
            "repository: ETCBC/bhsa",
            "repository: DT-UCPH/cuc",
            "repository: ETCBC/syriac",
            "repository: ETCBC/peshitta",
            "repository: ETCBC/syrnt",
            "repository: ETCBC/extrabiblical",
            "repository: alexsosn/TLHdig-TF",
            "git diff --exit-code -- docs/research/data/generated/r005",
        ):
            self.assertIn(required, source)
        self.assertIn("python-version: '3.14'",
                      (WORKFLOWS / "r011-report-validation.yml").read_text(encoding="utf-8"))
        self.assertIn("diff -u docs/research/data/generated/r020",
                      (WORKFLOWS / "r020-denotational-semantics.yml").read_text(encoding="utf-8"))
        self.assertFalse((WORKFLOWS / "i033e3-protected-batch-review.yml").exists())


if __name__ == "__main__":
    unittest.main()
