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


# Fixed mapping/projection SHA-256 values read from the *real protected*
# artifact 11714296834, run 38172147473. Never recompute these from
# locally modified release data when checking trusted source equivalence.
SIGNED_ROW_DIGESTS = {
    "bhsa": {
        "native-sp-prps": ("241f694efe632b59ddbe5036c9c45a49704c9dbd49ea18ed72678ee948f86ca4", None),
        "olia-article": ("02fed6919bb55a9c0e3599acfcc70e7e97c1371a6c028b699209d2630d428c46", "d729913509e88ec3409415b201090a15158830f142fb31d028cba11bc918d8d1"),
        "olia-conjunction": ("c00c41e474fff58d62827330d29a9448869ca666c4b73c9b37ea84316c787c35", "55a7ac3c69f4ef0e74fc6dd443ff8334485322cb8c838708c612221c17bf4b5e"),
        "olia-demonstrativepronoun": ("302a7540fe34f33466da1156c54a04c1a7c3b22c0c273690ee53c054ec34fb24", "a2785bdfbd332ee1c54b2fc841a5cb497880c64c64d8371bfa7d3d005a6265ca"),
        "olia-interjection": ("3b0e1a03ee69b134407e8e0aa57c8df6a6f973ec3a7dc0f46637dbf9f0b7ea04", "bbf93414c0631aaec8b6b1c2b96434b56056db4ce93d00e4cc0e9c84d68ac171"),
        "olia-interrogativeparticle": ("3d09ca6fa601ff1d131ed4b8bcc0784d95e06c27bf6d2c19212b063e2e4fcc09", "fe1e94043fa3c2ca7cfc149f6edb2de8094d89456f9dd836d74e462f48dda32c"),
        "olia-interrogativepronoun": ("ea4d645bb0d7656c1a8f68eee6988ea8061ce27dc286a4537ffbe136b0fa1c59", "0b3de572f1b0c2c847d7cfb55789fadf0866dc0b8452ac2060debc24498b8488"),
        "olia-negativeparticle": ("1ed8b68558ea894d15b6952b080b4bbda6701e89a12b735518e80c2e3bab6e25", "72769c2aba385fc85147f59ef39f9969cb7cb31acb7366a4b2afe44547ea4710"),
        "olia-preposition": ("bb284edf51cc0da2811663a9a06f559dd51c0c031e88855f2d067eefd7a45506", "84a52c030aa792f8b078aa664c20fd2f432bb47a9e2a8a134733bf33b5fd3507"),
    },
    "syriac": {
        "native-sp-inrg": ("aa0c3e868573120f2f99e2d690f7b580d07840e004890a8b5058b2ef3f47be8e", None),
        "native-sp-nega": ("5dc63376b36e26fc686169f6ca47407e351e6a798d62ecd63775479d75816872", None),
        "olia-conjunction": ("56eca7b622ed794ee20324cf10720805a6c3f1f487907814429093b3ed74c044", "23a45bc2f8dcc7348895657e62d177d3929699a098b5dfa5a13fe5dda372209f"),
        "olia-interjection": ("ade77ba1e4189915c8182ae5a1e9243b51cfc8257bab638c3b49e4864e9f0888", "6f8ff108e40c22032baa265e106be8a141c64c3a6cfd675ec5bc027e565ebd4b"),
        "olia-preposition": ("210700f975267e078fe518b87ec407a84db9872b63dabf6079a75dcd08e831c2", "86db5ca26f6c45e62a6301bba7bf1023c28fe33c82ae0c568ad672d6de96b57e"),
        "olia-pronoun": ("e350e41b4b403f9f57599504e4da05eb271ddbe18bbd4ef097033c91ade942d2", "c9baca70aac1f8d1ef96a7fe2d3b5396968de51247374c9d8859c3c0751ca390"),
    },
}


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
                self.assertEqual({m["mapping_id"].split(":", 2)[2] for m in new},
                                 set(SIGNED_ROW_DIGESTS[corpus]))
                for m in new:
                    tail = m["mapping_id"].split(":", 2)[2]
                    signed_mapping, signed_projection = SIGNED_ROW_DIGESTS[corpus][tail]
                    self.assertEqual(m["mapping_semantic_digest"],"sha256:"+signed_mapping)
                    self.assertEqual([p["projection_semantic_digest"] for p in m["projections"]],
                                     [] if signed_projection is None else ["sha256:"+signed_projection])
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

    def test_installed_positive_classes_compile_into_cross_corpus_semantic_ir(self):
        from tfont.semantic_ir import SemanticKey, compile_semantic_ir
        releases = tuple(validate_semantic_bundle(load_profile(corpus, "0.5.0"))
                         for corpus in ("bhsa", "syriac"))
        ir = compile_semantic_ir(releases)
        index = dict(ir.semantic_index)
        def key(target):
            return SemanticKey(
                profile_id="linguistic",
                capability_id="linguistic.part-of-speech",
                target=OLIA + target,
                formal_kind="class",
                semantic_role="annotation-value",
            )
        for concept in ("Conjunction", "Interjection", "Preposition"):
            with self.subTest(olia=concept):
                rows = index[key(concept)]
                self.assertEqual([row.corpus_id for row in rows],
                                 ["bhsa", "syriac"])
                self.assertTrue(all(row.assessment == "exact" for row in rows))
                self.assertTrue(all(row.native_execution_binding.feature == "sp"
                                    for row in rows))
        for concept in ("Article", "DemonstrativePronoun",
                        "InterrogativePronoun", "NegativeParticle",
                        "InterrogativeParticle"):
            with self.subTest(olia=concept):
                self.assertEqual([r.corpus_id for r in index[key(concept)]],
                                 ["bhsa"])
        self.assertEqual([r.corpus_id for r in index[key("Pronoun")]],
                         ["syriac"])

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
