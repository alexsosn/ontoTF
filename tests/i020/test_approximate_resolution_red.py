from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import unittest

import tfont
from tfont.digests import canonical_json_bytes
from tfont.semantic_ir import ApproximationIR, compile_semantic_ir
from tests.i006._fixtures import validated_assessment_bundle

from ._fixtures import (
    approximate_conjunction_request,
    approximate_request,
    compiled_binding_ir,
    compiled_noun_ir,
    compiled_presence_variant_ir,
    compiled_two_binding_ir,
    mutated_production_conjunction,
    noun_semantic_key,
    prerequisites_for,
    problem_category,
    replace_semantic_binding,
    validated_binding_bundle,
)


RESOLVER_API = (
    "APPROXIMATE_RESOLVER_CONTRACT",
    "APPROXIMATE_PLAN_FINGERPRINT_ALGORITHM",
    "APPROXIMATE_RESOLUTION_FINGERPRINT_ALGORITHM",
    "APPROXIMATE_CONJUNCTION_RESOLVER_CONTRACT",
    "APPROXIMATE_CONJUNCTION_RESOLUTION_FINGERPRINT_ALGORITHM",
    "ApproximateSemanticResolveRequest",
    "ApproximationLossRecord",
    "ApproximateNativePlan",
    "ApproximateSemanticResolutionResult",
    "ApproximateSemanticConjunctionRequest",
    "ApproximateSemanticConjunctionResolutionResult",
    "semantic_resolve_approximate",
    "semantic_resolve_approximate_conjunction",
)
HAS_APPROXIMATE_RESOLVER = all(hasattr(tfont, name) for name in RESOLVER_API)


def assert_problem(testcase, category, callable_, *args, **kwargs):
    with testcase.assertRaises(tfont.SemanticResolutionError) as raised:
        callable_(*args, **kwargs)
    testcase.assertEqual(problem_category(raised.exception), category)
    return raised.exception


class I020RedSentinelTests(unittest.TestCase):
    def test_public_approximate_resolver_surface_exists(self):
        missing = [name for name in RESOLVER_API if not hasattr(tfont, name)]
        self.assertEqual(
            missing,
            [],
            f"RED: missing I-020 approximate resolver API: {missing}",
        )

    def test_compiler_preserves_reviewed_projection_semantic_payload(self):
        ir = compiled_binding_ir((("bhsa", "broader", ("undercoverage",), True),))
        binding = dict(ir.semantic_index)[noun_semantic_key()][0]
        payload = getattr(binding, "projection_semantic_payload", None)
        self.assertIsInstance(
            payload,
            str,
            "RED: TargetBindingIR lacks reviewed projection semantic payload",
        )
        decoded = json.loads(payload)
        self.assertEqual(payload, canonical_json_bytes(decoded).decode("utf-8"))
        digest = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(digest, binding.projection_semantic_digest)
        self.assertEqual(decoded["assessment"], "broader")
        self.assertTrue(decoded["approximation"]["eligible"])
        self.assertEqual(decoded["approximation"]["losses"], ["undercoverage"])


