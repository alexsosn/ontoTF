from __future__ import annotations

import copy
import unittest

from tfont.coverage import coverage_denominator_digest, load_packaged_coverage_manifest
from tfont.semantic_validation import (
    SemanticArtifact, SemanticSourceBundle, SemanticValidationError, validate_semantic_bundle,
)


class I027B1AdversarialTests(unittest.TestCase):
    def test_forged_native_selector_fails_reviewed_digest(self):
        from tfont.production_bundles import load_production_verb_bundle
        original = load_production_verb_bundle("bhsa")
        mutated = copy.deepcopy(original.mappings.data)
        verb = next(x for x in mutated["mappings"] if x["mapping_id"] == "mapping:bhsa:olia-verb")
        verb["native_binding"]["value"] = "subs"
        forged = SemanticSourceBundle(
            profile=original.profile,
            expected_parent_manifest=original.expected_parent_manifest,
            mappings=SemanticArtifact("mapping", "forged-verb", mutated),
            ontology_locks=original.ontology_locks,
            evidences=original.evidences,
        )
        with self.assertRaises(SemanticValidationError):
            validate_semantic_bundle(forged)

    def test_verb_must_not_replace_historical_noun_release(self):
        from tfont.production_bundles import load_production_linguistic_bundle, load_production_verb_bundle
        noun = load_production_linguistic_bundle("bhsa")
        verb = load_production_verb_bundle("bhsa")
        self.assertEqual(noun.profile.data["profile_version"], "0.2.0")
        self.assertEqual(verb.profile.data["profile_version"], "0.3.0")
        self.assertNotIn(
            "mapping:bhsa:olia-verb",
            {m["mapping_id"] for m in noun.mappings.data["mappings"]},
        )

    def test_native_only_verbal_stems_are_not_promoted(self):
        manifest = load_packaged_coverage_manifest("p004-i027b1-bhsa-verb-v1", "bhsa")
        selected = [
            item for item in manifest["semantic_items"]
            if item["item_id"] == "node_feature:vs"
            or item["item_id"].startswith("node_value:vs=")
        ]
        self.assertEqual(len(selected), 27)
        self.assertTrue(all(
            item["accounting"]["production"]["assessments"] == ["native-only"]
            and item["accounting"]["production"]["common_target"] is False
            for item in selected
        ))


if __name__ == "__main__":
    unittest.main()
