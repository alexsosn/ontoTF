"""RED contract for protected, data-driven batch release base selection."""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from tfont import overlay_handoff
from tfont.batch_proposals import packaged_resource
from tfont.coverage import load_packaged_coverage_manifest
from tfont.release_registry import load_profile
from tests.i033e.test_overlay_handoff import cohort, assemble


REGISTRY = "resources/batch_release_bases/v1.json"
EXPECTED = {
    "bhsa": ("0.4.0", "p004-i027c2-bhsa-adj-adv-v1", 219),
    "syriac": ("0.4.0", "p004-i027c2-syriac-adj-adv-v1", 74),
    "extrabiblical": ("0.3.0", "p004-i027b4-extrabiblical-verb-v1", 136),
}


class TrustedHandoffBaseRed(unittest.TestCase):
    def test_three_explicit_immutable_installed_bases(self):
        registry = packaged_resource(REGISTRY)
        self.assertEqual(set(registry["corpora"]), set(EXPECTED))
        for corpus,(version,resource_set,count) in EXPECTED.items():
            with self.subTest(corpus=corpus):
                self.assertEqual(
                    overlay_handoff._trusted_handoff_base(corpus),
                    (version,resource_set),
                )
                base=load_profile(corpus)
                source=load_packaged_coverage_manifest(resource_set,corpus)
                self.assertEqual(base.profile.data["profile_version"],version)
                self.assertEqual(len(source["semantic_items"]),count)
                self.assertEqual(source["corpus_id"],corpus)

    def test_unsupported_or_malformed_registry_fails_closed(self):
        original=packaged_resource(REGISTRY)
        for bad_corpus in ("", "no-such-corpus", "../bhsa", 123):
            with self.subTest(corpus=bad_corpus),self.assertRaises(ValueError):
                overlay_handoff._trusted_handoff_base(bad_corpus)
        mutated=copy.deepcopy(original)
        mutated["corpora"]["bhsa"]["base_release"]="0.3.0"
        def broken(name):
            return mutated if name==REGISTRY else packaged_resource(name)
        with patch.object(overlay_handoff, "packaged_resource", side_effect=broken),self.assertRaises(ValueError):
            overlay_handoff._trusted_handoff_base("bhsa")
        mutated=copy.deepcopy(original)
        mutated["corpora"]["bhsa"]["coverage_resource_set"]="p004-r011-baseline-v1"
        with patch.object(overlay_handoff, "packaged_resource",
                          side_effect=lambda name: mutated if name==REGISTRY else packaged_resource(name)),self.assertRaises(ValueError):
            overlay_handoff._trusted_handoff_base("bhsa")
        mutated=copy.deepcopy(original)
        mutated["corpora"]["bhsa"]["coverage_git_blob"]="0"*40
        with patch.object(overlay_handoff,"packaged_resource",
                          side_effect=lambda name: mutated if name==REGISTRY else packaged_resource(name)),self.assertRaises(ValueError):
            overlay_handoff._trusted_handoff_base("bhsa")
        mutated=copy.deepcopy(original)
        mutated["corpora"]["bhsa"]["bogus_authentication"]="self-approved"
        with patch.object(overlay_handoff,"packaged_resource",
                          side_effect=lambda name: mutated if name==REGISTRY else packaged_resource(name)),self.assertRaises(ValueError):
            overlay_handoff._trusted_handoff_base("bhsa")

    def test_existing_ten_real_source_candidates_retain_exact_base_identities(self):
        ledger,read,packet,observation=cohort()
        pack=assemble(ledger,read,packet,observation)
        self.assertFalse(pack["release_authorized"])
        self.assertEqual({x["corpus_id"]:(x["base_release"],x["coverage_base"]["resource_set"])
                          for x in pack["corpora"]},
                         {corpus:tuple(EXPECTED[corpus][:2]) for corpus in ("bhsa","syriac")})
        self.assertIsNone(overlay_handoff.verify_overlay_handoff_integrity(pack))

    def test_forged_internally_consistent_historical_coverage_source_rejected(self):
        ledger,read,packet,observation=cohort()
        pack=assemble(ledger,read,packet,observation)
        replaced=copy.deepcopy(pack)
        corpus=next(c for c in replaced["corpora"] if c["corpus_id"]=="bhsa")
        old=load_packaged_coverage_manifest("p004-r011-baseline-v1","bhsa")
        corpus["coverage_base"]={
            "resource_set":"p004-r011-baseline-v1",
            "manifest_digest":overlay_handoff._digest(old),
            "denominator_digest":old["denominator_digest"],
        }
        replaced["content_digest"]=overlay_handoff._digest({
            k:v for k,v in replaced.items() if k!="content_digest"
        })
        # Hash consistency alone must never grant a stale selection.
        with self.assertRaisesRegex(ValueError,"coverage base"):
            overlay_handoff.verify_overlay_handoff_integrity(replaced)

    def test_rehashed_wrong_coverage_set_cannot_bypass_trusted_selection(self):
        ledger,read,packet,observation=cohort()
        pack=assemble(ledger,read,packet,observation)
        mutated=copy.deepcopy(pack)
        corp=next(c for c in mutated["corpora"] if c["corpus_id"]=="bhsa")
        corp["coverage_base"]["resource_set"]="p004-r011-baseline-v1"
        mutated["content_digest"]=overlay_handoff._digest({
            k:v for k,v in mutated.items() if k!="content_digest"
        })
        with self.assertRaises(ValueError):
            overlay_handoff.verify_overlay_handoff_integrity(mutated)


if __name__=="__main__":
    unittest.main()
