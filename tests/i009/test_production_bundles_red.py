from __future__ import annotations

import importlib
import importlib.util
import json
import unittest
from importlib.resources import files

from tfont.digests import evidence_payload_digest
from tfont.semantic_ir import SemanticKey, compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle

OLIA_NOUN = "http://purl.org/olia/olia.owl#Noun"
EXPECTED_PARENT_DIGESTS = {
    "bhsa": "sha256:cc2c65cd79b2cb7faf1a34b94feb3cc2d3291e7064cbec942c53b0e05f1b0837",
    "syriac": "sha256:afb5a826b9ebe10cdd4ca23d96e00ee7bf677d06496cfcfcee6bb37d2ecff6c4",
    "extrabiblical": "sha256:d39fe3f4848cadb14ae5ef453a5150ea6281b2874728566198d7de10d72bec4a",
}
EXPECTED_COMPONENT_DIGESTS = {
    "bhsa": "sha256:5178414e293a743fc98768abcab5b9cb268e14ad56fd2cfbac544ae2869d2e6f",
    "syriac": "sha256:54a2596d5525f3afb34db0a89d5511e6b8471ce4a93fae4825b22f0945ab62ef",
    "extrabiblical": "sha256:d0ca9bdf90bfdefe19861c2c68e91071650ed511b8a79270490238b30274aee0",
}
OLIA_DIGEST = "sha256:5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd"
OLIA_REVISION = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"


def noun_key() -> SemanticKey:
    return SemanticKey(
        profile_id="linguistic",
        capability_id="linguistic.part-of-speech",
        target=OLIA_NOUN,
        formal_kind="class",
        semantic_role="annotation-value",
    )


class I009ProductionBundleTests(unittest.TestCase):
    def _module(self):
        spec = importlib.util.find_spec("tfont.production_bundles")
        self.assertIsNotNone(spec, "I-009 production bundle module is absent")
        return importlib.import_module("tfont.production_bundles")

    def _bundles(self):
        module = self._module()
        bundles = module.load_production_noun_bundles()
        self.assertEqual(len(bundles), 3)
        return module, bundles

    def test_all_three_package_bundles_validate_and_compile_together(self):
        module, bundles = self._bundles()
        self.assertEqual(module.PRODUCTION_NOUN_CORPORA, ("bhsa", "syriac", "extrabiblical"))
        self.assertEqual(
            tuple(bundle.profile.data["profile_id"] for bundle in bundles),
            ("tfont-bhsa", "tfont-syriac", "tfont-extrabiblical"),
        )
        validated = tuple(validate_semantic_bundle(bundle) for bundle in bundles)
        ir = compile_semantic_ir(validated)
        self.assertEqual(
            tuple(row.key.corpus_id for row in ir.variants),
            tuple(sorted(module.PRODUCTION_NOUN_CORPORA)),
        )

    def test_profiles_use_real_parent_identities_and_mit_license(self):
        module, bundles = self._bundles()
        for corpus_id, bundle in zip(module.PRODUCTION_NOUN_CORPORA, bundles, strict=True):
            with self.subTest(corpus_id=corpus_id):
                validated = validate_semantic_bundle(bundle)
                self.assertEqual(validated.expected_parent_manifest_digest, EXPECTED_PARENT_DIGESTS[corpus_id])
                self.assertEqual(bundle.profile.data["license"], "MIT")
                components = bundle.expected_parent_manifest.data["components"]
                self.assertEqual(len(components), 1)
                self.assertEqual(components[0]["component_id"], f"{corpus_id}-tf")
                self.assertEqual(components[0]["content_digest"], EXPECTED_COMPONENT_DIGESTS[corpus_id])
                self.assertEqual(components[0]["identity_algorithm"], "tfont-tf-files-sha256-v1")

    def test_shared_olia_lock_is_exact_and_identical_across_bundles(self):
        _, bundles = self._bundles()
        locks = [bundle.ontology_locks[0].data for bundle in bundles]
        self.assertEqual(locks[0], locks[1])
        self.assertEqual(locks[1], locks[2])
        lock = locks[0]
        self.assertEqual(lock["lock_id"], "olia-reference-model")
        self.assertEqual(lock["content_digest"], OLIA_DIGEST)
        self.assertEqual(lock["license"], "CC-BY-3.0")
        self.assertEqual(lock["terms_used"], [OLIA_NOUN])
        self.assertEqual(lock["source_revision"], OLIA_REVISION)

    def test_shipped_olia_snapshot_bytes_match_researched_digest(self):
        snapshot = files("tfont").joinpath(
            "resources",
            "ontologies",
            "olia",
            OLIA_REVISION,
            "olia.owl",
        )
        self.assertEqual(evidence_payload_digest(snapshot.read_bytes()), OLIA_DIGEST)

    def test_compiled_noun_bindings_preserve_corpus_specific_execution_shapes(self):
        module, bundles = self._bundles()
        validated = tuple(validate_semantic_bundle(bundle) for bundle in bundles)
        ir = compile_semantic_ir(validated)
        rows = dict(ir.semantic_index)[noun_key()]
        by_corpus = {row.corpus_id: row for row in rows}
        self.assertEqual(tuple(sorted(by_corpus)), tuple(sorted(module.PRODUCTION_NOUN_CORPORA)))

        for corpus_id in ("bhsa", "extrabiblical"):
            binding = by_corpus[corpus_id].native_execution_binding
            self.assertEqual(binding.execution_shape, "value-set-predicate")
            self.assertEqual(binding.node_type, "word")
            self.assertEqual(binding.feature, "sp")
            self.assertEqual(binding.values, ("nmpr", "subs"))
            self.assertFalse(binding.value_present)

        syriac = by_corpus["syriac"].native_execution_binding
        self.assertEqual(syriac.execution_shape, "value-predicate")
        self.assertEqual(syriac.node_type, "word")
        self.assertEqual(syriac.feature, "sp")
        self.assertTrue(syriac.value_present)
        self.assertEqual(syriac.value, "subs")
        self.assertIsNone(syriac.values)

    def test_production_resources_contain_no_fixture_or_placeholder_provenance(self):
        _, bundles = self._bundles()
        forbidden = (
            "example.org",
            "fixture-v1",
            "reviewer:i005-fixture",
            "NOASSERTION",
            "LicenseRef-TFont-Unspecified",
        )
        for bundle in bundles:
            payloads = [
                bundle.profile.data,
                bundle.expected_parent_manifest.data,
                bundle.mappings.data,
                *(artifact.data for artifact in bundle.ontology_locks),
                *(artifact.data for artifact in bundle.evidences),
            ]
            text = "\n".join(json.dumps(payload, sort_keys=True) for payload in payloads)
            for needle in forbidden:
                with self.subTest(needle=needle):
                    self.assertNotIn(needle, text)


if __name__ == "__main__":
    unittest.main()
