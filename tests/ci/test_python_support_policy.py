"""Guard supported Python versions across package metadata and CI workflows."""
from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path

from ruamel.yaml import YAML


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
SUPPORTED = ["3.12", "3.13", "3.14", "3.15"]
# Catch quoted and unquoted EOL interpreters, including compact YAML matrices.
UNSUPPORTED = re.compile(r"(?<![0-9.])3\.(?:10|11)(?![0-9])")


class PythonSupportPolicyTests(unittest.TestCase):
    def test_package_declares_current_baseline(self):
        with (ROOT / "pyproject.toml").open("rb") as source:
            metadata = tomllib.load(source)
        self.assertEqual(metadata["project"]["requires-python"], ">=3.12")

    def test_full_suite_covers_all_supported_versions(self):
        workflow = YAML(typ="safe").load(
            (WORKFLOWS / "full-suite.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            workflow["jobs"]["validate"]["strategy"]["matrix"]["python-version"],
            SUPPORTED,
        )

    def test_no_ci_workflow_selects_unsupported_python(self):
        for path in sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml"))):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if UNSUPPORTED.search(line):
                    self.fail(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}")

    def test_readme_states_current_baseline(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Python 3.12 or newer", readme)


if __name__ == "__main__":
    unittest.main()
