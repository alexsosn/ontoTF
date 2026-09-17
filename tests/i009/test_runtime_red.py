from __future__ import annotations

import importlib
import importlib.util
import unittest

from tests.i008._fixtures import FakeLoadedApi
from tfont.semantic_execution import LoadedComponentContext, LoadedCorpusContext, execute_exact_semantic
from tfont.semantic_ir import SemanticKey, compile_semantic_ir
from tfont.semantic_resolver import SemanticResolveRequest, SemanticResolutionError
from tfont.semantic_validation import validate_semantic_bundle

OLIA_NOUN = "http://purl.org/olia/olia.owl#Noun"
PARENT_DIGESTS = {
    "bhsa": "sha256:cc2c65cd79b2cb7faf1a34b94feb3cc2d3291e7064cbec942c53b0e05f1b0837",
    "syriac": "sha256:afb5a826b9ebe10cdd4ca23d96e00ee7bf677d06496cfcfcee6bb37d2ecff6c4",
    "extrabiblical": "sha256:d39fe3f4848cadb14ae5ef453a5150ea6281b2874728566198d7de10d72bec4a",
}
COMPONENT_DIGESTS = {
    "bhsa": "sha256:5178414e293a743fc98768abcab5b9cb268e14ad56fd2cfbac544ae2869d2e6f",
    "syriac": "sha256:54a2596d5525f3afb34db0a89d5511e6b8471ce4a93fae4825b22f0945ab62ef",
    "extrabiblical": "sha256:d0ca9bdf90bfdefe19861c2c68e91071650ed511b8a79270490238b30274aee0",
}


def _key() -> SemanticKey:
    return SemanticKey(
        profile_id="linguistic",
        capability_id="linguistic.part-of-speech",
        target=OLIA_NOUN,
        formal_kind="class",
        semantic_role="annotation-value",
    )


def _module(testcase: unittest.TestCase):
    spec = importlib.util.find_spec("tfont.production_bundles")
    testcase.assertIsNotNone(spec, "I-009 production bundle module is absent")
    return importlib.import_module("tfont.production_bundles")


def _compiled(testcase: unittest.TestCase):
    module = _module(testcase)
    bundles = module.load_production_noun_bundles()
    validated = tuple(validate_semantic_bundle(bundle) for bundle in bundles)
    return module, compile_semantic_ir(validated)


def _api(corpus_id: str, *, missing_selected: bool = False) -> FakeLoadedApi:
    if corpus_id == "bhsa":
        values = {1: "subs", 2: "nmpr", 3: "verb", 4: "nmpr"}
        node_types = {1: "word", 2: "word", 3: "word", 4: "lex"}
        if missing_selected:
            values[2] = "verb"
    elif corpus_id == "syriac":
        # Common and proper nouns are both encoded under sp=subs in this parent.
        values = {11: "subs", 12: "subs", 13: "verb"}
        node_types = {11: "word", 12: "word", 13: "word"}
        if missing_selected:
            values[11] = "verb"
            values[12] = "verb"
    elif corpus_id == "extrabiblical":
        values = {21: "nmpr", 22: "subs", 23: "verb", 24: "subs"}
        node_types = {21: "word", 22: "word", 23: "word", 24: "lex"}
        if missing_selected:
            values[21] = "verb"
    else:
        raise AssertionError(f"unexpected corpus fixture: {corpus_id}")
    return FakeLoadedApi(values=values, node_types=node_types)


def _context(corpus_id: str, api: FakeLoadedApi, *, wrong_parent: bool = False) -> LoadedCorpusContext:
    parent = PARENT_DIGESTS[corpus_id]
    if wrong_parent:
        parent = "sha256:" + "0" * 64
    return LoadedCorpusContext(
        corpus_id=corpus_id,
        parent_manifest_digest=parent,
        components=(
            LoadedComponentContext(
                component_id=f"{corpus_id}-tf",
                content_digest=COMPONENT_DIGESTS[corpus_id],
                api=api,
            ),
        ),
    )


class I009ProductionRuntimeTests(unittest.TestCase):
    def test_one_semantic_request_executes_across_three_exact_loaded_parents(self):
        module, ir = _compiled(self)
        apis = {corpus_id: _api(corpus_id) for corpus_id in module.PRODUCTION_NOUN_CORPORA}
        contexts = tuple(_context(corpus_id, apis[corpus_id]) for corpus_id in module.PRODUCTION_NOUN_CORPORA)
        request = SemanticResolveRequest(key=_key(), corpora=module.PRODUCTION_NOUN_CORPORA)

        result = execute_exact_semantic(ir, request, contexts)
        self.assertEqual(
            tuple(row.corpus_id for row in result.corpora),
            tuple(sorted(module.PRODUCTION_NOUN_CORPORA)),
        )
        nodes = {row.corpus_id: row.nodes for row in result.corpora}
        self.assertEqual(nodes["bhsa"], (1, 2))
        self.assertEqual(nodes["syriac"], (11, 12))
        self.assertEqual(nodes["extrabiblical"], (21, 22))
        for api in apis.values():
            self.assertEqual(api.load_calls, 0)

    def test_wrong_exact_parent_fails_closed_before_native_selection(self):
        module, ir = _compiled(self)
        apis = {corpus_id: _api(corpus_id) for corpus_id in module.PRODUCTION_NOUN_CORPORA}
        contexts = tuple(
            _context(corpus_id, apis[corpus_id], wrong_parent=(corpus_id == "bhsa"))
            for corpus_id in module.PRODUCTION_NOUN_CORPORA
        )
        request = SemanticResolveRequest(key=_key(), corpora=module.PRODUCTION_NOUN_CORPORA)
        with self.assertRaises(SemanticResolutionError) as raised:
            execute_exact_semantic(ir, request, contexts)
        self.assertEqual(raised.exception.problem.category, "parent_incompatible")
        self.assertEqual(apis["bhsa"].F.sp.s_calls, 0)

    def test_missing_set_value_fails_runtime_authorization(self):
        module, ir = _compiled(self)
        apis = {corpus_id: _api(corpus_id) for corpus_id in module.PRODUCTION_NOUN_CORPORA}
        apis["extrabiblical"] = _api("extrabiblical", missing_selected=True)
        contexts = tuple(_context(corpus_id, apis[corpus_id]) for corpus_id in module.PRODUCTION_NOUN_CORPORA)
        request = SemanticResolveRequest(key=_key(), corpora=module.PRODUCTION_NOUN_CORPORA)
        with self.assertRaises(SemanticResolutionError) as raised:
            execute_exact_semantic(ir, request, contexts)
        self.assertEqual(raised.exception.problem.category, "parent_incompatible")

    def test_missing_syriac_subs_fails_runtime_authorization(self):
        module, ir = _compiled(self)
        apis = {corpus_id: _api(corpus_id) for corpus_id in module.PRODUCTION_NOUN_CORPORA}
        apis["syriac"] = _api("syriac", missing_selected=True)
        contexts = tuple(_context(corpus_id, apis[corpus_id]) for corpus_id in module.PRODUCTION_NOUN_CORPORA)
        request = SemanticResolveRequest(key=_key(), corpora=module.PRODUCTION_NOUN_CORPORA)
        with self.assertRaises(SemanticResolutionError) as raised:
            execute_exact_semantic(ir, request, contexts)
        self.assertEqual(raised.exception.problem.category, "parent_incompatible")


if __name__ == "__main__":
    unittest.main()
