"""Real-data proposal integrity; supplementary evidence is never approval."""
import copy
import json
import unittest
from unittest.mock import patch

from tfont.batch_proposals import load_ledger, packaged_resource
from tfont.digests import evidence_record_digest
from tfont.review_packets import build_review_packet, verify_review_packet
from tfont.external_review_gate import ExternalReviewError
from tests.i033e import test_protected_pr_batch_gate_red as transport
from tests.i033e.test_protected_pr_batch_gate_red import blob, MANIFEST
from tests.i033e.test_external_review_red import REPO, SHA, REVIEWER, pr_data, review


def cohort():
    ledger = copy.deepcopy(load_ledger())
    source = ledger["source_registry"]["bhsa"]
    native = packaged_resource(source["evidence_resource"])
    native["evidence_id"] = "evidence:bhsa:word-sp-candidate-cohort"
    native["content_digest"] = evidence_record_digest(native)
    name = "resources/profiles/bhsa/batch-candidates/native-sp.json"
    source["evidence_resource"] = name
    original = ledger["ontology_evidence_resources"]["adjective"]
    ontology = packaged_resource(original)
    ontology["evidence_id"] = "evidence:olia:adjective-candidate-cohort"
    ontology["content_digest"] = evidence_record_digest(ontology)
    target = original.replace("adjective-evidence.json", "candidate-adjective.json")
    ledger["ontology_evidence_resources"]["adjective"] = target
    return ledger, {name: native, target: ontology}


def loader(ledger, evidence):
    from tfont.candidate_evidence import CandidateEvidenceResources
    return CandidateEvidenceResources(ledger, evidence)


class CandidateEvidenceTests(unittest.TestCase):
    def test_packet_forwards_loader_to_compile_and_verify(self):
        ledger, evidence = cohort()
        def read(name):
            return copy.deepcopy(evidence[name]) if name in evidence else packaged_resource(name)
        packet = build_review_packet(ledger, resource_loader=read)
        self.assertTrue(verify_review_packet(packet, ledger, resource_loader=read))

    def test_packet_reproduces_new_evidence_without_any_review_authority(self):
        ledger, evidence = cohort()
        read = loader(ledger, evidence)
        packet = build_review_packet(ledger, resource_loader=read)
        self.assertTrue(verify_review_packet(packet, ledger, resource_loader=read))
        self.assertFalse(packet["release_authorized"])
        self.assertEqual(packet["authority"], "unreviewed-proposal")
        self.assertNotEqual(packet["batch_digest"], build_review_packet(load_ledger())["batch_digest"])
        with self.assertRaises(ValueError):
            verify_review_packet(packet, ledger)

    def test_wrong_native_pin_uri_semantics_and_target_revision_rejected(self):
        for location, key, value in (
            ("record", "source_revision", "b" * 40),
            ("record", "source_uri", "https://example.org/fabricated"),
            ("content", "target_tf_revision", "b" * 40),
            ("content", "feature_semantics", "invented-part-of-speech"),
        ):
            ledger, evidence = cohort()
            native = next(v for v in evidence.values() if v["kind"] == "corpus-feature-definition")
            obj = native if location == "record" else native["reviewed_content"]
            obj[key] = value
            native["content_digest"] = evidence_record_digest(native)
            with self.subTest(key=key), self.assertRaises(ValueError):
                loader(ledger, evidence)
        ledger, evidence = cohort()
        ledger["source_registry"]["bhsa"]["source_revision"] = "b" * 40
        native = next(iter(evidence.values()))
        native["source_revision"] = "b" * 40
        native["content_digest"] = evidence_record_digest(native)
        with self.assertRaises(ValueError):
            loader(ledger, evidence)

    def test_wrong_ontology_identity_license_rdf_kind_blob_and_line_rejected(self):
        for location, key, value in (
            ("record", "source_revision", "b" * 40),
            ("record", "license_ref", "proprietary"),
            ("content", "rdf_type", "owl:ObjectProperty"),
            ("content", "snapshot_digest", "sha256:" + "f" * 64),
            ("content", "original_source_blob", "f" * 40),
            ("content", "declaration_line", 1),
            ("content", "target", "http://purl.org/olia/olia.owl#Invented"),
        ):
            ledger, evidence = cohort()
            record = next(v for v in evidence.values() if v["kind"] == "ontology-definition")
            obj = record if location == "record" else record["reviewed_content"]
            obj[key] = value
            record["content_digest"] = evidence_record_digest(record)
            with self.subTest(key=key), self.assertRaises(ValueError):
                loader(ledger, evidence)

    def test_reject_shadow_lock_unused_record_and_unbound_citation(self):
        for defect in ("shadow", "identity", "lock", "unused", "citation", "digest"):
            ledger, evidence = cohort()
            if defect == "shadow":
                original = load_ledger()["source_registry"]["bhsa"]["evidence_resource"]
                ledger["source_registry"]["bhsa"]["evidence_resource"] = original
                record = evidence.pop(next(iter(evidence)))
                evidence[original] = record
            elif defect == "identity":
                record = next(iter(evidence.values()))
                original = load_ledger()["source_registry"]["bhsa"]["evidence_resource"]
                record["evidence_id"] = packaged_resource(original)["evidence_id"]
                record["content_digest"] = evidence_record_digest(record)
            elif defect == "lock":
                key = ledger["ontology_lock_resource"]
                evidence[key] = packaged_resource(key)
            elif defect == "unused":
                evidence["resources/profiles/bhsa/batch-candidates/unused.json"] = copy.deepcopy(next(iter(evidence.values())))
            elif defect == "citation":
                next(iter(evidence.values()))["citation"] = {"claim": "unbound by legacy digest"}
            else:
                next(iter(evidence.values()))["content_digest"] = "sha256:" + "f" * 64
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                loader(ledger, evidence)

    def test_loader_copies_inputs_and_packet_binds_normalized_source_coordinates(self):
        ledger, evidence = cohort()
        read = loader(ledger, evidence)
        packet = build_review_packet(ledger, resource_loader=read)
        name = next(iter(evidence))
        evidence[name]["reviewed_content"]["source_definitions"]["adjv"]["line"] = 999
        returned = read(name)
        returned["reviewed_content"]["source_definitions"]["adjv"]["line"] = 777
        self.assertTrue(verify_review_packet(packet, ledger, resource_loader=read))
        evidence[name]["content_digest"] = evidence_record_digest(evidence[name])
        changed = loader(ledger, evidence)
        with self.assertRaises(ValueError):
            verify_review_packet(packet, ledger, resource_loader=changed)

    def test_malformed_source_registry_fails_with_controlled_error(self):
        for field in ("source_registry", "ontology_evidence_resources"):
            ledger, evidence = cohort()
            ledger[field] = []
            with self.subTest(field=field), self.assertRaises(ValueError):
                loader(ledger, evidence)


class ProtectedCandidateEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = transport.ProtectedBatchGateRED()
        self.fixture.setUp()
        self.ledger, self.evidence = cohort()

    def records(self, *, manifest_changes=None):
        packet = build_review_packet(self.ledger, resource_loader=loader(self.ledger, self.evidence))
        manifest = dict(self.fixture.manifest, schema_version=2, evidence_resources={})
        records = dict(self.fixture.records)
        for index, (name, record) in enumerate(self.evidence.items()):
            path = f"docs/research/data/batch_review/evidence/cohort-{index}.json"
            manifest["evidence_resources"][name] = path
            records[path] = blob(json.dumps(record).encode(), path)
        manifest.update(manifest_changes or {})
        records[MANIFEST] = blob(json.dumps(manifest).encode(), MANIFEST)
        records[manifest["ledger"]] = blob(json.dumps(self.ledger).encode(), manifest["ledger"])
        records[manifest["packet"]] = blob(json.dumps(packet).encode(), manifest["packet"])
        return records, packet

    def fetch(self, records):
        gate = self.fixture.gate
        # Reuse the exact-head mock transport, never a receipt-as-authority mock.
        with patch.object(gate, "fetch_pr_head_inputs", side_effect=gate.fetch_pr_head_context):
            return self.fixture.load(records=records)

    def test_fetch_to_live_review_uses_same_validated_resources(self):
        records, expected = self.records()
        (packet, ledger, read), routes = self.fetch(records)
        self.assertEqual(packet, expected)
        self.assertEqual(sum("/contents/" in r for r in routes), 5)
        def api(path, token):
            if path.endswith("/pulls/299"):
                return pr_data()
            if "/reviews?" in path:
                return [review(packet)]
            if path.endswith("/collaborators/" + REVIEWER + "/permission"):
                return {"permission": "write"}
            raise AssertionError(path)
        import os
        gate = self.fixture.gate
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test"}), \
             patch.object(gate, "_github_event", return_value=(REPO, 299, SHA)), \
             patch.object(gate, "_api", side_effect=api):
            report = gate.evaluate_live_gate(packet, ledger, resource_loader=read)
        self.assertEqual(report["counts"]["accept"], 1)
        self.assertIn("not-offline-signed", report["provenance"])
        with self.assertRaises(ExternalReviewError):
            self.fixture.load(records=records)  # old two-value API cannot drop context

    def test_manifest_evidence_paths_bounds_and_blob_mutations_fail_closed(self):
        for defect in ("path", "count", "blob", "duplicate-path", "wrong-type"):
            records, _ = self.records()
            manifest = dict(self.fixture.manifest, schema_version=2,
                            evidence_resources={name: f"docs/research/data/batch_review/evidence/cohort-{i}.json"
                                                for i, name in enumerate(self.evidence)})
            if defect == "path":
                manifest["evidence_resources"][next(iter(self.evidence))] = "../../evil.py"
            elif defect == "count":
                manifest["evidence_resources"] = {str(i): f"docs/research/data/batch_review/evidence/{i}.json" for i in range(33)}
            elif defect == "wrong-type":
                manifest["evidence_resources"] = []
            elif defect == "duplicate-path":
                names = list(manifest["evidence_resources"])
                manifest["evidence_resources"][names[1]] = manifest["evidence_resources"][names[0]]
            else:
                path = next(iter(manifest["evidence_resources"].values()))
                records[path] = dict(records[path], sha="f" * 40)
            records[MANIFEST] = blob(json.dumps(manifest).encode(), MANIFEST)
            with self.subTest(defect=defect), self.assertRaises(ExternalReviewError):
                self.fetch(records)

    def test_cli_retains_candidate_resources_through_live_revalidation(self):
        records, packet = self.records()
        context, _ = self.fetch(records)
        gate = self.fixture.gate
        import contextlib
        import io
        import os
        def api(path, token):
            if path.endswith("/pulls/299"):
                return pr_data()
            if "/reviews?" in path:
                return [review(packet)]
            if "/permission" in path:
                return {"permission": "write"}
            raise AssertionError(path)
        output = io.StringIO()
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test"}), \
             patch.object(gate, "_github_event", return_value=(REPO, 299, SHA)), \
             patch.object(gate, "_api", side_effect=api), \
             patch.object(gate, "fetch_pr_head_context", return_value=context), \
             patch("sys.argv", ["check_external_review.py", "--from-pr-head"]), \
             contextlib.redirect_stdout(output):
            self.assertEqual(gate.main(), 0)
        self.assertEqual(json.loads(output.getvalue())["counts"]["accept"], 1)


if __name__ == "__main__":
    unittest.main()
