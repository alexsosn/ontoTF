from __future__ import annotations

import json
import unittest
from pathlib import Path

import tfont
from tfont import coverage


ROOT = Path(__file__).resolve().parents[2]
RESOURCE = "p004-oracc-0.4.0-f6f189b-v1"
HISTORICAL_DIGEST = "sha256:019d19e1248a19238fc3eadc1fd6e05ae0d1c0f596f0a6ef991a93c09bd65685"
EXPECTED_NODE_TYPES = {
    "chunk",
    "column",
    "document",
    "face",
    "lex",
    "line",
    "phrase",
    "sign",
    "translation_unit",
    "word",
}
EXPECTED_TECHNICAL = {
    "node_feature:otype",
    "edge_feature:oslots",
    "node_feature:cuneiform_trailer",
    "node_feature:lnno",
    "node_feature:readingu",
    "node_feature:synthetic",
}
EXPECTED_BOUNDED_VALUES = {
    "node_value:catalogue_present=0",
    "node_value:catalogue_present=1",
    'node_value:chunk_type="discourse"',
    'node_value:chunk_type="phrase"',
    'node_value:chunk_type="sentence"',
    'node_value:chunk_type="text"',
    "node_value:lemmaknown=0",
    "node_value:lemmaknown=1",
    "node_value:populated=0",
    "node_value:populated=1",
}


def _current_manifest():
    resource = getattr(coverage, "P004_ORACC_0_4_0_RESOURCE")
    return coverage.load_packaged_coverage_manifest(resource, "oracc")


class I018CurrentOraccRedTests(unittest.TestCase):
    def test_public_resource_constant_exists_and_is_exported(self):
        self.assertEqual(
            getattr(coverage, "P004_ORACC_0_4_0_RESOURCE", None),
            RESOURCE,
            "RED: current ORACC coverage resource constant is absent",
        )
        self.assertEqual(
            getattr(tfont, "P004_ORACC_0_4_0_RESOURCE", None),
            RESOURCE,
            "RED: current ORACC coverage resource constant is not exported",
        )

    def test_current_manifest_has_reviewed_denominator_shape(self):
        manifest = _current_manifest()
        report = coverage.coverage_report(manifest)
        self.assertEqual(report.semantic_items, 99)
        self.assertEqual(report.technical_exclusions, 6)
        self.assertEqual(report.production_reviewed_items, 0)
        self.assertEqual(report.production_unreviewed_items, 99)
        self.assertEqual(report.production_outside_denominator_items, 0)
        self.assertEqual(report.research_outside_denominator_items, 0)
        self.assertEqual(report.scope_quality, "machine-exhaustive")
        self.assertEqual(report.freshness, "current")
        self.assertFalse(report.bounded_scope_complete)
        self.assertFalse(report.corpus_wide_completion_claim_eligible)
        self.assertEqual(manifest["accounting_gaps"], [])

    def test_exact_node_types_technical_items_and_bounded_values(self):
        manifest = _current_manifest()
        semantic_ids = {row["item_id"] for row in manifest["semantic_items"]}
        technical_ids = {row["item_id"] for row in manifest["technical_exclusions"]}

        node_types = {
            item_id.split(":", 1)[1]
            for item_id in semantic_ids
            if item_id.startswith("node_type:")
        }
        self.assertEqual(node_types, EXPECTED_NODE_TYPES)
        self.assertEqual(technical_ids, EXPECTED_TECHNICAL)
        self.assertTrue(EXPECTED_BOUNDED_VALUES <= semantic_ids)
        self.assertTrue(EXPECTED_TECHNICAL.isdisjoint(semantic_ids))

    def test_translation_schema_is_materialized_but_notes_are_not_invented(self):
        semantic_ids = {row["item_id"] for row in _current_manifest()["semantic_items"]}
        self.assertIn("node_type:translation_unit", semantic_ids)
        self.assertIn("edge_feature:translation_document", semantic_ids)
        self.assertIn("edge_feature:translation_line", semantic_ids)
        self.assertFalse(
            any(
                item_id.startswith("node_type:translation_note")
                or item_id.startswith("node_feature:translation_note")
                or item_id == "edge_feature:translation_note_unit"
                for item_id in semantic_ids
            )
        )

    def test_observed_small_domains_and_provenance_constants_are_not_expanded(self):
        semantic_ids = {row["item_id"] for row in _current_manifest()["semantic_items"]}
        for feature in (
            "translation_subtype",
            "translation_rows",
            "chunk_subtype",
            "implicit",
            "lang",
            "language",
            "pos",
            "epos",
            "period",
            "script",
            "translation_source_archive",
            "translation_source_sha256",
            "translation_source_url",
        ):
            with self.subTest(feature=feature):
                self.assertFalse(
                    any(item_id.startswith(f"node_value:{feature}=") for item_id in semantic_ids)
                )

    def test_artifact_identity_matches_registered_candidate(self):
        manifest = _current_manifest()
        identity = manifest["denominator_basis"]["artifact_identity"]
        self.assertEqual(
            identity["locator"],
            "registered-build:alexsosn/ORACC-TF@f6f189bbd99d72bfdc7044555bd3113aa7b54232:"
            "assyrian-royal-inscriptions/tf/0.4.0",
        )
        self.assertEqual(
            identity["sha256"],
            "cbcc8299c1f5d02bc082ded824452fe3fb0a7857656a0556039a31667c48af1b",
        )
        self.assertEqual(
            identity["materialized_sha256"],
            "5d23f56eaa9461d7a6f42dc11a8c2f5d7307ba9820f49869400c5ac9af8bf34f",
        )

    def test_all_semantic_items_start_unreviewed(self):
        manifest = _current_manifest()
        self.assertTrue(
            all(
                row["accounting"]["research"] is None
                and row["accounting"]["production"] is None
                for row in manifest["semantic_items"]
            )
        )
        self.assertTrue(
            all(row["authority"] == "production" for row in manifest["technical_exclusions"])
        )

    def test_historical_oracc_baseline_is_unchanged(self):
        historical = coverage.load_p004_r011_baseline_manifests()["oracc"]
        self.assertEqual(len(historical["semantic_items"]), 42)
        self.assertEqual(historical["denominator_digest"], HISTORICAL_DIGEST)
        self.assertEqual(historical["scope_quality"], "bounded-curated")

    def test_offline_builder_and_policy_are_part_of_contract(self):
        self.assertTrue(
            (ROOT / "scripts/coverage/build_i018_oracc_current.py").is_file(),
            "RED: I-018 deterministic builder is absent",
        )
        policy_path = ROOT / "docs/research/data/i018/oracc-denominator-policy.json"
        self.assertTrue(policy_path.is_file(), "RED: I-018 denominator policy is absent")
        if policy_path.is_file():
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            self.assertEqual(
                set(policy["technical_node_features"]),
                {"cuneiform_trailer", "lnno", "readingu", "synthetic"},
            )


if __name__ == "__main__":
    unittest.main()
