"""F-030: preserve all TF-native guards under unconditional shared CI."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ArchitectureCIOwner(unittest.TestCase):
    def test_exact_head_matrix_runs_architecture_without_step_condition(self):
        workflow = (ROOT / ".github/workflows/full-suite.yml").read_text()
        for invariant in (
            "  pull_request:\n  workflow_dispatch:",
            'python-version: ["3.12", "3.13", "3.14", "3.15"]',
            "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
            "python -m unittest discover -s tests -v",
            "python -m pytest tests/research -q",
            "python -m build --wheel --outdir dist",
        ):
            self.assertIn(invariant, workflow)
        steps = workflow.split("      - ")
        architecture = [step for step in steps
                        if "run: python -m pytest tests/architecture -q" in step]
        self.assertEqual(len(architecture), 1, "nine architecture guards lack a shared owner")
        self.assertNotIn("if:", architecture[0])
        self.assertFalse((ROOT / ".github/workflows/a001-tf-native-boundary.yml").exists())

    def test_all_original_architecture_guards_remain(self):
        module = ROOT / "tests/architecture/test_tf_native_boundary.py"
        names = {node.name for node in ast.parse(module.read_text()).body
                 if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
        self.assertEqual(names, {
            "test_agents_pins_tf_native_materializer_boundary",
            "test_r005_supersession_amendment_preserves_history_and_corrects_oracc_boundary",
            "test_r007_supersession_rejects_generic_external_carrier",
            "test_r007_supersession_reconciles_oracc_with_current_tf_architecture",
            "test_supersession_states_storage_is_not_semantic_carrier_type",
            "test_a001_does_not_replace_adapter_with_another_generic_runtime_api",
            "test_p001_sections_6_and_7_are_explicitly_superseded_for_execution",
            "test_legacy_v1_component_kinds_are_identity_only_not_runtime_permission",
            "test_p001_reconciliation_preserves_still_valid_foundation_contracts",
        })


if __name__ == "__main__":
    unittest.main()
