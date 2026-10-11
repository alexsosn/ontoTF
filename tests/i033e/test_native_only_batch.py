"""Conservative proposal contracts using actual installed POS definitions.

Withholding a projection here is a test fixture, not a reversal of production
adjective/adverb mappings or a new reviewed semantic assertion.
"""
import copy
import hashlib
import json
import os
import unittest
from unittest.mock import patch

from tfont.batch_proposals import compile_candidate_batch, load_ledger
from tfont.digests import canonical_json_bytes
from tfont.review_packets import build_review_packet, verify_review_packet
from tfont.external_review_gate import evaluate_review_snapshot, ExternalReviewError
from tests.i033e import test_candidate_evidence as candidates
from tests.i033e import test_external_review_red as reviews
from tests.i033e import test_protected_pr_batch_gate_red as transport


def conservative(ledger=None):
    obj = copy.deepcopy(ledger if ledger is not None else load_ledger())
    obj["schema_version"] = 2
    obj["decisions"][0].update(
        assessment="native-only", term_key=None,
        rationale="Contract fixture: withhold shared projection pending adjudication; retain native adjective definition.",
    )
    return obj


def native_row(packet):
    return next(row for row in packet["rows"] if row["assessment"] == "native-only")


def rehash(packet):
    packet["batch_digest"] = "sha256:" + hashlib.sha256(canonical_json_bytes(
        {k: v for k, v in packet.items() if k != "batch_digest"}
    )).hexdigest()


