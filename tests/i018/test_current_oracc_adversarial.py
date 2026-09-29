from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tfont import coverage


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "scripts/coverage/build_i018_oracc_current.py"
EVIDENCE_PATH = ROOT / "docs/research/data/generated/i018/oracc-0.4.0.json"
POLICY_PATH = ROOT / "docs/research/data/i018/oracc-denominator-policy.json"
RESOURCE = "p004-oracc-0.4.0-f6f189b-v1"


def _builder_module():
    spec = importlib.util.spec_from_file_location("i018_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load I-018 builder")
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


class I018CurrentOraccAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = _builder_module()

    def test_technical_policy_rejects_absent_materialized_feature(self):
        policy = _json(POLICY_PATH)
        policy["technical_node_features"].append("not_materialized")
        with self.assertRaisesRegex(ValueError, "absent materialized"):
            _build_with(self.builder, policy=policy)

    def test_bounded_feature_reclassified_as_technical_fails(self):
        policy = _json(POLICY_PATH)
        policy["technical_node_features"].append("chunk_type")
        policy["technical_exclusion_details"]["node_feature:chunk_type"] = {
            "reason": "adversarial-overlap",
            "source_ids": ["review:I-018:adversarial"],
        }
        with self.assertRaisesRegex(ValueError, "not a semantic node feature"):
            _build_with(self.builder, policy=policy)

    def test_duplicate_bounded_values_fail_closed(self):
        policy = _json(POLICY_PATH)
        policy["bounded_node_values"]["chunk_type"].append("text")
        with self.assertRaisesRegex(ValueError, "contains duplicates"):
            _build_with(self.builder, policy=policy)

    def test_open_domain_observation_changes_do_not_change_denominator(self):
        baseline = _build_with(self.builder)
        evidence = _json(EVIDENCE_PATH)
        feature = evidence["node_features"]["translation_subtype"]
        feature["observed_unique_count"] = 2
        feature["observed_values"] = ["adversarial-a", "adversarial-b"]
        feature["domain_observation"] = "observed_small_domain"
        mutated = _build_with(self.builder, evidence=evidence)
        self.assertEqual(mutated["denominator_digest"], baseline["denominator_digest"])
        self.assertFalse(
            any(
                row["item_id"].startswith("node_value:translation_subtype=")
                for row in mutated["semantic_items"]
            )
        )

    def test_translation_source_singleton_change_does_not_create_value_item(self):
        baseline = _build_with(self.builder)
        evidence = _json(EVIDENCE_PATH)
        source = evidence["node_features"]["translation_source_name"]
        source["observed_unique_count"] = 1
        source["observed_values"] = ["different-release-local-name"]
        mutated = _build_with(self.builder, evidence=evidence)
        self.assertEqual(mutated["denominator_digest"], baseline["denominator_digest"])
        self.assertFalse(
            any(
                row["item_id"].startswith("node_value:translation_source_name=")
                for row in mutated["semantic_items"]
            )
        )

    def test_materialized_node_feature_drift_fails_fixed_contract(self):
        evidence = _json(EVIDENCE_PATH)
        del evidence["node_features"]["language"]
        with self.assertRaisesRegex(ValueError, "node-feature census drifted"):
            _build_with(self.builder, evidence=evidence)

    def test_materialized_edge_drift_fails_fixed_contract(self):
        evidence = _json(EVIDENCE_PATH)
        del evidence["edge_features"]["word_line"]
        with self.assertRaisesRegex(ValueError, "edge-feature census drifted"):
            _build_with(self.builder, evidence=evidence)

    def test_documented_only_translation_note_materialization_fails(self):
        evidence = _json(EVIDENCE_PATH)
        evidence["node_features"]["translation_note_text"] = copy.deepcopy(
            evidence["node_features"]["translation_text"]
        )
        with self.assertRaisesRegex(
            ValueError,
            "node-feature census drifted|translation-note schema became materialized",
        ):
            _build_with(self.builder, evidence=evidence)

    def test_candidate_tree_digest_mutation_fails_exact_identity(self):
        evidence = _json(EVIDENCE_PATH)
        evidence["candidate"]["candidate_tree_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "candidate identity drifted"):
            _build_with(self.builder, evidence=evidence)

    def test_tf_only_digest_mutation_fails_exact_identity(self):
        evidence = _json(EVIDENCE_PATH)
        evidence["candidate"]["tf_files_sha256"] = "1" * 64
        with self.assertRaisesRegex(ValueError, "candidate identity drifted"):
            _build_with(self.builder, evidence=evidence)

    def test_sidecar_set_or_size_mutation_fails_exact_identity(self):
        evidence = _json(EVIDENCE_PATH)
        evidence["sidecars"][0]["bytes"] += 1
        with self.assertRaisesRegex(ValueError, "sidecar identity drifted"):
            _build_with(self.builder, evidence=evidence)

        evidence = _json(EVIDENCE_PATH)
        evidence["sidecars"].append({"path": "invented.json", "bytes": 1})
        with self.assertRaisesRegex(ValueError, "sidecar identity drifted"):
            _build_with(self.builder, evidence=evidence)

    def test_translation_gap_records_are_not_fabricated_as_tf_items(self):
        manifest = coverage.load_packaged_coverage_manifest(RESOURCE, "oracc")
        semantic_ids = {row["item_id"] for row in manifest["semantic_items"]}
        self.assertIn("node_type:translation_unit", semantic_ids)
        self.assertFalse(any("translation_gap" in item_id for item_id in semantic_ids))
        self.assertFalse(any("translation_note" in item_id for item_id in semantic_ids))

    def test_historical_manifest_remains_unchanged(self):
        historical = coverage.load_p004_r011_baseline_manifests()["oracc"]
        self.assertEqual(len(historical["semantic_items"]), 42)
        self.assertEqual(
            historical["denominator_digest"],
            "sha256:019d19e1248a19238fc3eadc1fd6e05ae0d1c0f596f0a6ef991a93c09bd65685",
        )

    def test_builder_has_no_network_text_fabric_or_oracc_tf_dependency(self):
        text = BUILDER_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "requests",
            "urllib",
            "github.com",
            "from tf.",
            "from tf import",
            "import tf.",
            "import tf\n",
            "oracc_tf",
            "ORACC-TF import",
            "curl ",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
