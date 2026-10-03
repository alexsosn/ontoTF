from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

import tfont
import tfont.semantic_execution as semantic_execution
from jsonschema import Draft202012Validator

from tests.i006._fixtures import noun_semantic_key
from tests.i023._fixtures import (
    FakeEdgeFeature,
    compiled_edge_path_ir,
    compiled_two_path_ir,
    edge_path_context,
    proper_noun_key,
    semantic_request,
)
from tests.i024._fixtures import (
    MIXED_STEPS,
    VALUED_INT_STEPS,
    ValuedFakeEdgeFeature,
    compiled_authority_valued_ir,
    compiled_mixed_conjunction_ir,
    compiled_valued_ir,
    integer_api,
    selected_api,
    valued_context,
)


ROOT = Path(__file__).resolve().parents[2]
SAFE_MAX = 2**53 - 1


def category(error: BaseException) -> str:
    return getattr(getattr(error, "problem", None), "category", "")


def binding_validator():
    schema = json.loads(
        (ROOT / "src/tfont/schemas/mapping.schema.json").read_text(encoding="utf-8")
    )
    return Draft202012Validator(
        {
            "$schema": schema["$schema"],
            "$defs": schema["$defs"],
            "$ref": "#/$defs/nativeBinding",
        }
    )


def one_step(edge: str, result_node_type: str, value_role: str, value_type: str = "str"):
    return (
        {
            "edge": edge,
            "direction": "outgoing",
            "result_node_type": result_node_type,
            "valued": True,
            "value_type": value_type,
            "value_role": value_role,
        },
    )


