from __future__ import annotations

import bz2
import hashlib
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/research/i027b3_extract_mql.py"


class I027B3SourceEvidenceAdversarialTests(unittest.TestCase):
    def test_real_source_pin_is_fixed_not_user_configurable(self):
        if not SCRIPT.exists():
            self.fail("RED: extractor missing")
        spec = importlib.util.spec_from_file_location("i027b3_adversarial", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.PINNED_BLOB_SHA, "4ba717b1716b747bb94d0359b950a55d8624b109")
        self.assertEqual(module.PINNED_COMPRESSED_SIZE, 1992719)
        self.assertEqual(module.PINNED_SOURCE_REVISION, "9a56288e6777bad6328856acf055c780e65dd5d9")

    def test_frozen_evidence_cannot_forge_source_statements(self):
        spec = importlib.util.spec_from_file_location("i027b3_audit", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        raw = bz2.compress(
            b"CREATE ENUMERATION part_of_speech_t = {\n"
            b" verb = 1,\n"
            b"};\n"
        )
        digest = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest()
        report = module.extract(
            raw, expected_blob_sha=digest, expected_size=len(raw)
        )
        frozen = {
            key: report[key] for key in (
                "source_repository", "source_revision", "source_path",
                "compressed_size", "git_blob_sha", "compressed_sha256",
                "decompressed_size", "decompressed_sha256", "encoding",
            )
        }
        frozen["exact_mapping_authorized"] = False
        frozen["statements"] = [
            {"line": 1, "excerpt": "CREATE ENUMERATION part_of_speech_t"}
        ]
        module.verify_frozen(report, frozen)
        frozen["statements"][0]["excerpt"] = "invented source assertion"
        with self.assertRaisesRegex(ValueError, "not reproduced"):
            module.verify_frozen(report, frozen)
        frozen["statements"][0]["excerpt"] = "CREATE ENUMERATION part_of_speech_t"
        frozen["decompressed_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            module.verify_frozen(report, frozen)

    def test_empty_unrelated_file_is_not_positive_semantic_evidence(self):
        spec = importlib.util.spec_from_file_location("i027b3_adversarial_other", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        raw = bz2.compress(b"CREATE OBJECT TYPE word;\n")
        sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        report = module.extract(raw, expected_blob_sha=sha, expected_size=len(raw))
        self.assertEqual(report["match_counts"]["part_of_speech_t"], 0)
        self.assertFalse(report.get("exact_mapping_authorized", False))


if __name__ == "__main__":
    unittest.main()
