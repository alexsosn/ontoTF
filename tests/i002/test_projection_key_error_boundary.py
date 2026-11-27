from __future__ import annotations

import unittest

from ontotf.digests import (
    DigestError,
    canonical_json_bytes,
    evidence_record_projection,
    mapping_semantic_projection,
    profile_semantic_digest,
)


def normalized_evidence() -> dict:
    return {
        "evidence_id": "evidence:test",
        "kind": "native-doc",
        "source_uri": "https://example.org/source",
        "content_mode": "normalized-record",
        "reviewed_content": {"statement": "test"},
    }


def semantic_mapping() -> dict:
    return {
        "mapping_id": "mapping:test",
        "profile_id": "profile:test",
        "native_selector": {"kind": "feature-value", "feature": "gn", "value": "m"},
        "native_dependencies": [],
        "external_target": "https://example.org/term",
        "candidate_projections": [],
        "assessment": "exact",
        "publication_relation": None,
        "applicability": {},
        "ontology_lock": "lock:test",
        "evidence": [],
    }


def ontology_lock() -> dict:
    return {
        "lock_id": "lock:test",
        "ontology_id": "olia",
        "support_tier": "core",
        "term_namespace": "https://example.org/olia#",
        "release": "test-release",
        "source_uri": "https://example.org/olia.ttl",
        "content_digest": "sha256:test",
        "license": "CC-BY-4.0",
        "terms_used": [],
    }


def profile_projection() -> dict:
    return {
        "profile_id": "profile:test",
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


class ProjectionKeyErrorBoundaryTests(unittest.TestCase):
    def assert_projection_key_error(self, callable_, *args, expected_path=()) -> DigestError:
        with self.assertRaises(DigestError) as raised:
            callable_(*args)
        self.assertEqual(raised.exception.problem.category, "projection_error")
        self.assertEqual(raised.exception.problem.path, expected_path)
        self.assertIn("keys", raised.exception.problem.message)
        return raised.exception

    def test_evidence_projection_rejects_integer_key_through_digest_error(self):
        evidence = normalized_evidence()
        evidence[1] = "invalid-key"
        self.assert_projection_key_error(evidence_record_projection, evidence)

    def test_mapping_projection_rejects_mixed_unknown_key_types_through_digest_error(self):
        mapping = semantic_mapping()
        mapping["future_field"] = "unknown-string-key"
        mapping[1] = "invalid-key"
        self.assert_projection_key_error(mapping_semantic_projection, mapping)

    def test_candidate_projection_non_string_key_preserves_nested_path(self):
        mapping = semantic_mapping()
        candidate = {
            "external_target": "https://example.org/candidate",
            "ontology_lock": "lock:candidate",
            "assessment_candidate": "close",
            "evidence": [],
        }
        candidate[("invalid", "key")] = "value"
        mapping["candidate_projections"] = [candidate]
        self.assert_projection_key_error(
            mapping_semantic_projection,
            mapping,
            expected_path=("candidate_projections", 0),
        )

    def test_profile_projection_rejects_integer_top_level_key_through_digest_error(self):
        projection = profile_projection()
        projection[1] = "invalid-key"
        self.assert_projection_key_error(profile_semantic_digest, projection)

    def test_profile_ontology_lock_non_string_key_preserves_nested_path(self):
        projection = profile_projection()
        lock = ontology_lock()
        lock[1] = "invalid-key"
        projection["ontology_locks"] = [lock]
        self.assert_projection_key_error(
            profile_semantic_digest,
            projection,
            expected_path=("ontology_locks", 0),
        )

    def test_unknown_string_field_keeps_existing_projection_error_contract(self):
        evidence = normalized_evidence()
        evidence["future_field"] = "unknown"
        with self.assertRaises(DigestError) as raised:
            evidence_record_projection(evidence)
        self.assertEqual(raised.exception.problem.category, "projection_error")
        self.assertEqual(raised.exception.problem.path, ())
        self.assertIn("unknown projection fields", raised.exception.problem.message)

    def test_missing_required_field_keeps_existing_projection_error_contract(self):
        evidence = normalized_evidence()
        del evidence["evidence_id"]
        with self.assertRaises(DigestError) as raised:
            evidence_record_projection(evidence)
        self.assertEqual(raised.exception.problem.category, "projection_error")
        self.assertEqual(raised.exception.problem.path, ())
        self.assertIn("missing required projection fields", raised.exception.problem.message)

    def test_canonical_json_non_string_key_remains_non_json_value(self):
        with self.assertRaises(DigestError) as raised:
            canonical_json_bytes({1: "invalid-key"})
        self.assertEqual(raised.exception.problem.category, "non_json_value")


if __name__ == "__main__":
    unittest.main()
