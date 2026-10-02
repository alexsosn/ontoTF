from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import tfont
from jsonschema import Draft202012Validator
from tests.i022._fixtures import (
    compiled_edge_path_ir,
    compiled_membership_ir,
    membership_context,
    membership_request,
    membership_sources,
)
from tfont.semantic_validation import SemanticValidationError, validate_semantic_bundle
from tests.i005._fixtures import source_bundle, validate_structural_sources


ROOT = Path(__file__).resolve().parents[2]


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


class I022MembershipRedTests(unittest.TestCase):
    def test_membership_source_shape_is_closed(self):
        validator = binding_validator()
        typed = {
            "component_id": "bhsa-tf",
            "node_type": "word",
            "execution_shape": "membership",
        }
        self.assertFalse(tuple(validator.iter_errors(typed)))
        for incomplete in (
            {"execution_shape": "membership"},
            {"component_id": "bhsa-tf", "execution_shape": "membership"},
            {"node_type": "word", "execution_shape": "membership"},
        ):
            with self.subTest(incomplete=incomplete):
                self.assertTrue(tuple(validator.iter_errors(incomplete)))
        unknown = dict(typed)
        unknown["invented_field"] = "nope"
        self.assertTrue(tuple(validator.iter_errors(unknown)))
        for field, value in (
            ("feature", "sp"),
            ("value", "subs"),
            ("closed_values", ["subs"]),
            ("values", ["subs"]),
            ("edge", "mother"),
            ("direction", "outgoing"),
            ("steps", [{"edge": "mother", "direction": "outgoing"}]),
            ("interpretation", "occurrenceSet"),
        ):
            with self.subTest(field=field):
                forged = dict(typed)
                forged[field] = value
                self.assertTrue(
                    tuple(validator.iter_errors(forged)),
                    f"RED: membership silently accepts forbidden field {field}",
                )

    def test_membership_requires_exact_node_type_dependency_authority(self):
        authorized = membership_sources()
        validate_structural_sources(authorized)
        validate_semantic_bundle(source_bundle(authorized))

        for kwargs in (
            {"dependency_kind": "component-present"},
            {"dependency_node_type": "phrase"},
        ):
            with self.subTest(kwargs=kwargs):
                sources = membership_sources(**kwargs)
                validate_structural_sources(sources)
                with self.assertRaises(SemanticValidationError) as raised:
                    validate_semantic_bundle(source_bundle(sources))
                self.assertEqual(raised.exception.problem.category, "dependency_authority")

        wrong_component = membership_sources(dependency_component="other-tf")
        validate_structural_sources(wrong_component)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(wrong_component))
        self.assertEqual(raised.exception.problem.category, "component_authority")

    def test_membership_compiles_without_new_ir_shape(self):
        ir = compiled_membership_ir()
        binding = ir.semantic_index[0][1][0].native_execution_binding
        self.assertEqual(binding.component_id, "bhsa-tf")
        self.assertEqual(binding.node_type, "word")
        self.assertEqual(binding.execution_shape, "membership")
        self.assertIsNone(binding.feature)
        self.assertFalse(binding.value_present)
        self.assertIsNone(binding.value)
        self.assertIsNone(binding.values)
        self.assertIsNone(binding.edge)
        self.assertIsNone(binding.direction)
        self.assertIsNone(binding.steps)
        self.assertIsNone(binding.interpretation)

    def test_exact_semantic_execution_runs_membership_in_selector_order(self):
        ir = compiled_membership_ir()
        result = tfont.execute_exact_semantic(
            ir,
            membership_request(tfont),
            (membership_context(tfont, ir),),
        )
        self.assertEqual(result.corpora[0].nodes, (4, 2, 7))
        self.assertEqual(
            result.corpora[0].plan.native_execution_binding.execution_shape,
            "membership",
        )

    def test_edge_path_stays_unsupported(self):
        ir = compiled_edge_path_ir()
        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                ir,
                membership_request(tfont),
                (membership_context(tfont, ir),),
            )
        self.assertEqual(
            getattr(getattr(raised.exception, "problem", None), "category", ""),
            "unsupported_native_binding",
        )


if __name__ == "__main__":
    unittest.main()
