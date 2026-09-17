from __future__ import annotations

from dataclasses import replace
import unittest

import tfont
from tests.i005._fixtures import noun_sources, source_bundle, validate_structural_sources
from tests.i006._fixtures import _refresh_mapping, noun_semantic_key
from tests.i007.test_runtime_prerequisite_contract import FakeObservation
from tests.i008._fixtures import FakeLoadedApi
from tfont.semantic_ir import compile_semantic_ir
from tfont.semantic_resolver import SemanticResolveRequest, SemanticResolutionError, profile_release_fingerprint, semantic_resolve
from tfont.semantic_validation import validate_semantic_bundle
from tfont.source_validation import SourceValidationError
from tfont.runtime_prerequisites import evaluate_runtime_prerequisites


def compiled(policy: str | None = None, *, executable: bool = False):
    sources = noun_sources("bhsa", parent_char="a")
    if policy is not None:
        sources["profile"]["parent_compatibility"] = policy
    if executable:
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_binding"]["execution_shape"] = "value-predicate"
        mapping["projections"][0]["native_execution_binding"]["execution_shape"] = "value-predicate"
        _refresh_mapping(mapping)
    validate_structural_sources(sources)
    return compile_semantic_ir((validate_semantic_bundle(source_bundle(sources)),))


def report(ir, parent: str | None = None, *, values=("subs",), values_state="complete"):
    variant = ir.variants[0]
    observation = FakeObservation(
        variant.key.expected_parent_manifest_digest if parent is None else parent,
        values_state=values_state,
        values=values,
    )
    return evaluate_runtime_prerequisites(variant, observation, source_contract="test:i011-observation-v1")


def request():
    return SemanticResolveRequest(key=noun_semantic_key(), corpora=("bhsa",))


class I011ParentPolicyTests(unittest.TestCase):
    def test_omitted_and_explicit_exact_only_compile_to_same_release_authority(self):
        missing = compiled()
        explicit = compiled("exact-only")
        left = missing.variants[0].release_signature
        right = explicit.variants[0].release_signature
        self.assertEqual(left.parent_compatibility, "exact-only")
        self.assertEqual(right.parent_compatibility, "exact-only")
        self.assertEqual(left, right)
        self.assertEqual(profile_release_fingerprint(left), profile_release_fingerprint(right))

    def test_opt_in_changes_authority_and_release_fingerprint_not_mapping_digest(self):
        exact, compatible = compiled("exact-only"), compiled("dependency-verified")
        left, right = exact.variants[0], compatible.variants[0]
        self.assertEqual(right.release_signature.parent_compatibility, "dependency-verified")
        self.assertEqual(left.key, right.key)
        self.assertEqual(left.mapping_digests, right.mapping_digests)
        self.assertNotEqual(profile_release_fingerprint(left.release_signature), profile_release_fingerprint(right.release_signature))

    def test_bad_source_policy_rejected_structurally(self):
        for invalid in ("compatible", "", 123, None, True):
            with self.subTest(invalid=invalid):
                sources = noun_sources("bhsa", parent_char="a")
                sources["profile"]["parent_compatibility"] = invalid
                with self.assertRaises(SourceValidationError):
                    validate_structural_sources(sources)

    def test_malformed_compiled_signature_fails_closed(self):
        ir = compiled("exact-only")
        signature = ir.variants[0].release_signature
        for invalid in ("unknown", "", None, 1, True):
            with self.subTest(invalid=invalid):
                malformed = replace(signature, parent_compatibility=invalid)
                with self.assertRaises(SemanticResolutionError) as raised:
                    profile_release_fingerprint(malformed)
                self.assertEqual(raised.exception.problem.category, "invalid_compiled_ir")

    def test_exact_parent_stays_exact_under_both_policies(self):
        for policy in (None, "exact-only", "dependency-verified"):
            with self.subTest(policy=policy):
                ir = compiled(policy)
                result = report(ir)
                self.assertEqual(result.compatibility_state, "verified-exact")
                self.assertEqual(len(semantic_resolve(ir, request(), (result.to_prerequisite(),)).plans), 1)

    def test_wrong_parent_fails_closed_without_explicit_opt_in(self):
        for policy in (None, "exact-only"):
            with self.subTest(policy=policy):
                ir = compiled(policy)
                result = report(ir, "sha256:" + "9" * 64)
                self.assertEqual(result.compatibility_state, "incompatible")
                with self.assertRaises(SemanticResolutionError) as raised:
                    semantic_resolve(ir, request(), (result.to_prerequisite(),))
                self.assertEqual(raised.exception.problem.category, "parent_incompatible")

    def test_explicit_opt_in_requires_all_dependencies_to_pass(self):
        ir = compiled("dependency-verified")
        other_parent = "sha256:" + "9" * 64
        compatible = report(ir, other_parent)
        self.assertEqual(compatible.compatibility_state, "verified-compatible")
        self.assertEqual(len(semantic_resolve(ir, request(), (compatible.to_prerequisite(),)).plans), 1)
        failed = report(ir, other_parent, values=())
        self.assertEqual(failed.compatibility_state, "incompatible")
        unknown = report(ir, other_parent, values_state="unknown")
        self.assertEqual(unknown.compatibility_state, "unverified")
        for blocked in (failed, unknown):
            with self.assertRaises(SemanticResolutionError):
                semantic_resolve(ir, request(), (blocked.to_prerequisite(),))

    def test_dependency_failure_unknown_precede_policy_even_on_exact_parent(self):
        for policy in ("exact-only", "dependency-verified"):
            ir = compiled(policy)
            self.assertEqual(report(ir, values=()).compatibility_state, "incompatible")
            self.assertEqual(report(ir, values_state="unknown").compatibility_state, "unverified")

    def test_forged_compatible_prerequisite_cannot_widen_exact_only_release(self):
        ir = compiled("exact-only")
        good = report(ir).to_prerequisite()
        forged = replace(good, parent_state="verified-compatible", observed_parent_manifest_digest="sha256:" + "9" * 64)
        with self.assertRaises(SemanticResolutionError) as raised:
            semantic_resolve(ir, request(), (forged,))
        self.assertEqual(raised.exception.problem.category, "parent_incompatible")

    def test_policy_change_invalidates_old_prerequisite(self):
        old_ir = compiled("dependency-verified")
        old_state = report(old_ir).to_prerequisite()
        new_ir = compiled("exact-only")
        with self.assertRaises(SemanticResolutionError) as raised:
            semantic_resolve(new_ir, request(), (old_state,))
        self.assertEqual(raised.exception.problem.category, "stale_prerequisite")

    def test_loaded_executor_inherits_exact_only_without_caller_flag(self):
        ir = compiled("exact-only", executable=True)
        api = FakeLoadedApi(values={1: "subs", 2: "verb"}, node_types={1: "word", 2: "word"})
        context = tfont.LoadedCorpusContext(
            corpus_id="bhsa",
            parent_manifest_digest="sha256:" + "9" * 64,
            components=(tfont.LoadedComponentContext(
                component_id="bhsa-tf",
                content_digest="sha256:" + "e" * 64,
                api=api,
            ),),
        )
        with self.assertRaises(SemanticResolutionError) as raised:
            tfont.execute_exact_semantic(ir, request(), (context,))
        self.assertEqual(raised.exception.problem.category, "parent_incompatible")
        self.assertEqual(api.F.sp.s_calls, 0)
        self.assertEqual(api.load_calls, 0)


if __name__ == "__main__":
    unittest.main()
