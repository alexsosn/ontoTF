"""F-030 phase 2: protect unique gates while removing redundant PR triggers.

Research/plan: docs/research/F-030-ci-trigger-phase2.md
Issue #291. RED is intentional before workflow edits, not a releasable PR state.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github/workflows"

SCOPES = {
    "i009-production-bundles.yml": (
        ('"src/tfont/resources/**"', "'src/tfont/resources/**'"),
        "tests/i009/**",
    ),
    "i016-coverage.yml": (
        ('"src/tfont/resources/coverage/**"', "'src/tfont/resources/coverage/**'"),
        "tests/i016/**",
    ),
    "i026-work-queue.yml": (
        ('"src/tfont/resources/coverage/**"', "'src/tfont/resources/coverage/**'"),
        "tests/i026/**",
    ),
    "i027b1-bhsa-verb.yml": (
        ('"src/tfont/production_bundles.py"', "'src/tfont/production_bundles.py'"),
        "tests/i027b1/**",
    ),
    "i027b2-syriac-verb.yml": (
        ('"src/tfont/production_bundles.py"', "'src/tfont/production_bundles.py'"),
        "tests/i027b2/**",
    ),
    "i027b4-extrabiblical-verb.yml": (
        ('"src/tfont/production_bundles.py"', "'src/tfont/production_bundles.py'"),
        "tests/i027b4/**",
    ),
    "i027c2-adj-adv.yml": (
        ('"src/tfont/production_bundles.py"', "'src/tfont/production_bundles.py'",
         '"src/tfont/__init__.py"', "'src/tfont/__init__.py'"),
        "tests/i027c2/**",
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

    def test_legacy_sources_only_keep_scoped_pr_triggers(self):
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
