from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tfont import coverage
from tfont.source_validation import SourceValidationError


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "scripts/coverage/build_i019_tlhdig_current.py"
EVIDENCE_PATH = ROOT / "docs/research/data/generated/i019/tlhdig-0.4.0.json"
POLICY_PATH = ROOT / "docs/research/data/i019/tlhdig-denominator-policy.json"
RESOURCE = "p004-tlhdig-0.4.0-bc4a206-v1"


def _builder_module():
    spec = importlib.util.spec_from_file_location("i019_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load I-019 builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _build_with(module, *, evidence=None, policy=None):
    evidence = copy.deepcopy(_json(EVIDENCE_PATH) if evidence is None else evidence)
    policy = copy.deepcopy(_json(POLICY_PATH) if policy is None else policy)

    def fake_load(path):
        if path == module.EVIDENCE:
            return copy.deepcopy(evidence)
        if path == module.POLICY:
            return copy.deepcopy(policy)
        raise AssertionError(f"unexpected builder input: {path}")

    with patch.object(module, "load_json", side_effect=fake_load):
        return module.build_manifest()


class I019CurrentTLHdigAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = _builder_module()

    def test_bounded_edge_schema_rejects_wrong_shape_and_duplicates(self):
        manifest = coverage.load_packaged_coverage_manifest(RESOURCE, "tlhdig")

        wrong_shape = copy.deepcopy(manifest)
        wrong_shape["denominator_basis"]["bounded_edge_features"] = "joined"
        with self.assertRaises(SourceValidationError):
            coverage.validate_coverage_manifest(wrong_shape)

        duplicate = copy.deepcopy(manifest)
        duplicate["denominator_basis"]["bounded_edge_features"] = ["joined", "joined"]
        with self.assertRaises(SourceValidationError):
            coverage.validate_coverage_manifest(duplicate)

    def test_bounded_edge_family_names_change_denominator_digest(self):
        manifest = coverage.load_packaged_coverage_manifest(RESOURCE, "tlhdig")
        before = coverage.coverage_denominator_digest(manifest)
        mutated = copy.deepcopy(manifest)
        mutated["denominator_basis"]["bounded_edge_features"] = ["joined"]
        self.assertNotEqual(coverage.coverage_denominator_digest(mutated), before)

    def test_technical_policy_rejects_absent_materialized_feature(self):
        policy = _json(POLICY_PATH)
        policy["technical_node_features"].append("not_materialized")
        policy["technical_exclusion_details"]["node_feature:not_materialized"] = {
            "reason": "adversarial",
            "source_ids": ["review:I-019:adversarial"],
        }
        with self.assertRaisesRegex(ValueError, "absent materialized"):
            _build_with(self.builder, policy=policy)

    def test_bounded_node_family_cannot_be_reclassified_technical(self):
        policy = _json(POLICY_PATH)
        policy["technical_node_features"].append("parse_ok")
        policy["technical_exclusion_details"]["node_feature:parse_ok"] = {
            "reason": "adversarial",
            "source_ids": ["review:I-019:adversarial"],
        }
        with self.assertRaisesRegex(ValueError, "not a semantic materialized feature"):
            _build_with(self.builder, policy=policy)

    def test_bounded_edge_family_must_reference_materialized_edge(self):
        policy = _json(POLICY_PATH)
        policy["bounded_edge_values"]["not_an_edge"] = ["x"]
        policy["bounded_edge_sources"]["not_an_edge"] = ["review:I-019:adversarial"]
        with self.assertRaisesRegex(ValueError, "not a semantic materialized feature"):
            _build_with(self.builder, policy=policy)

    def test_duplicate_bounded_node_and_edge_values_fail_closed(self):
        policy = _json(POLICY_PATH)
        policy["bounded_node_values"]["join_kind"].append("direct")
        with self.assertRaisesRegex(ValueError, "contains duplicates"):
            _build_with(self.builder, policy=policy)

        policy = _json(POLICY_PATH)
        policy["bounded_edge_values"]["joined"].append("direct")
        with self.assertRaisesRegex(ValueError, "contains duplicates"):
            _build_with(self.builder, policy=policy)

    def test_core_provenance_and_edge_schema_drift_fail_closed(self):
        evidence = _json(EVIDENCE_PATH)
        evidence["core_node_features"].remove("lang")
        with self.assertRaisesRegex(ValueError, "core node-feature set drifted"):
            _build_with(self.builder, evidence=evidence)

        evidence = _json(EVIDENCE_PATH)
        evidence["optional_provenance_node_features"].remove("srcxml")
        with self.assertRaisesRegex(ValueError, "provenance feature set drifted"):
            _build_with(self.builder, evidence=evidence)

        evidence = _json(EVIDENCE_PATH)
        del evidence["edge_features"]["witness"]
        with self.assertRaisesRegex(ValueError, "edge-feature set drifted"):
            _build_with(self.builder, evidence=evidence)

    def test_node_type_drift_fails_fixed_contract(self):
        evidence = _json(EVIDENCE_PATH)
        del evidence["node_types"]["joinstmt"]
        with self.assertRaisesRegex(ValueError, "node-type set drifted"):
            _build_with(self.builder, evidence=evidence)

    def test_artifact_tree_and_combined_tf_identity_are_pinned(self):
        evidence = _json(EVIDENCE_PATH)
        evidence["artifact"]["outputs_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "artifact identity drifted"):
            _build_with(self.builder, evidence=evidence)

        evidence = _json(EVIDENCE_PATH)
        evidence["artifact"]["materialized_tf_files_sha256"] = "1" * 64
        with self.assertRaisesRegex(ValueError, "artifact identity drifted"):
            _build_with(self.builder, evidence=evidence)

    def test_observation_like_extra_data_cannot_expand_open_domains(self):
        baseline = _build_with(self.builder)
        evidence = _json(EVIDENCE_PATH)
        evidence["observed_domains"] = {
            "pos": ["N", "V"],
            "sep": ["+=", "@+="],
            "selected": ["1", "2a"],
        }
        mutated = _build_with(self.builder, evidence=evidence)
        self.assertEqual(mutated["denominator_digest"], baseline["denominator_digest"])
        ids = {row["item_id"] for row in mutated["semantic_items"]}
        self.assertFalse(any(item_id.startswith("node_value:pos=") for item_id in ids))
        self.assertFalse(any(item_id.startswith("node_value:sep=") for item_id in ids))
        self.assertFalse(any(item_id.startswith("edge_value:selected=") for item_id in ids))

    def test_policy_is_exact_source_of_value_expansion(self):
        manifest = _build_with(self.builder)
        ids = {row["item_id"] for row in manifest["semantic_items"]}
        node_values = {item_id for item_id in ids if item_id.startswith("node_value:")}
        edge_values = {item_id for item_id in ids if item_id.startswith("edge_value:")}
        self.assertEqual(len(node_values), 101)
        self.assertEqual(
            edge_values,
            {
                'edge_value:joined="direct"',
                'edge_value:joined="indirect"',
                'edge_value:witness_resolution="unique"',
                'edge_value:witness_resolution="ambiguous"',
            },
        )

    def test_builder_has_no_network_text_fabric_or_tlhdig_runtime_import(self):
        text = BUILDER_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "requests",
            "urllib",
            "from tf.",
            "from tf import",
            "import tf.",
            "import TLHdig",
            "from TLHdig",
            "git clone",
            "curl ",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
