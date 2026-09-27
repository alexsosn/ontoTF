from __future__ import annotations

import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tfont.source_validation import (  # noqa: E402
    SCHEMA_FILES,
    SourceValidationError,
    load_and_validate,
    load_source,
    loads_source,
    validate_source,
)

SCHEMA_ROOT = ROOT / "src" / "tfont" / "schemas"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


def evidence_binding(evidence_id: str = "evidence:test") -> dict:
    return {"evidence_id": evidence_id, "content_digest": "sha256:evidence"}


def review_record(review_id: str = "review:test", digest: str = "sha256:mapping") -> dict:
    return {
        "review_id": review_id,
        "status": "reviewed",
        "reviewed_mapping_digest": digest,
        "reviewer_id": "reviewer:test",
        "reviewed_at": "2026-09-05T21:00:00Z",
        "review_source": "offline:test",
        "review_method": "independent-skeptical",
    }


def exact_projection() -> dict:
    return {
        "projection_id": "projection:test",
        "target": "https://example.org/term",
        "reference_kind": "semantic-pivot",
        "query_role": "semantic-constraint",
        "formal_kind": "class",
        "semantic_role": "annotation-value",
        "profile_id": "linguistic",
        "capability_id": "linguistic.morphology",
        "assessment": "exact",
        "ontology_lock": "missing-lock-is-semantic-check",
        "native_execution_binding": {
            "component_id": "missing-component-is-semantic-check",
            "feature": "gn",
            "value": "m",
        },
        "evidence": [evidence_binding("missing-evidence-is-semantic-check")],
        "review": review_record("review:projection", "sha256:projection"),
        "projection_semantic_digest": "sha256:projection",
    }


def exact_mapping() -> dict:
    return {
        "mapping_id": "mapping:test",
        "corpus_id": "corpus:test",
        "native_binding": {
            "component_id": "missing-component-is-semantic-check",
            "feature": "gn",
            "value": "m",
        },
        "native_dependencies": ["missing-dependency-is-semantic-check"],
        "profiles": ["linguistic"],
        "capabilities": ["linguistic.morphology"],
        "native_state": "positive",
        "projections": [exact_projection()],
        "ambiguous_candidates": [],
        "external_references": [],
        "evidence": [evidence_binding("missing-evidence-is-semantic-check")],
        "review": review_record(),
        "mapping_semantic_digest": "sha256:mapping",
        "rationale": "fixture",
    }


def minimal_valid_instances() -> dict[str, dict]:
    return {
        "profile": {
            "schema_version": 2,
            "profile_id": "tfont-test",
            "profile_version": "0.2.0",
            "semantic_domains": ["morphology"],
            "parent_component_manifest": "parent/expected-components.json",
            "required_components": ["test-tf"],
            "ontology_locks": ["olia-test"],
            "mapping_sources": ["mappings/test.yaml"],
            "dependency_contract_version": 1,
            "dependencies": [
                {
                    "dependency_id": "dep:test",
                    "component_id": "test-tf",
                    "kind": "component-present",
                    "assertion": {},
                }
            ],
            "minimum_tfont_runtime": "0.1.0",
            "license": "CC-BY-4.0",
        },
        "parent-component-manifest": {
            "algorithm": "tfont-parent-components-sha256-v1",
            "components": [
                {
                    "component_id": "test-tf",
                    "kind": "tf-payload",
                    "identity_algorithm": "tfont-tf-files-sha256-v1",
                    "content_digest": "sha256:test",
                }
            ],
        },
        "ontology-lock": {
            "lock_id": "olia-test",
            "ontology_id": "olia",
            "support_tier": "core",
            "term_namespace": "https://example.org/olia#",
            "release": "test-release",
            "source_uri": "https://example.org/olia.ttl",
            "content_digest": "sha256:ontology",
            "license": "CC-BY-4.0",
            "snapshot_artifact": "ontology/olia.ttl",
            "terms_used": ["https://example.org/olia#Noun"],
        },
        "evidence": {
            "evidence_id": "evidence:test",
            "kind": "native-doc",
            "source_uri": "https://example.org/native-doc",
            "content_mode": "external-payload",
            "content_digest": "sha256:evidence",
        },
        "review": review_record(),
        "mapping": {"schema_version": 2, "mappings": [exact_mapping()]},
        "compatibility-report": {
            "compatibility_report_id": "tfont-compatibility-sha256-v1:test",
            "report_digest": "sha256:report",
            "profile_id": "tfont-test",
            "profile_version": "0.1.0",
            "profile_semantic_digest": "sha256:profile",
            "expected_parent_manifest_digest": "sha256:expected",
            "observed_parent_manifest_digest": "sha256:observed",
            "state": "verified-compatible",
            "changed_components": ["test-sidecar"],
            "dependency_results": [
                {
                    "dependency_id": "dep:test",
                    "component_id": "test-sidecar",
                    "result": "pass",
                    "evaluator_rule_version": "1",
                }
            ],
            "evaluator_version": "1",
            "incomplete_reasons": [],
            "failure_reasons": [],
        },
    }


