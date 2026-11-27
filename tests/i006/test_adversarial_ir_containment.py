from __future__ import annotations

import importlib
import unittest
from dataclasses import replace

from ontotf.semantic_ir import EdgeStepIR, native_binding_identity
from tests.i006._fixtures import compiled_noun_ir
from tests.i006.test_semantic_resolver_contract import prerequisite_for, request_for


RESOLVER = importlib.import_module("ontotf.semantic_resolver")


def assert_problem(testcase: unittest.TestCase, category: str, callable_, *args):
    with testcase.assertRaises(RESOLVER.SemanticResolutionError) as raised:
        callable_(*args)
    testcase.assertEqual(raised.exception.problem.category, category)


def native_projection(binding):
    result = {}
    for field in (
        "component_id",
        "node_type",
        "feature",
        "edge",
        "direction",
        "interpretation",
        "execution_shape",
    ):
        value = getattr(binding, field)
        if value is not None:
            result[field] = value
    if binding.value_present:
        result["value"] = binding.value
    if binding.closed_values is not None:
        result["closed_values"] = list(binding.closed_values)
    if binding.steps is not None:
        result["steps"] = [
            {"edge": step.edge, "direction": step.direction}
            for step in binding.steps
        ]
    return result


class I006AdversarialIRContainmentTests(unittest.TestCase):
    def resolve_bad_row(self, ir, key, forged_row):
        bad_ir = replace(ir, semantic_index=((key, (forged_row,)),))
        state = prerequisite_for(RESOLVER, bad_ir.variants[0])
        assert_problem(
            self,
            "invalid_compiled_ir",
            RESOLVER.semantic_resolve,
            bad_ir,
            request_for(RESOLVER, ("bhsa",)),
            (state,),
        )

    def test_mutable_native_dependencies_cannot_enter_frozen_plan(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        self.resolve_bad_row(
            ir,
            key,
            replace(rows[0], native_dependencies=list(rows[0].native_dependencies)),
        )

    def test_non_string_native_dependency_is_contained_as_invalid_compiled_ir(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        self.resolve_bad_row(ir, key, replace(rows[0], native_dependencies=([],)))

    def test_mutable_evidence_cannot_enter_frozen_plan(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        self.resolve_bad_row(
            ir,
            key,
            replace(rows[0], mapping_evidence=list(rows[0].mapping_evidence)),
        )

    def test_malformed_evidence_element_is_invalid_compiled_ir(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        self.resolve_bad_row(ir, key, replace(rows[0], mapping_evidence=(object(),)))

    def test_evidence_fingerprint_fields_must_be_deeply_immutable(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        evidence = rows[0].mapping_evidence[0]
        forged_evidence = replace(evidence, content_digest=[])
        self.resolve_bad_row(
            ir,
            key,
            replace(rows[0], mapping_evidence=(forged_evidence,)),
        )

    def test_malformed_bundle_requirement_is_invalid_compiled_ir(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        self.resolve_bad_row(
            ir,
            key,
            replace(rows[0], ontology_bundle_requirement=object()),
        )

    def test_mutable_native_binding_steps_cannot_enter_frozen_plan(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        binding = replace(
            rows[0].native_execution_binding,
            steps=[EdgeStepIR("mother", "outgoing")],
        )
        identity = native_binding_identity(native_projection(binding))
        self.resolve_bad_row(
            ir,
            key,
            replace(
                rows[0],
                native_execution_binding=binding,
                native_execution_binding_identity=identity,
            ),
        )

    def test_mutable_native_binding_closed_values_cannot_enter_frozen_plan(self):
        ir = compiled_noun_ir(("bhsa",))
        key, rows = ir.semantic_index[0]
        binding = replace(rows[0].native_execution_binding, closed_values=["subs"])
        identity = native_binding_identity(native_projection(binding))
        self.resolve_bad_row(
            ir,
            key,
            replace(
                rows[0],
                native_execution_binding=binding,
                native_execution_binding_identity=identity,
            ),
        )

    def test_mutable_mapping_review_field_is_rejected_before_plan_construction(self):
        ir = compiled_noun_ir(("bhsa",))
        _key, rows = ir.semantic_index[0]
        row = rows[0]
        forged_review = replace(row.mapping_review, review_id=[])
        signature = ir.variants[0].release_signature
        forged_mapping_reviews = tuple(
            (mapping_id, forged_review if mapping_id == row.mapping_id else review)
            for mapping_id, review in signature.mapping_reviews
        )
        forged_signature = replace(signature, mapping_reviews=forged_mapping_reviews)
        assert_problem(
            self,
            "invalid_compiled_ir",
            RESOLVER.profile_release_fingerprint,
            forged_signature,
        )

    def test_mutable_ontology_lock_field_is_rejected_before_plan_construction(self):
        ir = compiled_noun_ir(("bhsa",))
        _key, rows = ir.semantic_index[0]
        row = rows[0]
        forged_lock = replace(row.ontology_lock, term_namespace=[])
        signature = ir.variants[0].release_signature
        forged_locks = tuple(
            forged_lock if lock.lock_id == forged_lock.lock_id else lock
            for lock in signature.ontology_locks
        )
        forged_signature = replace(signature, ontology_locks=forged_locks)
        assert_problem(
            self,
            "invalid_compiled_ir",
            RESOLVER.profile_release_fingerprint,
            forged_signature,
        )


if __name__ == "__main__":
    unittest.main()