class I020ExactCompatibilityAnchors(unittest.TestCase):
    def test_exact_single_and_multicorpus_fingerprints_are_unchanged(self):
        one = compiled_noun_ir(("bhsa",))
        one_result = tfont.semantic_resolve(
            one,
            tfont.SemanticResolveRequest(
                key=noun_semantic_key(),
                corpora=("bhsa",),
                semantic_mode="exact",
            ),
            prerequisites_for(tfont, one),
        )
        self.assertEqual(
            one_result.plans[0].plan_fingerprint,
            "sha256:a7dc2b0d8e234a7df399fed88c2af79aee0653f2233a1b15f68c9022a8f44616",
        )
        self.assertEqual(
            one_result.resolution_fingerprint,
            "sha256:90b87e1b4f59c3a53338b8ff952c7a1088905f78d25e46adf0d191a904435cfc",
        )

        three = compiled_noun_ir(("bhsa", "syriac", "extrabiblical"))
        three_result = tfont.semantic_resolve(
            three,
            tfont.SemanticResolveRequest(
                key=noun_semantic_key(),
                corpora=("syriac", "extrabiblical", "bhsa"),
                semantic_mode="exact",
            ),
            prerequisites_for(tfont, three),
        )
        self.assertEqual(
            three_result.resolution_fingerprint,
            "sha256:024fceafaca2ff36ebb6f52953b32ae5ac36956d70ecb93e66facab67957a5c7",
        )

    def test_exact_conjunction_fingerprint_is_unchanged(self):
        from tests.i015.test_exact_conjunction_behavior import (
            compiled_and_contexts,
            key,
        )

        ir, contexts = compiled_and_contexts()
        result = tfont.execute_exact_conjunction(
            ir,
            tfont.SemanticConjunctionRequest(
                keys=(key("Plural"), key("Noun")),
                corpora=("syriac", "bhsa", "extrabiblical"),
                semantic_mode="exact",
            ),
            contexts,
        )
        self.assertEqual(
            result.resolution.resolution_fingerprint,
            "sha256:2f4b11335365b24adf8910c28a854dda5b0c99f702b38ad528a5b4c10a7054ca",
        )
        self.assertEqual(
            [(row.corpus_id, row.nodes) for row in result.corpora],
            [
                ("bhsa", (2, 4)),
                ("extrabiblical", (2, 4)),
                ("syriac", (2, 4)),
            ],
        )


