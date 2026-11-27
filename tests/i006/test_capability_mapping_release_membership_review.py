from __future__ import annotations

import importlib
import unittest
from dataclasses import replace

from tests.i006._fixtures import compiled_noun_ir
from tests.i006.test_semantic_resolver_contract import prerequisite_for


RESOLVER = importlib.import_module("ontotf.semantic_resolver")


class I006CapabilityMappingReleaseMembershipReviewTests(unittest.TestCase):
    def test_capability_mapping_id_outside_selected_release_fails_closed(self):
        ir = compiled_noun_ir(("bhsa",))
        key, facts = ir.capability_facts[0]
        self.assertNotIn(
            "mapping:forged-out-of-release",
            {mapping_id for mapping_id, _ in ir.variants[0].release_signature.mapping_digests},
        )
        forged = replace(facts, mapping_ids=("mapping:forged-out-of-release",))
        state = prerequisite_for(RESOLVER, ir.variants[0])

        with self.assertRaises(RESOLVER.SemanticResolutionError) as raised:
            RESOLVER.semantic_capabilities(
                replace(ir, capability_facts=((key, forged),)),
                (state,),
                corpora=("bhsa",),
            )

        self.assertEqual(raised.exception.problem.category, "invalid_compiled_ir")
        self.assertEqual(raised.exception.problem.corpus_id, "bhsa")


if __name__ == "__main__":
    unittest.main()
