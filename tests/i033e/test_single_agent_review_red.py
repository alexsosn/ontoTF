"""I-033E5 RED: same-account review needs two independent *passes*, not an invented person."""
from __future__ import annotations

import copy
import json
import unittest

from tests.i033e.test_overlay_handoff import cohort
from tests.i033e.test_external_review_red import (
    REPO, SHA, body_for, pr_data, review,
)
from tfont.external_review_gate import ExternalReviewError, evaluate_review_snapshot
from tfont.single_agent_review import (
    evaluate_single_agent_snapshot, parse_adversarial_report,
)

AUTHOR = "proposal-author"
LABEL = "ontology-single-agent-review"


def candidate_pr():
    result = pr_data(author=AUTHOR)
    result["base"]["ref"] = "main"
    result["labels"] = [{"name": LABEL}, {"name": "ontology-batch-review"}]
    return result


def adversarial_body(packet):
    return "ontoTF-adversarial-review-v1\n" + json.dumps({
        "packet_digest": packet["batch_digest"],
        "summary": "Independently challenge each native-only category against the pinned primary source, the limited reviewed OLiA lock and the distinction between a native feature definition and a validated ontology class target.",
        "rows": [{
            "mapping_id": row["mapping_id"],
            "decision_digest": row["decision_digest"],
            "challenge": f"Reassess {row['native_binding']['value']} independently: the native part-of-speech definition may not justify treating it as unmatched by any ontology; demand precise target evidence.",
            "source_check": f"Primary original source check: pinned revision {row['source_pin']['source_revision']} identifies {row['native_binding']['value']} in the documented word.sp domain; compare the ontology lock before adjudication.",
        } for row in packet["rows"]],
    }, ensure_ascii=False)


def author_event(packet, *, n=900, kind="adversarial", state="COMMENTED",
                 sha=SHA, at="2026-10-11T11:00:00Z", author=AUTHOR):
    event = review(packet, user=author, state=state, commit=sha,
                   submitted=at, review_id=n,
                   body=adversarial_body(packet) if kind=="adversarial"
                   else body_for(packet, first="accept"))
    return event


