from __future__ import annotations

import importlib
import unittest

from tfont.semantic_ir import SemanticKey, compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle

BASE = "http://purl.org/olia/olia.owl#"
EXPECTED_TARGETS = {
    BASE + "Noun",
    BASE + "ProperNoun",
    BASE + "Masculine",
    BASE + "Feminine",
    BASE + "Singular",
    BASE + "Plural",
    BASE + "Dual",
}


class I015ProductionNounMorphologyRedTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module("tfont.production_bundles")

    def test_general_linguistic_loader_is_public(self):
        self.assertTrue(
            hasattr(self.module, "PRODUCTION_LINGUISTIC_CORPORA")
            and hasattr(self.module, "load_production_linguistic_bundle")
            and hasattr(self.module, "load_production_linguistic_bundles"),
            "RED: production API is still Noun-only",
        )

    def test_profiles_expose_morphology_capability(self):
        bundles = getattr(self.module, "load_production_linguistic_bundles", self.module.load_production_noun_bundles)()
        for bundle in bundles:
            with self.subTest(profile=bundle.profile.data["profile_id"]):
                self.assertIn(
                    "linguistic.morphology",
                    bundle.profile.data["capabilities"],
                    "RED: production profile has no morphology capability",
                )

    def test_all_seven_noun_layer_targets_compile_for_all_three_corpora(self):
        bundles = self.module.load_production_noun_bundles()
        ir = compile_semantic_ir(tuple(validate_semantic_bundle(bundle) for bundle in bundles))
        semantic_index = dict(ir.semantic_index)
        for target in sorted(EXPECTED_TARGETS):
            capability = (
                "linguistic.part-of-speech"
                if target in {BASE + "Noun", BASE + "ProperNoun"}
                else "linguistic.morphology"
            )
            key = SemanticKey(
                profile_id="linguistic",
                capability_id=capability,
                target=target,
                formal_kind="class",
                semantic_role="annotation-value",
            )
            with self.subTest(target=target):
                self.assertIn(key, semantic_index, "RED: production semantic atom is absent")
                self.assertEqual(
                    {row.corpus_id for row in semantic_index[key]},
                    {"bhsa", "syriac", "extrabiblical"},
                )

    def test_olia_lock_declares_all_used_terms(self):
        bundle = getattr(self.module, "load_production_linguistic_bundle", self.module.load_production_noun_bundle)("bhsa")
        self.assertEqual(set(bundle.ontology_locks[0].data["terms_used"]), EXPECTED_TARGETS)


if __name__ == "__main__":
    unittest.main()
