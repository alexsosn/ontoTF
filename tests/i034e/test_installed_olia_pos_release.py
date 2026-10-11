"""I-034E RED: real 12 reviewed OLiA POS projections installed as opt-in 0.5.0.

Mappings are sourced from protected GitHub artifact for PR #343, not from
fabricated local review approval. Historic 0.4.0 current aliases stay intact.
"""
from __future__ import annotations

import copy
from importlib.resources import files
import unittest

from tfont.release_registry import _load_catalogue, _load_from_catalogue, load_profile, list_profile_releases
from tfont.semantic_validation import validate_semantic_bundle


POS = {
    "bhsa": {
        "art": "Article", "prep": "Preposition", "conj": "Conjunction",
        "prde": "DemonstrativePronoun", "prin": "InterrogativePronoun",
        "intj": "Interjection", "nega": "NegativeParticle", "inrg": "InterrogativeParticle",
        "prps": None,
    },
    "syriac": {
        "conj": "Conjunction", "intj": "Interjection", "prep": "Preposition",
        "pron": "Pronoun", "inrg": None, "nega": None,
    },
}
OLIA = "http://purl.org/olia/olia.owl#"
NEW_LOCK = "olia-reference-model-i034a-pos"
LEGACY_LOCK = "olia-reference-model"
REVIEW_URL = "https://github.com/alexsosn/ontoTF/pull/343"
SIGNED_BATCH_DIGEST = "sha256:9379981e174ef080468aa0e6f9c1b87b4fa06432effcd907e3973f3328eee308"
EXACT_HEAD = "b6168a6602ab546446d4101b2029207d840f2076"


class InstalledRealOLiAPOS(unittest.TestCase):
    def test_two_opt_in_installed_profiles_keep_all_old_mappings_and_two_locks(self):
        catalog = _load_catalogue()
        self.assertEqual(catalog["corpora"]["bhsa"]["current"], "0.4.0")
        self.assertEqual(catalog["corpora"]["syriac"]["current"], "0.4.0")
        positive = native_only = 0
        for corpus, expected in POS.items():
            with self.subTest(corpus=corpus):
                old = load_profile(corpus, "0.4.0")
                installed = load_profile(corpus, "0.5.0")
                self.assertEqual(installed.profile.data["profile_version"], "0.5.0")
                self.assertIsNotNone(validate_semantic_bundle(installed))
                self.assertEqual(len(installed.mappings.data["mappings"]),
                                 len(old.mappings.data["mappings"]) + len(expected))
                self.assertEqual(
                    {r["mapping_id"]:r["mapping_semantic_digest"] for r in old.mappings.data["mappings"]},
                    {r["mapping_id"]:r["mapping_semantic_digest"] for r in installed.mappings.data["mappings"]
                     if r["mapping_id"] in {m["mapping_id"] for m in old.mappings.data["mappings"]}},
                )
                self.assertEqual({l.data["lock_id"] for l in installed.ontology_locks},
                                 {LEGACY_LOCK, NEW_LOCK})
                new = [m for m in installed.mappings.data["mappings"]
                       if m["mapping_id"] not in {r["mapping_id"] for r in old.mappings.data["mappings"]}]
                bindings = [m["native_binding"] for m in installed.mappings.data["mappings"]]
                self.assertEqual(len(bindings),len({tuple(sorted(b.items())) for b in bindings}))
                self.assertEqual({m["native_binding"]["value"] for m in new},set(expected))
                for m in new:
                    name = m["native_binding"]["value"]
                    self.assertEqual(m["native_binding"]["feature"],"sp")
                    self.assertEqual(m["native_binding"]["node_type"],"word")
                    self.assertEqual(m["review"]["status"],"reviewed")
                    self.assertEqual(m["review"]["review_source"],REVIEW_URL)
                    self.assertEqual(m["review"]["reviewed_mapping_digest"],
                                     m["mapping_semantic_digest"])
                    self.assertEqual(m["review"]["review_id"].split(":")[0],"review")
                    if expected[name] is None:
                        native_only += 1
                        self.assertEqual(m["native_state"],"native-only")
                        self.assertEqual(m["projections"],[])
                    else:
                        positive += 1
                        self.assertEqual(m["native_state"],"positive")
                        p, = m["projections"]
                        self.assertEqual(p["target"],OLIA+expected[name])
                        self.assertEqual(p["ontology_lock"],NEW_LOCK)
                        self.assertEqual(p["review"]["reviewed_mapping_digest"],
                                         p["projection_semantic_digest"])
                        self.assertEqual(p["review"]["status"],"reviewed")
        self.assertEqual((positive,native_only),(12,3))

    def test_new_release_is_packaged_and_preserves_old_source_bytes(self):
        root=files("tfont")
        for corpus in POS:
            original=f"resources/profiles/{corpus}/0.4.0"
            extended=f"resources/profiles/{corpus}/0.5.0"
            for path in ("parent/expected-components.json",
                         "mappings/noun.json","mappings/noun-morphology.json",
                         "mappings/verb.json","mappings/adj-adv.json"):
                self.assertEqual(
                    root.joinpath(*f"{original}/{path}".split("/")).read_bytes(),
                    root.joinpath(*f"{extended}/{path}".split("/")).read_bytes(),
                    f"stale original release copy: {corpus}/{path}",
                )
            self.assertTrue(root.joinpath(*f"{extended}/mappings/olia-pos.json".split("/")).is_file())
            self.assertIn("0.5.0",list_profile_releases(corpus))
            self.assertEqual(load_profile(corpus).profile.data["profile_version"],"0.4.0")
        self.assertNotIn("0.5.0",list_profile_releases("extrabiblical"))

    def test_original_source_gates_and_catalogue_release_pins_are_closed(self):
        catalog=_load_catalogue()
        for corpus in POS:
            spec=catalog["corpora"][corpus]["releases"]["0.5.0"]
            self.assertEqual(spec["ontology_lock"].split("/")[-1],
                             "lock-linguistic-i034a-pos.json")
            self.assertEqual(spec["ontology_locks"][0].split("/")[-1],
                             "lock-linguistic-0.4.0.json")
            self.assertEqual(spec["ontology_locks"][1],spec["ontology_lock"])
            native=[x for x in spec["native_evidence"] if "/0.5.0/" in x]
            self.assertEqual(len(native),1)
            self.assertEqual(len([x for x in spec["ontology_evidence"]
                                  if "/i034a-" in x]),9)
        forged=copy.deepcopy(catalog)
        forged["corpora"]["bhsa"]["releases"]["0.5.0"]["ontology_locks"][1]=(
            "resources/ontologies/olia/0000000000000000000000000000000000000000/forged.json"
        )
        with self.assertRaises(ValueError):
            _load_from_catalogue(forged,"bhsa","0.5.0")
        forged=copy.deepcopy(catalog)
        forged["corpora"]["bhsa"]["releases"]["0.5.0"]["ontology_locks"].append(
            forged["corpora"]["bhsa"]["releases"]["0.5.0"]["ontology_locks"][0]
        )
        with self.assertRaises(ValueError):
            _load_from_catalogue(forged,"bhsa","0.5.0")


if __name__=="__main__":
    unittest.main()
