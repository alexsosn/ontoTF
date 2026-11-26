from __future__ import annotations

import copy
import unittest

from ontotf.digests import DigestError, profile_semantic_digest


def lock_identity() -> dict:
    return {
        "lock_id": "lock:a",
        "ontology_id": "olia",
        "support_tier": "core",
        "term_namespace": "http://purl.org/olia/olia.owl#",
        "release": "2026-02-04",
        "upstream_release_status": "stable",
        "source_uri": "https://example.org/olia.owl",
        "source_revision": "rev-a",
        "content_digest": "sha256:a",
        "license": "CC-BY-4.0",
        "redistribution_policy": "allowed",
        "terms_used": ["Masculine", "Feminine"],
    }


def profile_projection() -> dict:
    return {
        "profile_id": "tfont-test",
        "schema_version": 1,
        "semantic_contract_version": 1,
        "semantic_domains": ["morphology"],
        "expected_parent_manifest_digest": "sha256:parent",
        "dependencies": [
            {"dependency_id": "dep:a", "component_id": "c", "kind": "feature"},
        ],
        "ontology_locks": [lock_identity()],
        "mappings": [
            {"mapping_id": "map:a", "mapping_semantic_digest": "sha256:ma"},
        ],
        "review_readiness": [
            {"mapping_id": "map:a", "status": "reviewed", "reviewed_digest_matches": True},
        ],
        "applicability": {},
        "publication_semantics": {},
    }


class ProfileProjectionBoundaryTests(unittest.TestCase):
    def assert_projection_error(self, projection: dict) -> None:
        with self.assertRaises(DigestError) as raised:
            profile_semantic_digest(projection)
        self.assertEqual(raised.exception.problem.category, "projection_error")

    def test_under_specified_payload_only_lock_identity_is_rejected(self):
        projection = profile_projection()
        projection["ontology_locks"] = [{"lock_id": "lock:a", "content_digest": "sha256:a"}]
        self.assert_projection_error(projection)

    def test_ontology_lock_audit_timestamp_cannot_enter_semantic_digest(self):
        projection = profile_projection()
        projection["ontology_locks"][0]["retrieved_at"] = "2026-09-06T00:00:00Z"
        self.assert_projection_error(projection)

    def test_ontology_lock_snapshot_locator_cannot_enter_semantic_digest(self):
        projection = profile_projection()
        projection["ontology_locks"][0]["snapshot_artifact"] = "/tmp/local-copy.owl"
        self.assert_projection_error(projection)

    def test_mapping_review_provenance_cannot_enter_profile_semantic_digest(self):
        projection = profile_projection()
        projection["mappings"][0]["review"] = {
            "reviewer_id": "audit-only",
            "reviewed_at": "2026-09-06T00:00:00Z",
        }
        self.assert_projection_error(projection)

    def test_target_pin_semantics_change_profile_digest_even_when_payload_digest_is_same(self):
        base = profile_projection()
        for field, changed_value in (
            ("ontology_id", "olia-other"),
            ("support_tier", "reference"),
            ("term_namespace", "https://example.org/other#"),
            ("release", "2026-03-01"),
            ("source_uri", "https://mirror.example.org/olia.owl"),
            ("source_revision", "rev-b"),
            ("license", "CC0-1.0"),
            ("redistribution_policy", "restricted"),
        ):
            changed = copy.deepcopy(base)
            changed["ontology_locks"][0][field] = changed_value
            self.assertNotEqual(
                profile_semantic_digest(base),
                profile_semantic_digest(changed),
                msg=f"lock semantic field {field!r} did not affect profile digest",
            )

    def test_terms_used_is_set_like_but_semantic(self):
        base = profile_projection()
        reordered = copy.deepcopy(base)
        reordered["ontology_locks"][0]["terms_used"].reverse()
        self.assertEqual(profile_semantic_digest(base), profile_semantic_digest(reordered))

        changed = copy.deepcopy(base)
        changed["ontology_locks"][0]["terms_used"][0] = "Neuter"
        self.assertNotEqual(profile_semantic_digest(base), profile_semantic_digest(changed))

    def test_lock_payload_and_mapping_semantic_identity_changes_still_change_digest(self):
        base = profile_projection()
        changed_lock = copy.deepcopy(base)
        changed_lock["ontology_locks"][0]["content_digest"] = "sha256:changed-lock"
        changed_mapping = copy.deepcopy(base)
        changed_mapping["mappings"][0]["mapping_semantic_digest"] = "sha256:changed-mapping"
        self.assertNotEqual(profile_semantic_digest(base), profile_semantic_digest(changed_lock))
        self.assertNotEqual(profile_semantic_digest(base), profile_semantic_digest(changed_mapping))


if __name__ == "__main__":
    unittest.main()
