from __future__ import annotations

import copy
import unittest

from tfont.semantic_validation import (
    SemanticArtifact, SemanticSourceBundle, SemanticValidationError,
    validate_semantic_bundle,
)
from tfont.production_bundles import (
    load_production_verb_bundle, load_production_linguistic_bundle,
)


class SyriacVerbAdversarialTests(unittest.TestCase):
    def test_reject_forged_pos_or_morphology_selector(self):
        bundle = load_production_verb_bundle("syriac")
        for key, value in (("value", "subs"), ("feature", "vs"), ("node_type", "lex")):
            with self.subTest(key=key):
                mutated = copy.deepcopy(bundle.mappings.data)
                mapping = next(
                    row for row in mutated["mappings"]
                    if row["mapping_id"] == "mapping:syriac:olia-verb"
                )
                mapping["native_binding"][key] = value
                forged = SemanticSourceBundle(
                    profile=bundle.profile,
                    expected_parent_manifest=bundle.expected_parent_manifest,
                    mappings=SemanticArtifact("mapping", "forged-syriac", mutated),
                    ontology_locks=bundle.ontology_locks,
                    evidences=bundle.evidences,
                )
                with self.assertRaises(SemanticValidationError):
                    validate_semantic_bundle(forged)

    def test_historical_loader_is_stable(self):
        old = load_production_linguistic_bundle("syriac")
        latest = load_production_verb_bundle("syriac")
        self.assertEqual(old.profile.data["profile_version"], "0.2.0")
        self.assertEqual(latest.profile.data["profile_version"], "0.3.0")
        self.assertNotIn(
            "mapping:syriac:olia-verb",
            {m["mapping_id"] for m in old.mappings.data["mappings"]},
        )

    def test_not_implicit_extra_biblical_or_stem_mapping(self):
        from tfont.production_bundles import ProductionBundleError
        with self.assertRaises(ProductionBundleError):
            load_production_verb_bundle("extrabiblical")
        syriac = load_production_verb_bundle("syriac")
        added = next(
            mapping for mapping in syriac.mappings.data["mappings"]
            if mapping["mapping_id"] == "mapping:syriac:olia-verb"
        )
        self.assertEqual(added["native_binding"]["feature"], "sp")
        self.assertEqual(added["native_binding"]["value"], "verb")


if __name__ == "__main__":
    unittest.main()
