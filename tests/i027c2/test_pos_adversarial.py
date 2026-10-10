from __future__ import annotations

import copy
import unittest

from tfont.semantic_validation import (
    SemanticArtifact, SemanticSourceBundle, SemanticValidationError, validate_semantic_bundle,
)

class POSAdjectiveAdverbAdversarial(unittest.TestCase):
    def test_fail_closed_modified_selectors_and_reviews(self):
        from tfont.production_bundles import load_production_adj_adv_bundle
        for corpus in ("bhsa","syriac"):
            bundle=load_production_adj_adv_bundle(corpus)
            validate_semantic_bundle(bundle)
            for target in ("adjective","adverb"):
                for key,value in (("node_type","lex"),("feature","pdp"),("value","verb")):
                    with self.subTest(corpus=corpus,target=target,key=key):
                        original=copy.deepcopy(bundle.mappings.data)
                        row=next(x for x in original["mappings"]
                                if x["mapping_id"]==f"mapping:{corpus}:olia-{target}")
                        row["native_binding"][key]=value
                        forged=SemanticSourceBundle(
                            profile=bundle.profile,
                            expected_parent_manifest=bundle.expected_parent_manifest,
                            mappings=SemanticArtifact("mapping","forged-pos",original),
                            ontology_locks=bundle.ontology_locks,
                            evidences=bundle.evidences,
                        )
                        with self.assertRaises(SemanticValidationError):
                            validate_semantic_bundle(forged)

    def test_new_mapping_source_evidence_is_corpus_specific(self):
        from tfont.production_bundles import load_production_adj_adv_bundle
        for corpus in ("bhsa","syriac"):
            b=load_production_adj_adv_bundle(corpus)
            for target in ("adjective","adverb"):
                m=next(x for x in b.mappings.data["mappings"]
                       if x["mapping_id"]==f"mapping:{corpus}:olia-{target}")
                self.assertEqual(m["native_binding"]["component_id"],f"{corpus}-tf")
                self.assertTrue(any(e["evidence_id"]==f"evidence:{corpus}:word-sp-adj-adv-source"
                                    for e in m["evidence"]))
                self.assertTrue(any(e["evidence_id"]==f"evidence:olia:{target}-class"
                                    for e in m["evidence"]))

if __name__=="__main__":
    unittest.main()