class I024ValuedEdgePathAdversarialTests(unittest.TestCase):
    def test_all_reviewed_real_value_roles_and_integer_type_compile(self):
        controls = (
            ("selected", "analysis", "source-evidence", "str"),
            ("witness_resolution", "fragment", "semantic-qualifier", "str"),
            ("joined", "fragment", "semantic-qualifier", "str"),
            ("omap@2017-2021", "word", "technical", "int"),
        )
        validator = binding_validator()
        for edge, result_type, role, value_type in controls:
            with self.subTest(edge=edge):
                ir = compiled_valued_ir(
                    steps=one_step(edge, result_type, role, value_type),
                )
                step = ir.semantic_index[0][1][0].native_execution_binding.steps[0]
                self.assertEqual(
                    (step.edge, step.value_type, step.value_role),
                    (edge, value_type, role),
                )
                binding = {
                    "component_id": "bhsa-tf",
                    "node_type": "word",
                    "execution_shape": "edge-path",
                    "steps": [dict(one_step(edge, result_type, role, value_type)[0])],
                }
                self.assertFalse(tuple(validator.iter_errors(binding)))

    def test_full_path_preflight_checks_later_valued_metadata_before_empty_traversal(self):
        ir = compiled_valued_ir(steps=MIXED_STEPS)
        line_quality = ValuedFakeEdgeFeature(
            {10: ((20, "x"),)},
            value_type="int",
        )
        api = selected_api()
        api.node_types.update({20: "column"})
        api.F.otype.node_types.update({20: "column"})
        api.E.word_line = FakeEdgeFeature({1: (), 2: ()})
        api.E.line_quality = line_quality
        api.loaded_edges = ("word_line", "line_quality")

        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                ir,
                semantic_request(tfont),
                (valued_context(tfont, ir, api),),
            )
        self.assertEqual(category(raised.exception), "loaded_api_unavailable")
        self.assertEqual(line_quality.f_calls, [])

    def test_runtime_rejects_forged_non_edge_step_before_field_access(self):
        ir = compiled_valued_ir()
        binding = ir.semantic_index[0][1][0].native_execution_binding

        class Plan:
            corpus_id = "bhsa"
            native_execution_binding = replace(binding, steps=(object(),))

        with self.assertRaises(tfont.ExactExecutionError) as raised:
            semantic_execution._validate_edge_path_binding(Plan())
        self.assertEqual(raised.exception.problem.category, "unsupported_native_binding")
    def test_malformed_metadata_pair_shapes_and_value_subclasses_fail_closed(self):
        ir = compiled_valued_ir()

        class PairSubclass(tuple):
            pass

        class StringSubclass(str):
            pass

        cases = (
            ValuedFakeEdgeFeature({1: ((10, "x"),)}, meta=[]),
            ValuedFakeEdgeFeature({1: (PairSubclass((10, "x")),)}),
            ValuedFakeEdgeFeature({1: ({"node": 10, "value": "x"},)}),
            ValuedFakeEdgeFeature({1: (10,)}),
            ValuedFakeEdgeFeature({1: ((10, StringSubclass("x")),)}),
        )
        for feature in cases:
            with self.subTest(feature=feature):
                with self.assertRaises(Exception) as raised:
                    tfont.execute_exact_semantic(
                        ir,
                        semantic_request(tfont),
                        (valued_context(tfont, ir, selected_api(feature=feature)),),
                    )
                self.assertEqual(category(raised.exception), "loaded_api_unavailable")

        class IntSubclass(int):
            pass

        int_ir = compiled_valued_ir(steps=VALUED_INT_STEPS)
        int_feature = ValuedFakeEdgeFeature(
            {1: ((2, IntSubclass(1)),)},
            value_type="int",
        )
        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                int_ir,
                semantic_request(tfont),
                (valued_context(tfont, int_ir, integer_api(feature=int_feature)),),
            )
        self.assertEqual(category(raised.exception), "loaded_api_unavailable")

    def test_safe_jcs_upper_boundary_is_preserved_exactly(self):
        ir = compiled_valued_ir(steps=VALUED_INT_STEPS)
        feature = ValuedFakeEdgeFeature(
            {1: ((SAFE_MAX, SAFE_MAX),)},
            value_type="int",
        )
        api = integer_api(feature=feature)
        api.F.otype.node_types[SAFE_MAX] = "word"
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (valued_context(tfont, ir, api),),
        ).corpora[0]
        self.assertEqual(result.nodes, (SAFE_MAX,))
        observation = result.edge_path_evidence.layers[0].observations[0]
        self.assertEqual((observation.target_node, observation.value), (SAFE_MAX, SAFE_MAX))
        self.assertEqual(
            tfont.edge_path_evidence_fingerprint(result.edge_path_evidence),
            result.edge_path_evidence.evidence_fingerprint,
        )

    def test_pure_unvalued_execution_keeps_none_evidence_and_legacy_conjunction_empty_tuple(self):
        ir = compiled_edge_path_ir()
        exact = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (edge_path_context(tfont, ir),),
        )
        self.assertIsNone(exact.corpora[0].edge_path_evidence)

        conjunction_ir = compiled_two_path_ir()
        keys = (semantic_request(tfont).key, proper_noun_key(tfont))
        conjunction = tfont.execute_exact_conjunction(
            conjunction_ir,
            tfont.SemanticConjunctionRequest(keys=keys, corpora=("bhsa",)),
            (edge_path_context(tfont, conjunction_ir),),
        ).corpora[0]
        self.assertEqual(conjunction.constituent_edge_path_evidence, ())

    def test_approximate_authority_preserves_native_evidence_after_loss_acceptance(self):
        ir = compiled_authority_valued_ir(
            assessment="broader",
            losses=("undercoverage",),
        )
        key = ir.authority_index[0][0]
        result = tfont.execute_approximate_authority(
            ir,
            tfont.ApproximateAuthorityResolveRequest(
                key=key,
                corpora=("bhsa",),
                accept_losses=("undercoverage",),
            ),
            (valued_context(tfont, ir),),
        )
        self.assertEqual(result.resolution.losses, ("undercoverage",))
        self.assertIsNotNone(result.corpora[0].edge_path_evidence)

    def test_evidence_fingerprint_binds_observation_content_and_rejects_layer_reordering(self):
        first = tfont.EdgePathObservation(1, 2, True, "x")
        second = tfont.EdgePathObservation(2, 3, False, None)
        layer0 = tfont.EdgePathEvidenceLayer(0, (first,))
        layer1 = tfont.EdgePathEvidenceLayer(1, (second,))
        base = tfont.EdgePathEvidence(
            "tfont-edge-path-evidence-v1",
            "sha256:" + "a" * 64,
            "sha256:" + "b" * 64,
            (1,),
            (layer0, layer1),
            (3,),
            "",
        )
        fingerprint = tfont.edge_path_evidence_fingerprint(base)

        mutations = (
            replace(base, start_nodes=(2,)),
            replace(base, final_nodes=(2,)),
            replace(
                base,
                layers=(
                    tfont.EdgePathEvidenceLayer(
                        0,
                        (tfont.EdgePathObservation(1, 4, True, "x"),),
                    ),
                    layer1,
                ),
            ),
            replace(
                base,
                layers=(
                    tfont.EdgePathEvidenceLayer(
                        0,
                        (tfont.EdgePathObservation(1, 2, True, "y"),),
                    ),
                    layer1,
                ),
            ),
        )
        for changed in mutations:
            with self.subTest(changed=changed):
                self.assertNotEqual(
                    tfont.edge_path_evidence_fingerprint(changed),
                    fingerprint,
                )

        with self.assertRaises(TypeError):
            tfont.edge_path_evidence_fingerprint(
                replace(base, layers=(layer1, layer0))
            )

    def test_conjunction_intersection_does_not_trim_constituent_path_evidence(self):
        ir = compiled_mixed_conjunction_ir()
        keys = (
            noun_semantic_key(),
            tfont.SemanticKey(
                profile_id="linguistic",
                capability_id="linguistic.part-of-speech",
                target="http://purl.org/olia/olia.owl#ProperNoun",
                formal_kind="class",
                semantic_role="annotation-value",
            ),
        )
        api = selected_api(selections={"analysis": (10,)})
        result = tfont.execute_exact_conjunction(
            ir,
            tfont.SemanticConjunctionRequest(keys=keys, corpora=("bhsa",)),
            (valued_context(tfont, ir, api),),
        ).corpora[0]
        self.assertEqual(result.nodes, (10,))
        evidence = result.constituent_edge_path_evidence[0]
        self.assertIsNotNone(evidence)
        targets = tuple(
            row.target_node
            for row in evidence.layers[0].observations
        )
        self.assertIn(11, targets)

    def test_all_public_execution_dataclass_prefixes_and_contract_tokens_stay_compatible(self):
        self.assertIsNone(tfont.ExactCorpusExecution("x", (), None, None).edge_path_evidence)
        self.assertIsNone(tfont.ApproximateCorpusExecution("x", (), None, None).edge_path_evidence)
        self.assertIsNone(tfont.ExactAuthorityCorpusExecution("x", (), None, None).edge_path_evidence)
        self.assertIsNone(tfont.ApproximateAuthorityCorpusExecution("x", (), None, None).edge_path_evidence)
        self.assertIsNone(tfont.IdentityCorpusExecution("x", (), None, None).edge_path_evidence)
        self.assertIsNone(tfont.IdentifierCorpusExecution("x", (), None, None).edge_path_evidence)
        self.assertEqual(
            tfont.ExactConjunctionCorpusExecution("x", (), (), None).constituent_edge_path_evidence,
            (),
        )
        self.assertEqual(
            tfont.ApproximateConjunctionCorpusExecution("x", (), (), None).constituent_edge_path_evidence,
            (),
        )

        self.assertEqual(tfont.EXACT_EXECUTION_CONTRACT, "tfont-exact-execution-v1")
        self.assertEqual(tfont.APPROXIMATE_EXECUTION_CONTRACT, "tfont-approximate-execution-v1")
        self.assertEqual(
            tfont.EXACT_CONJUNCTION_EXECUTION_CONTRACT,
            "tfont-exact-semantic-conjunction-execution-v1",
        )
        self.assertEqual(
            tfont.APPROXIMATE_CONJUNCTION_EXECUTION_CONTRACT,
            "tfont-approximate-semantic-conjunction-execution-v1",
        )
        self.assertEqual(
            tfont.EXACT_AUTHORITY_EXECUTION_CONTRACT,
            "tfont-exact-authority-execution-v1",
        )
        self.assertEqual(
            tfont.APPROXIMATE_AUTHORITY_EXECUTION_CONTRACT,
            "tfont-approximate-authority-execution-v1",
        )
        self.assertEqual(tfont.IDENTITY_EXECUTION_CONTRACT, "tfont-identity-execution-v1")
        self.assertEqual(tfont.IDENTIFIER_EXECUTION_CONTRACT, "tfont-identifier-execution-v1")


if __name__ == "__main__":
    unittest.main()
