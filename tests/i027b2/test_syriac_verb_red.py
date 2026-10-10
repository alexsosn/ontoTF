from __future__ import annotations

import unittest

from tfont.coverage import coverage_denominator_digest, coverage_report, load_packaged_coverage_manifest
from tfont.semantic_ir import SemanticKey, compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle
from tfont.production_bundles import load_production_linguistic_bundle


TARGET = "http://purl.org/olia/olia.owl#Verb"


class SyriacVerbRedTests(unittest.TestCase):
    def test_separately_versioned_syriac_verb_loader(self):
        from tfont.production_bundles import load_production_verb_bundle
        bundle = load_production_verb_bundle("syriac")
        self.assertEqual(bundle.profile.data["profile_version"], "0.3.0")
        self.assertEqual(
            load_production_linguistic_bundle("syriac").profile.data["profile_version"],
            "0.2.0",
        )
        ir = compile_semantic_ir((validate_semantic_bundle(bundle),))
        key = SemanticKey(
            profile_id="linguistic", capability_id="linguistic.part-of-speech",
            target=TARGET, formal_kind="class", semantic_role="annotation-value"
        )
        rows = dict(ir.semantic_index)[key]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.corpus_id, "syriac")
        self.assertEqual(row.assessment, "exact")
        native = row.native_execution_binding
        self.assertEqual(
            (native.component_id, native.node_type, native.feature, native.value),
            ("syriac-tf", "word", "sp", "verb"),
        )
        self.assertEqual(native.execution_shape, "value-predicate")

    def test_syriac_verb_preserves_all_historical_reviewed_mappings(self):
        from tfont.production_bundles import load_production_verb_bundle
        old = validate_semantic_bundle(load_production_linguistic_bundle("syriac"))
        new = validate_semantic_bundle(load_production_verb_bundle("syriac"))
        a, b = dict(old.indexes.mappings), dict(new.indexes.mappings)
        self.assertEqual(set(b), set(a) | {"mapping:syriac:olia-verb"})
        for mapping_id in a:
            self.assertEqual(a[mapping_id], b[mapping_id])

    def test_syriac_verb_coverage_successor_is_one_item_delta(self):
        old = load_packaged_coverage_manifest("p004-r011-baseline-v1", "syriac")
        new = load_packaged_coverage_manifest("p004-i027b2-syriac-verb-v1", "syriac")
        self.assertEqual(old["denominator_digest"], new["denominator_digest"])
        self.assertEqual(coverage_denominator_digest(old), coverage_denominator_digest(new))
        self.assertEqual(old["accounting_gaps"], new["accounting_gaps"])
        self.assertEqual(len(new["accounting_gaps"]), 1)
        self.assertEqual(new["accounting_gaps"][0]["item_id"], 'node_value:ls="prop"')
        by_id = {row["item_id"]: row for row in old["semantic_items"]}
        after = {row["item_id"]: row for row in new["semantic_items"]}
        self.assertEqual(set(by_id), set(after))
        changed = {
            key for key in by_id
            if by_id[key]["accounting"] != after[key]["accounting"]
        }
        self.assertEqual(changed, {'node_value:sp="verb"'})
        value = after['node_value:sp="verb"']["accounting"]["production"]
        self.assertEqual(value, {
            "assessments":["exact"], "common_target":True,
            "source_ids":["mapping:syriac:olia-verb"],
            "profiles":["linguistic"], "capabilities":["linguistic.part-of-speech"],
        })
        report = coverage_report(new)
        self.assertEqual(report.production_reviewed_items, 7)
        self.assertEqual(report.production_common_target_items, 7)
        self.assertEqual(report.production_unreviewed_items, 67)
        self.assertEqual(report.production_outside_denominator_items, 1)
        self.assertFalse(report.bounded_scope_complete)

    def test_no_syriac_stem_inferred_from_pos_verb(self):
        from tfont.production_bundles import load_production_verb_bundle
        m = next(
            item for item in load_production_verb_bundle("syriac").mappings.data["mappings"]
            if item["mapping_id"] == "mapping:syriac:olia-verb"
        )
        self.assertEqual(m["native_binding"]["feature"], "sp")
        self.assertEqual(m["native_binding"]["value"], "verb")
        self.assertNotIn("vs", m["native_binding"])
        self.assertEqual(len(m["projections"]), 1)
        self.assertEqual(m["projections"][0]["target"], TARGET)


if __name__ == "__main__":
    unittest.main()
