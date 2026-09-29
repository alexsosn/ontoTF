from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import tfont
from tfont import coverage


ROOT = Path(__file__).resolve().parents[2]
RESOURCE = "p004-tlhdig-0.4.0-bc4a206-v1"
HISTORICAL_DIGEST = "sha256:eaf2436a90a85b1e5a8e02b4ad1f7070554d73de084eee589938586eecad2f1d"
I017_DIGEST = "sha256:4b6e6874cd7c903521ad3c2918652eb22292010c307b3aea8a762f36fca692fc"
I018_DIGEST = "sha256:436dc9a35080dd14a4bb6d0c1b5341b8dd2566e10608d5d37c1d2226aba3eda2"

EXPECTED_NODE_TYPES = {
    "analysis",
    "cluster",
    "colon",
    "column",
    "docgroup",
    "document",
    "edit",
    "fragment",
    "joinstmt",
    "layout",
    "lex",
    "line",
    "note",
    "paragraph",
    "sign",
    "surface",
    "word",
}
EXPECTED_TECHNICAL = {
    "node_feature:otype",
    "edge_feature:oslots",
    "node_feature:anchor",
    "node_feature:subcorpus",
}
EXPECTED_BOUNDED_NODE_FEATURES = {
    "type",
    "sgr",
    "agr",
    "det",
    "num",
    "missing",
    "laes",
    "ras",
    "add",
    "quot",
    "materlect_anomalous",
    "cu_unrendered",
    "crossesline",
    "nested",
    "siglum_ambiguous",
    "from_open_marker",
    "from_close_marker",
    "mrpsel_kind",
    "sel_group",
    "parse_ok",
    "field4_kind",
    "cu_aligned",
    "ruling",
    "kind",
    "orphan",
    "fragment_kind",
    "siglum_source",
    "join_kind",
    "join_encoding",
    "join_resolved",
}
EXPECTED_BOUNDED_EDGE_FEATURES = {"joined", "witness_resolution"}
EXPECTED_EDGE_VALUES = {
    'edge_value:joined="direct"',
    'edge_value:joined="indirect"',
    'edge_value:witness_resolution="unique"',
    'edge_value:witness_resolution="ambiguous"',
}


def _current_manifest():
    resource = getattr(coverage, "P004_TLHDIG_0_4_0_RESOURCE")
    return coverage.load_packaged_coverage_manifest(resource, "tlhdig")


