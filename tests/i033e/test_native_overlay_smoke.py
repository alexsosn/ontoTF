"""I-033F TDD RED: ten REAL source-bound candidate mappings, loaded-TF smoke.

An in-memory TF-like API tests behavior, NOT real BHSA node statistics.
"""
from __future__ import annotations

import copy
import unittest

from tests.i033e.test_overlay_handoff import cohort, assemble
from tfont.parent_identity import parent_manifest_digest
from tfont.release_registry import load_profile
from tfont.semantic_execution import LoadedComponentContext, LoadedCorpusContext
from tfont.native_overlay_smoke import inspect_native_overlay, NativeOverlaySmokeError


class _Otype:
    def __init__(self, nodes):
        self.nodes = nodes
        self.iterations = 0

    def s(self, node_type):
        if node_type != "word":
            raise AssertionError("unexpected node type")
        self.iterations += 1
        return iter(self.nodes)


class _Sp:
    def __init__(self, values):
        self.values = values
        self.calls = 0

    def v(self, node):
        self.calls += 1
        value = self.values[node]
        if isinstance(value, Exception):
            raise value
        return value


class _FeatureNamespace:
    def __init__(self, nodes, values):
        self.otype = _Otype(nodes)
        self.sp = _Sp(values)


class _API:
    def __init__(self, nodes, values, loaded=("otype", "sp")):
        self.F = _FeatureNamespace(nodes, values)
        self.loaded = loaded

    def Fall(self):
        return self.loaded


class NativeOverlaySmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger, cls.source_reader, cls.packet, cls.observation = cohort()
        cls.pack = assemble(cls.ledger, cls.source_reader, cls.packet, cls.observation)

    @staticmethod
    def context(corpus, api, *, parent=None, component=None):
        base = load_profile(corpus)
        source = base.expected_parent_manifest.data
        item, = source["components"]
        loaded_component = LoadedComponentContext(
            item["component_id"], component if component is not None else item["content_digest"], api
        )
        return LoadedCorpusContext(
            corpus_id=corpus,
            parent_manifest_digest=parent if parent is not None else parent_manifest_digest(source),
            components=(loaded_component,),
        )

    def test_real_source_candidate_bhsa_native_selectors_scan_once(self):
        values = {1:"art",2:"prep",3:"art",4:"conj",5:"prps",6:"unknown",7:None,8:"inrg"}
        api = _API(range(1,9),values)
        before = copy.deepcopy(self.pack)
        result = inspect_native_overlay(self.pack,self.context("bhsa",api))
        self.assertEqual(self.pack,before)
        self.assertEqual(result["contract"],"tfont-native-overlay-smoke-v1")
        self.assertEqual(result["authority"],"diagnostic-only-not-a-release")
        self.assertEqual(result["corpus_id"],"bhsa")
        self.assertEqual(result["pack_digest"],self.pack["content_digest"])
        self.assertEqual(result["shared_target_count"],0)
        self.assertEqual(result["scanned_words"],8)
        self.assertEqual(len(result["selectors"]),9)
        self.assertEqual(api.F.otype.iterations,1)
        self.assertEqual(api.F.sp.calls,8)
        by_value={row["value"]:row for row in result["selectors"]}
        self.assertEqual(by_value["art"]["count"],2)
        self.assertEqual(by_value["art"]["sample_nodes"],[1,3])
        self.assertEqual(by_value["inrg"]["count"],1)
        self.assertEqual(by_value["inrg"]["sample_nodes"],[8])
        self.assertEqual(by_value["prde"]["count"],0)
        self.assertEqual(by_value["prde"]["sample_nodes"],[])
        self.assertTrue(all(row["native_state"]=="native-only"
                            and "ontology_target" not in row
                            for row in result["selectors"]))
        self.assertEqual(result,inspect_native_overlay(self.pack,self.context("bhsa",_API(range(1,9),values))))

    def test_syriac_general_pronoun_does_not_infer_bhsa_subtypes(self):
        api=_API((2,4,6,8),{2:"pron",4:"pron",6:"verb",8:None})
        result=inspect_native_overlay(self.pack,self.context("syriac",api))
        self.assertEqual(len(result["selectors"]),1)
        self.assertEqual(result["selectors"][0]["value"],"pron")
        self.assertEqual(result["selectors"][0]["count"],2)
        self.assertEqual(result["selectors"][0]["sample_nodes"],[2,4])
        self.assertEqual(result["shared_target_count"],0)

    def test_wrong_corpus_parent_or_component_digest_fail_closed(self):
        api=_API((1,),{1:"art"})
        base=self.context("bhsa",api)
        defects=[
            LoadedCorpusContext("syriac",base.parent_manifest_digest,base.components),
            self.context("bhsa",api,parent="sha256:"+"0"*64),
            self.context("bhsa",api,component="sha256:"+"f"*64),
            LoadedCorpusContext("bhsa",base.parent_manifest_digest,()),
            LoadedCorpusContext("bhsa",base.parent_manifest_digest,(base.components[0],base.components[0])),
        ]
        for i,context in enumerate(defects):
            with self.subTest(case=i),self.assertRaises(NativeOverlaySmokeError):
                inspect_native_overlay(self.pack,context)

    def test_absent_sp_or_bad_tf_values_and_node_order_fail_closed(self):
        cases=[
            _API((1,),{1:"art"},loaded=("otype",)),
            _API((1,),{1:"art"},loaded=None),
            _API((1,),{1:RuntimeError("feature unavailable")}),
            _API((1,),{1:11}),
            _API((2,1),{1:"art",2:"prep"}),
            _API((1,1),{1:"art"}),
            _API((0,),{0:"art"}),
            _API((),{}),
            _API((1,),{}),
        ]
        for i,api in enumerate(cases):
            with self.subTest(case=i),self.assertRaises(NativeOverlaySmokeError):
                inspect_native_overlay(self.pack,self.context("bhsa",api))

    def test_unsealed_pack_tamper_or_positive_shared_target_fails(self):
        changed=copy.deepcopy(self.pack)
        changed["corpora"][0]["mappings"][0]["native_binding"]["value"]="wrong"
        with self.assertRaises((NativeOverlaySmokeError,ValueError)):
            inspect_native_overlay(changed,self.context("bhsa",_API((1,),{1:"art"})))
        positive=copy.deepcopy(self.pack)
        positive["counts"]["exact"]=1
        with self.assertRaises((NativeOverlaySmokeError,ValueError)):
            inspect_native_overlay(positive,self.context("bhsa",_API((1,),{1:"art"})))

    def test_no_requested_corpus_or_non_context_rejected(self):
        api=_API((1,),{1:"art"})
        with self.assertRaises(NativeOverlaySmokeError):
            inspect_native_overlay(self.pack,object())
        with self.assertRaises(NativeOverlaySmokeError):
            inspect_native_overlay(self.pack,self.context("extrabiblical",api))


if __name__=="__main__":
    unittest.main()
