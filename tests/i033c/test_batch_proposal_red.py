"""I-033C: RED/semantic parity against immutable released Mapping v2 sources."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tfont.batch_proposals import compile_candidate_batch, load_ledger
from tfont.semantic_digest_v2 import (
    mapping_semantic_digest_v2,
    mapping_semantic_projection_v2,
    projection_semantic_digest_v1,
    projection_semantic_projection_v1,
)
from tfont.source_validation import SourceValidationError, validate_source


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "src/tfont/resources/batch_pilots/i033c-adj-adv-proposals.json"
OUTPUT = ROOT / "docs/research/data/generated/i033c/adj-adv-candidates.json"


class BatchProposalRedTests(unittest.TestCase):
    def test_four_published_mapping_semantics_compile_from_one_ledger(self):
        compiled = compile_candidate_batch(load_ledger())
        self.assertEqual(compiled["release_authorized"], False)
        self.assertEqual(compiled["batch_id"], "i033c-olia-bhsa-syriac-adjadv")
        self.assertEqual(compiled["count"], 4)
        rows = compiled["candidates"]
        self.assertEqual(len(rows), 4)
        self.assertEqual(len({m["mapping_id"] for m in rows}), 4)
        for mapping in rows:
            with self.subTest(mapping=mapping["mapping_id"]):
                corpus = mapping["corpus_id"]
                target = mapping["projections"][0]["target"].rsplit("#", 1)[1]
                original = json.loads(
                    (ROOT / f"src/tfont/resources/profiles/{corpus}/0.4.0/mappings/adj-adv.json")
                    .read_text(encoding="utf-8")
                )
                historic = next(
                    m for m in original["mappings"]
                    if m["mapping_id"] == mapping["mapping_id"]
                )
                self.assertEqual(
                    mapping_semantic_projection_v2(mapping),
                    mapping_semantic_projection_v2(historic),
                )
                self.assertEqual(
                    projection_semantic_projection_v1(mapping["projections"][0]),
                    projection_semantic_projection_v1(historic["projections"][0]),
                )
                self.assertEqual(mapping["mapping_semantic_digest"], historic["mapping_semantic_digest"])
                self.assertEqual(
                    mapping["projections"][0]["projection_semantic_digest"],
                    historic["projections"][0]["projection_semantic_digest"],
                )
                self.assertEqual(mapping_semantic_digest_v2(mapping), historic["mapping_semantic_digest"])
                self.assertEqual(
                    projection_semantic_digest_v1(mapping["projections"][0]),
                    historic["projections"][0]["projection_semantic_digest"],
                )
                self.assertNotIn("review", mapping)
                self.assertNotIn("review", mapping["projections"][0])
                self.assertEqual(mapping["native_binding"]["execution_shape"], "value-predicate")
                self.assertEqual(mapping["native_binding"]["node_type"], "word")
                self.assertIn(target, ("Adjective", "Adverb"))

    def test_proposals_are_structurally_not_production_mapping_artifacts(self):
        prepared = compile_candidate_batch(load_ledger())
        with self.assertRaises(SourceValidationError):
            validate_source(
                {"schema_version": 2, "mappings": prepared["candidates"]},
                "mapping",
                source_name="unreviewed-batch",
            )

    def test_frozen_report_rebuilt_identically(self):
        from tfont.batch_proposals import serialized
        self.assertTrue(LEDGER.is_file())
        self.assertTrue(OUTPUT.is_file())
        self.assertEqual(
            OUTPUT.read_text(encoding="utf-8"),
            serialized(compile_candidate_batch(load_ledger())),
        )


if __name__ == "__main__":
    unittest.main()
