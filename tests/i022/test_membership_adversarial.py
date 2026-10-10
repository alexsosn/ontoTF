from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

import tfont
import tfont.semantic_execution as execution
from tests.i020._fixtures import prerequisites_for
from tests.i022._fixtures import (
    MembershipApi,
    compiled_authority_membership_ir,
    compiled_membership_ir,
    compiled_reference_membership_ir,
    compiled_two_key_membership_ir,
    membership_api,
    membership_context,
    membership_request,
    approximate_membership_request,
    proper_noun_key,
)
from tfont.semantic_digest_v2 import (
    mapping_semantic_digest_v2,
    projection_semantic_digest_v1,
)
from tfont.semantic_ir import native_binding_identity
from tfont.source_validation import validate_source


ROOT = Path(__file__).resolve().parents[2]


def category(error: BaseException) -> str:
    return getattr(getattr(error, "problem", None), "category", "")


def plan_and_component(api=None):
    ir = compiled_membership_ir()
    resolution = tfont.semantic_resolve(
        ir,
        membership_request(tfont),
        prerequisites_for(tfont, ir),
    )
    plan = resolution.plans[0]
    context = membership_context(tfont, ir, api or membership_api())
    return plan, context.components[0]


class I022MembershipAdversarialTests(unittest.TestCase):
    def test_absent_type_refuses_at_fresh_prerequisite_before_execution(self):
        ir = compiled_membership_ir()
        api = membership_api(selections=((),))
        with self.assertRaises(Exception):
            tfont.execute_exact_semantic(
                ir,
                membership_request(tfont),
                (membership_context(tfont, ir, api),),
            )
        self.assertEqual(api.F.otype.s_calls, 1)

    def test_post_prerequisite_empty_selector_is_runtime_drift(self):
        ir = compiled_membership_ir()
        api = membership_api(
            selections=((4,), ()),
            node_types={4: "word"},
        )
        with self.assertRaises(Exception) as raised:
            tfont.execute_exact_semantic(
                ir,
                membership_request(tfont),
                (membership_context(tfont, ir, api),),
            )
        self.assertEqual(category(raised.exception), "invalid_result_nodes")
        self.assertEqual(api.F.otype.s_calls, 2)

    def test_loaded_otype_api_contract_fails_closed(self):
        plan, component = plan_and_component()

        api = MembershipApi()
        delattr(api.F, "otype")
        with self.assertRaises(Exception) as raised:
            execution._execute_membership(
                plan,
                replace(component, api=api),
            )
        self.assertEqual(category(raised.exception), "loaded_api_unavailable")

        for field in ("s", "v"):
            with self.subTest(field=field):
                api = MembershipApi()
                setattr(api.F.otype, field, None)
                with self.assertRaises(Exception) as raised:
                    execution._execute_membership(
                        plan,
                        replace(component, api=api),
                    )
                self.assertEqual(category(raised.exception), "loaded_api_unavailable")

    def test_selector_and_result_node_failures_are_deterministic(self):
        plan, component = plan_and_component()
        cases = (
            (membership_api(selections=(RuntimeError("boom"),)), "loaded_api_unavailable"),
            (membership_api(selections=(123,)), "invalid_result_nodes"),
            (membership_api(selections=((True,),)), "invalid_result_nodes"),
            (membership_api(selections=((object(),),)), "invalid_result_nodes"),
            (membership_api(selections=((0,),)), "invalid_result_nodes"),
            (membership_api(selections=((-1,),)), "invalid_result_nodes"),
            (membership_api(selections=((4, 4),), node_types={4: "word"}), "invalid_result_nodes"),
            (membership_api(selections=((),)), "invalid_result_nodes"),
        )
        for api, expected in cases:
            with self.subTest(expected=expected, api=api):
                with self.assertRaises(Exception) as raised:
                    execution._execute_membership(
                        plan,
                        replace(component, api=api),
                    )
                self.assertEqual(category(raised.exception), expected)

    def test_wrong_or_malformed_node_domain_fails_closed(self):
        plan, component = plan_and_component()
        for api, expected in (
            (
                membership_api(
                    selections=((4,),),
                    node_types={4: "phrase"},
                ),
                "invalid_result_nodes",
            ),
            (
                membership_api(
                    selections=((4,),),
                    node_types={4: None},
                ),
                "loaded_api_unavailable",
            ),
            (
                membership_api(
                    selections=((4,),),
                    node_types={4: "word"},
                    raise_on_v=True,
                ),
                "loaded_api_unavailable",
            ),
        ):
            with self.subTest(expected=expected):
                with self.assertRaises(Exception) as raised:
                    execution._execute_membership(
                        plan,
                        replace(component, api=api),
                    )
                self.assertEqual(category(raised.exception), expected)

    def test_forged_membership_binding_with_extra_field_is_rejected(self):
        plan, component = plan_and_component()
        forged_binding = replace(
            plan.native_execution_binding,
            feature="sp",
        )
        forged_plan = replace(plan, native_execution_binding=forged_binding)
        with self.assertRaises(Exception) as raised:
            execution._execute_membership(forged_plan, component)
        self.assertEqual(category(raised.exception), "unsupported_native_binding")

    def test_membership_never_touches_edges_oslots_or_autoload(self):
        ir = compiled_membership_ir()
        api = membership_api()
        result = tfont.execute_exact_semantic(
            ir,
            membership_request(tfont),
            (membership_context(tfont, ir, api),),
        )
        self.assertEqual(result.corpora[0].nodes, (4, 2, 7))
        self.assertFalse(api.E.touched)
        self.assertEqual(api.load_calls, 0)

    def test_native_binding_identity_is_order_independent_and_domain_sensitive(self):
        left = {
            "component_id": "bhsa-tf",
            "node_type": "word",
            "execution_shape": "membership",
        }
        right = {
            "execution_shape": "membership",
            "node_type": "word",
            "component_id": "bhsa-tf",
        }
        baseline = native_binding_identity(left)
        self.assertEqual(baseline, native_binding_identity(right))
        self.assertNotEqual(
            baseline,
            native_binding_identity({**left, "node_type": "phrase"}),
        )
        self.assertNotEqual(
            baseline,
            native_binding_identity({**left, "component_id": "other-tf"}),
        )

    def test_packaged_production_mappings_remain_non_structural_and_digest_valid(self):
        count = 0
        historical_count = 0
        shapes = set()
        root = ROOT / "src/tfont/resources/profiles"
        for path in sorted(root.glob("*/*/mappings/*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            validate_source(data, "mapping", source_name=str(path))
            for mapping in data.get("mappings", []):
                self.assertEqual(
                    mapping_semantic_digest_v2(mapping),
                    mapping["mapping_semantic_digest"],
                )
                rows = [mapping.get("native_binding")]
                for projection in mapping.get("projections", []):
                    self.assertEqual(
                        projection_semantic_digest_v1(projection),
                        projection["projection_semantic_digest"],
                    )
                    rows.append(projection.get("native_execution_binding"))
                rows.extend(
                    reference.get("native_binding")
                    for reference in mapping.get("external_references", [])
                )
                for binding in rows:
                    if type(binding) is not dict:
                        continue
                    shape = binding.get("execution_shape")
                    if type(shape) is str:
                        count += 1
                        if path.parent.parent.name in {"0.1.0", "0.2.0"}:
                            historical_count += 1
                        shapes.add(shape)
                        self.assertNotIn(shape, {"membership", "edge-path"})
        self.assertEqual(historical_count, 48)
        self.assertGreater(count, historical_count)
        self.assertEqual(shapes, {"value-predicate", "value-set-predicate"})

    def test_approximate_semantic_executes_exact_membership_without_loss(self):
        ir = compiled_membership_ir()
        result = tfont.execute_approximate_semantic(
            ir,
            approximate_membership_request(tfont),
            (membership_context(tfont, ir),),
        )
        self.assertEqual(result.corpora[0].nodes, (4, 2, 7))
        self.assertEqual(result.resolution.losses, ())

    def test_authorized_approximate_membership_preserves_loss_record(self):
        ir = compiled_membership_ir(
            assessment="broader",
            losses=("undercoverage",),
        )
        result = tfont.execute_approximate_semantic(
            ir,
            approximate_membership_request(
                tfont,
                accept_losses=("undercoverage",),
            ),
            (membership_context(tfont, ir),),
        )
        self.assertEqual(result.corpora[0].nodes, (4, 2, 7))
        self.assertEqual(result.resolution.losses, ("undercoverage",))
        self.assertEqual(result.corpora[0].plan.native_execution_binding.execution_shape, "membership")

    def test_exact_and_approximate_conjunction_reuse_membership_domain_safety(self):
        ir = compiled_two_key_membership_ir()
        keys = (membership_request(tfont).key, proper_noun_key(tfont))
        exact = tfont.execute_exact_conjunction(
            ir,
            tfont.SemanticConjunctionRequest(
                keys=keys,
                corpora=("bhsa",),
            ),
            (membership_context(tfont, ir),),
        )
        self.assertEqual(exact.corpora[0].nodes, (2, 4, 7))

        approximate = tfont.execute_approximate_conjunction(
            ir,
            tfont.ApproximateSemanticConjunctionRequest(
                keys=keys,
                corpora=("bhsa",),
                semantic_mode="approximate",
                accept_losses=(),
            ),
            (membership_context(tfont, ir),),
        )
        self.assertEqual(approximate.corpora[0].nodes, (2, 4, 7))
        self.assertEqual(approximate.resolution.losses, ())

    def test_authority_identity_and_identifier_execute_membership(self):
        authority_ir = compiled_authority_membership_ir()
        authority_key = authority_ir.authority_index[0][0]
        authority = tfont.execute_exact_authority(
            authority_ir,
            tfont.AuthorityResolveRequest(
                key=authority_key,
                corpora=("bhsa",),
            ),
            (membership_context(tfont, authority_ir),),
        )
        self.assertEqual(authority.corpora[0].nodes, (4, 2, 7))

        approximate_ir = compiled_authority_membership_ir(
            assessment="broader",
            losses=("undercoverage",),
        )
        approximate_key = approximate_ir.authority_index[0][0]
        approximate = tfont.execute_approximate_authority(
            approximate_ir,
            tfont.ApproximateAuthorityResolveRequest(
                key=approximate_key,
                corpora=("bhsa",),
                accept_losses=("undercoverage",),
            ),
            (membership_context(tfont, approximate_ir),),
        )
        self.assertEqual(approximate.corpora[0].nodes, (4, 2, 7))
        self.assertEqual(approximate.resolution.losses, ("undercoverage",))

        refs_ir = compiled_reference_membership_ir()
        identity_key = refs_ir.identity_index[0][0]
        identity = tfont.execute_identity(
            refs_ir,
            tfont.IdentityResolveRequest(
                authority_system=identity_key.authority_system,
                external_entity_id=identity_key.external_entity_id,
                corpora=("bhsa",),
            ),
            (membership_context(tfont, refs_ir),),
        )
        self.assertEqual(identity.corpora[0].nodes, (4, 2, 7))

        identifier_key = refs_ir.identifier_index[0][0]
        identifier = tfont.execute_identifier(
            refs_ir,
            tfont.IdentifierResolveRequest(
                key=identifier_key,
                corpora=("bhsa",),
            ),
            (membership_context(tfont, refs_ir),),
        )
        self.assertEqual(identifier.corpora[0].nodes, (4, 2, 7))

    def test_no_text_fabric_runtime_dependency_is_declared(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
        self.assertNotIn('"text-fabric', pyproject)
        self.assertNotIn("'text-fabric", pyproject)


if __name__ == "__main__":
    unittest.main()
