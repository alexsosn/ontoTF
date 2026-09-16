from __future__ import annotations

import unittest

from tfont.production_bundles import PRODUCTION_NOUN_CORPORA, load_production_noun_bundles
from tfont.semantic_ir import compile_semantic_ir
from tfont.semantic_validation import validate_semantic_bundle
from tfont.semantic_resolver import SemanticResolveRequest, SemanticResolutionError
from tfont.semantic_execution import LoadedComponentContext, LoadedCorpusContext, execute_exact_semantic
from tests.i009.test_runtime_red import COMPONENT_DIGESTS, PARENT_DIGESTS, _api, _key


class ProductionExactParentPolicyTests(unittest.TestCase):
    def test_all_production_profiles_explicitly_declare_exact_only(self):
        bundles = load_production_noun_bundles()
        self.assertEqual(len(bundles), 3)
        for corpus_id, bundle in zip(PRODUCTION_NOUN_CORPORA, bundles, strict=True):
            with self.subTest(corpus=corpus_id):
                self.assertEqual(bundle.profile.data['parent_compatibility'], 'exact-only')
                self.assertEqual(
                    compile_semantic_ir((validate_semantic_bundle(bundle),)).variants[0].release_signature.parent_compatibility,
                    'exact-only',
                )

    def test_any_drifted_production_parent_aborts_all_corpora_before_selection(self):
        bundles = load_production_noun_bundles()
        ir = compile_semantic_ir(tuple(validate_semantic_bundle(bundle) for bundle in bundles))
        request = SemanticResolveRequest(key=_key(), corpora=PRODUCTION_NOUN_CORPORA)
        for drifted in PRODUCTION_NOUN_CORPORA:
            apis = {corpus: _api(corpus) for corpus in PRODUCTION_NOUN_CORPORA}
            contexts = tuple(
                LoadedCorpusContext(
                    corpus_id=corpus,
                    parent_manifest_digest=(PARENT_DIGESTS[corpus] if corpus != drifted else 'sha256:' + '0' * 64),
                    components=(LoadedComponentContext(
                        component_id=f'{corpus}-tf',
                        content_digest=COMPONENT_DIGESTS[corpus],
                        api=apis[corpus],
                    ),),
                )
                for corpus in PRODUCTION_NOUN_CORPORA
            )
            with self.subTest(drifted=drifted):
                with self.assertRaises(SemanticResolutionError) as raised:
                    execute_exact_semantic(ir, request, contexts)
                self.assertEqual(raised.exception.problem.category, 'parent_incompatible')
                for api in apis.values():
                    self.assertEqual(api.F.sp.s_calls, 0)
                    self.assertEqual(api.load_calls, 0)
