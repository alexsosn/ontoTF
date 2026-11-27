from __future__ import annotations

import copy
import unittest

from ontotf.digests import MAPPING_SEMANTIC_ALGORITHM, evidence_record_digest
from ontotf.semantic_digest_v2 import MAPPING_SEMANTIC_ALGORITHM_V2, mapping_semantic_digest_v2
from ontotf.semantic_validation import (
    SemanticArtifact,
    SemanticSourceBundle,
    SemanticValidationError,
    validate_semantic_bundle,
)
from tests.i004.test_semantic_validation_phase1 import base_sources


def reviewed_sources() -> dict:
    sources = base_sources()
    evidence = {
        "evidence_id": "evidence:noun",
        "kind": "ontology-definition",
        "source_uri": "https://example.org/olia/noun",
        "source_revision": "test-rev",
        "content_mode": "normalized-record",
        "reviewed_content": {"term": "Noun", "definition": "noun category"},
        "content_digest": "placeholder",
    }
    evidence["content_digest"] = evidence_record_digest(evidence)
    sources["evidences"] = [evidence]

    mapping = sources["mappings"]["mappings"][0]
    binding = {
        "evidence_id": evidence["evidence_id"],
        "content_digest": evidence["content_digest"],
    }
    mapping["evidence"] = [copy.deepcopy(binding)]
    mapping["projections"][0]["evidence"] = [copy.deepcopy(binding)]
    mapping["review"] = {
        "review_id": "review:mapping:noun",
        "status": "reviewed",
        "reviewed_mapping_digest": "placeholder",
        "reviewer_id": "reviewer:test",
        "reviewed_at": "2026-09-08T00:00:00Z",
        "review_source": "test",
        "review_method": "independent-adversarial",
        "notes": ["audit metadata"],
        "evidence": [evidence["evidence_id"]],
    }
    mapping["mapping_semantic_digest"] = mapping_semantic_digest_v2(mapping)
    mapping["review"]["reviewed_mapping_digest"] = mapping["mapping_semantic_digest"]
    return sources


def bundle(sources: dict) -> SemanticSourceBundle:
    return SemanticSourceBundle(
        profile=SemanticArtifact("profile", "profile.json", sources["profile"]),
        expected_parent_manifest=SemanticArtifact("parent-component-manifest", "parent.json", sources["parent"]),
        mappings=SemanticArtifact("mapping", "mappings.json", sources["mappings"]),
        ontology_locks=tuple(
            SemanticArtifact("ontology-lock", f"lock-{i}.json", lock)
            for i, lock in enumerate(sources["locks"])
        ),
        evidences=tuple(
            SemanticArtifact("evidence", f"evidence-{i}.json", evidence)
            for i, evidence in enumerate(sources.get("evidences", []))
        ),
    )


class I004Phase3Tests(unittest.TestCase):
    def assert_problem(self, category: str, sources: dict):
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(bundle(sources))
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception.problem

    def test_valid_reviewed_mapping_v2_passes_and_reports_digest(self):
        sources = reviewed_sources()
        result = validate_semantic_bundle(bundle(sources))
        self.assertEqual(
            dict(result.mapping_semantic_digests)["mapping:noun"],
            sources["mappings"]["mappings"][0]["mapping_semantic_digest"],
        )

    def test_missing_evidence_reference_fails(self):
        sources = reviewed_sources()
        sources["mappings"]["mappings"][0]["evidence"][0]["evidence_id"] = "evidence:missing"
        self.assert_problem("missing_reference", sources)

    def test_evidence_digest_mismatch_fails(self):
        sources = reviewed_sources()
        sources["mappings"]["mappings"][0]["projections"][0]["evidence"][0]["content_digest"] = "sha256:stale"
        self.assert_problem("evidence_digest_mismatch", sources)

    def test_stale_mapping_semantic_digest_fails(self):
        sources = reviewed_sources()
        sources["mappings"]["mappings"][0]["native_binding"]["node_type"] = "phrase"
        self.assert_problem("stale_semantic_digest", sources)

    def test_stale_reviewed_mapping_digest_fails(self):
        sources = reviewed_sources()
        mapping = sources["mappings"]["mappings"][0]
        mapping["review"]["reviewed_mapping_digest"] = "sha256:old-review-target"
        self.assert_problem("stale_review_binding", sources)

    def test_audit_only_review_edit_does_not_change_mapping_v2_digest(self):
        sources = reviewed_sources()
        mapping = sources["mappings"]["mappings"][0]
        before = mapping_semantic_digest_v2(mapping)
        mapping["review"]["reviewed_at"] = "2026-09-09T00:00:00Z"
        mapping["review"]["reviewer_id"] = "reviewer:other"
        mapping["review"]["notes"] = ["different audit note"]
        self.assertEqual(mapping_semantic_digest_v2(mapping), before)

    def test_semantic_projection_edit_changes_mapping_v2_digest(self):
        sources = reviewed_sources()
        mapping = sources["mappings"]["mappings"][0]
        before = mapping_semantic_digest_v2(mapping)
        mapping["projections"][0]["assessment"] = "close"
        self.assertNotEqual(mapping_semantic_digest_v2(mapping), before)

    def test_v2_algorithm_is_distinct_from_v1(self):
        self.assertEqual(MAPPING_SEMANTIC_ALGORITHM, "tfont-mapping-semantic-sha256-v1")
        self.assertEqual(MAPPING_SEMANTIC_ALGORITHM_V2, "tfont-mapping-semantic-sha256-v2")


if __name__ == "__main__":
    unittest.main()
