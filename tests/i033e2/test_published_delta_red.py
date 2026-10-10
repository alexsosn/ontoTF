"""TDD contract: published v0.3→v0.4 releases can be represented as compact deltas.

Only already published/validated registry releases are inputs. This test never
approves an unreviewed source/ontology proposal or issues a review receipt.
"""
from __future__ import annotations

import unittest

from tfont.published_deltas import (
    PublishedDeltaError, build_published_delta, load_published_delta,
)
from tfont.release_registry import load_profile
from tfont.semantic_validation import validate_semantic_bundle
from tfont.semantic_ir import compile_semantic_ir


class PublishedReleaseDeltaTests(unittest.TestCase):
    def test_two_corpora_adjective_adverb_parity_without_cloning_old_mappings(self):
        for corpus in ("bhsa","syriac"):
            with self.subTest(corpus=corpus):
                base=load_profile(corpus,"0.3.0")
                expected=load_profile(corpus,"0.4.0")
                delta=build_published_delta(corpus,"0.3.0","0.4.0")
                self.assertEqual(delta["schema_version"],1)
                self.assertEqual(delta["authority"],"published-registry-parity-only")
                self.assertEqual(delta["corpus_id"],corpus)
                self.assertEqual(delta["base_release"],"0.3.0")
                self.assertEqual(delta["target_release"],"0.4.0")
                self.assertEqual(
                    [m["mapping_id"] for m in delta["added_mappings"]],
                    [f"mapping:{corpus}:olia-adjective",f"mapping:{corpus}:olia-adverb"],
                )
                self.assertEqual(len(delta["added_dependencies"]),2)
                self.assertEqual(len(delta["added_evidence"]),3)
                self.assertNotIn("mappings",delta)
                self.assertNotIn("semantic_items",delta)
                self.assertNotIn("coverage_snapshot",delta)
                self.assertLess(len(__import__("json").dumps(delta)),3500)
                rebuilt=load_published_delta(delta)
                self.assertEqual(rebuilt,expected)
                self.assertEqual(
                    validate_semantic_bundle(rebuilt),
                    validate_semantic_bundle(expected),
                )
                self.assertEqual(
                    compile_semantic_ir((validate_semantic_bundle(rebuilt),)),
                    compile_semantic_ir((validate_semantic_bundle(expected),)),
                )
                self.assertEqual(base,load_profile(corpus,"0.3.0"))

    def test_deterministic_compact_delta_under_repeated_build(self):
        for corpus in ("bhsa","syriac"):
            first=build_published_delta(corpus,"0.3.0","0.4.0")
            self.assertEqual(first,build_published_delta(corpus,"0.3.0","0.4.0"))
            self.assertEqual(load_published_delta(first),load_profile(corpus,"0.4.0"))

    def test_unpublished_release_does_not_grant_runtime_approval(self):
        for corpus,version in (("bhsa","unreviewed-candidate"),("extrabiblical","0.4.0")):
            with self.subTest(corpus=corpus),self.assertRaises(PublishedDeltaError):
                build_published_delta(corpus,"0.3.0",version)


if __name__=="__main__":
    unittest.main()
