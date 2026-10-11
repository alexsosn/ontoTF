"""Real-source conservative handoff fixtures; mocked reviews are not authority."""
import copy
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tfont.batch_proposals import load_ledger, packaged_resource
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.digests import evidence_record_digest
from tfont.review_packets import build_review_packet
from tfont.external_review_gate import evaluate_review_snapshot
from tests.i033e import test_external_review_red as reviews
from tests.i033e import test_protected_pr_batch_gate_red as transport


def cohort():
    ledger = load_ledger()
    ledger["schema_version"] = 2
    ledger["decisions"] = []
    evidence = {}
    definitions = {
        "bhsa": [("art", "article", 17), ("prep", "preposition", 22),
                 ("conj", "conjunction", 23), ("prps", "personal pronoun", 24),
                 ("prde", "demonstrative pronoun", 25), ("prin", "interrogative pronoun", 26),
                 ("intj", "interjection", 27), ("nega", "negative particle", 28),
                 ("inrg", "interrogative particle", 29)],
        "syriac": [("pron", "pronoun", 91)],
    }
    for corpus, values in definitions.items():
        spec = ledger["source_registry"][corpus]
        record = packaged_resource(spec["evidence_resource"])
        record["evidence_id"] = f"evidence:{corpus}:handoff-contract-source"
        for value, gloss, line in values:
            record["reviewed_content"]["source_definitions"][value] = {"gloss": gloss, "line": line}
            ledger["decisions"].append({"corpus_id": corpus, "value": value, "assessment": "native-only",
                "rationale": "Contract fixture withholding projection for independently adjudicated native category; not a production decision."})
        record["content_digest"] = evidence_record_digest(record)
        name = f"resources/profiles/{corpus}/batch-candidates/handoff-source.json"
        spec["evidence_resource"] = name
        evidence[name] = record
    read = CandidateEvidenceResources(ledger, evidence)
    packet = build_review_packet(ledger, resource_loader=read)
    body = {"packet_digest": packet["batch_digest"], "rows": [
        {"mapping_id": row["mapping_id"], "decision_digest": row["decision_digest"], "disposition": "accept"}
        for row in packet["rows"]]}
    report = evaluate_review_snapshot(packet=packet, repository=reviews.REPO, pr_number=299,
        expected_head_sha=reviews.SHA, pull_request=reviews.pr_data(),
        reviews=[reviews.review(packet, body="ontoTF-batch-review-v1\n" + json.dumps(body))],
        reviewer_permissions={reviews.REVIEWER: "write"})
    return ledger, read, packet, report


def assemble(ledger, read, packet, report):
    from tfont.overlay_handoff import build_overlay_handoff
    return build_overlay_handoff(packet, ledger, report, resource_loader=read)


