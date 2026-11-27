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
        RESOLVER.semantic_capabilities(ir, (state,), corpora=("bhsa",))
    testcase.assertEqual(raised.exception.problem.category, "invalid_compiled_ir")


class I006ReleaseAuthorityReviewTests(unittest.TestCase):
    def test_capability_key_variant_must_exist_in_compiled_variants(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        orphan_variant = replace(key.variant, profile_version=key.variant.profile_version + "-orphan")
        forged_key = replace(key, variant=orphan_variant)
        assert_invalid(self, replace(ir, capability_facts=((forged_key, facts),)))

    def test_capability_key_profile_must_be_declared_by_selected_release(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        forged_key = replace(key, profile_id="lexical", capability_id="lexical.entry")
        assert_invalid(self, replace(ir, capability_facts=((forged_key, facts),)))

    def test_capability_key_capability_must_be_declared_by_selected_release(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        forged_key = replace(key, capability_id="linguistic.morphology")
        assert_invalid(self, replace(ir, capability_facts=((forged_key, facts),)))

    def test_capability_key_capability_must_be_scoped_by_its_profile(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        forged_key = replace(key, profile_id="linguistic", capability_id="lexical.entry")
        assert_invalid(self, replace(ir, capability_facts=((forged_key, facts),)))

    def test_semantic_binding_capability_must_be_declared_by_selected_release(self):
        ir = compiled_noun_ir(("bhsa",))
        variant = ir.variants[0]
        signature = replace(
            variant.release_signature,
            capabilities=("linguistic.morphology",),
        )
        forged_variant = replace(variant, release_signature=signature)
        # Remove capability facts so the malformed semantic binding is the only
        # undeclared part of the compiled IR. Global IR validation must still
        # reject it before discovery can return an apparently valid release.
        assert_invalid(self, replace(ir, variants=(forged_variant,), capability_facts=()))


if __name__ == "__main__":
    unittest.main()
