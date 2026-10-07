from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/coverage/build_i026_work_queue.py"
POLICY = ROOT / "docs/research/data/i026/p004-routing-policy.json"
GENERATED = ROOT / "docs/research/data/generated/i026/p004-work-queue.json"

EXPECTED_PER_CORPUS = {
    "bhsa": {"C": 149, "D": 22, "E": 0, "F": 6, "G": 0, "H": 42},
    "cuc": {"C": 0, "D": 2, "E": 23, "F": 1, "G": 10, "H": 1},
    "syriac": {"C": 61, "D": 5, "E": 0, "F": 0, "G": 0, "H": 8},
    "extrabiblical": {"C": 113, "D": 10, "E": 0, "F": 2, "G": 0, "H": 11},
    "pseudepigrapha": {"C": 0, "D": 8, "E": 0, "F": 80, "G": 0, "H": 25},
    "oracc": {"C": 11, "D": 13, "E": 40, "F": 18, "G": 0, "H": 17},
    "tlhdig": {"C": 46, "D": 7, "E": 90, "F": 51, "G": 29, "H": 33},
}
EXPECTED_AGGREGATE = {"C": 380, "D": 67, "E": 153, "F": 158, "G": 39, "H": 137}


def _load_builder():
    if not BUILDER.is_file():
        raise AssertionError("RED: I-026 work-queue builder is absent")
    spec = importlib.util.spec_from_file_location("i026_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise AssertionError("RED: cannot load I-026 builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class I026WorkQueueRedTests(unittest.TestCase):
    def test_builder_and_generated_artifact_exist(self):
        self.assertTrue(BUILDER.is_file(), "RED: I-026 builder is absent")
        self.assertTrue(GENERATED.is_file(), "RED: I-026 generated queue is absent")

    def test_policy_pins_seven_current_manifests(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(policy["schema_version"], 1)
        self.assertEqual(policy["policy_id"], "p004-routing-v1")
        self.assertEqual(policy["expected_semantic_items"], 934)
        self.assertEqual(policy["expected_technical_exclusions"], 15)
        self.assertEqual(policy["corpus_order"], list(EXPECTED_PER_CORPUS))
        self.assertEqual(set(policy["workstreams"]), set("CDEFGH"))
        for corpus, expected in EXPECTED_PER_CORPUS.items():
            self.assertEqual(policy["corpora"][corpus]["expected_counts"], expected)

    def test_generated_queue_exact_counts_and_zero_orphans(self):
        module = _load_builder()
        queue = module.build_queue()
        self.assertEqual(len(queue["semantic_rows"]), 934)
        self.assertEqual(queue["counts"]["aggregate_workstreams"], EXPECTED_AGGREGATE)
        self.assertEqual(queue["counts"]["per_corpus"], EXPECTED_PER_CORPUS)
        self.assertEqual(queue["counts"]["technical_exclusions"], 15)
        self.assertTrue(queue["invariants"]["zero_orphans"])
        self.assertTrue(queue["invariants"]["unique_primary_owner"])
        self.assertTrue(queue["invariants"]["technical_disjoint"])
        h_buckets = {}
        for row in queue["semantic_rows"]:
            if row["workstream"] == "H":
                h_buckets[row["routing_bucket"]] = h_buckets.get(row["routing_bucket"], 0) + 1
        self.assertEqual(h_buckets, {"cross-model": 7, "native-only-candidate": 130})

    def test_every_manifest_item_is_present_exactly_once(self):
        module = _load_builder()
        queue = module.build_queue()
        rows = queue["semantic_rows"]
        keys = [(row["corpus_id"], row["item_id"]) for row in rows]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(row["workstream"] for row in rows), set("CDEFGH"))
        self.assertTrue(all(type(row["owner_issue"]) is int for row in rows))
        self.assertTrue(all(row["evidence_source"] and row["evidence_pointer"] for row in rows))

    def test_node_and_edge_values_inherit_parent_route(self):
        module = _load_builder()
        queue = module.build_queue()
        index = {(row["corpus_id"], row["item_id"]): row for row in queue["semantic_rows"]}
        for row in queue["semantic_rows"]:
            item_id = row["item_id"]
            if item_id.startswith("node_value:"):
                feature = item_id.split(":", 1)[1].split("=", 1)[0]
                parent = index[(row["corpus_id"], f"node_feature:{feature}")]
                self.assertEqual(row["workstream"], parent["workstream"])
                if row["workstream"] == "H":
                    self.assertEqual(row["routing_bucket"], parent["routing_bucket"])
            elif item_id.startswith("edge_value:"):
                feature = item_id.split(":", 1)[1].split("=", 1)[0]
                parent = index[(row["corpus_id"], f"edge_feature:{feature}")]
                self.assertEqual(row["workstream"], parent["workstream"])
                if row["workstream"] == "H":
                    self.assertEqual(row["routing_bucket"], parent["routing_bucket"])

    def test_technical_exclusions_are_separate(self):
        module = _load_builder()
        queue = module.build_queue()
        semantic = {(row["corpus_id"], row["item_id"]) for row in queue["semantic_rows"]}
        technical = {
            (corpus, item_id)
            for corpus, item_ids in queue["technical_exclusions"].items()
            for item_id in item_ids
        }
        self.assertTrue(semantic.isdisjoint(technical))
        self.assertEqual(len(technical), 15)

    def test_syriac_outside_denominator_gap_is_routed_but_not_counted(self):
        module = _load_builder()
        queue = module.build_queue()
        gaps = queue["accounting_gaps"]
        self.assertEqual(len(gaps), 1)
        gap = gaps[0]
        self.assertEqual(gap["corpus_id"], "syriac")
        self.assertEqual(gap["item_id"], 'node_value:ls="prop"')
        self.assertEqual(gap["reason"], "outside-denominator")
        self.assertEqual(gap["workstream"], "C")
        self.assertEqual(gap["owner_issue"], 264)
        self.assertFalse(
            any(
                row["corpus_id"] == "syriac" and row["item_id"] == gap["item_id"]
                for row in queue["semantic_rows"]
            )
        )

    def test_frozen_artifact_matches_rebuild(self):
        module = _load_builder()
        rebuilt = module.serialized(module.build_queue())
        self.assertEqual(GENERATED.read_text(encoding="utf-8"), rebuilt)


if __name__ == "__main__":
    unittest.main()
