from __future__ import annotations

import unittest

from tfont.production_bundles import (
    load_production_adj_adv_bundle,
    load_production_linguistic_bundle,
    load_production_noun_bundle,
    load_production_verb_bundle,
)
from tfont.release_registry import load_profile, list_profile_releases
from tfont.semantic_validation import validate_semantic_bundle
from tfont.semantic_ir import compile_semantic_ir


LEGACY = {
    "0.1.0": load_production_noun_bundle,
    "0.2.0": load_production_linguistic_bundle,
    "0.3.0": load_production_verb_bundle,
    "0.4.0": load_production_adj_adv_bundle,
}
RELEASES = {
    "bhsa": ("0.1.0", "0.2.0", "0.3.0", "0.4.0"),
    "syriac": ("0.1.0", "0.2.0", "0.3.0", "0.4.0"),
    "extrabiblical": ("0.1.0", "0.2.0", "0.3.0"),
}


class GenericReleaseCatalogRed(unittest.TestCase):
    def test_all_eleven_historical_bundle_contracts_are_unchanged(self):
        for corpus, versions in RELEASES.items():
            self.assertEqual(list_profile_releases(corpus), versions)
            for version in versions:
                with self.subTest(corpus=corpus, version=version):
                    old = LEGACY[version](corpus)
                    new = load_profile(corpus, release_id=version)
                    for name in ("profile", "expected_parent_manifest", "mappings"):
                        self.assertEqual(getattr(old, name), getattr(new, name))
                    self.assertEqual(old.ontology_locks, new.ontology_locks)
                    self.assertEqual(old.evidences, new.evidences)
                    indexes = validate_semantic_bundle(new)
                    self.assertEqual(indexes, validate_semantic_bundle(old))
                    self.assertEqual(
                        compile_semantic_ir((indexes,)),
                        compile_semantic_ir((validate_semantic_bundle(old),)),
                    )

    def test_current_is_explicit_and_not_guessed(self):
        self.assertEqual(load_profile("bhsa").profile.data["profile_version"], "0.4.0")
        self.assertEqual(load_profile("syriac").profile.data["profile_version"], "0.4.0")
        self.assertEqual(load_profile("extrabiblical").profile.data["profile_version"], "0.3.0")

    def test_historical_wrappers_still_select_previous_releases(self):
        self.assertEqual(load_production_noun_bundle("bhsa").profile.data["profile_version"], "0.1.0")
        self.assertEqual(load_production_linguistic_bundle("syriac").profile.data["profile_version"], "0.2.0")
        self.assertEqual(load_production_verb_bundle("extrabiblical").profile.data["profile_version"], "0.3.0")


if __name__ == "__main__":
    unittest.main()
