from __future__ import annotations

import importlib
import unittest

from tests.i005._fixtures import noun_sources, source_bundle, validate_structural_sources
from tests.i006._fixtures import compiled_noun_ir, with_bundle_digest
from tfont.semantic_ir import compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle


class FakeObservation:
    def __init__(self, parent_digest: str, *, values_state: str = "complete", values=("subs",)):
        self.parent_manifest_digest = parent_digest
        self.values_state = values_state
        self._values = tuple(values)

    def component(self, component_id: str):
        return ("present", f"digest:{component_id}")

    def node_type(self, component_id: str, node_type: str):
        return "present"

    def feature(self, component_id: str, node_type: str, feature: str):
        return "present"

    def edge(self, component_id: str, edge: str, direction: str):
        return "present"

    def path(self, component_id: str, steps):
        return "present"

    def values(self, component_id: str, node_type: str, feature: str):
        return (self.values_state, self._values)

    def extent(self, component_id: str, node_type: str):
        return ("unknown", None)


class I007RuntimePrerequisiteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = importlib.import_module("tfont.runtime_prerequisites")

    def _variant(self):
        return compiled_noun_ir(("bhsa",)).variants[0]

    def _evaluate(self, variant, observation, **kwargs):
        return self.runtime.evaluate_runtime_prerequisites(
            variant,
            observation,
            source_contract="test:i007-observation-v1",
            **kwargs,
        )

    def test_public_module_and_versioned_contract_exist(self):
        self.assertTrue(self.runtime.RUNTIME_EVALUATION_CONTRACT.endswith("-v1"))
        self.assertTrue(self.runtime.OBSERVATION_FINGERPRINT_ALGORITHM.endswith("-v1"))
        self.assertTrue(self.runtime.RUNTIME_REPORT_FINGERPRINT_ALGORITHM.endswith("-v1"))

    def test_exact_parent_and_complete_passing_closure_yields_verified_exact(self):
        variant = self._variant()
        report = self._evaluate(
            variant,
            FakeObservation(variant.key.expected_parent_manifest_digest),
        )
        self.assertEqual(report.compatibility_state, "verified-exact")
        self.assertEqual(tuple(row.result for row in report.dependency_results), ("pass",))
        self.assertIsNotNone(report.dependency_results[0].observed_evidence_digest)
        prerequisite = report.to_prerequisite()
        self.assertEqual(prerequisite.parent_state, "verified-exact")
        self.assertEqual(prerequisite.variant, variant.key)
        self.assertEqual(prerequisite.ontology_bundle_state, "not-required")
        self.assertIsNone(prerequisite.active_ontology_bundle_digest)

    def test_changed_parent_and_complete_passing_closure_yields_verified_compatible(self):
        sources = noun_sources("bhsa", parent_char="a")
        sources["profile"]["parent_compatibility"] = "dependency-verified"
        validate_structural_sources(sources)
        variant = compile_semantic_ir((validate_semantic_bundle(source_bundle(sources)),)).variants[0]
        report = self._evaluate(variant, FakeObservation("sha256:" + "9" * 64))
        self.assertEqual(report.compatibility_state, "verified-compatible")
        self.assertEqual(report.to_prerequisite().parent_state, "verified-compatible")

    def test_known_dependency_failure_dominates_parent_match(self):
        variant = self._variant()
        report = self._evaluate(
            variant,
            FakeObservation(variant.key.expected_parent_manifest_digest, values=()),
        )
        self.assertEqual(report.compatibility_state, "incompatible")
        self.assertEqual(report.dependency_results[0].result, "fail")
        self.assertIsNotNone(report.dependency_results[0].observed_evidence_digest)
        self.assertEqual(report.to_prerequisite().parent_state, "incompatible")

    def test_incomplete_value_observation_yields_unverified(self):
        variant = self._variant()
        report = self._evaluate(
            variant,
            FakeObservation(
                variant.key.expected_parent_manifest_digest,
                values_state="unknown",
                values=(),
            ),
        )
        self.assertEqual(report.compatibility_state, "unverified")
        self.assertEqual(report.dependency_results[0].result, "unknown")
        self.assertIsNone(report.dependency_results[0].observed_evidence_digest)
        self.assertEqual(report.to_prerequisite().parent_state, "unverified")

    def test_required_bundle_is_orthogonal_to_parent_compatibility(self):
        variant = with_bundle_digest(compiled_noun_ir(("bhsa",)), "sha256:" + "b" * 64).variants[0]
        observation = FakeObservation(variant.key.expected_parent_manifest_digest)

        unavailable = self._evaluate(variant, observation)
        self.assertEqual(unavailable.compatibility_state, "verified-exact")
        self.assertEqual(unavailable.to_prerequisite().parent_state, "verified-exact")
        self.assertEqual(unavailable.to_prerequisite().ontology_bundle_state, "unavailable")

        verified = self._evaluate(
            variant,
            observation,
            active_ontology_bundle_digest=variant.key.ontology_bundle_digest,
        )
        self.assertEqual(verified.compatibility_state, "verified-exact")
        self.assertEqual(verified.to_prerequisite().ontology_bundle_state, "verified")
        self.assertEqual(
            verified.to_prerequisite().active_ontology_bundle_digest,
            variant.key.ontology_bundle_digest,
        )
        self.assertNotEqual(unavailable.report_fingerprint, verified.report_fingerprint)

    def test_report_projection_is_accepted_by_i006_resolver(self):
        resolver = importlib.import_module("tfont.semantic_resolver")
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        report = self._evaluate(
            variant,
            FakeObservation(variant.key.expected_parent_manifest_digest),
        )
        request = resolver.SemanticResolveRequest(
            key=ir.semantic_index[0][0],
            corpora=("bhsa",),
        )
        result = resolver.semantic_resolve(ir, request, (report.to_prerequisite(),))
        self.assertEqual(len(result.plans), 1)
        self.assertEqual(result.plans[0].parent_state, "verified-exact")


if __name__ == "__main__":
    unittest.main()
