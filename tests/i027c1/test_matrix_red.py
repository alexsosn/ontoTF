from __future__ import annotations

import bz2
import hashlib
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/research/build_i027c1_pos_matrix.py"
OUTPUT = ROOT / "docs/research/data/generated/i027c1/native-pos-matrix.json"


def module():
    if not SCRIPT.is_file():
        raise AssertionError("RED: I-027C1 source matrix builder is missing")
    spec = importlib.util.spec_from_file_location("i027c1_builder", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class PinnedPOSMatrixRedTests(unittest.TestCase):
    def test_builder_and_frozen_matrix_exist(self):
        self.assertTrue(SCRIPT.is_file(), "RED: source matrix builder absent")
        self.assertTrue(OUTPUT.is_file(), "RED: frozen matrix absent")

    def test_bhsa_markdown_codes_and_explicit_glosses(self):
        mod = module()
        src = "code|description\n---|---\n`prep` |preposition\n`verb` |verb\n"
        found = mod.parse_bhsa(src)
        self.assertEqual(
            {name: item["gloss"] for name, item in found.items()},
            {"prep": "preposition", "verb": "verb"},
        )
        self.assertEqual(found["prep"]["line"], 3)

    def test_syriac_native_grammar_section_and_explicit_glosses(self):
        mod = module()
        src = (
            '   ls: "lexical set" =\n      prep: "possible preposition"\n'
            '   sp: "part of speech" =\n'
            '      prep: "preposition",\n      verb: "verb"\n'
            '   st: "state" =\n      prep: "not a POS value"\n'
        )
        found = mod.parse_syriac(src)
        self.assertEqual(sorted(found), ["prep", "verb"])
        self.assertEqual(found["prep"]["gloss"], "preposition")
        self.assertEqual(found["prep"]["line"], 4)

    def test_mql_numeric_enum_has_no_fabricated_english_gloss(self):
        mod = module()
        src = (
            "CREATE ENUMERATION part_of_speech_t = {\n"
            "  verb = 1,\n  prep = 2\n};\n"
            "CREATE OBJECT TYPE [word]\n"
            "  sp : part_of_speech_t;\n"
            "sp:=verb;\n"
        )
        found = mod.parse_mql(src)
        self.assertEqual({k: x["numeric_id"] for k, x in found.items()}, {"verb": 1, "prep": 2})
        self.assertTrue(all(item["gloss"] is None for item in found.values()))
        self.assertEqual(found["verb"]["line"], 2)

    def test_inventory_reconciliation_fails_closed_on_missing_or_extra(self):
        mod = module()
        src = {
            "verb": {"line": 1, "gloss": "verb"},
            "prep": {"line": 2, "gloss": "preposition"},
        }
        observed = {"verb": 6, "prep": 4}
        rows = mod.reconcile("bhsa", src, observed, "pinned.md", "a" * 40, "a" * 40)
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(row["observed_feature_records"] for row in rows), 10)
        self.assertTrue(all(row["ontology_mapping_authorized"] is False for row in rows))
        with self.assertRaisesRegex(ValueError, "missing"):
            mod.reconcile("bhsa", {"verb": src["verb"]}, observed, "pinned.md", "a" * 40, "a" * 40)
        with self.assertRaisesRegex(ValueError, "source-only"):
            mod.reconcile("bhsa", src, {"verb": 6}, "pinned.md", "a" * 40, "a" * 40)

    def test_frozen_matrix_rebuilt_byte_for_byte(self):
        mod = module()
        self.assertEqual(OUTPUT.read_text(encoding="utf-8"), mod.serialized(mod.build_from_pinned_paths()))


if __name__ == "__main__":
    unittest.main()
