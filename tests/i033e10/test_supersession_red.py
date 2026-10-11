from __future__ import annotations

import copy
import unittest

from tests.i033e10.fixtures import synthetic_transition
from tfont.mapping_supersession import (
    NativeSupersessionError,
    plan_native_only_supersession,
    verify_supersession_preview,
)


class NativeOnlySupersessionRed(unittest.TestCase):
    def setUp(self):
        (self.old,self.new,self.source,self.ontology,self.lock) = synthetic_transition()

    def preview(self, **kwargs):
        args = {
            "previous":self.old,
            "candidate":self.new,
            "native_evidence":self.source,
            "ontology_evidence":self.ontology,
            "ontology_lock":self.lock,
            "base_release":"bhsa/0.3.0",
            "active_mappings":[self.old],
        }
        args.update(kwargs)
        return plan_native_only_supersession(**args)

    def test_source_bound_versioned_transition_keeps_history_without_activation(self):
        original=copy.deepcopy((self.old,self.new,self.source,self.ontology,self.lock))
        preview=self.preview()
        self.assertEqual((self.old,self.new,self.source,self.ontology,self.lock), original)
        self.assertEqual(preview["schema_version"],1)
        self.assertEqual(preview["authority"],"untrusted-supersession-preview")
        self.assertIs(preview["release_authorized"],False)
        self.assertEqual(preview["transition_kind"],"native-only-to-exact")
        self.assertEqual(preview["base_release"],"bhsa/0.3.0")
        self.assertEqual(preview["corpus_id"],"bhsa")
        self.assertTrue(preview["active_base_digest"].startswith("sha256:"))
        self.assertEqual(preview["retired"]["mapping_id"],self.old["mapping_id"])
        self.assertEqual(preview["retired"]["semantic_digest"],self.old["mapping_semantic_digest"])
        self.assertEqual(preview["candidate"]["mapping_id"],self.new["mapping_id"])
        self.assertEqual(preview["candidate"]["semantic_digest"],self.new["mapping_semantic_digest"])
        self.assertEqual(preview["candidate"]["target"],"http://purl.org/olia/olia.owl#Verb")
        self.assertEqual(preview["native_binding"],self.old["native_binding"])
        self.assertEqual(preview["ontology"]["source_revision"],self.lock["source_revision"])
        self.assertIn("transition_digest",preview)
        self.assertEqual(preview,self.preview())
        self.assertIsNone(verify_supersession_preview(
            preview,previous=self.old,candidate=self.new,
            native_evidence=self.source,ontology_evidence=self.ontology,
            ontology_lock=self.lock,base_release="bhsa/0.3.0",
            active_mappings=[self.old],
        ))

    def test_not_equivalent_to_approving_a_release(self):
        result=self.preview()
        self.assertNotIn("reviewer",result)
        self.assertNotIn("approved_head_sha",result)
        self.assertNotIn("coverage",result)
        self.assertNotIn("new_active_mappings",result)
        self.assertNotIn("common_target_count",result)

    def test_no_silent_replacement_or_unchanged_identity(self):
        same=copy.deepcopy(self.new)
        same["mapping_id"]=self.old["mapping_id"]
        from tfont.semantic_digest_v2 import mapping_semantic_digest_v2
        same["mapping_semantic_digest"]=mapping_semantic_digest_v2(same)
        with self.assertRaises(NativeSupersessionError):
            self.preview(candidate=same)

    def test_preview_cannot_be_modified_or_claim_release_authority(self):
        result=self.preview()
        for key,value in (
            ("release_authorized",True),
            ("transition_kind","automatic-upgrade"),
            ("base_release","bhsa/999.0.0"),
            ("authority","attested-review"),
        ):
            with self.subTest(key=key):
                forged=copy.deepcopy(result)
                forged[key]=value
                with self.assertRaises(NativeSupersessionError):
                    verify_supersession_preview(
                        forged,previous=self.old,candidate=self.new,
                        native_evidence=self.source,ontology_evidence=self.ontology,
                        ontology_lock=self.lock,base_release="bhsa/0.3.0",
                        active_mappings=[self.old],
                    )


if __name__=="__main__":
    unittest.main()