@unittest.skipUnless(
    HAS_APPROXIMATE_RESOLVER,
    "RED sentinel owns approximate resolver API absence",
)
class I020ApproximateResolutionTests(unittest.TestCase):
    def resolve(
        self,
        ir,
        *,
        corpora=("bhsa",),
        accept_losses=(),
        prerequisites=None,
        key=None,
    ):
        rows = prerequisites_for(tfont, ir) if prerequisites is None else prerequisites
        return tfont.semantic_resolve_approximate(
            ir,
            approximate_request(
                tfont,
                corpora=tuple(corpora),
                accept_losses=tuple(accept_losses),
                key=key,
            ),
            rows,
        )

    def test_reviewed_broader_requires_accepted_undercoverage(self):
        ir = compiled_binding_ir((("bhsa", "broader", ("undercoverage",), True),))
        assert_problem(
            self,
            "approximation_loss_not_accepted",
            self.resolve,
            ir,
        )

        result = self.resolve(ir, accept_losses=("undercoverage",))
        self.assertEqual(result.resolver_contract, tfont.APPROXIMATE_RESOLVER_CONTRACT)
        self.assertEqual(result.comparison_state, "approximately-comparable")
        self.assertEqual(result.losses, ("undercoverage",))
        self.assertEqual(len(result.loss_records), 1)

        plan = result.plans[0]
        record = result.loss_records[0]
        self.assertEqual(plan.assessment, "broader")
        self.assertEqual(plan.losses, ("undercoverage",))
        self.assertEqual(plan.loss_record, record)
        self.assertEqual(record.corpus_id, "bhsa")
        self.assertEqual(record.mapping_id, plan.mapping_id)
        self.assertEqual(record.projection_id, plan.projection_id)
        self.assertEqual(record.native_execution_binding_identity, plan.native_execution_binding_identity)
        self.assertEqual(record.losses, ("undercoverage",))
        self.assertEqual(
            record.effects,
            ("native selector may miss members of the requested semantic target",),
        )
        self.assertEqual(record.caller_accepted_losses, ("undercoverage",))
        self.assertEqual(record.mapping_semantic_digest, plan.mapping_semantic_digest)
        self.assertEqual(record.projection_semantic_digest, plan.projection_semantic_digest)
        self.assertEqual(record.prerequisite_fingerprint, plan.prerequisite_fingerprint)
        self.assertEqual(record.prerequisite_source_contract, plan.prerequisite_source_contract)
        self.assertTrue(record.approximation_review_id)
        self.assertTrue(plan.plan_fingerprint)
        self.assertTrue(result.resolution_fingerprint)

    def test_reviewed_narrower_requires_accepted_overcoverage(self):
        ir = compiled_binding_ir((("bhsa", "narrower", ("overcoverage",), True),))
        assert_problem(
            self,
            "approximation_loss_not_accepted",
            self.resolve,
            ir,
        )
        result = self.resolve(ir, accept_losses=("overcoverage",))
        self.assertEqual(result.losses, ("overcoverage",))
        self.assertEqual(
            result.loss_records[0].effects,
            ("native selector may include members outside the requested semantic target",),
        )

    def test_reviewed_close_supports_each_reviewed_loss_shape(self):
        cases = (
            (("undercoverage",), ("undercoverage",)),
            (("overcoverage",), ("overcoverage",)),
            (
                ("undercoverage", "overcoverage"),
                ("overcoverage", "undercoverage"),
            ),
        )
        for losses, accepted in cases:
            with self.subTest(losses=losses):
                ir = compiled_binding_ir((("bhsa", "close", losses, True),))
                result = self.resolve(ir, accept_losses=accepted)
                self.assertEqual(set(result.losses), set(losses))

                if len(losses) == 2:
                    assert_problem(
                        self,
                        "approximation_loss_not_accepted",
                        self.resolve,
                        ir,
                        accept_losses=("undercoverage",),
                    )

    def test_missing_or_ineligible_approximation_is_not_authorized(self):
        no_envelope = compile_semantic_ir(
            (validated_assessment_bundle("bhsa", "broader"),)
        )
        assert_problem(
            self,
            "approximation_not_authorized",
            self.resolve,
            no_envelope,
            accept_losses=("undercoverage",),
        )

        ineligible = compiled_binding_ir(
            (("bhsa", "broader", ("undercoverage",), False),)
        )
        assert_problem(
            self,
            "approximation_not_authorized",
            self.resolve,
            ineligible,
            accept_losses=("undercoverage",),
        )

    def test_related_native_only_and_unsupported_remain_non_substitutive(self):
        related = compile_semantic_ir(
            (validated_assessment_bundle("bhsa", "related"),)
        )
        assert_problem(
            self,
            "non_substitutive_mapping",
            self.resolve,
            related,
            accept_losses=("undercoverage", "overcoverage"),
        )

        native_only = compile_semantic_ir(
            (validated_binding_bundle("bhsa", native_state="native-only"),)
        )
        assert_problem(
            self,
            "semantic_tuple_absent",
            self.resolve,
            native_only,
            accept_losses=("undercoverage", "overcoverage"),
        )

        unsupported = compile_semantic_ir(
            (validated_binding_bundle("bhsa", native_state="unsupported"),)
        )
        assert_problem(
            self,
            "capability_absent",
            self.resolve,
            unsupported,
            accept_losses=("undercoverage", "overcoverage"),
        )

    def test_exact_binding_wins_without_loss_but_multiple_exact_still_refuses(self):
        mixed = compiled_two_binding_ir(
            first_assessment="exact",
            second_assessment="broader",
            second_losses=("undercoverage",),
            second_eligible=True,
        )
        result = self.resolve(mixed, accept_losses=("undercoverage",))
        self.assertEqual(len(result.plans), 1)
        self.assertEqual(result.plans[0].assessment, "exact")
        self.assertEqual(result.plans[0].losses, ())
        self.assertIsNone(result.plans[0].loss_record)
        self.assertEqual(result.losses, ())
        self.assertEqual(result.loss_records, ())
        self.assertEqual(result.comparison_state, "exactly-comparable")

        duplicate_exact = compiled_two_binding_ir(
            first_assessment="exact",
            second_assessment="exact",
        )
        assert_problem(
            self,
            "multiple_exact_bindings",
            self.resolve,
            duplicate_exact,
        )

    def test_multiple_authorized_approximate_bindings_fail_before_loss_tiebreak(self):
        ir = compiled_two_binding_ir(
            first_assessment="broader",
            first_losses=("undercoverage",),
            second_assessment="narrower",
            second_losses=("overcoverage",),
        )
        assert_problem(
            self,
            "multiple_approximate_bindings",
            self.resolve,
            ir,
            accept_losses=("undercoverage",),
        )
        assert_problem(
            self,
            "multiple_approximate_bindings",
            self.resolve,
            ir,
            accept_losses=("undercoverage", "overcoverage"),
        )

    def test_request_loss_validation_precedes_runtime_lookup(self):
        ir = compiled_binding_ir((("bhsa", "broader", ("undercoverage",), True),))
        key = noun_semantic_key()

        bad_container = tfont.ApproximateSemanticResolveRequest(
            key=key,
            corpora=("bhsa",),
            semantic_mode="approximate",
            accept_losses=["undercoverage"],
        )
        assert_problem(
            self,
            "invalid_loss_acceptance",
            tfont.semantic_resolve_approximate,
            ir,
            bad_container,
            (),
        )

        duplicate = tfont.ApproximateSemanticResolveRequest(
            key=key,
            corpora=("bhsa",),
            semantic_mode="approximate",
            accept_losses=("undercoverage", "undercoverage"),
        )
        assert_problem(
            self,
            "invalid_loss_acceptance",
            tfont.semantic_resolve_approximate,
            ir,
            duplicate,
            (),
        )

        non_string = tfont.ApproximateSemanticResolveRequest(
            key=key,
            corpora=("bhsa",),
            semantic_mode="approximate",
            accept_losses=(1,),
        )
        assert_problem(
            self,
            "invalid_loss_acceptance",
            tfont.semantic_resolve_approximate,
            ir,
            non_string,
            (),
        )

        unknown = tfont.ApproximateSemanticResolveRequest(
            key=key,
            corpora=("bhsa",),
            semantic_mode="approximate",
            accept_losses=("future-loss",),
        )
        assert_problem(
            self,
            "unknown_loss_token",
            tfont.semantic_resolve_approximate,
            ir,
            unknown,
            (),
        )

        wrong_mode = tfont.ApproximateSemanticResolveRequest(
            key=key,
            corpora=("bhsa",),
            semantic_mode="exact",
            accept_losses=(),
        )
        assert_problem(
            self,
            "unsupported_semantic_mode",
            tfont.semantic_resolve_approximate,
            ir,
            wrong_mode,
            (),
        )

    def test_valid_request_keeps_stale_prerequisite_precedence(self):
        ir = compiled_binding_ir((("bhsa", "broader", ("undercoverage",), True),))
        state = prerequisites_for(tfont, ir)[0]
        stale = replace(
            state,
            profile_release_fingerprint="sha256:" + "0" * 64,
        )
        assert_problem(
            self,
            "stale_prerequisite",
            self.resolve,
            ir,
            prerequisites=(stale,),
        )

    def test_reviewed_projection_payload_preserves_source_presence_variants(self):
        rows = []
        for publication_null in (False, True):
            for evidence_present in (False, True):
                ir = compiled_presence_variant_ir(
                    publication_null=publication_null,
                    approximation_evidence_present=evidence_present,
                )
                binding = dict(ir.semantic_index)[noun_semantic_key()][0]
                payload = binding.projection_semantic_payload
                self.assertIsInstance(payload, str)
                decoded = json.loads(payload)
                self.assertEqual(
                    payload,
                    canonical_json_bytes(decoded).decode("utf-8"),
                )
                self.assertEqual(
                    "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                    binding.projection_semantic_digest,
                )
                rows.append(payload)
        self.assertEqual(len(set(rows)), 4)

    def test_reviewed_projection_payload_fails_closed_when_forged(self):
        ir = compiled_binding_ir((("bhsa", "broader", ("undercoverage",), True),))
        binding = dict(ir.semantic_index)[noun_semantic_key()][0]
        payload = binding.projection_semantic_payload
        self.assertIsInstance(payload, str)
        decoded = json.loads(payload)

        malformed_payloads = (
            None,
            "{",
            json.dumps(decoded, sort_keys=True, indent=2),
            canonical_json_bytes(
                {
                    "projection_id": binding.projection_id,
                    "assessment": binding.assessment,
                }
            ).decode("utf-8"),
        )
        for forged in malformed_payloads:
            with self.subTest(forged=forged):
                bad = replace_semantic_binding(
                    ir,
                    "bhsa",
                    projection_semantic_payload=forged,
                )
                assert_problem(
                    self,
                    "invalid_compiled_ir",
                    self.resolve,
                    bad,
                    accept_losses=("undercoverage",),
                )

    def test_compiled_approximation_is_defensively_validated_and_digest_bound(self):
        ir = compiled_binding_ir((("bhsa", "broader", ("undercoverage",), True),))
        binding = dict(ir.semantic_index)[noun_semantic_key()][0]
        approximation = binding.approximation
        self.assertIsNotNone(approximation)

        forged_cases = (
            "not-an-approximation",
            replace(approximation, status="provisional"),
            replace(approximation, eligible=1),
            replace(approximation, losses=("overcoverage",)),
            replace(approximation, evidence=("bad-evidence",)),
            # Structurally legal, but no longer the reviewed semantic projection.
            replace(approximation, eligible=False),
            replace(approximation, rationale="forged but structurally valid"),
            replace(approximation, review_id="review:forged"),
        )
        for forged in forged_cases:
            with self.subTest(forged=forged):
                bad = replace_semantic_binding(ir, "bhsa", approximation=forged)
                assert_problem(
                    self,
                    "invalid_compiled_ir",
                    self.resolve,
                    bad,
                    accept_losses=("undercoverage", "overcoverage"),
                )

    def test_exact_and_related_rows_cannot_carry_forged_approximation(self):
        valid = compiled_binding_ir((("bhsa", "broader", ("undercoverage",), True),))
        approx = dict(valid.semantic_index)[noun_semantic_key()][0].approximation
        self.assertIsNotNone(approx)

        exact = compiled_noun_ir(("bhsa",))
        forged_exact = replace_semantic_binding(exact, "bhsa", approximation=approx)
        assert_problem(
            self,
            "invalid_compiled_ir",
            self.resolve,
            forged_exact,
            accept_losses=("undercoverage",),
        )

        related = compile_semantic_ir(
            (validated_assessment_bundle("bhsa", "related"),)
        )
        forged_related = replace_semantic_binding(related, "bhsa", approximation=approx)
        assert_problem(
            self,
            "invalid_compiled_ir",
            self.resolve,
            forged_related,
            accept_losses=("undercoverage",),
        )

    def test_canonical_request_ordering_and_acceptance_are_fingerprint_bound(self):
        close = compiled_binding_ir(
            (("syriac", "close", ("undercoverage", "overcoverage"), True),
             ("bhsa", "close", ("undercoverage", "overcoverage"), True))
        )
        forward = self.resolve(
            close,
            corpora=("syriac", "bhsa"),
            accept_losses=("undercoverage", "overcoverage"),
        )
        reverse = self.resolve(
            close,
            corpora=("bhsa", "syriac"),
            accept_losses=("overcoverage", "undercoverage"),
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(forward.request.corpora, ("bhsa", "syriac"))
        self.assertEqual(
            forward.request.accept_losses,
            tuple(sorted(("undercoverage", "overcoverage"))),
        )

        exact = compiled_noun_ir(("bhsa",))
        no_permission = self.resolve(exact)
        extra_permission = self.resolve(exact, accept_losses=("undercoverage",))
        self.assertEqual(
            no_permission.plans[0].plan_fingerprint,
            extra_permission.plans[0].plan_fingerprint,
        )
        self.assertNotEqual(
            no_permission.resolution_fingerprint,
            extra_permission.resolution_fingerprint,
        )

    def test_multicorpus_comparison_states_follow_loss_shapes(self):
        exact = compiled_noun_ir(("bhsa", "syriac", "extrabiblical"))
        exact_result = self.resolve(
            exact,
            corpora=("syriac", "bhsa", "extrabiblical"),
            accept_losses=("undercoverage",),
        )
        self.assertEqual(exact_result.comparison_state, "exactly-comparable")

        uniform = compiled_binding_ir(
            (
                ("bhsa", "exact", (), True),
                ("syriac", "broader", ("undercoverage",), True),
                ("extrabiblical", "broader", ("undercoverage",), True),
            )
        )
        uniform_result = self.resolve(
            uniform,
            corpora=("extrabiblical", "bhsa", "syriac"),
            accept_losses=("undercoverage",),
        )
        self.assertEqual(
            uniform_result.comparison_state,
            "approximately-comparable",
        )
        self.assertEqual(uniform_result.losses, ("undercoverage",))

        heterogeneous = compiled_binding_ir(
            (
                ("bhsa", "broader", ("undercoverage",), True),
                ("syriac", "narrower", ("overcoverage",), True),
            )
        )
        hetero_result = self.resolve(
            heterogeneous,
            corpora=("syriac", "bhsa"),
            accept_losses=("undercoverage", "overcoverage"),
        )
        self.assertEqual(hetero_result.comparison_state, "heterogeneous-loss")
        self.assertEqual(
            set(hetero_result.losses),
            {"undercoverage", "overcoverage"},
        )


@unittest.skipUnless(
    HAS_APPROXIMATE_RESOLVER,
    "RED sentinel owns approximate resolver API absence",
)
class I020ApproximateConjunctionResolutionTests(unittest.TestCase):
    def resolve(self, ir, request):
        return tfont.semantic_resolve_approximate_conjunction(
            ir,
            request,
            prerequisites_for(tfont, ir),
        )

    def test_exact_plus_broader_unions_undercoverage(self):
        mutations = {
            corpus: {
                "Plural": ("broader", ("undercoverage",), True),
            }
            for corpus in ("bhsa", "syriac", "extrabiblical")
        }
        ir, _contexts = mutated_production_conjunction(mutations)
        result = self.resolve(
            ir,
            approximate_conjunction_request(
                tfont,
                "Plural",
                "Noun",
                accept_losses=("undercoverage",),
            ),
        )
        self.assertEqual(result.losses, ("undercoverage",))
        self.assertEqual(result.comparison_state, "approximately-comparable")
        self.assertEqual(len(result.loss_records), 3)

    def test_broader_plus_narrower_unions_both_losses_per_corpus(self):
        mutations = {
            corpus: {
                "Noun": ("broader", ("undercoverage",), True),
                "Plural": ("narrower", ("overcoverage",), True),
            }
            for corpus in ("bhsa", "syriac", "extrabiblical")
        }
        ir, _contexts = mutated_production_conjunction(mutations)
        result = self.resolve(
            ir,
            approximate_conjunction_request(
                tfont,
                "Noun",
                "Plural",
                accept_losses=("undercoverage", "overcoverage"),
            ),
        )
        self.assertEqual(
            set(result.losses),
            {"undercoverage", "overcoverage"},
        )
        self.assertEqual(result.comparison_state, "approximately-comparable")
        self.assertEqual(len(result.loss_records), 6)

    def test_refused_required_atom_fails_whole_conjunction(self):
        mutations = {
            corpus: {
                "Plural": ("broader", ("undercoverage",), False),
            }
            for corpus in ("bhsa", "syriac", "extrabiblical")
        }
        ir, _contexts = mutated_production_conjunction(mutations)
        assert_problem(
            self,
            "approximation_not_authorized",
            self.resolve,
            ir,
            approximate_conjunction_request(
                tfont,
                "Noun",
                "Plural",
                accept_losses=("undercoverage",),
            ),
        )

    def test_key_and_corpus_input_order_do_not_change_conjunction_result(self):
        mutations = {
            corpus: {
                "Plural": ("broader", ("undercoverage",), True),
            }
            for corpus in ("bhsa", "syriac", "extrabiblical")
        }
        ir, _contexts = mutated_production_conjunction(mutations)
        forward = self.resolve(
            ir,
            approximate_conjunction_request(
                tfont,
                "Noun",
                "Plural",
                corpora=("syriac", "bhsa", "extrabiblical"),
                accept_losses=("undercoverage",),
            ),
        )
        reverse = self.resolve(
            ir,
            approximate_conjunction_request(
                tfont,
                "Plural",
                "Noun",
                corpora=("extrabiblical", "syriac", "bhsa"),
                accept_losses=("undercoverage",),
            ),
        )
        self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()
