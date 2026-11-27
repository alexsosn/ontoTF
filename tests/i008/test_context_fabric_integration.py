from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import tfont
from tests.i008._fixtures import compiled_executable_noun_ir, loaded_context, request

try:
    from cfabric.core import Fabric
except ImportError:  # pragma: no cover - exercised only outside integration job
    Fabric = None


@unittest.skipUnless(Fabric is not None, "context-fabric integration dependency not installed")
class I008ContextFabricIntegrationTests(unittest.TestCase):
    def make_api(self, *, sp_values=None, ls_values=None):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        files = {
            "otype.tf": """@node\n@valueType=str\n@description=node type\n\nword\nword\nword\nword\nword\n6\tphrase\n7\tphrase\n8\tsentence\n""",
            "oslots.tf": """@edge\n@valueType=int\n@description=slot containment\n\n6\t1-3\n7\t4-5\n8\t1-5\n""",
            "otext.tf": """@config\n@fmt:text-orig-full={word}\n@sectionFeatures=sentence_id,phrase_id\n@sectionTypes=sentence,phrase\n@structureFeatures=\n@structureTypes=\n""",
            "word.tf": """@node\n@valueType=str\n@description=word text\n\nhello\nbeautiful\nworld\ngood\nmorning\n""",
            "phrase_id.tf": """@node\n@valueType=int\n@description=phrase number\n\n6\t1\n7\t2\n""",
            "sentence_id.tf": """@node\n@valueType=str\n@description=sentence identifier\n\n8\tS1\n""",
            "sp.tf": """@node\n@valueType=str\n@description=part of speech\n\nsubs\nverb\nsubs\nverb\nsubs\n""",
        }
        if sp_values is not None:
            if len(sp_values) != 5:
                raise ValueError("fixture requires five word POS values")
            files["sp.tf"] = (
                "@node\n@valueType=str\n@description=part of speech\n\n"
                + "\n".join(sp_values) + "\n"
            )
        features = ["sp"]
        if ls_values is not None:
            # Sparse lexeme-kind tags, as in the Syriac native representation.
            files["ls.tf"] = (
                "@node\n@valueType=str\n@description=lexical subtype\n\n"
                + "".join(f"{node}\t{value}\n" for node, value in sorted(ls_values.items()))
            )
            features.append("ls")
        for name, content in files.items():
            (root / name).write_text(content, encoding="utf-8")
        cf = Fabric(locations=str(root), silent="deep")
        api = cf.load(" ".join(features))
        self.addCleanup(temp.cleanup)
        return api

    def test_fixture_control_exposes_loaded_sp_and_canonical_selector(self):
        api = self.make_api()
        self.assertIn("sp", api.Fall())
        self.assertEqual(tuple(int(node) for node in api.F.sp.s("subs")), (1, 3, 5))
        self.assertEqual(tuple(api.F.otype.v(node) for node in (1, 3, 5)), ("word", "word", "word"))

    def test_xml_cross_corpus_proper_noun_query_on_real_context_fabric(self):
        """No JSON release profiles: discover native XML and execute on actual CF APIs."""
        bhsa = self.make_api(sp_values=("nmpr", "verb", "subs", "nmpr", "subs"))
        syriac = self.make_api(
            sp_values=("subs", "verb", "subs", "subs", "subs"),
            ls_values={1: "prop", 4: "prop"},
        )
        # Discovery without a destination version returns separately labelled
        # correspondences. The two corpus versions must not be deduplicated.
        matches = tfont.find_correspondences(
            "bhsa", "syriac", node="word", feature="sp", value="nmpr",
            source_version="2021",
        )
        proper = [row for row in matches if row.target.endswith("#ProperNoun")]
        self.assertEqual(len(proper), 2)
        self.assertEqual({row.destination.corpus_version for row in proper},
                         {"0.9", "0.92"})
        for version, other_version in (("0.9", "0.92"), ("0.92", "0.9")):
            with self.subTest(version=version):
                scoped = tfont.find_correspondences(
                    "bhsa", "syriac", node="word", feature="sp", value="nmpr",
                    source_version="2021", target_version=version,
                )
                # The broader Noun projection is not a proper-name join.
                link, = [row for row in scoped if row.target.endswith("#ProperNoun")]
                self.assertEqual((link.destination.node, link.destination.feature,
                                  link.destination.value), ("word", "ls", "prop"))
                self.assertEqual(link.destination.corpus_version, version)
                self.assertEqual(link.scope, "category")
                self.assertEqual(
                    tfont.resolve_nodes(bhsa, link.source, corpus_version="2021"),
                    (1, 4),
                )
                # This is a real CF API over the synthetic fixture, not a loaded
                # upstream corpus; execution checks caller-supplied version.
                self.assertEqual(
                    tfont.resolve_nodes(syriac, link.destination, corpus_version=version),
                    (1, 4),
                )
                for wrong in (other_version, "wrong", None):
                    with self.assertRaises(tfont.MappingError):
                        tfont.resolve_nodes(syriac, link.destination, corpus_version=wrong)

    def test_public_executor_runs_against_real_loaded_context_fabric_api(self):
        if not hasattr(tfont, "execute_exact_semantic"):
            self.skipTest("RED: I-008 execution surface is not implemented yet")
        api = self.make_api()
        ir = compiled_executable_noun_ir(("bhsa",))
        context = loaded_context(tfont, ir, "bhsa", api)
        result = tfont.execute_exact_semantic(ir, request(tfont, ("bhsa",)), (context,))
        self.assertEqual(result.corpora[0].nodes, (1, 3, 5))


if __name__ == "__main__":
    unittest.main()
