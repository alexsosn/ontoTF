"""I-033E4 RED: candidate review handoff cannot manufacture approval.

Use the real ten-source BHSA/Syriac native-only cohort and strict live
review body parser. The test fixture's mock review is NOT authority.
"""
from __future__ import annotations

import copy
import json
import unittest

from tests.i033e.test_overlay_handoff import cohort
from tfont.external_review_gate import parse_structured_review, ExternalReviewError
from tfont.reviewer_handoff import (
    ReviewerHandoffError,
    reviewer_template,
    review_dossier,
    render_review_body,
)


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


if __name__ == "__main__":
    unittest.main()
