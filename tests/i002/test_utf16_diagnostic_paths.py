from __future__ import annotations

import copy
import unittest

from ontotf.digests import DigestError, mapping_semantic_digest, profile_semantic_digest

SURROGATE = "\ud800"
ASTRAL = "\U0001f600"
BMP_PRIVATE = "\ue000"


def mapping_fixture() -> dict:
    return {
        "mapping_id": "mapping:test",
        "profile_id": "ontotf-test",
        "native_selector": {
            "kind": "feature-value",
            "component_id": "test-tf",
            "feature": "gn",
            "value": "m",
            "extent": "semantic",
        },
        "native_dependencies": ["dep:a", "dep:b"],
        "external_target": "https://example.org/Masculine",
        "candidate_projections": [],
        "assessment": "exact",
        "publication_relation": None,
        "applicability": {"node_type": "word"},
        "ontology_lock": "lock:test",
        "evidence": [
            {"evidence_id": "evidence:a", "content_digest": "sha256:aaa"},
            {"evidence_id": "evidence:b", "content_digest": "sha256:bbb"},
        ],
        "review": {
            "review_id": "review:test",
            "status": "reviewed",
            "reviewed_mapping_digest": "sha256:old",
            "reviewer_id": "reviewer:audit",
            "reviewed_at": "2026-09-06T00:00:00Z",
            "review_source": "pr:test",
            "review_method": "independent-skeptical",
        },
        "mapping_semantic_digest": "sha256:self",
        "rationale": "display prose",
        "introduced_in": "0.1.0",
        "changed_in": "0.1.1",
    }


def lock_fixture(lock_id: str, suffix: str) -> dict:
    return {
        "lock_id": lock_id,
        "ontology_id": "olia",
        "support_tier": "core",
        "term_namespace": "http://purl.org/olia/olia.owl#",
        "release": "2026-02-04",
        "upstream_release_status": "stable",
        "source_uri": "https://example.org/olia.owl",
        "source_revision": f"rev-{suffix}",
        "content_digest": f"sha256:{suffix}",
        "license": "CC-BY-4.0",
        "redistribution_policy": "allowed",
        "terms_used": ["Feminine", "Masculine"],
    }


def profile_fixture() -> dict:
    return {
        "profile_id": "ontotf-test",
        "schema_version": 1,
        "semantic_contract_version": 1,
        "semantic_domains": ["morphology", "syntax"],
        "expected_parent_manifest_digest": "sha256:parent",
        "dependencies": [
            {"dependency_id": "dep:a", "component_id": "c", "kind": "feature"},
            {"dependency_id": "dep:b", "component_id": "c", "kind": "feature"},
        ],
        "ontology_locks": [
            lock_fixture("lock:a", "a"),
            lock_fixture("lock:b", "b"),
        ],
        "mappings": [
            {"mapping_id": "map:a", "mapping_semantic_digest": "sha256:ma"},
            {"mapping_id": "map:b", "mapping_semantic_digest": "sha256:mb"},
        ],
        "review_readiness": [
            {"mapping_id": "map:a", "status": "reviewed", "reviewed_digest_matches": True},
            {"mapping_id": "map:b", "status": "reviewed", "reviewed_digest_matches": True},
        ],
        "applicability": {},
        "publication_semantics": {},
    }


