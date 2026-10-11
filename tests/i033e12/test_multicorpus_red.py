"""RED contract: four realistic primary-source-backed, synthetic predecessor rows."""
from __future__ import annotations

import copy
import unittest

from tfont.release_registry import load_profile
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2
from tfont.mapping_supersession import (
    NativeSupersessionError,
    plan_multi_corpus_native_supersession,
    verify_multi_corpus_native_supersession_preview,
)


def corpus_cohort(corpus: str) -> dict:
    bundle=load_profile(corpus,release_id="0.4.0")
    source_id=f"evidence:{corpus}:word-sp-adj-adv-source"
    evidence={x.data["evidence_id"]:copy.deepcopy(x.data) for x in bundle.evidences}
    native=evidence[source_id]
    lock=copy.deepcopy(bundle.ontology_locks[0].data)
    originals=[row for row in bundle.mappings.data["mappings"]
        if row["mapping_id"] in (
            f"mapping:{corpus}:olia-adjective",
            f"mapping:{corpus}:olia-adverb",
        )]
    assert len(originals)==2
    transitions=[]
    inherited=[]
    for published in originals:
        value=published["native_binding"]["value"]
        prior=copy.deepcopy(published)
        prior["mapping_id"]=f"mapping:{corpus}:synthetic-native-sp-{value}"
        prior["native_state"]="native-only"
        prior["projections"]=[]
        prior["evidence"]=[ref for ref in prior["evidence"] if ref["evidence_id"]==source_id]
        prior["rationale"]="SYNTHETIC TEST-ONLY predecessor, not a historically published decision"
        prior["mapping_semantic_digest"]=mapping_semantic_digest_v2(prior)
        prior["review"]["reviewed_mapping_digest"]=prior["mapping_semantic_digest"]
        proposed=copy.deepcopy(published)
        proposed["mapping_id"]=f"mapping:{corpus}:exact-after-native-{value}"
        del proposed["review"]
        del proposed["projections"][0]["review"]
        proposed["mapping_semantic_digest"]=mapping_semantic_digest_v2(proposed)
        term=published["projections"][0]["target"].rsplit("#",1)[1].lower()
        transitions.append({
            "previous":prior, "candidate":proposed,
            "native_evidence":copy.deepcopy(native),
            "ontology_evidence":copy.deepcopy(evidence[f"evidence:olia:{term}-class"]),
            "ontology_lock":copy.deepcopy(lock),
        })
        inherited.append(prior)
    return {
        "base_release":f"{corpus}/0.4.0",
        "active_mappings":inherited,
        "transitions":transitions,
    }


def real_source_synthetic_cohorts() -> list[dict]:
    return [corpus_cohort("bhsa"),corpus_cohort("syriac")]


class MultiCorpusSupersessionRed(unittest.TestCase):
    def test_four_primary_source_based_transitions_in_one_preview(self):
        cohorts=real_source_synthetic_cohorts()
        initial=copy.deepcopy(cohorts)
        preview=plan_multi_corpus_native_supersession(cohorts=cohorts)
        self.assertEqual(cohorts,initial)
        self.assertEqual(preview["transition_kind"],"native-only-to-exact-multi-corpus")
        self.assertEqual(preview["authority"],"untrusted-multi-corpus-supersession-preview")
        self.assertIs(preview["release_authorized"],False)
        self.assertEqual(preview["count"],4)
        self.assertEqual(preview["corpus_count"],2)
        self.assertEqual([r["corpus_id"] for r in preview["corpora"]],["bhsa","syriac"])
        self.assertEqual([r["count"] for r in preview["corpora"]],[2,2])
        self.assertTrue(preview["content_digest"].startswith("sha256:"))
        self.assertNotIn("review",preview)
        self.assertNotIn("published_releases",preview)
        self.assertNotIn("active_mappings",preview)
        self.assertIsNone(verify_multi_corpus_native_supersession_preview(
            preview,cohorts=cohorts))

    def test_permutation_of_corpus_transition_and_active_order_is_immaterial(self):
        cohorts=real_source_synthetic_cohorts()
        original=plan_multi_corpus_native_supersession(cohorts=cohorts)
        altered=copy.deepcopy(list(reversed(cohorts)))
        for cohort in altered:
            cohort["transitions"].reverse()
            cohort["active_mappings"].reverse()
        self.assertEqual(original,plan_multi_corpus_native_supersession(cohorts=altered))

    def test_one_corpus_one_accepted_allowed(self):
        single=real_source_synthetic_cohorts()[0]
        single["transitions"]=single["transitions"][:1]
        preview=plan_multi_corpus_native_supersession(cohorts=[single])
        self.assertEqual((preview["count"],preview["corpus_count"]),(1,1))


if __name__=="__main__":
    unittest.main()