class SingleAgentReviewRED(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger, cls.source_reader, cls.packet, _mock = cohort()

    def evaluate(self, reviews, *, pr=None, permissions=None):
        return evaluate_single_agent_snapshot(
            packet=self.packet, repository=REPO, pr_number=299,
            expected_head_sha=SHA, pull_request=pr or candidate_pr(),
            reviews=reviews,
            reviewer_permissions=permissions or {AUTHOR: "admin"},
        )

    def pair(self):
        return [
            author_event(self.packet, n=900),
            author_event(self.packet, n=901, kind="decision",
                         at="2026-10-11T12:00:00Z"),
        ]

    def test_two_separate_commit_bound_events_authorize_only_single_agent_provenance(self):
        report=self.evaluate(self.pair())
        self.assertEqual(report["counts"], {"accept": 1, "reject": 0, "needs-evidence": 9})
        self.assertEqual(report["approved_head_sha"], SHA)
        self.assertEqual(report["reviewer_login"], AUTHOR)
        self.assertEqual(report["review_id"], 901)
        self.assertIn("single-agent", report["provenance"])
        self.assertNotIn("independent-person", report["provenance"])
        self.assertNotIn("release_authorized", report)
        self.assertEqual(len(report["rows"]), 10)

    def test_external_review_mode_still_rejects_author_comments(self):
        with self.assertRaises(ExternalReviewError):
            evaluate_review_snapshot(
                packet=self.packet, repository=REPO, pr_number=299,
                expected_head_sha=SHA, pull_request=candidate_pr(),
                reviews=self.pair(), reviewer_permissions={AUTHOR: "admin"},
            )

    def test_author_decision_alone_or_adversarial_alone_cannot_authorize(self):
        for events in ([self.pair()[0]], [self.pair()[1]], []):
            with self.subTest(size=len(events)), self.assertRaises(ExternalReviewError):
                self.evaluate(events)

    def test_two_events_require_sequence_unique_ids_and_same_current_sha(self):
        a,b=self.pair()
        cases = [
            [a,dict(b,id=a["id"])],
            [dict(a,commit_id="b"*40),b],
            [a,dict(b,commit_id="b"*40)],
            [a,dict(b,submitted_at=a["submitted_at"],id=899)],
            [a,dict(b,user={"login":"external-reviewer","type":"User"})],
            [a,dict(b,state="APPROVED")],
            [dict(a,state="APPROVED"),b],
            [a,b,dict(b,id=902,body="An unrelated later COMMENT",
                      submitted_at="2026-10-11T13:00:00Z")],
            [a,b,dict(b,id=903,state="DISMISSED",
                      submitted_at="2026-10-11T13:01:00Z")],
        ]
        for idx,events in enumerate(cases):
            with self.subTest(idx=idx), self.assertRaises(ExternalReviewError):
                self.evaluate(events)

    def test_explicit_live_opt_in_and_permission_are_required(self):
        for label in ([], [{"name":"ontology-batch-review"}]):
            with self.subTest(labels=label), self.assertRaises(ExternalReviewError):
                self.evaluate(self.pair(),pr=dict(candidate_pr(), labels=label))
        for role in ("read", "triage", "unknown"):
            with self.subTest(role=role), self.assertRaises(ExternalReviewError):
                self.evaluate(self.pair(), permissions={AUTHOR: role})
        with self.assertRaises(ExternalReviewError):
            self.evaluate(self.pair(), permissions={"OTHER": "admin"})
        with self.assertRaises(ExternalReviewError):
            self.evaluate(self.pair(),pr=pr_data(author=AUTHOR))

    def test_different_github_account_and_forged_fields_are_rejected(self):
        a,b=self.pair()
        for change in (
            {"user":{"login":"other","type":"User"}},
            {"user":{"login":AUTHOR,"type":"Bot"}},
            {"commit_id":"c"*40},
            {"state":"CHANGES_REQUESTED"},
        ):
            with self.subTest(change=change), self.assertRaises(ExternalReviewError):
                self.evaluate([dict(a,**change),b])

    def test_strict_adversarial_report_rejects_empty_copied_or_missing_row_evidence(self):
        a,b=self.pair()
        source=json.loads(a["body"].split("\n",1)[1])
        variants=[]
        x=copy.deepcopy(source);x["rows"].pop();variants.append(x)
        x=copy.deepcopy(source);x["rows"].append(copy.deepcopy(x["rows"][0]));variants.append(x)
        x=copy.deepcopy(source);x["rows"][0]["challenge"]="ok";variants.append(x)
        x=copy.deepcopy(source);x["rows"][0]["source_check"]="source";variants.append(x)
        x=copy.deepcopy(source);x["rows"][0]["challenge"]=self.packet["rows"][0]["rationale"];variants.append(x)
        x=copy.deepcopy(source);x["rows"][0]["decision_digest"]="sha256:"+"e"*64;variants.append(x)
        x=copy.deepcopy(source);x["rows"][0]["mapping_id"]="mapping:forged";variants.append(x)
        x=copy.deepcopy(source);x["packet_digest"]="sha256:"+"e"*64;variants.append(x)
        x=copy.deepcopy(source);x["summary"]="";variants.append(x)
        x=copy.deepcopy(source);x["reviewer_login"]="independent";variants.append(x)
        x=copy.deepcopy(source);x["rows"][0]["accepted"]=True;variants.append(x)
        for idx,v in enumerate(variants):
            with self.subTest(idx=idx), self.assertRaises(ExternalReviewError):
                self.evaluate([dict(a,body="ontoTF-adversarial-review-v1\n"+json.dumps(v)),b])
        for body in ('ontoTF-adversarial-review-v1\n{"x":1,"x":2}',
                     "ontoTF-adversarial-review-v1\nNaN",
                     "ontoTF-adversarial-review-v1\n[]"):
            with self.assertRaises(ExternalReviewError):
                parse_adversarial_report(body,self.packet)

    def test_protected_live_api_fetches_two_author_reviews_and_current_permission(self):
        from unittest.mock import patch
        import os
        from tests.i033e.test_live_review_gate_adversarial import cli
        module=cli()
        calls=[]
        def remote(path,token):
            calls.append(path)
            self.assertEqual(token,"protected-live-test-token")
            if path.endswith("/pulls/299"):
                return candidate_pr()
            if "/pulls/299/reviews?" in path:
                return self.pair()
            if path.endswith("/collaborators/proposal-author/permission"):
                return {"permission":"admin"}
            raise AssertionError("unexpected API request: "+path)
        with patch.dict(os.environ,{"GITHUB_TOKEN":"protected-live-test-token"}), \
             patch.object(module,"_github_event",return_value=(REPO,299,SHA)), \
             patch.object(module,"_api",side_effect=remote):
            report=module.evaluate_live_gate(self.packet,self.ledger,
                                              resource_loader=self.source_reader)
        self.assertIn("single-agent",report["provenance"])
        self.assertEqual(sum("/pulls/299/reviews?" in url for url in calls),2)
        self.assertEqual(sum(url.endswith("/pulls/299") for url in calls),2)
        self.assertEqual(sum("/collaborators/proposal-author/permission" in url for url in calls),1)

    def test_protected_live_gate_does_not_fallback_from_single_agent_to_external(self):
        from unittest.mock import patch
        import os
        from tests.i033e.test_live_review_gate_adversarial import cli
        module=cli()
        def remote(path,token):
            if path.endswith("/pulls/299"):return candidate_pr()
            if "/reviews?" in path:return [self.pair()[1]]
            if "/collaborators/" in path:return {"permission":"admin"}
            raise AssertionError(path)
        with patch.dict(os.environ,{"GITHUB_TOKEN":"protected-live-test-token"}), \
             patch.object(module,"_github_event",return_value=(REPO,299,SHA)), \
             patch.object(module,"_api",side_effect=remote), \
             self.assertRaises(ExternalReviewError):
            module.evaluate_live_gate(self.packet,self.ledger,
                                      resource_loader=self.source_reader)

    def test_unset_adversarial_worksheet_and_explicit_body_renderer(self):
        from tfont.single_agent_review import adversarial_template, render_adversarial_body
        sheet = adversarial_template(self.packet)
        self.assertIsNone(sheet["summary"])
        self.assertEqual(len(sheet["rows"]), 10)
        self.assertTrue(all(row["challenge"] is None and row["source_check"] is None
                            for row in sheet["rows"]))
        with self.assertRaises(ExternalReviewError):
            render_adversarial_body(self.packet, sheet)
        submitted = json.loads(adversarial_body(self.packet).split("\n",1)[1])
        formatted = render_adversarial_body(self.packet, submitted)
        self.assertEqual(parse_adversarial_report(formatted,self.packet),submitted)

    def test_live_policy_label_change_invalidates_the_snapshot(self):
        from unittest.mock import patch
        import os
        from tests.i033e.test_live_review_gate_adversarial import cli
        module = cli()
        reads = 0
        def remote(path, token):
            nonlocal reads
            if path.endswith("/pulls/299"):
                reads += 1
                pr = candidate_pr()
                if reads == 2:
                    pr["labels"].append({"name": "ontology-batch-publish"})
                return pr
            if "/reviews?" in path:
                return self.pair()
            if "/collaborators/" in path:
                return {"permission": "admin"}
            raise AssertionError(path)
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}), \
             patch.object(module, "_github_event", return_value=(REPO,299,SHA)), \
             patch.object(module, "_api", side_effect=remote), \
             self.assertRaises(ExternalReviewError):
            module.evaluate_live_gate(self.packet, self.ledger,
                                      resource_loader=self.source_reader)

    def test_changed_challenge_changes_the_observation_binding(self):
        events = self.pair()
        before = self.evaluate(events)
        changed = copy.deepcopy(events)
        report = json.loads(changed[0]["body"].split("\n", 1)[1])
        report["rows"][0]["challenge"] += " Further source scrutiny is still required."
        changed[0]["body"] = "ontoTF-adversarial-review-v1\n" + json.dumps(report)
        self.assertNotEqual(before, self.evaluate(changed))

    def test_publication_label_withdrawn_between_complete_checks_prevents_output(self):
        from unittest.mock import patch
        from tests.i033e.test_live_review_gate_adversarial import cli
        import os
        import tempfile
        import io
        from pathlib import Path
        module = cli()
        reads = 0
        events = self.pair()
        decisions = json.loads(events[1]["body"].split("\n", 1)[1])
        for row in decisions["rows"]:
            row["disposition"] = "accept"
        events[1]["body"] = "ontoTF-batch-review-v1\n" + json.dumps(decisions)
        def remote(path, token):
            nonlocal reads
            if path.endswith("/pulls/299"):
                reads += 1
                pr = candidate_pr()
                if reads <= 2:
                    pr["labels"].append({"name": "ontology-batch-publish"})
                return pr
            if "/reviews?" in path:
                return events
            if "/collaborators/" in path:
                return {"permission": "admin"}
            raise AssertionError(path)
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}), \
             patch.object(module, "_github_event", return_value=(REPO,299,SHA)), \
             patch.object(module, "_api", side_effect=remote), \
             patch.object(module, "fetch_pr_head_context", return_value=(self.packet,self.ledger,self.source_reader)), \
             patch("sys.argv", ["gate", "--from-pr-head", "--publish-handoff"]), \
             patch("sys.stdout", new=io.StringIO()), patch("sys.stderr", new=io.StringIO()):
            previous = os.getcwd()
            try:
                os.chdir(directory)
                self.assertEqual(module.main(), 1)
                self.assertFalse(Path("batch-review-pack.json").exists())
            finally:
                os.chdir(previous)

    def test_existing_cli_can_build_two_review_bodies_without_issuing_approval(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import contextlib
        import io
        import sys
        from scripts.mappings import prepare_external_review as cli
        packet = self.packet
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"challenges.json"
            challenge = json.loads(adversarial_body(packet).split("\n",1)[1])
            path.write_text(json.dumps(challenge),encoding="utf-8")
            for args in (["--challenge-template"],["--review-challenges",str(path)]):
                with patch.object(cli,"load_review_context",
                                  return_value=(packet,self.source_reader)), \
                     patch.object(sys,"argv",["trusted-review",*args]), \
                     contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(cli.main(),0)
                if args[0]=="--challenge-template":
                    self.assertIsNone(json.loads(output.getvalue())["summary"])
                else:
                    self.assertEqual(parse_adversarial_report(output.getvalue().rstrip(),packet),
                                     challenge)

    def test_current_pr_must_have_exact_head_base_repo_state(self):
        for broken in (
            {"state":"closed"}, {"draft":True},
            {"number":300}, {"head":{"sha":"c"*40,"repo":{"full_name":REPO}}},
            {"base":{"ref":"other","repo":{"full_name":REPO}}},
            {"base":{"ref":"main","repo":{"full_name":"other/repo"}}},
        ):
            with self.subTest(change=broken), self.assertRaises(ExternalReviewError):
                self.evaluate(self.pair(),pr=dict(candidate_pr(),**broken))


if __name__ == "__main__":
    unittest.main()
