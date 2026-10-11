"""Batch native-only upgrade preflight, using real published BHSA evidence but
SYNTHETIC historical predecessor decisions. No release authentication."""
from __future__ import annotations
import copy
import unittest

from tfont.release_registry import load_profile
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2
from tfont.mapping_supersession import (
    NativeSupersessionError,
    plan_native_only_supersession_batch,
    verify_supersession_batch_preview,
)


def two_real_source_synthetic_transitions():
    bundle=load_profile("bhsa", release_id="0.4.0")
    originals=[m for m in bundle.mappings.data["mappings"]
               if m["mapping_id"] in {
                  "mapping:bhsa:olia-adjective", "mapping:bhsa:olia-adverb"}]
    assert len(originals)==2
    evidence={e.data["evidence_id"]:copy.deepcopy(e.data) for e in bundle.evidences}
    native=evidence["evidence:bhsa:word-sp-adj-adv-source"]
    lock=copy.deepcopy(bundle.ontology_locks[0].data)
    transitions=[]
    previous=[]
    for m in originals:
        term=m["projections"][0]["target"].split("#")[-1].lower()
        old=copy.deepcopy(m)
        old["mapping_id"]=f"mapping:bhsa:native-sp-{old['native_binding']['value']}"
        old["native_state"]="native-only"
        old["projections"]=[]
        old["evidence"]=[ref for ref in old["evidence"] if ref["evidence_id"].startswith("evidence:bhsa:")]
        old["mapping_semantic_digest"]=mapping_semantic_digest_v2(old)
        old["review"]["reviewed_mapping_digest"]=old["mapping_semantic_digest"]
        candidate=copy.deepcopy(m)
        candidate["mapping_id"]=f"mapping:bhsa:olia-{term}-after-native"
        del candidate["review"]
        del candidate["projections"][0]["review"]
        candidate["mapping_semantic_digest"]=mapping_semantic_digest_v2(candidate)
        ontology=evidence[f"evidence:olia:{term}-class"]
        transitions.append({
            "previous":old, "candidate":candidate,
            "native_evidence":copy.deepcopy(native),
            "ontology_evidence":copy.deepcopy(ontology),
            "ontology_lock":copy.deepcopy(lock)
        })
        previous.append(old)
    return transitions,previous


class BatchSupersessionRed(unittest.TestCase):
    def setup(self):
        transitions,active=two_real_source_synthetic_transitions()
        return transitions,active

    def plan(self, transitions=None,active=None,base_release="bhsa/0.4.0"):
        t,a=self.setup()
        return plan_native_only_supersession_batch(
           transitions=t if transitions is None else transitions,
           active_mappings=a if active is None else active,
           base_release=base_release)

    def test_two_source_bound_transitions_one_deterministic_batch(self):
        t,a=self.setup()
        copy_inputs=copy.deepcopy((t,a))
        pack=self.plan(transitions=t,active=a)
        self.assertEqual((t,a),copy_inputs)
        self.assertEqual(pack["schema_version"],1)
        self.assertEqual(pack["authority"],"untrusted-supersession-batch-preview")
        self.assertIs(pack["release_authorized"],False)
        self.assertEqual(pack["transition_kind"],"native-only-to-exact-batch")
        self.assertEqual(pack["base_release"],"bhsa/0.4.0")
        self.assertEqual(pack["count"],2)
        self.assertEqual(len(pack["transitions"]),2)
        self.assertEqual([r["retired"]["mapping_id"] for r in pack["transitions"]],
                         sorted(r["retired"]["mapping_id"] for r in pack["transitions"]))
        self.assertEqual(pack,self.plan(transitions=list(reversed(t)),active=list(reversed(a))))
        self.assertTrue(pack["content_digest"].startswith("sha256:"))
        self.assertNotIn("reviewer",pack)
        self.assertNotIn("new_active_mappings",pack)
        self.assertNotIn("coverage",pack)
        self.assertNotIn("registry_release",pack)
        self.assertIsNone(verify_supersession_batch_preview(
            pack,transitions=t,base_release="bhsa/0.4.0",active_mappings=a))

    def test_one_accepted_transition_allowed_without_ten_accepts(self):
        t,a=self.setup()
        one=self.plan(transitions=t[:1],active=a)
        self.assertEqual(one["count"],1)

    def test_preview_must_not_be_self_authorizing(self):
        t,a=self.setup()
        preview=self.plan(transitions=t,active=a)
        for key,value in (("release_authorized",True),
                          ("authority","attested-github-review"),
                          ("count",20),("base_release","bhsa/999.0.0")):
            p=copy.deepcopy(preview)
            p[key]=value
            with self.subTest(key=key),self.assertRaises(NativeSupersessionError):
                verify_supersession_batch_preview(
                    p,transitions=t,base_release="bhsa/0.4.0",active_mappings=a)


if __name__=="__main__":
    unittest.main()
