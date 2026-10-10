from __future__ import annotations

import copy
import unittest

from tfont.production_bundles import ProductionBundleError
from tfont.release_registry import (
    load_profile,
    list_profile_releases,
    _load_catalogue,
    _load_from_catalogue,
)


class GenericReleaseCatalogAdversarial(unittest.TestCase):
    def test_unknown_models_and_corpus_rejected(self):
        for corpus, version, models in (
            ("unknown", "current", ("olia",)),
            ("bhsa", "100.0.0", ("olia",)),
            ("syriac", "current", ("crminf",)),
            ("bhsa", "current", ("olia", "skos")),
            ("bhsa", "current", ()),
            ("bhsa", "../syriac", ("olia",)),
        ):
            with self.subTest(corpus=corpus, version=version, models=models):
                with self.assertRaises(ProductionBundleError):
                    load_profile(corpus, version, models=models)

    def test_catalogue_rejects_profile_traversal_or_cross_corpus_swap(self):
        cat = _load_catalogue()
        for profile_path in ("../secret.json", "resources/profiles/syriac/0.4.0/profile.json", "/tmp/file.json"):
            changed=copy.deepcopy(cat)
            changed["corpora"]["bhsa"]["releases"]["0.4.0"]["profile"] = profile_path
            with self.subTest(path=profile_path), self.assertRaises(ProductionBundleError):
                _load_from_catalogue(changed, "bhsa", "0.4.0", ("olia",))

    def test_missing_duplicated_or_mixed_ontology_evidence_fails(self):
        cat = _load_catalogue()
        for mode in ("drop", "repeat", "foreign"):
            changed=copy.deepcopy(cat)
            e=changed["corpora"]["syriac"]["releases"]["0.4.0"]["ontology_evidence"]
            if mode == "drop":
                e.clear()
            elif mode == "repeat":
                e.append(e[0])
            else:
                e[0] = "resources/profiles/syriac/0.4.0/evidence/native-adj-adv-pos.json"
            with self.subTest(mode=mode), self.assertRaises(ProductionBundleError):
                _load_from_catalogue(changed, "syriac", "0.4.0", ("olia",))

    def test_legacy_syriac_digest_exception_is_exact_blob_only(self):
        from tfont.production_bundles import _artifact
        from tfont.release_registry import _historical_evidence_unchanged
        from tfont.semantic_validation import SemanticArtifact

        path = "resources/profiles/syriac/0.3.0/evidence/native-verb-pos.json"
        historical = _artifact("evidence", "evidence", path)
        self.assertTrue(_historical_evidence_unchanged(path, historical))

        modified = copy.deepcopy(historical.data)
        modified["reviewed_content"]["value"] = "noun"
        forged = SemanticArtifact("evidence", path, modified)
        self.assertFalse(_historical_evidence_unchanged(path, forged))
        self.assertFalse(_historical_evidence_unchanged(
            "resources/profiles/bhsa/0.3.0/evidence/native-verb-pos.json",
            historical,
        ))
        modified = copy.deepcopy(historical.data)
        modified["content_digest"] = "sha256:" + "0" * 64
        self.assertFalse(_historical_evidence_unchanged(
            path, SemanticArtifact("evidence", path, modified),
        ))

    def test_alias_cannot_select_unregistered_release(self):
        changed=copy.deepcopy(_load_catalogue())
        changed["corpora"]["extrabiblical"]["current"] = "0.4.0"
        with self.assertRaises(ProductionBundleError):
            _load_from_catalogue(changed, "extrabiblical", "current", ("olia",))

    def test_duplicate_native_evidence_and_schema_spoof_fail(self):
        cat=_load_catalogue()
        changed=copy.deepcopy(cat)
        extra=changed["corpora"]["extrabiblical"]["releases"]["0.3.0"]["native_evidence"]
        extra.append(extra[0])
        with self.assertRaises(ProductionBundleError):
            _load_from_catalogue(changed, "extrabiblical", "0.3.0", ("olia",))
        changed=copy.deepcopy(cat)
        changed["schema_version"]=42
        with self.assertRaises(ProductionBundleError):
            _load_from_catalogue(changed, "bhsa", "0.4.0", ("olia",))


if __name__ == "__main__":
    unittest.main()
