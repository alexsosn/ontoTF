"""I-033E3 TDD: protected review job fetches DATA only from an exact PR head."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tfont.batch_proposals import load_ledger
from tfont.review_packets import build_review_packet
from tfont.external_review_gate import ExternalReviewError
from tests.i033e.test_live_review_gate_adversarial import cli
from tests.i033e.test_external_review_red import REPO, SHA, pr_data

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT / ".github/workflows/i033e3-protected-batch-review.yml"
MANIFEST="docs/research/data/batch_review/inputs.json"
LEDGER="src/tfont/resources/batch_pilots/i033c-adj-adv-proposals.json"
PACKET="docs/research/data/generated/i033d/adj-adv-review-request.json"


def blob(raw: bytes, path: str):
    digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    return {"type":"file","path":path,"size":len(raw),"encoding":"base64",
            "content":base64.b64encode(raw).decode("ascii"),"sha":digest}


class ProtectedBatchGateRED(unittest.TestCase):
    def setUp(self):
        self.gate=cli()
        self.ledger=load_ledger()
        self.packet=build_review_packet(self.ledger)
        self.manifest={"schema_version":1,"ledger":LEDGER,"packet":PACKET}
        self.records={
            MANIFEST:blob(json.dumps(self.manifest).encode(),MANIFEST),
            LEDGER:blob(json.dumps(self.ledger).encode(),LEDGER),
            PACKET:blob(json.dumps(self.packet).encode(),PACKET),
        }

    def load(self,*, records=None, head=SHA):
        routes=[]
        def fake_api(path, token):
            routes.append(path)
            self.assertEqual(token,"test-read-token")
            if path.endswith("/pulls/299"):
                return pr_data(sha=head)
            if "/contents/" in path:
                item=path.split("/contents/",1)[1]
                name,ref=item.split("?ref=",1)
                self.assertEqual(ref,SHA)
                from urllib.parse import unquote
                return (records or self.records)[unquote(name)]
            raise AssertionError("unapproved API route: "+path)
        with patch.dict(os.environ,{"GITHUB_TOKEN":"test-read-token"}), \
             patch.object(self.gate,"_github_event",return_value=(REPO,299,SHA)), \
             patch.object(self.gate,"_api",side_effect=fake_api):
            answer=self.gate.fetch_pr_head_inputs()
        return answer,routes

    def test_authenticated_github_api_rejects_redirects_without_token_forwarding(self):
        from urllib.request import Request
        handler=self.gate._NoRedirect()
        request=Request(
            "https://api.github.com/repos/alexsosn/ontoTF/pulls/299",
            headers={"Authorization":"Bearer sensitive-token"}
        )
        self.assertIsNone(handler.redirect_request(
            request,None,302,"Found",
            {"Location":"https://untrusted.example/collect"},
            "https://untrusted.example/collect",
        ))

    def test_only_exact_head_proposal_and_packet_data_are_fetched(self):
        (packet,ledger),routes=self.load()
        self.assertEqual(packet,self.packet)
        self.assertEqual(ledger,self.ledger)
        self.assertEqual(sum("/contents/" in route for route in routes),3)
        self.assertTrue(all("?ref="+SHA in route for route in routes if "/contents/" in route))

    def test_reject_out_of_scope_manifest_paths_and_duplicate_fields(self):
        for changed in (
            {"packet":"../../.github/workflows/backdoor.yml"},
            {"ledger":"src/tfont/resources/batch_pilots/../tools.py"},
            {"packet":"https://evil.com/review.json"},
            {"ledger":"src/tfont/resources/batch_pilots/other.py"},
            {"ledger":"src/tfont/resources/batch_pilots/nested\ninvalid.json"},
            {"packet":"docs/research/data/generated/i033d/%2e%2e/approval.json"},
        ):
            payload=dict(self.manifest,**changed)
            fake=dict(self.records,**{MANIFEST:blob(json.dumps(payload).encode(),MANIFEST)})
            with self.subTest(changed=changed),self.assertRaises(ExternalReviewError):
                self.load(records=fake)
        raw=b'{"schema_version":1,"ledger":"'+LEDGER.encode()+b'","ledger":"'+LEDGER.encode()+b'","packet":"'+PACKET.encode()+b'"}'
        fake=dict(self.records,**{MANIFEST:blob(raw,MANIFEST)})
        with self.assertRaises(ExternalReviewError):
            self.load(records=fake)

    def test_github_blob_identity_encoding_size_and_head_drift_fail_closed(self):
        for defect in ("sha","encoding","size","content","path"):
            record=dict(self.records[LEDGER])
            if defect=="sha":record["sha"]="f"*40
            elif defect=="encoding":record["encoding"]="utf-8"
            elif defect=="size":record["size"]+=1
            elif defect=="content":record["content"]="!!!invalid-base64!!!"
            else:record["path"]="some/other/file.json"
            fake=dict(self.records,**{LEDGER:record})
            with self.subTest(defect=defect),self.assertRaises(ExternalReviewError):
                self.load(records=fake)
        with self.assertRaises(ExternalReviewError):
            self.load(head="b"*40)

    def test_stale_packet_or_ledger_cannot_pass_source_integrity(self):
        proposal=dict(self.ledger)
        proposal["batch_id"]="forged"
        fake=dict(self.records,**{LEDGER:blob(json.dumps(proposal).encode(),LEDGER)})
        with self.assertRaises(ExternalReviewError):
            self.load(records=fake)

    def test_second_review_trigger_must_use_protected_context(self):
        event={"number":299,"pull_request":{"number":299,"head":{"sha":SHA}}}
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/"event.json"
            source.write_text(json.dumps(event),encoding="utf-8")
            for event_name in ("pull_request_target",):
                with self.subTest(event=event_name),patch.dict(os.environ,{
                    "GITHUB_EVENT_NAME":event_name,
                    "GITHUB_REPOSITORY":REPO,
                    "GITHUB_EVENT_PATH":str(source),
                    "GITHUB_TOKEN":"test-read-token",
                },clear=True):
                    self.assertEqual(self.gate._github_event(),(REPO,299,SHA))
            for rejected in ("pull_request", "pull_request_review"):
                with patch.dict(os.environ,{
                    "GITHUB_EVENT_NAME":rejected,
                "GITHUB_REPOSITORY":REPO,
                "GITHUB_EVENT_PATH":str(source),
                "GITHUB_TOKEN":"test-read-token",
                },clear=True),self.assertRaises(ExternalReviewError):
                    self.gate._github_event()

    def test_trusted_workflow_never_checks_out_or_executes_candidate_code(self):
        self.assertTrue(WORKFLOW.exists())
        source=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request_target:",source)
        self.assertNotIn("\n  pull_request_review:",source)
        self.assertIn("ontology-batch-review",source)
        self.assertIn("ref: main",source)
        self.assertIn("check_external_review.py --from-pr-head",source)
        self.assertNotIn("github.event.pull_request.head.sha",source)
        self.assertNotIn("pull-requests: write",source)
        self.assertNotIn("contents: write",source)


if __name__=="__main__":
    unittest.main()
