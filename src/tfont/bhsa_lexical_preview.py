"""BHSA 2021 TF-native lexical entry→virtual Form *preview*.

This is NOT a reviewed mapping, ontology authority, shared-pivot release, or a
claim that BHSA publishes a native OntoLex Form node. It derives a queryable
source-bound representation from an actual otype=lex node and its own TF features.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Any, Mapping


BHSA_SOURCE_REVISION = "4db00e2157915495e1a4d3d57e41223df24775da"
_LEX_FIRST = 1437602
_LEX_LAST = 1446831
_ROOT = f"urn:tfont:derived:bhsa:{BHSA_SOURCE_REVISION}:lex:"
_URI = re.compile(rf"^{re.escape(_ROOT)}([1-9][0-9]*)(:form:voc_lex_utf8)?$")
ONTOLEX = "http://www.w3.org/ns/lemon/ontolex#"
_LANGUAGES = frozenset({"hbo", "arc"})


class LexicalProjectionError(ValueError):
    """Invalid source-bound lexical projection precondition."""


@dataclass(frozen=True)
class DerivedBHSAForm:
    """Preview values: source lex node is real, form resource is TFont-derived."""

    authority: str
    source_revision: str
    source_node_id: int
    source_lexeme: str
    source_representation_feature: str
    entry_iri: str
    entry_candidate_class: str
    form_iri: str
    form_candidate_class: str
    lexical_form_relation: str
    written_rep_relation: str
    written_rep: str
    language_tag: str


def _lex_id(node: Any) -> int:
    if type(node) is not int or not _LEX_FIRST <= node <= _LEX_LAST:
        raise LexicalProjectionError("node ID is outside pinned BHSA 2021 lex scope")
    return node


def parse_bhsa_lexical_uri(uri: str) -> tuple[int, str]:
    """Syntactically invert a local derived view identifier, not authenticate it.

    Returning a node ID does not prove that a caller supplied the pinned TF corpus
    or a valid RDF instance. Verify with project_bhsa_lexical_form and a genuine
    materialized BHSA source before treating a returned ID as a corpus node.
    """
    if type(uri) is not str:
        raise LexicalProjectionError("lexical URI must be a string")
    match = _URI.fullmatch(uri)
    if match is None:
        raise LexicalProjectionError("URI does not belong to pinned BHSA lexical view")
    node = _lex_id(int(match.group(1)))
    return (node, "form" if match.group(2) else "entry")


def _get(tf_api: Any, feature: str, node: int) -> Any:
    try:
        return getattr(getattr(tf_api.F, feature), "v")(node)
    except (AttributeError, TypeError, KeyError, ValueError) as exc:
        raise LexicalProjectionError(f"required Text-Fabric feature missing: {feature}") from exc


def project_bhsa_lexical_form(
    tf_api: Any,
    lex_node: int,
    *,
    source_revision: str,
) -> DerivedBHSAForm:
    """Project a source lex node, preserving homographs and language/script.

    Only valid for ETCBC BHSA 2021 at the pinned exact commit. Does not bind
    or prove the caller's actual TF checkout: revision argument alone is not an
    attestation. A real TF API should be passed by the caller. No canonicalForm,
    SKOS Concept, LexicalSense or cross-corpus correspondence is asserted.
    """
    node = _lex_id(lex_node)
    if source_revision != BHSA_SOURCE_REVISION:
        raise LexicalProjectionError("BHSA source revision is not pinned release")
    if _get(tf_api, "otype", node) != "lex":
        raise LexicalProjectionError("source node is not a BHSA lexeme node")
    lexeme = _get(tf_api, "lex", node)
    written = _get(tf_api, "voc_lex_utf8", node)
    language = _get(tf_api, "languageISO", node)
    if type(lexeme) is not str or not lexeme or type(written) is not str or not written:
        raise LexicalProjectionError("lexeme or written representation is missing")
    if type(language) is not str or language not in _LANGUAGES:
        raise LexicalProjectionError("unsupported or absent source language code")
    entry_iri = _ROOT + str(node)
    return DerivedBHSAForm(
        authority="unreviewed-derived-preview",
        source_revision=BHSA_SOURCE_REVISION,
        source_node_id=node,
        source_lexeme=lexeme,
        source_representation_feature="voc_lex_utf8",
        entry_iri=entry_iri,
        entry_candidate_class=ONTOLEX + "LexicalEntry",
        form_iri=entry_iri + ":form:voc_lex_utf8",
        form_candidate_class=ONTOLEX + "Form",
        lexical_form_relation=ONTOLEX + "lexicalForm",
        written_rep_relation=ONTOLEX + "writtenRep",
        written_rep=written,
        language_tag=language,
    )


def resolve_bhsa_lexical_uri(
    tf_api: Any,
    uri: str,
    *,
    source_revision: str,
) -> tuple[str, DerivedBHSAForm]:
    """Revalidate a derived entry/Form URI against the live materialized TF API.

    A parsable URI by itself confers no corpus provenance, source identity or
    review authority. Resolve every time through the real native TF features.
    The first result component is the requested "entry" or "form" kind.
    """
    node, kind = parse_bhsa_lexical_uri(uri)
    projection = project_bhsa_lexical_form(
        tf_api, node, source_revision=source_revision
    )
    expected = projection.entry_iri if kind == "entry" else projection.form_iri
    if uri != expected:
        raise LexicalProjectionError("unbound lexical URI does not match source record")
    return kind, projection



@dataclass(frozen=True)
class BHSAFormIndex:
    """Immutable source-revision-scoped snapshot, not reviewed RDF authority.

    Build again if the caller changes or reloads the materialized TF corpus.
    The index contains every lexeme node of the one pinned BHSA 2021 release.
    """
    source_revision: str
    lexeme_count: int
    by_written_rep: Mapping[str, tuple[DerivedBHSAForm, ...]]

    def lookup(self, written_rep: str) -> tuple[DerivedBHSAForm, ...]:
        """Return *all* lexeme/Form identities for this exact source string."""
        if type(written_rep) is not str or not written_rep:
            raise LexicalProjectionError("written representation must be nonempty text")
        return self.by_written_rep.get(written_rep, ())


def build_bhsa_lexical_form_index(
    tf_api: Any,
    *,
    source_revision: str,
) -> BHSAFormIndex:
    """Build a reusable Form index from 9,230 genuine BHSA lex nodes only.

    Text-Fabric NodeFeature.s() *scans the whole feature dictionary*; it is
    not an inverted index. This builder performs one bounded validation pass
    over the pinned lex-node ID range, never over the 426,590 word nodes.
    """
    if source_revision != BHSA_SOURCE_REVISION:
        raise LexicalProjectionError("BHSA source revision is not pinned release")
    lookup: dict[str, list[DerivedBHSAForm]] = {}
    for node in range(_LEX_FIRST, _LEX_LAST + 1):
        projection = project_bhsa_lexical_form(
            tf_api, node, source_revision=source_revision
        )
        lookup.setdefault(projection.written_rep, []).append(projection)
    frozen = MappingProxyType({
        value: tuple(projections) for value, projections in lookup.items()
    })
    return BHSAFormIndex(
        source_revision=BHSA_SOURCE_REVISION,
        lexeme_count=_LEX_LAST - _LEX_FIRST + 1,
        by_written_rep=frozen,
    )


def find_bhsa_lexical_forms(
    tf_api: Any,
    written_rep: str,
    *,
    source_revision: str,
) -> tuple[DerivedBHSAForm, ...]:
    """One-off exact-source lookup; reuse an index for many lookups instead.

    This deliberately does NOT call F.voc_lex_utf8.s(), which performs an
    O(435,820) scan. Build a BHSAFormIndex once for amortized constant-time
    lookups over just the 9,230 lexical records.
    """
    if type(written_rep) is not str or not written_rep:
        raise LexicalProjectionError("written representation must be nonempty text")
    return build_bhsa_lexical_form_index(
        tf_api, source_revision=source_revision
    ).lookup(written_rep)