class I019CurrentTLHdigRedTests(unittest.TestCase):
    def test_public_resource_constant_exists_and_is_exported(self):
        self.assertEqual(
            getattr(coverage, "P004_TLHDIG_0_4_0_RESOURCE", None),
            RESOURCE,
            "RED: current TLHdig coverage resource constant is absent",
        )
        self.assertEqual(
            getattr(tfont, "P004_TLHDIG_0_4_0_RESOURCE", None),
            RESOURCE,
            "RED: current TLHdig coverage resource constant is not exported",
        )

    def test_current_manifest_has_reviewed_denominator_shape(self):
        manifest = _current_manifest()
        report = coverage.coverage_report(manifest)

        self.assertEqual(report.semantic_items, 256)
        self.assertEqual(report.technical_exclusions, 4)
        self.assertEqual(report.research_reviewed_items, 0)
        self.assertEqual(report.production_reviewed_items, 0)
        self.assertEqual(report.production_unreviewed_items, 256)
        self.assertEqual(report.research_outside_denominator_items, 0)
        self.assertEqual(report.production_outside_denominator_items, 0)
        self.assertEqual(report.scope_quality, "machine-exhaustive")
        self.assertEqual(report.freshness, "current")
        self.assertFalse(report.bounded_scope_complete)
        self.assertFalse(report.corpus_wide_completion_claim_eligible)
        self.assertEqual(manifest["accounting_gaps"], [])

    def test_exact_node_types_technical_items_and_optional_provenance(self):
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
        self.assertTrue(EXPECTED_TECHNICAL.isdisjoint(semantic_ids))
        self.assertIn("node_feature:src_span", semantic_ids)
        self.assertIn("node_feature:srcxml", semantic_ids)

    def test_bounded_node_and_edge_value_contract(self):
        manifest = _current_manifest()
        semantic_ids = {row["item_id"] for row in manifest["semantic_items"]}
        node_values = {item_id for item_id in semantic_ids if item_id.startswith("node_value:")}
        edge_values = {item_id for item_id in semantic_ids if item_id.startswith("edge_value:")}

        self.assertEqual(len(node_values), 101)
        self.assertEqual(edge_values, EXPECTED_EDGE_VALUES)
        self.assertEqual(
            set(manifest["denominator_basis"]["bounded_node_features"]),
            EXPECTED_BOUNDED_NODE_FEATURES,
        )
        self.assertEqual(
            set(manifest["denominator_basis"]["bounded_edge_features"]),
            EXPECTED_BOUNDED_EDGE_FEATURES,
        )

    def test_open_node_and_edge_domains_are_not_expanded(self):
        semantic_ids = {row["item_id"] for row in _current_manifest()["semantic_items"]}
        for feature in (
            "after",
            "sep",
            "pos",
            "cu_method",
            "lang",
            "surface",
            "project",
            "join_reason",
        ):
            with self.subTest(feature=feature):
                self.assertFalse(
                    any(item_id.startswith(f"node_value:{feature}=") for item_id in semantic_ids)
                )
        self.assertFalse(
            any(item_id.startswith("edge_value:selected=") for item_id in semantic_ids)
        )

    def test_artifact_identity_binds_complete_and_combined_tf_outputs(self):
        manifest = _current_manifest()
        identity = manifest["denominator_basis"]["artifact_identity"]
        self.assertEqual(
            identity["locator"],
            "shipped-build:alexsosn/TLHdig-TF@bc4a206690c1856d3cfde8b291f626c45a712640:"
            "tf/0.4.0+tf-provenance/0.4.0",
        )
        self.assertEqual(
            identity["sha256"],
            "d0160532d03b86069132681ba68e23d3039bcebb96eb5684507ce660ea3b1634",
        )
        self.assertEqual(
            identity["materialized_sha256"],
            "fb447193b4f24a753154fbfdd4105cb855953af483b1160984435cf3f6422e6c",
        )

    def test_all_current_semantic_items_start_unreviewed(self):
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

    def test_bounded_edge_features_are_schema_and_digest_bound(self):
        manifest = coverage.load_packaged_coverage_manifest(
            coverage.P004_ORACC_0_4_0_RESOURCE,
            "oracc",
        )
        before = coverage.coverage_denominator_digest(manifest)
        mutated = copy.deepcopy(manifest)
        mutated["denominator_basis"]["bounded_edge_features"] = ["joined"]
        after = coverage.coverage_denominator_digest(mutated)
        self.assertNotEqual(before, after)
        mutated["denominator_digest"] = after
        coverage.validate_coverage_manifest(mutated)

    def test_existing_packaged_denominator_digests_are_unchanged(self):
        historical = coverage.load_p004_r011_baseline_manifests()["tlhdig"]
        self.assertEqual(len(historical["semantic_items"]), 137)
        self.assertEqual(historical["denominator_digest"], HISTORICAL_DIGEST)
        self.assertEqual(coverage.coverage_denominator_digest(historical), HISTORICAL_DIGEST)

        i017 = coverage.load_packaged_coverage_manifest(
            coverage.P004_PSEUDEPIGRAPHA_V1_RESOURCE,
            "pseudepigrapha",
        )
        i018 = coverage.load_packaged_coverage_manifest(
            coverage.P004_ORACC_0_4_0_RESOURCE,
            "oracc",
        )
        self.assertEqual(i017["denominator_digest"], I017_DIGEST)
        self.assertEqual(i018["denominator_digest"], I018_DIGEST)
        self.assertEqual(coverage.coverage_denominator_digest(i017), I017_DIGEST)
        self.assertEqual(coverage.coverage_denominator_digest(i018), I018_DIGEST)

    def test_offline_builder_and_policy_are_part_of_contract(self):
        self.assertTrue(
            (ROOT / "scripts/coverage/build_i019_tlhdig_current.py").is_file(),
            "RED: I-019 deterministic builder is absent",
        )
        policy_path = ROOT / "docs/research/data/i019/tlhdig-denominator-policy.json"
        self.assertTrue(policy_path.is_file(), "RED: I-019 denominator policy is absent")
        if policy_path.is_file():
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            self.assertEqual(
                set(policy["technical_node_features"]),
                {"anchor", "subcorpus"},
            )
            self.assertEqual(
                set(policy["bounded_edge_values"]),
                EXPECTED_BOUNDED_EDGE_FEATURES,
            )


if __name__ == "__main__":
    unittest.main()
