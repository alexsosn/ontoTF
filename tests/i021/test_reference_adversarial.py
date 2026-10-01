from __future__ import annotations

import hashlib
import inspect
import json
import unittest
from dataclasses import replace

import tfont
from tests.i005._fixtures import (
    catalogue_reference,
    entity_identity_reference,
    locator_reference,
    noun_sources,
    provenance_reference,
    source_bundle,
    validate_structural_sources,
)
from tests.i020._fixtures import noun_semantic_key
from tests.i021._fixtures import (
    authority_ir,
    prerequisites,
    reference_ir,
    replace_identifier_row,
    replace_identity_row,
)
from tfont.semantic_ir import (
    IdentifierKey,
    IdentityKey,
    SemanticKey,
    compile_semantic_ir,
)
from tfont.semantic_validation import validate_semantic_bundle


def category(error: BaseException) -> str:
    return getattr(getattr(error, "problem", None), "category", "")


def assert_problem(testcase, expected, fn, *args):
    with testcase.assertRaises(Exception) as raised:
        fn(*args)
    testcase.assertEqual(category(raised.exception), expected)


def explanation_reference_ir():
    refs = [
        entity_identity_reference("bhsa"),
        catalogue_reference("bhsa"),
        provenance_reference("bhsa"),
        locator_reference("bhsa"),
    ]
    sources = noun_sources(
        "bhsa",
        parent_char="d",
        external_references=refs,
    )
    validate_structural_sources(sources)
    return compile_semantic_ir((validate_semantic_bundle(source_bundle(sources)),))


class I021ReferenceAdversarialTests(unittest.TestCase):
    def test_reviewed_mapping_payload_is_canonical_and_digest_bound(self):
        ir = reference_ir()
        parent = next(row for _key, rows in ir.native_index for row in rows)
        payload = parent.mapping_semantic_payload
        self.assertIsInstance(payload, str)
        decoded = json.loads(payload)
        self.assertEqual(
            payload,
            json.dumps(decoded, separators=(",", ":"), sort_keys=True),
        )
        digest = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(digest, parent.mapping_semantic_digest)
        variant = ir.variants[0]
        self.assertIn(
            (parent.mapping_id, parent.mapping_semantic_digest),
            variant.release_signature.mapping_digests,
        )
        self.assertIn(
            (parent.mapping_id, parent.mapping_review),
            variant.release_signature.mapping_reviews,
        )

    def test_authority_value_never_becomes_semantic_pivot_by_uri_shape(self):
        ir = authority_ir()
        authority_key = ir.authority_index[0][0]
        self.assertFalse(
            any(
                key.target == authority_key.authority_resource
                for key, _rows in ir.semantic_index
            )
        )
        semantic_key = SemanticKey(
            profile_id="linguistic",
            capability_id="linguistic.part-of-speech",
            target=authority_key.authority_resource,
            formal_kind=authority_key.formal_kind,
            semantic_role=authority_key.semantic_role,
        )
        request = tfont.SemanticResolveRequest(
            key=semantic_key,
            corpora=("bhsa",),
        )
        with self.assertRaises(tfont.SemanticResolutionError):
            tfont.semantic_resolve(ir, request, prerequisites(tfont, ir))

    def test_related_authority_is_non_substitutive_in_both_modes(self):
        ir = authority_ir(assessment="related")
        key = ir.authority_index[0][0]
        exact = tfont.AuthorityResolveRequest(key=key, corpora=("bhsa",))
        assert_problem(
            self,
            "non_substitutive_authority_mapping",
            tfont.authority_resolve_exact,
            ir,
            exact,
            prerequisites(tfont, ir),
        )
        approximate = tfont.ApproximateAuthorityResolveRequest(
            key=key,
            corpora=("bhsa",),
            accept_losses=("undercoverage", "overcoverage"),
        )
        assert_problem(
            self,
            "non_substitutive_authority_mapping",
            tfont.authority_resolve_approximate,
            ir,
            approximate,
            prerequisites(tfont, ir),
        )

    def test_forged_identity_strength_and_native_binding_fail_closed(self):
        ir = reference_ir()
        key = ir.identity_index[0][0]
        request = tfont.IdentityResolveRequest(
            authority_system=key.authority_system,
            external_entity_id=key.external_entity_id,
            corpora=("bhsa",),
        )
        forged_strength = replace_identity_row(
            ir,
            identity_strength="probable-same-entity",
        )
        assert_problem(
            self,
            "invalid_compiled_ir",
            tfont.identity_resolve,
            forged_strength,
            request,
            prerequisites(tfont, forged_strength),
        )
        forged_binding = replace_identity_row(
            ir,
            native_binding_identity="sha256:" + "0" * 64,
        )
        assert_problem(
            self,
            "invalid_compiled_ir",
            tfont.identity_resolve,
            forged_binding,
            request,
            prerequisites(tfont, forged_binding),
        )

    def test_forged_identifier_issuer_and_literal_fail_closed(self):
        ir = reference_ir(issuer="issuer-A", literal_id="123")
        key = ir.identifier_index[0][0]
        request = tfont.IdentifierResolveRequest(key=key, corpora=("bhsa",))
        for changes in (
            {"issuer_or_namespace": "issuer-B"},
            {"external": "124"},
            {"native_binding_identity": "sha256:" + "0" * 64},
        ):
            with self.subTest(changes=changes):
                forged = replace_identifier_row(ir, **changes)
                assert_problem(
                    self,
                    "invalid_compiled_ir",
                    tfont.identifier_resolve,
                    forged,
                    request,
                    prerequisites(tfont, forged),
                )

    def test_explanation_only_rows_cannot_be_injected_into_reverse_indexes(self):
        ir = explanation_reference_ir()
        parent = next(row for _key, rows in ir.native_index for row in rows)
        provenance = next(
            row for row in parent.external_references
            if row.reference_kind == "provenance-source"
        )
        locator = next(
            row for row in parent.external_references
            if row.reference_kind == "locator"
        )

        identity_key = IdentityKey(
            authority_system="fixture-authority",
            external_entity_id=provenance.external,
            identity_strength="same-entity",
        )
        forged_identity = replace(
            ir,
            identity_index=((identity_key, (provenance,)),) + ir.identity_index,
        )
        identity_request = tfont.IdentityResolveRequest(
            authority_system=identity_key.authority_system,
            external_entity_id=identity_key.external_entity_id,
            corpora=("bhsa",),
        )
        assert_problem(
            self,
            "invalid_compiled_ir",
            tfont.identity_resolve,
            forged_identity,
            identity_request,
            prerequisites(tfont, forged_identity),
        )

        identifier_key = IdentifierKey(
            issuer_or_namespace="fixture-catalogue",
            literal_id=locator.external,
        )
        forged_identifier = replace(
            ir,
            identifier_index=((identifier_key, (locator,)),) + ir.identifier_index,
        )
        identifier_request = tfont.IdentifierResolveRequest(
            key=identifier_key,
            corpora=("bhsa",),
        )
        assert_problem(
            self,
            "invalid_compiled_ir",
            tfont.identifier_resolve,
            forged_identifier,
            identifier_request,
            prerequisites(tfont, forged_identifier),
        )

    def test_public_reference_executors_have_no_caller_plan_parameter(self):
        for fn in (
            tfont.execute_exact_authority,
            tfont.execute_approximate_authority,
            tfont.execute_identity,
            tfont.execute_identifier,
        ):
            with self.subTest(fn=fn.__name__):
                self.assertEqual(
                    tuple(inspect.signature(fn).parameters),
                    ("ir", "request", "contexts"),
                )


if __name__ == "__main__":
    unittest.main()
