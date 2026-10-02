from __future__ import annotations

import json
import unittest
from dataclasses import replace

import tfont
from tests.i021._fixtures import (
    authority_ir,
    authority_two_binding_ir,
    identity_external,
    prerequisites,
    reference_ir,
    replace_identifier_row,
    replace_identity_row,
)
from tfont.semantic_ir import IdentifierKey


API_NAMES = (
    "AuthorityResolveRequest",
    "ApproximateAuthorityResolveRequest",
    "IdentityResolveRequest",
    "IdentifierResolveRequest",
    "authority_resolve_exact",
    "authority_resolve_approximate",
    "identity_resolve",
    "identifier_resolve",
)
HAS_API = all(hasattr(tfont, name) for name in API_NAMES)


def category(error: BaseException) -> str:
    return getattr(getattr(error, "problem", None), "category", "")


def assert_problem(testcase, expected, fn, *args, **kwargs):
    with testcase.assertRaises(Exception) as raised:
        fn(*args, **kwargs)
    testcase.assertEqual(category(raised.exception), expected)
    return raised.exception


class I021RedSentinelTests(unittest.TestCase):
    def test_native_record_retains_reviewed_mapping_semantic_payload(self):
        ir = reference_ir()
        native = next(row for _key, rows in ir.native_index for row in rows)
        payload = getattr(native, "mapping_semantic_payload", None)
        self.assertIsInstance(
            payload,
            str,
            "RED: NativeRecordIR does not retain reviewed mapping semantic payload",
        )
        self.assertEqual(json.dumps(json.loads(payload), separators=(",", ":"), sort_keys=True), payload)

    def test_public_reference_resolver_api_exists(self):
        missing = [name for name in API_NAMES if not hasattr(tfont, name)]
        self.assertEqual(missing, [], f"RED: missing I-021 public API: {missing}")


