from __future__ import annotations

from dataclasses import replace
import inspect
import unittest
from unittest.mock import patch

import tfont
from tfont.semantic_ir import compile_semantic_ir

from ._fixtures import (
    FakeLoadedApi,
    approximate_conjunction_request,
    approximate_request,
    compiled_binding_ir,
    executable_context,
    mutated_production_conjunction,
    problem_category,
    validated_value_set_approximation_bundle,
)


EXECUTION_API = (
    "APPROXIMATE_EXECUTION_CONTRACT",
    "APPROXIMATE_EXECUTION_RUNTIME_SOURCE_CONTRACT",
    "APPROXIMATE_CONJUNCTION_EXECUTION_CONTRACT",
    "ApproximateExecutionProblem",
    "ApproximateExecutionError",
    "ApproximateCorpusExecution",
    "ApproximateExecutionResult",
    "ApproximateConjunctionCorpusExecution",
    "ApproximateConjunctionExecutionResult",
    "execute_approximate_semantic",
    "execute_approximate_conjunction",
)
HAS_APPROXIMATE_EXECUTION = all(hasattr(tfont, name) for name in EXECUTION_API)


class I020ExecutionRedSentinelTests(unittest.TestCase):
    def test_public_approximate_execution_surface_exists(self):
        missing = [name for name in EXECUTION_API if not hasattr(tfont, name)]
        self.assertEqual(
            missing,
            [],
            f"RED: missing I-020 approximate execution API: {missing}",
        )


