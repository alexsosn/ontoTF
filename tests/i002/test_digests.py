from __future__ import annotations

import math
import unittest

from ontotf.digests import (
    EVIDENCE_PAYLOAD_ALGORITHM,
    EVIDENCE_RECORD_ALGORITHM,
    JCS_FORMAT,
    MAPPING_SEMANTIC_ALGORITHM,
    PROFILE_SEMANTIC_ALGORITHM,
    SOURCE_BUNDLE_ALGORITHM,
    SOURCE_FILE_ALGORITHM,
    DigestError,
    canonical_json_bytes,
    evidence_payload_digest,
    evidence_record_digest,
    mapping_semantic_digest,
    normalize_source_bytes,
    profile_semantic_digest,
    source_bundle_digest,
    source_file_digest,
)


class DigestTestCase(unittest.TestCase):
    def assert_category(self, category: str, func, *args, **kwargs):
        with self.assertRaises(DigestError) as raised:
            func(*args, **kwargs)
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception


class CanonicalJSONTests(DigestTestCase):
    def test_algorithm_identifiers_are_versioned(self):
        self.assertEqual(JCS_FORMAT, "rfc8785-jcs")
        self.assertEqual(SOURCE_FILE_ALGORITHM, "tfont-source-file-sha256-v1")
        self.assertEqual(SOURCE_BUNDLE_ALGORITHM, "tfont-source-bundle-sha256-v1")
        self.assertEqual(EVIDENCE_PAYLOAD_ALGORITHM, "tfont-evidence-payload-sha256-v1")
        self.assertEqual(EVIDENCE_RECORD_ALGORITHM, "tfont-evidence-record-sha256-v1")
        self.assertEqual(MAPPING_SEMANTIC_ALGORITHM, "tfont-mapping-semantic-sha256-v1")
        self.assertEqual(PROFILE_SEMANTIC_ALGORITHM, "tfont-profile-semantic-sha256-v1")

    def test_rfc_number_serialization_sample(self):
        value = {"numbers": [333333333.33333329, 1e30, 4.50, 2e-3, 1e-27]}
        self.assertEqual(
            canonical_json_bytes(value),
            b'{"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27]}',
        )

    def test_rfc_utf16_property_order_sample(self):
        value = {
            "€": "Euro Sign",
            "\r": "Carriage Return",
            "דּ": "Hebrew Letter Dalet With Dagesh",
            "1": "One",
            "😀": "Emoji: Grinning Face",
            "\u0080": "Control",
            "ö": "Latin Small Letter O With Diaeresis",
        }
        expected = (
            '{"\\r":"Carriage Return","1":"One","\u0080":"Control",'
            '"ö":"Latin Small Letter O With Diaeresis","€":"Euro Sign",'
            '"😀":"Emoji: Grinning Face","דּ":"Hebrew Letter Dalet With Dagesh"}'
        ).encode("utf-8")
        self.assertEqual(canonical_json_bytes(value), expected)

    def test_object_order_is_irrelevant_but_array_order_is_not(self):
        self.assertEqual(canonical_json_bytes({"b": 2, "a": 1}), canonical_json_bytes({"a": 1, "b": 2}))
        self.assertNotEqual(canonical_json_bytes([1, 2]), canonical_json_bytes([2, 1]))
        self.assertEqual(canonical_json_bytes([{"b": 2, "a": 1}]), b'[{"a":1,"b":2}]')

    def test_unicode_is_not_normalized(self):
        self.assertNotEqual(canonical_json_bytes("é"), canonical_json_bytes("e\u0301"))

    def test_negative_zero_is_zero(self):
        self.assertEqual(canonical_json_bytes(-0.0), b"0")

    def test_safe_integer_domain(self):
        self.assertEqual(canonical_json_bytes(9007199254740991), b"9007199254740991")
        self.assertEqual(canonical_json_bytes(-9007199254740991), b"-9007199254740991")
        self.assert_category("integer_domain", canonical_json_bytes, 9007199254740992)
        self.assert_category("integer_domain", canonical_json_bytes, -9007199254740992)

    def test_nonfinite_numbers_fail_closed(self):
        self.assert_category("float_domain", canonical_json_bytes, math.nan)
        self.assert_category("float_domain", canonical_json_bytes, math.inf)
        self.assert_category("float_domain", canonical_json_bytes, -math.inf)

    def test_values_outside_ontotf_json_model_are_not_coerced(self):
        self.assert_category("non_json_value", canonical_json_bytes, (1, 2))
        self.assert_category("non_json_value", canonical_json_bytes, {1: "value"})

    def test_lone_surrogate_fails_with_stable_category(self):
        self.assert_category("unicode_domain", canonical_json_bytes, "\ud800")


