from __future__ import annotations

import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path

import tfont
import tfont.semantic_resolver as semantic_resolver
from jsonschema import Draft202012Validator

from tests.i006._fixtures import _refresh_mapping, noun_semantic_key
from tests.i023._fixtures import approximate_request, semantic_request
from tests.i024._fixtures import (
    EMPTY_TRAILING_STEPS,
    INCOMING_VALUED_STEPS,
    MIXED_STEPS,
    VALUED_INT_STEPS,
    VALUED_STR_STEPS,
    ValuedFakeEdgeFeature,
    compiled_authority_valued_ir,
    compiled_mixed_conjunction_ir,
    compiled_reference_valued_ir,
    compiled_valued_ir,
    empty_trailing_api,
    integer_api,
    mixed_api,
    selected_api,
    valued_context,
    valued_sources,
)
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2
from tfont.semantic_ir import native_binding_identity


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


class I024ValuedEdgePathRedTests(unittest.TestCase):
    def test_source_contract_accepts_typed_valued_steps_and_keeps_unvalued_shape(self):
        validator = binding_validator()
        valued = valued_sources()["mappings"]["mappings"][0]["native_binding"]
        self.assertFalse(tuple(validator.iter_errors(valued)))

        unvalued = copy.deepcopy(valued)
        unvalued["steps"][0] = {
            "edge": "selected",
            "direction": "outgoing",
            "result_node_type": "analysis",
            "valued": False,
        }
        self.assertFalse(tuple(validator.iter_errors(unvalued)))

        invalid = []
        for field in ("value_type", "value_role"):
            row = copy.deepcopy(valued)
            row["steps"][0].pop(field)
            invalid.append(row)
        for field, value in (
            ("value_type", "float"),
            ("value_role", "ontology-category"),
        ):
            row = copy.deepcopy(valued)
            row["steps"][0][field] = value
            invalid.append(row)
        for field, value in (
            ("value_type", "str"),
            ("value_role", "source-evidence"),
        ):
            row = copy.deepcopy(unvalued)
            row["steps"][0][field] = value
            invalid.append(row)
        for row in invalid:
            with self.subTest(row=row):
                self.assertTrue(tuple(validator.iter_errors(row)))

    def test_valued_fields_change_binding_and_mapping_identity(self):
        source_evidence = valued_sources()
        semantic_qualifier = copy.deepcopy(source_evidence)
        binding_a = source_evidence["mappings"]["mappings"][0]["native_binding"]
        binding_b = semantic_qualifier["mappings"]["mappings"][0]["native_binding"]
        binding_b["steps"][0]["value_role"] = "semantic-qualifier"
        row_b = semantic_qualifier["mappings"]["mappings"][0]
        row_b["projections"][0]["native_execution_binding"]["steps"][0]["value_role"] = "semantic-qualifier"
        _refresh_mapping(row_b)
        self.assertNotEqual(
            native_binding_identity(binding_a),
            native_binding_identity(binding_b),
        )
        self.assertNotEqual(
            mapping_semantic_digest_v2(source_evidence["mappings"]["mappings"][0]),
            mapping_semantic_digest_v2(row_b),
        )

    def test_edge_step_ir_appends_defaulted_value_contract(self):
        old = tfont.EdgeStepIR("selected", "outgoing", "analysis", False)
        self.assertIsNone(old.value_type)
        self.assertIsNone(old.value_role)

        ir = compiled_valued_ir()
        step = ir.semantic_index[0][1][0].native_execution_binding.steps[0]
        self.assertEqual(
            (
                step.edge,
                step.direction,
                step.result_node_type,
                step.valued,
                step.value_type,
                step.value_role,
            ),
            (
                "selected",
                "outgoing",
                "analysis",
                True,
                "str",
                "source-evidence",
            ),
        )

    def test_forged_compiled_step_contract_fails_closed(self):
        ir = compiled_valued_ir()
        binding = ir.semantic_index[0][1][0].native_execution_binding

        class StringSubclass(str):
            pass

        forged_steps = (
            tfont.EdgeStepIR("selected", "outgoing", "analysis", True),
            tfont.EdgeStepIR(
                "selected",
                "outgoing",
                "analysis",
                True,
                StringSubclass("str"),
                "source-evidence",
            ),
            tfont.EdgeStepIR(
                "selected",
                "outgoing",
                "analysis",
                False,
                "str",
                "source-evidence",
            ),
        )
        for step in forged_steps:
            with self.subTest(step=step):
                forged = replace(binding, steps=(step,))
                with self.assertRaises(Exception) as raised:
                    semantic_resolver._native_binding_projection(forged)
                self.assertEqual(category(raised.exception), "invalid_compiled_ir")

    def test_outgoing_valued_execution_preserves_fanin_and_typed_evidence(self):
        ir = compiled_valued_ir()
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (valued_context(tfont, ir, selected_api()),),
        )
        corpus = result.corpora[0]
        self.assertEqual(corpus.nodes, (11, 10))
        evidence = corpus.edge_path_evidence
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence.evidence_contract, "tfont-edge-path-evidence-v1")
        self.assertEqual(evidence.plan_fingerprint, corpus.plan.plan_fingerprint)
        self.assertEqual(evidence.start_nodes, (1, 2))
        self.assertEqual(evidence.final_nodes, (11, 10))
        self.assertEqual(len(evidence.layers), 1)
        self.assertEqual(evidence.layers[0].step_index, 0)
        self.assertEqual(
            tuple(
                (row.source_node, row.target_node, row.value_present, row.value)
                for row in evidence.layers[0].observations
            ),
            (
                (1, 11, True, "2a"),
                (1, 10, True, "1"),
                (2, 10, True, "1bR 1bS"),
            ),
        )
        self.assertEqual(
            tfont.edge_path_evidence_fingerprint(evidence),
            evidence.evidence_fingerprint,
        )

    def test_incoming_valued_execution_preserves_native_orientation(self):
        ir = compiled_valued_ir(
            start_node_type="analysis",
            steps=INCOMING_VALUED_STEPS,
        )
        api = selected_api(selections={"analysis": (10, 11)})
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (valued_context(tfont, ir, api),),
        )
        self.assertEqual(result.corpora[0].nodes, (1, 2))
        observations = result.corpora[0].edge_path_evidence.layers[0].observations
        self.assertEqual(
            tuple((row.source_node, row.target_node, row.value) for row in observations),
            (
                (1, 10, "1"),
                (2, 10, "1bR 1bS"),
                (1, 11, "2a"),
            ),
        )

    def test_string_empty_and_integer_none_are_distinct(self):
        str_feature = ValuedFakeEdgeFeature({1: ((10, ""),)})
        str_api = selected_api(feature=str_feature)
        str_ir = compiled_valued_ir()
        str_result = tfont.execute_exact_semantic(
            str_ir,
            semantic_request(tfont),
            (valued_context(tfont, str_ir, str_api),),
        )
        row = str_result.corpora[0].edge_path_evidence.layers[0].observations[0]
        self.assertTrue(row.value_present)
        self.assertEqual(row.value, "")

        int_ir = compiled_valued_ir(steps=VALUED_INT_STEPS)
        int_result = tfont.execute_exact_semantic(
            int_ir,
            semantic_request(tfont),
            (valued_context(tfont, int_ir, integer_api()),),
        )
        rows = int_result.corpora[0].edge_path_evidence.layers[0].observations
        self.assertEqual(
            tuple((row.target_node, row.value_present, row.value) for row in rows),
            ((2, True, 1), (3, False, None)),
        )

    def test_value_shape_type_metadata_and_do_values_drift_fail_closed(self):
        ir = compiled_valued_ir()
        cases = (
            ValuedFakeEdgeFeature({1: ((10, None),)}),
            ValuedFakeEdgeFeature({1: ((10, True),)}),
            ValuedFakeEdgeFeature({1: ([10, "1"],)}),
            ValuedFakeEdgeFeature({1: ((10, "1"),)}, value_type="int"),
            ValuedFakeEdgeFeature({1: ((10, "1"),)}, do_values=False),
            ValuedFakeEdgeFeature({1: ((99, None),)}),
        )
        for feature in cases:
            with self.subTest(feature=feature):
                api = selected_api(feature=feature)
                with self.assertRaises(Exception) as raised:
                    tfont.execute_exact_semantic(
                        ir,
                        semantic_request(tfont),
                        (valued_context(tfont, ir, api),),
                    )
                self.assertEqual(category(raised.exception), "loaded_api_unavailable")

    def test_duplicate_raw_pair_fails_but_fanin_evidence_is_lossless(self):
        ir = compiled_valued_ir()
        duplicate = ValuedFakeEdgeFeature(
            {1: ((10, "1"), (10, "1"))}
        )
        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                ir,
                semantic_request(tfont),
                (valued_context(tfont, ir, selected_api(feature=duplicate)),),
            )
        self.assertEqual(category(raised.exception), "invalid_result_nodes")

        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (valued_context(tfont, ir, selected_api()),),
        )
        observations = result.corpora[0].edge_path_evidence.layers[0].observations
        self.assertEqual(
            sum(row.target_node == 10 for row in observations),
            2,
        )
        self.assertEqual(result.corpora[0].nodes.count(10), 1)

    def test_mixed_path_records_unvalued_layer_and_trailing_empty_layer(self):
        mixed_ir = compiled_valued_ir(steps=MIXED_STEPS)
        mixed = tfont.execute_exact_semantic(
            mixed_ir,
            semantic_request(tfont),
            (valued_context(tfont, mixed_ir, mixed_api()),),
        ).corpora[0]
        self.assertEqual(mixed.nodes, (20,))
        self.assertEqual(len(mixed.edge_path_evidence.layers), 2)
        first = mixed.edge_path_evidence.layers[0]
        self.assertEqual(first.step_index, 0)
        self.assertTrue(first.observations)
        self.assertTrue(all(not row.value_present and row.value is None for row in first.observations))

        empty_ir = compiled_valued_ir(steps=EMPTY_TRAILING_STEPS)
        empty = tfont.execute_exact_semantic(
            empty_ir,
            semantic_request(tfont),
            (valued_context(tfont, empty_ir, empty_trailing_api()),),
        ).corpora[0]
        self.assertEqual(empty.nodes, ())
        self.assertEqual(tuple(layer.step_index for layer in empty.edge_path_evidence.layers), (0, 1))
        self.assertEqual(empty.edge_path_evidence.layers[1].observations, ())

    def test_safe_jcs_boundary_applies_only_when_evidence_is_required(self):
        int_ir = compiled_valued_ir(steps=VALUED_INT_STEPS)
        oversized_value = ValuedFakeEdgeFeature(
            {1: ((2, SAFE_MAX + 1),)},
            value_type="int",
        )
        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                int_ir,
                semantic_request(tfont),
                (valued_context(tfont, int_ir, integer_api(feature=oversized_value)),),
            )
        self.assertEqual(category(raised.exception), "loaded_api_unavailable")

        oversized_node = ValuedFakeEdgeFeature(
            {1: ((SAFE_MAX + 1, 1),)},
            value_type="int",
        )
        api = integer_api(feature=oversized_node)
        api.F.otype.node_types[SAFE_MAX + 1] = "word"
        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                int_ir,
                semantic_request(tfont),
                (valued_context(tfont, int_ir, api),),
            )
        self.assertEqual(category(raised.exception), "invalid_result_nodes")

    def test_fingerprint_binds_plan_trace_and_rejects_forged_container_shapes(self):
        self.assertTrue(hasattr(tfont, "EdgePathObservation"))
        self.assertTrue(hasattr(tfont, "EdgePathEvidenceLayer"))
        self.assertTrue(hasattr(tfont, "EdgePathEvidence"))
        observation = tfont.EdgePathObservation(1, 2, True, "x")
        layer = tfont.EdgePathEvidenceLayer(0, (observation,))
        base = tfont.EdgePathEvidence(
            "tfont-edge-path-evidence-v1",
            "sha256:" + "a" * 64,
            "sha256:" + "b" * 64,
            (1,),
            (layer,),
            (2,),
            "",
        )
        fp = tfont.edge_path_evidence_fingerprint(base)
        sealed = replace(base, evidence_fingerprint=fp)
        self.assertEqual(tfont.edge_path_evidence_fingerprint(sealed), fp)
        other_plan = replace(sealed, plan_fingerprint="sha256:" + "c" * 64)
        self.assertNotEqual(
            tfont.edge_path_evidence_fingerprint(other_plan),
            fp,
        )
        with self.assertRaises(TypeError):
            tfont.edge_path_evidence_fingerprint(replace(sealed, layers=[layer]))

    def test_exact_approximate_authority_identity_identifier_surfaces_carry_evidence(self):
        ir = compiled_valued_ir()
        exact = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (valued_context(tfont, ir),),
        )
        approximate = tfont.execute_approximate_semantic(
            ir,
            approximate_request(tfont),
            (valued_context(tfont, ir),),
        )
        self.assertIsNotNone(exact.corpora[0].edge_path_evidence)
        self.assertIsNotNone(approximate.corpora[0].edge_path_evidence)

        authority_ir = compiled_authority_valued_ir()
        authority_key = authority_ir.authority_index[0][0]
        authority = tfont.execute_exact_authority(
            authority_ir,
            tfont.AuthorityResolveRequest(key=authority_key, corpora=("bhsa",)),
            (valued_context(tfont, authority_ir),),
        )
        self.assertIsNotNone(authority.corpora[0].edge_path_evidence)

        refs_ir = compiled_reference_valued_ir()
        identity_key = refs_ir.identity_index[0][0]
        identity = tfont.execute_identity(
            refs_ir,
            tfont.IdentityResolveRequest(
                authority_system=identity_key.authority_system,
                external_entity_id=identity_key.external_entity_id,
                corpora=("bhsa",),
            ),
            (valued_context(tfont, refs_ir),),
        )
        identifier_key = refs_ir.identifier_index[0][0]
        identifier = tfont.execute_identifier(
            refs_ir,
            tfont.IdentifierResolveRequest(key=identifier_key, corpora=("bhsa",)),
            (valued_context(tfont, refs_ir),),
        )
        self.assertIsNotNone(identity.corpora[0].edge_path_evidence)
        self.assertIsNotNone(identifier.corpora[0].edge_path_evidence)

    def test_mixed_conjunction_evidence_is_plan_aligned(self):
        ir = compiled_mixed_conjunction_ir()
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
            (valued_context(tfont, ir),),
        ).corpora[0]
        self.assertEqual(len(exact.constituent_edge_path_evidence), len(exact.plans))
        self.assertIsNotNone(exact.constituent_edge_path_evidence[0])
        self.assertIsNone(exact.constituent_edge_path_evidence[1])

        approximate = tfont.execute_approximate_conjunction(
            ir,
            tfont.ApproximateSemanticConjunctionRequest(
                keys=keys,
                corpora=("bhsa",),
                semantic_mode="approximate",
                accept_losses=(),
            ),
            (valued_context(tfont, ir),),
        ).corpora[0]
        self.assertEqual(
            tuple(item is None for item in approximate.constituent_edge_path_evidence),
            (False, True),
        )

    def test_public_result_positional_compatibility_and_outer_contracts(self):
        exact = tfont.ExactCorpusExecution("bhsa", (1,), None, None)
        approximate = tfont.ApproximateCorpusExecution("bhsa", (1,), None, None)
        self.assertIsNone(exact.edge_path_evidence)
        self.assertIsNone(approximate.edge_path_evidence)

        self.assertEqual(
            tfont.EXACT_EXECUTION_CONTRACT,
            "tfont-exact-execution-v1",
        )
        self.assertEqual(
            tfont.APPROXIMATE_EXECUTION_CONTRACT,
            "tfont-approximate-execution-v1",
        )

    def test_packaged_mappings_and_runtime_dependency_boundary_remain_unchanged(self):
        count = 0
        historical_count = 0
        shapes = set()
        root = ROOT / "src/tfont/resources/profiles"
        for path in sorted(root.glob("*/*/mappings/*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for mapping in data.get("mappings", []):
                self.assertEqual(
                    mapping_semantic_digest_v2(mapping),
                    mapping["mapping_semantic_digest"],
                )
                rows = [mapping.get("native_binding")]
                rows.extend(
                    projection.get("native_execution_binding")
                    for projection in mapping.get("projections", [])
                )
                rows.extend(
                    reference.get("native_binding")
                    for reference in mapping.get("external_references", [])
                )
                for binding in rows:
                    if type(binding) is dict and type(binding.get("execution_shape")) is str:
                        count += 1
                        if path.parent.parent.name in {"0.1.0", "0.2.0"}:
                            historical_count += 1
                        shapes.add(binding["execution_shape"])
                        self.assertNotEqual(binding["execution_shape"], "edge-path")
        self.assertEqual(historical_count, 48)
        self.assertGreater(count, historical_count)
        self.assertEqual(shapes, {"value-predicate", "value-set-predicate"})

        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
        self.assertNotIn('"text-fabric', pyproject)
        self.assertNotIn("'text-fabric", pyproject)


if __name__ == "__main__":
    unittest.main()
