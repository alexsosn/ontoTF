from __future__ import annotations

import unittest
from dataclasses import replace

import tfont

from tests.i006._fixtures import noun_semantic_key
from tests.i023._fixtures import approximate_request, semantic_request
from tests.i025._fixtures import (
    ObservableValuedEdgeFeature,
    compiled_authority_predicate_ir,
    compiled_mixed_conjunction_predicate_ir,
    compiled_predicate_ir,
    compiled_reference_predicate_ir,
    predicate_api,
    predicate_context,
    predicate_feature,
    predicate_observation,
)


SAFE_MAX = 2**53 - 1


def category(error: BaseException) -> str:
    return getattr(getattr(error, "problem", None), "category", "")


class I025RuntimeExecutionRedTests(unittest.TestCase):
    def test_loaded_observation_reports_complete_string_domain_and_caches_scan(self):
        ir = compiled_predicate_ir()
        feature = predicate_feature()
        observation = predicate_observation(
            tfont,
            ir,
            predicate_api(feature=feature),
        )
        first = observation.edge_values(
            "bhsa-tf",
            "witness_resolution",
            "line",
            "fragment",
        )
        second = observation.edge_values(
            "bhsa-tf",
            "witness_resolution",
            "line",
            "fragment",
        )
        self.assertEqual(first, ("complete", "str", ("ambiguous", "unique"), 0))
        self.assertEqual(second, first)
        self.assertEqual(feature.item_calls, 1)

    def test_loaded_observation_preserves_integer_domain_and_missing_count(self):
        ir = compiled_predicate_ir(
            value_type="int",
            match_values=(1,),
            domain_values=(1, 2),
        )
        observation = predicate_observation(tfont, ir, value_type="int")
        self.assertEqual(
            observation.edge_values(
                "bhsa-tf",
                "quality_score",
                "line",
                "fragment",
            ),
            ("complete", "int", (1, 2), 1),
        )

    def test_loaded_observation_rejects_malformed_global_edge_values(self):
        ir = compiled_predicate_ir()
        cases = (
            ObservableValuedEdgeFeature(
                {1: ((10, "ambiguous"),)},
                item_data={1: {10: "ambiguous", 99: None}},
            ),
            ObservableValuedEdgeFeature(
                {1: ((10, "ambiguous"),)},
                do_values=False,
            ),
            ObservableValuedEdgeFeature(
                {1: ((10, "ambiguous"),)},
                meta={"valueType": "int"},
            ),
            ObservableValuedEdgeFeature(
                {1: ((10, "ambiguous"),)},
                raise_on_items=True,
            ),
        )
        for feature in cases:
            with self.subTest(feature=feature):
                observation = predicate_observation(
                    tfont,
                    ir,
                    predicate_api(feature=feature),
                )
                state = observation.edge_values(
                    "bhsa-tf",
                    "witness_resolution",
                    "line",
                    "fragment",
                )
                self.assertEqual(state[0], "unknown")

    def test_runtime_rejects_noncanonical_custom_edge_domain_observation(self):
        ir = compiled_predicate_ir()
        base = predicate_observation(tfont, ir)

        class ReorderedObservation:
            parent_manifest_digest = base.parent_manifest_digest

            def __getattr__(self, name):
                return getattr(base, name)

            def edge_values(self, component_id, edge, source_node_type, target_node_type):
                return ("complete", "str", ("unique", "ambiguous"), 0)

        report = tfont.evaluate_runtime_prerequisites(
            ir.variants[0],
            ReorderedObservation(),
            source_contract="i025-test",
        )
        edge_row = tuple(
            row
            for row in report.dependency_results
            if row.dependency_id.endswith(":domain")
        )[0]
        self.assertEqual(edge_row.result, "unknown")
        self.assertEqual(report.compatibility_state, "unverified")

    def test_runtime_closed_domain_fails_on_unexpected_value(self):
        ir = compiled_predicate_ir()
        feature = ObservableValuedEdgeFeature(
            {1: ((10, "ambiguous"),)},
            item_data={1: {10: "ambiguous", 11: "other"}},
        )
        observation = predicate_observation(
            tfont,
            ir,
            predicate_api(feature=feature),
        )
        report = tfont.evaluate_runtime_prerequisites(
            ir.variants[0],
            observation,
            source_contract="i025-test",
        )
        edge_rows = tuple(
            row
            for row in report.dependency_results
            if row.dependency_id.endswith(":domain")
        )
        self.assertEqual(len(edge_rows), 1)
        self.assertEqual(edge_rows[0].result, "fail")
        self.assertEqual(report.compatibility_state, "incompatible")

    def test_runtime_reviewed_but_absent_value_is_compatible_and_fingerprinted(self):
        ir = compiled_predicate_ir()
        unique_only = ObservableValuedEdgeFeature(
            {1: ((11, "unique"),), 2: ()},
            incoming={11: ((1, "unique"),)},
        )
        observation = predicate_observation(
            tfont,
            ir,
            predicate_api(feature=unique_only),
        )
        report = tfont.evaluate_runtime_prerequisites(
            ir.variants[0],
            observation,
            source_contract="i025-test",
        )
        self.assertNotEqual(report.compatibility_state, "incompatible")
        edge_row = tuple(
            row
            for row in report.dependency_results
            if row.dependency_id.endswith(":domain")
        )[0]
        self.assertEqual(edge_row.result, "pass")

        other = predicate_observation(tfont, ir, predicate_api())
        other_report = tfont.evaluate_runtime_prerequisites(
            ir.variants[0],
            other,
            source_contract="i025-test",
        )
        self.assertNotEqual(report.report_fingerprint, other_report.report_fingerprint)

    def test_forged_v1_release_cannot_carry_edge_value_domain(self):
        ir = compiled_predicate_ir()
        variant = ir.variants[0]
        forged_signature = replace(
            variant.release_signature,
            dependency_contract_version=1,
        )
        forged = replace(
            variant,
            release_signature=forged_signature,
            dependency_contract_version=1,
        )
        observation = predicate_observation(tfont, ir)
        with self.assertRaises(tfont.RuntimeEvaluationError):
            tfont.evaluate_runtime_prerequisites(
                forged,
                observation,
                source_contract="i025-test",
            )

    def test_exact_singleton_filter_keeps_only_matching_evidence(self):
        ir = compiled_predicate_ir()
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (predicate_context(tfont, ir),),
        ).corpora[0]
        self.assertEqual(result.nodes, (10,))
        evidence = result.edge_path_evidence
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence.final_nodes, (10,))
        self.assertEqual(
            tuple(
                (row.source_node, row.target_node, row.value)
                for row in evidence.layers[0].observations
            ),
            ((1, 10, "ambiguous"),),
        )

    def test_exact_finite_set_filter_is_stable_or_membership(self):
        ir = compiled_predicate_ir(match_values=("unique", "ambiguous"))
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (predicate_context(tfont, ir),),
        ).corpora[0]
        self.assertEqual(result.nodes, (10, 11))
        self.assertEqual(
            tuple(row.value for row in result.edge_path_evidence.layers[0].observations),
            ("ambiguous", "unique", "unique"),
        )

    def test_incoming_filter_keeps_native_orientation(self):
        ir = compiled_predicate_ir(direction="incoming")
        api = predicate_api(selections={"fragment": (10, 11)})
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (predicate_context(tfont, ir, api),),
        ).corpora[0]
        self.assertEqual(result.nodes, (1,))
        observations = result.edge_path_evidence.layers[0].observations
        self.assertEqual(
            tuple((row.source_node, row.target_node, row.value) for row in observations),
            ((1, 10, "ambiguous"),),
        )

    def test_integer_none_never_matches_but_present_integer_does(self):
        ir = compiled_predicate_ir(
            value_type="int",
            match_values=(1,),
            domain_values=(1, 2),
        )
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (predicate_context(tfont, ir, value_type="int"),),
        ).corpora[0]
        self.assertEqual(result.nodes, (10,))
        observations = result.edge_path_evidence.layers[0].observations
        self.assertEqual(
            tuple((row.target_node, row.value_present, row.value) for row in observations),
            ((10, True, 1),),
        )

    def test_reviewed_empty_string_is_matchable(self):
        ir = compiled_predicate_ir(
            match_values=("",),
            domain_values=("", "unique"),
        )
        feature = ObservableValuedEdgeFeature(
            {1: ((10, ""), (11, "unique")), 2: ()},
            incoming={10: ((1, ""),), 11: ((1, "unique"),)},
        )
        api = predicate_api(feature=feature)
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (predicate_context(tfont, ir, api),),
        ).corpora[0]
        self.assertEqual(result.nodes, (10,))
        self.assertEqual(result.edge_path_evidence.layers[0].observations[0].value, "")

    def test_off_domain_and_in_domain_nonmatches_do_not_enter_evidence(self):
        ir = compiled_predicate_ir()
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (predicate_context(tfont, ir),),
        ).corpora[0]
        self.assertEqual(result.nodes, (10,))
        self.assertTrue(
            all(row.target_node != 99 for row in result.edge_path_evidence.layers[0].observations)
        )
        self.assertTrue(
            all(row.value != "unique" for row in result.edge_path_evidence.layers[0].observations)
        )

    def test_oversized_in_domain_nonmatch_is_filtered_before_evidence_bound(self):
        ir = compiled_predicate_ir()
        oversized = SAFE_MAX + 1
        feature = ObservableValuedEdgeFeature(
            {1: ((oversized, "unique"), (10, "ambiguous")), 2: ()},
            incoming={
                oversized: ((1, "unique"),),
                10: ((1, "ambiguous"),),
            },
        )
        api = predicate_api(feature=feature)
        api.node_types[oversized] = "fragment"
        api.F.otype.node_types[oversized] = "fragment"
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (predicate_context(tfont, ir, api),),
        ).corpora[0]
        self.assertEqual(result.nodes, (10,))

    def test_duplicate_raw_neighbors_still_fail_before_filtering(self):
        ir = compiled_predicate_ir()
        feature = ObservableValuedEdgeFeature(
            {1: ((10, "unique"), (10, "unique")), 2: ()},
        )
        api = predicate_api(feature=feature)
        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                ir,
                semantic_request(tfont),
                (predicate_context(tfont, ir, api),),
            )
        self.assertEqual(category(raised.exception), "invalid_result_nodes")

    def test_filter_to_empty_is_valid_and_keeps_layered_evidence(self):
        ir = compiled_predicate_ir()
        feature = ObservableValuedEdgeFeature(
            {1: ((11, "unique"),), 2: ((10, "unique"),)},
            incoming={
                11: ((1, "unique"),),
                10: ((2, "unique"),),
            },
        )
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (predicate_context(tfont, ir, predicate_api(feature=feature)),),
        ).corpora[0]
        self.assertEqual(result.nodes, ())
        self.assertEqual(result.edge_path_evidence.final_nodes, ())
        self.assertEqual(result.edge_path_evidence.layers[0].observations, ())

    def test_exact_approximate_and_reference_surfaces_share_filter(self):
        ir = compiled_predicate_ir()
        exact = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (predicate_context(tfont, ir),),
        )
        approximate = tfont.execute_approximate_semantic(
            ir,
            approximate_request(tfont),
            (predicate_context(tfont, ir),),
        )
        self.assertEqual(exact.corpora[0].nodes, (10,))
        self.assertEqual(approximate.corpora[0].nodes, (10,))

        authority_ir = compiled_authority_predicate_ir()
        authority_key = authority_ir.authority_index[0][0]
        authority = tfont.execute_exact_authority(
            authority_ir,
            tfont.AuthorityResolveRequest(key=authority_key, corpora=("bhsa",)),
            (predicate_context(tfont, authority_ir),),
        )
        self.assertEqual(authority.corpora[0].nodes, (10,))

        approximate_authority_ir = compiled_authority_predicate_ir(
            assessment="broader",
            losses=("undercoverage",),
        )
        approximate_key = approximate_authority_ir.authority_index[0][0]
        approximate_authority = tfont.execute_approximate_authority(
            approximate_authority_ir,
            tfont.ApproximateAuthorityResolveRequest(
                key=approximate_key,
                corpora=("bhsa",),
                accept_losses=("undercoverage",),
            ),
            (predicate_context(tfont, approximate_authority_ir),),
        )
        self.assertEqual(approximate_authority.corpora[0].nodes, (10,))

        refs_ir = compiled_reference_predicate_ir()
        identity_key = refs_ir.identity_index[0][0]
        identity = tfont.execute_identity(
            refs_ir,
            tfont.IdentityResolveRequest(
                authority_system=identity_key.authority_system,
                external_entity_id=identity_key.external_entity_id,
                corpora=("bhsa",),
            ),
            (predicate_context(tfont, refs_ir),),
        )
        identifier_key = refs_ir.identifier_index[0][0]
        identifier = tfont.execute_identifier(
            refs_ir,
            tfont.IdentifierResolveRequest(key=identifier_key, corpora=("bhsa",)),
            (predicate_context(tfont, refs_ir),),
        )
        self.assertEqual(identity.corpora[0].nodes, (10,))
        self.assertEqual(identifier.corpora[0].nodes, (10,))

    def test_exact_and_approximate_conjunction_use_filtered_nodes_and_aligned_evidence(self):
        ir = compiled_mixed_conjunction_predicate_ir()
        keys = (
            semantic_request(tfont).key,
            tfont.SemanticKey(
                profile_id="linguistic",
                capability_id="linguistic.part-of-speech",
                target="http://purl.org/olia/olia.owl#ProperNoun",
                formal_kind="class",
                semantic_role="annotation-value",
            ),
        )
        exact = tfont.execute_exact_conjunction(
            ir,
            tfont.SemanticConjunctionRequest(keys=keys, corpora=("bhsa",)),
            (predicate_context(tfont, ir),),
        ).corpora[0]
        self.assertEqual(exact.nodes, (10,))
        self.assertEqual(
            tuple(item is None for item in exact.constituent_edge_path_evidence),
            (False, True),
        )

        approximate = tfont.execute_approximate_conjunction(
            ir,
            tfont.ApproximateSemanticConjunctionRequest(
                keys=keys,
                corpora=("bhsa",),
                semantic_mode="approximate",
                accept_losses=(),
            ),
            (predicate_context(tfont, ir),),
        ).corpora[0]
        self.assertEqual(approximate.nodes, (10,))
        self.assertEqual(
            tuple(item is None for item in approximate.constituent_edge_path_evidence),
            (False, True),
        )

    def test_public_contract_tokens_remain_unchanged(self):
        self.assertEqual(tfont.EXACT_EXECUTION_CONTRACT, "tfont-exact-execution-v1")
        self.assertEqual(tfont.APPROXIMATE_EXECUTION_CONTRACT, "tfont-approximate-execution-v1")
        self.assertEqual(tfont.EDGE_PATH_EVIDENCE_CONTRACT, "tfont-edge-path-evidence-v1")
        self.assertEqual(tfont.RUNTIME_EVALUATION_CONTRACT, "tfont-runtime-evaluation-v1")


if __name__ == "__main__":
    unittest.main()
