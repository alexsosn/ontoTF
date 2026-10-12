"""I-034G: fixed-denominator reviewed morphology coverage successors."""
import json
import unittest
from pathlib import Path
from tfont.coverage import coverage_report, coverage_denominator_digest, validate_coverage_manifest
from tfont.release_registry import load_profile

ROOT=Path(__file__).resolve().parents[2]
EXPECTED={"bhsa":(219,75,23,52),"syriac":(74,37,22,15)}

class MorphologyCoverage(unittest.TestCase):
    def test_successors_are_accounted_and_reconciled(self):
        for corpus,(denom,reviewed,shared,native) in EXPECTED.items():
            with self.subTest(corpus=corpus):
                old=json.loads((ROOT/f"src/tfont/resources/coverage/p004-i027c2-{corpus}-adj-adv-v1/{corpus}.json").read_text(encoding="utf-8"))
                new=json.loads((ROOT/f"src/tfont/resources/coverage/p004-i034g-{corpus}-morphology-v1/{corpus}.json").read_text(encoding="utf-8"))
                validate_coverage_manifest(new)
                self.assertEqual(coverage_denominator_digest(old),coverage_denominator_digest(new))
                self.assertEqual(new["denominator_digest"],old["denominator_digest"])
                self.assertEqual(len(new["semantic_items"]),denom)
                report=coverage_report(new)
                self.assertEqual(report.production_reviewed_items,reviewed)
                self.assertEqual(report.production_common_target_items,shared)
                self.assertEqual(dict(report.production_assessment_counts)["native-only"],native)
                self.assertFalse(report.corpus_wide_completion_claim_eligible)
                original={r["item_id"]:r["accounting"]["production"] for r in old["semantic_items"]}
                actual={r["item_id"]:r["accounting"]["production"] for r in new["semantic_items"]}
                self.assertEqual(set(original),set(actual))
                self.assertTrue(all(actual[k]==v for k,v in original.items() if v is not None))
                for m in load_profile(corpus,"0.6.0").mappings.data["mappings"]:
                    if not m["mapping_id"].startswith(f"mapping:{corpus}:morph-"):continue
                    b=m["native_binding"];id=f'node_value:{b["feature"]}="{b["value"]}"'
                    self.assertEqual(actual[id]["source_ids"],[m["mapping_id"]])
                    self.assertEqual(actual[id]["common_target"],bool(m["projections"]))
