"""I-034G RED: the two *opt-in*, reviewed morphology cohorts must be installed.

Source inventories and proposed dispositions are in merged research PRs #353/#355.
These tests intentionally fail until release resources exist.
"""
from __future__ import annotations

import json
import unittest

from tfont.release_registry import load_profile, list_profile_releases
from tfont.semantic_validation import validate_semantic_bundle
from tfont.digests import canonical_json_bytes

OLIA = "http://purl.org/olia/olia.owl#"
CANDIDATES = {
    "bhsa": ("docs/research/data/i034c/bhsa-morphology-olia.json", 29, 5),
    "syriac": ("docs/research/data/i034d/syriac-morphology-olia.json", 22, 9),
}


def observed_rows(corpus):
    # The repository-local research ledgers deliberately are not production authority.
    from pathlib import Path
    repo = Path(__file__).resolve().parents[2]
    path, _, _ = CANDIDATES[corpus]
    return json.loads((repo / path).read_text(encoding="utf-8"))["rows"]


class ReleasedMorphologyBatch(unittest.TestCase):
    def test_installed_versions_and_reviewed_decisions(self):
        for corpus, (_, total, exact) in CANDIDATES.items():
            with self.subTest(corpus=corpus):
                self.assertIn("0.6.0", list_profile_releases(corpus))
                old = validate_semantic_bundle(load_profile(corpus, "0.5.0"))
                new = validate_semantic_bundle(load_profile(corpus, "0.6.0"))
                old_ids = {m["mapping_id"] for m in old.mappings.data["mappings"]}
                self.assertEqual(
                    {m["mapping_id"]: m["mapping_semantic_digest"] for m in old.mappings.data["mappings"]},
                    {m["mapping_id"]: m["mapping_semantic_digest"] for m in new.mappings.data["mappings"]
                     if m["mapping_id"] in old_ids},
                )
                additions = [m for m in new.mappings.data["mappings"] if m["mapping_id"] not in old_ids]
                self.assertEqual(len(additions), total)
                expected = {(r["feature"], r["value"]): r for r in observed_rows(corpus)}
                self.assertEqual(len(expected), total)
                self.assertEqual(
                    {(m["native_binding"]["feature"], m["native_binding"]["value"]) for m in additions},
                    set(expected),
                )
                self.assertEqual(len([m for m in additions if m["native_state"] == "positive"]), exact)
                self.assertEqual(len([m for m in additions if m["native_state"] == "native-only"]), total-exact)
                self.assertEqual(len({canonical_json_bytes(m["native_binding"]) for m in new.mappings.data["mappings"]}),
                                 len(new.mappings.data["mappings"]))
                for m in additions:
                    selector = (m["native_binding"]["feature"], m["native_binding"]["value"])
                    row = expected[selector]
                    self.assertEqual(m["native_binding"]["node_type"], "word")
                    self.assertEqual(m["review"]["status"], "reviewed")
                    self.assertEqual(m["review"]["reviewed_mapping_digest"], m["mapping_semantic_digest"])
                    self.assertTrue(m["evidence"])
                    self.assertEqual(bool(m["projections"]), row["assessment"] == "exact" and not (corpus == "bhsa" and m["native_binding"]["feature"] in {"prs_ps", "prs_gn", "prs_nu"}))
                    if row["assessment"] == "exact" and not (corpus == "bhsa" and m["native_binding"]["feature"] in {"prs_ps", "prs_gn", "prs_nu"}):
                        self.assertEqual(m["projections"][0]["target"], row["ontology_target"])
                        self.assertEqual(m["projections"][0]["review"]["status"], "reviewed")
                    else:
                        self.assertEqual(m["projections"], [])
                # Suffix morphology is not silently flattened into host morphology.
                if corpus == "bhsa":
                    ps = next(m for m in additions if (m["native_binding"]["feature"], m["native_binding"]["value"]) == ("ps", "p1"))
                    suffix = next(m for m in additions if (m["native_binding"]["feature"], m["native_binding"]["value"]) == ("prs_ps", "p1"))
                    self.assertNotEqual(ps["native_binding"], suffix["native_binding"])
                    self.assertEqual(suffix["native_state"], "native-only")
                    self.assertEqual(suffix["projections"], [])
                self.assertIsNotNone(new)
    
    def test_historical_aliases_not_mutated(self):
        from tfont.release_registry import _load_catalogue
        c = _load_catalogue()
        for corpus in CANDIDATES:
            self.assertEqual(c["corpora"][corpus]["current"], "0.4.0")
            self.assertEqual(load_profile(corpus, "current").profile.data["profile_version"], "0.4.0")
            self.assertEqual(len(load_profile(corpus, "0.5.0").ontology_locks), 2)
            self.assertEqual(len(load_profile(corpus, "0.6.0").ontology_locks), 3)

    def test_no_invented_perfect_or_unverified_alias(self):
        for corpus in CANDIDATES:
            mappings = load_profile(corpus, "0.6.0").mappings.data["mappings"]
            new = [m for m in mappings if m["mapping_id"].startswith("mapping:"+corpus+":morph-")]
            for m in new:
                p = m["projections"]
                self.assertNotIn("#Perfect", str(p))
                self.assertNotIn("#Imperfect", str(p))
                if corpus == "syriac" and m["native_binding"]["feature"] == "st" and m["native_binding"]["value"] == "c":
                    self.assertFalse(p)