class SourceDigestTests(DigestTestCase):
    BOM_CRLF = b"\xef\xbb\xbfalpha: 1\r\nbeta: 2\r\n"
    BARE_CR = b"alpha\rbravo\r"

    def test_source_normalization_and_literal_digest_vectors(self):
        self.assertEqual(normalize_source_bytes(self.BOM_CRLF), b"alpha: 1\nbeta: 2\n")
        self.assertEqual(
            source_file_digest(self.BOM_CRLF),
            "sha256:d84c252600a370d7c2bbef45a926e6408cd2ca578f5a60e1b069342fbe9df760",
        )
        self.assertEqual(normalize_source_bytes(self.BARE_CR), b"alpha\nbravo\n")
        self.assertEqual(
            source_file_digest(self.BARE_CR),
            "sha256:1ec8367d6c8b59e9dd0c7a4f47214db8d2e76ebd2cd5bf4155508cb27263dd2f",
        )

    def test_source_normalization_preserves_other_whitespace(self):
        raw = b"a: 1  \n\t# comment\n"
        self.assertEqual(normalize_source_bytes(raw), raw)
        self.assertEqual(
            source_file_digest(raw),
            "sha256:43d51de0a94db49087a89ca8a98fe9e91c82062335d71090e9396ea88b367bbb",
        )

    def test_invalid_utf8_fails(self):
        self.assert_category("invalid_utf8", normalize_source_bytes, b"valid\xffinvalid")

    def test_source_bundle_is_order_independent_with_fixed_vector(self):
        a = self.BOM_CRLF
        b = self.BARE_CR
        expected = "sha256:57ab8e39e7a3f8966362892d47b3e63a6c6db6b4f843949b2808907fbed191f7"
        self.assertEqual(source_bundle_digest([("b.yaml", b), ("a.yaml", a)]), expected)
        self.assertEqual(source_bundle_digest([("a.yaml", a), ("b.yaml", b)]), expected)

    def test_source_bundle_rejects_duplicate_or_nonportable_paths(self):
        self.assert_category("duplicate_logical_path", source_bundle_digest, [("a.yaml", b"a"), ("a.yaml", b"b")])
        self.assert_category("projection_error", source_bundle_digest, [("../a.yaml", b"a")])
        self.assert_category("projection_error", source_bundle_digest, [("/a.yaml", b"a")])
        self.assert_category("projection_error", source_bundle_digest, [("a\\b.yaml", b"a")])


