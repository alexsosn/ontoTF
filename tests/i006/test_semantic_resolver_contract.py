from __future__ import annotations

import importlib
import re
import unittest
from dataclasses import replace
from unittest import mock

from tests.i005._fixtures import AUTHORITY_NOUN, validated_noun_bundle, noun_sources, source_bundle, validate_structural_sources
from tests.i006._fixtures import (
    OLIA_NOUN,
    TEST_SOURCE_CONTRACT,
    compiled_noun_ir,
    noun_semantic_key,
    validated_assessment_bundle,
    validated_binding_presence_bundle,
    validated_two_binding_bundle,
    with_bundle_digest,
)
from tfont.semantic_ir import SemanticKey, compile_semantic_ir, native_binding_identity
from tfont.semantic_validation import validate_semantic_bundle


try:
    RESOLVER = importlib.import_module("tfont.semantic_resolver")
except ModuleNotFoundError as exc:
    if exc.name != "tfont.semantic_resolver":
        raise
    RESOLVER = None


SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def problem_category(error: BaseException) -> str:
    problem = getattr(error, "problem", None)
    return getattr(problem, "category", "")


def variant_for(ir, corpus_id: str):
    return next(variant for variant in ir.variants if variant.key.corpus_id == corpus_id)


def prerequisite_for(
    module,
    variant_ir,
    *,
    parent_state: str = "verified-exact",
    observed_parent: str | None = None,
    dependency_result: str = "pass",
    source_contract: str = TEST_SOURCE_CONTRACT,
):
    if observed_parent is None:
        observed_parent = variant_ir.key.expected_parent_manifest_digest
    dependencies = tuple(
        module.DependencyPrerequisiteResult(
            dependency_id=dependency_id,
            result=dependency_result,
            observed_evidence_digest=None,
            evaluator_rule_version="test-rule-v1",
        )
        for dependency_id, _record in variant_ir.release_signature.dependency_records
    )
    bundle_digest = variant_ir.key.ontology_bundle_digest
    return module.RuntimePrerequisiteState(
        variant=variant_ir.key,
        profile_release_fingerprint=module.profile_release_fingerprint(
            variant_ir.release_signature
        ),
        observed_parent_manifest_digest=observed_parent,
        parent_state=parent_state,
        dependency_results=dependencies,
        active_ontology_bundle_digest=bundle_digest,
        ontology_bundle_state="verified" if bundle_digest is not None else "not-required",
        source_contract=source_contract,
    )


def prerequisites_for(module, ir, **kwargs):
    return tuple(prerequisite_for(module, variant, **kwargs) for variant in ir.variants)


def request_for(module, corpora, *, key=None, semantic_mode="exact"):
    return module.SemanticResolveRequest(
        key=key or noun_semantic_key(),
        corpora=tuple(corpora),
        semantic_mode=semantic_mode,
    )


def assert_problem(testcase: unittest.TestCase, category: str, callable_, *args, **kwargs):
    with testcase.assertRaises(RESOLVER.SemanticResolutionError) as raised:
        callable_(*args, **kwargs)
    testcase.assertEqual(problem_category(raised.exception), category)
    return raised.exception


class I006RedSentinelTests(unittest.TestCase):
    def test_public_resolver_module_exists(self):
        self.assertIsNotNone(
            RESOLVER,
            "RED: tfont.semantic_resolver must not exist before the implementation gate",
        )


