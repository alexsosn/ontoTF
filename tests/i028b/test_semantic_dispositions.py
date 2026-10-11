"""I-028B: 27 lexical dispositions are source-pinned, semantic, and NOT releases."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs/research/data/i028b/bhsa-syriac-ontology-dispositions.json"
QUEUE = ROOT / "docs/research/data/generated/i026/p004-work-queue.json"
SOURCES = ROOT / "docs/research/data/i028a/bhsa-syriac-lexical-depth.json"
BHSA = ROOT / "src/tfont/resources/coverage/p004-r011-baseline-v1/bhsa.json"
SYRIAC = ROOT / "src/tfont/resources/coverage/p004-r011-baseline-v1/syriac.json"
ONTOLEX = "http://www.w3.org/ns/lemon/ontolex#LexicalEntry"
ROW_KEYS = {"corpus_id", "item_id", "assessment", "target", "target_kind", "rationale"}
ROOT_KEYS = {"schema_version", "batch_id", "authority", "source_ledger", "source_registry",
             "ontology_evidence", "rows"}


def verify_proposals(data: dict, queue: dict, source: dict) -> None:
    """Independently reject source drift and overclaimed ontology identity."""
    if set(data) != ROOT_KEYS or data["schema_version"] != 1:
        raise ValueError("closed candidate schema required")
    if data["authority"] != "unreviewed-semantic-proposals":
        raise ValueError("unapproved research-only authority required")
    if data["batch_id"] != "i028b-bhsa-syriac-lexical-dispositions":
        raise ValueError("wrong batch")
    if data["source_ledger"] != "docs/research/data/i028a/bhsa-syriac-lexical-depth.json":
        raise ValueError("wrong source ledger")
    if data["source_registry"] != source["source_registry"]:
        raise ValueError("pinned source provenance mismatch")
    if data["ontology_evidence"] != {
        "model": "ontolex-core",
        "final_report": "https://www.w3.org/2016/05/ontolex/",
        "report_date": "2016-05-10",
        "snapshot_lock": None,
        "candidate_class": ONTOLEX,
    }:
        raise ValueError("unsupported or falsely installed ontology authority")
    allowed = {(row["corpus_id"], row["item_id"]) for row in queue["semantic_rows"]
               if row["workstream"] == "D" and row["corpus_id"] in ("bhsa", "syriac")}
    source_rows = {(row["corpus_id"], row["item_id"]) for row in source["rows"]}
    if allowed != source_rows or len(allowed) != 27:
        raise ValueError("research denominator drift")
    rows = data["rows"]
    if not isinstance(rows, list) or len(rows) != 27:
        raise ValueError("expected 27 proposed decisions")
    ids = [(row["corpus_id"], row["item_id"]) for row in rows]
    if len(set(ids)) != 27 or set(ids) != allowed:
        raise ValueError("duplicate, phantom or missing source item")
    if sum(row["corpus_id"] == "bhsa" for row in rows) != 22:
        raise ValueError("BHSA source count drift")
    for row in rows:
        if set(row) != ROW_KEYS:
            raise ValueError("unknown semantic decision field")
        if not isinstance(row["rationale"], str) or len(row["rationale"].strip()) < 65:
            raise ValueError("per-source semantic rationale required")
        entry_node = row["corpus_id"] == "bhsa" and row["item_id"] == "node_type:lex"
        if entry_node:
            if row["assessment"] != "exact" or row["target"] != ONTOLEX or row["target_kind"] != "class":
                raise ValueError("lex node must be the only lexical-entry target proposal")
        elif (row["assessment"], row["target"], row["target_kind"]) != ("native-only", None, None):
            raise ValueError("unproved property/Form/Sense/Concept or Syriac entry promotion")
    if sum(row["assessment"] == "exact" for row in rows) != 1:
        raise ValueError("fake shared coverage")


class LexicalDispositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        cls.source = json.loads(SOURCES.read_text(encoding="utf-8"))
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_source_bound_complete_semantic_decisions(self):
        verify_proposals(self.data, self.queue, self.source)

    def test_historical_syrian_close_is_not_a_reviewed_lexical_entry(self):
        for corpus, path, item, assessment in (
            ("bhsa", BHSA, "node_type:lex", "exact"),
            ("syriac", SYRIAC, "node_feature:lex", "close"),
        ):
            with self.subTest(corpus=corpus):
                baseline = json.loads(path.read_text(encoding="utf-8"))
                old = next(x for x in baseline["semantic_items"] if x["item_id"] == item)
                self.assertIsNone(old["accounting"]["production"])
                self.assertEqual(old["accounting"]["research"]["assessments"], [assessment])
        self.assertEqual(
            next(x for x in self.data["rows"]
                 if x["corpus_id"] == "syriac" and x["item_id"] == "node_feature:lex")["assessment"],
            "native-only",
        )

    def test_no_authored_review_or_publication_authority(self):
        serialized = json.dumps(self.data)
        for forbidden in ('"review"', '"release_authorized"', '"coverage_manifest"',
                          '"mapping_semantic_digest"', '"reviewed_by"'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)

    def test_adversarial_negative_semantic_mutations(self):
        for mode in ("drop", "duplicate", "new-feature", "gloss-as-sense", "syriac-entry",
                     "label-as-form", "forged-source", "bogus-ontology-lock", "approval-injection"):
            with self.subTest(mode=mode):
                altered = copy.deepcopy(self.data)
                rows = altered["rows"]
                if mode == "drop":
                    rows.pop()
                elif mode == "duplicate":
                    rows[-1] = copy.deepcopy(rows[0])
                elif mode == "new-feature":
                    rows[-1]["item_id"] = "node_feature:invented"
                elif mode == "gloss-as-sense":
                    row = next(r for r in rows if r["item_id"] == "node_feature:gloss")
                    row.update(assessment="exact", target="http://www.w3.org/ns/lemon/ontolex#LexicalSense", target_kind="class")
                elif mode == "syriac-entry":
                    row = next(r for r in rows if r["corpus_id"] == "syriac" and r["item_id"] == "node_feature:lex")
                    row.update(assessment="exact", target=ONTOLEX, target_kind="class")
                elif mode == "label-as-form":
                    row = next(r for r in rows if r["corpus_id"] == "bhsa" and r["item_id"] == "node_feature:lex0")
                    row.update(assessment="exact", target="http://www.w3.org/ns/lemon/ontolex#Form", target_kind="class")
                elif mode == "forged-source":
                    altered["source_registry"]["syriac"]["revision"] = "0" * 40
                elif mode == "bogus-ontology-lock":
                    altered["ontology_evidence"]["snapshot_lock"] = "author-self-approved"
                else:
                    altered["release_authorized"] = True
                with self.assertRaises(ValueError):
                    verify_proposals(altered, self.queue, self.source)


if __name__ == "__main__":
    unittest.main()
