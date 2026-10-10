from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts/coverage/build_i027d_current_queue.py"


def builder():
    if not SCRIPT.is_file():
        raise AssertionError("RED: current selection builder absent")
    spec=importlib.util.spec_from_file_location("i027d_current_adversarial",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class CurrentQueueAdversarial(unittest.TestCase):
    def setUp(self):
        self.mod=builder()

    def manifests(self,corpus="bhsa"):
        mod=self.mod
        baseline=mod.load_json(mod.ROOT/f"src/tfont/resources/coverage/p004-r011-baseline-v1/{corpus}.json")
        final=mod.load_json(mod.ROOT/mod.load_selection()["selected_manifests"][corpus])
        return baseline, final

    def test_denominator_or_corpus_swap_fails_closed(self):
        old,new=self.manifests()
        for k,value in (("denominator_digest","sha256:"+"0"*64),
                        ("corpus_id","syriac"),("target_corpus_revision","bad")):
            altered=copy.deepcopy(new)
            altered[k]=value
            with self.subTest(k=k),self.assertRaises(ValueError):
                self.mod.validate_successor("bhsa",old,altered)

    def test_dropping_native_only_review_fails_closed(self):
        old,new=self.manifests()
        changed=copy.deepcopy(new)
        node=next(row for row in changed["semantic_items"] if row["item_id"]=='node_value:vs="NA"')
        self.assertIn("native-only",node["accounting"]["production"]["assessments"])
        node["accounting"]["production"]=None
        with self.assertRaises(ValueError):
            self.mod.validate_successor("bhsa",old,changed)

    def test_forged_research_account_or_source_binding_fails_closed(self):
        old,new=self.manifests()
        first=next(row for row in new["semantic_items"] if row["accounting"]["production"])
        for key in ("research","production"):
            altered=copy.deepcopy(new)
            node=next(row for row in altered["semantic_items"] if row["item_id"]==first["item_id"])
            if key=="research":
                node["accounting"]["research"]={"assessments":["exact"],"common_target":True,"source_ids":["forged"]}
            else:
                node["accounting"]["production"]["source_ids"]=["forged"]
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.mod.validate_successor("bhsa",old,altered)

    def test_reject_changed_kind_new_id_and_missing_gap(self):
        for corpus in ("bhsa","syriac"):
            old,new=self.manifests(corpus)
            altered=copy.deepcopy(new)
            altered["semantic_items"][0]["kind"]="edge_feature"
            with self.assertRaises(ValueError):
                self.mod.validate_successor(corpus,old,altered)
            altered=copy.deepcopy(new)
            altered["semantic_items"].pop()
            with self.assertRaises(ValueError):
                self.mod.validate_successor(corpus,old,altered)
            if old["accounting_gaps"]:
                altered=copy.deepcopy(new)
                altered["accounting_gaps"]=[]
                with self.assertRaises(ValueError):
                    self.mod.validate_successor(corpus,old,altered)

    def test_selection_rejects_historical_downgrade(self):
        sel=self.mod.load_selection()
        changed=copy.deepcopy(sel)
        changed["selected_manifests"]["bhsa"]="src/tfont/resources/coverage/p004-i027a-bhsa-stems-v1/bhsa.json"
        with self.assertRaises(ValueError):
            self.mod.build_current_queue(selection=changed)

if __name__=="__main__":
    unittest.main()
