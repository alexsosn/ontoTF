from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/coverage/build_i027a_bhsa_verbal_stems.py"
POLICY = ROOT / "docs/research/data/i027a/bhsa-verbal-stem-policy.json"


def builder():
    if not SCRIPT.is_file():
        raise AssertionError("RED: I-027A builder is absent")
    spec = importlib.util.spec_from_file_location("i027a_builder_adversarial", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def policy():
    return json.loads(POLICY.read_text(encoding="utf-8"))


class I027AAdversarialTests(unittest.TestCase):
    def test_missing_stem_does_not_silently_shrink_review(self):
        p = policy()
        p["code_values"].remove("qal")
        with self.assertRaisesRegex(ValueError, "stem family|code values"):
            builder().build_successor(policy=p)

    def test_fabricated_stem_does_not_inflate_review(self):
        p = policy()
        p["code_values"].append("fictional")
        with self.assertRaisesRegex(ValueError, "stem family|code values"):
            builder().build_successor(policy=p)

    def test_wrong_native_feature_rejected(self):
        p = policy()
        p["native_feature"] = "gn"
        with self.assertRaisesRegex(ValueError, "native feature"):
            builder().build_successor(policy=p)

    def test_wrong_corpus_or_revision_rejected(self):
        for key, wrong in (("corpus_id", "syriac"), ("corpus_revision", "0" * 40)):
            with self.subTest(key=key):
                p = policy()
                p[key] = wrong
                with self.assertRaisesRegex(ValueError, "corpus|revision"):
                    builder().build_successor(policy=p)

    def test_digest_change_rejected(self):
        p = policy()
        p["denominator_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "denominator"):
            builder().build_successor(policy=p)

    def test_unauthorized_exact_target_rejected(self):
        p = policy()
        p["production_disposition"]["assessments"] = ["exact"]
        p["production_disposition"]["common_target"] = True
        with self.assertRaisesRegex(ValueError, "native-only"):
            builder().build_successor(policy=p)

    def test_a_different_capability_cannot_be_asserted(self):
        p = policy()
        p["production_disposition"]["capabilities"] = ["linguistic.discourse"]
        with self.assertRaisesRegex(ValueError, "linguistic.morphology"):
            builder().build_successor(policy=p)

    def test_input_not_mutated(self):
        p = policy()
        original = copy.deepcopy(p)
        builder().build_successor(policy=p)
        self.assertEqual(p, original)


if __name__ == "__main__":
    unittest.main()
