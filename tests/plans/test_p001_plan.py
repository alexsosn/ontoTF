from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs" / "plans" / "P-001-foundation-poc-design.md"

# Historical changed paths from merged P-001 PR #13. The design-only invariant
# belongs to that change set; later implementation tickets intentionally added
# production paths to the repository.
P001_DESIGN_CHANGED_PATHS = (
    ".github/workflows/p001-plan-validation.yml",
    "docs/plans/P-001-foundation-poc-design.md",
    "tests/plans/test_p001_plan.py",
)
PRODUCTION_SCOPE_ROOTS = frozenset({"src", "schemas", "profiles"})


def production_scope_violations(paths: Iterable[str]) -> tuple[str, ...]:
    """Return production paths that violate P-001's historical design-only scope.

    This evaluates a supplied change set rather than the current repository tree.
    Path separators are normalized so the contract is deterministic across hosts.
    """

    violations: set[str] = set()
    for raw_path in paths:
        normalized = str(raw_path).replace("\\", "/").strip("/")
        if not normalized:
            continue
        root = normalized.split("/", 1)[0]
        if root in PRODUCTION_SCOPE_ROOTS:
            violations.add(normalized)
    return tuple(sorted(violations))


class P001FoundationDesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PLAN.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_pins_all_accepted_foundation_dependencies(self):
        for value in (
            "48c8bd78d0c3a0501b2fdec6946db5df90517bdb",
            "a9c4d74d4de2f9a15eb1464dce341ecd2f92f898",
            "68b88a820f5519ad65d46b732679a6278e9ca3c9",
            "a22a95084a1518882d1e3e87d10e9757121f106d",
            "d82e6ef2726f149f903eb43ddbfb615faf399cd5",
            "a554d4fdc36c8854519064f3a7611b80efa29622",
            "6747379a4aa68c17c156344f3ed3b0c2cb29d423",
            "02abd89b5b7d4c83027e1e8503a02eef23cab91e",
            "3dcadc0b32aef95ecbf6ad94f6bbc062f8c6200f",
            "00a5d6b7de777074b01bb70ac425d7f187781298",
        ):
            self.assertIn(value, self.text)

    def test_artifact_flow_has_one_canonical_source_path(self):
        required = (
            "profile manifest",
            "parent component manifest",
            "ontology lock",
            "canonical mapping source",
            "normalized semantic ir",
            "runtime sidecar",
            "reference json",
            "publication output",
        )
        for phrase in required:
            self.assertIn(phrase, self.lower)
        self.assertIn("canonical source", self.lower)
        self.assertIn("generated derivative", self.lower)
        self.assertIn("deterministic", self.lower)

    def test_profile_manifest_contract_is_explicit(self):
        required = (
            "profile_id",
            "profile_version",
            "parent_component_manifest",
            "ontology_locks",
            "mapping_sources",
            "required_components",
        )
        for field in required:
            self.assertIn(f"`{field}`", self.text)

    def test_parent_component_manifest_is_component_aware(self):
        required = (
            "semantically addressable native component",
            "tf payload",
            "external/native sidecar",
            "catalogue",
            "zero-span",
            "native-adapter",
            "component identities",
            "complete dependency closure",
        )
        for phrase in required:
            self.assertIn(phrase, self.lower)
        self.assertIn("tf bytes stay identical", self.lower)
        self.assertIn("must not remain `verified-exact`", self.lower)

    def test_all_compatibility_states_and_execution_gate_are_defined(self):
        for state in ("verified-exact", "verified-compatible", "unverified", "incompatible"):
            self.assertIn(f"`{state}`", self.text)
        self.assertIn("only `verified-exact` and `verified-compatible` are executable", self.lower)
        self.assertIn("`unverified`", self.text)
        self.assertIn("non-executable", self.lower)

    def test_compatibility_evidence_has_machine_report_shape(self):
        for field in (
            "compatibility_report_id",
            "report_digest",
            "profile_semantic_digest",
            "expected_parent_manifest_digest",
            "observed_parent_manifest_digest",
            "changed_components",
            "dependency_results",
            "evaluator_version",
            "incomplete_reasons",
            "failure_reasons",
        ):
            self.assertIn(f"`{field}`", self.text)
        self.assertIn("runtime provenance", self.lower)
        self.assertIn("compatibility reports are deterministic evidence artifacts", self.lower)

    def test_compatibility_report_digest_projection_is_non_self_referential(self):
        self.assertIn("report digest projection", self.lower)
        self.assertIn("excludes `compatibility_report_id` and `report_digest`", self.lower)
        self.assertIn("ontotf-compatibility-sha256-v1", self.lower)
        self.assertIn("derived from `report_digest`", self.lower)

    def test_compatibility_report_lifecycle_separates_release_and_activation(self):
        self.assertIn("release-validation report", self.lower)
        self.assertIn("activation compatibility report", self.lower)
        self.assertIn("validated ir + observed parent component manifest", self.lower)
        self.assertIn("same report schema", self.lower)
        self.assertIn("runtime cache", self.lower)

    def test_mapping_object_preserves_r002_contract(self):
        for assessment in (
            "exact",
            "close",
            "broader",
            "narrower",
            "related",
            "ambiguous",
            "native-only",
            "unsupported",
        ):
            self.assertRegex(self.text, rf"(?m)^\s*-?\s*`?{re.escape(assessment)}`?\b")
        required_fields = (
            "mapping_id",
            "profile_id",
            "native_selector",
            "native_dependencies",
            "external_target",
            "assessment",
            "publication_relation",
            "applicability",
            "evidence",
            "review",
            "ontology_lock",
        )
        for field in required_fields:
            self.assertIn(f"`{field}`", self.text)
        self.assertIn("native/source", self.lower)
        self.assertIn("external target", self.lower)
        self.assertIn("assessment and publication relation", self.lower)
        self.assertIn("independent", self.lower)

    def test_no_target_and_ambiguity_states_are_fail_closed(self):
        self.assertIn("`native-only` and `unsupported` have no external target", self.lower)
        self.assertIn("`ambiguous`", self.text)
        self.assertIn("must not", self.lower)
        self.assertIn("automatically executable", self.lower)

    def test_ambiguity_represents_target_and_relation_candidates(self):
        self.assertIn("candidate_projections", self.text)
        self.assertIn("assessment_candidate", self.text)
        self.assertIn("same external target", self.lower)
        self.assertIn("different candidate assessments", self.lower)
        self.assertIn("external_target: null", self.lower)

    def test_ambiguous_candidates_bind_their_own_ontology_locks(self):
        self.assertIn("each candidate projection", self.lower)
        self.assertIn("`ontology_lock`", self.text)
        self.assertIn("candidate targets from different ontology locks", self.lower)
        self.assertIn("top-level `ontology_lock: null`", self.lower)
        self.assertIn("top-level `publication_relation: null`", self.lower)

    def test_canonicalization_and_digest_rules_are_concrete(self):
        required = (
            "utf-8",
            "sorted",
            "canonical json",
            "sha-256",
            "line endings",
            "timestamps",
            "semantic digest",
            "source digest",
        )
        for phrase in required:
            self.assertIn(phrase, self.lower)
        self.assertIn("must not affect", self.lower)

    def test_semantic_digest_excludes_release_label_but_bundle_identity_includes_it(self):
        self.assertIn("`profile_version` must not affect `semantic_digest`", self.lower)
        self.assertIn("profile_id + profile_version + semantic_digest", self.lower)
        self.assertIn("exact-parent rebase", self.lower)
        self.assertIn("changed exact parent need not automatically force major versioning", self.lower)

    def test_versioning_rule_is_deterministic_for_changed_semantic_digest(self):
        self.assertIn("a changed `semantic_digest` can never be a patch", self.lower)
        self.assertIn("exact-parent rebase", self.lower)
        self.assertIn("is a minor release", self.lower)
        self.assertIn("removes previously supported behavior", self.lower)
        self.assertIn("major", self.lower)

    def test_required_components_have_one_authority(self):
        self.assertIn("`required_components` is authoritative", self.lower)
        self.assertIn("component records do not carry an independent `required` flag", self.lower)
        self.assertIn("every active mapping dependency", self.lower)
        self.assertIn("must reference one of those components", self.lower)

    def test_review_is_bound_to_mapping_semantic_content(self):
        self.assertIn("mapping_semantic_digest", self.text)
        self.assertIn("reviewed_mapping_digest", self.text)
        self.assertIn("must match", self.lower)
        self.assertIn("review record itself", self.lower)
        self.assertIn("stale review", self.lower)
        self.assertIn("non-executable", self.lower)

    def test_review_record_has_offline_auditable_provenance(self):
        for field in (
            "review_id",
            "status",
            "reviewed_mapping_digest",
            "reviewer_id",
            "reviewed_at",
            "review_source",
            "review_method",
        ):
            self.assertIn(f"`{field}`", self.text)
        self.assertIn("executable readiness", self.lower)
        self.assertIn("audit-only", self.lower)
        self.assertIn("forge username", self.lower)
        self.assertIn("not part of semantic identity", self.lower)

    def test_review_binding_includes_content_addressed_evidence(self):
        self.assertIn("`evidence_id`", self.text)
        self.assertIn("`content_digest`", self.text)
        self.assertIn("evidence_id, content_digest", self.lower)
        self.assertIn("mapping_semantic_digest", self.text)
        self.assertIn("evidence content changes", self.lower)
        self.assertIn("invalidates", self.lower)
        self.assertIn("review", self.lower)

    def test_evidence_digest_projection_is_non_self_referential(self):
        self.assertIn("evidence digest projection", self.lower)
        self.assertIn("excludes `content_digest`", self.lower)
        self.assertIn("exact external payload bytes", self.lower)
        self.assertIn("display-only metadata", self.lower)

    def test_ir_and_runtime_handoff_are_defined(self):
        required = (
            "capability",
            "resolution plan",
            "native_constraints",
            "compatibility",
            "assessment",
            "publication_relation",
            "provenance",
            "resolution fingerprint",
            "protocol-independent",
            "mcp session state",
        )
        for phrase in required:
            self.assertIn(phrase, self.lower)

    def test_native_data_edge_cases_are_explicit(self):
        required = (
            "zero-span",
            "technical anchor",
            "semantic extent",
            "dense tf empty",
            "observed small domain",
            "documented bounded",
            "explicit absence",
        )
        for phrase in required:
            self.assertIn(phrase, self.lower)

    def test_documentation_and_semantic_diff_contract_is_explicit(self):
        for phrase in (
            "native -> semantic",
            "semantic -> corpora",
            "mapping assessment changed",
            "publication relation changed",
            "native selector/path changed",
            "ontology lock",
            "parent compatibility evidence changed",
            "prose-only",
        ):
            self.assertIn(phrase, self.lower)

    def test_fixture_matrix_has_positive_and_adversarial_cases(self):
        for phrase in (
            "bhsa",
            "changed-parent",
            "zero-span",
            "technical-anchor",
            "dense-empty",
            "native-only",
            "unsupported",
        ):
            self.assertIn(phrase, self.lower)

    def test_plan_ends_with_dependency_ordered_implementation_decomposition(self):
        self.assertIn("implementation ticket decomposition", self.lower)
        ticket_ids = re.findall(r"`I-\d{3}`", self.text)
        self.assertGreaterEqual(len(set(ticket_ids)), 5)
        self.assertIn("dependency order", self.lower)
        self.assertIn("red", self.lower)
        self.assertIn("green", self.lower)
        self.assertIn("independent review", self.lower)

    def test_design_ticket_contains_no_production_artifacts(self):
        self.assertEqual(production_scope_violations(P001_DESIGN_CHANGED_PATHS), ())
        self.assertIn("scope:** design only", self.lower)
        self.assertIn("this design pr does **not** create these directories", self.lower)
        self.assertIn("implementation tickets will create them after this plan is accepted", self.lower)


if __name__ == "__main__":
    unittest.main()
