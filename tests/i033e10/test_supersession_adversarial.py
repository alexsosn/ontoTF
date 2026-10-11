from __future__ import annotations

import copy
import unittest

from tests.i033e10.fixtures import synthetic_transition
from tfont.mapping_supersession import NativeSupersessionError, plan_native_only_supersession
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2, projection_semantic_digest_v1
from tfont.digests import evidence_record_digest


class NativeOnlyPromotionAdversarial(unittest.TestCase):
    def setUp(self):
        self.old,self.new,self.source,self.ontology,self.lock=synthetic_transition()

    def ask(self, *, old=None,new=None,source=None,ontology=None,lock=None,release="bhsa/0.3.0"):
        return plan_native_only_supersession(
            previous=self.old if old is None else old,
            candidate=self.new if new is None else new,
            native_evidence=self.source if source is None else source,
            ontology_evidence=self.ontology if ontology is None else ontology,
            ontology_lock=self.lock if lock is None else lock,
            base_release=release,
        )

    def test_native_only_predecessor_must_remain_reviewed_and_unprojected(self):
        for op in ("status","review_digest","positive","old_projection"):
            old=copy.deepcopy(self.old)
            if op=="status": old["review"]["status"]="draft"
            if op=="review_digest":old["review"]["reviewed_mapping_digest"]="sha256:"+"0"*64
            if op=="positive":old["native_state"]="positive"
            if op=="old_projection":old["projections"]=[copy.deepcopy(self.new["projections"][0])]
            if op in ("positive","old_projection"):
                old["mapping_semantic_digest"]=mapping_semantic_digest_v2(old)
                old["review"]["reviewed_mapping_digest"]=old["mapping_semantic_digest"]
            with self.subTest(op=op),self.assertRaises(NativeSupersessionError):
                self.ask(old=old)

    def test_new_candidate_selector_must_match_pinned_native_source(self):
        mutations=[("corpus_id","syriac"),("native_binding.feature","vs"),
                   ("native_binding.node_type","lex"),("native_binding.value","subs"),
                   ("native_binding.component_id","fake-tf"),
                   ("native_dependencies",["dep:bhsa:word-sp:wrong"]),
                   ("profiles",["written-text"]),("capabilities",["linguistic.morphology"])]
        for key,value in mutations:
            new=copy.deepcopy(self.new)
            if "." in key:
                a,b=key.split(".");new[a][b]=value
            else:new[key]=value
            new["mapping_semantic_digest"]=mapping_semantic_digest_v2(new)
            with self.subTest(key=key),self.assertRaises(NativeSupersessionError):
                self.ask(new=new)

    def test_stale_semantic_digests_and_forged_reviews(self):
        newer=copy.deepcopy(self.new)
        newer["mapping_semantic_digest"]="sha256:"+"0"*64
        with self.assertRaises(NativeSupersessionError):self.ask(new=newer)
        newer=copy.deepcopy(self.new);newer["projections"][0]["projection_semantic_digest"]="sha256:"+"0"*64
        newer["mapping_semantic_digest"]=mapping_semantic_digest_v2(newer)
        with self.assertRaises(NativeSupersessionError):self.ask(new=newer)
        newer=copy.deepcopy(self.new);newer["review"]={"status":"reviewed"}
        with self.assertRaises(NativeSupersessionError):self.ask(new=newer)
        newer=copy.deepcopy(self.new);newer["projections"][0]["assessment"]="close"
        newer["projections"][0]["projection_semantic_digest"]=projection_semantic_digest_v1(newer["projections"][0])
        newer["mapping_semantic_digest"]=mapping_semantic_digest_v2(newer)
        with self.assertRaises(NativeSupersessionError):self.ask(new=newer)

    def test_unknown_ontology_target_and_modified_class_claim_fail_closed(self):
        lock=copy.deepcopy(self.lock);lock["terms_used"].remove("http://purl.org/olia/olia.owl#Verb")
        with self.assertRaises(NativeSupersessionError):self.ask(lock=lock)
        ontology=copy.deepcopy(self.ontology);ontology["reviewed_content"]["rdf_type"]="owl:ObjectProperty"
        ontology["content_digest"]=evidence_record_digest(ontology)
        with self.assertRaises(NativeSupersessionError):self.ask(ontology=ontology)
        ontology=copy.deepcopy(self.ontology);ontology["reviewed_content"]["snapshot_digest"]="sha256:"+"0"*64
        ontology["content_digest"]=evidence_record_digest(ontology)
        with self.assertRaises(NativeSupersessionError):self.ask(ontology=ontology)
        source=copy.deepcopy(self.source);source["reviewed_content"]["values"]["verb"]="noun"
        with self.assertRaises(NativeSupersessionError):self.ask(source=source)

    def test_ontology_evidence_requires_proposal_binding_and_lock(self):
        new=copy.deepcopy(self.new);new["evidence"]=[self.old["evidence"][0]]
        new["projections"][0]["evidence"]=copy.deepcopy(new["evidence"])
        new["projections"][0]["projection_semantic_digest"]=projection_semantic_digest_v1(new["projections"][0])
        new["mapping_semantic_digest"]=mapping_semantic_digest_v2(new)
        with self.assertRaises(NativeSupersessionError):self.ask(new=new)
        new=copy.deepcopy(self.new);new["projections"][0]["ontology_lock"]="other"
        new["projections"][0]["projection_semantic_digest"]=projection_semantic_digest_v1(new["projections"][0])
        new["mapping_semantic_digest"]=mapping_semantic_digest_v2(new)
        with self.assertRaises(NativeSupersessionError):self.ask(new=new)

    def test_release_must_have_matching_corpus_version(self):
        for release in ("syriac/0.3.0","bhsa/current","bhsa/../0.3.0","bhsa/0.3.0/extra"):
            with self.subTest(release=release),self.assertRaises(NativeSupersessionError):
                self.ask(release=release)


if __name__=="__main__":
    unittest.main()
