from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tfont.source_validation import SourceValidationError, validate_source  # noqa: E402

SCHEMA_ROOT = ROOT / "src" / "tfont" / "schemas"
PROFILE_SCHEMA = SCHEMA_ROOT / "profile.schema.json"
RESEARCH = ROOT / "docs" / "research" / "P-002-i004-source-contract-amendment.md"
PLAN = ROOT / "docs" / "plans" / "P-002-i004-source-contract-amendment.md"

TF_NATIVE_KINDS_V1 = {
    "component-present",
    "node-type-present",
    "feature-present",
    "edge-present",
    "path-present",
    "native-value-present",
    "value-domain",
    "extent-interpretation",
}
TF_NATIVE_KINDS_V2 = TF_NATIVE_KINDS_V1 | {"edge-value-domain"}
TF_NATIVE_KINDS = TF_NATIVE_KINDS_V1
FORBIDDEN_RUNTIME_KINDS = {
    "adapter-capability",
    "sidecar-field",
    "carrier-interpretation",
}
EXTENT_MODES = {"textualExtent", "occurrenceSet", "technicalAnchor", "noSlot"}


def assertion_for(kind: str) -> dict:
    return {
        "component-present": {},
        "node-type-present": {"node_type": "word"},
        "feature-present": {"node_type": "word", "feature": "sp"},
        "edge-present": {"edge": "mother", "direction": "outgoing"},
        "path-present": {
            "steps": [
                {"edge": "mother", "direction": "outgoing"},
                {"edge": "mother", "direction": "incoming"},
            ]
        },
        "native-value-present": {
            "node_type": "word",
            "feature": "gn",
            "value": "m",
            "value_semantics": "semantic",
        },
        "value-domain": {
            "node_type": "word",
            "feature": "gn",
            "values": ["m", "f", "NA", "unknown"],
            "domain_semantics": "observed",
        },
        "extent-interpretation": {
            "node_type": "word",
            "interpretation": "textualExtent",
        },
        "edge-value-domain": {
            "edge": "witness_resolution",
            "source_node_type": "line",
            "target_node_type": "fragment",
            "value_type": "str",
            "value_role": "semantic-qualifier",
            "values": ["ambiguous", "unique"],
            "domain_semantics": "closed-reviewed",
        },
    }[kind]


def dependency(**overrides):
    kind = overrides.get("kind", "feature-present")
    record = {
        "dependency_id": "dep:word-pos",
        "component_id": "test-tf",
        "kind": kind,
        "assertion": assertion_for(kind) if kind in TF_NATIVE_KINDS_V2 else {},
        "evidence": [
            {
                "evidence_id": "evidence:test",
                "content_digest": "sha256:evidence",
            }
        ],
    }
    record.update(overrides)
    return record


def profile_v2():
    return {
        "schema_version": 2,
        "profile_id": "tfont-test",
        "profile_version": "0.2.0",
        "semantic_domains": ["morphology"],
        "parent_component_manifest": "parent/expected-components.json",
        "required_components": ["test-tf"],
        "ontology_locks": ["olia-test"],
        "mapping_sources": ["mappings/test.yaml"],
        "dependency_contract_version": 1,
        "dependencies": [dependency()],
        "minimum_tfont_runtime": "0.1.0",
        "license": "CC-BY-4.0",
    }


