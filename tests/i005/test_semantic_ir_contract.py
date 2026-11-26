from __future__ import annotations

import importlib
import unittest

from tests.i005._fixtures import (
    AUTHORITY_NOUN,
    OLIA_NOUN,
    catalogue_reference,
    entity_identity_reference,
    locator_reference,
    provenance_reference,
    validated_noun_bundle,
)


def semantic_ir_module():
    return importlib.import_module("ontotf.semantic_ir")


def problem_category(error: Exception) -> str:
    problem = getattr(error, "problem", None)
    return getattr(problem, "category", "")


class I005SemanticIRContractTests(unittest.TestCase):
    def test_public_compiler_module_exists(self):
        module = semantic_ir_module()
        self.assertTrue(callable(module.compile_semantic_ir))
        self.assertEqual(
            module.NATIVE_BINDING_IDENTITY_ALGORITHM,
            "ontotf-native-binding-jcs-sha256-v1",
        )

    def test_three_exact_noun_bundles_share_one_semantic_key(self):
        module = semantic_ir_module()
        bundles = (
            validated_noun_bundle("bhsa", parent_char="a"),
            validated_noun_bundle("syriac", parent_char="b"),
            validated_noun_bundle("extrabiblical", parent_char="c"),
        )
        ir = module.compile_semantic_ir(bundles)
        key = module.SemanticKey(
            profile_id="linguistic",
            capability_id="linguistic.part-of-speech",
            target=OLIA_NOUN,
            formal_kind="class",
            semantic_role="annotation-value",
        )
        rows = dict(ir.semantic_index)[key]
        self.assertEqual(
            [row.corpus_id for row in rows],
            ["bhsa", "extrabiblical", "syriac"],
        )
        self.assertTrue(all(row.assessment == "exact" for row in rows))
        self.assertTrue(all(row.native_execution_binding.node_type == "word" for row in rows))
        self.assertTrue(all(row.native_execution_binding.feature == "sp" for row in rows))
        self.assertTrue(all(row.native_execution_binding.value == "subs" for row in rows))
        self.assertTrue(all(row.ontology_lock.ontology_id == "olia" for row in rows))
        self.assertTrue(all(row.mapping_review.status == "reviewed" for row in rows))
        self.assertTrue(all(row.projection_review.status == "reviewed" for row in rows))
        self.assertTrue(all(len(row.mapping_evidence) == 1 for row in rows))
        self.assertTrue(all(len(row.projection_evidence) == 1 for row in rows))

    def test_compilation_is_deterministic_under_bundle_reversal(self):
        module = semantic_ir_module()
        bundles = [
            validated_noun_bundle("bhsa", parent_char="a"),
            validated_noun_bundle("syriac", parent_char="b"),
            validated_noun_bundle("extrabiblical", parent_char="c"),
        ]
        first = module.compile_semantic_ir(bundles)
        second = module.compile_semantic_ir(reversed(bundles))
        self.assertEqual(first, second)

    def test_utf16_order_not_python_codepoint_order(self):
        module = semantic_ir_module()
        supplementary = "\U00010000-corpus"
        bmp = "\ue000-corpus"
        ir = module.compile_semantic_ir(
            (
                validated_noun_bundle(bmp, parent_char="b"),
                validated_noun_bundle(supplementary, parent_char="a"),
            )
        )
        key = next(key for key, _ in ir.semantic_index)
        rows = dict(ir.semantic_index)[key]
        self.assertEqual([row.corpus_id for row in rows], [supplementary, bmp])

    def test_native_binding_identity_is_jcs_stable_and_null_sensitive(self):
        module = semantic_ir_module()
        first = {"node_type": "word", "feature": "sp", "value": "subs"}
        reordered = {"value": "subs", "feature": "sp", "node_type": "word"}
        self.assertEqual(
            module.native_binding_identity(first),
            module.native_binding_identity(reordered),
        )
        self.assertNotEqual(
            module.native_binding_identity({"node_type": "word", "feature": "sp"}),
            module.native_binding_identity(
                {"node_type": "word", "feature": "sp", "value": None}
            ),
        )

    def test_two_parent_variants_of_one_release_are_legal(self):
        module = semantic_ir_module()
        first = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            authored_profile_id="ontotf-bhsa",
            profile_version="0.1.0",
        )
        second = validated_noun_bundle(
            "bhsa",
            parent_char="d",
            authored_profile_id="ontotf-bhsa",
            profile_version="0.1.0",
        )
        ir = module.compile_semantic_ir((second, first))
        self.assertEqual(len(ir.variants), 2)
        key = next(key for key, _ in ir.semantic_index)
        rows = dict(ir.semantic_index)[key]
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(
            rows[0].variant.expected_parent_manifest_digest,
            rows[1].variant.expected_parent_manifest_digest,
        )

    def test_duplicate_exact_variant_fails_closed(self):
        module = semantic_ir_module()
        bundle = validated_noun_bundle("bhsa", parent_char="a")
        with self.assertRaises(module.SemanticIRError) as raised:
            module.compile_semantic_ir((bundle, bundle))
        self.assertEqual(problem_category(raised.exception), "duplicate_bundle_variant")

    def test_mapping_review_authority_is_release_coherent(self):
        module = semantic_ir_module()
        reviewed = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            authored_profile_id="ontotf-bhsa",
            mapping_review_status="reviewed",
        )
        provisional = validated_noun_bundle(
            "bhsa",
            parent_char="b",
            authored_profile_id="ontotf-bhsa",
            mapping_review_status="provisional",
        )
        with self.assertRaises(module.SemanticIRError) as raised:
            module.compile_semantic_ir((reviewed, provisional))
        self.assertEqual(problem_category(raised.exception), "profile_release_conflict")

    def test_projection_review_authority_is_release_coherent(self):
        module = semantic_ir_module()
        reviewed = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            authored_profile_id="ontotf-bhsa",
            projection_review_status="reviewed",
        )
        provisional = validated_noun_bundle(
            "bhsa",
            parent_char="b",
            authored_profile_id="ontotf-bhsa",
            projection_review_status="provisional",
        )
        with self.assertRaises(module.SemanticIRError) as raised:
            module.compile_semantic_ir((reviewed, provisional))
        self.assertEqual(problem_category(raised.exception), "profile_release_conflict")

    def test_review_id_change_is_release_conflict(self):
        module = semantic_ir_module()
        first = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            authored_profile_id="ontotf-bhsa",
            mapping_review_id="review:bhsa:mapping:noun:v1",
        )
        second = validated_noun_bundle(
            "bhsa",
            parent_char="b",
            authored_profile_id="ontotf-bhsa",
            mapping_review_id="review:bhsa:mapping:noun:v2",
        )
        with self.assertRaises(module.SemanticIRError) as raised:
            module.compile_semantic_ir((first, second))
        self.assertEqual(problem_category(raised.exception), "profile_release_conflict")

    def test_audit_only_review_edits_do_not_conflict(self):
        module = semantic_ir_module()
        first = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            authored_profile_id="ontotf-bhsa",
            audit_suffix="-a",
        )
        second = validated_noun_bundle(
            "bhsa",
            parent_char="b",
            authored_profile_id="ontotf-bhsa",
            audit_suffix="-b",
        )
        ir = module.compile_semantic_ir((first, second))
        self.assertEqual(len(ir.variants), 2)

    def test_semantic_change_under_same_release_is_conflict(self):
        module = semantic_ir_module()
        first = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            authored_profile_id="ontotf-bhsa",
            native_value="subs",
        )
        second = validated_noun_bundle(
            "bhsa",
            parent_char="b",
            authored_profile_id="ontotf-bhsa",
            native_value="substantive",
        )
        with self.assertRaises(module.SemanticIRError) as raised:
            module.compile_semantic_ir((first, second))
        self.assertEqual(problem_category(raised.exception), "profile_release_conflict")

    def test_semantic_change_under_new_profile_version_is_legal(self):
        module = semantic_ir_module()
        first = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            authored_profile_id="ontotf-bhsa",
            profile_version="0.1.0",
            native_value="subs",
        )
        second = validated_noun_bundle(
            "bhsa",
            parent_char="b",
            authored_profile_id="ontotf-bhsa",
            profile_version="0.2.0",
            native_value="substantive",
        )
        ir = module.compile_semantic_ir((first, second))
        self.assertEqual(len(ir.variants), 2)

    def test_provisional_mapping_is_not_authoritative(self):
        module = semantic_ir_module()
        bundle = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            mapping_review_status="provisional",
        )
        ir = module.compile_semantic_ir((bundle,))
        self.assertEqual(ir.semantic_index, ())
        self.assertEqual(ir.authority_index, ())
        facts = [facts for _, facts in ir.capability_facts]
        self.assertTrue(all(fact.reviewed_native_support == 0 for fact in facts))

    def test_provisional_projection_does_not_enter_target_index(self):
        module = semantic_ir_module()
        bundle = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            projection_review_status="provisional",
        )
        ir = module.compile_semantic_ir((bundle,))
        self.assertEqual(ir.semantic_index, ())
        facts = [facts for _, facts in ir.capability_facts]
        self.assertEqual(facts[0].reviewed_native_support, 1)
        self.assertEqual(facts[0].shared_projections, 0)

    def test_native_only_and_ambiguous_support_without_reverse_target(self):
        module = semantic_ir_module()
        native_only = module.compile_semantic_ir(
            (validated_noun_bundle("native-only", parent_char="a", native_state="native-only"),)
        )
        ambiguous = module.compile_semantic_ir(
            (validated_noun_bundle("ambiguous", parent_char="b", native_state="ambiguous"),)
        )
        self.assertEqual(native_only.semantic_index, ())
        self.assertEqual(ambiguous.semantic_index, ())
        self.assertEqual(next(iter(native_only.capability_facts))[1].native_only, 1)
        self.assertEqual(next(iter(ambiguous.capability_facts))[1].ambiguous, 1)
        self.assertEqual(next(iter(native_only.capability_facts))[1].reviewed_native_support, 1)
        self.assertEqual(next(iter(ambiguous.capability_facts))[1].reviewed_native_support, 1)

    def test_unsupported_is_negative_knowledge_only(self):
        module = semantic_ir_module()
        ir = module.compile_semantic_ir(
            (validated_noun_bundle("unsupported", parent_char="a", native_state="unsupported"),)
        )
        self.assertEqual(ir.semantic_index, ())
        facts = next(iter(ir.capability_facts))[1]
        self.assertEqual(facts.unsupported, 1)
        self.assertEqual(facts.reviewed_native_support, 0)

    def test_authority_value_routes_only_to_authority_index(self):
        module = semantic_ir_module()
        ir = module.compile_semantic_ir(
            (validated_noun_bundle("authority", parent_char="a", projection_route="authority"),)
        )
        self.assertEqual(ir.semantic_index, ())
        self.assertEqual(len(ir.authority_index), 1)
        key, rows = ir.authority_index[0]
        self.assertEqual(key.authority_system, "authority-test")
        self.assertEqual(key.authority_resource, AUTHORITY_NOUN)
        self.assertEqual(rows[0].reference_kind, "authority-value")

    def test_identity_and_catalogue_indexes_are_separate(self):
        module = semantic_ir_module()
        refs = [
            entity_identity_reference("refs"),
            catalogue_reference("refs"),
            provenance_reference("refs"),
            locator_reference("refs"),
        ]
        ir = module.compile_semantic_ir(
            (validated_noun_bundle("refs", parent_char="a", external_references=refs),)
        )
        self.assertEqual(len(ir.identity_index), 1)
        self.assertEqual(len(ir.identifier_index), 1)
        self.assertEqual(len(ir.semantic_index), 1)
        reference_ids = {
            reference.reference_id
            for _, rows in ir.native_index
            for native in rows
            for reference in getattr(native, "external_references", ())
        }
        self.assertIn("reference:refs:source", reference_ids)
        self.assertIn("reference:refs:locator", reference_ids)

    def test_non_validated_input_is_type_error(self):
        module = semantic_ir_module()
        with self.assertRaises(TypeError):
            module.compile_semantic_ir(({},))


if __name__ == "__main__":
    unittest.main()
