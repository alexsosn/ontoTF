from __future__ import annotations

import hashlib
import unittest
from importlib.resources import files

from tfont.production_bundles import (
    load_production_linguistic_bundle,
    load_production_noun_bundle,
)

BASELINE_BLOBS = {
    "profiles/bhsa/0.1.0/evidence/native-pos.json": "ab9cea0d7d55d36e152525f752e363eac50064e3",
    "profiles/bhsa/0.1.0/mappings/noun.json": "1e4facf1013679ae3586ac735981bd40e6fe0532",
    "profiles/bhsa/0.1.0/parent/expected-components.json": "6d1e2b220051776b2f1142db494d09ef46006503",
    "profiles/bhsa/0.1.0/profile.json": "393a6eae7976840e15c7a228bf792f0657987eba",
    "profiles/extrabiblical/0.1.0/evidence/feature-authority.json": "4fec22effdb9aa92eab13ff1e81aeea748f25978",
    "profiles/extrabiblical/0.1.0/evidence/native-pos-enum.json": "dfa931466325157fd8869bf4346887217d65c38f",
    "profiles/extrabiblical/0.1.0/mappings/noun.json": "5659dc0610180127dbfa2b441afd84f55eb46598",
    "profiles/extrabiblical/0.1.0/parent/expected-components.json": "4da5e89530799ee7d90b4c86d21a2d37f4079934",
    "profiles/extrabiblical/0.1.0/profile.json": "a4068f60951effd1dde211dfd193d7b190db6696",
    "profiles/syriac/0.1.0/evidence/native-pos.json": "ce48b294f0aa091048b64abb97ba078bfae02470",
    "profiles/syriac/0.1.0/evidence/proper-noun-encoding.json": "b3604b9fb4c475f1e939c9973a371046070586aa",
    "profiles/syriac/0.1.0/mappings/noun.json": "732eda5bc2932ac4448aec7635f752667e016038",
    "profiles/syriac/0.1.0/parent/expected-components.json": "7834d896a8fcfecb3eb9cf356607f1d4a1c66187",
    "profiles/syriac/0.1.0/profile.json": "5150d66432b3b48bd42cd0cd62ef24d40d2426e7",
}


def git_blob_sha(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


class I015ProfileReleaseIdentityTests(unittest.TestCase):
    def test_all_historical_profile_010_bytes_are_unchanged(self):
        root = files("tfont").joinpath("resources")
        for relative, expected in BASELINE_BLOBS.items():
            with self.subTest(relative=relative):
                self.assertEqual(git_blob_sha(root.joinpath(*relative.split("/")).read_bytes()), expected)

    def test_legacy_and_expanded_loaders_keep_distinct_profile_releases(self):
        for corpus_id in ("bhsa", "syriac", "extrabiblical"):
            with self.subTest(corpus_id=corpus_id):
                old = load_production_noun_bundle(corpus_id)
                new = load_production_linguistic_bundle(corpus_id)
                self.assertEqual(old.profile.data["profile_version"], "0.1.0")
                self.assertEqual(new.profile.data["profile_version"], "0.2.0")
                self.assertEqual(
                    old.expected_parent_manifest.data,
                    new.expected_parent_manifest.data,
                )
                self.assertEqual(
                    old.ontology_locks[0].data["content_digest"],
                    new.ontology_locks[0].data["content_digest"],
                )
                self.assertNotEqual(
                    old.ontology_locks[0].data["terms_used"],
                    new.ontology_locks[0].data["terms_used"],
                )


if __name__ == "__main__":
    unittest.main()
