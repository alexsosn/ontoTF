from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin

from ontotf.parent_identity import (
    PARENT_COMPONENTS_ALGORITHM,
    TF_FILES_ALGORITHM,
    file_component_digest,
    parent_manifest_digest,
    tf_payload_digest,
)


SPECS = (
    ("bhsa", "bhsa-tf", "ETCBC/bhsa", "4db00e2157915495e1a4d3d57e41223df24775da", "2021"),
    ("syriac", "syriac-tf", "ETCBC/syriac", "bb0eaa7e21b020a26b7566d2e495da9b1f84a919", "0.9"),
    ("extrabiblical", "extrabiblical-tf", "ETCBC/extrabiblical", "9a56288e6777bad6328856acf055c780e65dd5d9", "0.2"),
)

OLIA_REPOSITORY = "acoli-repo/olia"
OLIA_REVISION = "d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6"
OLIA_PATH = "owl/core/olia.owl"
OLIA_NS = "http://purl.org/olia/olia.owl#"
OLIA_NOUN = f"{OLIA_NS}Noun"
OLIA_COMMON_NOUN = f"{OLIA_NS}CommonNoun"
OLIA_PROPER_NOUN = f"{OLIA_NS}ProperNoun"
OLIA_LICENSE_URI = "https://creativecommons.org/licenses/by/3.0/"
DCT_NS = "http://purl.org/dc/terms/"
OWL_NS = "http://www.w3.org/2002/07/owl#"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def measure(corpus_id: str, component_id: str, repository: str, revision: str, tf_version: str, path: Path) -> dict[str, str]:
    content_digest = tf_payload_digest(path)
    manifest = {
        "algorithm": PARENT_COMPONENTS_ALGORITHM,
        "components": [
            {
                "component_id": component_id,
                "kind": "tf-payload",
                "identity_algorithm": TF_FILES_ALGORITHM,
                "content_digest": content_digest,
            }
        ],
    }
    return {
        "corpus_id": corpus_id,
        "component_id": component_id,
        "repository": repository,
        "revision": revision,
        "tf_version": tf_version,
        "content_digest": content_digest,
        "parent_manifest_digest": parent_manifest_digest(manifest),
    }


def _class_iri(element: ET.Element, base: str) -> str | None:
    about = element.attrib.get(f"{{{RDF_NS}}}about")
    if about is not None:
        return urljoin(base, about)
    rdf_id = element.attrib.get(f"{{{RDF_NS}}}ID")
    if rdf_id is not None:
        return urljoin(base, f"#{rdf_id}")
    return None


def _direct_subclass_parent_iri(relation: ET.Element, base: str) -> str | None:
    """Resolve only the two direct RDF/XML forms used by the pinned OLiA payload."""
    resource = relation.attrib.get(f"{{{RDF_NS}}}resource")
    if resource is not None:
        return urljoin(base, resource)

    children = list(relation)
    if len(children) != 1 or children[0].tag != f"{{{OWL_NS}}}Class":
        return None
    return _class_iri(children[0], base)


def _verify_olia_license(root: ET.Element, base: str) -> None:
    ontology = root.find(f"{{{OWL_NS}}}Ontology")
    if ontology is None:
        raise SystemExit("OLiA ontology declaration missing from exact payload")
    licenses = {
        urljoin(base, resource)
        for element in ontology.findall(f"{{{DCT_NS}}}license")
        if (resource := element.attrib.get(f"{{{RDF_NS}}}resource")) is not None
    }
    if OLIA_LICENSE_URI not in licenses:
        raise SystemExit(
            f"expected OLiA CC-BY-3.0 license assertion missing: {OLIA_LICENSE_URI}"
        )


def measure_olia(path: Path) -> dict[str, object]:
    tree = ET.parse(path)
    root = tree.getroot()
    base = root.attrib.get(f"{{{XML_NS}}}base", "")
    _verify_olia_license(root, base)

    # Only direct rdf:RDF children are class declarations. Nested owl:Class
    # elements in this exact payload are reference nodes inside relations and
    # must not overwrite the top-level class declarations.
    classes: dict[str, ET.Element] = {}
    for element in root.findall(f"{{{OWL_NS}}}Class"):
        iri = _class_iri(element, base)
        if iri is not None:
            classes[iri] = element

    if OLIA_NOUN not in classes:
        raise SystemExit(f"canonical OLiA term not found in exact payload: {OLIA_NOUN}")

    noun_subclasses: list[str] = []
    for child_iri, element in classes.items():
        for relation in element.findall(f"{{{RDFS_NS}}}subClassOf"):
            if _direct_subclass_parent_iri(relation, base) == OLIA_NOUN:
                noun_subclasses.append(child_iri)
                break
    noun_subclasses.sort()

    required = {OLIA_COMMON_NOUN, OLIA_PROPER_NOUN}
    if not required.issubset(noun_subclasses):
        missing = sorted(required - set(noun_subclasses))
        raise SystemExit(f"expected OLiA Noun direct subclasses missing: {missing}")

    return {
        "lock_id": "olia-reference-model",
        "ontology_id": "olia",
        "repository": OLIA_REPOSITORY,
        "revision": OLIA_REVISION,
        "path": OLIA_PATH,
        "term_namespace": OLIA_NS,
        "term": OLIA_NOUN,
        "noun_direct_subclasses": noun_subclasses,
        "content_digest": file_component_digest(path),
        "license": "CC-BY-3.0",
        "license_uri": OLIA_LICENSE_URI,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bhsa", type=Path, required=True)
    parser.add_argument("--syriac", type=Path, required=True)
    parser.add_argument("--extrabiblical", type=Path, required=True)
    parser.add_argument("--olia", type=Path, required=True)
    args = parser.parse_args()
    paths = {
        "bhsa": args.bhsa,
        "syriac": args.syriac,
        "extrabiblical": args.extrabiblical,
    }
    rows = [measure(*spec, paths[spec[0]]) for spec in SPECS]
    result = {
        "algorithm": "i009-parent-identity-research-v3",
        "corpora": rows,
        "ontology": measure_olia(args.olia),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
