from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from tfont.coverage import (
    coverage_denominator_digest, coverage_report, load_packaged_coverage_manifest,
)
from tfont.production_bundles import (
    load_production_linguistic_bundle, load_production_verb_bundle,
)
from tfont.semantic_ir import SemanticKey, compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


BASE = "http://purl.org/olia/olia.owl#"
ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/coverage/build_i027b4_extrabiblical_verb.py"
OUTPUT = ROOT / "src/tfont/resources/coverage/p004-i027b4-extrabiblical-verb-v1/extrabiblical.json"


def build_from_disk():
    self_spec = importlib.util.spec_from_file_location("i027b4_builder", BUILDER)
    assert self_spec is not None and self_spec.loader is not None
    module = importlib.util.module_from_spec(self_spec)
    self_spec.loader.exec_module(module)
    return module


class ExtraBiblicalVerbRedTests(unittest.TestCase):
    def test_immutable_verb_release_exists_with_exact_word_mapping(self):
        old = load_production_linguistic_bundle("extrabiblical")
        new = load_production_verb_bundle("extrabiblical")
        self.assertEqual(old.profile.data["profile_version"], "0.2.0")
        self.assertEqual(new.profile.data["profile_version"], "0.3.0")
        validated = validate_semantic_bundle(new)
        ir = compile_semantic_ir((validated,))
        key = SemanticKey(
            profile_id="linguistic", capability_id="linguistic.part-of-speech",
            target=BASE + "Verb", formal_kind="class",
            semantic_role="annotation-value",
        )
        rows = dict(ir.semantic_index)[key]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.corpus_id, "extrabiblical")
        self.assertEqual(row.assessment, "exact")
        binding = row.native_execution_binding
        self.assertEqual(
            (binding.component_id, binding.node_type, binding.feature,
             binding.value, binding.execution_shape),
            ("extrabiblical-tf", "word", "sp", "verb", "value-predicate"),
        )
        self.assertIn(BASE + "Verb", new.ontology_locks[0].data["terms_used"])

    def test_old_reviewed_mapping_and_loader_identity_stays_immutable(self):
        old = validate_semantic_bundle(load_production_linguistic_bundle("extrabiblical"))
        new = validate_semantic_bundle(load_production_verb_bundle("extrabiblical"))
        old_map, new_map = dict(old.indexes.mappings), dict(new.indexes.mappings)
        self.assertEqual(set(new_map), set(old_map) | {"mapping:extrabiblical:olia-verb"})
        for mapping_id, original in old_map.items():
            self.assertEqual(original, new_map[mapping_id])

    def test_positive_mapping_evidence_and_no_stem_inference(self):
        b = load_production_verb_bundle("extrabiblical")
        target = next(
            row for row in b.mappings.data["mappings"]
            if row["mapping_id"] == "mapping:extrabiblical:olia-verb"
        )
        self.assertEqual(target["native_binding"], {
            "component_id":"extrabiblical-tf", "execution_shape":"value-predicate",
            "feature":"sp", "node_type":"word", "value":"verb"
        })
        self.assertNotIn("vs", json.dumps(target["native_binding"]))
        self.assertEqual(len(target["projections"]), 1)
        self.assertEqual(target["projections"][0]["target"], BASE + "Verb")
        self.assertEqual(target["projections"][0]["assessment"], "exact")
        self.assertTrue(
            any(x["evidence_id"] == "evidence:extrabiblical:word-sp-verb-source"
                for x in target["evidence"])
        )

    def test_only_verb_coverage_accounting_delta(self):
        old = load_packaged_coverage_manifest("p004-r011-baseline-v1", "extrabiblical")
        new = load_packaged_coverage_manifest("p004-i027b4-extrabiblical-verb-v1", "extrabiblical")
        self.assertEqual(new["denominator_digest"], old["denominator_digest"])
        self.assertEqual(
            coverage_denominator_digest(new), coverage_denominator_digest(old)
        )
        self.assertEqual(new["accounting_gaps"], old["accounting_gaps"])
        original={row["item_id"]:row for row in old["semantic_items"]}
        updated={row["item_id"]:row for row in new["semantic_items"]}
        self.assertEqual(set(original),set(updated))
        self.assertEqual(
            {k for k in original if original[k]["accounting"]!=updated[k]["accounting"]},
            {'node_value:sp="verb"'},
        )
        self.assertEqual(updated['node_value:sp="verb"']["accounting"]["production"],{
            "assessments":["exact"], "common_target":True,
            "source_ids":["mapping:extrabiblical:olia-verb"],
            "profiles":["linguistic"], "capabilities":["linguistic.part-of-speech"]
        })
        report=coverage_report(new)
        self.assertEqual(report.production_reviewed_items,8)
        self.assertEqual(report.production_common_target_items,8)
        self.assertEqual(report.production_unreviewed_items,128)
        self.assertEqual(report.semantic_items,136)
        self.assertFalse(report.bounded_scope_complete)

    def test_coverage_builder_byte_for_byte_reproduces_packaged_artifact(self):
        self.assertTrue(BUILDER.is_file(), "RED: no coverage successor generator")
        self.assertTrue(OUTPUT.is_file(), "RED: no immutable coverage successor")
        module=build_from_disk()
        self.assertEqual(
            OUTPUT.read_text(encoding="utf-8"),
            module.serialized(module.build_successor())
        )


if __name__ == "__main__":
    unittest.main()