class NativeOnlyBatchTests(unittest.TestCase):
    def test_mixed_candidates_preserve_no_target_state(self):
        compiled = compile_candidate_batch(conservative())
        self.assertFalse(compiled["release_authorized"])
        self.assertEqual(compiled["schema_version"], 2)
        self.assertEqual(compiled["disposition_counts"], {"exact": 3, "native-only": 1})
        mapping = next(m for m in compiled["candidates"] if m["native_state"] == "native-only")
        self.assertEqual(mapping["mapping_id"], "mapping:bhsa:olia-native-sp-adjv")
        self.assertEqual(mapping["native_binding"]["value"], "adjv")
        self.assertEqual(len(mapping["evidence"]), 1)
        for key in ("projections", "ambiguous_candidates", "external_references"):
            self.assertEqual(mapping[key], [])
        self.assertNotIn("review", mapping)

    def test_all_native_only_needs_no_term_evidence(self):
        ledger = conservative()
        ledger["ontology_evidence_resources"] = {}
        for row in ledger["decisions"]:
            row.update(assessment="native-only", term_key=None)
        packet = build_review_packet(ledger)
        self.assertEqual(packet["disposition_counts"], {"exact": 0, "native-only": 4})
        self.assertTrue(verify_review_packet(packet, ledger))
        for row in packet["rows"]:
            self.assertEqual(row["assessment"], "native-only")
            for field in ("ontology_target", "formal_kind", "projection_semantic_digest"):
                self.assertIsNone(row[field])
            self.assertEqual(row["semantic_role"], "annotation-value")
            self.assertFalse(packet["release_authorized"])

    def test_rationale_and_assessment_are_review_bound(self):
        ledger = conservative()
        packet = build_review_packet(ledger)
        changed = copy.deepcopy(ledger)
        changed["decisions"][0]["rationale"] += " Distinct scholarly caveat."
        revised = build_review_packet(changed)
        self.assertNotEqual(packet["batch_digest"], revised["batch_digest"])
        self.assertNotEqual(native_row(packet)["decision_digest"], native_row(revised)["decision_digest"])
        for field, value in (("assessment", "exact"), ("ontology_target", "http://purl.org/olia/olia.owl#Adjective"),
                             ("projection_semantic_digest", "sha256:" + "f" * 64), ("schema_version", 1)):
            altered = copy.deepcopy(packet)
            if field == "schema_version": altered[field] = value
            else: native_row(altered)[field] = value
            rehash(altered)
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_review_packet(altered, ledger)

    def test_reject_target_injection_invalid_source_duplicate_and_downgrade(self):
        for defect in ("target", "projection", "missing", "pin", "duplicate", "v1", "bool", "float", "exact-null"):
            ledger = conservative()
            row = ledger["decisions"][0]
            if defect == "target": row["term_key"] = "adjective"
            elif defect == "projection": row["projections"] = [{"target": "invented"}]
            elif defect == "missing": row["value"] = "invented"
            elif defect == "pin": ledger["source_registry"]["bhsa"]["source_revision"] = "a" * 40
            elif defect == "duplicate": ledger["decisions"].append(copy.deepcopy(row))
            elif defect == "v1": ledger["schema_version"] = 1
            elif defect == "bool": ledger["schema_version"] = True
            elif defect == "float": ledger["schema_version"] = 2.0
            else: row["assessment"] = "exact"
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                compile_candidate_batch(ledger)

    def test_external_dispositions_do_not_promote_native_only(self):
        packet = build_review_packet(conservative())
        for disposition in ("accept", "reject", "needs-evidence"):
            body = json.loads(reviews.body_for(packet).split("\n", 1)[1])
            ident = native_row(packet)["mapping_id"]
            next(row for row in body["rows"] if row["mapping_id"] == ident)["disposition"] = disposition
            event = reviews.review(packet, body="ontoTF-batch-review-v1\n" + json.dumps(body))
            result = evaluate_review_snapshot(
                packet=packet, repository=reviews.REPO, pr_number=299,
                expected_head_sha=reviews.SHA, pull_request=reviews.pr_data(),
                reviews=[event], reviewer_permissions={reviews.REVIEWER: "write"},
            )
            self.assertEqual(next(row for row in result["rows"] if row["mapping_id"] == ident)["disposition"], disposition)
            self.assertNotIn("release_authorized", result)
            self.assertEqual(native_row(packet)["assessment"], "native-only")
        with self.assertRaises(ExternalReviewError):
            evaluate_review_snapshot(
                packet=packet, repository=reviews.REPO, pr_number=299,
                expected_head_sha=reviews.SHA, pull_request=reviews.pr_data(),
                reviews=[reviews.review(packet, user=reviews.AUTHOR)],
                reviewer_permissions={reviews.AUTHOR: "admin"},
            )

    def test_supplementary_native_evidence_survives_protected_live_path(self):
        ledger, evidence = candidates.cohort()
        ledger = conservative(ledger)
        ledger["decisions"] = [ledger["decisions"][0]]
        ledger["ontology_evidence_resources"] = {}
        evidence = {k: v for k, v in evidence.items() if v["kind"] == "corpus-feature-definition"}
        read = candidates.loader(ledger, evidence)
        packet = build_review_packet(ledger, resource_loader=read)
        evidence_path = "docs/research/data/batch_review/evidence/native-only.json"
        name, record = next(iter(evidence.items()))
        objects = {
            transport.MANIFEST: {"schema_version": 2, "ledger": transport.LEDGER,
                                 "packet": transport.PACKET, "evidence_resources": {name: evidence_path}},
            transport.LEDGER: ledger, transport.PACKET: packet, evidence_path: record,
        }
        cli = transport.cli()
        def api(path, token):
            if "/contents/" in path:
                from urllib.parse import unquote
                target, sha = path.split("/contents/", 1)[1].split("?ref=")
                self.assertEqual(sha, reviews.SHA)
                target = unquote(target)
                return transport.blob(json.dumps(objects[target]).encode(), target)
            if path.endswith("/pulls/299"): return reviews.pr_data()
            if "/reviews?" in path: return [reviews.review(packet)]
            if path.endswith("/permission"): return {"permission": "write"}
            raise AssertionError(path)
        with patch.dict(os.environ, {"GITHUB_TOKEN": "read-token"}), \
             patch.object(cli, "_github_event", return_value=(reviews.REPO, 299, reviews.SHA)), \
             patch.object(cli, "_api", side_effect=api):
            fetched, source, context = cli.fetch_pr_head_context()
            result = cli.evaluate_live_gate(fetched, source, resource_loader=context)
        self.assertEqual(result["rows"][0]["disposition"], "accept")
        self.assertEqual(fetched["rows"][0]["ontology_target"], None)
        self.assertNotIn("release_authorized", result)
