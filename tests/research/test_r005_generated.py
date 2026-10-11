from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINS_PATH = ROOT / "docs" / "research" / "data" / "R-005-corpus-pins.json"
REPORT_PATH = ROOT / "docs" / "research" / "R-005-corpus-semantic-census.md"
MATRIX_PATH = ROOT / "docs" / "research" / "R-005-candidate-strength-matrix.md"
GENERATED = ROOT / "docs" / "research" / "data" / "generated" / "r005"

# Stress targets without a committed released TF artifact are intentionally absent.
PIN_TO_FILE = {
    "bhsa": "bhsa.json",
    "cuc": "cuc.json",
    "syriac": "syriac.json",
    "peshitta": "peshitta.json",
    "syrnt": "syrnt.json",
    "extrabiblical": "extrabiblical.json",
    "tlhdig_tf": "tlhdig-tf.json",
}

CORPUS_ID = {
    "tlhdig_tf": "tlhdig-tf",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
STALE_CUC_DEFERRAL = (
    "CUC's editorial feature value domains should be regenerated from the exact TF "
    "release when a production mapping is designed"
)


class GeneratedInventoryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pins = json.loads(PINS_PATH.read_text(encoding="utf-8"))["corpora"]
        cls.inventories = {
            key: json.loads((GENERATED / filename).read_text(encoding="utf-8"))
            for key, filename in PIN_TO_FILE.items()
        }

    def test_authoritative_report_describes_current_empirical_evidence_path(self):
        report = REPORT_PATH.read_text(encoding="utf-8")
        self.assertNotIn(STALE_CUC_DEFERRAL, report)
        self.assertIn("docs/research/data/generated/r005/cuc.json", report)
        self.assertIn("observed small domain", report.lower())
        self.assertIn("remark", report)
        self.assertIn("R-005-candidate-strength-matrix.md", report)

    def test_curated_cuc_applicability_matches_generated_inventory(self):
        cuc = self.inventories["cuc"]["node_features"]
        expected = {
            "g_cons": ["word"],
            "trailer": ["word"],
            "utrailer": ["word"],
            "trailer_emen": ["word"],
            "language": ["word"],
            "side": ["line"],
            "cont": ["sign"],
        }
        for feature, applies_to in expected.items():
            with self.subTest(feature=feature):
                self.assertEqual(cuc[feature]["applies_to"], applies_to)

        report = REPORT_PATH.read_text(encoding="utf-8")
        expected_rows = (
            "| `g_cons` | string | consonantal value | `word` |",
            "| `trailer`, `utrailer`, `trailer_emen` | string | following spacing/punctuation/editorial rendering | `word` |",
            "| `language` | string/categorical | encoded language | `word` |",
            "| `side` | string/categorical | physical side | `line` |",
            "| `cont` | string/flag-like | line-continuation information | `sign` |",
        )
        for row in expected_rows:
            with self.subTest(row=row):
                self.assertIn(row, report)

    def test_curated_bhsa_domains_preserve_documented_and_observed_native_values(self):
        bhsa = self.inventories["bhsa"]["node_features"]

        # The BHSA metadata itself documents NA/unknown as members of these
        # grammatical feature domains. They are native non-empty values and must not
        # be collapsed with TF storage empties just because a particular subfeature
        # does not instantiate every documented value in this release.
        documented_special_values = (
            "gn",
            "prs_gn",
            "nu",
            "prs_nu",
            "ps",
            "prs_ps",
        )
        for feature in documented_special_values:
            with self.subTest(feature=feature):
                description = bhsa[feature]["metadata"]["description"]
                self.assertIn("NA", description)
                self.assertIn("unknown", description)
                self.assertIn("NA", bhsa[feature]["observed_values"])

        # Exact-release observations are a separate fact from the documented domain.
        self.assertEqual(
            set(bhsa["gn"]["observed_values"]), {"NA", "f", "m", "unknown"}
        )
        self.assertEqual(
            set(bhsa["prs_gn"]["observed_values"]), {"NA", "f", "m", "unknown"}
        )
        self.assertEqual(
            set(bhsa["nu"]["observed_values"]), {"NA", "du", "pl", "sg", "unknown"}
        )
        self.assertEqual(set(bhsa["prs_nu"]["observed_values"]), {"NA", "pl", "sg"})
        self.assertEqual(
            set(bhsa["ps"]["observed_values"]), {"NA", "p1", "p2", "p3", "unknown"}
        )
        self.assertEqual(
            set(bhsa["prs_ps"]["observed_values"]), {"NA", "p1", "p2", "p3"}
        )

        # st's metadata documents a/c/e, while the exact release also contains the
        # ordinary non-empty native value NA.
        self.assertEqual(set(bhsa["st"]["observed_values"]), {"NA", "a", "c", "e"})

        report = REPORT_PATH.read_text(encoding="utf-8")
        expected_rows = (
            "| gender | `gn`, `prs_gn` | documented `m`, `f`, `NA`, `unknown` | `word` |",
            "| number | `nu`, `prs_nu` | documented `sg`, `du`, `pl`, `NA`, `unknown` | `word` |",
            "| person | `ps`, `prs_ps` | documented `p1`, `p2`, `p3`, `NA`, `unknown` | `word` |",
            "| state | `st` | documented `a`, `c`, `e`; observed native `NA` also present | `word` |",
        )
        for row in expected_rows:
            with self.subTest(row=row):
                self.assertIn(row, report)
        self.assertIn("native non-empty values", report)
        self.assertIn("documented domain", report)
        self.assertIn("observed release subset", report)

    def test_compact_candidate_strength_cells_match_dedicated_matrix_contract(self):
        report = REPORT_PATH.read_text(encoding="utf-8")
        rows = {
            line.split("|", 2)[1].strip(): [
                cell.strip() for cell in line.strip().strip("|").split("|")
            ]
            for line in report.splitlines()
            if line.startswith("| word/token |") or line.startswith("| sign/grapheme |")
        }

        word = rows["word/token"]
        sign = rows["sign/grapheme"]
        # Columns: semantic cluster, BHSA, CUC, Syriac, Peshitta, SyrNT,
        # ExtraBiblical, TLHdig-TF, Pseudepigrapha-TF, ORACC-TF target.
        self.assertEqual(word[2], "S word over signs")
        self.assertEqual(word[7], "S word over signs")
        self.assertEqual(word[9], "S word over signs")
        self.assertEqual(sign[2], "C primary alphabetic sign")
        self.assertEqual(sign[7], "C primary cuneiform sign + alignment")
        self.assertEqual(sign[9], "C semantic GDL sign")

    def test_dependency_and_hierarchical_parent_relations_remain_separate(self):
        bhsa_edges = self.inventories["bhsa"]["edge_features"]
        self.assertIn("linguistic dependency", bhsa_edges["mother"]["metadata"]["description"])
        self.assertNotIn(
            "linguistic dependency",
            bhsa_edges["functional_parent"]["metadata"]["description"],
        )
        self.assertNotIn(
            "linguistic dependency",
            bhsa_edges["distributional_parent"]["metadata"]["description"],
        )

        report = REPORT_PATH.read_text(encoding="utf-8")
        compact_rows = {
            line.split("|", 2)[1].strip(): [
                cell.strip() for cell in line.strip().strip("|").split("|")
            ]
            for line in report.splitlines()
            if line.startswith("| syntactic dependency |")
            or line.startswith("| hierarchical parent relation |")
        }
        self.assertEqual(compact_rows["syntactic dependency"][1], "S `mother`")
        self.assertEqual(compact_rows["syntactic dependency"][6], "S `mother`")
        self.assertEqual(
            compact_rows["hierarchical parent relation"][1],
            "S `functional_parent` + `distributional_parent`",
        )
        self.assertEqual(
            compact_rows["hierarchical parent relation"][6],
            "S `functional_parent` + `distributional_parent`",
        )

        matrix = MATRIX_PATH.read_text(encoding="utf-8")
        dedicated_rows = {
            line.split("|", 2)[1].strip(): [
                cell.strip() for cell in line.strip().strip("|").split("|")
            ]
            for line in matrix.splitlines()
            if line.startswith("| syntactic dependency |")
            or line.startswith("| hierarchical parent relation |")
        }
        self.assertEqual(dedicated_rows["syntactic dependency"][1], "`S` `mother`")
        self.assertEqual(dedicated_rows["syntactic dependency"][6], "`S` `mother`")
        self.assertEqual(
            dedicated_rows["hierarchical parent relation"][1],
            "`S` `functional_parent` / `distributional_parent`",
        )
        self.assertEqual(
            dedicated_rows["hierarchical parent relation"][6],
            "`S` `functional_parent` / `distributional_parent`",
        )

    def test_r005_verification_ci_is_non_mutating(self):
        # The report reconciliation was a one-time migration. Keeping its write-enabled
        # workflow after the report is repaired can move the PR head from CI and recreate
        # the exact-head race that the final verification contract is meant to prevent.
        self.assertFalse(
            (ROOT / ".github" / "workflows" / "r005-report-reconcile.yml").exists()
        )
        self.assertFalse(
            (ROOT / "scripts" / "research" / "r005_reconcile_report.py").exists()
        )

        # The generated-only validation workflow was retired. Its test
        # contract is now owned by the unfiltered exact-head full suite.
        for filename in (
            "r005-research-inventory.yml",
            "full-suite.yml",
        ):
            workflow = (ROOT / ".github" / "workflows" / filename).read_text(
                encoding="utf-8"
            )
            with self.subTest(workflow=filename):
                self.assertIn("contents: read", workflow)
                self.assertNotIn("contents: write", workflow)
                self.assertNotIn("git push", workflow)

        main_suite = (ROOT / ".github" / "workflows" / "full-suite.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("  pull_request:\n  workflow_dispatch:", main_suite)
        self.assertIn("python -m unittest discover -s tests -v", main_suite)
        self.assertIn(
            "python -m pytest tests/research -q", main_suite
        )

    def test_exact_generated_file_set(self):
        self.assertEqual(
            {path.name for path in GENERATED.glob("*.json")},
            set(PIN_TO_FILE.values()),
        )

    def test_identity_version_slot_and_node_counts_match_research_pins(self):
        for key, inventory in self.inventories.items():
            with self.subTest(corpus=key):
                pin = self.pins[key]
                self.assertEqual(inventory["schema_version"], 1)
                self.assertEqual(inventory["evidence_kind"], "loaded_tf_artifact")
                self.assertEqual(inventory["corpus_id"], CORPUS_ID.get(key, key))
                self.assertEqual(inventory["repository"], pin["repository"])
                self.assertEqual(inventory["revision"], pin["commit"])
                self.assertEqual(inventory["tf_version"], pin["tf_version"])
                self.assertEqual(inventory["slot_type"], pin["slot_type"])
                self.assertEqual(inventory["node_types"], pin["node_counts"])
                self.assertRegex(inventory["tf_files_sha256"], SHA256_RE)

    def test_generated_edge_inventory_covers_pinned_semantic_edges(self):
        for key, inventory in self.inventories.items():
            with self.subTest(corpus=key):
                semantic_edges = set(self.pins[key].get("custom_edges", []))
                observed_edges = set(inventory["edge_features"])
                self.assertTrue(semantic_edges.issubset(observed_edges))

                # The pins file is intentionally a semantic synopsis, whereas the
                # generated inventory is exhaustive. BHSA additionally exposes TF
                # version/node mapping edge features; preserve them in the census
                # without pretending they are corpus-semantic relations.
                infrastructure_edges = observed_edges - semantic_edges
                self.assertTrue(
                    all(name.startswith("omap@") for name in infrastructure_edges),
                    (key, sorted(infrastructure_edges)),
                )

    def test_feature_metadata_and_applicability_are_explicit(self):
        for key, inventory in self.inventories.items():
            for name, feature in inventory["node_features"].items():
                with self.subTest(corpus=key, feature=name):
                    self.assertEqual(feature["kind"], "node")
                    self.assertIsInstance(feature["metadata"], dict)
                    self.assertIn("valueType", feature["metadata"])
                    self.assertIsInstance(feature["applies_to"], list)
                    self.assertIsInstance(feature["nodes_with_value"], int)
                    self.assertIsInstance(feature["node_records_seen"], int)
                    self.assertLessEqual(
                        feature["nodes_with_value"], feature["node_records_seen"]
                    )

            for name, feature in inventory["edge_features"].items():
                with self.subTest(corpus=key, edge=name):
                    self.assertEqual(feature["kind"], "edge")
                    self.assertIsInstance(feature["metadata"], dict)
                    self.assertIn("valueType", feature["metadata"])
                    self.assertIsInstance(feature["source_types"], list)
                    self.assertIsInstance(feature["target_types"], list)
                    self.assertIsInstance(feature["valued"], bool)
                    self.assertIsInstance(feature["edge_count"], int)

    def test_node_value_accounting_and_domains_exclude_storage_empties(self):
        for key, inventory in self.inventories.items():
            for name, feature in inventory["node_features"].items():
                with self.subTest(corpus=key, feature=name):
                    self.assertEqual(
                        feature["observation_count"] + feature["empty_observation_count"],
                        feature["raw_observation_count"],
                    )
                    self.assertEqual(
                        feature["nodes_with_value"], feature["observation_count"]
                    )
                    self._check_domain(feature)

    def test_valued_edge_domains_exclude_storage_empties(self):
        for key, inventory in self.inventories.items():
            for name, feature in inventory["edge_features"].items():
                if not feature["valued"]:
                    continue
                with self.subTest(corpus=key, edge=name):
                    self.assertEqual(
                        feature["observation_count"] + feature["empty_observation_count"],
                        feature["raw_observation_count"],
                    )
                    self.assertEqual(feature["edge_count"], feature["raw_observation_count"])
                    self._check_domain(feature)

    def test_cuc_review_regressions_are_pinned(self):
        cuc = self.inventories["cuc"]["node_features"]
        self.assertEqual(cuc["cert"]["observed_values"], ["False", "True"])
        self.assertEqual(
            set(cuc["emen"]["observed_values"]),
            {"excised", "missing", "redundant", "remark", "restored"},
        )
        self.assertEqual(cuc["cert"]["applies_to"], ["sign"])
        self.assertEqual(cuc["emen"]["applies_to"], ["sign"])

    def test_known_semantic_edge_directions_are_preserved(self):
        bhsa = self.inventories["bhsa"]["edge_features"]
        self.assertIn("mother", bhsa)
        self.assertFalse(bhsa["mother"]["valued"])

        tlhdig = self.inventories["tlhdig_tf"]["edge_features"]
        self.assertEqual(tlhdig["lexeme"]["source_types"], ["analysis"])
        self.assertEqual(tlhdig["lexeme"]["target_types"], ["lex"])
        self.assertTrue(tlhdig["selected"]["valued"])
        self.assertEqual(tlhdig["selected"]["source_types"], ["word"])
        self.assertEqual(tlhdig["selected"]["target_types"], ["analysis"])

    def _check_domain(self, feature):
        if feature["domain_observation"] == "observed_small_domain":
            values = feature["observed_values"]
            self.assertEqual(len(values), feature["observed_unique_count"])
        else:
            values = feature.get("sample_values", [])
        self.assertNotIn("", values)
        self.assertNotIn(None, values)


if __name__ == "__main__":
    unittest.main()
