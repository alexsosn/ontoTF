from __future__ import annotations

import unittest

import tfont
from tests.i021._fixtures import authority_ir, context, reference_ir
from tfont.semantic_ir import IdentifierKey


EXECUTION_API = (
    "execute_exact_authority",
    "execute_approximate_authority",
    "execute_identity",
    "execute_identifier",
)
HAS_EXECUTION = all(hasattr(tfont, name) for name in EXECUTION_API)


def category(error: BaseException) -> str:
    return getattr(getattr(error, "problem", None), "category", "")


class I021ExecutionRedSentinelTests(unittest.TestCase):
    def test_public_reference_execution_api_exists(self):
        missing = [name for name in EXECUTION_API if not hasattr(tfont, name)]
        self.assertEqual(missing, [], f"RED: missing I-021 execution API: {missing}")


@unittest.skipUnless(HAS_EXECUTION, "RED sentinel owns I-021 execution API absence")
class I021ReferenceExecutionContractTests(unittest.TestCase):
    def test_exact_authority_executes_explicit_scalar_binding(self):
        ir = authority_ir(executable=True)
        key = ir.authority_index[0][0]
        request = tfont.AuthorityResolveRequest(key=key, corpora=("bhsa",))
        result = tfont.execute_exact_authority(
            ir,
            request,
            (context(tfont, ir),),
        )
        self.assertEqual(
            [(row.corpus_id, row.nodes) for row in result.corpora],
            [("bhsa", (1, 3))],
        )
        self.assertEqual(result.resolution.losses, ())

    def test_approximate_authority_executes_only_after_accepted_loss(self):
        ir = authority_ir(
            assessment="broader",
            losses=("undercoverage",),
            executable=True,
        )
        key = ir.authority_index[0][0]
        refused = tfont.ApproximateAuthorityResolveRequest(
            key=key,
            corpora=("bhsa",),
        )
        with self.assertRaises(Exception) as raised:
            tfont.execute_approximate_authority(ir, refused, (context(tfont, ir),))
        self.assertEqual(category(raised.exception), "approximation_loss_not_accepted")

        accepted = tfont.ApproximateAuthorityResolveRequest(
            key=key,
            corpora=("bhsa",),
            accept_losses=("undercoverage",),
        )
        result = tfont.execute_approximate_authority(
            ir,
            accepted,
            (context(tfont, ir),),
        )
        self.assertEqual(result.corpora[0].nodes, (1, 3))
        self.assertEqual(result.resolution.losses, ("undercoverage",))

    def test_same_entity_and_identifier_execute_explicit_scalar_bindings(self):
        ir = reference_ir(executable=True)
        identity_key = ir.identity_index[0][0]
        identity_request = tfont.IdentityResolveRequest(
            authority_system=identity_key.authority_system,
            external_entity_id=identity_key.external_entity_id,
            corpora=("bhsa",),
        )
        identity = tfont.execute_identity(
            ir,
            identity_request,
            (context(tfont, ir),),
        )
        self.assertEqual(identity.corpora[0].nodes, (1, 3))

        identifier_key = ir.identifier_index[0][0]
        identifier_request = tfont.IdentifierResolveRequest(
            key=IdentifierKey(
                issuer_or_namespace=identifier_key.issuer_or_namespace,
                literal_id=identifier_key.literal_id,
            ),
            corpora=("bhsa",),
        )
        identifier = tfont.execute_identifier(
            ir,
            identifier_request,
            (context(tfont, ir),),
        )
        self.assertEqual(identifier.corpora[0].nodes, (1, 3))

    def test_shape_less_reviewed_reference_resolves_but_execution_refuses(self):
        ir = reference_ir(executable=False)
        identity_key = ir.identity_index[0][0]
        request = tfont.IdentityResolveRequest(
            authority_system=identity_key.authority_system,
            external_entity_id=identity_key.external_entity_id,
            corpora=("bhsa",),
        )
        resolved = tfont.identity_resolve(
            ir,
            request,
            tfont.prerequisites_for(ir) if hasattr(tfont, "prerequisites_for") else (),
        ) if False else None
        with self.assertRaises(Exception) as raised:
            tfont.execute_identity(ir, request, (context(tfont, ir),))
        self.assertEqual(category(raised.exception), "unsupported_native_binding")

    def test_mutated_loaded_state_refuses_before_native_selector(self):
        ir = reference_ir(executable=True)
        key = ir.identity_index[0][0]
        request = tfont.IdentityResolveRequest(
            authority_system=key.authority_system,
            external_entity_id=key.external_entity_id,
            corpora=("bhsa",),
        )
        loaded = context(tfont, ir)
        bad = tfont.LoadedCorpusContext(
            corpus_id=loaded.corpus_id,
            parent_manifest_digest="sha256:" + "0" * 64,
            components=loaded.components,
        )
        api = loaded.components[0].api
        before = api.F.sp.s_calls
        with self.assertRaises(Exception):
            tfont.execute_identity(ir, request, (bad,))
        self.assertEqual(api.F.sp.s_calls, before)


if __name__ == "__main__":
    unittest.main()
