from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "research" / "r005_inventory.py"
SPEC = importlib.util.spec_from_file_location("r005_inventory", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FakeNodeFeature:
    def __init__(self, data, meta=None, slot_type=None):
        self.data = data
        self.meta = meta or {}
        self.slotType = slot_type

    def items(self):
        return self.data.items()

    def v(self, node):
        return self.data.get(node)


class FakeEdgeFeature:
    def __init__(self, data, *, valued=False, meta=None):
        self.data = data
        self.doValues = valued
        self.meta = meta or {}

    def items(self):
        return self.data.items()


class Namespace:
    pass


class FakeApi:
    def __init__(self):
        self.F = Namespace()
        self.E = Namespace()
        self.F.otype = FakeNodeFeature(
            {
                1: "word",
                2: "word",
                3: "sign",
                4: "sign",
                5: "line",
            },
            {"description": "object type", "valueType": "str"},
            slot_type="sign",
        )
        # The empty string on node 3 models a dense TF record with no semantic
        # feature value. It must not make `pos` look applicable to signs.
        self.F.pos = FakeNodeFeature(
            {1: "noun", 2: "verb", 3: ""},
            {"description": "part of speech", "valueType": "str"},
        )
        self.F.form = FakeNodeFeature(
            {1: "alpha", 2: "beta", 3: "gamma", 4: "delta"},
            {"description": "surface form", "valueType": "str"},
        )
        self.E.parent = FakeEdgeFeature(
            {1: {5}, 2: {5}},
            meta={"description": "word to line", "valueType": "str"},
        )
        self.E.selected = FakeEdgeFeature(
            {1: {2: "1", 3: "1bR"}},
            valued=True,
            meta={"description": "selected analysis", "valueType": "str"},
        )

    def Fall(self, warp=False):
        self.assert_false(warp)
        return ["form", "pos"]

    def Eall(self, warp=False):
        self.assert_false(warp)
        return ["parent", "selected"]

    @staticmethod
    def assert_false(value):
        if value:
            raise AssertionError("test fake expects warp=False")

    def Fs(self, name):
        return getattr(self.F, name)

    def Es(self, name):
        return getattr(self.E, name)


class InventoryTests(unittest.TestCase):
    def test_small_observed_domain_is_not_declared_closed(self):
        got = MODULE.summarize_values(["f", "m", "f"], small_domain_limit=8)
        self.assertEqual(got["domain_observation"], "observed_small_domain")
        self.assertEqual(got["observed_values"], ["f", "m"])
        self.assertEqual(got["observed_unique_count"], 2)
        self.assertEqual(got["observation_count"], 3)
        self.assertEqual(got["raw_observation_count"], 3)
        self.assertEqual(got["empty_observation_count"], 0)

    def test_empty_and_none_records_are_not_domain_members(self):
        got = MODULE.summarize_values(["", None, "f", "m", "f"], small_domain_limit=8)
        self.assertEqual(got["observed_values"], ["f", "m"])
        self.assertEqual(got["observed_unique_count"], 2)
        self.assertEqual(got["observation_count"], 3)
        self.assertEqual(got["raw_observation_count"], 5)
        self.assertEqual(got["empty_observation_count"], 2)

    def test_large_domain_is_sampled_not_exhaustively_dumped(self):
        got = MODULE.summarize_values(
            [f"v{i}" for i in range(10)], small_domain_limit=3, sample_limit=4
        )
        self.assertEqual(got["domain_observation"], "open_or_large_observed_domain")
        self.assertEqual(got["observed_unique_count"], 10)
        self.assertNotIn("observed_values", got)
        self.assertEqual(len(got["sample_values"]), 4)

    def test_node_inventory_records_metadata_types_and_observed_domain(self):
        got = MODULE.inventory_api(FakeApi(), small_domain_limit=3)
        pos = got["node_features"]["pos"]
        self.assertEqual(pos["metadata"]["description"], "part of speech")
        self.assertEqual(pos["applies_to"], ["word"])
        self.assertEqual(pos["observed_values"], ["noun", "verb"])
        self.assertEqual(pos["nodes_with_value"], 2)
        self.assertEqual(pos["node_records_seen"], 3)
        self.assertEqual(pos["empty_observation_count"], 1)
        self.assertEqual(got["slot_type"], "sign")

    def test_open_node_domain_is_identified_from_actual_values(self):
        got = MODULE.inventory_api(FakeApi(), small_domain_limit=3)
        form = got["node_features"]["form"]
        self.assertEqual(form["domain_observation"], "open_or_large_observed_domain")
        self.assertEqual(form["observed_unique_count"], 4)

    def test_unvalued_edge_records_direction_and_node_types(self):
        got = MODULE.inventory_api(FakeApi(), small_domain_limit=8)
        parent = got["edge_features"]["parent"]
        self.assertFalse(parent["valued"])
        self.assertEqual(parent["source_types"], ["word"])
        self.assertEqual(parent["target_types"], ["line"])
        self.assertEqual(parent["edge_count"], 2)

    def test_valued_edge_records_actual_edge_value_domain(self):
        got = MODULE.inventory_api(FakeApi(), small_domain_limit=8)
        selected = got["edge_features"]["selected"]
        self.assertTrue(selected["valued"])
        self.assertEqual(selected["source_types"], ["word"])
        self.assertEqual(selected["target_types"], ["sign", "word"])
        self.assertEqual(selected["observed_values"], ["1", "1bR"])
        self.assertEqual(selected["edge_count"], 2)

    def test_digest_ignores_directories_whose_names_end_in_dot_tf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "otype.tf").write_text("@node\n1\tword\n", encoding="utf-8")
            expected = MODULE.digest_tf_files(root)
            (root / ".tf").mkdir()
            self.assertEqual(MODULE.digest_tf_files(root), expected)

    def test_scoped_domains_do_not_cross_multiply_node_types(self):
        api = FakeApi()
        api.F.pos.data = {1: "noun", 2: "verb", 3: "noun", 4: "", 5: None}
        got = MODULE.inventory_scoped_api(api, node_value_features={"pos"})
        pos = got["node_features"]["pos"]
        self.assertEqual(pos["scopes"]["word"]["values"], {"noun": 1, "verb": 1})
        self.assertEqual(pos["scopes"]["sign"]["values"], {"noun": 1})
        self.assertNotIn("line", pos["scopes"])
        self.assertEqual(pos["empty_records"], 2)
        self.assertEqual(got["node_types"], {"word": 2, "sign": 2, "line": 1})
        self.assertEqual(got["node_features"]["form"]["scopes"]["word"]["count"], 2)
        self.assertNotIn("values", got["node_features"]["form"]["scopes"]["word"])

    def test_scoped_edges_keep_actual_pairs_and_missing_values(self):
        api = FakeApi()
        api.E.selected.data = {1: {2: "x", 3: ""}, 3: {5: "y"}, 4: {5: None}}
        got = MODULE.inventory_scoped_api(api, edge_value_features={"selected"})
        edges = got["edge_features"]["selected"]["pairs"]
        pairs = {(e["from"], e["to"]): e for e in edges}
        self.assertEqual(set(pairs), {("word", "word"), ("word", "sign"), ("sign", "line")})
        self.assertEqual(pairs["word", "word"]["values"], {"x": 1})
        self.assertEqual(pairs["word", "sign"]["values"], {})
        self.assertEqual(pairs["word", "sign"]["empty_values"], 1)
        self.assertEqual(pairs["sign", "line"]["values"], {"y": 1})
        self.assertEqual(pairs["sign", "line"]["count"], 2)
        self.assertEqual(pairs["sign", "line"]["empty_values"], 1)

    def test_scoped_domain_overflow_is_explicit_and_never_a_sample(self):
        got = MODULE.inventory_scoped_api(FakeApi(), node_value_features={"form"},
                                          domain_limit=1)
        word = got["node_features"]["form"]["scopes"]["word"]
        self.assertEqual(word["count"], 2)
        self.assertEqual(word["value_domain"], "overflow")
        self.assertNotIn("values", word)

    def test_scoped_numeric_zero_preserved_and_unknown_nodes_fail(self):
        api = FakeApi()
        api.F.pos.data = {1: 0, 2: 1}
        got = MODULE.inventory_scoped_api(api, node_value_features={"pos"})
        self.assertEqual(got["node_features"]["pos"]["scopes"]["word"]["values"],
                         {"0": 1, "1": 1})
        api.F.pos.data[99] = "unknown"
        with self.assertRaisesRegex(ValueError, "node type"):
            MODULE.inventory_scoped_api(api)

    def test_cross_version_node_map_is_not_a_local_edge(self):
        api = FakeApi()
        api.E.__dict__["omap@old-new"] = FakeEdgeFeature({99: {1: 1}}, valued=True)
        api.Eall = lambda warp=False: ["parent", "selected", "omap@old-new"]
        got = MODULE.inventory_scoped_api(api)
        edge = got["edge_features"]["omap@old-new"]
        self.assertEqual(edge["scope_status"], "cross_version")
        self.assertEqual(edge["edge_count"], 1)
        self.assertNotIn("pairs", edge)
        with self.assertRaisesRegex(ValueError, "cross.version"):
            MODULE.inventory_scoped_api(api, edge_value_features={"omap@old-new"})

    def test_scoped_identity_distinguishes_catalog_release_and_tf_version(self):
        got = MODULE.scoped_identity(corpus_id="oracc", repository="owner/repo",
                                     revision="abc", tf_version="0.4.0",
                                     catalog_version="1.0.0", archive_sha256="a"*64)
        self.assertEqual(got["tf_version"], "0.4.0")
        self.assertEqual(got["catalog_version"], "1.0.0")
        self.assertEqual(got["archive_sha256"], "a"*64)
        default = MODULE.scoped_identity(corpus_id="bhsa", repository="ETCBC/bhsa",
                                         revision="abc", tf_version="2021")
        self.assertEqual(default["catalog_version"], "2021")

    def test_scoped_allowlist_typo_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            MODULE.inventory_scoped_api(FakeApi(), node_value_features={"missing"})
        with self.assertRaisesRegex(ValueError, "parent"):
            MODULE.inventory_scoped_api(FakeApi(), edge_value_features={"parent"})


if __name__ == "__main__":
    unittest.main()