@unittest.skipUnless(HAS_API, "RED sentinel owns I-021 API absence")
class I021ReferenceResolutionContractTests(unittest.TestCase):
    def exact_authority(self, ir):
        key = ir.authority_index[0][0]
        request = tfont.AuthorityResolveRequest(key=key, corpora=("bhsa",))
        return tfont.authority_resolve_exact(ir, request, prerequisites(tfont, ir))

    def approx_authority(self, ir, *, accept_losses=()):
        key = ir.authority_index[0][0]
        request = tfont.ApproximateAuthorityResolveRequest(
            key=key,
            corpora=("bhsa",),
            accept_losses=tuple(accept_losses),
        )
        return tfont.authority_resolve_approximate(ir, request, prerequisites(tfont, ir))

    def identity(self, ir):
        key = ir.identity_index[0][0]
        request = tfont.IdentityResolveRequest(
            authority_system=key.authority_system,
            external_entity_id=key.external_entity_id,
            corpora=("bhsa",),
        )
        return tfont.identity_resolve(ir, request, prerequisites(tfont, ir))

    def identifier(self, ir, *, issuer=None, literal=None):
        key = ir.identifier_index[0][0]
        request = tfont.IdentifierResolveRequest(
            key=IdentifierKey(
                issuer_or_namespace=issuer or key.issuer_or_namespace,
                literal_id=literal or key.literal_id,
            ),
            corpora=("bhsa",),
        )
        return tfont.identifier_resolve(ir, request, prerequisites(tfont, ir))

    def test_exact_authority_resolves_only_authority_index(self):
        ir = authority_ir()
        result = self.exact_authority(ir)
        self.assertEqual(result.comparison_state, "exactly-comparable")
        self.assertEqual(result.losses, ())
        self.assertEqual(len(result.plans), 1)
        plan = result.plans[0]
        self.assertEqual(plan.corpus_id, "bhsa")
        self.assertEqual(plan.assessment, "exact")
        self.assertEqual(plan.authority_key, ir.authority_index[0][0])
        self.assertEqual(plan.query_role, "authority-value-filter")
        self.assertTrue(plan.plan_fingerprint)

    def test_non_exact_authority_refuses_exact_mode(self):
        for assessment, losses in (
            ("broader", ("undercoverage",)),
            ("narrower", ("overcoverage",)),
            ("close", ("undercoverage",)),
        ):
            with self.subTest(assessment=assessment):
                ir = authority_ir(assessment=assessment, losses=losses)
                assert_problem(
                    self,
                    "non_exact_authority_mapping",
                    self.exact_authority,
                    ir,
                )

    def test_approximate_authority_requires_loss_acceptance(self):
        ir = authority_ir(assessment="broader", losses=("undercoverage",))
        assert_problem(
            self,
            "approximation_loss_not_accepted",
            self.approx_authority,
            ir,
        )
        result = self.approx_authority(ir, accept_losses=("undercoverage",))
        self.assertEqual(result.losses, ("undercoverage",))
        self.assertEqual(result.comparison_state, "approximately-comparable")
        self.assertEqual(result.plans[0].assessment, "broader")
        self.assertEqual(result.loss_records[0].losses, ("undercoverage",))

    def test_exact_authority_wins_over_approximate(self):
        ir = authority_two_binding_ir(
            first_assessment="exact",
            second_assessment="broader",
            second_losses=("undercoverage",),
        )
        result = self.approx_authority(ir)
        self.assertEqual(result.losses, ())
        self.assertEqual(result.plans[0].assessment, "exact")

    def test_multiple_authority_bindings_fail_closed(self):
        exact = authority_two_binding_ir(
            first_assessment="exact",
            second_assessment="exact",
        )
        assert_problem(self, "multiple_authority_bindings", self.exact_authority, exact)

        approx = authority_two_binding_ir(
            first_assessment="broader",
            first_losses=("undercoverage",),
            second_assessment="broader",
            second_losses=("undercoverage",),
        )
        assert_problem(
            self,
            "multiple_approximate_authority_bindings",
            self.approx_authority,
            approx,
            accept_losses=("undercoverage",),
        )

    def test_same_entity_is_only_exact_identity_authority(self):
        exact = reference_ir(strengths=("same-entity",))
        result = self.identity(exact)
        self.assertEqual(len(result.plans), 1)
        self.assertEqual(result.plans[0].identity_strength, "same-entity")
        self.assertTrue(result.plans[0].reference_fingerprint)

        for strength in (
            "probable-same-entity",
            "related-record",
            "ambiguous-identity",
        ):
            with self.subTest(strength=strength):
                ir = reference_ir(strengths=(strength,))
                assert_problem(self, "identity_not_exact", self.identity, ir)

    def test_same_entity_wins_when_non_exact_strengths_coexist(self):
        ir = reference_ir(
            strengths=("probable-same-entity", "same-entity", "related-record")
        )
        result = self.identity(ir)
        self.assertEqual(result.plans[0].identity_strength, "same-entity")

    def test_multiple_same_entity_rows_fail_closed(self):
        ir = reference_ir(strengths=("same-entity", "same-entity"))
        assert_problem(self, "multiple_identity_bindings", self.identity, ir)

    def test_identity_request_has_no_caller_strength_field(self):
        fields = tfont.IdentityResolveRequest.__dataclass_fields__
        self.assertNotIn("identity_strength", fields)

    def test_native_only_parent_can_authorize_reference(self):
        ir = reference_ir(native_state="native-only")
        self.assertEqual(self.identity(ir).plans[0].identity_strength, "same-entity")
        self.assertEqual(len(self.identifier(ir).plans), 1)

    def test_identifier_is_strictly_issuer_scoped(self):
        ir = reference_ir(issuer="issuer-A", literal_id="123")
        self.assertEqual(len(self.identifier(ir).plans), 1)
        assert_problem(
            self,
            "identifier_reference_absent",
            self.identifier,
            ir,
            issuer="issuer-B",
            literal="123",
        )

    def test_multiple_identifier_rows_fail_closed(self):
        ir = reference_ir(duplicate_identifier=True)
        assert_problem(
            self,
            "multiple_identifier_bindings",
            self.identifier,
            ir,
        )

    def test_forged_identity_and_identifier_rows_fail_closed(self):
        ir = reference_ir()
        identity = ir.identity_index[0][1][0]
        forged_identity = replace_identity_row(
            ir,
            external="https://example.org/entity/forged",
        )
        request = tfont.IdentityResolveRequest(
            authority_system=identity.authority_system,
            external_entity_id=identity.external,
            corpora=("bhsa",),
        )
        assert_problem(
            self,
            "invalid_compiled_ir",
            tfont.identity_resolve,
            forged_identity,
            request,
            prerequisites(tfont, forged_identity),
        )

        identifier = ir.identifier_index[0][1][0]
        forged_identifier = replace_identifier_row(
            ir,
            native_binding_identity="sha256:" + "0" * 64,
        )
        request = tfont.IdentifierResolveRequest(
            key=ir.identifier_index[0][0],
            corpora=("bhsa",),
        )
        assert_problem(
            self,
            "invalid_compiled_ir",
            tfont.identifier_resolve,
            forged_identifier,
            request,
            prerequisites(tfont, forged_identifier),
        )

    def test_forged_parent_tuple_cannot_inherit_reviewed_payload(self):
        ir = reference_ir()
        key, native_rows = ir.native_index[0]
        native = native_rows[0]
        forged_ref = replace(
            native.external_references[0],
            external="https://example.org/entity/forged-parent",
        )
        forged_native = replace(
            native,
            external_references=(forged_ref,) + native.external_references[1:],
        )
        forged_ir = replace(ir, native_index=((key, (forged_native,)),) + ir.native_index[1:])
        identity_key = ir.identity_index[0][0]
        request = tfont.IdentityResolveRequest(
            authority_system=identity_key.authority_system,
            external_entity_id=identity_key.external_entity_id,
            corpora=("bhsa",),
        )
        assert_problem(
            self,
            "invalid_compiled_ir",
            tfont.identity_resolve,
            forged_ir,
            request,
            prerequisites(tfont, forged_ir),
        )

    def test_forged_mapping_payload_fails_closed(self):
        ir = reference_ir()
        key, native_rows = ir.native_index[0]
        native = native_rows[0]
        forged = replace(native, mapping_semantic_payload='{"mapping_id":"forged"}')
        forged_ir = replace(ir, native_index=((key, (forged,)),) + ir.native_index[1:])
        identity_key = ir.identity_index[0][0]
        request = tfont.IdentityResolveRequest(
            authority_system=identity_key.authority_system,
            external_entity_id=identity_key.external_entity_id,
            corpora=("bhsa",),
        )
        assert_problem(
            self,
            "invalid_compiled_ir",
            tfont.identity_resolve,
            forged_ir,
            request,
            prerequisites(tfont, forged_ir),
        )


if __name__ == "__main__":
    unittest.main()