class ProfileDependencyContractTests(unittest.TestCase):
    def validate(self, instance):
        validate_source(instance, "profile", schema_root=SCHEMA_ROOT)

    def assert_invalid(self, instance):
        with self.assertRaises(SourceValidationError):
            self.validate(instance)

    def dependency_kind_enum(self) -> set[str]:
        schema = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))
        return set(schema["$defs"]["dependency"]["properties"]["kind"]["enum"])

    def profile_with_dependency(self, dep: dict) -> dict:
        instance = profile_v2()
        instance["dependencies"] = [dep]
        return instance

    def test_v2_profile_with_dependency_is_valid(self):
        self.validate(profile_v2())

    def test_v1_profile_is_rejected_by_current_contract(self):
        instance = profile_v2()
        instance["schema_version"] = 1
        self.assert_invalid(instance)

    def test_dependencies_are_required_and_nonempty(self):
        missing = profile_v2()
        del missing["dependencies"]
        self.assert_invalid(missing)

        empty = profile_v2()
        empty["dependencies"] = []
        self.assert_invalid(empty)

    def test_dependency_contract_versions_are_closed_to_v1_and_v2(self):
        for supported in (1, 2):
            instance = profile_v2()
            instance["dependency_contract_version"] = supported
            with self.subTest(version=supported):
                self.validate(instance)
        for unsupported in (0, 3, 999):
            instance = profile_v2()
            instance["dependency_contract_version"] = unsupported
            with self.subTest(version=unsupported):
                self.assert_invalid(instance)

    def test_dependency_kind_set_is_exact_and_external_runtime_kinds_are_rejected(self):
        self.assertEqual(self.dependency_kind_enum(), TF_NATIVE_KINDS_V2)
        for kind in sorted(FORBIDDEN_RUNTIME_KINDS | {"semantic-target"}):
            with self.subTest(kind=kind):
                self.assert_invalid(self.profile_with_dependency(dependency(kind=kind)))

    def test_edge_value_domain_is_dependency_v2_only(self):
        dep = dependency(kind="edge-value-domain")

        v1 = self.profile_with_dependency(dep)
        self.assert_invalid(v1)

        v2 = self.profile_with_dependency(dep)
        v2["dependency_contract_version"] = 2
        self.validate(v2)

    def test_dependency_common_fields_are_required(self):
        for missing in ("dependency_id", "component_id", "kind", "assertion"):
            dep = dependency()
            del dep[missing]
            with self.subTest(missing=missing):
                self.assert_invalid(self.profile_with_dependency(dep))

    def test_dependency_evidence_binding_and_common_envelope_are_closed(self):
        dep = dependency()
        dep["evidence"][0]["unexpected"] = True
        self.assert_invalid(self.profile_with_dependency(dep))

        forbidden = (
            "semantic_target",
            "semantic_profile",
            "semantic_capability",
            "external_target",
            "ontology_bundle",
            "publication_relation",
            "mapping_assessment",
            "authority_reference",
        )
        for field in forbidden:
            dep = dependency()
            dep[field] = "forbidden"
            with self.subTest(field=field):
                self.assert_invalid(self.profile_with_dependency(dep))

    def test_all_eight_canonical_assertion_shapes_are_valid(self):
        instance = profile_v2()
        instance["dependencies"] = [
            dependency(dependency_id=f"dep:{index}", kind=kind, assertion=assertion_for(kind))
            for index, kind in enumerate(sorted(TF_NATIVE_KINDS))
        ]
        self.validate(instance)

    def test_component_present_assertion_is_exactly_empty(self):
        valid = dependency(kind="component-present", assertion={})
        self.validate(self.profile_with_dependency(valid))

        invalid = dependency(kind="component-present", assertion={"path": "outside.tf"})
        self.assert_invalid(self.profile_with_dependency(invalid))

    def test_required_fields_are_pinned_per_assertion_kind(self):
        required = {
            "node-type-present": ("node_type",),
            "feature-present": ("node_type", "feature"),
            "edge-present": ("edge", "direction"),
            "path-present": ("steps",),
            "native-value-present": ("node_type", "feature", "value", "value_semantics"),
            "value-domain": ("node_type", "feature", "values", "domain_semantics"),
            "extent-interpretation": ("node_type", "interpretation"),
        }
        for kind, fields in required.items():
            for field in fields:
                assertion = assertion_for(kind).copy()
                del assertion[field]
                with self.subTest(kind=kind, field=field):
                    self.assert_invalid(
                        self.profile_with_dependency(dependency(kind=kind, assertion=assertion))
                    )

    def test_all_assertion_shapes_reject_unknown_fields(self):
        for kind in sorted(TF_NATIVE_KINDS):
            assertion = assertion_for(kind).copy()
            assertion["sidecar_path"] = "outside/records.json"
            with self.subTest(kind=kind):
                self.assert_invalid(
                    self.profile_with_dependency(dependency(kind=kind, assertion=assertion))
                )

    def test_edge_and_path_direction_are_closed(self):
        for bad in ("forward", "reverse", "both", ""):
            with self.subTest(edge_direction=bad):
                self.assert_invalid(
                    self.profile_with_dependency(
                        dependency(kind="edge-present", assertion={"edge": "mother", "direction": bad})
                    )
                )

            with self.subTest(path_direction=bad):
                self.assert_invalid(
                    self.profile_with_dependency(
                        dependency(
                            kind="path-present",
                            assertion={"steps": [{"edge": "mother", "direction": bad}]},
                        )
                    )
                )

    def test_path_steps_are_nonempty_closed_and_ordered_source_data(self):
        self.assert_invalid(
            self.profile_with_dependency(dependency(kind="path-present", assertion={"steps": []}))
        )
        self.assert_invalid(
            self.profile_with_dependency(
                dependency(
                    kind="path-present",
                    assertion={
                        "steps": [
                            {"edge": "mother", "direction": "outgoing", "source_path": "x"}
                        ]
                    },
                )
            )
        )

        one = dependency(
            kind="path-present",
            assertion={
                "steps": [
                    {"edge": "a", "direction": "outgoing"},
                    {"edge": "b", "direction": "incoming"},
                ]
            },
        )
        two = dependency(
            kind="path-present",
            assertion={
                "steps": [
                    {"edge": "b", "direction": "incoming"},
                    {"edge": "a", "direction": "outgoing"},
                ]
            },
        )
        self.validate(self.profile_with_dependency(one))
        self.validate(self.profile_with_dependency(two))
        self.assertNotEqual(one["assertion"], two["assertion"])

    def test_native_value_requires_explicit_semantic_marker_including_empty_and_null(self):
        for value in ("", None, "m", 1, True):
            assertion = {
                "node_type": "word",
                "feature": "gn",
                "value": value,
                "value_semantics": "semantic",
            }
            with self.subTest(value=value):
                self.validate(
                    self.profile_with_dependency(
                        dependency(kind="native-value-present", assertion=assertion)
                    )
                )

        missing = assertion_for("native-value-present").copy()
        del missing["value_semantics"]
        self.assert_invalid(
            self.profile_with_dependency(
                dependency(kind="native-value-present", assertion=missing)
            )
        )
        wrong = assertion_for("native-value-present").copy()
        wrong["value_semantics"] = "storage-present"
        self.assert_invalid(
            self.profile_with_dependency(dependency(kind="native-value-present", assertion=wrong))
        )

    def test_value_domain_requires_values_and_explicit_closure_status(self):
        for invalid_assertion in (
            {"node_type": "word", "feature": "gn", "values": [], "domain_semantics": "observed"},
            {"node_type": "word", "feature": "gn", "values": ["m", "m"], "domain_semantics": "observed"},
            {"node_type": "word", "feature": "gn", "values": ["m"]},
            {"node_type": "word", "feature": "gn", "values": ["m"], "domain_semantics": "inferred-closed"},
        ):
            with self.subTest(assertion=invalid_assertion):
                self.assert_invalid(
                    self.profile_with_dependency(
                        dependency(kind="value-domain", assertion=invalid_assertion)
                    )
                )

        observed = dependency(
            kind="value-domain",
            assertion={
                "node_type": "word",
                "feature": "gn",
                "values": ["m", "f"],
                "domain_semantics": "observed",
            },
            evidence=[],
        )
        self.validate(self.profile_with_dependency(observed))

    def test_closed_reviewed_domain_requires_nonempty_evidence(self):
        assertion = {
            "node_type": "word",
            "feature": "gn",
            "values": ["m", "f"],
            "domain_semantics": "closed-reviewed",
        }
        missing = dependency(kind="value-domain", assertion=assertion)
        del missing["evidence"]
        self.assert_invalid(self.profile_with_dependency(missing))

        empty = dependency(kind="value-domain", assertion=assertion, evidence=[])
        self.assert_invalid(self.profile_with_dependency(empty))

        valid = dependency(kind="value-domain", assertion=assertion)
        self.validate(self.profile_with_dependency(valid))

    def test_extent_interpretation_is_closed_to_tf_native_modes(self):
        for mode in sorted(EXTENT_MODES):
            with self.subTest(mode=mode):
                self.validate(
                    self.profile_with_dependency(
                        dependency(
                            kind="extent-interpretation",
                            assertion={"node_type": "word", "interpretation": mode},
                        )
                    )
                )

        for invalid in ("sidecar", "externalRecord", "nativeAdapter", ""):
            with self.subTest(mode=invalid):
                self.assert_invalid(
                    self.profile_with_dependency(
                        dependency(
                            kind="extent-interpretation",
                            assertion={"node_type": "word", "interpretation": invalid},
                        )
                    )
                )

    def test_external_record_escape_attempt_is_rejected_under_allowed_kind(self):
        self.assert_invalid(
            self.profile_with_dependency(
                dependency(
                    kind="extent-interpretation",
                    assertion={
                        "node_type": "word",
                        "interpretation": "technicalAnchor",
                        "external_record": {"path": "sidecar.json", "id": "x"},
                    },
                )
            )
        )

    def test_canonical_documents_pin_a001_and_p003_boundaries(self):
        research = RESEARCH.read_text(encoding="utf-8")
        plan = PLAN.read_text(encoding="utf-8")
        combined = research + "\n" + plan
        lower = combined.lower()

        self.assertIn("a-001", lower)
        self.assertIn("tf-native", lower)
        self.assertIn("p-003", lower)
        self.assertIn("does not imply a fetch/storage capability", lower)
        self.assertIn("additionalproperties: false", lower)
        self.assertIn("closed-reviewed", lower)
        self.assertNotIn("carrier kind is `tf-node` or `native-adapter`", lower)
        self.assertNotIn("a `native-adapter` entity is outside the tf warp", lower)


if __name__ == "__main__":
    unittest.main()
