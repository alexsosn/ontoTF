"""Separate challenge path for false shared authority and aliasing across corpora."""
from __future__ import annotations

import copy
import unittest
from tfont.digests import evidence_record_digest
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2, projection_semantic_digest_v1
from tfont.mapping_supersession import plan_native_only_supersession_batch
from tfont.mapping_supersession import (
    NativeSupersessionError,
    plan_multi_corpus_native_supersession,
    verify_multi_corpus_native_supersession_preview,
)
from tests.i033e12.test_multicorpus_red import real_source_synthetic_cohorts


class MultiCorpusSupersessionAdversarial(unittest.TestCase):
    def setUp(self):
        self.groups=real_source_synthetic_cohorts()

    def ask(self,cohorts=None):
        return plan_multi_corpus_native_supersession(
            cohorts=self.groups if cohorts is None else cohorts)

    def test_duplicate_corpus_and_empty_corpus_cohort_fail_closed(self):
        with self.assertRaises(NativeSupersessionError):
            self.ask(self.groups+[copy.deepcopy(self.groups[0])])
        groups=copy.deepcopy(self.groups)
        groups[1]["transitions"]=[]
        with self.assertRaises(NativeSupersessionError):
            self.ask(groups)

    def test_global_total_limit_prevents_splitting_51_under_the_same_corpus(self):
        groups=copy.deepcopy(self.groups)
        groups[0]["transitions"]=groups[0]["transitions"]*26
        with self.assertRaises(NativeSupersessionError):
            self.ask(groups)

    def test_cross_corpus_selector_or_ontology_provenance_substitution_rejected(self):
        for key in ("previous","native_evidence"):
            groups=copy.deepcopy(self.groups)
            groups[1]["transitions"][0][key]=copy.deepcopy(groups[0]["transitions"][0][key])
            with self.subTest(key=key),self.assertRaises(NativeSupersessionError):
                self.ask(groups)

    def test_ontology_evidence_is_legitimately_shared_across_corpora(self):
        # OLiA Adjective is ONE pinned OWL Class, not corpus-specific.
        # Copying identical ontology evidence/lock from BHSA to Syriac is
        # allowed; native evidence and selector identity must remain separate.
        groups=copy.deepcopy(self.groups)
        groups[1]["transitions"][0]["ontology_evidence"]=copy.deepcopy(
            groups[0]["transitions"][0]["ontology_evidence"])
        groups[1]["transitions"][0]["ontology_lock"]=copy.deepcopy(
            groups[0]["transitions"][0]["ontology_lock"])
        self.assertEqual(self.ask(groups),self.ask())

    def test_substituted_other_ontology_class_fails(self):
        groups=copy.deepcopy(self.groups)
        groups[1]["transitions"][0]["ontology_evidence"]=copy.deepcopy(
            groups[1]["transitions"][1]["ontology_evidence"])
        with self.assertRaises(NativeSupersessionError):
            self.ask(groups)

    def test_individually_valid_alternate_ontology_revision_cannot_mix_in_release(self):
        cohorts=copy.deepcopy(self.groups)
        alternate=cohorts[1]["transitions"][1]
        # A fabricated but internally self-consistent UNTRUSTED source snapshot
        # can pass the per-row preflight. It must NOT join a release that
        # otherwise uses the independently pinned actual OLiA revision.
        revision="a"*40
        alternate["ontology_lock"]["source_revision"]=revision
        alt_evidence=alternate["ontology_evidence"]
        alt_evidence["source_revision"]=revision
        alt_evidence["content_digest"]=evidence_record_digest(alt_evidence)
        new_ref={"evidence_id":alt_evidence["evidence_id"],
                 "content_digest":alt_evidence["content_digest"]}
        candidate=alternate["candidate"]
        candidate["evidence"][1]=new_ref
        projection=candidate["projections"][0]
        projection["evidence"][1]=new_ref
        projection["projection_semantic_digest"]=projection_semantic_digest_v1(projection)
        candidate["mapping_semantic_digest"]=mapping_semantic_digest_v2(candidate)
        # The source, category, class and digest are still self-consistent:
        plan_native_only_supersession_batch(
            transitions=cohorts[1]["transitions"],
            base_release=cohorts[1]["base_release"],
            active_mappings=cohorts[1]["active_mappings"],
        )
        with self.assertRaisesRegex(NativeSupersessionError,"ontology snapshot"):
            self.ask(cohorts)

    def test_no_unreviewed_self_approval_or_forged_cohort_review(self):
        for kind in ("candidate","cohort"):
            groups=copy.deepcopy(self.groups)
            if kind=="candidate":
                groups[0]["transitions"][0]["candidate"]["review"]={"status":"reviewed"}
            else:
                groups[0]["approved_by"]="fake-user"
            with self.subTest(kind=kind),self.assertRaises(NativeSupersessionError):
                self.ask(groups)

    def test_full_preview_recompute_fails_after_review_or_release_claim_forgery(self):
        preview=self.ask()
        for key,value in (("release_authorized",True),
                          ("authority","attested"),
                          ("count",50),("corpus_count",1)):
            altered=copy.deepcopy(preview)
            altered[key]=value
            with self.subTest(key=key),self.assertRaises(NativeSupersessionError):
                verify_multi_corpus_native_supersession_preview(
                    altered,cohorts=self.groups)

    def test_cross_corpus_preview_does_not_rely_on_reused_OLIA_label(self):
        preview=self.ask()
        keys={(p["corpus_id"],t["native_binding"]["value"])
            for p in preview["corpora"] for t in p["batch"]["transitions"]}
        self.assertEqual(keys,{
            ("bhsa","adjv"),("bhsa","advb"),
            ("syriac","adjv"),("syriac","advb"),
        })


if __name__=="__main__":
    unittest.main()
