"""Full-suite discoverability and source-change gate conservation.

Do not let old focused CI jobs mask test directories skipped by
`unittest discover -s tests`.
"""
from __future__ import annotations

import unittest
from pathlib import Path


ROOT=Path(__file__).resolve().parents[2]
TESTS=ROOT/"tests"
WORKFLOWS=ROOT/".github/workflows"
REDUNDANT=(
    "i001-validation.yml",
    "i002-validation.yml",
    "i003-validation.yml",
    "i004-semantic-validation.yml",
    "i005-semantic-ir.yml",
    "i006-semantic-resolver.yml",
    "i015-noun-morphology.yml",
    "f002-wheel-schema-resources.yml",
)


def test_directories():
    return tuple(sorted({
        path.parent
        for path in TESTS.rglob("test*.py")
        if path.name != "__init__.py"
    }))


class FullSuiteDiscoveryGate(unittest.TestCase):
    def test_every_test_directory_is_importable_for_unittest_discover(self):
        missing=[str(folder.relative_to(ROOT))
                 for folder in test_directories()
                 if not (folder/"__init__.py").is_file()]
        self.assertEqual(missing, [], "unittest silently skips test subtrees missing package markers")

    def test_canonical_full_suite_keeps_source_and_test_change_gates(self):
        wf=(WORKFLOWS/"full-suite.yml").read_text(encoding="utf-8")
        self.assertIn("  pull_request:",wf)
        self.assertIn('"src/**"',wf)
        self.assertIn('"tests/**"',wf)
        self.assertIn("python -m unittest discover -s tests -v",wf)
        self.assertIn("python -m build --wheel --outdir dist",wf)
        self.assertIn("python -m pip install build pytest",wf)
        self.assertIn("python -m pytest tests/research -q",wf)
        self.assertIn('python-version: ["3.10", "3.12"]',wf)

    def test_pruning_applies_only_to_legacy_generic_source_triggers(self):
        for name in REDUNDANT:
            with self.subTest(workflow=name):
                source=(WORKFLOWS/name).read_text(encoding="utf-8")
                self.assertIn("  pull_request:",source)
                pull=source.split("  pull_request:",1)[1].split("\n  workflow_dispatch:",1)[0].split("\npermissions:",1)[0].split("\njobs:",1)[0]
                self.assertNotIn("src/tfont/**",pull)
                self.assertIn("tests/",pull)
                self.assertIn(name,pull)


if __name__=="__main__":
    unittest.main()
