from __future__ import annotations

import importlib
import unittest
from dataclasses import replace

from tests.i006._fixtures import compiled_noun_ir, with_bundle_digest
from tests.i006.test_semantic_resolver_contract import prerequisite_for


RESOLVER = importlib.import_module("ontotf.semantic_resolver")


def assert_problem(testcase: unittest.TestCase, category: str, callable_, *args, **kwargs):
    with testcase.assertRaises(RESOLVER.SemanticResolutionError) as raised:
        callable_(*args, **kwargs)
    testcase.assertEqual(raised.exception.problem.category, category)


class I006CapabilityPrerequisiteIntegrityTests(unittest.TestCase):
    def test_capabilities_reject_stale_exact_parent_attestation(self):
        ir = compiled_noun_ir(("bhsa",))
        state = prerequisite_for(RESOLVER, ir.variants[0])
        stale = replace(
            state,
            observed_parent_manifest_digest="sha256:" + "9" * 64,
        )
        assert_problem(
            self,
            "stale_prerequisite",
            RESOLVER.semantic_capabilities,
            ir,
            (stale,),
            corpora=("bhsa",),
        )

    def test_capabilities_reject_contradictory_required_bundle_attestation(self):
        ir = with_bundle_digest(
            compiled_noun_ir(("bhsa",)),
            "sha256:" + "6" * 64,
        )
        state = prerequisite_for(RESOLVER, ir.variants[0])
        invalid = replace(
            state,
            ontology_bundle_state="verified",
            active_ontology_bundle_digest=None,
        )
        assert_problem(
            self,
            "invalid_prerequisite",
            RESOLVER.semantic_capabilities,
            ir,
            (invalid,),
            corpora=("bhsa",),
        )

    def test_capabilities_keep_valid_nonexecutability_as_unavailable(self):
        ir = compiled_noun_ir(("bhsa",))
        state = prerequisite_for(RESOLVER, ir.variants[0])
        unverified = replace(state, parent_state="unverified")
        views = RESOLVER.semantic_capabilities(
            ir,
            (unverified,),
            corpora=("bhsa",),
        )
        noun_view = next(
            item
            for item in views
            if item.profile_id == "linguistic"
            and item.capability_id == "linguistic.part-of-speech"
        )
        self.assertEqual(noun_view.state, "unavailable")
        self.assertFalse(noun_view.executable_exact)


if __name__ == "__main__":
    unittest.main()
