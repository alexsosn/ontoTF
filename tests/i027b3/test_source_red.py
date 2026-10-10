from __future__ import annotations

import bz2
import hashlib
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/research/i027b3_extract_mql.py"


def load_builder():
    if not SCRIPT.is_file():
        raise AssertionError("RED: I-027B3 extractor is absent")
    spec = importlib.util.spec_from_file_location("i027b3_source_extractor", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("RED: extractor module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\\0" + raw
    ).hexdigest()


def synthetic_mql():
    return bz2.compress(
        b"CREATE ENUMERATION part_of_speech_t = {\\n"
        b"  noun, verb, adjective\\n"
        b"};\\n"
        b"CREATE OBJECT TYPE [word]\\n"
        b" sp: part_of_speech_t;\\n"
    )


class I027B3SourceEvidenceRedTests(unittest.TestCase):
    def test_pinned_extractor_exists(self):
        self.assertTrue(SCRIPT.is_file(), "RED: extractor absent")

    def test_source_is_extractable_as_bounded_evidence(self):
        module = load_builder()
        raw = synthetic_mql()
        report = module.extract(
            raw, expected_blob_sha=blob_sha(raw), expected_size=len(raw)
        )
        self.assertEqual(report["compressed_size"], len(raw))
        self.assertEqual(report["git_blob_sha"], blob_sha(raw))
        self.assertIn("compressed_sha256", report)
        self.assertIn("decompressed_sha256", report)
        self.assertGreater(report["match_counts"]["part_of_speech_t"], 0)
        self.assertGreater(report["match_counts"]["verb"], 0)
        self.assertTrue(
            any(
                "part_of_speech_t" in excerpt["context"]
                for excerpt in report["excerpts"]["part_of_speech_t"]
            )
        )
        self.assertEqual(report, module.extract(
            raw, expected_blob_sha=blob_sha(raw), expected_size=len(raw)
        ))

    def test_source_checksum_and_size_fail_closed(self):
        module = load_builder()
        raw = synthetic_mql()
        with self.assertRaisesRegex(ValueError, "blob"):
            module.extract(raw, expected_blob_sha="0" * 40, expected_size=len(raw))
        with self.assertRaisesRegex(ValueError, "size"):
            module.extract(raw, expected_blob_sha=blob_sha(raw), expected_size=len(raw) + 1)

    def test_bad_bzip_and_invalid_utf8_are_rejected(self):
        module = load_builder()
        corrupt = b"not bzip2"
        with self.assertRaisesRegex(ValueError, "bzip2"):
            module.extract(
                corrupt, expected_blob_sha=blob_sha(corrupt), expected_size=len(corrupt)
            )
        bad_unicode = bz2.compress(b"part_of_speech_t = verb;\\xff")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            module.extract(
                bad_unicode, expected_blob_sha=blob_sha(bad_unicode),
                expected_size=len(bad_unicode),
            )

    def test_excerpt_length_is_bounded(self):
        module = load_builder()
        raw = bz2.compress(
            ("part_of_speech_t " + "X" * 30000 + " verb sp\\n").encode()
        )
        report = module.extract(
            raw, expected_blob_sha=blob_sha(raw), expected_size=len(raw)
        )
        for windows in report["excerpts"].values():
            self.assertLessEqual(len(windows), 6)
            self.assertTrue(all(len(window["context"]) <= 600 for window in windows))


if __name__ == "__main__":
    unittest.main()
