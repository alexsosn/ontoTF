from __future__ import annotations

import unittest

from ontotf.digests import (
    _normalize_evidence_bindings,
    _normalize_mapping_identities,
    _normalize_ontology_lock_identities,
    _normalize_record_set,
    _normalize_review_readiness,
    _normalize_unique_strings,
)


BMP_PRIVATE = "\ue000"
NON_BMP = "\U0001f600"
UTF16_ORDER = [NON_BMP, BMP_PRIVATE]


def lock(lock_id: str) -> dict:
    return {
        "lock_id": lock_id,
        "ontology_id": "ontology",
        "support_tier": "core",
        "term_namespace": "https://example.org/#",
        "release": "1",
        "source_uri": "https://example.org/ontology",
        "content_digest": "sha256:x",
        "license": "CC0-1.0",
        "terms_used": [BMP_PRIVATE, NON_BMP],
    }


class UTF16SetOrderingTests(unittest.TestCase):
    def test_all_semantic_string_sets_use_utf16_code_unit_order(self):
        # Python code-point order puts U+E000 before U+1F600, while UTF-16
        # code-unit order puts the non-BMP surrogate pair first. The v1
        # contract must choose one language-neutral order explicitly.
        self.assertEqual(
            _normalize_unique_strings([BMP_PRIVATE, NON_BMP], path=("semantic_domains",)),
            UTF16_ORDER,
        )

        evidence = _normalize_evidence_bindings(
            [
                {"evidence_id": BMP_PRIVATE, "content_digest": "sha256:b"},
                {"evidence_id": NON_BMP, "content_digest": "sha256:a"},
            ],
            path=("evidence",),
        )
        self.assertEqual([item["evidence_id"] for item in evidence], UTF16_ORDER)

        dependencies = _normalize_record_set(
            [
                {"dependency_id": BMP_PRIVATE, "kind": "feature"},
                {"dependency_id": NON_BMP, "kind": "feature"},
            ],
            id_field="dependency_id",
            path=("dependencies",),
        )
        self.assertEqual([item["dependency_id"] for item in dependencies], UTF16_ORDER)

        locks = _normalize_ontology_lock_identities([lock(BMP_PRIVATE), lock(NON_BMP)])
        self.assertEqual([item["lock_id"] for item in locks], UTF16_ORDER)
        for item in locks:
            self.assertEqual(item["terms_used"], UTF16_ORDER)

        mappings = _normalize_mapping_identities(
            [
                {"mapping_id": BMP_PRIVATE, "mapping_semantic_digest": "sha256:b"},
                {"mapping_id": NON_BMP, "mapping_semantic_digest": "sha256:a"},
            ]
        )
        self.assertEqual([item["mapping_id"] for item in mappings], UTF16_ORDER)

        readiness = _normalize_review_readiness(
            [
                {"mapping_id": BMP_PRIVATE, "status": "reviewed", "reviewed_digest_matches": True},
                {"mapping_id": NON_BMP, "status": "reviewed", "reviewed_digest_matches": True},
            ]
        )
        self.assertEqual([item["mapping_id"] for item in readiness], UTF16_ORDER)


if __name__ == "__main__":
    unittest.main()
