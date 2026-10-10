"""I-033E: the only eligible 'live' path must fetch PR/reviews/permissions."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tfont.batch_proposals import load_ledger
from tfont.review_packets import build_review_packet
from tfont.external_review_gate import ExternalReviewError
from tests.i033e.test_external_review_red import (
    SHA, REPO, REVIEWER, body_for, pr_data, review,
)

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/mappings/check_external_review.py"


def cli():
    spec=importlib.util.spec_from_file_location("i033e_live_gate",SCRIPT)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class LiveReviewBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.ledger=load_ledger()
        self.packet=build_review_packet(self.ledger)
        self.gate=cli()

    def test_requires_real_trusted_github_event_not_local_json(self):
        with patch.dict(os.environ,{},clear=True),self.assertRaises(ExternalReviewError):
            self.gate.evaluate_live_gate(self.packet,self.ledger)
        for event_name in ("pull_request","workflow_dispatch","push"):
            with patch.dict(os.environ,{
                "GITHUB_EVENT_NAME":event_name,
                "GITHUB_TOKEN":"test-placeholder",
                "GITHUB_REPOSITORY":REPO,
                "GITHUB_EVENT_PATH":"/nonexistent/unsafe-event",
            },clear=True),self.subTest(event_name=event_name),self.assertRaises(ExternalReviewError):
                self.gate.evaluate_live_gate(self.packet,self.ledger)

    def test_rejects_changed_proposal_before_any_network_call(self):
        changed=dict(self.packet)
        changed["batch_digest"]="sha256:"+"f"*64
        with patch.object(self.gate,"_api") as network, self.assertRaises(ExternalReviewError):
            self.gate.evaluate_live_gate(changed,self.ledger)
        network.assert_not_called()

    def test_live_gate_fetches_own_pr_and_collaborator_permission(self):
        routes=[]
        def fake_api(path,token):
            routes.append(path)
            self.assertEqual(token,"fake-ci-token")
            if path.endswith("/pulls/299"):
                return pr_data()
            if "/reviews?" in path:
                return [review(self.packet)]
            if path.endswith("/collaborators/"+REVIEWER+"/permission"):
                return {"permission":"write"}
            raise AssertionError("unexpected GitHub API path: "+path)
        with patch.dict(os.environ,{"GITHUB_TOKEN":"fake-ci-token"}),              patch.object(self.gate,"_github_event",return_value=(REPO,299,SHA)),              patch.object(self.gate,"_api",side_effect=fake_api):
            result=self.gate.evaluate_live_gate(self.packet,self.ledger)
        self.assertEqual(result["counts"]["accept"],1)
        self.assertIn("not-offline-signed",result["provenance"])
        self.assertTrue(any("/pulls/299/reviews?" in r for r in routes))
        self.assertTrue(any("/collaborators/" in r for r in routes))

    def test_forged_self_review_cannot_pass_even_with_admin_permission(self):
        def fake_api(path,token):
            if path.endswith("/pulls/299"):return pr_data()
            if "/reviews?" in path:return [review(self.packet,user="proposal-author")]
            if "/permission" in path:return {"permission":"admin"}
            raise AssertionError(path)
        with patch.dict(os.environ,{"GITHUB_TOKEN":"fake-ci-token"}),              patch.object(self.gate,"_github_event",return_value=(REPO,299,SHA)),              patch.object(self.gate,"_api",side_effect=fake_api),              self.assertRaises(ExternalReviewError):
            self.gate.evaluate_live_gate(self.packet,self.ledger)

    def test_pr_head_race_during_api_reads_fails_closed(self):
        attempts = 0
        def fake_api(path, token):
            nonlocal attempts
            if path.endswith("/pulls/299"):
                attempts += 1
                return pr_data() if attempts == 1 else pr_data(sha="b" * 40)
            if "/reviews?" in path:
                return [review(self.packet)]
            if "/permission" in path:
                return {"permission": "write"}
            raise AssertionError(path)
        with patch.dict(os.environ, {"GITHUB_TOKEN": "fake-ci-token"}), \
             patch.object(self.gate, "_github_event", return_value=(REPO,299,SHA)), \
             patch.object(self.gate, "_api", side_effect=fake_api), \
             self.assertRaises(ExternalReviewError):
            self.gate.evaluate_live_gate(self.packet,self.ledger)
        self.assertEqual(attempts, 2)

    def test_review_revoked_during_permissions_check_is_rejected(self):
        call_count = 0
        def fake_api(path,token):
            nonlocal call_count
            if path.endswith("/pulls/299"):
                return pr_data()
            if "/reviews?" in path:
                call_count += 1
                if call_count == 1:
                    return [review(self.packet)]
                return [review(self.packet,state="DISMISSED")]
            if "/permission" in path:
                return {"permission":"write"}
            raise AssertionError(path)
        with patch.dict(os.environ,{"GITHUB_TOKEN":"fake-ci-token"}), \
             patch.object(self.gate,"_github_event",return_value=(REPO,299,SHA)), \
             patch.object(self.gate,"_api",side_effect=fake_api), \
             self.assertRaises(ExternalReviewError):
            self.gate.evaluate_live_gate(self.packet,self.ledger)
        self.assertEqual(call_count,2)

    def test_review_api_pagination_fails_closed_when_truncated(self):
        page=[review(self.packet,review_id=i+1) for i in range(100)]
        def fake_api(path,token):
            if path.endswith("/pulls/299"):return pr_data()
            if "/reviews?" in path:return page
            raise AssertionError("a 500-review page bound must fail before permissions")
        with patch.dict(os.environ,{"GITHUB_TOKEN":"fake-ci-token"}),              patch.object(self.gate,"_github_event",return_value=(REPO,299,SHA)),              patch.object(self.gate,"_api",side_effect=fake_api),              self.assertRaises(ExternalReviewError):
            self.gate.evaluate_live_gate(self.packet,self.ledger)


if __name__=="__main__":
    unittest.main()
