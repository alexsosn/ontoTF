from __future__ import annotations

import importlib
import unittest
from dataclasses import replace

from tests.i006._fixtures import compiled_noun_ir
from ontotf.digests import canonical_json_bytes


RUNTIME = importlib.import_module("ontotf.runtime_prerequisites")


def _record(
    dependency_id: str,
    kind: str,
    assertion: dict,
    component_id: str = "bhsa-tf",
    *,
    evidence: list[dict] | None = None,
):
    value = {
        "dependency_id": dependency_id,
        "component_id": component_id,
        "kind": kind,
        "assertion": assertion,
    }
    if evidence is not None:
        value["evidence"] = evidence
    return dependency_id, canonical_json_bytes(value).decode("utf-8")


def variant_with(*records):
    variant = compiled_noun_ir(("bhsa",)).variants[0]
    signature = replace(variant.release_signature, dependency_records=tuple(records))
    return replace(variant, release_signature=signature)


class Observation:
    def __init__(self, parent_digest: str):
        self.parent_manifest_digest = parent_digest
        self.component_states = {}
        self.node_type_states = {}
        self.feature_states = {}
        self.edge_states = {}
        self.path_states = {}
        self.value_states = {}
        self.extent_states = {}

    def component(self, component_id):
        return self.component_states.get(component_id, ("unknown", None))

    def node_type(self, component_id, node_type):
        return self.node_type_states.get((component_id, node_type), "unknown")

    def feature(self, component_id, node_type, feature):
        return self.feature_states.get((component_id, node_type, feature), "unknown")

    def edge(self, component_id, edge, direction):
        return self.edge_states.get((component_id, edge, direction), "unknown")

    def path(self, component_id, steps):
        return self.path_states.get((component_id, tuple(steps)), "unknown")

    def values(self, component_id, node_type, feature):
        return self.value_states.get((component_id, node_type, feature), ("unknown", ()))

    def extent(self, component_id, node_type):
        return self.extent_states.get((component_id, node_type), ("unknown", None))


def evaluate(variant, observation):
    return RUNTIME.evaluate_runtime_prerequisites(
        variant,
        observation,
        source_contract="test:i007-kinds-v1",
    )