class Utf16DiagnosticPathTests(unittest.TestCase):
    def assert_unicode_path(self, expected_path: tuple[str | int, ...], func, value) -> None:
        with self.assertRaises(DigestError) as raised:
            func(value)
        self.assertEqual(raised.exception.problem.category, "unicode_domain")
        self.assertEqual(raised.exception.problem.path, expected_path)

    def test_mapping_native_dependency_keeps_authored_item_path(self):
        mapping = mapping_fixture()
        mapping["native_dependencies"][1] = SURROGATE
        self.assert_unicode_path(("native_dependencies", 1), mapping_semantic_digest, mapping)

    def test_mapping_evidence_id_keeps_binding_field_path(self):
        mapping = mapping_fixture()
        mapping["evidence"][1]["evidence_id"] = SURROGATE
        self.assert_unicode_path(("evidence", 1, "evidence_id"), mapping_semantic_digest, mapping)

    def test_mapping_evidence_digest_keeps_binding_field_path(self):
        mapping = mapping_fixture()
        mapping["evidence"][1]["content_digest"] = SURROGATE
        self.assert_unicode_path(("evidence", 1, "content_digest"), mapping_semantic_digest, mapping)

    def test_candidate_evidence_keeps_nested_binding_field_path(self):
        mapping = mapping_fixture()
        mapping.update(
            assessment="ambiguous",
            external_target=None,
            ontology_lock=None,
            publication_relation=None,
            candidate_projections=[
                {
                    "external_target": "https://example.org/A",
                    "ontology_lock": "lock:a",
                    "assessment_candidate": "exact",
                    "evidence": [
                        {"evidence_id": "evidence:a", "content_digest": "sha256:a"},
                        {"evidence_id": SURROGATE, "content_digest": "sha256:b"},
                    ],
                }
            ],
        )
        self.assert_unicode_path(
            ("candidate_projections", 0, "evidence", 1, "evidence_id"),
            mapping_semantic_digest,
            mapping,
        )

    def test_profile_semantic_domain_keeps_authored_item_path(self):
        profile = profile_fixture()
        profile["semantic_domains"][1] = SURROGATE
        self.assert_unicode_path(("semantic_domains", 1), profile_semantic_digest, profile)

    def test_profile_ontology_term_keeps_authored_item_path(self):
        profile = profile_fixture()
        profile["ontology_locks"][1]["terms_used"][1] = SURROGATE
        self.assert_unicode_path(
            ("ontology_locks", 1, "terms_used", 1),
            profile_semantic_digest,
            profile,
        )

    def test_profile_ontology_lock_id_keeps_record_field_path(self):
        profile = profile_fixture()
        profile["ontology_locks"][1]["lock_id"] = SURROGATE
        self.assert_unicode_path(("ontology_locks", 1, "lock_id"), profile_semantic_digest, profile)

    def test_profile_mapping_id_keeps_record_field_path(self):
        profile = profile_fixture()
        profile["mappings"][1]["mapping_id"] = SURROGATE
        self.assert_unicode_path(("mappings", 1, "mapping_id"), profile_semantic_digest, profile)

    def test_profile_review_readiness_mapping_id_keeps_record_field_path(self):
        profile = profile_fixture()
        profile["review_readiness"][1]["mapping_id"] = SURROGATE
        self.assert_unicode_path(("review_readiness", 1, "mapping_id"), profile_semantic_digest, profile)

    def test_dependency_id_is_already_path_safe_before_sorting(self):
        profile = profile_fixture()
        profile["dependencies"][1]["dependency_id"] = SURROGATE
        self.assert_unicode_path(("dependencies", 1, "dependency_id"), profile_semantic_digest, profile)

    def test_valid_non_bmp_utf16_ordering_remains_order_invariant(self):
        one = mapping_fixture()
        one["native_dependencies"] = [BMP_PRIVATE, ASTRAL]
        two = copy.deepcopy(one)
        two["native_dependencies"].reverse()
        self.assertEqual(mapping_semantic_digest(one), mapping_semantic_digest(two))

    def test_duplicate_set_identifier_contract_is_unchanged(self):
        mapping = mapping_fixture()
        mapping["native_dependencies"] = ["dep:a", "dep:a"]
        with self.assertRaises(DigestError) as raised:
            mapping_semantic_digest(mapping)
        self.assertEqual(raised.exception.problem.category, "projection_error")
        self.assertEqual(raised.exception.problem.path, ("native_dependencies", 1))


if __name__ == "__main__":
    unittest.main()
