from __future__ import annotations

import bz2
import hashlib
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/research/build_i027c1_pos_matrix.py"


def mod():
    if not SCRIPT.exists():
        raise AssertionError("RED: builder is absent")
    spec = importlib.util.spec_from_file_location("i027c1_adversarial", SCRIPT)
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


class PinnedPOSMatrixAdversarialTests(unittest.TestCase):
    def test_duplicate_markdown_codes_are_rejected(self):
        source = "`prep` |preposition\n`prep` |other\n"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod().parse_bhsa(source)

    def test_duplicate_syriac_grammar_values_are_rejected(self):
        source = (
            '   sp: "part of speech" =\n'
            '      prep: "preposition",\n      prep: "other"\n'
            '   st: "state" =\n'
        )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod().parse_syriac(source)

    def test_mql_source_type_cannot_be_changed(self):
        source = "CREATE ENUMERATION part_of_speech_t = {\n verb = 1\n};\nsp : other_type;\n"
        with self.assertRaisesRegex(ValueError, "sp"):
            mod().parse_mql(source)

    def test_compressed_original_source_identity_fails_closed(self):
        obj = mod()
        raw = bz2.compress(
            b"CREATE ENUMERATION part_of_speech_t = {\n verb = 1\n};\nsp : part_of_speech_t;\n"
        )
        with self.assertRaisesRegex(ValueError, "size"):
            obj.decode_pinned_mql(raw, expected_size=len(raw) + 1, expected_blob="0" * 40)
        with self.assertRaisesRegex(ValueError, "blob"):
            obj.decode_pinned_mql(raw, expected_size=len(raw), expected_blob="0" * 40)
        broken = b"garbage"
        blob = hashlib.sha1(b"blob " + str(len(broken)).encode() + b"\0" + broken).hexdigest()
        with self.assertRaisesRegex(ValueError, "bzip2"):
            obj.decode_pinned_mql(broken, expected_size=len(broken), expected_blob=blob)

    def test_disallow_fabricated_mql_gloss(self):
        item = {"verb": {"line": 5, "gloss": "verb", "numeric_id": 1}}
        with self.assertRaisesRegex(ValueError, "gloss"):
            mod().reconcile("extrabiblical", item, {"verb": 6}, "source.mql.bz2", "b" * 40, "b" * 40)


if __name__ == "__main__":
    unittest.main()
