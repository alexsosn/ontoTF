"""I-033E red: externally attested per-row decisions, not self-authored receipts."""
from __future__ import annotations

import copy
import json
import unittest

from tfont.batch_proposals import load_ledger
from tfont.review_packets import build_review_packet
from tfont.external_review_gate import (
    ExternalReviewError,
    evaluate_review_snapshot,
    parse_structured_review,
)

SHA = "a" * 40
REPO = "alexsosn/ontoTF"
AUTHOR = "proposal-author"
REVIEWER = "independent-reviewer"


def body_for(packet, *, first="accept"):
    rows = [
        {
            "mapping_id": row["mapping_id"],
            "decision_digest": row["decision_digest"],
            "disposition": first if i == 0 else "needs-evidence",
        }
        for i, row in enumerate(packet["rows"])
    ]
    return "ontoTF-batch-review-v1\n" + json.dumps(
        {"packet_digest": packet["batch_digest"], "rows": rows}, sort_keys=True
    )


def pr_data(*, sha=SHA, author=AUTHOR, draft=False):
    return {
        "number": 299,
        "state": "open",
        "draft": draft,
        "head": {"sha": sha, "repo": {"full_name": REPO}},
        "base": {"repo": {"full_name": REPO}},
        "user": {"login": author, "type": "User"},
    }


def review(packet, *, user=REVIEWER, state="APPROVED", commit=SHA,
           submitted="2026-10-10T15:00:00Z", review_id=100, body=None):
    return {
        "id": review_id,
        "state": state,
        "commit_id": commit,
        "submitted_at": submitted,
        "user": {"login": user, "type": "User"},
        "body": body if body is not None else body_for(packet),
    }


