from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "research" / "R-004-documentation-architecture.md"
RECONCILIATION = ROOT / "docs" / "research" / "R-004-reconciliation.md"


class R004AuthoritativeReportTests(unittest.TestCase):
    def test_accepted_dependencies_are_pinned(self):
        text = REPORT.read_text(encoding="utf-8")
        self.assertIn("R-005 accepted", text)
        self.assertIn("48c8bd78d0c3a0501b2fdec6946db5df90517bdb", text)
        self.assertIn("a9c4d74d4de2f9a15eb1464dce341ecd2f92f898", text)
        self.assertIn("R-001 accepted", text)
        self.assertIn("68b88a820f5519ad65d46b732679a6278e9ca3c9", text)
        self.assertIn("a22a95084a1518882d1e3e87d10e9757121f106d", text)
        self.assertIn("R-002 accepted", text)
        self.assertIn("d82e6ef2726f149f903eb43ddbfb615faf399cd5", text)
        self.assertIn("a554d4fdc36c8854519064f3a7611b80efa29622", text)
        self.assertIn("R-003 accepted", text)
        self.assertIn("6747379a4aa68c17c156344f3ed3b0c2cb29d423", text)
        self.assertIn("02abd89b5b7d4c83027e1e8503a02eef23cab91e", text)

    def test_authority_is_scoped_not_numeric_precedence(self):
        text = REPORT.read_text(encoding="utf-8").lower()
        self.assertNotIn("| rank | artifact | authority |", text)
        self.assertNotIn("the poc should use the following precedence", text)
        self.assertIn("scoped authority domains", text)
        self.assertIn("native corpus semantics", text)
        self.assertIn("external ontology semantics", text)
        self.assertIn("ontotf mapping assertions", text)
        self.assertIn("profile identity and compatibility", text)
        self.assertIn("normative interpretation rules", text)
        self.assertIn("generated derivatives", text)

    def test_normative_rules_constrain_mapping_data(self):
        text = REPORT.read_text(encoding="utf-8").lower()
        self.assertIn("mapping/profile data vs approved normative ontotf rule", text)
        self.assertIn("invalid mapping/profile", text)
        self.assertIn("ci and profile activation fail", text)
        self.assertNotIn("prose never silently overrides the mapping", text)

    def test_mapping_assessment_and_publication_relation_are_separate_everywhere(self):
        text = REPORT.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertNotIn("relation: exact/close", lower)
        self.assertNotIn("relation strengthened/weakened", lower)
        self.assertNotIn("Mapping relation:   exact", text)
        self.assertNotIn("Mapping relation: exact", text)
        self.assertIn("Mapping assessment", text)
        self.assertIn("Publication relation", text)
        self.assertIn("assessment changed", lower)
        self.assertIn("publication relation changed", lower)

    def test_directional_approximation_effects_match_r003(self):
        text = REPORT.read_text(encoding="utf-8").lower()
        self.assertIn("`broader` can under-cover", text)
        self.assertIn("`narrower` can over-cover", text)
        self.assertNotIn("relation: broader", text)
        self.assertNotIn("may include native cases outside the requested concept", text)

    def test_compatibility_reference_is_component_aware(self):
        text = REPORT.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertIn("verified-exact", text)
        self.assertIn("verified-compatible", text)
        self.assertIn("unverified", text)
        self.assertIn("incompatible", text)
        self.assertIn("parent component manifest", lower)
        self.assertIn("component identities", lower)
        self.assertIn("complete dependency closure", lower)
        self.assertNotIn("transport-independent semantic-content digest", lower)
        self.assertNotIn("exact parent corpus binding/schema requirements", lower)

    def test_research_candidate_and_approved_mapping_are_separate(self):
        text = REPORT.read_text(encoding="utf-8").lower()
        self.assertIn("research candidate", text)
        self.assertIn("approved mapping", text)
        self.assertIn("publication relation", text)
        self.assertIn("mapping assessment", text)
        self.assertIn("cannot appear as an approved released mapping", text)

    def test_empirical_domains_do_not_promote_storage_empties_or_closure(self):
        text = REPORT.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertIn("empty_observation_count", text)
        self.assertIn("nodes_with_value", text)
        self.assertIn("observed small domain", lower)
        self.assertIn("documented bounded", lower)
        self.assertIn("remark", lower)
        self.assertIn("closed vocabulary", lower)

    def test_negative_states_are_explicit_documentation_values(self):
        text = REPORT.read_text(encoding="utf-8").lower()
        for state in ("native-only", "unsupported", "ambiguous", "unverified", "incompatible"):
            self.assertIn(f"`{state}`", text)
        self.assertIn("empty cell", text)
        self.assertIn("forbidden", text)

    def test_agent_docs_distinguish_host_protocol_and_semantic_identity(self):
        text = REPORT.read_text(encoding="utf-8").lower()
        self.assertIn("current host implementation", text)
        self.assertIn("cfabric-mcp 0.1.7", text)
        self.assertIn("mcp>=1.0,<2", text)
        self.assertIn("current protocol target", text)
        self.assertIn("2026-07-28", text)
        self.assertIn("negotiated protocol", text)
        self.assertIn("must not become part of semantic identity", text)
        self.assertIn("session state", text)

    def test_canonical_ci_contract_contains_all_drift_checks(self):
        text = REPORT.read_text(encoding="utf-8").lower()
        required = (
            "canonical mapping source against schema",
            "parent component manifest",
            "complete dependency closure",
            "research candidate",
            "mapping assessment and publication relation",
            "storage-level empty",
            "observed small domain",
            "documented bounded",
            "four r-001 compatibility states",
            "negative states",
            "deterministic normalized semantic intermediate representation",
            "semantic diff",
            "generated/do-not-edit marker",
            "negotiated protocol",
        )
        for phrase in required:
            self.assertIn(phrase, text)

    def test_semantic_diff_names_independent_change_dimensions(self):
        text = REPORT.read_text(encoding="utf-8").lower()
        self.assertIn("mapping assessment changed", text)
        self.assertIn("publication relation changed", text)
        self.assertIn("native selector/path changed", text)
        self.assertIn("parent compatibility evidence changed", text)
        self.assertIn("ontology lock/release changed", text)

    def test_reconciliation_note_is_historical_not_normative_amendment(self):
        text = RECONCILIATION.read_text(encoding="utf-8").lower()
        self.assertIn("historical reconciliation record", text)
        self.assertIn("canonical r-004 report is authoritative", text)
        self.assertNotIn("normative amendment", text)
        self.assertNotIn("where this note conflicts", text)


if __name__ == "__main__":
    unittest.main()
