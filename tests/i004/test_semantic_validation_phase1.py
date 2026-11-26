from __future__ import annotations

import copy
import unittest

from ontotf.semantic_validation import (
    SemanticArtifact,
    SemanticSourceBundle,
    SemanticValidationError,
    validate_semantic_bundle,
)


def base_sources() -> dict:
    dep = {
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
        "evidence": [],
        "review": {},
        "projection_semantic_digest": "sha256:placeholder",
    }
    mapping = {
        "mapping_id": "mapping:noun",
        "corpus_id": "test-corpus",
        "native_binding": {"component_id": "test-tf", "node_type": "word"},
        "native_dependencies": ["dep:word-sp"],
        "profiles": ["linguistic"],
        "capabilities": ["linguistic.part-of-speech"],
        "native_state": "positive",
        "projections": [projection],
        "ambiguous_candidates": [],
        "external_references": [],
        "evidence": [],
        "review": {},
        "mapping_semantic_digest": "sha256:placeholder",
        "rationale": "phase-1 fixture",
    }
    return {
        "profile": {
            "schema_version": 2,
            "profile_id": "test-profile",
            "profile_version": "0.3.0",
            "semantic_domains": ["linguistic"],
            "profile_catalog_version": 1,
            "profiles": ["linguistic"],
            "capabilities": ["linguistic.part-of-speech"],
            "parent_component_manifest": "parent/expected-components.json",
            "required_components": ["test-tf"],
            "ontology_locks": ["olia-test"],
            "mapping_sources": ["mappings/test.yaml"],
            "dependency_contract_version": 1,
            "dependencies": [dep],
            "minimum_tfont_runtime": "0.1.0",
            "license": "CC-BY-4.0",
        },
        "parent": {
            "algorithm": "tfont-parent-components-sha256-v1",
            "components": [
                {
                    "component_id": "test-tf",
                    "kind": "tf-payload",
                    "identity_algorithm": "tfont-tf-files-sha256-v1",
                    "content_digest": "sha256:test-parent",
                }
            ],
        },
        "mappings": {"schema_version": 2, "mappings": [mapping]},
        "locks": [
            {
                "lock_id": "olia-test",
                "ontology_id": "olia",
                "support_tier": "core",
                "term_namespace": "http://purl.org/olia/olia.owl#",
                "release": "test-release",
                "source_uri": "https://example.org/olia.ttl",
                "content_digest": "sha256:ontology",
                "license": "CC-BY-4.0",
                "terms_used": ["http://purl.org/olia/olia.owl#Noun"],
            }
        ],
    }


def bundle(sources: dict) -> SemanticSourceBundle:
    return SemanticSourceBundle(
        profile=SemanticArtifact("profile", "profile.json", sources["profile"]),
        expected_parent_manifest=SemanticArtifact("parent-component-manifest", "parent.json", sources["parent"]),
        mappings=SemanticArtifact("mapping", "mappings.json", sources["mappings"]),
        ontology_locks=tuple(
            SemanticArtifact("ontology-lock", f"lock-{i}.json", lock)
            for i, lock in enumerate(sources["locks"])
        ),
    )


class I004Phase1Tests(unittest.TestCase):
    def assert_problem(self, category: str, sources: dict):
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(bundle(sources))
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception.problem

    def test_valid_bundle_builds_core_indexes(self):
        result = validate_semantic_bundle(bundle(base_sources()))
        self.assertEqual(dict(result.indexes.components).keys(), {"test-tf"})
        self.assertEqual(dict(result.indexes.dependencies).keys(), {"dep:word-sp"})
        self.assertEqual(dict(result.indexes.mappings).keys(), {"mapping:noun"})
        self.assertEqual(dict(result.indexes.projections).keys(), {"projection:noun"})
        self.assertEqual(dict(result.indexes.ontology_locks).keys(), {"olia-test"})

    def test_duplicate_mapping_id_fails_before_other_semantics(self):
        sources = base_sources()
        duplicate = copy.deepcopy(sources["mappings"]["mappings"][0])
        duplicate["native_dependencies"] = ["missing-dependency"]
        sources["mappings"]["mappings"].append(duplicate)
        problem = self.assert_problem("duplicate_id", sources)
        self.assertEqual(problem.related_id, "mapping:noun")

    def test_required_component_missing_from_parent_fails(self):
        sources = base_sources()
        sources["profile"]["required_components"] = ["missing-tf"]
        self.assert_problem("component_authority", sources)

    def test_dependency_component_must_be_required(self):
        sources = base_sources()
        sources["profile"]["dependencies"][0]["component_id"] = "other-tf"
        self.assert_problem("component_authority", sources)

    def test_mapping_dependency_must_resolve(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["native_dependencies"] = ["dep:missing"]
        self.assert_problem("missing_reference", sources)

    def test_unknown_formal_kind_fails_closed(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["projections"][0]["formal_kind"] = "owl-class"
        self.assert_problem("unknown_vocabulary", sources)

    def test_target_routing_pair_is_closed(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["projections"][0]["query_role"] = "authority-value-filter"
        self.assert_problem("invalid_reference_routing", sources)

    def test_unknown_profile_capability_alias_fails(self):
        sources = base_sources()
        sources["mappings"]["mappings"][0]["profiles"] = ["Linguistic"]
        self.assert_problem("unknown_vocabulary", sources)


if __name__ == "__main__":
    unittest.main()
