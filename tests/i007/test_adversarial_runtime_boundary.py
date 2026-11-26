from __future__ import annotations

import importlib
import unittest
from dataclasses import replace

from tests.i006._fixtures import compiled_noun_ir
from tests.i007.test_dependency_kinds_red import _record, variant_with


RUNTIME = importlib.import_module("ontotf.runtime_prerequisites")


class AbsentComponentObservation:
    def __init__(self, parent_digest: str):
        self.parent_manifest_digest = parent_digest

    def component(self, component_id):
        return ("absent", None)

    def node_type(self, component_id, node_type):
        return "absent"

    def feature(self, component_id, node_type, feature):
        return "absent"

    def edge(self, component_id, edge, direction):
        return "absent"

    def path(self, component_id, steps):
        return "absent"

    def values(self, component_id, node_type, feature):
        return ("absent", ())

    def extent(self, component_id, node_type):
        return ("absent", None)


def evaluate(variant, observation):
    return RUNTIME.evaluate_runtime_prerequisites(
        variant,
        observation,
        source_contract="test:i007-adversarial-v1",
    )


class I007AdversarialRuntimeBoundaryTests(unittest.TestCase):
    def test_absent_component_fails_value_and_extent_dependencies(self):
        cases = (
            _record(
                "dep:value",
                "native-value-present",
                {"node_type": "word", "feature": "sp", "value": "subs", "value_semantics": "semantic"},
            ),
            _record(
                "dep:domain",
                "value-domain",
                {"node_type": "word", "feature": "sp", "values": ["subs"], "domain_semantics": "observed"},
            ),
            _record(
                "dep:extent",
                "extent-interpretation",
                {"node_type": "word", "interpretation": "occurrenceSet"},
            ),
        )
        for record in cases:
            with self.subTest(dependency_id=record[0]):
                variant = variant_with(record)
                report = evaluate(
                    variant,
                    AbsentComponentObservation(variant.key.expected_parent_manifest_digest),
                )
                self.assertEqual(report.dependency_results[0].result, "fail")
                self.assertEqual(report.compatibility_state, "incompatible")
                self.assertIsNotNone(report.dependency_results[0].observed_evidence_digest)

    def test_present_component_without_identity_is_not_a_verified_pass(self):
        variant = variant_with(_record("dep:component", "component-present", {}))
        observation = AbsentComponentObservation(variant.key.expected_parent_manifest_digest)
        observation.component = lambda component_id: ("present", None)
        report = evaluate(variant, observation)
        self.assertEqual(report.dependency_results[0].result, "unknown")
        self.assertEqual(report.compatibility_state, "unverified")
        self.assertIsNone(report.dependency_results[0].observed_evidence_digest)

    def test_forged_nested_variant_authority_fails_as_runtime_evaluation_error(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        observation = AbsentComponentObservation(variant.key.expected_parent_manifest_digest)
        for field, forged_value in (
            ("key", object()),
            ("release_key", object()),
            ("release_signature", object()),
        ):
            with self.subTest(field=field):
                forged = replace(variant, **{field: forged_value})
                with self.assertRaises(RUNTIME.RuntimeEvaluationError):
                    evaluate(forged, observation)

    def test_mutable_nested_variant_key_field_is_contained_before_equality_or_hashing(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        forged = replace(variant, key=replace(variant.key, corpus_id=[]))
        observation = AbsentComponentObservation(variant.key.expected_parent_manifest_digest)
        with self.assertRaises(RUNTIME.RuntimeEvaluationError):
            evaluate(forged, observation)

    def test_repeated_variant_contract_fields_must_match_release_signature(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        observation = AbsentComponentObservation(variant.key.expected_parent_manifest_digest)
        fields = (
            "profile_schema_version",
            "profile_catalog_version",
            "dependency_contract_version",
            "mapping_schema_version",
            "mapping_semantic_algorithm",
            "projection_semantic_algorithm",
        )
        for field in fields:
            with self.subTest(field=field):
                value = getattr(variant, field)
                forged_value = value + 1 if type(value) is int else value + ":forged"
                forged = replace(variant, **{field: forged_value})
                with self.assertRaises(RUNTIME.RuntimeEvaluationError):
                    evaluate(forged, observation)


if __name__ == "__main__":
    unittest.main()
