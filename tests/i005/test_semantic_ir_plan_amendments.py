from __future__ import annotations

import copy
import unittest

import ontotf.semantic_ir as semantic_ir
from ontotf.semantic_digest_v2 import mapping_semantic_digest_v2, projection_semantic_digest_v1
from ontotf.semantic_validation import SemanticArtifact, SemanticSourceBundle, validate_semantic_bundle
from tests.i005._fixtures import (
    catalogue_reference,
    entity_identity_reference,
    noun_sources,
    source_bundle,
    validate_structural_sources,
)


def _refresh_mapping(mapping):
    for projection in mapping.get("projections", []):
        projection["projection_semantic_digest"] = projection_semantic_digest_v1(projection)
        projection["review"]["reviewed_mapping_digest"] = projection["projection_semantic_digest"]
    mapping["mapping_semantic_digest"] = mapping_semantic_digest_v2(mapping)
    mapping["review"]["reviewed_mapping_digest"] = mapping["mapping_semantic_digest"]


def _validated_sources(sources, *, ontology_bundle=None):
    validate_structural_sources(sources)
    base = source_bundle(sources)
    if ontology_bundle is not None:
        base = SemanticSourceBundle(
            profile=base.profile,
            expected_parent_manifest=base.expected_parent_manifest,
            mappings=base.mappings,
            ontology_locks=base.ontology_locks,
            evidences=base.evidences,
            ontology_bundle=SemanticArtifact(
                "ontology-bundle", "ontology-bundle.json", ontology_bundle
            ),
            bridges=base.bridges,
            profile_catalog=base.profile_catalog,
            reference_catalog=base.reference_catalog,
        )
    return validate_semantic_bundle(base)


def _ontology_bundle(sources, *profile_contracts):
    return {
        "schema_version": 1,
        "profile_contracts": list(profile_contracts),
        "ontology_locks": [copy.deepcopy(sources["locks"][0])],
        "bridge_locks": [],
        "dependency_edges": [],
    }


