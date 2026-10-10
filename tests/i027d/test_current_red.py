from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

from tfont.coverage import coverage_denominator_digest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/coverage/build_i027d_current_queue.py"
OUTPUT = ROOT / "docs/research/data/generated/i027d/p004-current-work-queue.json"
SELECTOR = ROOT / "docs/research/data/i027d/p004-current-manifest-selection.json"
LEGACY = ROOT / "docs/research/data/generated/i026/p004-work-queue.json"
EXPECTED = {"C":380,"D":67,"E":153,"F":161,"G":39,"H":134}


def builder():
    if not SCRIPT.is_file():
        raise AssertionError("RED: current selection builder missing")
    spec = importlib.util.spec_from_file_location("i027d_current_builder", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CurrentQueueRed(unittest.TestCase):
    def test_current_release_selection_and_output_are_immutable(self):
        self.assertTrue(SELECTOR.is_file(), "RED: versioned selection is absent")
        self.assertTrue(SCRIPT.is_file(), "RED: current queue builder is absent")
        self.assertTrue(OUTPUT.is_file(), "RED: versioned current queue is absent")

    def test_current_queue_uses_exact_reviewed_corpus_sources(self):
        mod = builder()
        current = mod.build_current_queue()
        legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
        self.assertEqual(current["counts"], legacy["counts"])
        self.assertEqual(current["counts"]["aggregate_workstreams"], EXPECTED)
        self.assertEqual(current["invariants"], legacy["invariants"])
        self.assertEqual(len(current["semantic_rows"]), 934)
        self.assertEqual(current["counts"]["technical_exclusions"], 15)
        self.assertEqual(current["current_view"]["view_id"], "p004-current-v1")
        self.assertEqual(current["current_view"]["underlying_policy_id"], "p004-routing-v1")
        expected = {
            "bhsa": ("p004-i027b1-bhsa-verb-v1", 35, 8),
            "syriac": ("p004-i027b2-syriac-verb-v1", 7, 7),
            "extrabiblical": ("p004-i027b4-extrabiblical-verb-v1", 8, 8),
        }
        for corpus,(manifest,reviewed,shared) in expected.items():
            info=current["current_view"]["production_by_corpus"][corpus]
            self.assertEqual(info["reviewed_items"], reviewed)
            self.assertEqual(info["shared_target_items"], shared)
            self.assertIn(manifest, current["manifest_bindings"][corpus]["manifest"])
        old={(row["corpus_id"],row["item_id"]):row for row in legacy["semantic_rows"]}
        new={(row["corpus_id"],row["item_id"]):row for row in current["semantic_rows"]}
        self.assertEqual(set(old),set(new))
        for k,row in new.items():
            self.assertEqual(
                {key:value for key,value in row.items() if key!="existing_accounting"},
                {key:value for key,value in old[k].items() if key!="existing_accounting"},
            )

    def test_historical_queue_stays_frozen(self):
        mod=builder()
        mod.verify_historical_queue()
        self.assertEqual(
            json.loads(LEGACY.read_text(encoding="utf-8"))["manifest_bindings"]["bhsa"]["manifest"],
            "src/tfont/resources/coverage/p004-r011-baseline-v1/bhsa.json"
        )

    def test_stable_output_rebuild(self):
        mod=builder()
        self.assertEqual(OUTPUT.read_text(encoding="utf-8"),
                         mod.serialized(mod.build_current_queue()))


if __name__=="__main__":
    unittest.main()