class ExternalReviewRed(unittest.TestCase):
    def setUp(self):
        self.packet = build_review_packet(load_ledger())
        self.permissions = {REVIEWER: "write"}

    def evaluate(self, reviews, *, pr=None, permissions=None):
        return evaluate_review_snapshot(
            packet=self.packet,
            repository=REPO,
            pr_number=299,
            expected_head_sha=SHA,
            pull_request=pr if pr is not None else pr_data(),
            reviews=reviews,
            reviewer_permissions=self.permissions if permissions is None else permissions,
        )

    def test_independent_review_adjudicates_rows_not_all_approved(self):
        outcome = self.evaluate([review(self.packet)])
        self.assertEqual(outcome["batch_digest"], self.packet["batch_digest"])
        self.assertEqual(outcome["approved_head_sha"], SHA)
        self.assertEqual(outcome["reviewer_login"], REVIEWER)
        self.assertEqual(outcome["counts"], {
            "accept": 1, "reject": 0, "needs-evidence": 3
        })
        self.assertEqual(
            [row["disposition"] for row in outcome["rows"]],
            ["accept", "needs-evidence", "needs-evidence", "needs-evidence"],
        )
        self.assertNotIn("release_authorized", outcome)

    def test_review_body_parser_rejects_repeats_and_non_json(self):
        with self.assertRaises(ExternalReviewError):
            parse_structured_review(
                'ontoTF-batch-review-v1\n{"packet_digest":"x","packet_digest":"y","rows":[]}'
            )
        for s in ("", "APPROVED", "ontoTF-batch-review-v1\nNaN",
                  "ontoTF-batch-review-v1\n[]"):
            with self.subTest(s=s), self.assertRaises(ExternalReviewError):
                parse_structured_review(s)

    def test_author_and_unprivileged_reviewer_cannot_approve(self):
        for who, roles in [
            (AUTHOR, {AUTHOR:"admin"}),
            (REVIEWER, {REVIEWER:"read"}),
            (REVIEWER, {REVIEWER:"unknown"}),
        ]:
            with self.subTest(user=who,roles=roles), self.assertRaises(ExternalReviewError):
                self.evaluate([review(self.packet,user=who)],permissions=roles)

    def test_case_variant_github_identity_cannot_self_approve(self):
        # GitHub logins are case-insensitive, including for PR authors.
        # A case-variant author must not count as a second reviewer.
        altered = pr_data(author="Proposal-Author")
        with self.assertRaises(ExternalReviewError):
            self.evaluate(
                [review(self.packet, user="proposal-author")],
                pr=altered,
                permissions={"proposal-author": "admin"},
            )

    def test_exact_head_and_pr_repository_binding(self):
        for pr, record in [
            (pr_data(sha="b"*40), review(self.packet)),
            (pr_data(draft=True), review(self.packet)),
            (pr_data(), review(self.packet, commit="c"*40)),
        ]:
            with self.subTest(pr=pr["head"]["sha"],rec=record["commit_id"]), self.assertRaises(ExternalReviewError):
                self.evaluate([record],pr=pr)
        switched=pr_data()
        switched["base"]["repo"]["full_name"]="attacker/ontoTF"
        with self.assertRaises(ExternalReviewError):
            self.evaluate([review(self.packet)],pr=switched)

    def test_stale_approval_revoked_by_later_review_event(self):
        early=review(self.packet)
        for state in ("DISMISSED","COMMENTED","CHANGES_REQUESTED"):
            later=review(self.packet,state=state,review_id=101,
                         submitted="2026-10-10T15:01:00Z")
            with self.subTest(state=state), self.assertRaises(ExternalReviewError):
                self.evaluate([early,later])

    def test_case_variant_reviewer_later_retraction_invalidates_approval(self):
        earlier = review(self.packet,user="independent-reviewer")
        later = review(
            self.packet, user="Independent-Reviewer", state="CHANGES_REQUESTED",
            review_id=101, submitted="2026-10-10T15:01:00Z",
        )
        with self.assertRaises(ExternalReviewError):
            self.evaluate([earlier,later])

    def test_rationale_or_digest_replay_rejected(self):
        changed=copy.deepcopy(self.packet)
        changed["rows"][0]["rationale"]="altered scholarly rationale"
        # Normal runtime gate must validate packet vs source ledger BEFORE this evaluator.
        for field in ("packet_digest","decision_digest","mapping_id"):
            forged=json.loads(body_for(self.packet).split("\n",1)[1])
            if field=="packet_digest":
                forged["packet_digest"]="sha256:"+"0"*64
            elif field=="decision_digest":
                forged["rows"][0]["decision_digest"]="sha256:"+"0"*64
            else:
                forged["rows"][0]["mapping_id"]="mapping:foreign:unreviewed"
            raw="ontoTF-batch-review-v1\n"+json.dumps(forged)
            with self.subTest(field=field), self.assertRaises(ExternalReviewError):
                self.evaluate([review(self.packet,body=raw)])

    def test_no_partial_omitted_or_duplicate_rows(self):
        for modify in ("pop","duplicate","unknown","type"):
            obj=json.loads(body_for(self.packet).split("\n",1)[1])
            if modify=="pop":obj["rows"].pop()
            if modify=="duplicate":obj["rows"].append(copy.deepcopy(obj["rows"][0]))
            if modify=="unknown":obj["rows"][0]["disposition"]="maybe"
            if modify=="type":obj["rows"][0]["disposition"]=True
            with self.subTest(modify=modify), self.assertRaises(ExternalReviewError):
                self.evaluate([review(self.packet,body="ontoTF-batch-review-v1\n"+json.dumps(obj))])

    def test_conflicting_independent_approved_reviews_fail_closed(self):
        rev1=review(self.packet)
        rev2=review(self.packet,user="reviewer-two",review_id=101,
                    body=body_for(self.packet,first="reject"))
        with self.assertRaises(ExternalReviewError):
            self.evaluate([rev1,rev2],permissions={REVIEWER:"write","reviewer-two":"admin"})

    def test_dismissed_and_self_review_do_not_qualify_even_with_valid_body(self):
        with self.assertRaises(ExternalReviewError):
            self.evaluate([review(self.packet,state="DISMISSED")])
        with self.assertRaises(ExternalReviewError):
            self.evaluate([review(self.packet,user=AUTHOR)],permissions={AUTHOR:"admin"})


if __name__ == "__main__":
    unittest.main()
