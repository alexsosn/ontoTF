from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from tfont.published_deltas import (
    PublishedDeltaError, build_published_delta, load_published_delta,
)
from tfont.release_registry import load_profile
from tfont.semantic_validation import SemanticArtifact, SemanticSourceBundle


class PublishedDeltaAdversarial(unittest.TestCase):
    def setUp(self):
        self.delta=build_published_delta("bhsa","0.3.0","0.4.0")

    def test_data_written_review_flags_do_not_authorize_new_release(self):
        changed=copy.deepcopy(self.delta)
        for key, value in (
            ("authority","github-live-verified"),
            ("release_authorized",True),
            ("reviewer","author"),
        ):
            candidate=copy.deepcopy(changed)
            candidate[key]=value
            with self.subTest(key=key),self.assertRaises(PublishedDeltaError):
                load_published_delta(candidate)

    def test_forged_digest_mapping_source_or_dependency_fails_closed(self):
        for part,field,value in (
            ("added_mappings","semantic_digest","sha256:"+"0"*64),
            ("added_mappings","mapping_id","mapping:bhsa:olia-fake"),
            ("added_mappings","source_resource","resources/profiles/syriac/0.4.0/mappings/adj-adv.json"),
            ("added_dependencies","dependency_id","dep:syriac:word-sp:adjv"),
            ("added_evidence","evidence_id","evidence:foreign:unreviewed"),
        ):
            altered=copy.deepcopy(self.delta)
            altered[part][0][field]=value
            with self.subTest(part=part,field=field),self.assertRaises(PublishedDeltaError):
                load_published_delta(altered)

    def test_corpus_target_swap_and_partial_batch_rejected(self):
        for key,value in (("corpus_id","syriac"),("base_release","0.2.0"),("target_release","0.3.0")):
            altered=copy.deepcopy(self.delta)
            altered[key]=value
            with self.subTest(key=key),self.assertRaises(PublishedDeltaError):
                load_published_delta(altered)
        altered=copy.deepcopy(self.delta)
        altered["added_mappings"].pop()
        with self.assertRaises(PublishedDeltaError):
            load_published_delta(altered)

    def test_dropped_inherited_review_is_not_a_valid_overlay(self):
        source=load_profile("bhsa","0.4.0")
        changed=copy.deepcopy(source.mappings.data)
        old=next(x for x in changed["mappings"] if x["mapping_id"]=="mapping:bhsa:olia-verb")
        old["review"]["status"]="unreviewed"
        corrupt=SemanticSourceBundle(
            profile=source.profile,
            expected_parent_manifest=source.expected_parent_manifest,
            mappings=SemanticArtifact("mapping",source.mappings.source_name,changed),
            ontology_locks=source.ontology_locks,
            evidences=source.evidences,
        )
        # No injection of an unverified bundle is exposed by the published
        # registry-only reader. The corruption must fail the ordinary validator.
        from tfont.semantic_validation import SemanticValidationError,validate_semantic_bundle
        with self.assertRaises(SemanticValidationError):
            validate_semantic_bundle(corrupt)


if __name__=="__main__":
    unittest.main()
