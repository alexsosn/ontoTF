"""Installed-wheel release smoke against the pinned ETCBC ExtraBiblical TF corpus.

Use independently obtained TF 0.2 files from the *pinned* repository revision:
https://github.com/ETCBC/extrabiblical/tree/9a56288e6777bad6328856acf055c780e65dd5d9/tf/0.2

This script deliberately does not download sources or trust a caller's corpus
version as proof of byte identity. The release CI downloads the five required
original files from revision-pinned URLs before invoking this script outside
the checkout with a freshly installed wheel and real Context-Fabric.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import tfont


PIN = "9a56288e6777bad6328856acf055c780e65dd5d9"
TF_VERSION = "0.2"
TOKEN = "http://purl.org/olia/olia.owl#Token"
NOUN = "http://purl.org/olia/olia.owl#Noun"
PROPER_NOUN = "http://purl.org/olia/olia.owl#ProperNoun"
EXPECTED = {
    # Frozen R-005 census of the actual ExtraBiblical 0.2 TF source.
    "word_slots": 39862,
    "surface_tokens": 39560,
    "empty_slots": 302,
    "nouns_subs": 12225,
    "proper_nouns_nmpr": 723,
}
NEEDED_FILES = ("otype.tf", "oslots.tf", "otext.tf", "book.tf", "chapter.tf", "verse.tf", "sp.tf", "g_word.tf")


def audit_loaded_api(api) -> dict[str, int]:
    """Evaluate real native selectors; never equate words across corpora."""
    catalog = tfont.MappingCatalog()
    token_rows = catalog.find_by_target(TOKEN, corpus="extrabiblical")
    tokens = [
        row for row in token_rows
        if row.kind == "node" and row.node == "word" and row.feature == "g_word"
        and row.relation == "exact" and row.corpus_version == TF_VERSION
    ]
    if len(tokens) != 1:
        raise ValueError("expected exactly one source-guarded ExtraBiblical Token mapping")
    token = tokens[0]

    noun_rows = catalog.map_native(
        "extrabiblical", node="word", feature="sp", value="subs",
        corpus_version=TF_VERSION,
    )
    proper_rows = catalog.map_native(
        "extrabiblical", node="word", feature="sp", value="nmpr",
        corpus_version=TF_VERSION,
    )
    nouns = [row for row in noun_rows if row.target == NOUN and row.relation == "exact"]
    proper = [row for row in proper_rows
              if row.target == PROPER_NOUN and row.relation == "exact"]
    if len(nouns) != 1 or len(proper) != 1:
        raise ValueError("expected reviewed source noun/proper-noun selectors")

    links = catalog.find_correspondences(
        "extrabiblical", "bhsa", node="word", feature="sp", value="subs",
        source_version=TF_VERSION, target_version="2021",
    )
    if not links or any(link.target != NOUN or link.scope != "category"
                        or link.relation != "exact" for link in links):
        raise ValueError("expected category-only OLiA Noun correspondences")

    native_only, = catalog.map_native(
        "extrabiblical", node="word", feature="sp", value="inrg",
        corpus_version=TF_VERSION,
    )
    if native_only.relation != "native-only" or native_only.target is not None:
        raise ValueError("unresolved source POS promoted to an ontology category")
    if catalog.find_correspondences(
        "extrabiblical", "bhsa", node="word", feature="sp", value="inrg",
        include_approximate=True, source_version=TF_VERSION,
        target_version="2021",
    ):
        raise ValueError("native-only source POS yielded a correspondence")

    try:
        tfont.resolve_nodes(api, token, corpus_version="not-0.2")
    except tfont.MappingError:
        pass
    else:
        raise ValueError("wrong corpus-version argument was accepted")

    slots = tuple(api.F.otype.s("word"))
    token_nodes = tfont.resolve_nodes(api, token, corpus_version=TF_VERSION)
    noun_nodes = tfont.resolve_nodes(api, nouns[0], corpus_version=TF_VERSION)
    proper_nodes = tfont.resolve_nodes(api, proper[0], corpus_version=TF_VERSION)
    if not set(token_nodes) <= set(slots):
        raise ValueError("token selection contains non-word nodes")
    if not set(noun_nodes) <= set(slots) or not set(proper_nodes) <= set(slots):
        raise ValueError("POS selection contains non-word nodes")

    return {
        "word_slots": len(slots),
        "surface_tokens": len(token_nodes),
        "empty_slots": len(slots) - len(token_nodes),
        "nouns_subs": len(noun_nodes),
        "proper_nouns_nmpr": len(proper_nodes),
        "shared_noun_category_matches": len(links),
    }


def verify_source_counts(observed: dict[str, int]) -> None:
    missing = EXPECTED.keys() - observed.keys()
    if missing:
        raise ValueError(f"missing source counters: {sorted(missing)}")
    for name, expected in EXPECTED.items():
        if observed[name] != expected:
            raise ValueError(
                f"{name}: expected {expected} source observations, got {observed[name]}"
            )
    if observed.get("shared_noun_category_matches", 0) < 1:
        raise ValueError("missing cross-corpus OLiA Noun category correspondences")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tf-dir", type=Path, required=True,
                        help="Local directory of original pinned ExtraBiblical tf/0.2 files")
    args = parser.parse_args()

    forbidden = os.environ.get("TFONT_ACCEPTANCE_FORBID_ROOT")
    if forbidden and Path(tfont.__file__).resolve().is_relative_to(
        Path(forbidden).resolve()
    ):
        raise SystemExit("imported tfont from checkout instead of installed wheel")

    tf_dir = args.tf_dir.expanduser().resolve()
    missing = [name for name in NEEDED_FILES if not (tf_dir / name).is_file()]
    if missing:
        raise SystemExit(f"missing original TF files: {missing}")

    from cfabric.core import Fabric

    fabric = Fabric(locations=str(tf_dir), silent="deep")
    api = fabric.load("sp g_word")
    if api is None or api is False:
        raise SystemExit("could not load pinned ExtraBiblical TF with Context-Fabric")

    observed = audit_loaded_api(api)
    verify_source_counts(observed)
    print(json.dumps({
        "contract": "tfont-real-extrabiblical-wheel-smoke-v1",
        "status": "pass",
        "corpus": "extrabiblical",
        "source_version": TF_VERSION,
        "source_revision_expected": PIN,
        "counts": observed,
        "package_file": str(Path(tfont.__file__).resolve()),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
