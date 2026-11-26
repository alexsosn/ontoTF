from __future__ import annotations

import importlib
import unittest


FORMAL_KINDS = {"class", "property", "skos-concept", "named-resource"}
SEMANTIC_ROLES = {
    "entity-type",
    "annotation-category",
    "annotation-value",
    "relation",
    "attribute",
    "lexical-entry-identity",
    "lexical-form-identity",
    "lexical-sense-identity",
    "lexical-concept-identity",
    "authority-reference",
    "claim-proposition",
    "inference-activity",
}


def minimal_v2_sources() -> dict:
    dependency = {
        "dependency_id": "dep:word-sp",
        "component_id": "test-tf",
        "kind": "native-value-present",
        "assertion": {
            "node_type": "word",
            "feature": "sp",
            "value": "subs",
            "value_semantics": "semantic",
        },
    }
    projection = {
        "projection_id": "projection:noun",
        "target": "http://purl.org/olia/olia.owl#Noun",
        "reference_kind": "semantic-pivot",
        "query_role": "semantic-constraint",
        "formal_kind": "class",
        "semantic_role": "annotation-value",
        "profile_id": "linguistic",
        "capability_id": "linguistic.part-of-speech",
        "assessment": "exact",
        "ontology_lock": "olia-test",
        "native_execution_binding": {
            "component_id": "test-tf",
            "node_type": "word",
            "feature": "sp",
            "value": "subs",
        },
        "evidence": [
            {"evidence_id": "evidence:noun", "content_digest": "sha256:evidence-noun"}
        ],
        "review": {
            "review_id": "review:projection-noun",
            "status": "reviewed",
            "reviewed_semantic_digest": "sha256:projection-noun",
            "reviewer_id": "reviewer:test",
            "reviewed_at": "2026-09-08T07:00:00Z",
            "review_source": "offline:test",
            "review_method": "independent-skeptical",
        },
        "projection_semantic_digest": "sha256:projection-noun",
    }
    mapping = {
        "mapping_id": "mapping:noun",
        "corpus_id": "test-corpus",
        "native_binding": {
            "component_id": "test-tf",
            "node_type": "word",
            "feature": "sp",
            "value": "subs",
        },
        "native_dependencies": ["dep:word-sp"],
        "profiles": ["linguistic"],
        "capabilities": ["linguistic.part-of-speech"],
        "native_state": "positive",
        "projections": [projection],
        "ambiguous_candidates": [],
        "external_references": [],
        "evidence": [],
        "review": {
            "review_id": "review:mapping-noun",
            "status": "reviewed",
            "reviewed_semantic_digest": "sha256:mapping-noun",
            "reviewer_id": "reviewer:test",
            "reviewed_at": "2026-09-08T07:00:00Z",
            "review_source": "offline:test",
            "review_method": "independent-skeptical",
        },
        "mapping_semantic_digest": "sha256:mapping-noun",
        "rationale": "RED fixture",
    }
    return {
        "profile": {
            "schema_version": 2,
            "profile_id": "test-profile",
            "profile_version": "0.3.0",
            "semantic_domains": ["linguistic"],
            "parent_component_manifest": "parent/expected-components.json",
            "required_components": ["test-tf"],
            "ontology_locks": ["olia-test"],
            "mapping_sources": ["mappings/test.yaml"],
            "dependency_contract_version": 1,
            "dependencies": [dependency],
            "minimum_ontotf_runtime": "0.1.0",
            "license": "CC-BY-4.0",
        },
        "expected_parent_manifest": {
            "algorithm": "ontotf-parent-components-sha256-v1",
            "components": [
                {
                    "component_id": "test-tf",
                    "kind": "tf-payload",
                    "identity_algorithm": "ontotf-tf-files-sha256-v1",
                    "content_digest": "sha256:test-parent",
                }
            ],
        },
        "mappings": {"schema_version": 2, "mappings": [mapping]},
        "ontology_locks": [
            {
                "lock_id": "olia-test",
                "ontology_id": "olia",
                "support_tier": "core",
                "term_namespace": "http://purl.org/olia/olia.owl#",
                "release": "test-release",
                "source_uri": "https://example.org/olia.ttl",
                "content_digest": "sha256:ontology",
                "license": "CC-BY-4.0",
                "snapshot_artifact": "ontology/olia.ttl",
                "terms_used": ["http://purl.org/olia/olia.owl#Noun"],
            }
        ],
        "evidences": [
            {
                "evidence_id": "evidence:noun",
                "kind": "native-doc",
                "source_uri": "https://example.org/native-doc",
                "content_mode": "external-payload",
                "content_digest": "sha256:evidence-noun",
            }
        ],
    }


class I004RedContractTests(unittest.TestCase):
    def test_fixture_uses_p003_typed_projection_not_v1_external_target(self):
        sources = minimal_v2_sources()
        mapping = sources["mappings"]["mappings"][0]
        projection = mapping["projections"][0]

        self.assertNotIn("external_target", mapping)
        self.assertNotIn("assessment", mapping)
        self.assertEqual(mapping["native_state"], "positive")
        self.assertIn(projection["formal_kind"], FORMAL_KINDS)
        self.assertIn(projection["semantic_role"], SEMANTIC_ROLES)
        self.assertEqual(
            (projection["reference_kind"], projection["query_role"]),
            ("semantic-pivot", "semantic-constraint"),
        )

    def test_fixture_native_binding_is_tf_native(self):
        sources = minimal_v2_sources()
        mapping = sources["mappings"]["mappings"][0]
        serialized = repr(mapping["native_binding"])
        for forbidden in ("sidecar", "external_record", "database", "api_url", "file_path"):
            self.assertNotIn(forbidden, serialized)

    def test_production_semantic_validation_api_exists(self):
        module = importlib.import_module("ontotf.semantic_validation")
        for name in (
            "SemanticArtifact",
            "SemanticSourceBundle",
            "SemanticValidationProblem",
            "SemanticValidationError",
            "ValidatedSemanticBundle",
            "validate_semantic_bundle",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(module, name), name)


if __name__ == "__main__":
    unittest.main()