class I005PlanAmendmentContractTests(unittest.TestCase):
    def test_dependency_semantic_drift_is_release_conflict(self):
        first_sources = noun_sources(
            "bhsa", parent_char="a", authored_profile_id="ontotf-bhsa"
        )
        second_sources = noun_sources(
            "bhsa", parent_char="b", authored_profile_id="ontotf-bhsa"
        )
        second_sources["profile"]["dependencies"][0]["assertion"]["value"] = "substantive"

        first = _validated_sources(first_sources)
        second = _validated_sources(second_sources)
        with self.assertRaises(semantic_ir.SemanticIRError) as raised:
            semantic_ir.compile_semantic_ir((first, second))
        self.assertEqual(raised.exception.problem.category, "profile_release_conflict")

    def test_value_domain_order_is_non_semantic_for_release_signature(self):
        first_sources = noun_sources(
            "bhsa", parent_char="a", authored_profile_id="ontotf-bhsa"
        )
        second_sources = noun_sources(
            "bhsa", parent_char="b", authored_profile_id="ontotf-bhsa"
        )
        for sources, values in (
            (first_sources, ["subs", "verb"]),
            (second_sources, ["verb", "subs"]),
        ):
            dependency = sources["profile"]["dependencies"][0]
            dependency["kind"] = "value-domain"
            dependency["assertion"] = {
                "node_type": "word",
                "feature": "sp",
                "values": values,
                "domain_semantics": "observed",
            }

        first = _validated_sources(first_sources)
        second = _validated_sources(second_sources)
        ir = semantic_ir.compile_semantic_ir((second, first))
        self.assertEqual(len(ir.variants), 2)
        self.assertEqual(
            ir.variants[0].release_signature,
            ir.variants[1].release_signature,
        )

    def test_ontology_bundle_digest_drift_is_release_conflict(self):
        first_sources = noun_sources(
            "bhsa", parent_char="a", authored_profile_id="ontotf-bhsa"
        )
        second_sources = noun_sources(
            "bhsa", parent_char="b", authored_profile_id="ontotf-bhsa"
        )
        first = _validated_sources(
            first_sources,
            ontology_bundle=_ontology_bundle(first_sources, "linguistic"),
        )
        second = _validated_sources(
            second_sources,
            ontology_bundle=_ontology_bundle(
                second_sources, "linguistic", "fixture-extra-contract"
            ),
        )
        with self.assertRaises(semantic_ir.SemanticIRError) as raised:
            semantic_ir.compile_semantic_ir((first, second))
        self.assertEqual(raised.exception.problem.category, "profile_release_conflict")

    def test_unused_lock_artifact_does_not_change_ir(self):
        baseline_sources = noun_sources("bhsa", parent_char="a")
        extra_sources = copy.deepcopy(baseline_sources)
        unused = copy.deepcopy(extra_sources["locks"][0])
        unused.update(
            {
                "lock_id": "bhsa-unused-lock",
                "ontology_id": "unused-fixture",
                "term_namespace": "https://example.org/unused/",
                "release": "unused-release",
                "source_uri": "https://example.org/unused.ttl",
                "snapshot_artifact": "fixtures/unused.ttl",
                "content_digest": "sha256:" + "e" * 64,
                "terms_used": ["https://example.org/unused/Thing"],
            }
        )
        extra_sources["locks"].append(unused)

        baseline = _validated_sources(baseline_sources)
        extra = _validated_sources(extra_sources)
        self.assertEqual(
            semantic_ir.compile_semantic_ir((baseline,)),
            semantic_ir.compile_semantic_ir((extra,)),
        )

    def test_referenced_lock_identity_drift_is_release_conflict(self):
        first_sources = noun_sources(
            "bhsa", parent_char="a", authored_profile_id="ontotf-bhsa"
        )
        second_sources = noun_sources(
            "bhsa", parent_char="b", authored_profile_id="ontotf-bhsa"
        )
        second_sources["locks"][0]["release"] = "fixture-release-2"

        first = _validated_sources(first_sources)
        second = _validated_sources(second_sources)
        with self.assertRaises(semantic_ir.SemanticIRError) as raised:
            semantic_ir.compile_semantic_ir((first, second))
        self.assertEqual(raised.exception.problem.category, "profile_release_conflict")

    def test_provisional_mapping_cannot_authorize_identity_or_identifier(self):
        refs = [entity_identity_reference("refs"), catalogue_reference("refs")]
        sources = noun_sources(
            "refs",
            parent_char="a",
            mapping_review_status="provisional",
            external_references=refs,
        )
        ir = semantic_ir.compile_semantic_ir((_validated_sources(sources),))
        self.assertEqual(ir.identity_index, ())
        self.assertEqual(ir.identifier_index, ())

    def test_native_value_present_distinguishes_null_from_absent(self):
        null_sources = noun_sources("null", parent_char="a", native_value=None)
        null_ir = semantic_ir.compile_semantic_ir((_validated_sources(null_sources),))
        null_record = null_ir.native_index[0][1][0]
        self.assertTrue(null_record.native_binding.value_present)
        self.assertIsNone(null_record.native_binding.value)

        absent_sources = noun_sources("absent", parent_char="b")
        mapping = absent_sources["mappings"]["mappings"][0]
        mapping["native_binding"].pop("value")
        mapping["projections"][0]["native_execution_binding"].pop("value")
        dependency = absent_sources["profile"]["dependencies"][0]
        dependency["kind"] = "feature-present"
        dependency["assertion"] = {"node_type": "word", "feature": "sp"}
        _refresh_mapping(mapping)
        absent_ir = semantic_ir.compile_semantic_ir((_validated_sources(absent_sources),))
        absent_record = absent_ir.native_index[0][1][0]
        self.assertFalse(absent_record.native_binding.value_present)
        self.assertIsNone(absent_record.native_binding.value)

    def test_nullable_variant_sort_key_orders_none_before_present(self):
        none_key = semantic_ir.BundleVariantKey("c", "p", "1", "parent", None)
        present_key = semantic_ir.BundleVariantKey(
            "c", "p", "1", "parent", "sha256:" + "f" * 64
        )
        self.assertLess(
            semantic_ir._variant_sort_key(none_key),
            semantic_ir._variant_sort_key(present_key),
        )

    def test_public_key_dataclasses_do_not_expose_python_string_ordering(self):
        left = semantic_ir.SemanticKey("linguistic", "a", "t", "class", "annotation-value")
        right = semantic_ir.SemanticKey("linguistic", "b", "t", "class", "annotation-value")
        with self.assertRaises(TypeError):
            _ = left < right

    def test_mapping_document_order_does_not_change_ir(self):
        first_sources = noun_sources("bhsa", parent_char="a")
        first_mapping = first_sources["mappings"]["mappings"][0]
        second_mapping = copy.deepcopy(first_mapping)
        second_mapping["mapping_id"] = "mapping:bhsa:noun-2"
        second_mapping["review"]["review_id"] = "review:bhsa:mapping:noun-2"
        projection = second_mapping["projections"][0]
        projection["projection_id"] = "projection:bhsa:noun-2"
        projection["review"]["review_id"] = "review:bhsa:projection:noun-2"
        _refresh_mapping(second_mapping)
        first_sources["mappings"]["mappings"].append(second_mapping)

        second_sources = copy.deepcopy(first_sources)
        second_sources["mappings"]["mappings"].reverse()

        first = _validated_sources(first_sources)
        second = _validated_sources(second_sources)
        self.assertEqual(
            semantic_ir.compile_semantic_ir((first,)),
            semantic_ir.compile_semantic_ir((second,)),
        )


if __name__ == "__main__":
    unittest.main()
