"""I-028C: actual, independently pinned and parseable OntoLex Core model."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import json

from tfont.source_validation import validate_source


ROOT = Path(__file__).resolve().parents[2]
REVISION = "d6f840f40a05b76cbd8c10b9472ddd097371d610"
FOLDER = ROOT / "src/tfont/resources/ontologies/ontolex" / REVISION
OWL_FILE = FOLDER / "ontolex.owl"
LOCK = FOLDER / "lock-core-v1.json"
FILE_SHA256 = "76e4c74fae4013944f60701df83828836c22a7f19c8cc8f72f994e321d12efd9"
BLOB_SHA1 = "10783b4c747bbc5f08fbae8f4169d6e02fc22565"
NS = "http://www.w3.org/ns/lemon/ontolex#"
OWL = "{http://www.w3.org/2002/07/owl#}"
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"
DC = "{http://purl.org/dc/elements/1.1/}"
CC = "{http://creativecommons.org/ns#}"
EXPECTED = {
    "LexicalEntry": "Class",
    "Form": "Class",
    "LexicalSense": "Class",
    "LexicalConcept": "Class",
    "lexicalForm": "ObjectProperty",
    "canonicalForm": "ObjectProperty",
    "writtenRep": "DatatypeProperty",
}


def identity(raw: bytes):
    """Compare actual upstream bytes, not an author-supplied digest only."""
    blob = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    if hashlib.sha1(blob).hexdigest() != BLOB_SHA1:
        raise ValueError("not the pinned upstream Git blob")
    if hashlib.sha256(raw).hexdigest() != FILE_SHA256:
        raise ValueError("not the pinned OntoLex RDF/XML file")
    return ET.fromstring(raw)


def find_term(root, name, kind):
    uri = NS + name
    xs = [el for el in root.iter(OWL + kind) if el.get(RDF + "about") == uri]
    if len(xs) != 1:
        raise ValueError("wrong OWL term kind, absent or multiply declared: " + name)
    return xs[0]


def restrictions(node):
    return node.findall(RDFS + "subClassOf/" + OWL + "Restriction")


def has_cardinality(node, prop, cls, card):
    for restriction in restrictions(node):
        on_prop = restriction.find(OWL + "onProperty")
        on_cls = restriction.find(OWL + "onClass") if cls != "langString" else restriction.find(OWL + "onDataRange")
        cardinality = restriction.find(OWL + "minQualifiedCardinality")
        if (on_prop is not None and on_cls is not None and cardinality is not None
                and on_prop.get(RDF + "resource") == NS + prop
                and on_cls.get(RDF + "resource") == (NS + cls if cls != "langString" else RDF[1:-1] + "langString")
                and cardinality.text == str(card)):
            return True
    return False


def validate_model(root):
    """Check actual RDF declaration roles and required model links."""
    for name, kind in EXPECTED.items():
        find_term(root, name, kind)
    for name, domain, range_ in (
        ("lexicalForm", NS + "LexicalEntry", NS + "Form"),
        ("canonicalForm", NS + "LexicalEntry", NS + "Form"),
        ("writtenRep", NS + "Form", RDF[1:-1] + "langString"),
    ):
        prop = find_term(root, name, EXPECTED[name])
        d = prop.find(RDFS + "domain")
        r = prop.find(RDFS + "range")
        if d is None or d.get(RDF + "resource") != domain or r is None or r.get(RDF + "resource") != range_:
            raise ValueError("OWL property domain/range mismatch: " + name)
    cf = find_term(root, "canonicalForm", "ObjectProperty")
    sub = cf.find(RDFS + "subPropertyOf")
    if sub is None or sub.get(RDF + "resource") != NS + "lexicalForm":
        raise ValueError("canonicalForm must specialize lexicalForm")
    if not has_cardinality(find_term(root, "LexicalEntry", "Class"), "lexicalForm", "Form", 1):
        raise ValueError("LexicalEntry must require at least one Form")
    if not has_cardinality(find_term(root, "Form", "Class"), "writtenRep", "langString", 1):
        raise ValueError("Form must require writtenRep as language-tagged text")
    header = next((o for o in root.iter(OWL + "Ontology")
                   if o.get(RDF + "about") == "http://www.w3.org/ns/lemon/ontolex"), None)
    if header is None:
        raise ValueError("ontology header missing")
    rights = header.find(DC + "rights")
    license_ = header.find(CC + "license")
    if (rights is None or rights.text != "CC-Zero"
            or license_ is None
            or license_.get(RDF + "resource") != "https://creativecommons.org/publicdomain/zero/1.0/"):
        raise ValueError("source does not attest CC0")
    return True


class OntoLexCoreSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = OWL_FILE.read_bytes()
        cls.lock = json.loads(LOCK.read_text(encoding="utf-8"))
        cls.root = identity(cls.raw)

    def test_real_upstream_blob_and_full_ontology_semantics(self):
        self.assertTrue(validate_model(self.root))

    def test_packaged_ontology_lock_source_and_license(self):
        validate_source(self.lock, "ontology-lock")
        self.assertEqual(self.lock["ontology_id"], "ontolex")
        self.assertEqual(self.lock["source_revision"], REVISION)
        self.assertEqual(self.lock["source_uri"],
                         "https://raw.githubusercontent.com/ontolex/ontolex/"
                         + REVISION + "/Ontologies/ontolex.owl")
        self.assertEqual(self.lock["snapshot_artifact"],
                         "resources/ontologies/ontolex/" + REVISION + "/ontolex.owl")
        self.assertEqual(self.lock["content_digest"], "sha256:" + FILE_SHA256)
        self.assertEqual(self.lock["term_namespace"], NS)
        self.assertEqual(self.lock["license"], "CC0-1.0")
        self.assertEqual(self.lock["redistribution_policy"], "public-domain-dedication")
        self.assertEqual(set(self.lock["terms_used"]), {NS + name for name in EXPECTED})
        self.assertEqual(self.lock["lock_id"], "ontolex-core-reference-model")

    def test_modified_owl_and_forged_semantic_roles_fail(self):
        with self.assertRaises(ValueError):
            identity(self.raw + b" ")
        # Mutate the RDF parsed graph separately from the raw digest to
        # exercise actual ontology semantics, not simply a checksum shortcut.
        for change in ("no-lexical-entry", "form-as-string", "wrong-written-rep", "drop-min-form",
                       "drop-cc0"):
            with self.subTest(change=change):
                root = ET.fromstring(self.raw)
                if change == "no-lexical-entry":
                    term = find_term(root, "LexicalEntry", "Class")
                    root.remove(term)
                elif change == "form-as-string":
                    term = find_term(root, "Form", "Class")
                    term.tag = OWL + "DatatypeProperty"
                elif change == "wrong-written-rep":
                    term = find_term(root, "writtenRep", "DatatypeProperty")
                    term.find(RDFS + "domain").set(RDF + "resource", NS + "LexicalEntry")
                elif change == "drop-min-form":
                    term = find_term(root, "LexicalEntry", "Class")
                    r = next(x for x in restrictions(term)
                             if x.find(OWL + "onProperty") is not None
                             and x.find(OWL + "onProperty").get(RDF + "resource") == NS + "lexicalForm")
                    for subclass in term.findall(RDFS + "subClassOf"):
                        if r in list(subclass):
                            subclass.remove(r)
                            break
                else:
                    header = next(el for el in root.iter(OWL + "Ontology")
                                  if el.get(RDF + "about") == "http://www.w3.org/ns/lemon/ontolex")
                    header.remove(header.find(CC + "license"))
                with self.assertRaises(ValueError):
                    validate_model(root)


if __name__ == "__main__":
    unittest.main()
