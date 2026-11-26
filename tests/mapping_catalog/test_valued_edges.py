"""Valued edges are selectors, never whole-edge or individual identity claims."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tfont import MappingCatalog, MappingError, resolve_nodes, resolve_edges
from scripts.pages.scoped_progress import scoped_progress, eligible_progress
from tests.mapping_catalog.test_scoped_progress import inventory


TARGET = "https://example.org/relation"
def catalog_xml(corpus, records):
    return f'<mappings corpus="{corpus}" source="owner/{corpus}" corpusVersion="1">{records}</mappings>'


def edge(feature="choice", value=None, source="word", target="lex", relation="exact", iri=TARGET):
    attributes = dict(kind="edge", feature=feature, relation=relation)
    if value is not None:
        attributes["value"] = value
    if source is not None:
        attributes["from"] = source
    if target is not None:
        attributes["to"] = target
    if iri is not None:
        attributes["target"] = iri
    return "<map " + " ".join(f'{key}="{val}"' for key, val in attributes.items()) + "/>"


class EdgeFeature:
    def __init__(self, data, valued):
        self.data = data
        self.doValues = valued

    def items(self):
        return self.data.items()


class ValuedEdgesTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name)
        self.cat = MappingCatalog(self.directory)

    def put(self, name, records):
        (self.directory / (name + ".xml")).write_text(catalog_xml(name, records))

    def test_exact_lookup_separates_whole_and_valued_selectors(self):
        self.put("demo", edge() + edge(value="yes") + edge(value="no", relation="native-only", iri=None))
        query = dict(kind="edge", feature="choice", from_node="word", to_node="lex", corpus_version="1")
        self.assertIsNone(self.cat.map_native("demo", **query)[0].value)
        self.assertEqual(self.cat.map_native("demo", value="yes", **query)[0].value, "yes")
        self.assertEqual(self.cat.map_native("demo", value="no", **query)[0].relation, "native-only")
        self.assertEqual(self.cat.map_native("demo", value="maybe", **query), ())
        with self.assertRaises(MappingError):
            self.cat.map_native("demo", value="yes", **{**query, "corpus_version": "2"})
        self.assertEqual(len(self.cat.find_by_target(TARGET, kind="edge")), 2)
        self.assertEqual(self.cat.find_by_target(TARGET), ())

    def test_cross_corpus_preserves_edge_value_granularity(self):
        self.put("demo", edge(value="yes"))
        self.put("other", edge("rel") + edge("rel", "Y") + edge("rel", "N", relation="narrower"))
        q = dict(kind="edge", feature="choice", from_node="word", to_node="lex", value="yes")
        matches = self.cat.find_correspondences("demo", "other", **q)
        self.assertEqual([x.destination.value for x in matches], ["Y"])
        self.assertEqual([x.destination.value for x in self.cat.find_across_corpora("demo", **q, include_approximate=True)], ["Y", "N"])

    def test_invalid_empty_value_and_conflicting_duplicates(self):
        for records in (edge(value=""), edge(value="yes") * 2,
                        edge(value="yes") + edge(value="yes", relation="native-only", iri=None)):
            self.put("bad", records)
            with self.assertRaises(MappingError):
                self.cat.load("bad")

    def test_execution_preserves_values_direction_and_zero(self):
        self.put("demo", edge(value="0") + edge() + edge(value="1", relation="narrower"))
        data = {1: {2: 0, 3: 1, 4: None, 5: ""}, 2: {1: 0}, 6: {2: 0}}
        types = {1:"word",2:"lex",3:"lex",4:"lex",5:"lex",6:"word"}
        api = SimpleNamespace(Es=lambda name: EdgeFeature(data, True),
                              F=SimpleNamespace(otype=SimpleNamespace(v=types.get)))
        q = dict(kind="edge", feature="choice", from_node="word", to_node="lex")
        mapping, = self.cat.map_native("demo", value="0", **q)
        self.assertEqual(resolve_edges(api, mapping, corpus_version="1"), ((1, 2), (6, 2)))
        whole, = self.cat.map_native("demo", **q)
        self.assertEqual(resolve_edges(api, whole, corpus_version="1"), ((1, 2), (1, 3), (1, 4), (1, 5), (6, 2)))
        for version in (None, "2"):
            with self.assertRaises(MappingError):
                resolve_edges(api, mapping, corpus_version=version)
        approx, = self.cat.map_native("demo", value="1", **q)
        with self.assertRaises(MappingError):
            resolve_edges(api, approx, corpus_version="1")
        with self.assertRaises(MappingError):
            resolve_nodes(api, mapping, corpus_version="1")
        api.Es = lambda name: EdgeFeature({1: {2}}, False)
        with self.assertRaises(MappingError):
            resolve_edges(api, mapping, corpus_version="1")
        self.assertEqual(resolve_edges(api, whole, corpus_version="1"), ((1, 2),))

    def test_real_tlhdig_edge_dispositions_and_occurrence_counts(self):
        root = Path(__file__).resolve().parents[2]
        import json
        observed = json.loads((root / "docs/research/data/generated/scoped/tlhdig-tf.json").read_text())
        rows = MappingCatalog(root / "src/tfont/mappings").load("tlhdig-tf")
        stats = scoped_progress(rows, observed, "alexsosn/TLHdig-TF", "0.4.0")
        self.assertEqual(stats["edge_values"]["total"], 4)
        # Later source-supported positive targets are allowed without editing
        # this test. Only the observation and reviewed selector coverage matter.
        self.assertEqual(stats["edge_values"]["reviewed"], 4)
        self.assertEqual(stats["edge_values"]["reviewed_occurrences"], 139584)
        self.assertFalse(stats["outside_edge_values"])
        self.assertFalse(stats["unmeasured_edge_values"])
        self.assertEqual({(d["feature"], d["reviewed"]) for d in stats["edge_domains"]},
                         {("joined", 2), ("witness_resolution", 2)})

    def test_cross_version_node_maps_cannot_execute(self):
        self.put("demo", edge(feature="omap@old-new", value="1"))
        mapping, = self.cat.map_native("demo", kind="edge", feature="omap@old-new",
                                         from_node="word", to_node="lex", value="1")
        with self.assertRaisesRegex(MappingError, "cross-version"):
            resolve_edges(None, mapping, corpus_version="1")

    def test_dashboard_accounts_value_without_whole_edge_credit(self):
        self.put("demo", edge(value="yes") + edge(value="absent") + edge(value="yes", source="lex", target="word"))
        rows = self.cat.load("demo")
        s = scoped_progress(rows, inventory(), "owner/demo", "1")
        self.assertEqual(s["edge_pairs"]["positive"], 0)
        self.assertEqual(s["edge_values"]["positive"], 1)
        self.assertEqual(s["edge_values"]["positive_occurrences"], 2)
        self.assertEqual(s["outside_edge_values"], [["choice", "absent", "word", "lex"], ["choice", "yes", "lex", "word"]])
        self.assertEqual(s["edge_domains"][0]["positive"], 1)
        self.assertEqual(s["edge_domains"][0]["unreviewed_values"], [])
        policy = {"OLiA": [{"kind":"edge_value", "features":["choice"]}]}
        p = eligible_progress(rows, inventory(), policy, "1")
        self.assertEqual(p["OLiA"]["other_target"], 1)


if __name__ == "__main__":
    unittest.main()