class I007DependencyKindsRedTests(unittest.TestCase):
    def _observation(self, variant):
        return Observation(variant.key.expected_parent_manifest_digest)

    def test_component_present_pass_fail_unknown(self):
        variant = variant_with(_record("dep:component", "component-present", {}))
        for state, expected in (("present", "pass"), ("absent", "fail"), ("unknown", "unknown")):
            with self.subTest(state=state):
                obs = self._observation(variant)
                obs.component_states["bhsa-tf"] = (state, "sha256:" + "c" * 64 if state != "unknown" else None)
                self.assertEqual(evaluate(variant, obs).dependency_results[0].result, expected)

    def test_node_type_feature_edge_and_path_have_three_state_semantics(self):
        cases = (
            ("node-type-present", {"node_type": "word"}, "node_type_states", ("bhsa-tf", "word")),
            ("feature-present", {"node_type": "word", "feature": "sp"}, "feature_states", ("bhsa-tf", "word", "sp")),
            ("edge-present", {"edge": "mother", "direction": "incoming"}, "edge_states", ("bhsa-tf", "mother", "incoming")),
            (
                "path-present",
                {"steps": [{"edge": "mother", "direction": "incoming"}, {"edge": "parent", "direction": "outgoing"}]},
                "path_states",
                ("bhsa-tf", (("mother", "incoming"), ("parent", "outgoing"))),
            ),
        )
        for kind, assertion, attr, key in cases:
            variant = variant_with(_record(f"dep:{kind}", kind, assertion))
            for state, expected in (("present", "pass"), ("absent", "fail"), ("unknown", "unknown")):
                with self.subTest(kind=kind, state=state):
                    obs = self._observation(variant)
                    getattr(obs, attr)[key] = state
                    self.assertEqual(evaluate(variant, obs).dependency_results[0].result, expected)

    def test_json_scalar_identity_keeps_bool_and_int_distinct(self):
        for authored, observed in ((False, (0,)), (0, (False,)), (True, (1,)), (1, (True,))):
            with self.subTest(authored=authored, observed=observed):
                variant = variant_with(
                    _record(
                        "dep:value",
                        "native-value-present",
                        {"node_type": "word", "feature": "sp", "value": authored, "value_semantics": "semantic"},
                    )
                )
                obs = self._observation(variant)
                obs.value_states[("bhsa-tf", "word", "sp")] = ("complete", observed)
                self.assertEqual(evaluate(variant, obs).dependency_results[0].result, "fail")

    def test_value_domain_observed_requires_declared_values_but_allows_extras(self):
        variant = variant_with(
            _record(
                "dep:domain",
                "value-domain",
                {"node_type": "word", "feature": "sp", "values": ["subs", "adj"], "domain_semantics": "observed"},
            )
        )
        obs = self._observation(variant)
        obs.value_states[("bhsa-tf", "word", "sp")] = ("complete", ("subs", "adj", "verb"))
        self.assertEqual(evaluate(variant, obs).dependency_results[0].result, "pass")
        obs.value_states[("bhsa-tf", "word", "sp")] = ("complete", ("subs", "verb"))
        self.assertEqual(evaluate(variant, obs).dependency_results[0].result, "fail")

    def test_closed_reviewed_domain_is_allowed_closure_not_occurrence_checklist(self):
        variant = variant_with(
            _record(
                "dep:domain",
                "value-domain",
                {"node_type": "word", "feature": "sp", "values": ["subs", "adj"], "domain_semantics": "closed-reviewed"},
                evidence=[{"evidence_id": "evidence:domain", "content_digest": "sha256:" + "e" * 64}],
            )
        )
        obs = self._observation(variant)
        obs.value_states[("bhsa-tf", "word", "sp")] = ("complete", ("subs",))
        self.assertEqual(evaluate(variant, obs).dependency_results[0].result, "pass")
        obs.value_states[("bhsa-tf", "word", "sp")] = ("complete", ("subs", "verb"))
        self.assertEqual(evaluate(variant, obs).dependency_results[0].result, "fail")

    def test_incomplete_value_domain_is_unknown(self):
        variant = variant_with(
            _record(
                "dep:domain",
                "value-domain",
                {"node_type": "word", "feature": "sp", "values": ["subs"], "domain_semantics": "observed"},
            )
        )
        obs = self._observation(variant)
        obs.value_states[("bhsa-tf", "word", "sp")] = ("unknown", ())
        self.assertEqual(evaluate(variant, obs).dependency_results[0].result, "unknown")

    def test_extent_interpretation_requires_explicit_metadata(self):
        variant = variant_with(
            _record(
                "dep:extent",
                "extent-interpretation",
                {"node_type": "word", "interpretation": "occurrenceSet"},
            )
        )
        obs = self._observation(variant)
        self.assertEqual(evaluate(variant, obs).dependency_results[0].result, "unknown")
        obs.extent_states[("bhsa-tf", "word")] = ("known", "textualExtent")
        self.assertEqual(evaluate(variant, obs).dependency_results[0].result, "fail")
        obs.extent_states[("bhsa-tf", "word")] = ("known", "occurrenceSet")
        self.assertEqual(evaluate(variant, obs).dependency_results[0].result, "pass")

    def test_fail_dominates_unknown_independent_of_dependency_order(self):
        failing = _record("dep:a-fail", "component-present", {})
        unknown = _record("dep:z-unknown", "extent-interpretation", {"node_type": "word", "interpretation": "noSlot"})
        for records in ((failing, unknown), (unknown, failing)):
            with self.subTest(order=[row[0] for row in records]):
                variant = variant_with(*records)
                obs = self._observation(variant)
                obs.component_states["bhsa-tf"] = ("absent", "sha256:" + "d" * 64)
                report = evaluate(variant, obs)
                self.assertEqual(report.compatibility_state, "incompatible")
                self.assertEqual(tuple(row.dependency_id for row in report.dependency_results), ("dep:a-fail", "dep:z-unknown"))


if __name__ == "__main__":
    unittest.main()
