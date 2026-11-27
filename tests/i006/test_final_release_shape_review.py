from __future__ import annotations

import importlib
import unittest
from dataclasses import replace

from tests.i006._fixtures import compiled_noun_ir
from tests.i006.test_semantic_resolver_contract import prerequisite_for, request_for


RESOLVER = importlib.import_module("ontotf.semantic_resolver")


def assert_invalid_compiled_ir(testcase: unittest.TestCase, ir, state):
    with testcase.assertRaises(RESOLVER.SemanticResolutionError) as raised:
        RESOLVER.semantic_resolve(
            ir,
            request_for(RESOLVER, ("bhsa",)),
            (state,),
        )
    testcase.assertEqual(raised.exception.problem.category, "invalid_compiled_ir")


class I006FinalReleaseShapeReviewTests(unittest.TestCase):
    def test_release_authority_row_shapes_fail_closed(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        state = prerequisite_for(RESOLVER, variant)
        signature = variant.release_signature

        cases = (
            (
                "dependency_records",
                replace(signature, dependency_records=(("dep-only",),)),
                {},
            ),
            (
                "mapping_digests",
                replace(signature, mapping_digests=(("map-only",),)),
                {"mapping_digests": (("map-only",),)},
            ),
            (
                "mapping_reviews",
                replace(signature, mapping_reviews=(("map-only",),)),
                {},
            ),
            (
                "projection_reviews",
                replace(signature, projection_reviews=(("map", "projection"),)),
                {},
            ),
            (
                "ontology_locks",
                replace(signature, ontology_locks=(object(),)),
                {"ontology_locks": (object(),)},
            ),
        )

        for label, bad_signature, mirrored in cases:
            with self.subTest(label=label):
                if label == "ontology_locks":
                    bad_lock = bad_signature.ontology_locks[0]
                    mirrored = {"ontology_locks": (bad_lock,)}
                bad_variant = replace(
                    variant,
                    release_signature=bad_signature,
                    **mirrored,
                )
                bad_ir = replace(ir, variants=(bad_variant,))
                assert_invalid_compiled_ir(self, bad_ir, state)

    def test_release_vocabulary_collection_shapes_fail_closed(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        state = prerequisite_for(RESOLVER, variant)
        signature = variant.release_signature

        cases = (
            ("profiles-not-tuple", replace(signature, profiles=object())),
            ("capabilities-not-tuple", replace(signature, capabilities=object())),
            ("profiles-bad-member", replace(signature, profiles=("linguistic", object()))),
            (
                "capabilities-bad-member",
                replace(signature, capabilities=("linguistic.part-of-speech", object())),
            ),
        )
        for label, bad_signature in cases:
            with self.subTest(label=label):
                bad_variant = replace(variant, release_signature=bad_signature)
                bad_ir = replace(ir, variants=(bad_variant,))
                assert_invalid_compiled_ir(self, bad_ir, state)


if __name__ == "__main__":
    unittest.main()
