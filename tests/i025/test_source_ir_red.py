from __future__ import annotations

import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path

import tfont
import tfont.semantic_resolver as semantic_resolver
from jsonschema import Draft202012Validator

from tests.i005._fixtures import source_bundle, validate_structural_sources
from tests.i006._fixtures import _refresh_mapping
from tests.i023._fixtures import edge_path_sources
from tests.i024._fixtures import VALUED_STR_STEPS
from tests.i025._fixtures import (
    compiled_predicate_ir,
    edge_domain_dependency,
    predicate_sources,
    predicate_step,
)
from tfont.semantic_digest_v2 import mapping_semantic_digest_v2
from tfont.semantic_ir import native_binding_identity
from tfont.semantic_validation import SemanticValidationError, validate_semantic_bundle


ROOT = Path(__file__).resolve().parents[2]
SAFE_MAX = 2**53 - 1


def category(error: BaseException) -> str:
    return getattr(getattr(error, "problem", None), "category", "")


def mapping_binding_validator():
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


def profile_validator():
    schema = json.loads(
        (ROOT / "src/tfont/schemas/profile.schema.json").read_text(encoding="utf-8")
    )
    return Draft202012Validator(schema)


class I025SourceIRRedTests(unittest.TestCase):
    def test_source_accepts_singleton_and_finite_string_match_sets(self):
        validator = mapping_binding_validator()
        for values in (["ambiguous"], ["unique", "ambiguous"]):
            binding = predicate_sources(match_values=values)["mappings"]["mappings"][0][
                "native_binding"
            ]
            with self.subTest(values=values):
                self.assertFalse(tuple(validator.iter_errors(binding)))

    def test_source_accepts_safe_integer_match_set(self):
        validator = mapping_binding_validator()
        binding = predicate_sources(
            value_type="int",
            match_values=(SAFE_MAX, 1),
            domain_values=(1, SAFE_MAX),
        )["mappings"]["mappings"][0]["native_binding"]
        self.assertFalse(tuple(validator.iter_errors(binding)))

    def test_source_rejects_invalid_match_contracts(self):
        validator = mapping_binding_validator()
        base = predicate_sources()["mappings"]["mappings"][0]["native_binding"]

        invalid = []
        row = copy.deepcopy(base)
        row["steps"][0]["match_values"] = []
        invalid.append(row)

        row = copy.deepcopy(base)
        row["steps"][0]["match_values"] = ["ambiguous", "ambiguous"]
        invalid.append(row)

        row = copy.deepcopy(base)
        row["steps"][0]["match_values"] = [None]
        invalid.append(row)

        row = copy.deepcopy(base)
        row["steps"][0]["value_role"] = "source-evidence"
        invalid.append(row)

        row = copy.deepcopy(base)
        row["steps"][0]["value_role"] = "technical"
        invalid.append(row)

        row = copy.deepcopy(base)
        row["steps"][0]["valued"] = False
        row["steps"][0].pop("value_type")
        row["steps"][0].pop("value_role")
        invalid.append(row)

        int_binding = predicate_sources(
            value_type="int",
            match_values=(1,),
            domain_values=(1, 2),
        )["mappings"]["mappings"][0]["native_binding"]

        row = copy.deepcopy(int_binding)
        row["steps"][0]["match_values"] = [True]
        invalid.append(row)

        row = copy.deepcopy(int_binding)
        row["steps"][0]["match_values"] = ["1"]
        invalid.append(row)

        row = copy.deepcopy(int_binding)
        row["steps"][0]["match_values"] = [SAFE_MAX + 1]
        invalid.append(row)

        for value in invalid:
            with self.subTest(value=value):
                self.assertTrue(tuple(validator.iter_errors(value)))

    def test_integral_float_cannot_smuggle_integer_match_or_reviewed_domain(self):
        match_float = predicate_sources(
            value_type="int",
            match_values=(1.0,),
            domain_values=(1, 2),
        )
        # Draft 2020-12 treats 1.0 as an integer; semantic validation must
        # still enforce the exact TFont int contract.
        validate_structural_sources(match_float)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(match_float))
        self.assertEqual(category(raised.exception), "dependency_authority")

        domain_float = predicate_sources(
            value_type="int",
            match_values=(1,),
            domain_values=(1.0, 2),
        )
        validate_structural_sources(domain_float)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(domain_float))
        self.assertEqual(category(raised.exception), "dependency_authority")

    def test_no_predicate_i024_shape_remains_valid(self):
        binding = edge_path_sources(
            start_node_type="word",
            steps=VALUED_STR_STEPS,
        )["mappings"]["mappings"][0]["native_binding"]
        self.assertFalse(tuple(mapping_binding_validator().iter_errors(binding)))

    def test_unused_integer_edge_domain_still_rejects_integral_float_values(self):
        sources = edge_path_sources(
            start_node_type="word",
            steps=VALUED_STR_STEPS,
        )
        sources["profile"]["dependency_contract_version"] = 2
        dependency = edge_domain_dependency(
            sources,
            edge="quality_score",
            source_node_type="line",
            target_node_type="fragment",
            value_type="int",
            values=(1.0, 2),
            dependency_id="dep:bhsa:unused-quality-domain",
        )
        sources["profile"]["dependencies"].append(dependency)

        validate_structural_sources(sources)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(sources))
        self.assertEqual(category(raised.exception), "dependency_authority")

    def test_profile_v2_accepts_old_kinds_and_edge_domain_but_v1_rejects_new_kind(self):
        sources = predicate_sources()
        self.assertFalse(tuple(profile_validator().iter_errors(sources["profile"])))

        v1 = copy.deepcopy(sources["profile"])
        v1["dependency_contract_version"] = 1
        self.assertTrue(tuple(profile_validator().iter_errors(v1)))

        old = edge_path_sources(start_node_type="word", steps=VALUED_STR_STEPS)
        old["profile"]["dependency_contract_version"] = 2
        self.assertFalse(tuple(profile_validator().iter_errors(old["profile"])))

    def test_semantic_validation_rejects_v1_edge_domain_even_if_schema_is_bypassed(self):
        sources = predicate_sources()
        sources["profile"]["dependency_contract_version"] = 1
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(sources))
        self.assertEqual(category(raised.exception), "unsupported_contract_version")

    def test_edge_domain_requires_closed_semantic_qualifier_evidence_and_typed_values(self):
        base = predicate_sources()["profile"]
        validator = profile_validator()
        invalid = []

        row = copy.deepcopy(base)
        dep = row["dependencies"][-1]
        dep.pop("evidence")
        invalid.append(row)

        row = copy.deepcopy(base)
        row["dependencies"][-1]["assertion"]["value_role"] = "technical"
        invalid.append(row)

        row = copy.deepcopy(base)
        row["dependencies"][-1]["assertion"]["domain_semantics"] = "observed"
        invalid.append(row)

        row = copy.deepcopy(base)
        row["dependencies"][-1]["assertion"]["values"] = []
        invalid.append(row)

        row = copy.deepcopy(base)
        row["dependencies"][-1]["assertion"]["values"] = ["ambiguous", "ambiguous"]
        invalid.append(row)

        int_profile = predicate_sources(
            value_type="int",
            match_values=(1,),
            domain_values=(1, 2),
        )["profile"]
        row = copy.deepcopy(int_profile)
        row["dependencies"][-1]["assertion"]["values"] = [True]
        invalid.append(row)

        row = copy.deepcopy(int_profile)
        row["dependencies"][-1]["assertion"]["values"] = [SAFE_MAX + 1]
        invalid.append(row)

        for value in invalid:
            with self.subTest(value=value):
                self.assertTrue(tuple(validator.iter_errors(value)))

    def test_match_values_are_canonical_in_ir_and_binding_identity(self):
        a = predicate_sources(match_values=("unique", "ambiguous"))
        b = predicate_sources(match_values=("ambiguous", "unique"))
        binding_a = a["mappings"]["mappings"][0]["native_binding"]
        binding_b = b["mappings"]["mappings"][0]["native_binding"]
        self.assertEqual(native_binding_identity(binding_a), native_binding_identity(binding_b))

        _refresh_mapping(a["mappings"]["mappings"][0])
        _refresh_mapping(b["mappings"]["mappings"][0])
        self.assertEqual(
            mapping_semantic_digest_v2(a["mappings"]["mappings"][0]),
            mapping_semantic_digest_v2(b["mappings"]["mappings"][0]),
        )

        ir = compiled_predicate_ir(match_values=("unique", "ambiguous"))
        step = ir.semantic_index[0][1][0].native_execution_binding.steps[0]
        self.assertEqual(step.match_values, ("ambiguous", "unique"))

    def test_match_values_change_binding_and_mapping_identity(self):
        a = predicate_sources(match_values=("ambiguous",))
        b = predicate_sources(match_values=("unique",))
        binding_a = a["mappings"]["mappings"][0]["native_binding"]
        binding_b = b["mappings"]["mappings"][0]["native_binding"]
        self.assertNotEqual(native_binding_identity(binding_a), native_binding_identity(binding_b))
        self.assertNotEqual(
            mapping_semantic_digest_v2(a["mappings"]["mappings"][0]),
            mapping_semantic_digest_v2(b["mappings"]["mappings"][0]),
        )

    def test_edge_step_ir_appends_defaulted_match_values(self):
        old = tfont.EdgeStepIR(
            "witness_resolution",
            "outgoing",
            "fragment",
            True,
            "str",
            "semantic-qualifier",
        )
        self.assertIsNone(old.match_values)

        ir = compiled_predicate_ir()
        step = ir.semantic_index[0][1][0].native_execution_binding.steps[0]
        self.assertEqual(step.match_values, ("ambiguous",))

    def test_forged_match_ir_fails_resolver_reconstruction(self):
        ir = compiled_predicate_ir()
        binding = ir.semantic_index[0][1][0].native_execution_binding
        step = binding.steps[0]

        class StringSubclass(str):
            pass

        forged_values = (
            [],
            (),
            ("ambiguous", "ambiguous"),
            (StringSubclass("ambiguous"),),
            (None,),
        )
        for values in forged_values:
            with self.subTest(values=values):
                forged_step = replace(step, match_values=values)
                forged = replace(binding, steps=(forged_step,))
                with self.assertRaises(Exception) as raised:
                    semantic_resolver._native_binding_projection(forged)
                self.assertEqual(category(raised.exception), "invalid_compiled_ir")

    def test_whole_match_set_needs_one_matching_domain_dependency(self):
        sources = predicate_sources(
            match_values=("ambiguous", "unique"),
            domain_values=("ambiguous",),
        )
        validate_structural_sources(sources)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(sources))
        self.assertEqual(category(raised.exception), "dependency_authority")

    def test_second_step_predicate_tracks_prior_result_as_native_source_domain(self):
        first = {
            "edge": "word_line",
            "direction": "outgoing",
            "result_node_type": "line",
            "valued": False,
        }
        second = predicate_step(
            edge="witness_resolution",
            result_node_type="fragment",
        )
        sources = edge_path_sources(
            start_node_type="word",
            steps=(first, second),
        )
        sources["profile"]["dependency_contract_version"] = 2
        dependency = edge_domain_dependency(
            sources,
            edge="witness_resolution",
            source_node_type="line",
            target_node_type="fragment",
        )
        sources["profile"]["dependencies"].append(dependency)
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_dependencies"].append(dependency["dependency_id"])
        _refresh_mapping(mapping)

        validate_structural_sources(sources)
        validate_semantic_bundle(source_bundle(sources))

        wrong = copy.deepcopy(sources)
        wrong["profile"]["dependencies"][-1]["assertion"]["source_node_type"] = "word"
        validate_structural_sources(wrong)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(wrong))
        self.assertEqual(category(raised.exception), "dependency_authority")

    def test_partial_edge_domains_cannot_be_unioned_for_one_match_set(self):
        sources = predicate_sources(
            match_values=("ambiguous", "unique"),
            domain_values=("ambiguous",),
        )
        second = edge_domain_dependency(
            sources,
            values=("unique",),
            dependency_id="dep:bhsa:witness-resolution:domain:second",
        )
        sources["profile"]["dependencies"].append(second)
        mapping = sources["mappings"]["mappings"][0]
        mapping["native_dependencies"].append(second["dependency_id"])
        _refresh_mapping(mapping)

        validate_structural_sources(sources)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(sources))
        self.assertEqual(category(raised.exception), "dependency_authority")

    def test_incoming_dependency_uses_native_source_target_orientation(self):
        sources = predicate_sources(direction="incoming")
        validate_structural_sources(sources)
        validate_semantic_bundle(source_bundle(sources))

        wrong = predicate_sources(direction="incoming")
        wrong_dep = wrong["profile"]["dependencies"][-1]
        wrong_dep["assertion"]["source_node_type"] = "fragment"
        wrong_dep["assertion"]["target_node_type"] = "line"
        validate_structural_sources(wrong)
        with self.assertRaises(SemanticValidationError) as raised:
            validate_semantic_bundle(source_bundle(wrong))
        self.assertEqual(category(raised.exception), "dependency_authority")

    def test_dependency_mismatch_dimensions_fail_authority(self):
        mutations = (
            ("edge", "other"),
            ("source_node_type", "word"),
            ("target_node_type", "word"),
            ("value_type", "int"),
        )
        for field, value in mutations:
            sources = predicate_sources()
            assertion = sources["profile"]["dependencies"][-1]["assertion"]
            assertion[field] = value
            if field == "value_type":
                assertion["values"] = [1, 2]
            validate_structural_sources(sources)
            with self.subTest(field=field):
                with self.assertRaises(SemanticValidationError) as raised:
                    validate_semantic_bundle(source_bundle(sources))
                self.assertEqual(category(raised.exception), "dependency_authority")


if __name__ == "__main__":
    unittest.main()
