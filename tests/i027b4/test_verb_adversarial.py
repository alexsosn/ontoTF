from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

from tfont.semantic_validation import (
    SemanticArtifact, SemanticSourceBundle,
    SemanticValidationError, validate_semantic_bundle,
)

ROOT=Path(__file__).resolve().parents[2]
BUILDER=ROOT/"scripts/coverage/build_i027b4_extrabiblical_verb.py"


class ExtraBiblicalVerbAdversarialTests(unittest.TestCase):
    def test_forged_native_selector_invalidates_review(self):
        from tfont.production_bundles import load_production_verb_bundle
        bundle=load_production_verb_bundle("extrabiblical")
        for key,value in (("value","subs"),("feature","vs"),("node_type","lex")):
            with self.subTest(key=key):
                mutated=copy.deepcopy(bundle.mappings.data)
                mapping=next(x for x in mutated["mappings"]
                    if x["mapping_id"]=="mapping:extrabiblical:olia-verb")
                mapping["native_binding"][key]=value
                forged=SemanticSourceBundle(
                    profile=bundle.profile,
                    expected_parent_manifest=bundle.expected_parent_manifest,
                    mappings=SemanticArtifact("mapping","forged-extra",mutated),
                    ontology_locks=bundle.ontology_locks,
                    evidences=bundle.evidences,
                )
                with self.assertRaises(SemanticValidationError):
                    validate_semantic_bundle(forged)

    def test_verb_cannot_be_loaded_from_historical_profile(self):
        from tfont.production_bundles import load_production_linguistic_bundle
        old=load_production_linguistic_bundle("extrabiblical")
        self.assertEqual(old.profile.data["profile_version"],"0.2.0")
        self.assertNotIn("mapping:extrabiblical:olia-verb",
            {x["mapping_id"] for x in old.mappings.data["mappings"]})

    def test_source_pins_cannot_be_forged_in_coverage_builder(self):
        spec=importlib.util.spec_from_file_location("i027b4_audit",BUILDER)
        assert spec and spec.loader
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        baseline=mod.build_successor()
        self.assertEqual(baseline["denominator_source_revision"],
            "9a56288e6777bad6328856acf055c780e65dd5d9")
        self.assertEqual(baseline["denominator_digest"],
            "sha256:58bdadddd54cc1848eddf0b5918137e37e85bbea52022cc2a40386ad46f1b46e")
        self.assertEqual(
            [x["item_id"] for x in baseline["semantic_items"]
             if x["accounting"]["production"] and
                "mapping:extrabiblical:olia-verb" in
                x["accounting"]["production"]["source_ids"]],
            ['node_value:sp="verb"'],
        )


if __name__=="__main__":
    unittest.main()
