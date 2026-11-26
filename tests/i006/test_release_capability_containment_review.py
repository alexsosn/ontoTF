from __future__ import annotations

import importlib
import unittest
from dataclasses import replace

from tests.i006._fixtures import compiled_noun_ir
from tests.i006.test_semantic_resolver_contract import prerequisite_for


RESOLVER = importlib.import_module("ontotf.semantic_resolver")


def assert_invalid(testcase: unittest.TestCase, ir) -> None:
    with testcase.assertRaises(RESOLVER.SemanticResolutionError) as raised:
        state = prerequisite_for(RESOLVER, ir.variants[0])
        RESOLVER.semantic_capabilities(
            ir,
            (state,),
            corpora=("bhsa",),
        )
    testcase.assertEqual(raised.exception.problem.category, "invalid_compiled_ir")


class I006ReleaseCapabilityContainmentReviewTests(unittest.TestCase):
    def test_duplicate_release_profiles_fail_closed(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        signature = replace(
            variant.release_signature,
            profiles=variant.release_signature.profiles + (variant.release_signature.profiles[0],),
        )
        assert_invalid(self, replace(ir, variants=(replace(variant, release_signature=signature),)))

    def test_duplicate_release_capabilities_fail_closed(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        signature = replace(
            variant.release_signature,
            capabilities=variant.release_signature.capabilities + (variant.release_signature.capabilities[0],),
        )
        assert_invalid(self, replace(ir, variants=(replace(variant, release_signature=signature),)))

    def test_unknown_release_profile_fails_closed(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        signature = replace(
            variant.release_signature,
            profiles=variant.release_signature.profiles + ("future-profile",),
        )
        assert_invalid(self, replace(ir, variants=(replace(variant, release_signature=signature),)))

    def test_unknown_release_capability_fails_closed(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        signature = replace(
            variant.release_signature,
            capabilities=variant.release_signature.capabilities + ("linguistic.future-capability",),
        )
        assert_invalid(self, replace(ir, variants=(replace(variant, release_signature=signature),)))

    def test_release_capability_must_be_scoped_by_release_profile(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        signature = replace(
            variant.release_signature,
            profiles=("lexical",),
            capabilities=("linguistic.part-of-speech",),
        )
        assert_invalid(self, replace(ir, variants=(replace(variant, release_signature=signature),)))

    def test_negative_capability_counter_cannot_authorize_execution(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        forged = replace(facts, reviewed_native_support=-1, exact=1)
        assert_invalid(self, replace(ir, capability_facts=((key, forged),)))

    def test_boolean_capability_counter_is_not_an_integer_count(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        forged = replace(facts, reviewed_native_support=True)
        assert_invalid(self, replace(ir, capability_facts=((key, forged),)))

    def test_capability_projection_counts_must_be_coherent(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        forged = replace(facts, shared_projections=0, exact=1)
        assert_invalid(self, replace(ir, capability_facts=((key, forged),)))

    def test_capability_mapping_ids_must_be_an_exact_tuple(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        forged = replace(facts, mapping_ids=list(facts.mapping_ids))
        assert_invalid(self, replace(ir, capability_facts=((key, forged),)))

    def test_capability_mapping_ids_must_be_unique_nonempty_strings(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        forged = replace(facts, mapping_ids=facts.mapping_ids + (facts.mapping_ids[0],))
        assert_invalid(self, replace(ir, capability_facts=((key, forged),)))


if __name__ == "__main__":
    unittest.main()