class SemanticDigestTests(DigestTestCase):
    def evidence_record(self) -> dict:
        return {
            "evidence_id": "evidence:test",
            "kind": "native-doc",
            "source_uri": "https://example.org/doc",
            "source_revision": "rev-1",
            "content_mode": "normalized-record",
            "reviewed_content": {"statement": "gn=m means masculine", "locator": ["section", 3]},
            "content_digest": "sha256:stale-self-value",
            "license_ref": "CC-BY-4.0",
            "citation": {"title": "display only"},
        }

    def mapping(self) -> dict:
        return {
            "mapping_id": "mapping:test",
            "profile_id": "tfont-test",
            "native_selector": {
                "kind": "feature-value",
                "component_id": "test-tf",
                "feature": "gn",
                "value": "m",
                "extent": "semantic",
            },
            "native_dependencies": ["dep:b", "dep:a"],
            "external_target": "https://example.org/Masculine",
            "candidate_projections": [],
            "assessment": "exact",
            "publication_relation": None,
            "applicability": {"node_type": "word"},
            "ontology_lock": "lock:test",
            "evidence": [
                {"evidence_id": "evidence:b", "content_digest": "sha256:bbb"},
                {"evidence_id": "evidence:a", "content_digest": "sha256:aaa"},
            ],
            "review": {
                "review_id": "review:test",
                "status": "reviewed",
                "reviewed_mapping_digest": "sha256:old",
                "reviewer_id": "reviewer:audit",
                "reviewed_at": "2026-09-06T00:00:00Z",
                "review_source": "pr:15",
                "review_method": "independent-skeptical",
            },
            "mapping_semantic_digest": "sha256:self",
            "rationale": "display prose",
            "introduced_in": "0.1.0",
            "changed_in": "0.1.1",
        }

    def profile_projection(self) -> dict:
        def lock(lock_id: str, revision: str, digest: str) -> dict:
            return {
                "lock_id": lock_id,
                "ontology_id": "olia",
                "support_tier": "core",
                "term_namespace": "http://purl.org/olia/olia.owl#",
                "release": "2026-02-04",
                "upstream_release_status": "stable",
                "source_uri": "https://example.org/olia.owl",
                "source_revision": revision,
                "content_digest": digest,
                "license": "CC-BY-4.0",
                "redistribution_policy": "allowed",
                "terms_used": ["Masculine", "Feminine"],
            }

        return {
            "profile_id": "tfont-test",
            "schema_version": 1,
            "semantic_contract_version": 1,
            "semantic_domains": ["syntax", "morphology"],
            "expected_parent_manifest_digest": "sha256:parent",
            "dependencies": [
                {"dependency_id": "dep:b", "component_id": "c", "kind": "feature"},
                {"dependency_id": "dep:a", "component_id": "c", "kind": "feature"},
            ],
            "ontology_locks": [
                lock("lock:b", "rev-b", "sha256:b"),
                lock("lock:a", "rev-a", "sha256:a"),
            ],
            "mappings": [
                {"mapping_id": "map:b", "mapping_semantic_digest": "sha256:mb"},
                {"mapping_id": "map:a", "mapping_semantic_digest": "sha256:ma"},
            ],
            "review_readiness": [
                {"mapping_id": "map:b", "status": "reviewed", "reviewed_digest_matches": True},
                {"mapping_id": "map:a", "status": "reviewed", "reviewed_digest_matches": True},
            ],
            "applicability": {},
            "publication_semantics": {},
        }

    def test_evidence_payload_is_exact_bytes(self):
        self.assertEqual(
            evidence_payload_digest(b"\x00TFont evidence\r\n\xff"),
            "sha256:cc63f4469d92d52add4ddec1dfd42903171a50a63f39511228035a604b849870",
        )

    def test_evidence_record_fixed_vector_and_self_reference_exclusion(self):
        record = self.evidence_record()
        expected = "sha256:1910379d4858f7f4b4c3d8fa95f1879f727128b65ee79186fad8159774add454"
        self.assertEqual(evidence_record_digest(record), expected)
        record["content_digest"] = "sha256:different-self-value"
        record["citation"] = {"title": "different display formatting"}
        self.assertEqual(evidence_record_digest(record), expected)
        record["reviewed_content"]["statement"] = "changed reviewed semantics"
        self.assertNotEqual(evidence_record_digest(record), expected)

    def test_evidence_record_unknown_fields_fail_closed(self):
        record = self.evidence_record()
        record["future_semantic_field"] = "cannot silently omit"
        self.assert_category("projection_error", evidence_record_digest, record)

    def test_mapping_fixed_vector_and_audit_self_fields_excluded(self):
        mapping = self.mapping()
        expected = "sha256:e84e543863b0d86bd2edeaaa68b0458027050a8e5f549e170d0a2e7c34b733b5"
        self.assertEqual(mapping_semantic_digest(mapping), expected)
        mapping["review"]["reviewer_id"] = "reviewer:other"
        mapping["review"]["reviewed_at"] = "2030-01-01T00:00:00Z"
        mapping["mapping_semantic_digest"] = "sha256:different"
        mapping["rationale"] = "different prose"
        mapping["introduced_in"] = "9.9.9"
        mapping["changed_in"] = "9.9.10"
        self.assertEqual(mapping_semantic_digest(mapping), expected)

    def test_mapping_set_like_order_is_normalized_but_evidence_change_matters(self):
        one = self.mapping()
        two = self.mapping()
        two["native_dependencies"].reverse()
        two["evidence"].reverse()
        self.assertEqual(mapping_semantic_digest(one), mapping_semantic_digest(two))
        two["evidence"][0]["content_digest"] = "sha256:changed"
        self.assertNotEqual(mapping_semantic_digest(one), mapping_semantic_digest(two))

    def test_mapping_duplicate_set_entries_and_unknown_fields_fail(self):
        mapping = self.mapping()
        mapping["native_dependencies"] = ["dep:a", "dep:a"]
        self.assert_category("projection_error", mapping_semantic_digest, mapping)
        mapping = self.mapping()
        mapping["future_semantic_field"] = True
        self.assert_category("projection_error", mapping_semantic_digest, mapping)

    def test_ambiguous_candidate_order_is_nonsemantic(self):
        mapping = self.mapping()
        mapping.update(
            assessment="ambiguous",
            external_target=None,
            ontology_lock=None,
            publication_relation=None,
            candidate_projections=[
                {
                    "external_target": "https://example.org/B",
                    "ontology_lock": "lock:b",
                    "assessment_candidate": "close",
                    "evidence": [{"evidence_id": "e:b", "content_digest": "sha256:b"}],
                },
                {
                    "external_target": "https://example.org/A",
                    "ontology_lock": "lock:a",
                    "assessment_candidate": "exact",
                    "evidence": [{"evidence_id": "e:a", "content_digest": "sha256:a"}],
                },
            ],
        )
        reversed_mapping = self.mapping()
        reversed_mapping.update(mapping)
        reversed_mapping["candidate_projections"] = list(reversed(mapping["candidate_projections"]))
        self.assertEqual(mapping_semantic_digest(mapping), mapping_semantic_digest(reversed_mapping))

    def test_profile_projection_fixed_vector_and_set_order(self):
        projection = self.profile_projection()
        expected = "sha256:e407e7f1ab60110a4d5146af51fa10e4c4f7ebb1ed4c3277c595ee0327dcb9ea"
        self.assertEqual(profile_semantic_digest(projection), expected)
        reordered = self.profile_projection()
        for field in ("semantic_domains", "dependencies", "ontology_locks", "mappings", "review_readiness"):
            reordered[field].reverse()
        for lock in reordered["ontology_locks"]:
            lock["terms_used"].reverse()
        self.assertEqual(profile_semantic_digest(reordered), expected)

    def test_profile_version_is_outside_semantic_projection(self):
        projection = self.profile_projection()
        release_a = {"profile_version": "0.1.0", "semantic_projection": projection}
        release_b = {"profile_version": "0.1.1", "semantic_projection": projection}
        self.assertNotEqual(release_a["profile_version"], release_b["profile_version"])
        self.assertEqual(
            profile_semantic_digest(release_a["semantic_projection"]),
            profile_semantic_digest(release_b["semantic_projection"]),
        )
        invalid = self.profile_projection()
        invalid["profile_version"] = "0.1.0"
        self.assert_category("projection_error", profile_semantic_digest, invalid)

    def test_audit_only_review_provenance_cannot_enter_profile_projection(self):
        invalid = self.profile_projection()
        invalid["review_readiness"][0]["reviewer_id"] = "audit-only"
        self.assert_category("projection_error", profile_semantic_digest, invalid)

    def test_duplicate_profile_set_ids_fail_instead_of_silent_dedup(self):
        invalid = self.profile_projection()
        invalid["dependencies"][1]["dependency_id"] = invalid["dependencies"][0]["dependency_id"]
        self.assert_category("projection_error", profile_semantic_digest, invalid)


if __name__ == "__main__":
    unittest.main()
