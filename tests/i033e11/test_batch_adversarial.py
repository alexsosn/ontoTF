"""Independent skeptical collision and evidence failures for batch preflight."""
from __future__ import annotations
import copy
import unittest
from tfont.mapping_supersession import (
    NativeSupersessionError,plan_native_only_supersession_batch)
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2
from tests.i033e11.test_batch_red import two_real_source_synthetic_transitions

class BatchSupersessionAdversarial(unittest.TestCase):
    def setUp(self):
        self.transitions,self.active=two_real_source_synthetic_transitions()

    def ask(self,transitions=None,active=None,version="bhsa/0.4.0"):
        return plan_native_only_supersession_batch(
            transitions=self.transitions if transitions is None else transitions,
            active_mappings=self.active if active is None else active,
            base_release=version)

    def test_reject_empty_or_more_than_fifty_accepted_transitions(self):
        for xs in ([],self.transitions*26):
            with self.subTest(n=len(xs)),self.assertRaises(NativeSupersessionError):
                self.ask(xs)

    def test_duplicate_retirement_and_selector_cannot_pass(self):
        with self.assertRaises(NativeSupersessionError):
            self.ask(self.transitions+[copy.deepcopy(self.transitions[0])])

    def test_reject_colliding_successor_or_projection_identifiers(self):
        for collision in ("mapping","projection"):
            t=copy.deepcopy(self.transitions)
            if collision=="mapping":
                t[1]["candidate"]["mapping_id"]=t[0]["candidate"]["mapping_id"]
            else:
                t[1]["candidate"]["projections"][0]["projection_id"]=(
                    t[0]["candidate"]["projections"][0]["projection_id"])
                from tfont.semantic_digest_v2 import projection_semantic_digest_v1
                p=t[1]["candidate"]["projections"][0]
                p["projection_semantic_digest"]=projection_semantic_digest_v1(p)
            t[1]["candidate"]["mapping_semantic_digest"]=mapping_semantic_digest_v2(
                t[1]["candidate"])
            with self.subTest(collision=collision),self.assertRaises(NativeSupersessionError):
                self.ask(t)

    def test_foreign_base_and_forged_evidence_fail(self):
        with self.assertRaises(NativeSupersessionError):
            self.ask(version="syriac/0.4.0")
        t=copy.deepcopy(self.transitions)
        t[1]["ontology_evidence"]["reviewed_content"]["target"]="http://evil.invalid/Fake"
        with self.assertRaises(NativeSupersessionError):
            self.ask(t)

    def test_unreviewed_predecessor_and_new_positive_self_review_fail(self):
        for kind in ("old","new"):
            t=copy.deepcopy(self.transitions)
            if kind=="old":t[0]["previous"]["review"]["status"]="draft"
            else:t[0]["candidate"]["review"]={"status":"reviewed"}
            with self.subTest(kind=kind),self.assertRaises(NativeSupersessionError):
                self.ask(t)

    def test_extra_keys_are_not_hidden_review_authority(self):
        t=copy.deepcopy(self.transitions)
        t[0]["approved_by"]="fake-reviewer"
        with self.assertRaises(NativeSupersessionError):
            self.ask(t)

if __name__=="__main__":
    unittest.main()