class OverlayHandoffTests(unittest.TestCase):
    def test_ten_real_native_items_compact_and_unsealed(self):
        ledger, read, packet, report = cohort()
        pack = assemble(ledger, read, packet, report)
        self.assertFalse(pack["release_authorized"])
        self.assertEqual(pack["authority"], "requires-workflow-attestation-and-registry-validation")
        self.assertEqual(pack["counts"], {"exact": 0, "native-only": 10})
        self.assertEqual(pack, assemble(ledger, read, packet, report))
        self.assertNotIn("semantic_items", pack)
        self.assertNotIn("profile", pack)
        self.assertEqual(sum(len(x["mappings"]) for x in pack["corpora"]), 10)
        self.assertEqual(sum(len(x["added_dependencies"]) for x in pack["corpora"]), 10)
        self.assertEqual(sum(len(x["added_evidence"]) for x in pack["corpora"]), 2)
        for corpus in pack["corpora"]:
            self.assertEqual(corpus["base_release"], "0.4.0")
            self.assertEqual(len(corpus["coverage_assignments"]), len(corpus["mappings"]))
            self.assertTrue(all("review" not in m and not m["projections"] for m in corpus["mappings"]))
            self.assertTrue(all(not item["common_target"] for item in corpus["coverage_assignments"]))
        self.assertLess(len(json.dumps(pack)), 40000)

    def test_forged_observation_cannot_assemble(self):
        ledger, read, packet, report = cohort()
        for defect in ("digest", "duplicate", "count", "pin"):
            changed = copy.deepcopy(report)
            if defect == "digest": changed["rows"][0]["decision_digest"] = "sha256:" + "a" * 64
            elif defect == "duplicate": changed["rows"].append(changed["rows"][0])
            elif defect == "count": changed["counts"]["accept"] = 11
            else: changed["batch_digest"] = "sha256:" + "a" * 64
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                assemble(ledger, read, packet, changed)

    def test_inherited_selector_cannot_be_released_as_new_native_only(self):
        ledger, read, _, report = cohort()
        ledger["decisions"][0]["value"] = "adjv"
        packet = build_review_packet(ledger, resource_loader=read)
        report["batch_digest"] = packet["batch_digest"]
        report["rows"] = [{"mapping_id": r["mapping_id"], "decision_digest": r["decision_digest"],
                           "disposition": "accept"} for r in packet["rows"]]
        with self.assertRaisesRegex(ValueError, "inherited|reviewed"):
            assemble(ledger, read, packet, report)

    def test_new_selector_cannot_reuse_inherited_mapping_or_projection_identity(self):
        ledger, read, _, report = cohort()
        # Deliberately conflicting proposal, not a scholarly equivalence:
        # new art selector would reuse the installed adjv mapping identity.
        ledger["decisions"][0].update(assessment="exact", term_key="adjective")
        packet = build_review_packet(ledger, resource_loader=read)
        report["batch_digest"] = packet["batch_digest"]
        report["rows"] = [{"mapping_id": r["mapping_id"], "decision_digest": r["decision_digest"],
                           "disposition": "accept"} for r in packet["rows"]]
        with self.assertRaisesRegex(ValueError, "inherited.*identity"):
            assemble(ledger, read, packet, report)

    def test_rejected_and_needs_evidence_candidates_are_excluded(self):
        ledger, read, _, report = cohort()
        for corpus in ("bhsa", "syriac"):
            ledger["decisions"].append({"corpus_id": corpus, "value": "adjv", "term_key": "adjective",
                "assessment": "exact", "rationale": "Existing exact contract fixture, not accepted as a new release."})
        packet = build_review_packet(ledger, resource_loader=read)
        report.update(batch_digest=packet["batch_digest"], counts={"accept": 10, "reject": 1, "needs-evidence": 1})
        report["rows"] = [{"mapping_id": r["mapping_id"], "decision_digest": r["decision_digest"],
            "disposition": ("reject" if r["corpus_id"] == "bhsa" else "needs-evidence")
            if r["assessment"] == "exact" else "accept"} for r in packet["rows"]]
        pack = assemble(ledger, read, packet, report)
        self.assertEqual(pack["counts"], {"exact": 0, "native-only": 10})
        self.assertTrue(all(m["native_state"] == "native-only" for c in pack["corpora"] for m in c["mappings"]))
        self.assertEqual(pack["review_observation"]["counts"], report["counts"])

    def test_inherited_native_only_coverage_remains_authoritative(self):
        from tfont.coverage import load_packaged_coverage_manifest
        ledger, read, packet, report = cohort()
        real = load_packaged_coverage_manifest("p004-i027c2-bhsa-adj-adv-v1", "bhsa")
        native = next(item["accounting"]["production"] for item in real["semantic_items"]
                      if item["accounting"]["production"] and item["accounting"]["production"]["assessments"] == ["native-only"])
        next(item for item in real["semantic_items"] if item["item_id"] == 'node_value:sp="art"')["accounting"]["production"] = copy.deepcopy(native)
        def coverage(name, corpus):
            return real if corpus == "bhsa" else load_packaged_coverage_manifest(name, corpus)
        with patch("tfont.overlay_handoff.load_packaged_coverage_manifest", side_effect=coverage), self.assertRaisesRegex(ValueError, "reviewed coverage"):
            assemble(ledger, read, packet, report)

    def test_cli_final_revocation_no_write_and_exclusive_output(self):
        ledger, read, packet, report = cohort()
        cli = transport.cli()
        report["provenance"] = "github-live-rest-verified-at-this-run;not-offline-signed"
        with patch("sys.stdout", new=io.StringIO()), patch("sys.stderr", new=io.StringIO()), tempfile.TemporaryDirectory() as directory, patch.object(cli, "fetch_pr_head_context", return_value=(packet, ledger, read)), \
             patch.object(cli, "evaluate_live_gate", side_effect=[report, dict(report, review_id=101)]), \
             patch("sys.argv", ["gate", "--from-pr-head", "--publish-handoff"]):
            previous = os.getcwd()
            try:
                os.chdir(directory)
                self.assertEqual(cli.main(), 1)
                self.assertFalse(Path("batch-review-pack.json").exists())
                with patch.object(cli, "evaluate_live_gate", return_value=report):
                    self.assertEqual(cli.main(), 0)
                    raw = Path("batch-review-pack.json").read_bytes()
                    self.assertEqual(cli.main(), 1)
                    self.assertEqual(Path("batch-review-pack.json").read_bytes(), raw)
            finally: os.chdir(previous)

    def test_cli_local_json_cannot_publish(self):
        cli = transport.cli()
        with patch("sys.argv", ["gate", "--packet", "local.json", "--ledger", "local-ledger.json", "--publish-handoff"]), \
             self.assertRaises(SystemExit):
            cli.main()

    def test_protected_workflow_attests_only_fixed_protected_output(self):
        text = transport.WORKFLOW.read_text()
        self.assertIn("ontology-batch-publish", text)
        self.assertIn("--from-pr-head --publish-handoff", text)
        self.assertIn("actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6", text)
        self.assertIn("subject-path: batch-review-pack.json", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("ref: ${{ github.event.pull_request.head", text)
        self.assertIn("ref: ${{ github.sha }}", text)
