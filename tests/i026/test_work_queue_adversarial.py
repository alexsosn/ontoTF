from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/coverage/build_i026_work_queue.py"
POLICY = ROOT / "docs/research/data/i026/p004-routing-policy.json"


def _load_builder():
    if not BUILDER.is_file():
        raise AssertionError("RED: I-026 work-queue builder is absent")
    spec = importlib.util.spec_from_file_location("i026_builder_adversarial", BUILDER)
    if spec is None or spec.loader is None:
        raise AssertionError("RED: cannot load I-026 builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _policy():
    return json.loads(POLICY.read_text(encoding="utf-8"))


class I026WorkQueueAdversarialTests(unittest.TestCase):
    def test_denominator_digest_drift_fails_closed(self):
        module = _load_builder()
        policy = _policy()
        policy["corpora"]["bhsa"]["denominator_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "denominator digest"):
            module.build_queue(policy=policy)

    def test_revision_drift_fails_closed(self):
        module = _load_builder()
        policy = _policy()
        policy["corpora"]["oracc"]["target_corpus_revision"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "target revision"):
            module.build_queue(policy=policy)

    def test_duplicate_primary_route_fails_closed(self):
        module = _load_builder()
        policy = _policy()
        policy["corpora"]["bhsa"]["routes"].setdefault("D", {}).setdefault(
            "node_features", []
        ).append("gn")
        with self.assertRaisesRegex(ValueError, "multiple primary routes"):
            module.build_queue(policy=policy)

    def test_policy_reference_to_absent_native_identity_fails_closed(self):
        module = _load_builder()
        policy = _policy()
        policy["corpora"]["cuc"]["routes"]["E"]["node_features"].append(
            "does_not_exist"
        )
        with self.assertRaisesRegex(ValueError, "absent native identity"):
            module.build_queue(policy=policy)

    def test_h_bucket_cannot_overlap_model_route(self):
        module = _load_builder()
        policy = _policy()
        policy["corpora"]["oracc"]["h_buckets"].setdefault(
            "native-only-candidate", {}
        ).setdefault("node_features", []).append("material")
        with self.assertRaisesRegex(ValueError, "H bucket overlaps"):
            module.build_queue(policy=policy)

    def test_missing_gap_route_fails_closed(self):
        module = _load_builder()
        policy = _policy()
        policy["accounting_gaps"] = []
        with self.assertRaisesRegex(ValueError, "accounting gap"):
            module.build_queue(policy=policy)

    def test_unexpected_gap_route_fails_closed(self):
        module = _load_builder()
        policy = _policy()
        fake = copy.deepcopy(policy["accounting_gaps"][0])
        fake["item_id"] = 'node_value:ls="fake"'
        policy["accounting_gaps"].append(fake)
        with self.assertRaisesRegex(ValueError, "accounting gap"):
            module.build_queue(policy=policy)

    def test_semantic_and_technical_identity_cannot_overlap(self):
        module = _load_builder()
        queue = module.build_queue()
        mutated = copy.deepcopy(queue)
        mutated["technical_exclusions"]["oracc"].append(
            mutated["semantic_rows"][0]["item_id"]
        )
        with self.assertRaisesRegex(ValueError, "semantic/technical overlap"):
            module.validate_queue(mutated)


if __name__ == "__main__":
    unittest.main()
