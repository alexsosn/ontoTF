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

    def test_no_implicit_cross_corpus_or_stem_mapping(self):
        from tfont.production_bundles import ProductionBundleError

        with self.assertRaises(ProductionBundleError):
            load_production_verb_bundle("unsupported-corpus")
        # ExtraBiblical now has an independently reviewed v0.3.0 Verb
        # release. The Syriac v0.3.0 bundle must still own its own source,
        # component identity and selector (never reuse a foreign mapping).
        syriac = validate_semantic_bundle(load_production_verb_bundle("syriac"))
        extrabiblical = validate_semantic_bundle(
            load_production_verb_bundle("extrabiblical")
        )
        for corpus_id, bundle in (
            ("syriac", syriac),
            ("extrabiblical", extrabiblical),
        ):
            added = next(
                mapping for mapping in bundle.indexes.mappings.values()
                if mapping["mapping_id"] == f"mapping:{corpus_id}:olia-verb"
            )
            self.assertEqual(added["corpus_id"], corpus_id)
            self.assertEqual(added["native_binding"], {
                "component_id": f"{corpus_id}-tf",
                "execution_shape": "value-predicate",
                "feature": "sp",
                "node_type": "word",
                "value": "verb",
            })
            self.assertTrue(all(
                item["evidence_id"].startswith(f"evidence:{corpus_id}:")
                or item["evidence_id"] == "evidence:olia:verb-class"
                for item in added["evidence"]
            ))
            self.assertNotIn("vs", added["native_binding"])


if __name__ == "__main__":
    unittest.main()
