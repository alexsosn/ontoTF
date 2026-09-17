from __future__ import annotations

import unittest

import tfont


class I009PublicContractTests(unittest.TestCase):
    def test_production_bundle_surface_is_public_and_narrow(self):
        expected = (
            "PRODUCTION_NOUN_CORPORA",
            "ProductionBundleError",
            "load_production_noun_bundle",
            "load_production_noun_bundles",
        )
        for name in expected:
            with self.subTest(name=name):
                self.assertTrue(hasattr(tfont, name), f"missing public I-009 symbol: {name}")

        self.assertEqual(
            tfont.PRODUCTION_NOUN_CORPORA,
            ("bhsa", "syriac", "extrabiblical"),
        )
        self.assertTrue(issubclass(tfont.ProductionBundleError, ValueError))
        self.assertTrue(callable(tfont.load_production_noun_bundle))
        self.assertTrue(callable(tfont.load_production_noun_bundles))

    def test_unknown_and_non_string_corpus_ids_fail_with_public_error(self):
        self.assertTrue(hasattr(tfont, "ProductionBundleError"), "I-009 error type is not public")
        self.assertTrue(hasattr(tfont, "load_production_noun_bundle"), "I-009 loader is not public")
        for value in ("BHSA", "unknown", None, 7):
            with self.subTest(value=value):
                with self.assertRaises(tfont.ProductionBundleError):
                    tfont.load_production_noun_bundle(value)


if __name__ == "__main__":
    unittest.main()
