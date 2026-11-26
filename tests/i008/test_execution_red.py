from __future__ import annotations

from dataclasses import replace
import unittest

import ontotf
from tests.i006._fixtures import compiled_noun_ir
from tests.i008._fixtures import (
    FakeLoadedApi,
    IndexNode,
    compiled_executable_noun_ir,
    duplicate_variant_ir,
    loaded_context,
    request,
)


@unittest.skipUnless(
    hasattr(ontotf, "execute_exact_semantic"),
    "RED: I-008 execution surface is not implemented yet",
)
class I008ExecutionBehaviorTests(unittest.TestCase):
    def execute_one(self, api, *, dependency_kind="native-value-present"):
        ir = compiled_executable_noun_ir(("bhsa",), dependency_kind=dependency_kind)
        context = loaded_context(ontotf, ir, "bhsa", api)
        return ontotf.execute_exact_semantic(ir, request(ontotf, ("bhsa",)), (context,))

    def test_bhsa_exact_value_predicate_returns_word_nouns_only(self):
        api = FakeLoadedApi(
            values={1: "subs", 2: "verb", 3: "subs"},
            node_types={1: "word", 2: "word", 3: "phrase"},
        )
        result = self.execute_one(api)
        self.assertEqual(result.execution_contract, "ontotf-exact-execution-v1")
        self.assertEqual(result.resolution.comparison_state, "exactly-comparable")
        self.assertEqual(result.corpora[0].corpus_id, "bhsa")
        self.assertEqual(result.corpora[0].nodes, (1,))
        self.assertEqual(result.corpora[0].plan.native_execution_binding.value, "subs")
        self.assertEqual(
            result.corpora[0].plan.native_execution_binding.execution_shape,
            "value-predicate",
        )
        self.assertEqual(api.load_calls, 0)
        self.assertEqual(api.F.sp.s_calls, 1)

    def test_three_corpora_are_deterministic_and_keep_fresh_provenance(self):
        ir = compiled_executable_noun_ir()
        apis = {
            "bhsa": FakeLoadedApi(values={11: "subs"}, node_types={11: "word"}),
            "syriac": FakeLoadedApi(values={22: "subs"}, node_types={22: "word"}),
            "extrabiblical": FakeLoadedApi(values={33: "subs"}, node_types={33: "word"}),
        }
        contexts = tuple(
            loaded_context(ontotf, ir, corpus, apis[corpus])
            for corpus in ("syriac", "extrabiblical", "bhsa")
        )
        result = ontotf.execute_exact_semantic(
            ir,
            request(ontotf, ("syriac", "bhsa", "extrabiblical")),
            contexts,
        )
        self.assertEqual(
            tuple(row.corpus_id for row in result.corpora),
            ("bhsa", "extrabiblical", "syriac"),
        )
        self.assertEqual(
            tuple(row.nodes for row in result.corpora),
            ((11,), (33,), (22,)),
        )
        self.assertEqual(
            tuple(row.plan.corpus_id for row in result.corpora),
            tuple(row.corpus_id for row in result.corpora),
        )
        self.assertTrue(all(row.runtime_report.report_fingerprint for row in result.corpora))
        self.assertTrue(all(row.plan.plan_fingerprint for row in result.corpora))
        self.assertTrue(result.resolution.resolution_fingerprint)

    def test_feature_present_control_can_authorize_successful_empty_result(self):
        api = FakeLoadedApi(values={1: "verb"}, node_types={1: "word"}, selected=())
        result = self.execute_one(api, dependency_kind="feature-present")
        self.assertEqual(result.corpora[0].nodes, ())
        self.assertEqual(api.F.sp.s_calls, 1)

    def test_result_order_is_preserved_not_numeric_sorted(self):
        api = FakeLoadedApi(
            values={9: "subs", 2: "subs"},
            node_types={9: "word", 2: "word"},
            selected=(9, 2),
        )
        result = self.execute_one(api)
        self.assertEqual(result.corpora[0].nodes, (9, 2))

    def test_index_protocol_nodes_are_normalized_to_builtin_ints(self):
        api = FakeLoadedApi(
            values={7: "subs"},
            node_types={7: "word"},
            selected=(IndexNode(7),),
        )
        result = self.execute_one(api)
        self.assertEqual(result.corpora[0].nodes, (7,))
        self.assertIs(type(result.corpora[0].nodes[0]), int)

    def test_boolean_float_and_duplicate_normalized_nodes_fail_closed(self):
        for selected in ((True,), (7.0,), (7, IndexNode(7))):
            with self.subTest(selected=selected):
                api = FakeLoadedApi(
                    values={1: "subs", 7: "subs"},
                    node_types={1: "word", 7: "word"},
                    selected=selected,
                )
                with self.assertRaises(ontotf.ExactExecutionError) as caught:
                    self.execute_one(api)
                self.assertEqual(caught.exception.problem.category, "invalid_result_nodes")

    def test_feature_removed_after_runtime_evaluation_fails_without_autoload(self):
        api = FakeLoadedApi(
            values={1: "subs"},
            node_types={1: "word"},
            fall_sequence=(("otype", "sp"), ("otype",)),
        )
        with self.assertRaises(ontotf.ExactExecutionError) as caught:
            self.execute_one(api)
        self.assertEqual(caught.exception.problem.category, "feature_not_loaded")
        self.assertEqual(api.F.sp.s_calls, 0)
        self.assertEqual(api.load_calls, 0)

    def test_selector_and_otype_failures_become_loaded_api_errors(self):
        cases = (
            FakeLoadedApi(values={1: "subs"}, node_types={1: "word"}, raise_on_s=True),
            FakeLoadedApi(
                values={1: "subs"},
                node_types={1: "word"},
                selected=(1,),
                raise_on_otype_v=True,
            ),
        )
        for api in cases:
            with self.subTest(api=api):
                with self.assertRaises(ontotf.ExactExecutionError) as caught:
                    self.execute_one(api)
                self.assertEqual(caught.exception.problem.category, "loaded_api_unavailable")
                self.assertEqual(api.load_calls, 0)

    def test_old_exact_plan_without_explicit_execution_shape_is_not_executable(self):
        ir = compiled_noun_ir(("bhsa",))
        api = FakeLoadedApi(values={1: "subs"}, node_types={1: "word"})
        context = loaded_context(ontotf, ir, "bhsa", api)
        with self.assertRaises(ontotf.ExactExecutionError) as caught:
            ontotf.execute_exact_semantic(ir, request(ontotf, ("bhsa",)), (context,))
        self.assertEqual(caught.exception.problem.category, "unsupported_native_binding")
        self.assertEqual(api.F.sp.s_calls, 0)

    def test_duplicate_contexts_fail_before_result_access(self):
        ir = compiled_executable_noun_ir(("bhsa",))
        api = FakeLoadedApi(values={1: "subs"}, node_types={1: "word"})
        context = loaded_context(ontotf, ir, "bhsa", api)
        with self.assertRaises(ontotf.ExactExecutionError) as caught:
            ontotf.execute_exact_semantic(
                ir,
                request(ontotf, ("bhsa",)),
                (context, context),
            )
        self.assertEqual(caught.exception.problem.category, "duplicate_execution_context")
        self.assertEqual(api.F.sp.s_calls, 0)

    def test_missing_context_fails_before_result_access(self):
        ir = compiled_executable_noun_ir(("bhsa",))
        with self.assertRaises(ontotf.ExactExecutionError) as caught:
            ontotf.execute_exact_semantic(ir, request(ontotf, ("bhsa",)), ())
        self.assertEqual(caught.exception.problem.category, "missing_execution_context")

    def test_duplicate_runtime_variant_fails_before_prerequisite_or_result_access(self):
        ir = compiled_executable_noun_ir(("bhsa",))
        forged = duplicate_variant_ir(ir)
        api = FakeLoadedApi(values={1: "subs"}, node_types={1: "word"})
        context = loaded_context(ontotf, ir, "bhsa", api)
        with self.assertRaises(ontotf.ExactExecutionError) as caught:
            ontotf.execute_exact_semantic(forged, request(ontotf, ("bhsa",)), (context,))
        self.assertEqual(caught.exception.problem.category, "ambiguous_runtime_variant")
        self.assertEqual(api.fall_calls, 0)
        self.assertEqual(api.F.sp.s_calls, 0)

    def test_malformed_variant_rows_fail_deterministically_before_runtime_access(self):
        ir = compiled_executable_noun_ir(("bhsa",))
        forged = replace(ir, variants=("not-a-variant",))
        api = FakeLoadedApi(values={1: "subs"}, node_types={1: "word"})
        context = loaded_context(ontotf, ir, "bhsa", api)
        with self.assertRaises(ontotf.ExactExecutionError) as caught:
            ontotf.execute_exact_semantic(forged, request(ontotf, ("bhsa",)), (context,))
        self.assertEqual(caught.exception.problem.category, "invalid_compiled_ir")
        self.assertEqual(api.fall_calls, 0)
        self.assertEqual(api.F.sp.s_calls, 0)

    def test_incompatible_runtime_state_blocks_result_selector(self):
        api = FakeLoadedApi(values={1: "verb"}, node_types={1: "word"})
        with self.assertRaises(ontotf.SemanticResolutionError):
            self.execute_one(api)
        self.assertEqual(api.F.sp.s_calls, 0)

    def test_unavailable_runtime_observation_blocks_result_selector(self):
        api = FakeLoadedApi(
            values={1: "subs"},
            node_types={1: "word"},
            raise_on_fall=True,
        )
        with self.assertRaises(ontotf.SemanticResolutionError):
            self.execute_one(api)
        self.assertEqual(api.F.sp.s_calls, 0)
        self.assertEqual(api.load_calls, 0)


if __name__ == "__main__":
    unittest.main()
