"""Adversarial source / approval and accounting spoofing checks."""
from __future__ import annotations

import copy
import unittest

from tfont.coverage import load_packaged_coverage_manifest
from tfont.coverage_deltas import (
    PublishedCoverageDeltaError,
    _build_delta_between,
    build_published_coverage_delta,
    load_published_coverage_delta,
)


class SparsePublishedCoverageAdversarial(unittest.TestCase):
    def setUp(self):
        self.corpus="bhsa"
        self.before="p004-i027b1-bhsa-verb-v1"
        self.after="p004-i027c2-bhsa-adj-adv-v1"
        self.base=load_packaged_coverage_manifest(self.before,self.corpus)
        self.target=load_packaged_coverage_manifest(self.after,self.corpus)
        self.delta=build_published_coverage_delta(self.corpus,self.before,self.after)

    def assert_rejected_target(self, mutate):
        target=copy.deepcopy(self.target)
        mutate(target)
        with self.assertRaises(PublishedCoverageDeltaError):
            _build_delta_between(self.corpus,self.before,self.after,self.base,target)

    def test_forged_delta_replay_retarget_or_fake_authority_fails(self):
        for key,value in (
            ("corpus_id","syriac"), ("base_resource_set","p004-r011-baseline-v1"),
            ("target_manifest_digest","sha256:"+"0"*64),
            ("authority","github-verified"),("release_authorized",True),
            ("reviewer_id","self"),("added_production",[]),
        ):
            delta=copy.deepcopy(self.delta)
            delta[key]=value
            with self.subTest(key=key),self.assertRaises(PublishedCoverageDeltaError):
                load_published_coverage_delta(delta)

    def test_forged_new_production_source_id_rejected(self):
        delta=copy.deepcopy(self.delta)
        delta["added_production"][0]["production"]["source_ids"]=["forged-approve"]
        with self.assertRaises(PublishedCoverageDeltaError):
            load_published_coverage_delta(delta)

    def test_research_or_historical_production_mutation_rejected(self):
        self.assert_rejected_target(
            lambda x:x["semantic_items"][0]["accounting"].__setitem__(
                "research", {"assessments":["exact"],"capabilities":["linguistic.part-of-speech"],
                             "common_target":True,"profiles":["linguistic"],"source_ids":["fabricated"]},
            )
        )
        def mutate_previous(x):
            p=next(row for row in x["semantic_items"]
                   if row["item_id"]=='node_value:sp="verb"')
            p["accounting"]["production"]["source_ids"]=["forged"]
        self.assert_rejected_target(mutate_previous)

    def test_denominator_native_identity_and_gap_regression_rejected(self):
        self.assert_rejected_target(lambda x:x.__setitem__("denominator_digest","sha256:"+"0"*64))
        self.assert_rejected_target(lambda x:x.__setitem__("target_corpus_revision","forged"))
        self.assert_rejected_target(lambda x:x["semantic_items"][0].__setitem__("kind","edge_feature"))
        self.assert_rejected_target(lambda x:x["semantic_items"].pop())
        self.assert_rejected_target(lambda x:x.__setitem__("technical_exclusions",[{"item_id":"fabricated"}]))
        sy_base=load_packaged_coverage_manifest("p004-i027b2-syriac-verb-v1","syriac")
        sy_target=load_packaged_coverage_manifest("p004-i027c2-syriac-adj-adv-v1","syriac")
        sy_target["accounting_gaps"]=[]
        with self.assertRaises(PublishedCoverageDeltaError):
            _build_delta_between("syriac","p004-i027b2-syriac-verb-v1",
                                 "p004-i027c2-syriac-adj-adv-v1",sy_base,sy_target)

    def test_noop_or_removed_review_is_not_additive_delta(self):
        with self.assertRaises(PublishedCoverageDeltaError):
            _build_delta_between(self.corpus,self.before,self.after,self.base,copy.deepcopy(self.base))
        def drop(x):
            p=next(row for row in x["semantic_items"]
                   if row["item_id"]=='node_value:sp="verb"')
            p["accounting"]["production"]=None
        self.assert_rejected_target(drop)

    def test_repackaged_delta_is_not_untrusted_reviewer_approval(self):
        self.assertEqual(self.delta["authority"],"published-registry-parity-only")
        self.assertNotIn("review_source",self.delta)
        self.assertNotIn("github_token",self.delta)


if __name__=="__main__":
    unittest.main()
