from __future__ import annotations

import copy
import unittest

from ontotf.digests import profile_semantic_digest, source_bundle_digest


def semantic_projection() -> dict:
    return {
        "profile_id": "ontotf-test",
        "schema_version": 1,
        "semantic_contract_version": 1,
        "semantic_domains": ["morphology"],
        "expected_parent_manifest_digest": "sha256:parent",
        "dependencies": [],
        "ontology_locks": [],
        "mappings": [],
        "review_readiness": [],
        "applicability": {},
        "publication_semantics": {},
    }


class SourceSemanticIdentitySeparationTests(unittest.TestCase):
    def test_formatting_or_comment_only_source_change_does_not_change_semantic_digest(self):
        release_a = {
            "sources": [("profile.yaml", b"profile_id: ontotf-test\nsemantic: same\n")],
            "semantic_projection": semantic_projection(),
        }
        release_b = {
            "sources": [
                (
                    "profile.yaml",
                    b"# display-only comment\nprofile_id: ontotf-test  \nsemantic: same\n",
                )
            ],
            "semantic_projection": copy.deepcopy(release_a["semantic_projection"]),
        }

        self.assertNotEqual(
            source_bundle_digest(release_a["sources"]),
            source_bundle_digest(release_b["sources"]),
        )
        self.assertEqual(
            profile_semantic_digest(release_a["semantic_projection"]),
            profile_semantic_digest(release_b["semantic_projection"]),
        )


if __name__ == "__main__":
    unittest.main()
