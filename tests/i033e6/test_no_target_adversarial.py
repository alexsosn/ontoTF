"""I-033E6 adversarial negatives for native-only and exact mixed cohorts."""
from __future__ import annotations

import copy
import hashlib
import unittest

from tfont.batch_proposals import BatchProposalError, compile_candidate_batch, load_ledger
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.digests import canonical_json_bytes, evidence_record_digest
from tfont.review_packets import (
    BatchReviewPacketError, build_review_packet, verify_review_packet,
)
from tests.i033e6.test_no_target_red import no_target_cohort


class NoTargetAdversarial(unittest.TestCase):
    def setUp(self):
        self.ledger, self.read = no_target_cohort()

    def rejects(self, callback):
        ledger = copy.deepcopy(self.ledger)
        callback(ledger)
        with self.assertRaises((BatchProposalError, ValueError)):
            compile_candidate_batch(ledger, resource_loader=self.read)

    def test_no_target_forbids_term_key_even_null_and_synthetic_review(self):
        for key,value in (("term_key", None), ("term_key", "adjective"),
                          ("target", "http://purl.org/olia/olia.owl#Pronoun"),
                          ("projections", []), ("review", {"status":"reviewed"}),
                          ("release_authorized", True)):
            with self.subTest(key=key):
                self.rejects(lambda l,k=key,v=value: l["decisions"][-1].__setitem__(k,v))

    def test_native_source_is_required_not_inferred_from_other_corpus(self):
        self.rejects(lambda l:l["decisions"][-1].__setitem__("value","unknown"))
        self.rejects(lambda l:l["decisions"][-1].__setitem__("corpus_id","syriac"))
        self.rejects(lambda l:l["decisions"][-1].__setitem__("rationale",""))
        self.rejects(lambda l:l["source_registry"]["bhsa"].__setitem__(
            "source_revision","0"*40))

    def test_native_only_does_not_accept_a_second_exact_for_same_selector(self):
        def append(l):
            l["decisions"].append({
                "corpus_id":"bhsa", "value":"prps", "term_key":"adjective",
                "assessment":"exact", "rationale":"forged concurrent target"
            })
        self.rejects(append)

    def test_forged_packet_rehash_does_not_change_no_target(self):
        packet = build_review_packet(self.ledger, resource_loader=self.read)
        ident = next(i for i,r in enumerate(packet["rows"])
                     if r["mapping_id"]=="mapping:bhsa:native-sp-prps")
        for name, value in (("ontology_target","http://purl.org/olia/olia.owl#Pronoun"),
                            ("projection_semantic_digest","sha256:"+"a"*64),
                            ("assessment","exact"),
                            ("rationale","forged approved equivalence")):
            altered=copy.deepcopy(packet)
            altered["rows"][ident][name]=value
            altered["batch_digest"]="sha256:"+hashlib.sha256(canonical_json_bytes(
                {k:v for k,v in altered.items() if k!="batch_digest"}
            )).hexdigest()
            with self.subTest(field=name),self.assertRaises(BatchReviewPacketError):
                verify_review_packet(altered,self.ledger,resource_loader=self.read)

    def test_candidate_source_line_and_digest_rebind_invalidates_packet(self):
        packet=build_review_packet(self.ledger,resource_loader=self.read)
        from tfont.batch_proposals import packaged_resource
        name=self.ledger["source_registry"]["bhsa"]["evidence_resource"]
        record=self.read(name)
        record["reviewed_content"]["source_definitions"]["prps"]["line"]=25
        record["content_digest"]=evidence_record_digest(record)
        changed=CandidateEvidenceResources(self.ledger,{name:record})
        with self.assertRaises(BatchReviewPacketError):
            verify_review_packet(packet,self.ledger,resource_loader=changed)

    def test_legacy_native_only_coverage_not_rewritten(self):
        from pathlib import Path
        import json
        root=Path(__file__).resolve().parents[2]
        bhsa=json.loads((root/"src/tfont/resources/coverage/p004-i027b1-bhsa-verb-v1/bhsa.json"
                          ).read_text(encoding="utf-8"))
        old=[r for r in bhsa["semantic_items"]
             if r["accounting"]["production"] is not None
             and "native-only" in r["accounting"]["production"]["assessments"]]
        self.assertEqual(len(old),27)
        self.assertTrue(all(not x["accounting"]["production"]["common_target"] for x in old))
        compiled=compile_candidate_batch(self.ledger,resource_loader=self.read)
        self.assertFalse(compiled["release_authorized"])


if __name__=="__main__":
    unittest.main()
