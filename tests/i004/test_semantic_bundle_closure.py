from __future__ import annotations

import copy
import hashlib
import unittest

from ontotf.digests import canonical_json_bytes, evidence_record_digest
from ontotf.semantic_validation import (
    SemanticArtifact,
    SemanticSourceBundle,
    SemanticValidationError,
    validate_semantic_bundle,
)
from tests.i004.test_semantic_validation_phase1 import base_sources


BRIDGE_CONTENT_FIELDS = (
    "source_lock_id",
    "source_lock_release",
    "source_lock_digest",
    "target_lock_id",
    "target_lock_release",
    "target_lock_digest",
    "assertion_kind",
    "scope",
    "compatibility",
    "evidence_id",
    "evidence_digest",
    "runtime_strength",
    "runtime_limitations",
)


def bridge_digest(bridge: dict) -> str:
    projected = {key: bridge[key] for key in BRIDGE_CONTENT_FIELDS if key in bridge}
    return "sha256:" + hashlib.sha256(canonical_json_bytes(projected)).hexdigest()


def evidence_record() -> dict:
    record = {
        "evidence_id": "evidence:bridge",
        "kind": "ontology-definition",
        "source_uri": "https://example.org/bridge-evidence",
        "source_revision": "reviewed-rev",
        "content_mode": "normalized-record",
        "reviewed_content": {"statement": "reviewed bridge continuity evidence"},
        "content_digest": "placeholder",
    }
    record["content_digest"] = evidence_record_digest(record)
    return record


def lock(lock_id: str, release: str, term: str, digest_char: str) -> dict:
    return {
        "lock_id": lock_id,
        "ontology_id": lock_id.split(":")[-1],
        "support_tier": "core",
        "term_namespace": f"https://example.org/{lock_id}#",
        "release": release,
        "source_uri": f"https://example.org/{lock_id}.ttl",
        "content_digest": "sha256:" + digest_char * 64,
        "license": "CC-BY-4.0",
        "terms_used": [term],
    }


def bundle_sources(with_bridge: bool = False) -> dict:
    sources = base_sources()
    source_lock = lock("lock:old", "1.0", "old:F28", "a")
    target_lock = lock("lock:new", "2.0", "new:F28", "b")
    sources["locks"] = [*sources["locks"], source_lock, target_lock]
    sources["evidences"] = []

    bundle = {
        "schema_version": 1,
        "profile_contracts": ["profile:lexical-v1"],
        "ontology_locks": copy.deepcopy(sources["locks"]),
        "bridge_locks": [],
        "dependency_edges": [],
    }
    bridges: list[dict] = []

    if with_bridge:
        evidence = evidence_record()
        sources["evidences"] = [evidence]
        bridge = {
            "bridge_id": "f28-continuity",
            "source_lock_id": source_lock["lock_id"],
            "source_lock_release": source_lock["release"],
            "source_lock_digest": source_lock["content_digest"],
            "target_lock_id": target_lock["lock_id"],
            "target_lock_release": target_lock["release"],
            "target_lock_digest": target_lock["content_digest"],
            "assertion_kind": "term-continuity",
            "scope": {
                "source_term": "old:F28",
                "target_term": "new:F28",
                "relation": "reviewed-continuity",
            },
            "compatibility": "compatible",
            "evidence_id": evidence["evidence_id"],
            "evidence_digest": evidence["content_digest"],
            "runtime_strength": "exact",
            "runtime_limitations": ["term-scoped"],
            "review_status": "reviewed",
            "review_id": "review:bridge",
            "reviewer_id": "reviewer:test",
            "reviewed_at": "2026-09-08T09:00:00Z",
        }
        bridge["digest"] = bridge_digest(bridge)
        bridge["reviewed_content_digest"] = bridge["digest"]
        bridges.append(bridge)
        bundle["bridge_locks"] = [copy.deepcopy(bridge)]
        bundle["dependency_edges"] = [
            {
                "id": "edge:f28",
                "consumer": target_lock["lock_id"],
                "requires": source_lock["lock_id"],
                "satisfied_by": "bridge:f28-continuity",
                "active": True,
                "required_bridge_scope": copy.deepcopy(bridge["scope"]),
            }
        ]

    sources["ontology_bundle"] = bundle
    sources["bridges"] = bridges
    return sources


