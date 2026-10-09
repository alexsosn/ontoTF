from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from tfont.coverage import (
    coverage_denominator_digest,
    coverage_report,
    load_coverage_manifest,
    validate_coverage_manifest,
)


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/coverage/build_i027a_bhsa_verbal_stems.py"
POLICY = ROOT / "docs/research/data/i027a/bhsa-verbal-stem-policy.json"
SOURCE = ROOT / "src/tfont/resources/coverage/p004-r011-baseline-v1/bhsa.json"
OUTPUT = ROOT / "src/tfont/resources/coverage/p004-i027a-bhsa-stems-v1/bhsa.json"

CODES = (
    "NA", "afel", "etpa", "etpe", "haf", "hif", "hit", "hof",
    "hotp", "hsht", "htpa", "htpe", "htpo", "nif", "nit",
    "pael", "pasq", "peal", "peil", "piel", "poal", "poel",
    "pual", "qal", "shaf", "tif",
)
SELECTED = {"node_feature:vs"} | {
    f"node_value:vs={json.dumps(code)}" for code in CODES
}


def load_builder():
    if not SCRIPT.is_file():
        raise AssertionError("RED: I-027A builder is absent")
    spec = importlib.util.spec_from_file_location("i027a_builder_red", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class I027AVerbalStemRedTests(unittest.TestCase):
    def test_tdd_outputs_exist(self):
        self.assertTrue(SCRIPT.is_file(), "RED: builder is absent")
        self.assertTrue(OUTPUT.is_file(), "RED: immutable successor is absent")

    def test_policy_targets_exact_native_family(self):
        p = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(p["schema_version"], 1)
        self.assertEqual(p["native_feature"], "vs")
        self.assertEqual(p["code_values"], list(CODES))
        self.assertEqual(p["expected_selected_items"], 27)
        self.assertEqual(p["expected_production_after"], 34)

    def test_successor_is_valid_and_preserves_denominator(self):
        module = load_builder()
        before = load_coverage_manifest(SOURCE)
        after = module.build_successor()
        validate_coverage_manifest(after)
        self.assertEqual(len(after["semantic_items"]), 219)
        self.assertEqual(after["denominator_digest"], before["denominator_digest"])
        self.assertEqual(coverage_denominator_digest(after), before["denominator_digest"])
        for identity in (
            "corpus_id", "repository", "denominator_source_revision",
            "target_corpus_revision", "tf_version", "scope_quality",
            "denominator_basis", "technical_exclusions", "accounting_gaps",
        ):
            self.assertEqual(after[identity], before[identity], identity)

    def test_exactly_27_reviewed_native_only_deltas(self):
        module = load_builder()
        before = load_coverage_manifest(SOURCE)
        after = module.build_successor()
        orig = {row["item_id"]: row for row in before["semantic_items"]}
        curr = {row["item_id"]: row for row in after["semantic_items"]}
        self.assertEqual(set(orig), set(curr))
        changed = {
            key for key in orig if orig[key]["accounting"] != curr[key]["accounting"]
        }
        self.assertEqual(changed, SELECTED)
        for item_id in SELECTED:
            old, new = orig[item_id], curr[item_id]
            self.assertIsNone(old["accounting"]["production"])
            self.assertEqual(
                old["accounting"]["research"], new["accounting"]["research"]
            )
            self.assertEqual(
                new["accounting"]["production"],
                {
                    "assessments": ["native-only"],
                    "common_target": False,
                    "source_ids": ["i027a:bhsa-vs-pinned-source-review"],
                    "profiles": ["linguistic"],
                    "capabilities": ["linguistic.morphology"],
                },
            )

    def test_current_production_exact_targets_are_preserved(self):
        module = load_builder()
        before = load_coverage_manifest(SOURCE)
        after = module.build_successor()
        original_production = {
            row["item_id"]: row["accounting"]["production"]
            for row in before["semantic_items"]
            if row["accounting"]["production"] is not None
        }
        successor_production = {
            row["item_id"]: row["accounting"]["production"]
            for row in after["semantic_items"]
        }
        for item_id, account in original_production.items():
            self.assertEqual(successor_production[item_id], account)
        report = coverage_report(after)
        self.assertEqual(report.production_reviewed_items, 34)
        self.assertEqual(report.production_common_target_items, 7)
        self.assertEqual(report.production_unreviewed_items, 185)
        self.assertEqual(report.production_outside_denominator_items, 0)

    def test_frozen_artifact_matches_exact_rebuild(self):
        module = load_builder()
        self.assertEqual(
            OUTPUT.read_text(encoding="utf-8"),
            module.serialized(module.build_successor()),
        )


if __name__ == "__main__":
    unittest.main()
