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
BUILDER_PATH = ROOT / "scripts/coverage/build_i017_pseudepigrapha_v1.py"
EVIDENCE_PATH = ROOT / "docs/research/data/generated/i017/pseudepigrapha-v1.0.0.json"
POLICY_PATH = ROOT / "docs/research/data/i017/pseudepigrapha-denominator-policy.json"
RESOURCE = "p004-pseudepigrapha-v1.0.0-v1"


def _builder_module():
    spec = importlib.util.spec_from_file_location("i017_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load I-017 builder")
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


class I017CurrentPseudepigraphaAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = _builder_module()

    def test_partial_or_malformed_artifact_identity_is_rejected(self):
        manifest = coverage.load_packaged_coverage_manifest(RESOURCE, "pseudepigrapha")

        partial = copy.deepcopy(manifest)
        del partial["denominator_basis"]["artifact_identity"]["materialized_sha256"]
        with self.assertRaises(SourceValidationError):
            coverage.validate_coverage_manifest(partial)

        malformed = copy.deepcopy(manifest)
        malformed["denominator_basis"]["artifact_identity"]["sha256"] = "sha256:not-raw-hex"
        with self.assertRaises(SourceValidationError):
            coverage.validate_coverage_manifest(malformed)

    def test_historical_manifest_without_artifact_identity_keeps_digest(self):
        historical = coverage.load_p004_r011_baseline_manifests()["pseudepigrapha"]
        self.assertNotIn("artifact_identity", historical["denominator_basis"])
        self.assertEqual(
            coverage.coverage_denominator_digest(historical),
            "sha256:d45c83f4afb51cae81405205b2111f7329ed65d5d85b5268719717fb64286746",
        )

    def test_policy_rejects_absent_materialized_technical_feature(self):
        policy = _json(POLICY_PATH)
        policy["technical_node_features"].append("not_materialized")
        with self.assertRaisesRegex(ValueError, "absent materialized"):
            _build_with(self.builder, policy=policy)

    def test_policy_rejects_semantic_bounded_feature_reclassified_as_technical(self):
        policy = _json(POLICY_PATH)
        policy["technical_node_features"].append("generation_marker")
        policy["technical_exclusion_details"]["node_feature:generation_marker"] = {
            "reason": "adversarial-overlap",
            "source_ids": ["review:I-017:adversarial"],
        }
        with self.assertRaisesRegex(ValueError, "not a semantic node feature"):
            _build_with(self.builder, policy=policy)

    def test_duplicate_bounded_values_fail_closed(self):
        policy = _json(POLICY_PATH)
        policy["bounded_node_values"]["version_kind"].append("source")
        with self.assertRaisesRegex(ValueError, "contains duplicates"):
            _build_with(self.builder, policy=policy)

    def test_open_domain_observations_do_not_change_denominator(self):
        baseline = _build_with(self.builder)
        evidence = _json(EVIDENCE_PATH)
        language = evidence["node_features"]["language"]
        language["domain_observation"] = "observed_small_domain"
        language["observed_unique_count"] = 2
        language["observed_values"] = ["adversarial-a", "adversarial-b"]

        mutated = _build_with(self.builder, evidence=evidence)
        self.assertEqual(
            mutated["denominator_digest"],
            baseline["denominator_digest"],
        )
        self.assertFalse(
            any(
                row["item_id"].startswith("node_value:language=")
                for row in mutated["semantic_items"]
            )
        )

    def test_materialized_feature_set_drift_fails_closed(self):
        evidence = _json(EVIDENCE_PATH)
        del evidence["node_features"]["language"]
        with self.assertRaisesRegex(ValueError, "semantic denominator count drifted"):
            _build_with(self.builder, evidence=evidence)

    def test_warp_feature_policy_must_exactly_match_inventory(self):
        policy = _json(POLICY_PATH)
        policy["technical_warp_edge_features"] = []
        with self.assertRaisesRegex(ValueError, "does not exactly account"):
            _build_with(self.builder, policy=policy)

    def test_builder_has_no_network_or_text_fabric_dependency(self):
        text = BUILDER_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "requests",
            "urllib",
            "github.com",
            "from tf",
            "import tf",
            "Fabric(",
            "curl ",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
