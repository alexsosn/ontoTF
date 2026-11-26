"""Current and historical source versions remain separately executable."""
import json
from pathlib import Path
import unittest

from tfont.xml_mappings import MappingCatalog, MappingError, resolve_nodes
from scripts.pages.build_progress import build_report

ROOT = Path(__file__).resolve().parents[2]
CASES = (
    ("syriac", "0.9", "0.92", "0b6ded2b369c7d81589a98c92325290e24b20af6", 407319),
    ("pseudepigrapha", "1.0", "1.1", "39bd9fb895d1201e9cd9260170512fd8c399a3ac", 922922),
)

class CurrentCorpusVersionsTests(unittest.TestCase):
    def test_explicit_version_selectors_and_source_evidence(self):
        c = MappingCatalog()
        for corpus, old, current, pin, words in CASES:
            with self.subTest(corpus=corpus):
                history = [r for r in c.load(corpus) if r.corpus_version == old]
                rows = [r for r in c.load(corpus) if r.corpus_version == current]
                self.assertTrue(history)
                self.assertEqual({(r.selector, r.relation, r.target) for r in history},
                                 {(r.selector, r.relation, r.target) for r in rows})
                self.assertTrue(all(pin in (r.evidence or "") for r in rows))
                for r in rows:
                    query = dict(kind=r.kind, node=r.node, feature=r.feature,
                                 value=r.value, from_node=r.from_node, to_node=r.to_node)
                    self.assertIn(r, c.map_native(corpus, corpus_version=current, **query))
                    with self.assertRaisesRegex(MappingError, "multiple source versions"):
                        c.map_native(corpus, **query)
                    with self.assertRaises(MappingError):
                        c.map_native(corpus, corpus_version="unknown", **query)
                inventory = json.loads((ROOT / "docs/research/data/generated/scoped" /
                                        (corpus + ".json")).read_text())
                self.assertEqual(inventory["revision"], pin)
                self.assertEqual(inventory["tf_version"], current)
                self.assertEqual(inventory["node_types"]["word"], words)

    def test_versioned_real_report(self):
        report = build_report(ROOT, "a"*40)
        by_name = {r["corpus"]: r for r in report["corpora"]}
        for corpus, old, current, pin, words in CASES:
            row = by_name[corpus]
            self.assertEqual(row["version"], current)
            self.assertEqual(row["scoped"]["revision"], pin)
            self.assertIsNotNone(row["schema_total"])
            self.assertIsNotNone(row["applicability"])
            status = report["source_status"]["corpora"][corpus]
            self.assertEqual((status["checked_tf_version"], status["checked_revision"], status["status"]),
                             (current, pin, "current"))

    def test_current_qualified_and_native_only_are_not_promoted(self):
        c = MappingCatalog()
        row, = c.map_native("syriac", node="word", feature="ls", value="demo", corpus_version="0.92")
        self.assertEqual(row.relation, "narrower")
        with self.assertRaises(MappingError):
            resolve_nodes(object(), row, corpus_version="0.92")
        row, = c.map_native("pseudepigrapha", kind="node", node="word", corpus_version="1.1")
        self.assertEqual(row.relation, "native-only")
        self.assertEqual(c.find_correspondences("pseudepigrapha", "bhsa",
                         kind="node", node="word", source_version="1.1"), ())

    def test_current_cross_corpus_discovery_keeps_version_identity(self):
        c = MappingCatalog()
        for version in ("0.9", "0.92"):
            rows = c.find_correspondences("syriac", "bhsa", node="word",
                                          feature="sp", value="subs",
                                          source_version=version)
            self.assertTrue(rows)
            self.assertTrue(all(r.source.corpus_version == version and r.scope == "category"
                                for r in rows))
            reverse = c.find_correspondences("bhsa", "syriac", node="word",
                                             feature="sp", value="subs",
                                             target_version=version)
            self.assertTrue(reverse)
            self.assertTrue(all(r.destination.corpus_version == version for r in reverse))
        for version in ("1.0", "1.1"):
            rows = c.find_correspondences("pseudepigrapha", "peshitta", kind="node",
                                          node="book", source_version=version)
            self.assertTrue(rows)
            self.assertTrue(all(r.source.corpus_version == version and r.scope == "category"
                                for r in rows))
