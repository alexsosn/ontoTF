from __future__ import annotations

import json
import unittest
from dataclasses import replace

from tests.i006._fixtures import compiled_noun_ir, with_bundle_digest
from ontotf.digests import canonical_json_bytes
import ontotf.runtime_prerequisites as runtime


class Observation:
    def __init__(self, parent_digest, values=("subs",), *, local_path="/one", timestamp="one"):
        self.parent_manifest_digest = parent_digest
        self._values = tuple(values)
        self.local_path = local_path
        self.timestamp = timestamp

    def values(self, component_id, node_type, feature):
        return ("complete", self._values)


def evaluate(variant, observation, **kwargs):
    return runtime.evaluate_runtime_prerequisites(
        variant,
        observation,
        source_contract=kwargs.pop("source_contract", "test:i007-fingerprint-v1"),
        **kwargs,
    )


class I007InputAndFingerprintRedTests(unittest.TestCase):
    def test_noncanonical_dependency_json_fails_before_observation(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        dependency_id, encoded = variant.release_signature.dependency_records[0]
        noncanonical = json.dumps(json.loads(encoded), indent=2, sort_keys=False)
        forged = replace(
            variant,
            release_signature=replace(
                variant.release_signature,
                dependency_records=((dependency_id, noncanonical),),
            ),
        )
        with self.assertRaises(runtime.RuntimeEvaluationError):
            evaluate(forged, Observation(variant.key.expected_parent_manifest_digest))

    def test_duplicate_dependency_ids_fail_before_observation(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        row = variant.release_signature.dependency_records[0]
        forged = replace(
            variant,
            release_signature=replace(variant.release_signature, dependency_records=(row, row)),
        )
        with self.assertRaises(runtime.RuntimeEvaluationError):
            evaluate(forged, Observation(variant.key.expected_parent_manifest_digest))

    def test_dependency_tuple_id_mismatch_fails(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        _, encoded = variant.release_signature.dependency_records[0]
        forged = replace(
            variant,
            release_signature=replace(
                variant.release_signature,
                dependency_records=(("dep:forged", encoded),),
            ),
        )
        with self.assertRaises(runtime.RuntimeEvaluationError):
            evaluate(forged, Observation(variant.key.expected_parent_manifest_digest))

    def test_optional_dependency_evidence_still_matches_the_profile_schema(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        dependency_id, encoded = variant.release_signature.dependency_records[0]
        record = json.loads(encoded)
        record["evidence"] = [{"evidence_id": "evidence:broken"}]
        forged = replace(
            variant,
            release_signature=replace(
                variant.release_signature,
                dependency_records=((dependency_id, canonical_json_bytes(record).decode("utf-8")),),
            ),
        )
        with self.assertRaises(runtime.RuntimeEvaluationError):
            evaluate(forged, Observation(variant.key.expected_parent_manifest_digest))

    def test_wrong_dependency_contract_version_fails(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        forged = replace(
            variant,
            release_signature=replace(variant.release_signature, dependency_contract_version=2),
        )
        with self.assertRaises(runtime.RuntimeEvaluationError):
            evaluate(forged, Observation(variant.key.expected_parent_manifest_digest))

    def test_empty_observed_parent_digest_is_invalid_input(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        with self.assertRaises(runtime.RuntimeEvaluationError):
            evaluate(variant, Observation(""))

    def test_wrong_and_empty_active_bundle_digest_are_invalid_not_incompatible(self):
        variant = with_bundle_digest(compiled_noun_ir(("bhsa",)), "sha256:" + "b" * 64).variants[0]
        obs = Observation(variant.key.expected_parent_manifest_digest)
        for digest in ("", "sha256:" + "c" * 64):
            with self.subTest(digest=digest):
                with self.assertRaises(runtime.RuntimeEvaluationError):
                    evaluate(variant, obs, active_ontology_bundle_digest=digest)

    def test_report_identity_changes_with_semantic_runtime_inputs(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        exact = evaluate(variant, Observation(variant.key.expected_parent_manifest_digest))
        changed_parent = evaluate(variant, Observation("sha256:" + "9" * 64))
        changed_values = evaluate(variant, Observation(variant.key.expected_parent_manifest_digest, values=("other",)))
        changed_source = evaluate(
            variant,
            Observation(variant.key.expected_parent_manifest_digest),
            source_contract="test:i007-fingerprint-v2",
        )
        fingerprints = {
            exact.report_fingerprint,
            changed_parent.report_fingerprint,
            changed_values.report_fingerprint,
            changed_source.report_fingerprint,
        }
        self.assertEqual(len(fingerprints), 4)

    def test_volatile_observation_metadata_does_not_change_identity(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        one = evaluate(
            variant,
            Observation(variant.key.expected_parent_manifest_digest, local_path="/a", timestamp="one"),
        )
        two = evaluate(
            variant,
            Observation(variant.key.expected_parent_manifest_digest, local_path="/b", timestamp="two"),
        )
        self.assertEqual(one.report_fingerprint, two.report_fingerprint)
        self.assertEqual(
            one.dependency_results[0].observed_evidence_digest,
            two.dependency_results[0].observed_evidence_digest,
        )

    def test_value_observation_order_does_not_change_evidence_or_report_identity(self):
        variant = compiled_noun_ir(("bhsa",)).variants[0]
        one = evaluate(variant, Observation(variant.key.expected_parent_manifest_digest, values=("subs", "x")))
        two = evaluate(variant, Observation(variant.key.expected_parent_manifest_digest, values=("x", "subs")))
        self.assertEqual(
            one.dependency_results[0].observed_evidence_digest,
            two.dependency_results[0].observed_evidence_digest,
        )
        self.assertEqual(one.report_fingerprint, two.report_fingerprint)

    def test_old_v1_compatibility_shape_cannot_be_evaluated_as_current_variant(self):
        legacy = {
            "profile_semantic_digest": "sha256:" + "a" * 64,
            "state": "verified-exact",
        }
        with self.assertRaises(TypeError):
            runtime.evaluate_runtime_prerequisites(
                legacy,
                Observation("sha256:" + "a" * 64),
                source_contract="legacy:v1",
            )


if __name__ == "__main__":
    unittest.main()
