"""I-033E6 RED: source-backed no-target proposals and independent packets."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest

from tfont.batch_proposals import compile_candidate_batch, load_ledger
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.digests import canonical_json_bytes, evidence_record_digest
from tfont.review_packets import build_review_packet, verify_review_packet
from tfont.external_review_gate import evaluate_review_snapshot
from tests.i033e.test_external_review_red import (
    REPO, SHA, REVIEWER, body_for, pr_data, review,
)


def no_target_cohort():
    """Real pinned BHSA sp=prps source definition, not a synthetic target."""
    ledger = copy.deepcopy(load_ledger())
    ledger["schema_version"] = 2
    native = ledger["source_registry"]["bhsa"]
    from tfont.batch_proposals import packaged_resource
    record = packaged_resource(native["evidence_resource"])
    record["evidence_id"] = "evidence:bhsa:word-sp-source-prps-review-candidate"
    record["reviewed_content"]["source_definitions"]["prps"] = {
        "gloss": "personal pronoun",
        "line": 24,
        "featureObservations": 5035,
    }
    record["content_digest"] = evidence_record_digest(record)
    name = "resources/profiles/bhsa/batch-candidates/native-prps.json"
    native["evidence_resource"] = name
    ledger["decisions"].append({
        "corpus_id": "bhsa", "value": "prps", "assessment": "native-only",
        "rationale": (
            "Original BHSA docs/features/sp.md line 24 calls prps a personal "
            "pronoun; defer a class-level OLiA equivalence rather than "
            "asserting a target based on its code spelling."
        ),
    })
    return ledger, CandidateEvidenceResources(ledger, {name: record})


class NoTargetBatchRed(unittest.TestCase):
    def test_real_native_source_no_target_compiles_as_unreviewed_mapping(self):
        ledger, read = no_target_cohort()
        result = compile_candidate_batch(ledger, resource_loader=read)
        self.assertFalse(result["release_authorized"])
        self.assertEqual(result["count"], 5)
        native = next(m for m in result["candidates"]
                      if m["mapping_id"] == "mapping:bhsa:native-sp-prps")
        self.assertEqual(native["native_state"], "native-only")
        self.assertEqual(native["projections"], [])
        self.assertEqual(native["ambiguous_candidates"], [])
        self.assertEqual(native["external_references"], [])
        self.assertEqual(len(native["evidence"]), 1)
        self.assertEqual(native["evidence"][0]["evidence_id"],
                         "evidence:bhsa:word-sp-source-prps-review-candidate")
        self.assertEqual(native["native_binding"]["value"], "prps")
        self.assertNotIn("review", native)
        self.assertEqual(native["profiles"], ["linguistic"])
        self.assertEqual(native["capabilities"], ["linguistic.part-of-speech"])

    def test_packet_commits_no_target_source_rationale_without_projection(self):
        ledger, read = no_target_cohort()
        packet = build_review_packet(ledger, resource_loader=read)
        self.assertEqual(packet["schema_version"], 2)
        self.assertEqual(packet["count"], 5)
        row = next(x for x in packet["rows"]
                   if x["mapping_id"] == "mapping:bhsa:native-sp-prps")
        self.assertEqual(row["assessment"], "native-only")
        self.assertIsNone(row["ontology_target"])
        self.assertIsNone(row["formal_kind"])
        self.assertIsNone(row["projection_semantic_digest"])
        self.assertEqual(row["coverage_item_ids"], ['node_value:sp="prps"'])
        self.assertEqual(len(row["evidence"]), 1)
        self.assertTrue(verify_review_packet(packet, ledger, resource_loader=read))
        changed = copy.deepcopy(ledger)
        changed["decisions"][-1]["rationale"] += " Different scholarly judgment."
        revised = build_review_packet(changed, resource_loader=read)
        revised_row = next(x for x in revised["rows"] if x["mapping_id"] == row["mapping_id"])
        self.assertNotEqual(row["decision_digest"], revised_row["decision_digest"])
        self.assertNotEqual(packet["batch_digest"], revised["batch_digest"])

    def test_external_reviewer_attests_native_only_no_publishing(self):
        ledger, read = no_target_cohort()
        packet = build_review_packet(ledger, resource_loader=read)
        permissions = {REVIEWER: "write"}
        for verdict in ("accept", "reject", "needs-evidence"):
            body = body_for(packet, first=verdict)
            event = review(packet, body=body)
            result = evaluate_review_snapshot(
                packet=packet,repository=REPO,pr_number=299,
                expected_head_sha=SHA,pull_request=pr_data(),
                reviews=[event],reviewer_permissions=permissions,
            )
            native_row = next(
                row for row in result["rows"]
                if row["mapping_id"] == "mapping:bhsa:native-sp-prps"
            )
            self.assertEqual(native_row["disposition"], verdict)
            self.assertEqual(
                result["counts"][verdict],
                5 if verdict == "needs-evidence" else 1,
            )
            self.assertNotIn("release_authorized", result)
        self.assertFalse(packet["release_authorized"])

    def test_protected_exact_head_fetch_and_live_review_v2(self):
        import os
        from urllib.parse import unquote
        from unittest.mock import patch
        from tests.i033e import test_protected_pr_batch_gate_red as transport

        ledger, read = no_target_cohort()
        packet = build_review_packet(ledger, resource_loader=read)
        name = ledger["source_registry"]["bhsa"]["evidence_resource"]
        source_path = "docs/research/data/batch_review/evidence/bhsa-prps.json"
        manifest = {
            "schema_version": 2,
            "ledger": transport.LEDGER,
            "packet": transport.PACKET,
            "evidence_resources": {name: source_path},
        }
        records = {
            transport.MANIFEST: transport.blob(
                json.dumps(manifest).encode(), transport.MANIFEST
            ),
            transport.LEDGER: transport.blob(
                json.dumps(ledger).encode(), transport.LEDGER
            ),
            transport.PACKET: transport.blob(
                json.dumps(packet).encode(), transport.PACKET
            ),
            source_path: transport.blob(
                json.dumps(read(name)).encode(), source_path
            ),
        }
        fixture = transport.ProtectedBatchGateRED()
        fixture.setUp()
        gate = fixture.gate
        routes = []
        def api(path, token):
            routes.append(path)
            if path.endswith("/pulls/299"):
                return pr_data()
            if "/contents/" in path:
                name_at_head, ref = path.split("/contents/", 1)[1].split("?ref=")
                self.assertEqual(ref, SHA)
                return records[unquote(name_at_head)]
            if "/reviews?" in path:
                return [review(packet)]
            if path.endswith("/collaborators/" + REVIEWER + "/permission"):
                return {"permission": "write"}
            raise AssertionError("Unexpected privileged route: " + path)
        with (
            patch.dict(os.environ, {"GITHUB_TOKEN": "test-read-token"}),
            patch.object(gate, "_github_event", return_value=(REPO, 299, SHA)),
            patch.object(gate, "_api", side_effect=api),
        ):
            got_packet, got_ledger, verified = gate.fetch_pr_head_context()
            self.assertTrue(verify_review_packet(
                got_packet, got_ledger, resource_loader=verified
            ))
            eligibility = gate.evaluate_live_gate(
                got_packet, got_ledger, resource_loader=verified
            )
        self.assertEqual(got_packet["schema_version"], 2)
        self.assertEqual(eligibility["counts"]["accept"], 1)
        self.assertNotIn("release_authorized", eligibility)
        self.assertEqual(sum("/contents/" in route for route in routes), 4)

    def test_v1_frozen_legacy_packet_and_candidates_unchanged(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        original = build_review_packet(load_ledger())
        frozen = (root / "docs/research/data/generated/i033d/adj-adv-review-request.json"
                  ).read_text(encoding="utf-8")
        from tfont.review_packets import serialized
        self.assertEqual(serialized(original), frozen)
        self.assertEqual(original["schema_version"], 1)
        self.assertEqual(original["count"], 4)


if __name__ == "__main__":
    unittest.main()
