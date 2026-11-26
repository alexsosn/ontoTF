from __future__ import annotations

import unittest

from ontotf.digests import DigestError, profile_semantic_digest


class UnicodeProjectionErrorContractTests(unittest.TestCase):
    def test_lone_surrogate_in_semantic_set_uses_stable_unicode_domain_error(self):
        projection = {
            "profile_id": "tfont-test",
            "schema_version": 1,
            "semantic_contract_version": 1,
            "semantic_domains": ["\ud800"],
            "expected_parent_manifest_digest": "sha256:parent",
            "dependencies": [],
            "ontology_locks": [],
            "mappings": [],
            "review_readiness": [],
            "applicability": {},
            "publication_semantics": {},
        }

        with self.assertRaises(DigestError) as raised:
            profile_semantic_digest(projection)
        self.assertEqual(raised.exception.problem.category, "unicode_domain")


if __name__ == "__main__":
    unittest.main()