class SchemaContractTests(unittest.TestCase):
    def test_registry_and_all_registered_schema_files_exist(self):
        expected = {
            "profile",
            "parent-component-manifest",
            "ontology-lock",
            "evidence",
            "review",
            "mapping",
            "compatibility-report",
            "coverage-manifest",
        }
        self.assertEqual(set(SCHEMA_FILES), expected)
        for schema_name, filename in SCHEMA_FILES.items():
            with self.subTest(schema=schema_name):
                self.assertTrue((SCHEMA_ROOT / filename).is_file())

    def test_schemas_declare_2020_12_and_self_validate(self):
        from jsonschema import Draft202012Validator

        for schema_name, filename in SCHEMA_FILES.items():
            with self.subTest(schema=schema_name):
                schema = json.loads((SCHEMA_ROOT / filename).read_text(encoding="utf-8"))
                self.assertEqual(schema.get("$schema"), DRAFT_2020_12)
                Draft202012Validator.check_schema(schema)

    def test_minimal_valid_instance_for_every_schema(self):
        for schema_name, instance in minimal_valid_instances().items():
            with self.subTest(schema=schema_name):
                validate_source(instance, schema_name, schema_root=SCHEMA_ROOT)

    def test_parent_component_rejects_independent_required_flag(self):
        instance = minimal_valid_instances()["parent-component-manifest"]
        instance["components"][0]["required"] = True
        with self.assertRaises(SourceValidationError) as raised:
            validate_source(instance, "parent-component-manifest", schema_root=SCHEMA_ROOT)
        self.assertEqual(raised.exception.problem.category, "schema_validation")

    def test_evidence_content_mode_shapes_are_structural(self):
        external = minimal_valid_instances()["evidence"]
        external["reviewed_content"] = {"statement": "not allowed for payload mode"}
        with self.assertRaises(SourceValidationError):
            validate_source(external, "evidence", schema_root=SCHEMA_ROOT)

        normalized = minimal_valid_instances()["evidence"]
        normalized["content_mode"] = "normalized-record"
        with self.assertRaises(SourceValidationError):
            validate_source(normalized, "evidence", schema_root=SCHEMA_ROOT)

        normalized["reviewed_content"] = {"statement": "reviewed"}
        validate_source(normalized, "evidence", schema_root=SCHEMA_ROOT)

    def test_review_requires_digest_and_audit_provenance(self):
        for missing in (
            "reviewed_mapping_digest",
            "reviewer_id",
            "reviewed_at",
            "review_source",
            "review_method",
        ):
            instance = review_record()
            del instance[missing]
            with self.subTest(missing=missing), self.assertRaises(SourceValidationError):
                validate_source(instance, "review", schema_root=SCHEMA_ROOT)

    def test_positive_projection_requires_target_lock_and_no_candidates(self):
        for field in ("target", "ontology_lock"):
            mapping = exact_mapping()
            del mapping["projections"][0][field]
            with self.subTest(field=field), self.assertRaises(SourceValidationError):
                validate_source({"schema_version": 2, "mappings": [mapping]}, "mapping", schema_root=SCHEMA_ROOT)

        mapping = exact_mapping()
        mapping["ambiguous_candidates"] = [
            {
                "candidate_id": "candidate:test",
                "target": "https://example.org/candidate",
                "reference_kind": "semantic-pivot",
                "query_role": "semantic-constraint",
                "formal_kind": "class",
                "semantic_role": "annotation-value",
                "profile_id": "linguistic",
                "capability_id": "linguistic.morphology",
                "assessment_candidate": "close",
                "ontology_lock": "lock:test",
                "evidence": [evidence_binding()],
            }
        ]
        with self.assertRaises(SourceValidationError):
            validate_source({"schema_version": 2, "mappings": [mapping]}, "mapping", schema_root=SCHEMA_ROOT)

    def test_ambiguous_requires_candidate_specific_ontology_lock(self):
        mapping = exact_mapping()
        projection = mapping["projections"].pop()
        mapping["native_state"] = "ambiguous"
        mapping["ambiguous_candidates"] = [
            {
                "candidate_id": "candidate:test",
                "target": projection["target"],
                "reference_kind": projection["reference_kind"],
                "query_role": projection["query_role"],
                "formal_kind": projection["formal_kind"],
                "semantic_role": projection["semantic_role"],
                "profile_id": projection["profile_id"],
                "capability_id": projection["capability_id"],
                "assessment_candidate": "close",
                "evidence": [evidence_binding()],
            }
        ]
        with self.assertRaises(SourceValidationError):
            validate_source({"schema_version": 2, "mappings": [mapping]}, "mapping", schema_root=SCHEMA_ROOT)

        mapping["ambiguous_candidates"][0]["ontology_lock"] = "candidate-lock"
        validate_source({"schema_version": 2, "mappings": [mapping]}, "mapping", schema_root=SCHEMA_ROOT)

    def test_native_only_and_unsupported_require_zero_target_arrays(self):
        for state in ("native-only", "unsupported"):
            valid = exact_mapping()
            valid["native_state"] = state
            valid["projections"] = []
            valid["ambiguous_candidates"] = []
            validate_source({"schema_version": 2, "mappings": [valid]}, "mapping", schema_root=SCHEMA_ROOT)

            invalid = copy.deepcopy(valid)
            invalid["projections"] = [exact_projection()]
            with self.subTest(state=state), self.assertRaises(SourceValidationError):
                validate_source({"schema_version": 2, "mappings": [invalid]}, "mapping", schema_root=SCHEMA_ROOT)

    def test_structurally_valid_unresolved_ids_do_not_fail_i001(self):
        validate_source(
            {"schema_version": 2, "mappings": [exact_mapping()]},
            "mapping",
            schema_root=SCHEMA_ROOT,
        )

    def test_legacy_v1_mapping_is_rejected(self):
        legacy = {
            "schema_version": 1,
            "mappings": [
                {
                    "mapping_id": "legacy",
                    "profile_id": "old",
                    "native_selector": {"kind": "feature-value"},
                    "native_dependencies": [],
                    "external_target": "https://example.org/term",
                    "candidate_projections": [],
                    "assessment": "exact",
                    "publication_relation": None,
                    "applicability": {},
                    "ontology_lock": "lock",
                    "evidence": [],
                    "review": review_record(),
                    "mapping_semantic_digest": "sha256:old",
                    "rationale": "legacy",
                }
            ],
        }
        with self.assertRaises(SourceValidationError):
            validate_source(legacy, "mapping", schema_root=SCHEMA_ROOT)

    def test_unknown_schema_is_stable_category(self):
        with self.assertRaises(SourceValidationError) as raised:
            validate_source({}, "does-not-exist", schema_root=SCHEMA_ROOT)
        self.assertEqual(raised.exception.problem.category, "unknown_schema")

    def test_invalid_committed_like_schema_is_stable_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / SCHEMA_FILES["profile"]).write_text(
                json.dumps({"$schema": DRAFT_2020_12, "type": 42}),
                encoding="utf-8",
            )
            with self.assertRaises(SourceValidationError) as raised:
                validate_source({}, "profile", schema_root=root)
        self.assertEqual(raised.exception.problem.category, "invalid_schema")


