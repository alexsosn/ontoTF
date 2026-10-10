"""Canonical regression must cover all PR paths without duplicate push events."""
from pathlib import Path
import unittest

from ruamel.yaml import YAML


WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/full-suite.yml"


class CanonicalPREventTests(unittest.TestCase):
    def setUp(self):
        self.workflow = YAML(typ="safe").load(WORKFLOW.read_text(encoding="utf-8"))

    def test_every_pr_uses_default_events_without_path_or_branch_filters(self):
        events = self.workflow["on"]
        self.assertIn("pull_request", events)
        # Null event configuration uses GitHub's opened/synchronize/reopened
        # defaults, independent of changed paths (including future ledgers).
        self.assertIsNone(events["pull_request"])

    def test_push_regression_runs_only_on_main_without_path_filters(self):
        self.assertEqual(self.workflow["on"]["push"], {"branches": ["main"]})

    def test_unopened_branches_can_still_run_manual_or_reusable_regression(self):
        self.assertIn("workflow_dispatch", self.workflow["on"])
        self.assertIn("workflow_call", self.workflow["on"])
        self.assertNotIn("pull_request_target", self.workflow["on"])

    def test_canonical_matrix_cannot_report_success_by_skipping_the_job(self):
        self.assertEqual(self.workflow["name"], "Full repository suite")
        self.assertEqual(set(self.workflow["jobs"]), {"validate"})
        job = self.workflow["jobs"]["validate"]
        self.assertNotIn("if", job)
        self.assertNotIn("needs", job)
        self.assertNotIn("continue-on-error", job)
        self.assertEqual(job["strategy"]["matrix"], {"python-version": ["3.10", "3.12"]})
        self.assertFalse(job["strategy"]["fail-fast"])
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        checkout = job["steps"][0]
        self.assertEqual(checkout["with"]["ref"],
                         "${{ github.event.pull_request.head.sha || github.sha }}")
        self.assertNotIn("if", checkout)
        # Only wheel smoke steps intentionally run once on Python 3.12.
        smoke_steps = {
            "Verify frozen seven-corpus coverage files inside wheel",
            "Install reviewed profile wheel in isolated environment",
        }
        for step in job["steps"]:
            if step.get("name") in smoke_steps:
                self.assertEqual(step["if"], "matrix.python-version == '3.12'")
            else:
                self.assertNotIn("if", step)
            self.assertNotIn("continue-on-error", step)


if __name__ == "__main__":
    unittest.main()