@unittest.skipUnless(
    HAS_APPROXIMATE_EXECUTION,
    "RED sentinel owns approximate execution API absence",
)
class I020ApproximateExecutionTests(unittest.TestCase):
    def test_public_executors_do_not_accept_caller_supplied_plan(self):
        self.assertEqual(
            tuple(inspect.signature(tfont.execute_approximate_semantic).parameters),
            ("ir", "request", "contexts"),
        )
        self.assertEqual(
            tuple(inspect.signature(tfont.execute_approximate_conjunction).parameters),
            ("ir", "request", "contexts"),
        )

    def test_reviewed_broader_executes_scalar_predicate_with_fresh_runtime_report(self):
        ir = compiled_binding_ir(
            (("bhsa", "broader", ("undercoverage",), True),),
            executable=True,
        )
        api = FakeLoadedApi(
            values={1: "subs", 2: "verb", 3: "subs"},
            node_types={1: "word", 2: "word", 3: "phrase"},
        )
        context = executable_context(tfont, ir, "bhsa", api)
        result = tfont.execute_approximate_semantic(
            ir,
            approximate_request(
                tfont,
                accept_losses=("undercoverage",),
            ),
            (context,),
        )

        self.assertEqual(result.execution_contract, tfont.APPROXIMATE_EXECUTION_CONTRACT)
        self.assertEqual(result.resolution.losses, ("undercoverage",))
        self.assertEqual(result.corpora[0].nodes, (1,))
        self.assertEqual(result.corpora[0].plan.assessment, "broader")
        self.assertEqual(result.corpora[0].plan.losses, ("undercoverage",))
        self.assertEqual(
            result.corpora[0].runtime_report.source_contract,
            tfont.APPROXIMATE_EXECUTION_RUNTIME_SOURCE_CONTRACT,
        )
        self.assertEqual(api.F.sp.s_calls, 1)
        self.assertEqual(api.load_calls, 0)

    def test_exact_binding_through_approximate_execution_has_no_loss(self):
        ir = compiled_binding_ir(
            (("bhsa", "exact", (), True),),
            executable=True,
        )
        api = FakeLoadedApi(
            values={1: "subs", 2: "verb"},
            node_types={1: "word", 2: "word"},
        )
        context = executable_context(tfont, ir, "bhsa", api)
        result = tfont.execute_approximate_semantic(
            ir,
            approximate_request(
                tfont,
                accept_losses=("undercoverage", "overcoverage"),
            ),
            (context,),
        )
        self.assertEqual(result.corpora[0].nodes, (1,))
        self.assertEqual(result.resolution.losses, ())
        self.assertEqual(result.resolution.loss_records, ())
        self.assertEqual(result.corpora[0].plan.assessment, "exact")
        self.assertIsNone(result.corpora[0].plan.loss_record)

    def test_value_set_predicate_executes_all_reviewed_values(self):
        ir = compile_semantic_ir(
            (validated_value_set_approximation_bundle("bhsa"),)
        )
        api = FakeLoadedApi(
            values={1: "subs", 2: "nmpr", 3: "verb", 4: "subs"},
            node_types={1: "word", 2: "word", 3: "word", 4: "phrase"},
        )
        context = executable_context(tfont, ir, "bhsa", api)
        result = tfont.execute_approximate_semantic(
            ir,
            approximate_request(tfont, accept_losses=("undercoverage",)),
            (context,),
        )
        self.assertEqual(result.corpora[0].nodes, (1, 2))
        self.assertEqual(
            result.corpora[0].plan.native_execution_binding.execution_shape,
            "value-set-predicate",
        )

    def test_unsupported_native_shape_is_approximate_execution_error(self):
        ir = compiled_binding_ir(
            (("bhsa", "broader", ("undercoverage",), True),),
            executable=False,
        )
        api = FakeLoadedApi(
            values={1: "subs"},
            node_types={1: "word"},
        )
        context = executable_context(tfont, ir, "bhsa", api)
        with self.assertRaises(tfont.ApproximateExecutionError) as raised:
            tfont.execute_approximate_semantic(
                ir,
                approximate_request(tfont, accept_losses=("undercoverage",)),
                (context,),
            )
        self.assertEqual(
            raised.exception.problem.category,
            "unsupported_native_binding",
        )
        self.assertEqual(api.F.sp.s_calls, 0)

    def test_shared_exact_execution_failures_are_translated_without_context_loss(self):
        ir = compiled_binding_ir(
            (("bhsa", "broader", ("undercoverage",), True),),
            executable=True,
        )
        api = FakeLoadedApi(
            values={1: "subs"},
            node_types={1: "word"},
            raise_on_s=True,
        )
        context = executable_context(tfont, ir, "bhsa", api)
        with self.assertRaises(tfont.ApproximateExecutionError) as raised:
            tfont.execute_approximate_semantic(
                ir,
                approximate_request(tfont, accept_losses=("undercoverage",)),
                (context,),
            )
        problem = raised.exception.problem
        self.assertEqual(problem.category, "loaded_api_unavailable")
        self.assertEqual(problem.corpus_id, "bhsa")
        self.assertEqual(problem.component_id, "bhsa-tf")
        self.assertNotIsInstance(raised.exception, tfont.ExactExecutionError)

    def test_missing_context_uses_approximate_error_surface(self):
        ir = compiled_binding_ir(
            (("bhsa", "broader", ("undercoverage",), True),),
            executable=True,
        )
        with self.assertRaises(tfont.ApproximateExecutionError) as raised:
            tfont.execute_approximate_semantic(
                ir,
                approximate_request(tfont, accept_losses=("undercoverage",)),
                (),
            )
        self.assertEqual(
            raised.exception.problem.category,
            "missing_execution_context",
        )

    def test_runtime_dependency_failure_blocks_native_selector(self):
        ir = compiled_binding_ir(
            (("bhsa", "broader", ("undercoverage",), True),),
            executable=True,
        )
        api = FakeLoadedApi(
            values={1: "verb"},
            node_types={1: "word"},
        )
        context = executable_context(tfont, ir, "bhsa", api)
        with self.assertRaises(tfont.SemanticResolutionError):
            tfont.execute_approximate_semantic(
                ir,
                approximate_request(tfont, accept_losses=("undercoverage",)),
                (context,),
            )
        self.assertEqual(api.F.sp.s_calls, 0)

    def test_feature_removed_after_fresh_runtime_evaluation_fails_before_query(self):
        ir = compiled_binding_ir(
            (("bhsa", "broader", ("undercoverage",), True),),
            executable=True,
        )
        api = FakeLoadedApi(
            values={1: "subs"},
            node_types={1: "word"},
            fall_sequence=(("otype", "sp"), ("otype",)),
        )
        context = executable_context(tfont, ir, "bhsa", api)
        with self.assertRaises(tfont.ApproximateExecutionError) as raised:
            tfont.execute_approximate_semantic(
                ir,
                approximate_request(tfont, accept_losses=("undercoverage",)),
                (context,),
            )
        self.assertEqual(raised.exception.problem.category, "feature_not_loaded")
        self.assertEqual(api.F.sp.s_calls, 0)
        self.assertEqual(api.load_calls, 0)


