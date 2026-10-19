"""F-030 phase 2: protect unique gates while removing redundant PR triggers.

Research/plan: docs/research/F-030-ci-trigger-phase2.md
Issue #291. RED is intentional before workflow edits, not a releasable PR state.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github/workflows"

# This map contains ONLY still-active focused PR owners. F-030 POS successors
# were retired in favor of full-suite exact-head invariant checks; the
# removed owners are enforced by test_ci_consolidation_pos_pilot.py.
SCOPES = {
    "i009-production-bundles.yml": (
        ('"src/tfont/resources/**"', "'src/tfont/resources/**'"),
        "tests/i009/**",
    ),
}


def pr_section(text: str) -> str:
    self_contained = text.split("\n  pull_request:\n", 1)
    if len(self_contained) != 2:
        raise AssertionError("legacy workflow must still own a pull_request event")
    return self_contained[1].split("\n  workflow_dispatch:", 1)[0]


class CITriggerScopeRED(unittest.TestCase):
    def test_one_authoritative_full_suite_preserves_unique_resource_tests(self):
        full = (WORKFLOWS/"full-suite.yml").read_text(encoding="utf-8")
        for name in (
            'github.event.pull_request.head.sha || github.sha',
            'python-version: ["3.10", "3.12"]',
            'python -m unittest discover -s tests -v',
            'python -m pytest tests/research -q',
            'python -m build --wheel --outdir dist',
            'python scripts/coverage/build_p004_r011_baseline.py --check',
            'python scripts/coverage/build_i026_work_queue.py --check',
            'tests.i009.test_wheel_install_red',
            'I009_WHEEL_TEST: "1"',
            'tfont/resources/coverage/p004-r011-baseline-v1/',
        ):
            with self.subTest(required=name):
                self.assertIn(name, full)
        self.assertIn("python-version == '3.12'", full)
        for corpus in ("bhsa", "cuc", "syriac", "extrabiblical",
                       "pseudepigrapha", "oracc", "tlhdig"):
            with self.subTest(corpus=corpus):
                self.assertIn('"' + corpus + '.json"', full)

    def test_remaining_legacy_sources_only_keep_scoped_pr_triggers(self):
        for filename in (
            "i016-coverage.yml",
            "i017-pseudepigrapha-coverage.yml",
            "i018-oracc-coverage.yml",
            "i019-tlhdig-coverage.yml",
            "i033e3-protected-batch-review.yml",
        ):
            self.assertFalse((WORKFLOWS / filename).exists(), filename)
        for workflow, (removed, retained) in SCOPES.items():
            src = (WORKFLOWS/workflow).read_text(encoding="utf-8")
            pr = pr_section(src)
            with self.subTest(workflow=workflow):
                # I-009 historically uses a scoped implementation-branch
                # push event, not workflow_dispatch. Do not invent a trigger.
                if workflow != "i009-production-bundles.yml":
                    self.assertIn("workflow_dispatch:", src)
                else:
                    self.assertIn("impl/i009-production-noun-bundles", src)
                self.assertIn(retained, pr)
                self.assertIn(workflow, pr)
                for glob in removed:
                    self.assertNotIn(glob, pr)

    def test_original_source_download_workflows_remain_available(self):
        for name in (
            "i027b3-extrabiblical-source.yml",
            "i027c1-native-pos.yml",
            "r005-research-inventory.yml",
            "full-suite.yml",
        ):
            with self.subTest(workflow=name):
                self.assertTrue((WORKFLOWS/name).is_file())


if __name__ == "__main__":
    unittest.main()
