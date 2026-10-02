from __future__ import annotations

import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path

import tfont
import tfont.semantic_resolver as semantic_resolver
from jsonschema import Draft202012Validator

from tests.i005._fixtures import (
    entity_identity_reference,
    noun_sources,
    source_bundle,
    validate_structural_sources,
)
from tests.i006._fixtures import _refresh_mapping
from tests.i023._fixtures import (
    INCOMING_STEPS,
    LINE_TO_COLUMN_STEPS,
    OUTGOING_STEPS,
    FakeEdgeFeature,
    compiled_authority_edge_path_ir,
    compiled_edge_path_ir,
    compiled_reference_edge_path_ir,
    compiled_two_path_ir,
    edge_path_binding,
    edge_path_context,
    edge_path_sources,
    path_api,
    proper_noun_key,
    semantic_request,
    approximate_request,
)
from tfont.semantic_digest_v2 import (
    mapping_semantic_digest_v2,
    projection_semantic_digest_v1,
)
from tfont.semantic_ir import native_binding_identity
from tfont.semantic_validation import SemanticValidationError, validate_semantic_bundle
from tfont.source_validation import validate_source


ROOT = Path(__file__).resolve().parents[2]


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


class I023EdgePathContractTests(unittest.TestCase):
    def test_edge_path_source_shape_is_closed_and_typed(self):
        validator = binding_validator()
        typed = edge_path_binding()
        self.assertFalse(tuple(validator.iter_errors(typed)))

        incomplete = (
            {"execution_shape": "edge-path"},
            {
                "component_id": "bhsa-tf",
                "node_type": "word",
                "execution_shape": "edge-path",
            },
            {
                "component_id": "bhsa-tf",
                "node_type": "word",
                "execution_shape": "edge-path",
                "steps": [],
            },
            {
                "component_id": "bhsa-tf",
                "node_type": "word",
                "execution_shape": "edge-path",
                "steps": [{"edge": "word_line", "direction": "outgoing"}],
            },
            {
                "component_id": "bhsa-tf",
                "node_type": "word",
                "execution_shape": "edge-path",
                "edge": "word_line",
                "direction": "outgoing",
            },
        )
        for row in incomplete:
            with self.subTest(row=row):
                self.assertTrue(tuple(validator.iter_errors(row)))

        for mutation in (
            {"steps": [{"edge": "word_line", "direction": "outgoing", "valued": False}]},
            {"steps": [{"edge": "word_line", "direction": "outgoing", "result_node_type": "line"}]},
            {"steps": [{"edge": "word_line", "direction": "outgoing", "result_node_type": "line", "valued": True}]},
            {"feature": "sp"},
            {"value": "subs"},
            {"closed_values": ["subs"]},
            {"values": ["subs"]},
            {"edge": "word_line"},
            {"direction": "outgoing"},
            {"interpretation": "occurrenceSet"},
        ):
            with self.subTest(mutation=mutation):
                forged = copy.deepcopy(typed)
                forged.update(mutation)
                self.assertTrue(tuple(validator.iter_errors(forged)))

        forged = copy.deepcopy(typed)
        forged["steps"][0]["invented"] = "nope"
        self.assertTrue(tuple(validator.iter_errors(forged)))

    def test_edge_path_requires_start_result_and_ordered_path_authority(self):
        sources = edge_path_sources()
        validate_structural_sources(sources)
        validate_semantic_bundle(source_bundle(sources))

        mapping = sources["mappings"]["mappings"][0]
        cases = (
            "dep:bhsa:node-type:word",
            "dep:bhsa:node-type:line",
            "dep:bhsa:node-type:column",
            "dep:bhsa:path",
        )
        for missing in cases:
            with self.subTest(missing=missing):
                mutated = copy.deepcopy(sources)
                row = mutated["mappings"]["mappings"][0]
                row["native_dependencies"] = [
                    dep for dep in row["native_dependencies"] if dep != missing
                ]
                _refresh_mapping(row)
                validate_structural_sources(mutated)
                with self.assertRaises(SemanticValidationError) as raised:
                    validate_semantic_bundle(source_bundle(mutated))
                self.assertEqual(category(raised.exception), "dependency_authority")

        mutated = copy.deepcopy(sources)
        dep = next(
            row
            for row in mutated["profile"]["dependencies"]
            if row["kind"] == "path-present"
        )
        dep["assertion"]["steps"] = list(reversed(dep["assertion"]["steps"]))
        validate_structural_sources(mutated)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(mutated))
        self.assertEqual(category(raised.exception), "dependency_authority")

    def test_dependency_authority_applies_to_all_binding_owners(self):
        binding = edge_path_binding()
        for owner in ("mapping", "projection", "reference"):
            with self.subTest(owner=owner):
                refs = [entity_identity_reference("bhsa")] if owner == "reference" else None
                sources = noun_sources(
                    "bhsa",
                    parent_char="a",
                    external_references=refs,
                )
                mapping = sources["mappings"]["mappings"][0]
                if owner == "mapping":
                    mapping["native_binding"] = copy.deepcopy(binding)
                elif owner == "projection":
                    mapping["projections"][0]["native_execution_binding"] = copy.deepcopy(binding)
                else:
                    mapping["external_references"][0]["native_binding"] = copy.deepcopy(binding)
                _refresh_mapping(mapping)
                validate_structural_sources(sources)
                with self.assertRaises(SemanticValidationError) as raised:
                    validate_semantic_bundle(source_bundle(sources))
                self.assertEqual(category(raised.exception), "dependency_authority")

    def test_typed_steps_compile_and_public_two_argument_constructor_remains_compatible(self):
        old = tfont.EdgeStepIR("mother", "outgoing")
        self.assertIsNone(old.result_node_type)
        self.assertIsNone(old.valued)

        ir = compiled_edge_path_ir()
        binding = ir.semantic_index[0][1][0].native_execution_binding
        self.assertEqual(binding.execution_shape, "edge-path")
        self.assertEqual(binding.node_type, "word")
        self.assertEqual(
            tuple(
                (step.edge, step.direction, step.result_node_type, step.valued)
                for step in binding.steps
            ),
            (
                ("word_line", "outgoing", "line", False),
                ("line_column", "outgoing", "column", False),
            ),
        )

    def test_native_binding_identity_covers_typed_step_contract(self):
        baseline = edge_path_binding()
        reordered_keys = {
            "steps": [
                {
                    "valued": False,
                    "result_node_type": "line",
                    "direction": "outgoing",
                    "edge": "word_line",
                },
                {
                    "direction": "outgoing",
                    "valued": False,
                    "edge": "line_column",
                    "result_node_type": "column",
                },
            ],
            "execution_shape": "edge-path",
            "node_type": "word",
            "component_id": "bhsa-tf",
        }
        self.assertEqual(
            native_binding_identity(baseline),
            native_binding_identity(reordered_keys),
        )
        for mutation in (
            lambda row: row["steps"].reverse(),
            lambda row: row["steps"][0].__setitem__("direction", "incoming"),
            lambda row: row["steps"][0].__setitem__("result_node_type", "phrase"),
            lambda row: row["steps"][0].__setitem__("valued", True),
        ):
            changed = copy.deepcopy(baseline)
            mutation(changed)
            self.assertNotEqual(
                native_binding_identity(baseline),
                native_binding_identity(changed),
            )

    def test_exact_outgoing_execution_filters_polymorphic_neighbors_and_preserves_order(self):
        ir = compiled_edge_path_ir()
        api = path_api()
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (edge_path_context(tfont, ir, api),),
        )
        self.assertEqual(result.corpora[0].nodes, (21, 20))
        self.assertEqual(api.E.word_line.f_calls, [1, 2])
        self.assertEqual(api.E.line_column.f_calls, [11, 10])
        self.assertEqual(api.load_calls, 0)
        self.assertFalse(api.E.oslots_touched)

    def test_incoming_execution_uses_returned_source_domain(self):
        ir = compiled_edge_path_ir(
            start_node_type="column",
            steps=INCOMING_STEPS,
        )
        api = path_api()
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (edge_path_context(tfont, ir, api),),
        )
        self.assertEqual(result.corpora[0].nodes, (1, 2))
        self.assertTrue(api.E.line_column.t_calls)
        self.assertTrue(api.E.word_line.t_calls)

    def test_empty_typed_projection_is_valid_but_empty_start_after_authorization_is_drift(self):
        ir = compiled_edge_path_ir()
        empty_feature = FakeEdgeFeature({1: (99,), 2: (99,)})
        api = path_api(
            features={
                "word_line": empty_feature,
                "line_column": FakeEdgeFeature({10: (20,), 11: (21,)}),
            }
        )
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (edge_path_context(tfont, ir, api),),
        )
        self.assertEqual(result.corpora[0].nodes, ())

        drift_api = path_api(
            selection_sequences={
                "word": ((1, 2), ()),
            }
        )
        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                ir,
                semantic_request(tfont),
                (edge_path_context(tfont, ir, drift_api),),
            )
        self.assertEqual(category(raised.exception), "invalid_result_nodes")

    def test_full_path_preflight_rejects_later_valued_edge_even_after_empty_frontier(self):
        ir = compiled_edge_path_ir()
        api = path_api(
            features={
                "word_line": FakeEdgeFeature({1: (), 2: ()}),
                "line_column": FakeEdgeFeature({10: (20,)}, do_values=True),
            }
        )
        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                ir,
                semantic_request(tfont),
                (edge_path_context(tfont, ir, api),),
            )
        self.assertEqual(category(raised.exception), "loaded_api_unavailable")
        self.assertEqual(api.E.line_column.f_calls, [])

    def test_loaded_edge_contract_and_valuedness_fail_closed(self):
        ir = compiled_edge_path_ir()
        cases = (
            path_api(loaded_edges=("word_line",)),
            path_api(
                features={
                    "word_line": FakeEdgeFeature({1: (10,), 2: (10,)}, do_values=True),
                    "line_column": FakeEdgeFeature({10: (20,)}),
                }
            ),
            path_api(eall_sequence=(("word_line", "line_column"), RuntimeError("boom"))),
        )
        for api in cases:
            with self.subTest(api=api):
                with self.assertRaises(Exception):
                    tfont.execute_exact_semantic(
                        ir,
                        semantic_request(tfont),
                        (edge_path_context(tfont, ir, api),),
                    )
                self.assertEqual(api.load_calls, 0)

    def test_exact_approximate_and_reference_surfaces_reuse_edge_path_execution(self):
        ir = compiled_edge_path_ir()
        exact = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (edge_path_context(tfont, ir),),
        )
        approximate = tfont.execute_approximate_semantic(
            ir,
            approximate_request(tfont),
            (edge_path_context(tfont, ir),),
        )
        self.assertEqual(exact.corpora[0].nodes, (21, 20))
        self.assertEqual(approximate.corpora[0].nodes, (21, 20))

        authority_ir = compiled_authority_edge_path_ir()
        authority_key = authority_ir.authority_index[0][0]
        authority = tfont.execute_exact_authority(
            authority_ir,
            tfont.AuthorityResolveRequest(
                key=authority_key,
                corpora=("bhsa",),
            ),
            (edge_path_context(tfont, authority_ir),),
        )
        self.assertEqual(authority.corpora[0].nodes, (21, 20))

        refs_ir = compiled_reference_edge_path_ir()
        identity_key = refs_ir.identity_index[0][0]
        identity = tfont.execute_identity(
            refs_ir,
            tfont.IdentityResolveRequest(
                authority_system=identity_key.authority_system,
                external_entity_id=identity_key.external_entity_id,
                corpora=("bhsa",),
            ),
            (edge_path_context(tfont, refs_ir),),
        )
        self.assertEqual(identity.corpora[0].nodes, (21, 20))

        identifier_key = refs_ir.identifier_index[0][0]
        identifier = tfont.execute_identifier(
            refs_ir,
            tfont.IdentifierResolveRequest(
                key=identifier_key,
                corpora=("bhsa",),
            ),
            (edge_path_context(tfont, refs_ir),),
        )
        self.assertEqual(identifier.corpora[0].nodes, (21, 20))

    def test_conjunction_uses_final_typed_domain_not_start_domain(self):
        ir = compiled_two_path_ir()
        keys = (semantic_request(tfont).key, proper_noun_key(tfont))
        exact = tfont.execute_exact_conjunction(
            ir,
            tfont.SemanticConjunctionRequest(
                keys=keys,
                corpora=("bhsa",),
            ),
            (edge_path_context(tfont, ir),),
        )
        self.assertEqual(exact.corpora[0].nodes, (20, 21))

        approximate = tfont.execute_approximate_conjunction(
            ir,
            tfont.ApproximateSemanticConjunctionRequest(
                keys=keys,
                corpora=("bhsa",),
                semantic_mode="approximate",
                accept_losses=(),
            ),
            (edge_path_context(tfont, ir),),
        )
        self.assertEqual(approximate.corpora[0].nodes, (20, 21))

    def test_mixed_direction_path_uses_each_reviewed_result_domain(self):
        steps = (
            {
                "edge": "word_line",
                "direction": "outgoing",
                "result_node_type": "line",
                "valued": False,
            },
            {
                "edge": "word_line",
                "direction": "incoming",
                "result_node_type": "word",
                "valued": False,
            },
        )
        ir = compiled_edge_path_ir(steps=steps)
        result = tfont.execute_exact_semantic(
            ir,
            semantic_request(tfont),
            (edge_path_context(tfont, ir),),
        )
        self.assertEqual(result.corpora[0].nodes, (1, 2))

    def test_forged_defaulted_edge_step_fails_compiled_ir_validation(self):
        ir = compiled_edge_path_ir()
        binding = ir.semantic_index[0][1][0].native_execution_binding
        forged = replace(
            binding,
            steps=(tfont.EdgeStepIR("word_line", "outgoing"),),
        )
        with self.assertRaises(Exception) as raised:
            semantic_resolver._native_binding_projection(forged)
        self.assertEqual(category(raised.exception), "invalid_compiled_ir")

    def test_approximate_authority_reuses_edge_path_after_loss_acceptance(self):
        ir = compiled_authority_edge_path_ir(
            assessment="broader",
            losses=("undercoverage",),
        )
        key = ir.authority_index[0][0]
        refused = tfont.ApproximateAuthorityResolveRequest(
            key=key,
            corpora=("bhsa",),
        )
        with self.assertRaises(Exception) as raised:
            tfont.execute_approximate_authority(
                ir,
                refused,
                (edge_path_context(tfont, ir),),
            )
        self.assertEqual(category(raised.exception), "approximation_loss_not_accepted")

        accepted = tfont.ApproximateAuthorityResolveRequest(
            key=key,
            corpora=("bhsa",),
            accept_losses=("undercoverage",),
        )
        result = tfont.execute_approximate_authority(
            ir,
            accepted,
            (edge_path_context(tfont, ir),),
        )
        self.assertEqual(result.corpora[0].nodes, (21, 20))
        self.assertEqual(result.resolution.losses, ("undercoverage",))

    def test_loaded_edge_path_adversarial_api_failures_are_closed(self):
        ir = compiled_edge_path_ir()
        loaded = ("word_line", "line_column")

        malformed_inventory = path_api(
            eall_sequence=(loaded, loaded, "word_line"),
        )

        noncallable_method = path_api()
        noncallable_method.E.word_line.f = None

        missing_valuedness = path_api()
        delattr(missing_valuedness.E.word_line, "doValues")

        traversal_failure = path_api(
            features={
                "word_line": FakeEdgeFeature(
                    {1: (10,), 2: (10,)},
                    raise_on_f=True,
                ),
                "line_column": FakeEdgeFeature({10: (20,)}),
            }
        )

        malformed_otype = path_api(
            node_types={
                1: "word",
                2: "word",
                10: "line",
                11: None,
                20: "column",
                21: "column",
                99: "phrase",
            }
        )

        invalid_raw_node = path_api(
            features={
                "word_line": FakeEdgeFeature({1: (True,), 2: ()}),
                "line_column": FakeEdgeFeature({10: (20,)}),
            }
        )

        duplicate_raw_node = path_api(
            features={
                "word_line": FakeEdgeFeature({1: (10, 10), 2: ()}),
                "line_column": FakeEdgeFeature({10: (20,)}),
            }
        )

        cases = (
            (malformed_inventory, "loaded_api_unavailable"),
            (noncallable_method, "loaded_api_unavailable"),
            (missing_valuedness, "loaded_api_unavailable"),
            (traversal_failure, "loaded_api_unavailable"),
            (malformed_otype, "loaded_api_unavailable"),
            (invalid_raw_node, "invalid_result_nodes"),
            (duplicate_raw_node, "invalid_result_nodes"),
        )
        for api, expected in cases:
            with self.subTest(expected=expected, api=api):
                with self.assertRaises(Exception) as raised:
                    tfont.execute_exact_semantic(
                        ir,
                        semantic_request(tfont),
                        (edge_path_context(tfont, ir, api),),
                    )
                self.assertEqual(category(raised.exception), expected)
                self.assertEqual(api.load_calls, 0)
                self.assertFalse(api.E.oslots_touched)

    def test_packaged_resources_and_real_edge_controls_remain_grounded(self):
        count = 0
        shapes = set()
        root = ROOT / "src/tfont/resources/profiles"
        for path in sorted(root.glob("*/*/mappings/*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            validate_source(data, "mapping", source_name=str(path))
            for mapping in data.get("mappings", []):
                self.assertEqual(
                    mapping_semantic_digest_v2(mapping),
                    mapping["mapping_semantic_digest"],
                )
                rows = [mapping.get("native_binding")]
                for projection in mapping.get("projections", []):
                    self.assertEqual(
                        projection_semantic_digest_v1(projection),
                        projection["projection_semantic_digest"],
                    )
                    rows.append(projection.get("native_execution_binding"))
                rows.extend(
                    reference.get("native_binding")
                    for reference in mapping.get("external_references", [])
                )
                for binding in rows:
                    if type(binding) is not dict:
                        continue
                    shape = binding.get("execution_shape")
                    if type(shape) is str:
                        count += 1
                        shapes.add(shape)
                        self.assertNotIn(shape, {"membership", "edge-path"})
        self.assertEqual(count, 48)
        self.assertEqual(shapes, {"value-predicate", "value-set-predicate"})

        bhsa = json.loads(
            (ROOT / "docs/research/data/generated/r005/bhsa.json").read_text(encoding="utf-8")
        )
        mother = bhsa["edge_features"]["mother"]
        self.assertGreater(len(mother["source_types"]), 1)
        self.assertGreater(len(mother["target_types"]), 1)
        self.assertIs(mother["valued"], False)

        tlhdig = json.loads(
            (ROOT / "docs/research/data/generated/i019/tlhdig-0.4.0.json").read_text(encoding="utf-8")
        )
        valued = sorted(
            edge
            for edge, row in tlhdig["edge_features"].items()
            if row.get("valued") is True
        )
        self.assertEqual(valued, ["joined", "selected", "witness_resolution"])

    def test_no_text_fabric_runtime_dependency_is_declared(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
        self.assertNotIn('"text-fabric', pyproject)
        self.assertNotIn("'text-fabric", pyproject)


if __name__ == "__main__":
    unittest.main()
