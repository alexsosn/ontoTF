"""F-030 pilot: retired POS workflow checks still run on every exact PR head."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"

# Every retired job used offline frozen evidence and duplicated full test discovery.
RETIRED = {
    "i026-work-queue.yml": ("scripts/coverage/build_i026_work_queue.py", "i026"),
    "i027a-bhsa-stems.yml": ("scripts/coverage/build_i027a_bhsa_verbal_stems.py", "i027a"),
    "i027b1-bhsa-verb.yml": ("scripts/coverage/build_i027b1_bhsa_verb.py", "i027b1"),
    "i027b2-syriac-verb.yml": ("scripts/coverage/build_i027b2_syriac_verb.py", "i027b2"),
    "i027b4-extrabiblical-verb.yml": ("scripts/coverage/build_i027b4_extrabiblical_verb.py", "i027b4"),
    "i027c2-adj-adv.yml": ("scripts/coverage/build_i027c2_bhsa_adj_adv.py", "i027c2"),
    "i027d-current-coverage.yml": ("scripts/coverage/build_i027d_current_queue.py", "i027d"),
}
EXTRA_CHECKS = ("scripts/coverage/build_i027c2_syriac_adj_adv.py",)
SOURCE_PINNED_WORKFLOWS = (
    "i027b3-extrabiblical-source.yml",
    "i027c1-native-pos.yml",
)
PROTECTED_REVIEW_WORKFLOW = "i033e3-protected-batch-review.yml"


class POSConsolidationContract(unittest.TestCase):
    def test_retired_workflows_are_absent_but_regression_suites_remain(self):
        for filename, (script, suite) in RETIRED.items():
            with self.subTest(workflow=filename):
                self.assertFalse((WORKFLOWS / filename).exists())
                self.assertTrue((ROOT / script).is_file())
                self.assertTrue(list((ROOT / "tests" / suite).glob("test_*.py")))

    def test_every_pinned_builder_is_checked_once_in_full_suite(self):
        text = (WORKFLOWS / "full-suite.yml").read_text(encoding="utf-8")
        checks = tuple(script for script, _ in RETIRED.values()) + EXTRA_CHECKS
        for script in checks:
            with self.subTest(script=script):
                self.assertTrue((ROOT / script).is_file())
                self.assertEqual(text.count("python " + script + " --check"), 1)
        self.assertIn('python-version: ["3.10", "3.12"]', text)
        self.assertIn("github.event.pull_request.head.sha || github.sha", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python -m pytest tests/research -q", text)
        self.assertIn("python -m build --wheel", text)
        self.assertIn("  pull_request:\n  workflow_dispatch:", text)

    def test_external_evidence_and_protected_reviewer_are_not_removed(self):
        for filename in SOURCE_PINNED_WORKFLOWS:
            with self.subTest(workflow=filename):
                text = (WORKFLOWS / filename).read_text(encoding="utf-8")
                self.assertIn("repository: ETCBC/", text)
                self.assertIn("persist-credentials: false", text)
        trusted = (WORKFLOWS / PROTECTED_REVIEW_WORKFLOW).read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", trusted)
        self.assertIn("ref: main", trusted)
        self.assertNotIn("pull_request_review:\n", trusted)


if __name__ == "__main__":
    unittest.main()
