from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import tfont
from tfont import coverage
from tfont.coverage import CoverageError


ROOT = Path(__file__).resolve().parents[2]
RESOURCE = "p004-pseudepigrapha-v1.0.0-v1"
HISTORICAL_DIGEST = "sha256:d45c83f4afb51cae81405205b2111f7329ed65d5d85b5268719717fb64286746"
EXPECTED_TECHNICAL = {
    "node_feature:otype",
    "edge_feature:oslots",
    "node_feature:boundary_utf8",
    "node_feature:is_gap",
    "node_feature:reading_option",
}
EXPECTED_NODE_TYPES = {
    "book",
    "chapter",
    "div",
    "document_metadata",
    "ellipsis",
    "manuscript",
    "orphan_reading",
    "reading",
    "unit",
    "variant_word",
    "verse",
    "version_metadata",
    "word",
}
EXPECTED_BOUNDED_VALUES = {
    'node_value:generation_marker="OCP-Trans"',
    'node_value:version_kind="generated_translation"',
    'node_value:version_kind="source"',
    "node_value:is_metadata_only=1",
    "node_value:is_missing_unit_id=1",
    "node_value:is_omission=1",
    "node_value:is_primary=1",
    "node_value:is_source_anomaly=1",
    "node_value:synthetic_witness=1",
    "node_value:undefined_manuscript=1",
}


def _current_manifest():
    loader = getattr(coverage, "load_packaged_coverage_manifest")
    return loader(RESOURCE, "pseudepigrapha")


class I017CurrentPseudepigraphaRedTests(unittest.TestCase):
    def test_public_packaged_loader_and_resource_constant_exist(self):
        self.assertTrue(
            hasattr(coverage, "load_packaged_coverage_manifest"),
            "RED: generic packaged coverage loader is absent",
        )
        self.assertTrue(
            hasattr(tfont, "load_packaged_coverage_manifest"),
            "RED: generic packaged coverage loader is not exported",
        )
        self.assertEqual(
            getattr(coverage, "P004_PSEUDEPIGRAPHA_V1_RESOURCE", None),
            RESOURCE,
            "RED: current Pseudepigrapha resource identity is absent",
        )

    def test_current_manifest_has_reviewed_denominator_shape(self):
        manifest = _current_manifest()
        report = coverage.coverage_report(manifest)

        self.assertEqual(report.semantic_items, 113)
        self.assertEqual(report.technical_exclusions, 5)
        self.assertEqual(report.production_reviewed_items, 0)
        self.assertEqual(report.production_unreviewed_items, 113)
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

        for item_id in EXPECTED_TECHNICAL:
            self.assertNotIn(item_id, semantic_ids)

    def test_observed_small_domains_are_not_implicitly_expanded(self):
        semantic_ids = {
            row["item_id"]
            for row in _current_manifest()["semantic_items"]
        }
        for feature in (
            "language",
            "ms_language",
            "reading_option",
            "boundary_utf8",
            "generated_language",
            "text_structure",
            "linebreak",
        ):
            with self.subTest(feature=feature):
                self.assertFalse(
                    any(item_id.startswith(f"node_value:{feature}=") for item_id in semantic_ids)
                )

    def test_artifact_identity_is_bound_into_denominator_digest(self):
        manifest = _current_manifest()
        identity = manifest["denominator_basis"]["artifact_identity"]
        self.assertEqual(identity["locator"], "github-release:v1.0.0/tf-1.0.zip")
        self.assertEqual(
            identity["sha256"],
            "d2dfad7e643699617a9493b9f5d724868f8027dd5f2e88bd558451e3e7819b7a",
        )
        self.assertEqual(
            identity["materialized_sha256"],
            "9b708add5b9f8ddbfdafa7dd61507956f7987ca6a70b2b9164342bd49003ec61",
        )

        before = coverage.coverage_denominator_digest(manifest)
        mutated = copy.deepcopy(manifest)
        mutated["denominator_basis"]["artifact_identity"]["sha256"] = "0" * 64
        self.assertNotEqual(coverage.coverage_denominator_digest(mutated), before)

        mutated = copy.deepcopy(manifest)
        mutated["denominator_basis"]["artifact_identity"]["materialized_sha256"] = "1" * 64
        self.assertNotEqual(coverage.coverage_denominator_digest(mutated), before)

    def test_all_semantic_items_start_unreviewed_and_technical_items_are_reviewed(self):
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
        self.assertTrue(
            all(row["source_ids"] for row in manifest["technical_exclusions"])
        )

    def test_historical_pseudepigrapha_baseline_is_unchanged(self):
        historical = coverage.load_p004_r011_baseline_manifests()["pseudepigrapha"]
        self.assertEqual(len(historical["semantic_items"]), 40)
        self.assertEqual(historical["denominator_digest"], HISTORICAL_DIGEST)
        self.assertEqual(historical["scope_quality"], "bounded-curated")

    def test_generic_loader_fails_closed_on_unsafe_or_missing_resources(self):
        loader = getattr(coverage, "load_packaged_coverage_manifest")
        for unsafe_resource, unsafe_corpus in (
            ("../escape", "pseudepigrapha"),
            ("a/b", "pseudepigrapha"),
            ("safe", "../escape"),
            ("safe", "a\\b"),
            ("", "pseudepigrapha"),
        ):
            with self.subTest(resource=unsafe_resource, corpus=unsafe_corpus):
                with self.assertRaises(CoverageError) as raised:
                    loader(unsafe_resource, unsafe_corpus)
                self.assertEqual(raised.exception.problem.category, "invalid_resource_component")

        with self.assertRaises(CoverageError) as raised:
            loader("does-not-exist", "pseudepigrapha")
        self.assertEqual(raised.exception.problem.category, "missing_resource")

    def test_offline_builder_and_policy_are_part_of_the_contract(self):
        self.assertTrue(
            (ROOT / "scripts/coverage/build_i017_pseudepigrapha_v1.py").is_file(),
            "RED: I-017 deterministic builder is absent",
        )
        policy_path = ROOT / "docs/research/data/i017/pseudepigrapha-denominator-policy.json"
        self.assertTrue(policy_path.is_file(), "RED: I-017 denominator policy is absent")
        if policy_path.is_file():
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            self.assertEqual(
                set(policy["technical_node_features"]),
                {"boundary_utf8", "is_gap", "reading_option"},
            )


if __name__ == "__main__":
    unittest.main()
