from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from ontotf.semantic_ir import NativeBindingIR, native_binding_identity


SCHEMA = json.loads(
    Path("src/ontotf/schemas/mapping.schema.json").read_text(encoding="utf-8")
)
VALIDATOR = Draft202012Validator(
    {
        "$schema": SCHEMA["$schema"],
        "$defs": SCHEMA["$defs"],
        "$ref": "#/$defs/nativeBinding",
    }
)


def _binding(**overrides):
    row = {
        "component_id": "bhsa-tf",
        "node_type": "word",
        "feature": "sp",
        "values": ["subs", "nmpr"],
        "execution_shape": "value-set-predicate",
    }
    row.update(overrides)
    return row


def _errors(row):
    return list(VALIDATOR.iter_errors(row))


class I010ValueSetSchemaTests(unittest.TestCase):
    def test_mapping_schema_accepts_finite_value_set_predicate(self):
        self.assertEqual(_errors(_binding()), [])

    def test_mapping_schema_rejects_empty_or_duplicate_selected_values(self):
        self.assertTrue(_errors(_binding(values=[])))
        self.assertTrue(_errors(_binding(values=["subs", "subs"])))
        # JSON Schema equality treats numerically equal JSON numbers as duplicates.
        self.assertTrue(_errors(_binding(values=[1, 1.0])))

    def test_mapping_schema_rejects_mixed_scalar_closed_and_selected_values(self):
        self.assertTrue(_errors(_binding(value="subs")))
        self.assertTrue(_errors(_binding(closed_values=["subs", "nmpr"])))

    def test_native_binding_ir_has_selected_values_field(self):
        self.assertIn("values", NativeBindingIR.__dataclass_fields__)

    def test_native_binding_identity_is_invariant_to_selected_value_order(self):
        left = _binding(values=["subs", "nmpr"])
        right = _binding(values=["nmpr", "subs"])
        self.assertEqual(native_binding_identity(left), native_binding_identity(right))
