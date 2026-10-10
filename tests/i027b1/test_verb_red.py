from __future__ import annotations

import importlib
import importlib.util
import json
import unittest
from importlib.resources import files

from tfont.coverage import (
    coverage_denominator_digest,
    coverage_report,
    load_packaged_coverage_manifest,
)
from tfont.semantic_ir import SemanticKey, compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


BASE = "http://purl.org/olia/olia.owl#"
PROFILE_VERSION = "0.3.0"


class I027B1VerbRedTests(unittest.TestCase):
    def test_versioned_verb_loader_exists(self):
        loader = importlib.import_module("tfont.production_bundles")
        self.assertTrue(
            hasattr(loader, "load_production_verb_bundle"),
            "RED: no separately versioned OLiA Verb production loader",
        )

    def test_new_verb_bundle_compiles_as_exact_word_selector(self):
        loader = importlib.import_module("tfont.production_bundles")
        bundle = loader.load_production_verb_bundle("bhsa")
        self.assertEqual(bundle.profile.data["profile_version"], PROFILE_VERSION)
        validated = validate_semantic_bundle(bundle)
        ir = compile_semantic_ir((validated,))
        key = SemanticKey(
            profile_id="linguistic",
            capability_id="linguistic.part-of-speech",
            target=BASE + "Verb",
            formal_kind="class",
            semantic_role="annotation-value",
        )
        records = dict(ir.semantic_index)[key]
        self.assertEqual(len(records), 1)
        only = records[0]
        self.assertEqual(only.corpus_id, "bhsa")
        self.assertEqual(only.assessment, "exact")
        native = only.native_execution_binding
        self.assertEqual(native.node_type, "word")
        self.assertEqual(native.feature, "sp")
        self.assertEqual(native.value, "verb")
        self.assertEqual(native.execution_shape, "value-predicate")
        self.assertNotEqual(native.node_type, "lex")
        self.assertIn(BASE + "Verb", bundle.ontology_locks[0].data["terms_used"])

    def test_new_release_preserves_noun_and_morphology_semantics(self):
        loader = importlib.import_module("tfont.production_bundles")
        old = validate_semantic_bundle(loader.load_production_linguistic_bundle("bhsa"))
        new = validate_semantic_bundle(loader.load_production_verb_bundle("bhsa"))
        old_by_id = dict(old.indexes.mappings)
        new_by_id = dict(new.indexes.mappings)
        self.assertEqual(set(new_by_id), set(old_by_id) | {"mapping:bhsa:olia-verb"})
        for mapping_id, old_row in old_by_id.items():
            self.assertEqual(old_row, new_by_id[mapping_id])
        self.assertEqual(
            loader.load_production_linguistic_bundle("bhsa").profile.data["profile_version"],
            "0.2.0",
        )

    def test_immutable_coverage_successor_adds_one_reviewed_target(self):
        before = load_packaged_coverage_manifest("p004-i027a-bhsa-stems-v1", "bhsa")
        after = load_packaged_coverage_manifest("p004-i027b1-bhsa-verb-v1", "bhsa")
        self.assertEqual(after["corpus_id"], "bhsa")
        self.assertEqual(coverage_denominator_digest(before), coverage_denominator_digest(after))
        self.assertEqual(after["denominator_digest"], before["denominator_digest"])
        old_rows = {row["item_id"]: row for row in before["semantic_items"]}
        new_rows = {row["item_id"]: row for row in after["semantic_items"]}
        self.assertEqual(set(old_rows), set(new_rows))
        changed = [
            item_id for item_id in old_rows
            if old_rows[item_id]["accounting"] != new_rows[item_id]["accounting"]
        ]
        self.assertEqual(changed, ['node_value:sp="verb"'])
        updated = new_rows[changed[0]]["accounting"]["production"]
        self.assertEqual(updated["assessments"], ["exact"])
        self.assertTrue(updated["common_target"])
        self.assertEqual(updated["profiles"], ["linguistic"])
        self.assertEqual(updated["capabilities"], ["linguistic.part-of-speech"])
        self.assertEqual(updated["source_ids"], ["mapping:bhsa:olia-verb"])
        report = coverage_report(after)
        self.assertEqual(report.production_reviewed_items, 35)
        self.assertEqual(report.production_common_target_items, 8)
        self.assertEqual(report.production_unreviewed_items, 184)

    def test_verb_does_not_forge_stem_or_non_word_bindings(self):
        loader = importlib.import_module("tfont.production_bundles")
        bundle = loader.load_production_verb_bundle("bhsa")
        verb = next(
            item for item in bundle.mappings.data["mappings"]
            if item["mapping_id"] == "mapping:bhsa:olia-verb"
        )
        self.assertEqual(verb["native_binding"], {
            "component_id": "bhsa-tf",
            "execution_shape": "value-predicate",
            "feature": "sp",
            "node_type": "word",
            "value": "verb",
        })
        self.assertNotIn("vs", json.dumps(verb["native_binding"]))
        self.assertEqual(verb["projections"][0]["target"], BASE + "Verb")
        self.assertEqual(verb["projections"][0]["assessment"], "exact")

    def test_coverage_successor_is_byte_for_byte_reproducible(self):
        root = files("tfont").joinpath("resources", "coverage")
        actual = root.joinpath("p004-i027b1-bhsa-verb-v1", "bhsa.json").read_text(
            encoding="utf-8"
        )
        from pathlib import Path
        script = Path(__file__).resolve().parents[2] / "scripts/coverage/build_i027b1_bhsa_verb.py"
        self.assertTrue(script.is_file())
        spec = importlib.util.spec_from_file_location("i027b1_coverage_builder", script)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(actual, module.serialized(module.build_successor()))


if __name__ == "__main__":
    unittest.main()
