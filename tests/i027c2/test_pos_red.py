from __future__ import annotations

import importlib
import importlib.util
import json
import unittest
from pathlib import Path

from tfont.semantic_validation import validate_semantic_bundle
from tfont.semantic_ir import SemanticKey, compile_semantic_ir
from tfont.production_bundles import load_production_verb_bundle

ROOT=Path(__file__).resolve().parents[2]
BASE="http://purl.org/olia/olia.owl#"

class POSAdjectiveAdverbRed(unittest.TestCase):
    def new_bundle(self, corpus):
        from tfont.production_bundles import load_production_adj_adv_bundle
        return load_production_adj_adv_bundle(corpus)

    def test_two_corpus_four_independent_positive_categories(self):
        bundles=tuple(validate_semantic_bundle(self.new_bundle(corpus))
                      for corpus in ("bhsa","syriac"))
        ir=compile_semantic_ir(bundles)
        for code, target in (("adjv","Adjective"),("advb","Adverb")):
            key=SemanticKey(profile_id="linguistic",capability_id="linguistic.part-of-speech",
                            target=BASE+target,formal_kind="class",semantic_role="annotation-value")
            rows=dict(ir.semantic_index)[key]
            self.assertEqual({row.corpus_id for row in rows},{"bhsa","syriac"})
            for row in rows:
                self.assertEqual(row.assessment,"exact")
                b=row.native_execution_binding
                self.assertEqual((b.node_type,b.feature,b.value,b.execution_shape),
                                 ("word","sp",code,"value-predicate"))

    def test_histories_unchanged_and_no_extra_biblical_mapping(self):
        from tfont.production_bundles import ProductionBundleError
        with self.assertRaises(ProductionBundleError):
            self.new_bundle("extrabiblical")
        for corpus in ("bhsa","syriac"):
            historical=load_production_verb_bundle(corpus)
            newest=self.new_bundle(corpus)
            self.assertEqual(historical.profile.data["profile_version"],"0.3.0")
            self.assertEqual(newest.profile.data["profile_version"],"0.4.0")
            a={m["mapping_id"]:m for m in historical.mappings.data["mappings"]}
            b={m["mapping_id"]:m for m in newest.mappings.data["mappings"]}
            self.assertEqual(set(b)-set(a),{
                f"mapping:{corpus}:olia-adjective",f"mapping:{corpus}:olia-adverb"
            })
            for mapping_id,m in a.items():
                self.assertEqual(m,b[mapping_id])
            ontology=newest.ontology_locks[0].data
            self.assertIn(BASE+"Adjective",ontology["terms_used"])
            self.assertIn(BASE+"Adverb",ontology["terms_used"])

    def test_coverage_successor_two_items_each(self):
        for corpus,expected in (("bhsa",(219,37,10,27)),("syriac",(74,9,9,0))):
            module=importlib.import_module("tfont.coverage")
            old=module.load_packaged_coverage_manifest(
                "p004-i027b1-bhsa-verb-v1" if corpus=="bhsa" else "p004-i027b2-syriac-verb-v1",
                corpus)
            current=module.load_packaged_coverage_manifest(
                "p004-i027c2-bhsa-adj-adv-v1" if corpus=="bhsa" else "p004-i027c2-syriac-adj-adv-v1",
                corpus)
            self.assertEqual(old["denominator_digest"],current["denominator_digest"])
            prev={r["item_id"]:r for r in old["semantic_items"]}
            next_={r["item_id"]:r for r in current["semantic_items"]}
            self.assertEqual(set(prev),set(next_))
            changes={k for k in next_
                     if prev[k]["accounting"]!=next_[k]["accounting"]}
            self.assertEqual(changes,{'node_value:sp="adjv"','node_value:sp="advb"'})
            for code,target in (("adjv","adjective"),("advb","adverb")):
                a=next_[f'node_value:sp="{code}"']["accounting"]["production"]
                self.assertEqual(a,{"assessments":["exact"],"common_target":True,
                    "source_ids":[f"mapping:{corpus}:olia-{target}"],
                    "profiles":["linguistic"],"capabilities":["linguistic.part-of-speech"]})
            report=module.coverage_report(current)
            self.assertEqual((report.semantic_items,report.production_reviewed_items,
                              report.production_common_target_items,
                              dict(report.production_assessment_counts).get("native-only",0)),expected)
            self.assertEqual(old["accounting_gaps"],current["accounting_gaps"])

    def test_reproduce_immutable_coverage_builders(self):
        for corpus in ("bhsa","syriac"):
            path=ROOT/f"scripts/coverage/build_i027c2_{corpus}_adj_adv.py"
            self.assertTrue(path.is_file(),f"RED missing {corpus} deterministic builder")
            spec=importlib.util.spec_from_file_location(f"i027c2_{corpus}",path)
            assert spec and spec.loader
            mod=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.assertEqual(mod.OUTPUT.read_text(encoding="utf-8"),
                             mod.serialized(mod.build_successor()))

if __name__=="__main__":
    unittest.main()