def semantic_bundle(sources: dict) -> SemanticSourceBundle:
    return SemanticSourceBundle(
        profile=SemanticArtifact("profile", "profile.json", sources["profile"]),
        expected_parent_manifest=SemanticArtifact("parent-component-manifest", "parent.json", sources["parent"]),
        mappings=SemanticArtifact("mapping", "mappings.json", sources["mappings"]),
        ontology_locks=tuple(
            SemanticArtifact("ontology-lock", f"lock-{i}.json", item)
            for i, item in enumerate(sources["locks"])
        ),
        evidences=tuple(
            SemanticArtifact("evidence", f"evidence-{i}.json", item)
            for i, item in enumerate(sources.get("evidences", []))
        ),
        ontology_bundle=SemanticArtifact("ontology-bundle", "bundle.json", sources["ontology_bundle"]),
        bridges=tuple(
            SemanticArtifact("bridge", f"bridge-{i}.json", item)
            for i, item in enumerate(sources.get("bridges", []))
        ),
    )


class I004BundleClosureTests(unittest.TestCase):
    def assert_problem(self, category: str, sources: dict):
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(semantic_bundle(sources))
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception.problem

    def test_bundle_with_exact_embedded_lock_identities_passes(self):
        result = validate_semantic_bundle(semantic_bundle(bundle_sources()))
        self.assertTrue(result.ontology_bundle_digest.startswith("sha256:"))

    def test_bundle_embedded_lock_release_mismatch_fails_closed(self):
        sources = bundle_sources()
        sources["ontology_bundle"]["ontology_locks"][0]["release"] = "wrong-release"
        self.assert_problem("bundle_closure", sources)

    def test_valid_active_reviewed_bridge_source_closure_passes(self):
        validate_semantic_bundle(semantic_bundle(bundle_sources(with_bridge=True)))

    def test_missing_active_bridge_artifact_fails_closed(self):
        sources = bundle_sources(with_bridge=True)
        sources["bridges"] = []
        self.assert_problem("bridge_closure", sources)

    def test_bridge_review_must_bind_current_content_digest(self):
        sources = bundle_sources(with_bridge=True)
        sources["bridges"][0]["reviewed_content_digest"] = "sha256:" + "d" * 64
        sources["ontology_bundle"]["bridge_locks"][0]["reviewed_content_digest"] = "sha256:" + "d" * 64
        self.assert_problem("bridge_closure", sources)

    def test_bridge_scope_terms_must_belong_to_endpoint_locks(self):
        sources = bundle_sources(with_bridge=True)
        for location in (sources["bridges"][0], sources["ontology_bundle"]["bridge_locks"][0]):
            location["scope"]["source_term"] = "old:F999"
            location["digest"] = bridge_digest(location)
            location["reviewed_content_digest"] = location["digest"]
        sources["ontology_bundle"]["dependency_edges"][0]["required_bridge_scope"]["source_term"] = "old:F999"
        self.assert_problem("bridge_closure", sources)

    def test_inactive_edge_cannot_smuggle_bridge_into_active_bundle(self):
        sources = bundle_sources(with_bridge=True)
        sources["ontology_bundle"]["dependency_edges"][0]["active"] = False
        self.assert_problem("bridge_closure", sources)

    def test_bridge_evidence_must_resolve_to_current_evidence_digest(self):
        sources = bundle_sources(with_bridge=True)
        sources["evidences"] = []
        self.assert_problem("bridge_closure", sources)

    def test_bridge_evidence_digest_mismatch_fails_closed(self):
        sources = bundle_sources(with_bridge=True)
        for location in (sources["bridges"][0], sources["ontology_bundle"]["bridge_locks"][0]):
            location["evidence_digest"] = "sha256:" + "e" * 64
            location["digest"] = bridge_digest(location)
            location["reviewed_content_digest"] = location["digest"]
        self.assert_problem("bridge_closure", sources)

    def test_exact_lock_edge_requires_release_and_digest_binding(self):
        sources = bundle_sources()
        source_lock = sources["locks"][-2]
        target_lock = sources["locks"][-1]
        sources["ontology_bundle"]["dependency_edges"] = [
            {
                "id": "edge:exact",
                "consumer": target_lock["lock_id"],
                "requires": source_lock["lock_id"],
                "satisfied_by": f"lock:{source_lock['lock_id']}",
                "active": True,
            }
        ]
        self.assert_problem("bundle_closure", sources)

    def test_exact_lock_edge_with_current_release_and_digest_passes(self):
        sources = bundle_sources()
        source_lock = sources["locks"][-2]
        target_lock = sources["locks"][-1]
        sources["ontology_bundle"]["dependency_edges"] = [
            {
                "id": "edge:exact",
                "consumer": target_lock["lock_id"],
                "requires": source_lock["lock_id"],
                "satisfied_by": f"lock:{source_lock['lock_id']}",
                "active": True,
                "required_lock_release": source_lock["release"],
                "required_lock_digest": source_lock["content_digest"],
            }
        ]
        validate_semantic_bundle(semantic_bundle(sources))


if __name__ == "__main__":
    unittest.main()
