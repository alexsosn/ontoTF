from __future__ import annotations

import importlib
import importlib.util
import unittest

from tfont.semantic_validation import validate_semantic_bundle


class I009ProductionProvenanceTests(unittest.TestCase):
    def _bundles(self):
        spec = importlib.util.find_spec("tfont.production_bundles")
        self.assertIsNotNone(spec, "I-009 production bundle module is absent")
        module = importlib.import_module("tfont.production_bundles")
        return module, module.load_production_noun_bundles()

    def test_artifact_source_names_are_deterministic_package_relative_paths(self):
        module, bundles = self._bundles()
        for corpus_id, bundle in zip(module.PRODUCTION_NOUN_CORPORA, bundles, strict=True):
            prefix = f"resources/profiles/{corpus_id}/0.1.0"
            with self.subTest(corpus_id=corpus_id):
                self.assertEqual(bundle.profile.source_name, f"{prefix}/profile.json")
                self.assertEqual(
                    bundle.expected_parent_manifest.source_name,
                    f"{prefix}/parent/expected-components.json",
                )
                self.assertEqual(bundle.mappings.source_name, f"{prefix}/mappings/noun.json")
                for artifact in bundle.evidences:
                    self.assertTrue(
                        artifact.source_name.startswith("resources/"),
                        artifact.source_name,
                    )
                for artifact in bundle.ontology_locks:
                    self.assertTrue(
                        artifact.source_name.startswith("resources/ontologies/"),
                        artifact.source_name,
                    )

    def test_mapping_and_projection_reviews_are_real_and_bind_current_semantics(self):
        _, bundles = self._bundles()
        for bundle in bundles:
            validate_semantic_bundle(bundle)
            for mapping in bundle.mappings.data["mappings"]:
                mapping_review = mapping["review"]
                self.assertEqual(mapping_review["status"], "reviewed")
                self.assertEqual(mapping_review["reviewer_id"], "openai:gpt-5.6-sol")
                self.assertTrue(
                    mapping_review["review_source"].startswith("https://github.com/alexsosn/ontoTF/"),
                    mapping_review["review_source"],
                )
                self.assertNotIn("fixture", mapping_review["review_source"].lower())
                for projection in mapping["projections"]:
                    projection_review = projection["review"]
                    self.assertEqual(projection_review["status"], "reviewed")
                    self.assertEqual(projection_review["reviewer_id"], "openai:gpt-5.6-sol")
                    self.assertTrue(
                        projection_review["review_source"].startswith("https://github.com/alexsosn/ontoTF/"),
                        projection_review["review_source"],
                    )

    def test_native_and_olia_evidence_are_bound_to_each_approved_projection(self):
        module, bundles = self._bundles()
        expected_native = {
            "bhsa": {"evidence:bhsa:word-sp-noun-codes"},
            "syriac": {
                "evidence:syriac:word-sp-substantive",
                "evidence:syriac:proper-inside-subs",
            },
            "extrabiblical": {
                "evidence:extrabiblical:word-sp-enum",
                "evidence:extrabiblical:feature-authority",
                "evidence:bhsa:word-sp-noun-codes",
            },
        }
        for corpus_id, bundle in zip(module.PRODUCTION_NOUN_CORPORA, bundles, strict=True):
            mapping = bundle.mappings.data["mappings"][0]
            projection = mapping["projections"][0]
            mapping_ids = {row["evidence_id"] for row in mapping["evidence"]}
            projection_ids = {row["evidence_id"] for row in projection["evidence"]}
            required = expected_native[corpus_id] | {"evidence:olia:noun-hierarchy"}
            with self.subTest(corpus_id=corpus_id):
                self.assertTrue(required <= mapping_ids)
                self.assertTrue(required <= projection_ids)

    def test_semantic_runtime_dependencies_bind_evidence_for_value_meanings(self):
        module, bundles = self._bundles()
        required = {
            "bhsa": {"evidence:bhsa:word-sp-noun-codes"},
            "syriac": {"evidence:syriac:word-sp-substantive"},
            "extrabiblical": {
                "evidence:extrabiblical:word-sp-enum",
                "evidence:extrabiblical:feature-authority",
                "evidence:bhsa:word-sp-noun-codes",
            },
        }
        for corpus_id, bundle in zip(module.PRODUCTION_NOUN_CORPORA, bundles, strict=True):
            for dependency in bundle.profile.data["dependencies"]:
                evidence_ids = {row["evidence_id"] for row in dependency.get("evidence", [])}
                with self.subTest(corpus_id=corpus_id, dependency=dependency["dependency_id"]):
                    self.assertTrue(
                        required[corpus_id] <= evidence_ids,
                        f"semantic dependency lacks meaning evidence: {sorted(required[corpus_id] - evidence_ids)}",
                    )


if __name__ == "__main__":
    unittest.main()
