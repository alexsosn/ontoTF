"""I-034F RED: extract actual MQL POS enum declarations, not guessed TF glosses."""
from __future__ import annotations

import bz2
import hashlib
import json
import unittest

from scripts.research.i027b3_extract_mql import extract, extract_pos_enum, verify_frozen


SOURCE = """-- unrelated decoy
CREATE ENUMERATION unrelated_t = {
  sp = 77,
};
CREATE ENUMERATION part_of_speech_t = {
  verb = 1,
  subs = 2,
  nmpr = 3,
  art = 14,
};
CREATE OBJECT TYPE [word]
  sp : part_of_speech_t;
END;
CREATE ENUMERATION later_t = {
  invented = 28,
};
"""


class OriginalPOSDeclarationsRED(unittest.TestCase):
    def test_extracts_declared_enum_ids_codes_lines_and_word_feature_binding(self):
        result = extract_pos_enum(SOURCE)
        self.assertEqual(result, {
            "enum_declaration_line": 5,
            "feature_type_line": 12,
            "values": [
                {"value": "verb", "code": 1, "line": 6},
                {"value": "subs", "code": 2, "line": 7},
                {"value": "nmpr", "code": 3, "line": 8},
                {"value": "art", "code": 14, "line": 9},
            ],
        })
        self.assertNotIn("invented", [v["value"] for v in result["values"]])
        self.assertNotIn("sp", [v["value"] for v in result["values"]])

    def test_requires_typed_sp_and_one_real_enum_not_a_stray_string(self):
        for bad in (
            SOURCE.replace("sp : part_of_speech_t;", "sp : other_type;"),
            SOURCE.replace("CREATE ENUMERATION part_of_speech_t", "CREATE ENUMERATION unrelated_sp_t"),
            SOURCE + "\nCREATE ENUMERATION part_of_speech_t = {\n  art = 14,\n};",
            SOURCE.replace("  art = 14,\n};", "  art = 14,\n"),
            SOURCE.replace("  subs = 2,", "  verb = 2,"),
            SOURCE.replace("  subs = 2,", "  subs = 1,"),
            SOURCE.replace("  subs = 2,", "  subs = true,"),
            SOURCE.replace("  art = 14,", "  art = -1,"),
            SOURCE.replace("  art = 14,", "  art = 14, nonsense"),
        ):
            with self.subTest(bad=bad[-90:]), self.assertRaises(ValueError):
                extract_pos_enum(bad)

    def test_verified_blob_extraction_includes_small_original_enum(self):
        raw = bz2.compress(SOURCE.encode("utf-8"))
        expected_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest()
        report = extract(raw, expected_blob_sha=expected_blob, expected_size=len(raw))
        self.assertEqual(report["part_of_speech_enum"], extract_pos_enum(SOURCE))
        self.assertFalse(report["exact_mapping_authorized"])
        self.assertEqual(report["decompressed_sha256"],
                         hashlib.sha256(SOURCE.encode("utf-8")).hexdigest())

    def test_enumeration_is_bounded(self):
        excess = (
            "CREATE ENUMERATION part_of_speech_t = {\n"
            + "".join(f"x{i} = {i},\n" for i in range(70))
            + "};\nsp : part_of_speech_t;\n"
        )
        with self.assertRaises(ValueError):
            extract_pos_enum(excess)

    def test_legacy_bounded_scan_still_accepts_unrelated_mql(self):
        # Earlier I-027B3 research API intentionally scanned unrelated / partial
        # MQL sources without claiming any executable POS mapping.
        raw = bz2.compress(b"CREATE OBJECT TYPE [other]\n name: string;\nEND;\n")
        expected_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest()
        report = extract(raw, expected_blob_sha=expected_blob, expected_size=len(raw))
        self.assertIsNone(report["part_of_speech_enum"])
        self.assertEqual(report["match_counts"]["part_of_speech_t"], 0)
        self.assertFalse(report["exact_mapping_authorized"])

    def test_frozen_v2_requires_exact_original_enum_not_just_source_digests(self):
        raw = bz2.compress(SOURCE.encode("utf-8"))
        expected_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest()
        report = extract(raw, expected_blob_sha=expected_blob, expected_size=len(raw))
        frozen = {key: report[key] for key in (
            "source_repository", "source_revision", "source_path",
            "compressed_size", "git_blob_sha", "compressed_sha256",
            "decompressed_size", "decompressed_sha256", "encoding",
        )}
        frozen.update(schema_version=2, exact_mapping_authorized=False,
                      part_of_speech_enum=json.loads(json.dumps(report["part_of_speech_enum"])))
        verify_frozen(report, frozen)
        forged = json.loads(json.dumps(frozen))
        forged["part_of_speech_enum"]["values"][0]["code"] = 999
        with self.assertRaisesRegex(ValueError, "POS enum"):
            verify_frozen(report, forged)
        forged = dict(frozen)
        del forged["part_of_speech_enum"]
        with self.assertRaisesRegex(ValueError, "POS enum"):
            verify_frozen(report, forged)



if __name__ == "__main__":
    unittest.main()