@unittest.skipUnless(RESOLVER is not None, "RED sentinel owns absence attribution")
class I006SemanticResolverContractTests(unittest.TestCase):
    def setUp(self):
        self.module = RESOLVER
        self.ir = compiled_noun_ir()
        self.prerequisites = prerequisites_for(self.module, self.ir)

    def resolve(self, corpora=("bhsa",), *, ir=None, prerequisites=None, key=None, mode="exact"):
        selected_ir = self.ir if ir is None else ir
        selected_prerequisites = self.prerequisites if prerequisites is None else prerequisites
        return self.module.semantic_resolve(
            selected_ir,
            request_for(self.module, corpora, key=key, semantic_mode=mode),
            selected_prerequisites,
        )

    def compatible_ir(self):
        sources = noun_sources("bhsa", parent_char="a")
        sources["profile"]["parent_compatibility"] = "dependency-verified"
        validate_structural_sources(sources)
        return compile_semantic_ir((validate_semantic_bundle(source_bundle(sources)),))

    # Public and happy-path contract.
    def test_public_constants_are_versioned(self):
        self.assertEqual(self.module.EXACT_RESOLVER_CONTRACT, "tfont-exact-semantic-resolver-v1")
        self.assertEqual(
            self.module.PROFILE_RELEASE_FINGERPRINT_ALGORITHM,
            "tfont-profile-release-signature-jcs-sha256-v1",
        )
        self.assertEqual(
            self.module.RUNTIME_PREREQUISITE_FINGERPRINT_ALGORITHM,
            "tfont-runtime-prerequisite-jcs-sha256-v1",
        )
        self.assertEqual(
            self.module.EXACT_PLAN_FINGERPRINT_ALGORITHM,
            "tfont-exact-native-plan-jcs-sha256-v1",
        )
        self.assertEqual(
            self.module.EXACT_RESOLUTION_FINGERPRINT_ALGORITHM,
            "tfont-exact-resolution-jcs-sha256-v1",
        )

    def test_bhsa_noun_resolves_to_typed_native_plan(self):
        result = self.resolve(("bhsa",))
        self.assertEqual(len(result.plans), 1)
        plan = result.plans[0]
        self.assertEqual(plan.corpus_id, "bhsa")
        self.assertEqual(plan.semantic_key, noun_semantic_key())
        self.assertEqual(plan.reference_kind, "semantic-pivot")
        self.assertEqual(plan.query_role, "semantic-constraint")
        self.assertEqual(plan.semantic_mode, "exact")
        self.assertEqual(plan.capability_state, "active")
        self.assertEqual(plan.assessment, "exact")
        self.assertEqual(plan.native_execution_binding.node_type, "word")
        self.assertEqual(plan.native_execution_binding.feature, "sp")
        self.assertEqual(plan.native_execution_binding.value, "subs")
        self.assertEqual(plan.prerequisite_source_contract, TEST_SOURCE_CONTRACT)
        self.assertTrue(SHA256_RE.fullmatch(plan.plan_fingerprint))
        self.assertFalse(hasattr(plan, "query"))
        self.assertFalse(hasattr(plan, "cf_query"))

    def test_syriac_noun_resolves(self):
        self.assertEqual(self.resolve(("syriac",)).plans[0].corpus_id, "syriac")

    def test_extrabiblical_noun_resolves(self):
        self.assertEqual(
            self.resolve(("extrabiblical",)).plans[0].corpus_id,
            "extrabiblical",
        )

    def test_three_corpus_result_is_canonical_and_exactly_comparable(self):
        result = self.resolve(("syriac", "bhsa", "extrabiblical"))
        self.assertEqual(
            [plan.corpus_id for plan in result.plans],
            ["bhsa", "extrabiblical", "syriac"],
        )
        self.assertEqual(result.comparison_state, "exactly-comparable")
        self.assertEqual(result.losses, ())
        self.assertEqual(result.resolver_contract, self.module.EXACT_RESOLVER_CONTRACT)
        self.assertTrue(SHA256_RE.fullmatch(result.resolution_fingerprint))

    def test_request_order_does_not_change_result_or_fingerprint(self):
        forward = self.resolve(("bhsa", "extrabiblical", "syriac"))
        reverse = self.resolve(("syriac", "extrabiblical", "bhsa"))
        self.assertEqual(forward, reverse)

    def test_plan_retains_required_provenance(self):
        plan = self.resolve(("bhsa",)).plans[0]
        self.assertTrue(plan.mapping_id)
        self.assertTrue(plan.projection_id)
        self.assertTrue(plan.mapping_semantic_digest)
        self.assertTrue(plan.projection_semantic_digest)
        self.assertEqual(plan.mapping_review.status, "reviewed")
        self.assertEqual(plan.projection_review.status, "reviewed")
        self.assertTrue(plan.ontology_lock.lock_id)
        self.assertTrue(plan.mapping_evidence)
        self.assertTrue(plan.projection_evidence)
        self.assertEqual(
            plan.expected_parent_manifest_digest,
            plan.variant.expected_parent_manifest_digest,
        )
        self.assertEqual(plan.parent_state, "verified-exact")

    # Request validation.
    def test_empty_corpora_fail(self):
        assert_problem(
            self,
            "invalid_corpus_selection",
            self.module.semantic_resolve,
            self.ir,
            request_for(self.module, ()),
            self.prerequisites,
        )

    def test_duplicate_corpus_fails(self):
        assert_problem(
            self,
            "invalid_corpus_selection",
            self.module.semantic_resolve,
            self.ir,
            request_for(self.module, ("bhsa", "bhsa")),
            self.prerequisites,
        )

    def test_approximate_mode_is_rejected(self):
        assert_problem(self, "unsupported_semantic_mode", self.resolve, ("bhsa",), mode="approximate")

    def test_unknown_request_vocabulary_fails(self):
        bad = replace(noun_semantic_key(), profile_id="unknown-profile")
        assert_problem(self, "unknown_request_vocabulary", self.resolve, ("bhsa",), key=bad)

    def test_wrong_existing_capability_does_not_resolve_by_target(self):
        bad = replace(noun_semantic_key(), capability_id="linguistic.morphology")
        assert_problem(self, "capability_absent", self.resolve, ("bhsa",), key=bad)

    def test_wrong_formal_kind_does_not_resolve_by_target(self):
        bad = replace(noun_semantic_key(), formal_kind="property")
        assert_problem(self, "semantic_tuple_absent", self.resolve, ("bhsa",), key=bad)

    def test_unrequested_corpus_never_leaks(self):
        result = self.resolve(("bhsa",))
        self.assertEqual([plan.corpus_id for plan in result.plans], ["bhsa"])

    # Prerequisite selection and runtime state.
    def test_missing_prerequisite_fails(self):
        assert_problem(self, "missing_prerequisite", self.resolve, ("bhsa",), prerequisites=())

    def test_unknown_variant_is_stale(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        stale = replace(current, variant=replace(current.variant, authored_profile_id="other"))
        assert_problem(self, "stale_prerequisite", self.resolve, ("bhsa",), prerequisites=(stale,))

    def test_wrong_release_fingerprint_is_stale(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        stale = replace(current, profile_release_fingerprint="sha256:" + "0" * 64)
        assert_problem(self, "stale_prerequisite", self.resolve, ("bhsa",), prerequisites=(stale,))

    def test_two_fresh_variants_are_ambiguous(self):
        ir = compile_semantic_ir(
            (
                validated_noun_bundle("bhsa", parent_char="a"),
                validated_noun_bundle("bhsa", parent_char="d"),
            )
        )
        prerequisites = prerequisites_for(self.module, ir)
        assert_problem(
            self,
            "ambiguous_prerequisite_variant",
            self.resolve,
            ("bhsa",),
            ir=ir,
            prerequisites=prerequisites,
        )

    def test_duplicate_identical_prerequisite_fails(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        assert_problem(
            self,
            "invalid_prerequisite",
            self.resolve,
            ("bhsa",),
            prerequisites=(current, current),
        )

    def test_duplicate_conflicting_same_variant_is_order_independent(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        conflicting = replace(current, source_contract="test:other")
        for rows in ((current, conflicting), (conflicting, current)):
            assert_problem(
                self,
                "invalid_prerequisite",
                self.resolve,
                ("bhsa",),
                prerequisites=rows,
            )

    def test_verified_exact_parent_mismatch_is_stale(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        stale = replace(current, observed_parent_manifest_digest="sha256:" + "9" * 64)
        assert_problem(self, "stale_prerequisite", self.resolve, ("bhsa",), prerequisites=(stale,))

    def test_parent_unverified_fails(self):
        state = prerequisite_for(self.module, variant_for(self.ir, "bhsa"), parent_state="unverified")
        assert_problem(self, "parent_unverified", self.resolve, ("bhsa",), prerequisites=(state,))

    def test_parent_incompatible_fails(self):
        state = prerequisite_for(self.module, variant_for(self.ir, "bhsa"), parent_state="incompatible")
        assert_problem(self, "parent_incompatible", self.resolve, ("bhsa",), prerequisites=(state,))

    def test_verified_compatible_requires_changed_parent_and_can_resolve(self):
        compatible_ir = self.compatible_ir()
        state = prerequisite_for(
            self.module,
            variant_for(compatible_ir, "bhsa"),
            parent_state="verified-compatible",
            observed_parent="sha256:" + "8" * 64,
        )
        result = self.resolve(("bhsa",), ir=compatible_ir, prerequisites=(state,))
        self.assertEqual(result.plans[0].parent_state, "verified-compatible")

    def test_verified_compatible_equal_parent_is_invalid(self):
        state = prerequisite_for(
            self.module,
            variant_for(self.ir, "bhsa"),
            parent_state="verified-compatible",
        )
        assert_problem(self, "invalid_prerequisite", self.resolve, ("bhsa",), prerequisites=(state,))

    def test_missing_release_dependency_is_stale(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        state = replace(current, dependency_results=current.dependency_results[:-1])
        assert_problem(self, "stale_prerequisite", self.resolve, ("bhsa",), prerequisites=(state,))

    def test_extra_release_dependency_is_stale(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        extra = self.module.DependencyPrerequisiteResult(
            "dep:extra", "pass", None, "test-rule-v1"
        )
        state = replace(current, dependency_results=current.dependency_results + (extra,))
        assert_problem(self, "stale_prerequisite", self.resolve, ("bhsa",), prerequisites=(state,))

    def test_duplicate_dependency_id_is_invalid(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        state = replace(
            current,
            dependency_results=current.dependency_results + (current.dependency_results[0],),
        )
        assert_problem(self, "invalid_prerequisite", self.resolve, ("bhsa",), prerequisites=(state,))

    def test_failed_or_unknown_dependency_is_unavailable(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        for result in ("fail", "unknown"):
            dependency = replace(current.dependency_results[0], result=result)
            state = replace(current, dependency_results=(dependency,))
            assert_problem(
                self,
                "dependency_unavailable",
                self.resolve,
                ("bhsa",),
                prerequisites=(state,),
            )

    def test_invalid_dependency_result_is_invalid_prerequisite(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        dependency = replace(current.dependency_results[0], result="maybe")
        state = replace(current, dependency_results=(dependency,))
        assert_problem(self, "invalid_prerequisite", self.resolve, ("bhsa",), prerequisites=(state,))

    def test_empty_source_contract_is_invalid(self):
        state = prerequisite_for(
            self.module,
            variant_for(self.ir, "bhsa"),
            source_contract="",
        )
        assert_problem(self, "invalid_prerequisite", self.resolve, ("bhsa",), prerequisites=(state,))

    def test_null_bundle_variant_rejects_fabricated_bundle(self):
        current = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        state = replace(
            current,
            active_ontology_bundle_digest="sha256:" + "7" * 64,
            ontology_bundle_state="verified",
        )
        assert_problem(self, "invalid_prerequisite", self.resolve, ("bhsa",), prerequisites=(state,))

    def test_required_bundle_unavailable_fails(self):
        ir = with_bundle_digest(
            compiled_noun_ir(("bhsa",)),
            "sha256:" + "6" * 64,
        )
        current = prerequisite_for(self.module, ir.variants[0])
        state = replace(
            current,
            active_ontology_bundle_digest=None,
            ontology_bundle_state="unavailable",
        )
        assert_problem(
            self,
            "ontology_bundle_unavailable",
            self.resolve,
            ("bhsa",),
            ir=ir,
            prerequisites=(state,),
        )

    def test_required_bundle_digest_mismatch_is_stale(self):
        ir = with_bundle_digest(compiled_noun_ir(("bhsa",)), "sha256:" + "6" * 64)
        current = prerequisite_for(self.module, ir.variants[0])
        state = replace(current, active_ontology_bundle_digest="sha256:" + "5" * 64)
        assert_problem(
            self,
            "stale_prerequisite",
            self.resolve,
            ("bhsa",),
            ir=ir,
            prerequisites=(state,),
        )

    def test_required_bundle_not_required_state_is_invalid(self):
        ir = with_bundle_digest(compiled_noun_ir(("bhsa",)), "sha256:" + "6" * 64)
        current = prerequisite_for(self.module, ir.variants[0])
        state = replace(current, active_ontology_bundle_digest=None, ontology_bundle_state="not-required")
        assert_problem(
            self,
            "invalid_prerequisite",
            self.resolve,
            ("bhsa",),
            ir=ir,
            prerequisites=(state,),
        )

    # Capability discovery remains separate from exact execution authority.
    def test_native_only_capability_can_be_active_without_target_resolution(self):
        ir = compile_semantic_ir(
            (validated_noun_bundle("native-only", parent_char="a", native_state="native-only"),)
        )
        prerequisite = prerequisite_for(self.module, ir.variants[0])
        views = self.module.semantic_capabilities(ir, (prerequisite,))
        self.assertEqual(len(views), 1)
        self.assertEqual(views[0].state, "active")
        self.assertFalse(views[0].executable_exact)
        assert_problem(
            self,
            "semantic_tuple_absent",
            self.module.semantic_resolve,
            ir,
            request_for(self.module, ("native-only",)),
            (prerequisite,),
        )

    def test_unsupported_only_capability_is_absent(self):
        ir = compile_semantic_ir(
            (validated_noun_bundle("unsupported", parent_char="a", native_state="unsupported"),)
        )
        prerequisite = prerequisite_for(self.module, ir.variants[0])
        views = self.module.semantic_capabilities(ir, (prerequisite,))
        self.assertEqual(views[0].state, "absent")
        assert_problem(
            self,
            "capability_absent",
            self.module.semantic_resolve,
            ir,
            request_for(self.module, ("unsupported",)),
            (prerequisite,),
        )

    def test_positive_capability_with_unverified_parent_is_unavailable_in_discovery(self):
        ir = compiled_noun_ir(("bhsa",))
        prerequisite = prerequisite_for(self.module, ir.variants[0], parent_state="unverified")
        views = self.module.semantic_capabilities(ir, (prerequisite,))
        self.assertEqual(views[0].state, "unavailable")

    def test_capability_view_cannot_substitute_for_prerequisite(self):
        ir = compiled_noun_ir(("bhsa",))
        prerequisite = prerequisite_for(self.module, ir.variants[0])
        view = self.module.semantic_capabilities(ir, (prerequisite,))[0]
        with self.assertRaises(TypeError):
            self.module.semantic_resolve(
                ir,
                request_for(self.module, ("bhsa",)),
                (view,),
            )

    # Exact assessment/routing and multi-binding behavior.
    def test_related_mapping_is_non_exact(self):
        ir = compile_semantic_ir((validated_assessment_bundle("related", "related"),))
        prerequisite = prerequisite_for(self.module, ir.variants[0])
        assert_problem(
            self,
            "non_exact_mapping",
            self.module.semantic_resolve,
            ir,
            request_for(self.module, ("related",)),
            (prerequisite,),
        )

    def test_authority_index_cannot_satisfy_semantic_resolve(self):
        ir = compile_semantic_ir(
            (validated_noun_bundle("authority", parent_char="a", projection_route="authority"),)
        )
        self.assertEqual(ir.semantic_index, ())
        self.assertEqual(ir.authority_index[0][0].authority_resource, AUTHORITY_NOUN)
        prerequisite = prerequisite_for(self.module, ir.variants[0])
        authority_key = SemanticKey(
            "linguistic",
            "linguistic.part-of-speech",
            AUTHORITY_NOUN,
            "skos-concept",
            "annotation-value",
        )
        assert_problem(
            self,
            "semantic_tuple_absent",
            self.module.semantic_resolve,
            ir,
            request_for(self.module, ("authority",), key=authority_key),
            (prerequisite,),
        )

    def test_mismatched_routing_in_semantic_index_is_invalid_compiled_ir(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        bad_row = replace(
            rows[0],
            reference_kind="authority-value",
            query_role="authority-value-filter",
        )
        bad_ir = replace(ir, semantic_index=((key, (bad_row,)),))
        prerequisite = prerequisite_for(self.module, bad_ir.variants[0])
        assert_problem(
            self,
            "invalid_compiled_ir",
            self.module.semantic_resolve,
            bad_ir,
            request_for(self.module, ("bhsa",)),
            (prerequisite,),
        )

    def test_two_exact_bindings_fail_closed(self):
        ir = compile_semantic_ir((validated_two_binding_bundle("multi"),))
        prerequisite = prerequisite_for(self.module, ir.variants[0])
        assert_problem(
            self,
            "multiple_exact_bindings",
            self.module.semantic_resolve,
            ir,
            request_for(self.module, ("multi",)),
            (prerequisite,),
        )

    def test_exact_plus_related_selects_only_exact(self):
        ir = compile_semantic_ir(
            (validated_two_binding_bundle("mixed", second_assessment="related"),)
        )
        prerequisite = prerequisite_for(self.module, ir.variants[0])
        result = self.module.semantic_resolve(
            ir,
            request_for(self.module, ("mixed",)),
            (prerequisite,),
        )
        self.assertEqual(len(result.plans), 1)
        self.assertEqual(result.plans[0].assessment, "exact")

    # Defensive compiled-IR coherence.
    def test_duplicate_variant_keys_fail_before_lookup(self):
        ir = compiled_noun_ir(("bhsa",))
        bad_ir = replace(ir, variants=(ir.variants[0], ir.variants[0]))
        assert_problem(
            self,
            "invalid_compiled_ir",
            self.module.semantic_resolve,
            bad_ir,
            request_for(self.module, ("bhsa",)),
            (),
        )

    def test_duplicate_semantic_index_keys_fail_before_lookup(self):
        ir = compiled_noun_ir(("bhsa",))
        bad_ir = replace(ir, semantic_index=(ir.semantic_index[0], ir.semantic_index[0]))
        assert_problem(
            self,
            "invalid_compiled_ir",
            self.module.semantic_resolve,
            bad_ir,
            request_for(self.module, ("bhsa",)),
            (),
        )

    def test_duplicate_capability_keys_fail_before_lookup(self):
        ir = compiled_noun_ir(("bhsa",))
        bad_ir = replace(ir, capability_facts=(ir.capability_facts[0], ir.capability_facts[0]))
        assert_problem(
            self,
            "invalid_compiled_ir",
            self.module.semantic_resolve,
            bad_ir,
            request_for(self.module, ("bhsa",)),
            (),
        )

    def test_binding_mapping_digest_must_belong_to_release(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        bad = replace(rows[0], mapping_semantic_digest="sha256:" + "4" * 64)
        bad_ir = replace(ir, semantic_index=((key, (bad,)),))
        prerequisite = prerequisite_for(self.module, bad_ir.variants[0])
        assert_problem(
            self,
            "invalid_compiled_ir",
            self.module.semantic_resolve,
            bad_ir,
            request_for(self.module, ("bhsa",)),
            (prerequisite,),
        )

    def test_binding_mapping_review_must_match_release(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        bad_review = replace(rows[0].mapping_review, review_id="review:forged")
        bad = replace(rows[0], mapping_review=bad_review)
        bad_ir = replace(ir, semantic_index=((key, (bad,)),))
        prerequisite = prerequisite_for(self.module, bad_ir.variants[0])
        assert_problem(self, "invalid_compiled_ir", self.module.semantic_resolve, bad_ir, request_for(self.module, ("bhsa",)), (prerequisite,))

    def test_binding_projection_review_must_match_release(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        bad_review = replace(rows[0].projection_review, review_id="review:forged")
        bad = replace(rows[0], projection_review=bad_review)
        bad_ir = replace(ir, semantic_index=((key, (bad,)),))
        prerequisite = prerequisite_for(self.module, bad_ir.variants[0])
        assert_problem(self, "invalid_compiled_ir", self.module.semantic_resolve, bad_ir, request_for(self.module, ("bhsa",)), (prerequisite,))

    def test_binding_ontology_lock_must_match_release(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        bad_lock = replace(rows[0].ontology_lock, content_digest="sha256:" + "3" * 64)
        bad = replace(rows[0], ontology_lock=bad_lock)
        bad_ir = replace(ir, semantic_index=((key, (bad,)),))
        prerequisite = prerequisite_for(self.module, bad_ir.variants[0])
        assert_problem(self, "invalid_compiled_ir", self.module.semantic_resolve, bad_ir, request_for(self.module, ("bhsa",)), (prerequisite,))

    def test_binding_dependency_must_belong_to_release(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        bad = replace(rows[0], native_dependencies=rows[0].native_dependencies + ("dep:forged",))
        bad_ir = replace(ir, semantic_index=((key, (bad,)),))
        prerequisite = prerequisite_for(self.module, bad_ir.variants[0])
        assert_problem(self, "invalid_compiled_ir", self.module.semantic_resolve, bad_ir, request_for(self.module, ("bhsa",)), (prerequisite,))

    def test_variant_release_key_must_match_variant_key(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        bad_variant = replace(
            variant,
            release_key=replace(variant.release_key, corpus_id="other"),
        )
        bad_ir = replace(ir, variants=(bad_variant,))
        prerequisite = prerequisite_for(self.module, bad_variant)
        assert_problem(self, "invalid_compiled_ir", self.module.semantic_resolve, bad_ir, request_for(self.module, ("bhsa",)), (prerequisite,))

    def test_variant_bundle_digest_must_match_release_signature(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        bad_signature = replace(
            variant.release_signature,
            ontology_bundle_digest="sha256:" + "2" * 64,
        )
        bad_variant = replace(variant, release_signature=bad_signature)
        bad_ir = replace(ir, variants=(bad_variant,))
        prerequisite = prerequisite_for(self.module, bad_variant)
        assert_problem(self, "invalid_compiled_ir", self.module.semantic_resolve, bad_ir, request_for(self.module, ("bhsa",)), (prerequisite,))

    def test_native_binding_identity_tamper_is_invalid(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        binding = replace(rows[0].native_execution_binding, feature="tampered")
        bad = replace(rows[0], native_execution_binding=binding)
        bad_ir = replace(ir, semantic_index=((key, (bad,)),))
        prerequisite = prerequisite_for(self.module, bad_ir.variants[0])
        assert_problem(self, "invalid_compiled_ir", self.module.semantic_resolve, bad_ir, request_for(self.module, ("bhsa",)), (prerequisite,))

    def test_authored_null_native_value_resolves_without_false_identity_mismatch(self):
        ir = compile_semantic_ir(
            (validated_binding_presence_bundle("null-value", value_mode="null"),)
        )
        prerequisite = prerequisite_for(self.module, ir.variants[0])
        plan = self.module.semantic_resolve(
            ir,
            request_for(self.module, ("null-value",)),
            (prerequisite,),
        ).plans[0]
        self.assertTrue(plan.native_execution_binding.value_present)
        self.assertIsNone(plan.native_execution_binding.value)

    def test_absent_native_value_resolves_without_false_identity_mismatch(self):
        ir = compile_semantic_ir(
            (validated_binding_presence_bundle("absent-value", value_mode="absent"),)
        )
        prerequisite = prerequisite_for(self.module, ir.variants[0])
        plan = self.module.semantic_resolve(
            ir,
            request_for(self.module, ("absent-value",)),
            (prerequisite,),
        ).plans[0]
        self.assertFalse(plan.native_execution_binding.value_present)
        self.assertIsNone(plan.native_execution_binding.value)

    # Fingerprint contracts.
    def test_profile_release_fingerprint_is_stable(self):
        signature = variant_for(self.ir, "bhsa").release_signature
        first = self.module.profile_release_fingerprint(signature)
        second = self.module.profile_release_fingerprint(signature)
        self.assertEqual(first, second)
        self.assertTrue(SHA256_RE.fullmatch(first))

    def test_dependency_input_order_does_not_change_prerequisite_fingerprint(self):
        state = prerequisite_for(self.module, variant_for(self.ir, "bhsa"))
        reversed_state = replace(state, dependency_results=tuple(reversed(state.dependency_results)))
        self.assertEqual(
            self.module.runtime_prerequisite_fingerprint(state),
            self.module.runtime_prerequisite_fingerprint(reversed_state),
        )

    def test_source_contract_is_preserved_and_changes_all_runtime_fingerprints(self):
        variant = variant_for(self.ir, "bhsa")
        first = prerequisite_for(self.module, variant, source_contract="source:a")
        second = prerequisite_for(self.module, variant, source_contract="source:b")
        first_result = self.resolve(("bhsa",), prerequisites=(first,))
        second_result = self.resolve(("bhsa",), prerequisites=(second,))
        self.assertEqual(first_result.plans[0].prerequisite_source_contract, "source:a")
        self.assertEqual(second_result.plans[0].prerequisite_source_contract, "source:b")
        self.assertNotEqual(
            self.module.runtime_prerequisite_fingerprint(first),
            self.module.runtime_prerequisite_fingerprint(second),
        )
        self.assertNotEqual(first_result.plans[0].plan_fingerprint, second_result.plans[0].plan_fingerprint)
        self.assertNotEqual(first_result.resolution_fingerprint, second_result.resolution_fingerprint)
        self.assertEqual(
            self.module.profile_release_fingerprint(variant.release_signature),
            first.profile_release_fingerprint,
        )

    def test_source_contract_is_not_normalized(self):
        state = prerequisite_for(
            self.module,
            variant_for(self.ir, "bhsa"),
            source_contract="  Test Contract  ",
        )
        plan = self.resolve(("bhsa",), prerequisites=(state,)).plans[0]
        self.assertEqual(plan.prerequisite_source_contract, "  Test Contract  ")

    def test_observed_parent_change_changes_runtime_plan_and_resolution_identity(self):
        compatible_ir = self.compatible_ir()
        variant = variant_for(compatible_ir, "bhsa")
        exact = prerequisite_for(self.module, variant)
        compatible = prerequisite_for(
            self.module,
            variant,
            parent_state="verified-compatible",
            observed_parent="sha256:" + "1" * 64,
        )
        first = self.resolve(("bhsa",), ir=compatible_ir, prerequisites=(exact,))
        second = self.resolve(("bhsa",), ir=compatible_ir, prerequisites=(compatible,))
        self.assertNotEqual(
            self.module.runtime_prerequisite_fingerprint(exact),
            self.module.runtime_prerequisite_fingerprint(compatible),
        )
        self.assertNotEqual(first.plans[0].plan_fingerprint, second.plans[0].plan_fingerprint)
        self.assertNotEqual(first.resolution_fingerprint, second.resolution_fingerprint)

    def test_request_corpus_set_changes_resolution_fingerprint(self):
        one = self.resolve(("bhsa",))
        three = self.resolve(("bhsa", "syriac", "extrabiblical"))
        self.assertNotEqual(one.resolution_fingerprint, three.resolution_fingerprint)

    def test_resolver_contract_participates_in_plan_and_result_identity(self):
        baseline = self.resolve(("bhsa",))
        with mock.patch.object(
            self.module,
            "EXACT_RESOLVER_CONTRACT",
            "tfont-exact-semantic-resolver-v1-test-mutation",
        ):
            changed = self.resolve(("bhsa",))
        self.assertNotEqual(baseline.plans[0].plan_fingerprint, changed.plans[0].plan_fingerprint)
        self.assertNotEqual(baseline.resolution_fingerprint, changed.resolution_fingerprint)

    def test_audit_only_review_edits_do_not_change_resolution_identity(self):
        first_ir = compile_semantic_ir(
            (validated_noun_bundle("bhsa", parent_char="a", audit_suffix="-a"),)
        )
        second_ir = compile_semantic_ir(
            (validated_noun_bundle("bhsa", parent_char="a", audit_suffix="-b"),)
        )
        first_pre = prerequisite_for(self.module, first_ir.variants[0])
        second_pre = prerequisite_for(self.module, second_ir.variants[0])
        first = self.module.semantic_resolve(
            first_ir,
            request_for(self.module, ("bhsa",)),
            (first_pre,),
        )
        second = self.module.semantic_resolve(
            second_ir,
            request_for(self.module, ("bhsa",)),
            (second_pre,),
        )
        self.assertEqual(first, second)

    def test_native_source_projection_distinguishes_null_from_absence(self):
        null_ir = compile_semantic_ir(
            (validated_binding_presence_bundle("null-value", value_mode="null"),)
        )
        absent_ir = compile_semantic_ir(
            (validated_binding_presence_bundle("absent-value", value_mode="absent"),)
        )
        null_binding = dict(null_ir.semantic_index)[noun_semantic_key()][0].native_execution_binding
        absent_binding = dict(absent_ir.semantic_index)[noun_semantic_key()][0].native_execution_binding
        self.assertTrue(null_binding.value_present)
        self.assertFalse(absent_binding.value_present)
        self.assertNotEqual(
            native_binding_identity({"component_id": "x", "feature": "sp", "value": None}),
            native_binding_identity({"component_id": "x", "feature": "sp"}),
        )


if __name__ == "__main__":
    unittest.main()
