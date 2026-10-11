"""Sparse outcomes from the real ten-category source-bound review fixture."""
import copy
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tfont.overlay_handoff import verify_overlay_handoff_integrity
from tfont.review_packets import build_review_packet
from tests.i033e.test_overlay_handoff import cohort, assemble
from tests.i033e import test_protected_pr_batch_gate_red as transport
from tests.i033e8.test_handoff_integrity_red import sealed


def adjudicate(report, states):
    report = copy.deepcopy(report)
    for row, state in zip(report["rows"], states):
        row["disposition"] = state
    report["counts"] = {state: sum(row["disposition"] == state for row in report["rows"])
                        for state in ("accept", "reject", "needs-evidence")}
    return report


class PartialAcceptanceTests(unittest.TestCase):
    def test_mixed_outcomes_publish_only_accepted_ids_and_dependencies(self):
        ledger, read, packet, report = cohort()
        for states in (["reject"] + ["accept"] * 9,
                       ["accept"] + ["reject"] * 4 + ["needs-evidence"] * 5,
                       ["accept"] * 4 + ["reject"] * 3 + ["needs-evidence"] * 3):
            with self.subTest(states=states):
                observation = adjudicate(report, states)
                pack = assemble(ledger, read, packet, observation)
                self.assertIsNone(verify_overlay_handoff_integrity(pack))
                accepted = {r["mapping_id"] for r in observation["rows"] if r["disposition"] == "accept"}
                mappings = [m for c in pack["corpora"] for m in c["mappings"]]
                self.assertEqual({m["mapping_id"] for m in mappings}, accepted)
                self.assertEqual({a["mapping_id"] for c in pack["corpora"] for a in c["coverage_assignments"]}, accepted)
                self.assertEqual({d["dependency_id"] for c in pack["corpora"] for d in c["added_dependencies"]},
                                 {d for m in mappings for d in m["native_dependencies"]})
                self.assertEqual(pack["counts"], {"exact": 0, "native-only": len(accepted)})
                self.assertEqual(pack["review_observation"], observation)
                self.assertEqual(pack, assemble(ledger, read, packet, observation))
                self.assertEqual({c["corpus_id"] for c in pack["corpora"]}, {m["corpus_id"] for m in mappings})

    def test_fewer_than_ten_proposals_cannot_be_published(self):
        ledger, read, _, report = cohort()
        ledger["decisions"].pop()
        packet = build_review_packet(ledger, resource_loader=read)
        report.update(batch_digest=packet["batch_digest"], counts={"accept": 9, "reject": 0, "needs-evidence": 0})
        report["rows"] = [{"mapping_id": r["mapping_id"], "decision_digest": r["decision_digest"], "disposition": "accept"}
                          for r in packet["rows"]]
        with self.assertRaisesRegex(ValueError, "propos|source-bound"):
            assemble(ledger, read, packet, report)

    def test_underfilled_review_or_unaccepted_mapping_cannot_pass_integrity(self):
        ledger, read, packet, report = cohort()
        observation = adjudicate(report, ["accept"] * 9 + ["reject"])
        pack = assemble(ledger, read, packet, observation)
        smaller = copy.deepcopy(pack)
        smaller["review_observation"]["rows"].pop()
        smaller["review_observation"]["counts"]["reject"] = 0
        with self.assertRaisesRegex(ValueError, "propos|source-bound"):
            verify_overlay_handoff_integrity(sealed(smaller))
        forged = assemble(ledger, read, packet, report)
        forged["review_observation"] = observation
        with self.assertRaises(ValueError):
            verify_overlay_handoff_integrity(sealed(forged))

    def test_zero_acceptance_is_a_fresh_audit_without_output(self):
        ledger, read, packet, report = cohort()
        report = adjudicate(report, ["reject"] * 5 + ["needs-evidence"] * 5)
        cli = transport.cli()
        with tempfile.TemporaryDirectory() as directory, patch.object(cli, "fetch_pr_head_context", return_value=(packet, ledger, read)), \
             patch("sys.argv", ["gate", "--from-pr-head", "--publish-handoff"]), \
             patch("sys.stdout", new_callable=io.StringIO) as output, patch("sys.stderr", new=io.StringIO()):
            previous = os.getcwd()
            try:
                os.chdir(directory)
                with patch.object(cli, "evaluate_live_gate", return_value=report) as gate:
                    self.assertEqual(cli.main(), 0)
                    self.assertEqual(gate.call_count, 2)
                    self.assertTrue(all(call.kwargs["require_publish"] for call in gate.call_args_list))
                    self.assertIn('"accept": 0', output.getvalue())
                    self.assertFalse(Path("batch-review-pack.json").exists())
                with patch.object(cli, "evaluate_live_gate", side_effect=[report, dict(report, review_id=999)]) as gate:
                    self.assertEqual(cli.main(), 1)
                    self.assertEqual(gate.call_count, 2)
                    self.assertFalse(Path("batch-review-pack.json").exists())
                Path("batch-review-pack.json").write_text("previous handoff")
                with patch.object(cli, "evaluate_live_gate", return_value=report):
                    self.assertEqual(cli.main(), 1)
                    self.assertEqual(Path("batch-review-pack.json").read_text(), "previous handoff")
            finally:
                os.chdir(previous)
        with self.assertRaisesRegex(ValueError, "accepted|accepts"):
            assemble(ledger, read, packet, report)

    def test_signing_and_mapping_upload_require_fixed_output(self):
        text = transport.WORKFLOW.read_text()
        for marker in ("      - name: Bind pack bytes", "          name: ontology-overlay-handoff"):
            start = text.index(marker)
            if marker.startswith("          name:"):
                start = text.rfind("      - uses:", 0, start)
            step = text[start:].split("\n      - ", 1)[0]
            self.assertIn("if: hashFiles('batch-review-pack.json') != ''", step)
