"""I-028A: source-bound 27-row BHSA/Syriac lexical-depth candidate contract."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs/research/data/i028a/bhsa-syriac-lexical-depth.json"
QUEUE = ROOT / "docs/research/data/generated/i026/p004-work-queue.json"
INVENTORY = {c: ROOT / f"docs/research/data/generated/r005/{c}.json" for c in ("bhsa", "syriac")}
PINS = {
    "bhsa": ("4db00e2157915495e1a4d3d57e41223df24775da", "5b179e543d9ce17f59c2902afdf3736d3803777f518ec92dd5f19fc14a96496d", "f7f21b755b91877e83a33a5edf04494084439a41"),
    "syriac": ("bb0eaa7e21b020a26b7566d2e495da9b1f84a919", "eca80cb23fc2cea0b55381d9cea0cc313eeccd42879a2d686e769145a8ada2eb", "c572948a22e4ab16cee571726dad7e272e7d04ec"),
}
LAYERS = {"source-lexeme-node", "lexical-label", "lexical-representation", "token-surface", "gloss-literal", "corpus-statistic", "language-metadata", "named-entity-classification", "morphological-root"}
ROW_FIELDS = {"corpus_id", "item_id", "layer", "source_description", "source_node_types", "source_value_type", "source_observed_unique_count", "rationale", "next_evidence_needed"}


def audit(ledger, queue, inventories):
    """Fail closed on source drift, denominator drift, or forged review authority."""
    assert set(ledger) == {"schema_version", "batch_id", "mode", "workstream", "source_registry", "rows"}
    assert ledger["schema_version"] == 1
    assert ledger["mode"] == "research-proposal-only"
    assert ledger["workstream"] == "D"
    assert ledger["batch_id"] == "i028a-bhsa-syriac-lexical-depth"
    assert set(ledger["source_registry"]) == set(PINS)
    scoped = {(r["corpus_id"], r["item_id"]) for r in queue["semantic_rows"] if r["workstream"] == "D" and r["corpus_id"] in PINS}
    assert len(scoped) == 27
    assert len(ledger["rows"]) == 27
    assert len({(r["corpus_id"], r["item_id"]) for r in ledger["rows"]}) == 27
    assert {(r["corpus_id"], r["item_id"]) for r in ledger["rows"]} == scoped
    for corpus, inv in inventories.items():
        pin = ledger["source_registry"][corpus]
        assert set(pin) == {"repository", "revision", "tf_files_sha256", "tf_inventory", "inventory_git_blob_sha"}
        assert pin["repository"] == f"ETCBC/{corpus}"
        assert (pin["revision"], pin["tf_files_sha256"]) == PINS[corpus][:2]
        assert (inv["revision"], inv["tf_files_sha256"]) == PINS[corpus][:2]
        assert pin["inventory_git_blob_sha"] == PINS[corpus][2]
        assert pin["tf_inventory"] == f"docs/research/data/generated/r005/{corpus}.json"
    for row in ledger["rows"]:
        assert set(row) == ROW_FIELDS
        assert row["layer"] in LAYERS
        assert isinstance(row["rationale"], str) and len(row["rationale"].strip()) >= 30
        assert isinstance(row["next_evidence_needed"], str) and len(row["next_evidence_needed"].strip()) >= 10
        corpus, item_id = row["corpus_id"], row["item_id"]
        inv = inventories[corpus]
        kind, name = item_id.split(":", 1)
        if kind == "node_type":
            assert name == "lex" and corpus == "bhsa"
            assert name in inv["node_types"]
            assert row["layer"] == "source-lexeme-node"
            assert row["source_description"] is None
            assert row["source_node_types"] == ["lex"]
            assert row["source_value_type"] is None
            assert row["source_observed_unique_count"] == inv["node_types"][name]
        else:
            assert kind == "node_feature"
            feat = inv["node_features"][name]
            assert row["source_description"] == feat["metadata"]["description"]
            assert row["source_node_types"] == feat["applies_to"]
            assert row["source_value_type"] == feat["metadata"]["valueType"]
            assert row["source_observed_unique_count"] == feat["observed_unique_count"]
            assert row["layer"] != "source-lexeme-node"
    by_id = {(r["corpus_id"], r["item_id"]): r for r in ledger["rows"]}
    assert by_id[("bhsa", "node_feature:lex0")]["layer"] == "lexical-label"
    assert by_id[("bhsa", "node_feature:gloss")]["layer"] == "gloss-literal"
    assert by_id[("syriac", "node_feature:gloss")]["layer"] == "gloss-literal"
    assert by_id[("bhsa", "node_feature:root")]["layer"] == "morphological-root"
    assert by_id[("syriac", "node_feature:lex")]["source_node_types"] == ["word"]
    assert by_id[("bhsa", "node_feature:lex0")]["source_observed_unique_count"] < by_id[("bhsa", "node_feature:lex")]["source_observed_unique_count"]
    assert sum(r["layer"] == "source-lexeme-node" for r in ledger["rows"]) == 1


class LexicalDepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        cls.inventories = {c: json.loads(p.read_text(encoding="utf-8")) for c, p in INVENTORY.items()}

    def test_packaged_inventory_blob_sha_matches_review_pin(self):
        for corpus, path in INVENTORY.items():
            with self.subTest(corpus=corpus):
                raw = path.read_bytes()
                git_blob = b"blob " + str(len(raw)).encode("ascii") + b"\\0" + raw
                self.assertEqual(hashlib.sha1(git_blob).hexdigest(), PINS[corpus][2])

    def test_exact_denominator_and_pinned_source_semantics(self):
        audit(self.ledger, self.queue, self.inventories)

    def test_no_unreviewed_target_or_production_authority(self):
        payload = json.dumps(self.ledger)
        for forbidden in ('"mapping_id"', '"target"', '"review"', '"release_authorized"', '"coverage_manifest"', '"semantic_digest"'):
            self.assertNotIn(forbidden, payload)

    def test_adversarial_negative_mutations(self):
        for kind in ("drop", "duplicate", "forged-gloss", "wrong-scope", "bad-source-pin", "fake-entry"):
            with self.subTest(kind=kind):
                bad = copy.deepcopy(self.ledger)
                if kind == "drop":
                    bad["rows"].pop()
                elif kind == "duplicate":
                    bad["rows"].append(copy.deepcopy(bad["rows"][0]))
                elif kind == "forged-gloss":
                    next(r for r in bad["rows"] if r["corpus_id"] == "syriac" and r["item_id"] == "node_feature:gloss")["source_description"] = "Authoritative English translation of lexical sense"
                elif kind == "wrong-scope":
                    next(r for r in bad["rows"] if r["corpus_id"] == "syriac" and r["item_id"] == "node_feature:lex")["source_node_types"] = ["lex"]
                elif kind == "bad-source-pin":
                    bad["source_registry"]["bhsa"]["revision"] = "0" * 40
                elif kind == "fake-entry":
                    next(r for r in bad["rows"] if r["item_id"] == "node_feature:lex0")["layer"] = "source-lexeme-node"
                with self.assertRaises(AssertionError):
                    audit(bad, self.queue, self.inventories)


if __name__ == "__main__":
    unittest.main()