class SourceLoadingTests(unittest.TestCase):
    def assert_category(self, expected: str, callable_, *args, **kwargs):
        with self.assertRaises(SourceValidationError) as raised:
            callable_(*args, **kwargs)
        self.assertEqual(raised.exception.problem.category, expected)
        return raised.exception

    def test_duplicate_yaml_key_is_rejected(self):
        self.assert_category("duplicate_key", loads_source, "a: 1\na: 2\n", format="yaml")

    def test_duplicate_json_key_is_rejected(self):
        self.assert_category("duplicate_key", loads_source, '{"a": 1, "a": 2}', format="json")

    def test_non_string_yaml_mapping_key_is_rejected(self):
        self.assert_category("non_json_value", loads_source, "1: value\n", format="yaml")

    def test_yaml_timestamp_object_is_rejected(self):
        self.assert_category("non_json_value", loads_source, "value: 2026-09-05\n", format="yaml")

    def test_non_finite_yaml_number_is_rejected(self):
        self.assert_category("non_json_value", loads_source, "value: .nan\n", format="yaml")

    def test_non_finite_json_number_is_rejected(self):
        self.assert_category("decode_error", loads_source, '{"value": NaN}', format="json")

    def test_json_compatible_yaml_is_normalized_to_plain_types(self):
        data = loads_source("a: [1, true, null, text]\n", format="yaml")
        self.assertEqual(data, {"a": [1, True, None, "text"]})
        self.assertIs(type(data), dict)
        self.assertIs(type(data["a"]), list)

    def test_json_compatible_json_loads(self):
        data = loads_source('{"a": [1, true, null, "text"]}', format="json")
        self.assertEqual(data, {"a": [1, True, None, "text"]})

    def test_load_source_uses_suffix_and_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.yaml"
            path.write_text("a: 1\n", encoding="utf-8")
            self.assertEqual(load_source(path), {"a": 1})

            bad = Path(tmp) / "source.txt"
            bad.write_text("a: 1\n", encoding="utf-8")
            self.assert_category("decode_error", load_source, bad)

    def test_load_and_validate_returns_loaded_value(self):
        profile = minimal_valid_instances()["profile"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            path.write_text(json.dumps(profile), encoding="utf-8")
            result = load_and_validate(path, "profile", schema_root=SCHEMA_ROOT)
        self.assertEqual(result, profile)

    def test_problem_exposes_paths_for_schema_error(self):
        instance = minimal_valid_instances()["profile"]
        instance["schema_version"] = "one"
        with self.assertRaises(SourceValidationError) as raised:
            validate_source(instance, "profile", schema_root=SCHEMA_ROOT)
        problem = raised.exception.problem
        self.assertEqual(problem.category, "schema_validation")
        self.assertIn("schema_version", problem.instance_path)
        self.assertTrue(problem.schema_path)


if __name__ == "__main__":
    unittest.main()