@unittest.skipUnless(
    HAS_APPROXIMATE_EXECUTION,
    "RED sentinel owns approximate execution API absence",
)
class I020ApproximateConjunctionExecutionTests(unittest.TestCase):
    def test_exact_plus_broader_conjunction_intersects_and_retains_losses(self):
        mutations = {
            corpus: {
                "Plural": ("broader", ("undercoverage",), True),
            }
            for corpus in ("bhsa", "syriac", "extrabiblical")
        }
        ir, contexts = mutated_production_conjunction(mutations)
        result = tfont.execute_approximate_conjunction(
            ir,
            approximate_conjunction_request(
                tfont,
                "Plural",
                "Noun",
                accept_losses=("undercoverage",),
            ),
            contexts,
        )
        self.assertEqual(
            result.execution_contract,
            tfont.APPROXIMATE_CONJUNCTION_EXECUTION_CONTRACT,
        )
        self.assertEqual(result.resolution.losses, ("undercoverage",))
        self.assertEqual(
            [(row.corpus_id, row.nodes) for row in result.corpora],
            [
                ("bhsa", (2, 4)),
                ("extrabiblical", (2, 4)),
                ("syriac", (2, 4)),
            ],
        )
        self.assertTrue(
            all(
                row.runtime_report.source_contract
                == tfont.APPROXIMATE_EXECUTION_RUNTIME_SOURCE_CONTRACT
                for row in result.corpora
            )
        )

    def test_broader_plus_narrower_conjunction_retains_both_loss_directions(self):
        mutations = {
            corpus: {
                "Noun": ("broader", ("undercoverage",), True),
                "Plural": ("narrower", ("overcoverage",), True),
            }
            for corpus in ("bhsa", "syriac", "extrabiblical")
        }
        ir, contexts = mutated_production_conjunction(mutations)
        result = tfont.execute_approximate_conjunction(
            ir,
            approximate_conjunction_request(
                tfont,
                "Noun",
                "Plural",
                accept_losses=("undercoverage", "overcoverage"),
            ),
            contexts,
        )
        self.assertEqual(
            set(result.resolution.losses),
            {"undercoverage", "overcoverage"},
        )
        self.assertEqual(
            result.resolution.comparison_state,
            "approximately-comparable",
        )
        self.assertEqual(len(result.resolution.loss_records), 6)

    def test_conjunction_node_domain_safety_is_preserved(self):
        mutations = {
            "bhsa": {
                "Plural": ("broader", ("undercoverage",), True),
            }
        }
        ir, contexts = mutated_production_conjunction(mutations)
        request = approximate_conjunction_request(
            tfont,
            "Noun",
            "Plural",
            corpora=("bhsa",),
            accept_losses=("undercoverage",),
        )
        baseline = tfont.execute_approximate_conjunction(ir, request, contexts)
        resolution = baseline.resolution
        first, second = resolution.resolutions
        original = second.plans[0]
        altered_binding = replace(
            original.native_execution_binding,
            node_type="lex",
        )
        altered_plan = replace(
            original,
            native_execution_binding=altered_binding,
        )
        altered_second = replace(second, plans=(altered_plan,))
        altered_resolution = replace(
            resolution,
            resolutions=(first, altered_second),
        )

        with patch.object(
            tfont.semantic_execution,
            "semantic_resolve_approximate_conjunction",
            return_value=altered_resolution,
        ):
            with self.assertRaises(tfont.ApproximateExecutionError) as raised:
                tfont.execute_approximate_conjunction(ir, request, contexts)
        self.assertEqual(
            raised.exception.problem.category,
            "incompatible_conjunction_node_domain",
        )


if __name__ == "__main__":
    unittest.main()
