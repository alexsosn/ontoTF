from __future__ import annotations

import unittest

from tests.i005._fixtures import OLIA_NOUN, validated_noun_bundle


class I005FixtureControlTests(unittest.TestCase):
    def test_three_exact_noun_bundles_are_independently_valid(self):
        bundles = (
            validated_noun_bundle("bhsa", parent_char="a"),
            validated_noun_bundle("syriac", parent_char="b"),
            validated_noun_bundle("extrabiblical", parent_char="c"),
        )
        self.assertEqual(len(bundles), 3)
        for bundle in bundles:
            projections = dict(bundle.indexes.projections)
            self.assertEqual(len(projections), 1)
            projection = next(iter(projections.values()))
            self.assertEqual(projection["target"], OLIA_NOUN)
            self.assertEqual(projection["assessment"], "exact")

    def test_reviewed_parent_variants_are_independently_valid(self):
        first = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            authored_profile_id="tfont-bhsa",
            profile_version="0.1.0",
        )
        second = validated_noun_bundle(
            "bhsa",
            parent_char="d",
            authored_profile_id="tfont-bhsa",
            profile_version="0.1.0",
        )
        self.assertNotEqual(
            first.expected_parent_manifest_digest,
            second.expected_parent_manifest_digest,
        )
        self.assertEqual(
            dict(first.mapping_semantic_digests),
            dict(second.mapping_semantic_digests),
        )

    def test_provisional_review_status_is_valid_source_state(self):
        mapping_provisional = validated_noun_bundle(
            "bhsa",
            parent_char="a",
            mapping_review_status="provisional",
        )
        projection_provisional = validated_noun_bundle(
            "bhsa-projection-provisional",
            parent_char="e",
            projection_review_status="provisional",
        )
        self.assertEqual(
            next(iter(dict(mapping_provisional.indexes.mappings).values()))["review"]["status"],
            "provisional",
        )
        self.assertEqual(
            next(iter(dict(projection_provisional.indexes.projections).values()))["review"]["status"],
            "provisional",
        )


if __name__ == "__main__":
    unittest.main()
