"""ORACC-TF 1.0.0 native word→lexeme lookup, preserving compound analyses.

The ORACC-TF materializer owns the lexical graph, including the canonical
[lang, cf, gw, pos] tuple on each lex node and the word_lex edge. TFont reads
those loaded source features; it never infers an edge from spelling, a gloss,
or a raw word signature. The resulting OntoLex class is a *category* hint,
not an asserted RDF individual or LexicalSense.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


ORACC_SOURCE_REVISION = "60db4b724a687c0f425e78eae924fce89454e106"
ONTOLEX_LEXICAL_ENTRY = "http://www.w3.org/ns/lemon/ontolex#LexicalEntry"


class ORACCLexicalResolutionError(ValueError):
    """Invalid ORACC source word→lexeme lookup precondition."""


@dataclass(frozen=True)
class ORACCWordLexemeLink:
    """One native edge from an ORACC word to one canonical lexeme node.

    Multiple instances may share a word_node_id. The lexical_key is exactly
    the source [lang, cf, gw, pos] tuple, not an ontology sense identity.
    """

    word_node_id: int
    lex_node_id: int
    source_revision: str
    source_edge_feature: str
    lexical_key: tuple[str, str, str, str]
    entry_candidate_class: str


def _feature(api: Any, name: str, node: int) -> Any:
    try:
        return getattr(api.F, name).v(node)
    except (AttributeError, TypeError, KeyError, ValueError) as exc:
        raise ORACCLexicalResolutionError(
            f"required Text-Fabric feature missing: {name}"
        ) from exc


def _lexical_key(api: Any, node: int) -> tuple[str, str, str, str]:
    if _feature(api, "otype", node) != "lex":
        raise ORACCLexicalResolutionError("native word_lex target is not lex")
    serialized = _feature(api, "lexeme", node)
    if type(serialized) is not str:
        raise ORACCLexicalResolutionError("canonical source lexeme key missing")
    try:
        key = json.loads(serialized)
    except (ValueError, TypeError) as exc:
        raise ORACCLexicalResolutionError("invalid source lexeme key JSON") from exc
    if (type(key) is not list or len(key) != 4
            or any(type(value) is not str for value in key)):
        raise ORACCLexicalResolutionError(
            "ORACC source lexeme key must be [lang, cf, gw, pos]"
        )
    for feature, expected in zip(("lang", "cf", "gw", "pos"), key):
        observed = _feature(api, feature, node)
        if type(observed) is not str or observed != expected:
            raise ORACCLexicalResolutionError(
                f"lexeme key differs from native {feature} feature"
            )
    return (key[0], key[1], key[2], key[3])


def resolve_oracc_word_lexemes(
    tf_api: Any,
    word_node: int,
    *,
    source_revision: str,
) -> tuple[ORACCWordLexemeLink, ...]:
    """Return ALL native ORACC lexical analyses of a word, without guessing.

    The pinned source documents 0–3 lexeme links per word. In particular, a
    word without a link is genuinely unlemmatized and produces an empty tuple.
    The caller must separately authenticate/load the pinned TF source; merely
    passing its revision here does not prove the source bytes are genuine.
    """
    if source_revision != ORACC_SOURCE_REVISION:
        raise ORACCLexicalResolutionError("ORACC source revision is not pinned")
    if type(word_node) is not int or word_node < 1:
        raise ORACCLexicalResolutionError("word node ID must be positive int")
    if _feature(tf_api, "otype", word_node) != "word":
        raise ORACCLexicalResolutionError("source node is not a word")

    try:
        linked_nodes = tuple(tf_api.E.word_lex.f(word_node))
    except (AttributeError, TypeError, KeyError, ValueError) as exc:
        raise ORACCLexicalResolutionError(
            "required native word_lex edge unavailable"
        ) from exc
    if len(linked_nodes) > 3:
        raise ORACCLexicalResolutionError(
            "word_lex degree exceeds the pinned ORACC-TF source maximum"
        )
    if any(type(n) is not int or n < 1 for n in linked_nodes):
        raise ORACCLexicalResolutionError("native word_lex has invalid node ID")
    if len(set(linked_nodes)) != len(linked_nodes):
        raise ORACCLexicalResolutionError("native word_lex repeats a lex node")
    return tuple(
        ORACCWordLexemeLink(
            word_node_id=word_node,
            lex_node_id=node,
            source_revision=ORACC_SOURCE_REVISION,
            source_edge_feature="word_lex",
            lexical_key=_lexical_key(tf_api, node),
            entry_candidate_class=ONTOLEX_LEXICAL_ENTRY,
        )
        for node in linked_nodes
    )
