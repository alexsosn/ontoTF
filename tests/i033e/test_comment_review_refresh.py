"""I-033E3: a comment can request fresh protected review, never grant approval."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tfont.external_review_gate import ExternalReviewError
from tests.i033e.test_external_review_red import REPO, SHA, pr_data
from tests.i033e.test_live_review_gate_adversarial import cli


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/i033e3-protected-batch-review.yml"
COMMAND = "/ontoTF verify-review"


class ProtectedCommentRefreshTests(unittest.TestCase):
    def setUp(self):
        self.gate = cli()
        self.event = {
            "action": "created",
            "issue": {
                "number": 299,
                "pull_request": {
                    "url": f"https://api.github.com/repos/{REPO}/pulls/299"
                },
                "labels": [{"name": "ontology-batch-review"}],
            },
            "comment": {
                "body": COMMAND,
                "author_association": "COLLABORATOR",
                "user": {"login": "independent-reviewer"},
            },
        }
        self.pr = pr_data()
        self.pr["base"]["ref"] = "main"
        self.pr["labels"] = [{"name": "ontology-batch-review"}]

    def load(self, *, event=None, pr=None, event_name="issue_comment",
             ref="refs/heads/main"):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "github-event.json"
            path.write_text(json.dumps(self.event if event is None else event),
                            encoding="utf-8")
            calls = []
            def read_api(route, token):
                calls.append(route)
                self.assertEqual(token, "read-only-test-token")
                self.assertEqual(route, f"/repos/{REPO}/pulls/299")
                return self.pr if pr is None else pr

            with patch.dict(os.environ, {
                "GITHUB_EVENT_NAME": event_name,
                "GITHUB_REPOSITORY": REPO,
                "GITHUB_EVENT_PATH": str(path),
                "GITHUB_REF": ref,
                "GITHUB_TOKEN": "read-only-test-token",
            }, clear=True), patch.object(self.gate, "_api", side_effect=read_api):
                result = self.gate._github_event()
        return result, calls

    def test_authorized_comment_fetches_live_current_head_not_comment_sha(self):
        candidate = dict(self.event)
        candidate["head"] = {"sha": "f" * 40}
        self.assertEqual(self.load(event=candidate),
                         ((REPO, 299, SHA), [f"/repos/{REPO}/pulls/299"]))

    def test_only_a_real_created_pr_comment_is_a_refresh_request(self):
        for mutation in (
            {"action": "edited"},
            {"action": "deleted"},
            {"issue": {"number": 299, "labels": self.event["issue"]["labels"]}},
            {"issue": {**self.event["issue"], "number": True}},
            {"issue": {**self.event["issue"], "number": 0}},
            {"issue": {**self.event["issue"], "pull_request": {}}},
            {"comment": {**self.event["comment"], "body": "APPROVED"}},
            {"comment": {**self.event["comment"], "body": COMMAND + "\n"}},
            {"comment": {**self.event["comment"], "body": COMMAND + "; echo hacked"}},
            {"comment": {**self.event["comment"], "author_association": "CONTRIBUTOR"}},
            {"comment": {**self.event["comment"], "author_association": "NONE"}},
            {"comment": {**self.event["comment"], "user": {}}},
        ):
            event = dict(self.event, **mutation)
            with self.subTest(event=event), self.assertRaises(ExternalReviewError):
                self.load(event=event)

    def test_comment_event_requires_protected_default_branch_and_read_token(self):
        for name, ref in (
            ("issue_comment", "refs/pull/299/merge"),
            ("issue_comment", "refs/heads/untrusted"),
            ("pull_request_review", "refs/heads/main"),
        ):
            with self.subTest(name=name, ref=ref), self.assertRaises(ExternalReviewError):
                self.load(event_name=name, ref=ref)

    def test_current_pr_must_still_be_open_same_repo_base_main_and_labeled(self):
        for bad in (
            {"draft": True},
            {"state": "closed"},
            {"head": {"sha": SHA, "repo": {"full_name": "attacker/fork"}}},
            {"head": {"sha": "not-a-sha", "repo": {"full_name": REPO}}},
            {"base": {"ref": "untrusted", "repo": {"full_name": REPO}}},
            {"base": {"ref": "main", "repo": {"full_name": "someone/fork"}}},
            {"labels": []},
            {"number": 301},
        ):
            with self.subTest(change=bad), self.assertRaises(ExternalReviewError):
                self.load(pr=dict(self.pr, **bad))

    def test_event_metadata_cannot_divert_api_read_to_foreign_pr(self):
        changed = dict(self.event)
        changed["issue"] = dict(self.event["issue"])
        changed["issue"]["pull_request"] = {
            "url": "https://api.github.com/repos/attacker/fork/pulls/299"
        }
        with self.assertRaises(ExternalReviewError):
            self.load(event=changed)

    def test_retired_comment_trigger_cannot_activate_legacy_gate(self):
        self.assertFalse(WORKFLOW.exists())


if __name__ == "__main__":
    unittest.main()
