from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P001_TEST = ROOT / "tests" / "plans" / "test_p001_plan.py"


def _load_p001_contract_module():
    spec = importlib.util.spec_from_file_location("p001_plan_contract", P001_TEST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {P001_TEST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class P001DesignScopeRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = _load_p001_contract_module()

    def test_current_repository_may_contain_legitimate_src(self):
        self.assertTrue((ROOT / "src").is_dir())
        violations = self.contract.production_scope_violations(
            (
                ".github/workflows/p001-plan-validation.yml",
                "docs/plans/P-001-foundation-poc-design.md",
                "tests/plans/test_p001_plan.py",
            )
        )
        self.assertEqual(violations, ())

    def test_design_change_rejects_production_artifact_families(self):
        violations = self.contract.production_scope_violations(
            (
                "docs/plans/P-001-foundation-poc-design.md",
                "src/ontotf/compiler.py",
                "schemas/profile.schema.json",
                "profiles/demo/profile.yaml",
            )
        )
        self.assertEqual(
            violations,
            (
                "profiles/demo/profile.yaml",
                "schemas/profile.schema.json",
                "src/ontotf/compiler.py",
            ),
        )

    def test_directory_boundaries_and_windows_separators_are_deterministic(self):
        violations = self.contract.production_scope_violations(
            (
                "src",
                "schemas\\mapping.schema.json",
                "profiles/",
                "docs/src-notes.md",
                "schemas-notes.md",
                "nested/profiles/example",
                "src/ontotf/compiler.py",
                "src/ontotf/compiler.py",
            )
        )
        self.assertEqual(
            violations,
            (
                "profiles",
                "schemas/mapping.schema.json",
                "src",
                "src/ontotf/compiler.py",
            ),
        )


if __name__ == "__main__":
    unittest.main()
