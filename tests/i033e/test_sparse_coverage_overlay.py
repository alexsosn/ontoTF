"""I-033G RED: source-bound, sparse, UNSEALED production coverage previews.

The review observation in these tests is a mock. It is not GitHub authority.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.i033e.test_overlay_handoff import assemble, cohort
from tfont.candidate_evidence import CandidateEvidenceResources
from tfont.coverage import (
    coverage_report, load_packaged_coverage_manifest, validate_coverage_manifest,
)
from tfont.coverage_overlay import (
    CoverageOverlayError, apply_sparse_coverage_delta, build_sparse_coverage_delta,
)
from tfont.digests import canonical_json_bytes
from tfont.overlay_handoff import build_overlay_handoff
from tfont.review_packets import verify_review_packet


ROOT = Path(__file__).resolve().parents[2]


class SparseCoverageOverlayTDD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger, cls.reader, cls.packet, cls.mock_review = cohort()
        cls.pack = assemble(cls.ledger, cls.reader, cls.packet, cls.mock_review)

    @staticmethod
    def mixed_pack(keep):
        ledger, reader, packet, review = cohort()
        for index, row in enumerate(review["rows"]):
            row["disposition"] = (
                "accept" if index < keep else
                "reject" if index % 2 else "needs-evidence"
            )
        review["counts"] = {
            kind: sum(r["disposition"] == kind for r in review["rows"])
            for kind in ("accept", "reject", "needs-evidence")
        }
        return assemble(ledger, reader, packet, review)

    def test_ten_actual_source_values_produce_ten_sparse_assignments(self):
        delta = build_sparse_coverage_delta(self.pack)
        self.assertEqual(delta["authority"], "unsealed-coverage-preview-only")
        self.assertEqual(delta["pack_digest"], self.pack["content_digest"])
        self.assertEqual(len(delta["corpora"]), 2)
        self.assertEqual(sum(len(c["assignments"]) for c in delta["corpora"]), 10)
        self.assertEqual(delta, build_sparse_coverage_delta(self.pack))
        self.assertNotIn("release_authorized", delta)
        self.assertNotIn("semantic_items", json.dumps(delta))
        self.assertLess(len(json.dumps(delta)), 10000)
        for corpus in delta["corpora"]:
            self.assertEqual(set(corpus), {"corpus_id", "coverage_base", "assignments"})
            for row in corpus["assignments"]:
                self.assertEqual(
                    set(row), {"item_id", "mapping_id", "decision_digest", "production"}
                )
                self.assertEqual(row["production"], {
                    "assessments": ["native-only"],
                    "common_target": False,
                    "source_ids": [row["mapping_id"]],
                    "profiles": ["linguistic"],
                    "capabilities": ["linguistic.part-of-speech"],
                })

    def test_in_memory_delta_updates_only_ten_null_production_cells(self):
        original = {
            corpus: load_packaged_coverage_manifest(
                f"p004-i027c2-{corpus}-adj-adv-v1", corpus
            )
            for corpus in ("bhsa", "syriac")
        }
        frozen = {corpus: canonical_json_bytes(manifest)
                  for corpus, manifest in original.items()}
        delta = build_sparse_coverage_delta(self.pack)
        preview = apply_sparse_coverage_delta(self.pack, delta)
        self.assertEqual(set(preview), {"bhsa", "syriac"})
        self.assertEqual(preview, apply_sparse_coverage_delta(self.pack, delta))
        for corpus, changed in preview.items():
            before = original[corpus]
            validate_coverage_manifest(changed)
            self.assertEqual(before["denominator_digest"], changed["denominator_digest"])
            self.assertEqual(before["technical_exclusions"], changed["technical_exclusions"])
            self.assertEqual(before["accounting_gaps"], changed["accounting_gaps"])
            self.assertEqual(
                [(x["item_id"], x["accounting"]["research"]) for x in before["semantic_items"]],
                [(x["item_id"], x["accounting"]["research"]) for x in changed["semantic_items"]],
            )
            previous = {x["item_id"]:x for x in before["semantic_items"]}
            current = {x["item_id"]:x for x in changed["semantic_items"]}
            additions = [id for id in current if previous[id]["accounting"]["production"]
                         != current[id]["accounting"]["production"]]
            self.assertEqual(len(additions), 9 if corpus == "bhsa" else 1)
            self.assertTrue(all(previous[id]["accounting"]["production"] is None
                                and current[id]["accounting"]["production"]["common_target"] is False
                                for id in additions))
            old_report, new_report = coverage_report(before), coverage_report(changed)
            self.assertEqual(new_report.production_reviewed_items,
                             old_report.production_reviewed_items + len(additions))
            self.assertEqual(new_report.production_common_target_items,
                             old_report.production_common_target_items)
            self.assertEqual(frozen[corpus], canonical_json_bytes(
                load_packaged_coverage_manifest(f"p004-i027c2-{corpus}-adj-adv-v1", corpus)
            ))

    def test_nine_and_one_accept_do_not_require_ten_accepts(self):
        for keep in (9,1):
            with self.subTest(keep=keep):
                pack = self.mixed_pack(keep)
                delta = build_sparse_coverage_delta(pack)
                ids = {r["mapping_id"] for c in pack["corpora"] for r in c["mappings"]}
                self.assertEqual(sum(len(c["assignments"]) for c in delta["corpora"]), keep)
                self.assertEqual(
                    {r["mapping_id"] for c in delta["corpora"] for r in c["assignments"]},
                    ids,
                )
                preview = apply_sparse_coverage_delta(pack, delta)
                self.assertEqual(sum(
                    sum(row["accounting"]["production"] is not None for row in manifest["semantic_items"])
                    - sum(row["accounting"]["production"] is not None for row in
                          load_packaged_coverage_manifest(
                              f"p004-i027c2-{corpus}-adj-adv-v1", corpus
                          )["semantic_items"])
                    for corpus, manifest in preview.items()
                ), keep)

    def test_all_rejected_has_no_positive_pack_to_publish(self):
        with self.assertRaisesRegex(ValueError, "accepted"):
            self.mixed_pack(0)

    def test_forged_mutated_or_stale_delta_rejected_even_if_rehashed(self):
        pack = self.pack
        delta = build_sparse_coverage_delta(pack)
        defects = []
        for mutation in ("digest", "item", "common", "source", "duplicate",
                         "corpus", "extra", "status", "baseline", "omit"):
            x = copy.deepcopy(delta)
            c = x["corpora"][0]
            row = c["assignments"][0]
            if mutation == "digest": x["content_digest"] = "sha256:" + "1"*64
            if mutation == "item": row["item_id"] = "node_value:sp=\"forged\""
            if mutation == "common": row["production"]["common_target"] = True
            if mutation == "source": row["production"]["source_ids"] = ["mapping:unrelated"]
            if mutation == "duplicate": c["assignments"].append(copy.deepcopy(row))
            if mutation == "corpus": c["corpus_id"] = "extrabiblical"
            if mutation == "extra": x["release_authorized"] = True
            if mutation == "status": x["authority"] = "trusted-release"
            if mutation == "baseline": c["coverage_base"]["denominator_digest"] = "sha256:"+"0"*64
            if mutation == "omit": c["assignments"].pop()
            defects.append((mutation, x))
        for name, defect in defects:
            with self.subTest(name=name), self.assertRaises(CoverageOverlayError):
                apply_sparse_coverage_delta(pack, defect)

    def test_changing_installed_baseline_fails_closed(self):
        delta = build_sparse_coverage_delta(self.pack)
        original = load_packaged_coverage_manifest("p004-i027c2-bhsa-adj-adv-v1", "bhsa")
        tampered = copy.deepcopy(original)
        tampered["semantic_items"][0]["accounting"]["production"] = {
            "assessments": ["native-only"], "common_target": False,
            "profiles": ["linguistic"], "capabilities": ["linguistic.part-of-speech"],
            "source_ids": ["forged"],
        }
        def loader(resource, corpus):
            return tampered if corpus == "bhsa" else load_packaged_coverage_manifest(resource, corpus)
        with patch("tfont.coverage_overlay.load_packaged_coverage_manifest", side_effect=loader):
            with self.assertRaises(CoverageOverlayError):
                apply_sparse_coverage_delta(self.pack, delta)

    def test_real_committed_candidate_ledger_packet_and_supplemental_evidence(self):
        from tests.i033e.test_real_ten_source_batch import LEGACY_MANIFEST
        meta = LEGACY_MANIFEST
        ledger = json.loads((ROOT/meta["ledger"]).read_text())
        packet = json.loads((ROOT/meta["packet"]).read_text())
        supplemental = {
            name:json.loads((ROOT/path).read_text())
            for name,path in meta["evidence_resources"].items()
        }
        reader = CandidateEvidenceResources(ledger, supplemental)
        verify_review_packet(packet, ledger, resource_loader=reader)
        mocked = copy.deepcopy(self.mock_review)
        mocked.update(
            packet_id=packet["packet_id"], batch_digest=packet["batch_digest"],
            provenance="UNAUTHENTICATED-TEST-ONLY-NOT-GITHUB",
            rows=[{"mapping_id":row["mapping_id"],"decision_digest":row["decision_digest"],
                   "disposition":"accept"} for row in packet["rows"]],
        )
        staged = build_overlay_handoff(packet, ledger, mocked, resource_loader=reader)
        delta = build_sparse_coverage_delta(staged)
        self.assertEqual(sum(len(c["assignments"]) for c in delta["corpora"]),10)
        preview = apply_sparse_coverage_delta(staged, delta)
        self.assertEqual(preview["bhsa"]["denominator_source_revision"],
                         ledger["source_registry"]["bhsa"]["target_corpus_revision"])
        self.assertEqual(preview["syriac"]["denominator_source_revision"],
                         ledger["source_registry"]["syriac"]["target_corpus_revision"])
        self.assertTrue(all(
            not row["production"]["common_target"]
            for c in delta["corpora"] for row in c["assignments"]
        ))


if __name__ == "__main__":
    unittest.main()
