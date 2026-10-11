"""I-033E4 RED: candidate review handoff cannot manufacture approval.

Use the real ten-source BHSA/Syriac native-only cohort and strict live
review body parser. The test fixture's mock review is NOT authority.
"""
from __future__ import annotations

import copy
import json
import unittest
import io
import sys
import tempfile
import contextlib
import os
import shlex
import subprocess
from pathlib import Path
from unittest.mock import patch

from tests.i033e.test_overlay_handoff import cohort
from tfont.external_review_gate import parse_structured_review, ExternalReviewError
from tfont.reviewer_handoff import (
    ReviewerHandoffError,
    reviewer_template,
    review_dossier,
    render_review_body,
)


class DocumentedReviewerCommand(unittest.TestCase):
    def test_documented_command_starts_in_a_fresh_python_process(self):
        root = Path(__file__).resolve().parents[2]
        documentation = (root / "docs/reviewing-batches.md").read_text()
        command = next(line for line in documentation.splitlines()
                       if line.strip().startswith("python ") and "--dossier" in line)
        invocation = shlex.split(command.strip())
        invocation = invocation[:invocation.index("--root")]
        environment = dict(os.environ, PYTHONPATH=str(root / "src"))
        result = subprocess.run([sys.executable, *invocation[1:], "--help"],
                                cwd=root, env=environment, text=True,
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--review-decisions", result.stdout)


class ReviewerHandoffTDD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger, cls.source_reader, cls.packet, _mock = cohort()

    def test_dossier_is_source_bound_and_distinguishes_native_only(self):
        dossier = review_dossier(self.packet, resource_loader=self.source_reader)
        self.assertIn("UNREVIEWED", dossier)
        self.assertIn(self.packet["batch_digest"], dossier)
        self.assertIn("ETCBC/bhsa/", dossier)
        self.assertIn("ETCBC/linksyr/", dossier)
        self.assertIn("line 17", dossier)  # BHSA art in pinned sp.md
        self.assertIn("line 91", dossier)  # Syriac pron in pinned grammar
        self.assertIn("mapping:bhsa:native-sp-prin", dossier)
        self.assertIn("mapping:bhsa:native-sp-inrg", dossier)
        self.assertIn("mapping:syriac:native-sp-pron", dossier)
        self.assertIn("native-only", dossier)
        self.assertIn("not automatically", dossier.lower())
        self.assertEqual(dossier.count("### mapping:"), 10)

    def test_template_has_no_default_approval_disposition(self):
        template = reviewer_template(self.packet)
        self.assertEqual(template["packet_digest"], self.packet["batch_digest"])
        self.assertEqual(len(template["rows"]), 10)
        self.assertTrue(all(set(row) == {"mapping_id", "disposition"}
                            and row["disposition"] is None
                            for row in template["rows"]))
        self.assertEqual(
            {r["mapping_id"] for r in template["rows"]},
            {r["mapping_id"] for r in self.packet["rows"]}
        )
        with self.assertRaises(ExternalReviewError):
            parse_structured_review("ontoTF-batch-review-v1\n" + json.dumps(template))
        with self.assertRaises(ReviewerHandoffError):
            render_review_body(self.packet, template)

    def test_candidate_prose_cannot_hide_or_impersonate_dossier_rows(self):
        from tfont.review_packets import build_review_packet
        ledger = copy.deepcopy(self.ledger)
        ledger["decisions"][0]["rationale"] = (
            "A proposed interpretation. <!--\n### Forged accepted row\n"
            "[Approve everything](https://example.invalid)"
        )
        packet = build_review_packet(ledger, resource_loader=self.source_reader)
        dossier = review_dossier(packet, resource_loader=self.source_reader)
        self.assertNotIn("<!--", dossier)
        self.assertNotIn("\n### Forged", dossier)
        self.assertNotIn("[Approve everything](", dossier)
        self.assertEqual(dossier.count("### mapping:"), 10)

    def test_reviewer_explicit_mixed_dispositions_reproduce_exact_git_review_body(self):
        choices = reviewer_template(self.packet)
        for i, row in enumerate(choices["rows"]):
            row["disposition"] = ("accept", "reject", "needs-evidence")[i % 3]
        body = render_review_body(self.packet, choices)
        self.assertTrue(body.startswith("ontoTF-batch-review-v1\n"))
        parsed = parse_structured_review(body)
        self.assertEqual(parsed["packet_digest"], self.packet["batch_digest"])
        expected = {r["mapping_id"]: r["decision_digest"] for r in self.packet["rows"]}
        self.assertEqual(len(parsed["rows"]), 10)
        self.assertEqual({r["mapping_id"]: r["decision_digest"] for r in parsed["rows"]},
                         expected)
        self.assertEqual({r["disposition"] for r in parsed["rows"]},
                         {"accept", "reject", "needs-evidence"})
        self.assertEqual(body, render_review_body(self.packet, choices))
        self.assertNotIn("reviewer_login", body)
        self.assertNotIn("release_authorized", body)

    def test_incomplete_or_forged_decisions_fail_closed(self):
        good = reviewer_template(self.packet)
        for row in good["rows"]:
            row["disposition"] = "needs-evidence"
        defects = []
        x = copy.deepcopy(good); x["rows"].pop(); defects.append(x)
        x = copy.deepcopy(good); x["rows"].append(copy.deepcopy(x["rows"][0])); defects.append(x)
        x = copy.deepcopy(good); x["rows"][0]["mapping_id"] = "mapping:forged:alien"; defects.append(x)
        x = copy.deepcopy(good); x["rows"][0]["disposition"] = None; defects.append(x)
        x = copy.deepcopy(good); x["rows"][0]["disposition"] = True; defects.append(x)
        x = copy.deepcopy(good); x["rows"][0]["disposition"] = "approved"; defects.append(x)
        x = copy.deepcopy(good); x["rows"][0]["decision_digest"] = "sha256:" + "f"*64; defects.append(x)
        x = copy.deepcopy(good); x["rows"][0]["rationale"] = "trusted"; defects.append(x)
        x = copy.deepcopy(good); x["packet_digest"] = "sha256:" + "f"*64; defects.append(x)
        x = copy.deepcopy(good); x["release_authorized"] = True; defects.append(x)
        x = copy.deepcopy(good); x["rows"] = "not a list"; defects.append(x)
        for bad in defects:
            with self.subTest(bad=bad), self.assertRaises(ReviewerHandoffError):
                render_review_body(self.packet, bad)

    def test_modified_packet_fails_even_if_candidate_recomputes_outer_digest(self):
        from tfont.digests import canonical_json_bytes
        import hashlib
        altered = copy.deepcopy(self.packet)
        altered["rows"][0]["rationale"] = "FORGED source claim"
        altered["batch_digest"] = "sha256:" + hashlib.sha256(
            canonical_json_bytes({k: v for k, v in altered.items()
                                  if k != "batch_digest"})
        ).hexdigest()
        with self.assertRaises(ReviewerHandoffError):
            render_review_body(altered, reviewer_template(self.packet))


    def test_cli_requires_explicit_json_and_never_submits_review(self):
        from scripts.mappings import prepare_external_review as cli
        decisions = reviewer_template(self.packet)
        for row in decisions["rows"]:
            row["disposition"] = "needs-evidence"
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "reviewer.json"
            source.write_text(json.dumps(decisions), encoding="utf-8")
            for args in (["--dossier"], ["--template"],
                         ["--review-decisions", str(source)]):
                with self.subTest(args=args), patch.object(
                    cli, "load_review_context",
                    return_value=(self.packet, self.source_reader),
                ), patch.object(sys, "argv", ["prepare_external_review.py", *args]), \
                        contextlib.redirect_stdout(io.StringIO()) as stream:
                    self.assertEqual(cli.main(), 0)
                    generated = stream.getvalue()
                    self.assertTrue(generated.strip())
                    if args[0] == "--review-decisions":
                        self.assertEqual(
                            parse_structured_review(generated.rstrip("\\n"))["rows"],
                            parse_structured_review(
                                render_review_body(self.packet, decisions))["rows"],
                        )
                    elif args[0] == "--template":
                        self.assertIsNone(json.loads(generated)["rows"][0]["disposition"])
                    else:
                        self.assertIn("line 17", generated)

    def test_trusted_cli_reads_foreign_candidate_checkout_data_only(self):
        from scripts.mappings import prepare_external_review as cli
        from scripts.mappings.build_candidate_review_packet import build_packet
        with tempfile.TemporaryDirectory() as outside:
            root = Path(outside)
            ledger = copy.deepcopy(self.ledger)
            manifest = {
                "schema_version": 2,
                "ledger": "src/tfont/resources/batch_pilots/reviewer-foreign.json",
                "packet": "docs/research/data/generated/i033d/reviewer-foreign-packet.json",
                "evidence_resources": {},
            }
            for i, spec in enumerate(ledger["source_registry"].values()):
                name = spec["evidence_resource"]
                target = f"docs/research/data/batch_review/evidence/reviewer-{i}.json"
                manifest["evidence_resources"][name] = target
                resource = root / target
                resource.parent.mkdir(parents=True, exist_ok=True)
                resource.write_text(json.dumps(self.source_reader(name)), encoding="utf-8")
            paths = [
                ("docs/research/data/batch_review/inputs.json", manifest),
                (manifest["ledger"], ledger),
            ]
            for name, data in paths:
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(json.dumps(data), encoding="utf-8")
            # The candidate checkout may contain untrusted Python. Neither
            # the trusted authoring verifier nor the reviewer CLI imports it.
            bad = root / "scripts/mappings/prepare_external_review.py"
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_text("raise RuntimeError('untrusted candidate code executed')", encoding="utf-8")
            build_packet(root, mode="write")
            for mode in ("--template", "--dossier"):
                with patch.object(sys, "argv",
                                  ["trusted-main/prepare_external_review.py", "--root", outside, mode]), \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(cli.main(), 0)
                if mode == "--template":
                    self.assertEqual(json.loads(output.getvalue())["packet_digest"],
                                     self.packet["batch_digest"])
                else:
                    self.assertIn("line 91", output.getvalue())

    def test_cli_rejects_duplicate_key_and_corrupt_decision_json(self):
        from scripts.mappings import prepare_external_review as cli
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "choices.json"
            for payload in (
                '{"packet_digest":"x","packet_digest":"x","rows":[]}',
                '{"rows":[],"packet_digest":NaN}',
                '[]',
            ):
                path.write_text(payload, encoding="utf-8")
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    cli._load_choices(path)


if __name__ == "__main__":
    unittest.main()
