"""Separate challenge path for false shared authority and aliasing across corpora."""
from __future__ import annotations

import copy
import unittest
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
        for key in ("previous","native_evidence","ontology_evidence","ontology_lock"):
            groups=copy.deepcopy(self.groups)
            groups[1]["transitions"][0][key]=copy.deepcopy(groups[0]["transitions"][0][key])
            with self.subTest(key=key),self.assertRaises(NativeSupersessionError):
                self.ask(groups)

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
