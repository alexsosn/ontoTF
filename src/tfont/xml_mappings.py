"""Small, repository-local XML catalog for corpus-to-ontology correspondences.

The XML files are authoritative; there is no release or review-packet generator.
Only category correspondence is inferred from shared class IRIs. Node identity
needs explicit kind="entity" mappings.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET


_KINDS = {"node", "feature", "value", "edge", "entity"}
_RELATIONS = {"exact", "close", "broader", "narrower", "related",
              "ambiguous", "native-only", "unsupported"}
_NON_MATCHING = {"ambiguous", "native-only", "unsupported"}
_SELECTOR_FIELDS = ("node", "feature", "value", "from_node", "to_node")
_ALLOWED_ROOT = {"corpus", "source", "corpusVersion"}
_ALLOWED_MAP = {"kind", "relation", "target", "corpusVersion", "evidence",
                "note", "node", "feature", "value", "from", "to"}
_CORPUS = re.compile(r"[a-z][a-z0-9_-]*\Z")


class MappingError(ValueError):
    """Invalid XML mapping data or incompatible native corpus version."""


@dataclass(frozen=True)
class Mapping:
    corpus: str
    source: str
    corpus_version: str | None
    kind: str
    relation: str
    target: str | None
    node: str | None = None
    feature: str | None = None
    value: str | None = None
    from_node: str | None = None
    to_node: str | None = None
    evidence: str | None = None
    note: str | None = None

    @property
    def selector(self) -> tuple[str | None, ...]:
        return (self.kind, *(getattr(self, field) for field in _SELECTOR_FIELDS))


@dataclass(frozen=True)
class Correspondence:
    source: Mapping
    destination: Mapping
    target: str

    @property
    def scope(self) -> str:
        return "entity-candidate" if self.source.kind == "entity" else "category"

    @property
    def relation(self) -> str:
        # An entity IRI match without a uniqueness check is only a candidate.
        if self.source.kind == "entity":
            return "unverified"
        # A mixed or approximate category path is not a direct equivalence.
        return ("exact" if self.source.relation == self.destination.relation == "exact"
                else "approximate-via-target")


def _iri(value: str) -> bool:
    parts = urlsplit(value)
    return bool(parts.scheme and value[len(parts.scheme) + 1:])


def _checked(name: str, text: str) -> tuple[Mapping, ...]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise MappingError(f"{name}: malformed XML: {exc}") from exc
    if root.tag != "mappings" or set(root.attrib) - _ALLOWED_ROOT:
        raise MappingError(f"{name}: expected <mappings> with known attributes")
    corpus = root.get("corpus")
    source = root.get("source")
    if corpus != name[:-4] or not corpus or not _CORPUS.fullmatch(corpus):
        raise MappingError(f"{name}: root corpus must equal XML filename")
    if not source or not source.strip():
        raise MappingError(f"{name}: nonempty source is required")
    rows: list[Mapping] = []
    seen: set[tuple[object, ...]] = set()
    for index, item in enumerate(root, start=1):
        where = f"{name}: map #{index}"
        if item.tag != "map" or set(item.attrib) - _ALLOWED_MAP or len(item):
            raise MappingError(f"{where}: unexpected XML element or attribute")
        kind, relation = item.get("kind"), item.get("relation")
        if kind not in _KINDS or relation not in _RELATIONS:
            raise MappingError(f"{where}: unknown kind or relation")
        given = {key for key in ("node", "feature", "value", "from", "to")
                 if item.get(key) is not None}
        required = {
            "node": {"node"},
            "feature": {"feature"},
            "value": {"node", "feature", "value"},
            "edge": {"feature"},
            "entity": {"node", "feature", "value"},
        }[kind]
        optional = {"node"} if kind == "feature" else (
            {"from", "to"} if kind == "edge" else set())
        if not required <= given or given - (required | optional):
            raise MappingError(f"{where}: invalid {kind} selector fields")
        if any(not item.get(key, "").strip() for key in given):
            raise MappingError(f"{where}: selector values must be nonempty")
        target = item.get("target")
        if relation in _NON_MATCHING:
            if relation != "ambiguous" and target is not None:
                raise MappingError(f"{where}: {relation} must not have a target")
            if target is not None and not _iri(target):
                raise MappingError(f"{where}: invalid candidate IRI")
        elif target is None or not _iri(target):
            raise MappingError(f"{where}: {relation} requires an absolute target IRI")
        row = Mapping(
            corpus=corpus, source=source,
            corpus_version=item.get("corpusVersion", root.get("corpusVersion")),
            kind=kind, relation=relation, target=target,
            node=item.get("node"), feature=item.get("feature"),
            value=item.get("value"), from_node=item.get("from"),
            to_node=item.get("to"), evidence=item.get("evidence"),
            note=item.get("note"),
        )
        fingerprint = (row.selector, row.relation, row.target, row.corpus_version)
        if fingerprint in seen:
            raise MappingError(f"{where}: duplicate mapping")
        seen.add(fingerprint)
        rows.append(row)
    return tuple(rows)


class MappingCatalog:
    """Load discovered corpus XML files lazily, independently of each other."""

    def __init__(self, directory: Any = None) -> None:
        self.directory = (Path(directory) if directory is not None
                          else files("tfont").joinpath("mappings"))
        self._loaded: dict[str, tuple[Mapping, ...]] = {}

    def list_corpora(self) -> tuple[str, ...]:
        return tuple(sorted(p.name[:-4] for p in self.directory.iterdir()
                            if p.name.endswith(".xml") and p.is_file()))

    def load(self, corpus: str) -> tuple[Mapping, ...]:
        if not isinstance(corpus, str) or not _CORPUS.fullmatch(corpus):
            raise MappingError(f"invalid corpus name: {corpus!r}")
        if corpus not in self._loaded:
            filename = f"{corpus}.xml"
            path = self.directory.joinpath(filename)
            if not path.is_file():
                raise MappingError(f"unknown corpus: {corpus}")
            self._loaded[corpus] = _checked(filename, path.read_text(encoding="utf-8"))
        return self._loaded[corpus]

    def map_native(
        self, corpus: str, *, kind: str = "value",
        node: str | None = None, feature: str | None = None,
        value: str | None = None, from_node: str | None = None,
        to_node: str | None = None, corpus_version: str | None = None,
    ) -> tuple[Mapping, ...]:
        selector = (kind, node, feature, value, from_node, to_node)
        found = tuple(row for row in self.load(corpus) if row.selector == selector)
        if corpus_version is not None:
            incompatible = [row for row in found if row.corpus_version is not None
                            and row.corpus_version != corpus_version]
            found = tuple(row for row in found if row not in incompatible)
            if incompatible and not found:
                raise MappingError(f"{corpus}: selector not verified for corpus version {corpus_version}")
        return found

    def find_by_target(
        self, target: str, *, corpus: str | None = None,
        kind: str = "value", include_approximate: bool = False,
    ) -> tuple[Mapping, ...]:
        """Find native category selectors mapped to a known ontology IRI.

        Only positive category links are returned. An ambiguous candidate
        cannot be used as an ontology match, even with approximate lookup.
        To examine individual identity assertions, explicitly request
        kind="entity"; those rows are *not* verified token identities.
        """
        if not isinstance(target, str) or not _iri(target):
            raise MappingError("target must be an absolute ontology IRI")
        if kind not in _KINDS:
            raise MappingError(f"unknown mapping kind: {kind!r}")
        corpora = self.list_corpora() if corpus is None else (corpus,)
        return tuple(
            row
            for name in corpora
            for row in self.load(name)
            if row.kind == kind
            and row.target == target
            and row.relation not in _NON_MATCHING
            and (include_approximate or row.relation == "exact")
        )

    def find_correspondences(
        self, source_corpus: str, target_corpus: str, *,
        kind: str = "value", node: str | None = None,
        feature: str | None = None, value: str | None = None,
        from_node: str | None = None, to_node: str | None = None,
        include_approximate: bool = False,
        source_version: str | None = None, target_version: str | None = None,
    ) -> tuple[Correspondence, ...]:
        origins = self.map_native(
            source_corpus, kind=kind, node=node, feature=feature, value=value,
            from_node=from_node, to_node=to_node, corpus_version=source_version)
        destinations = self.load(target_corpus)
        result: list[Correspondence] = []
        for origin in origins:
            if not origin.target or origin.relation in _NON_MATCHING:
                continue
            if not include_approximate and origin.relation != "exact":
                continue
            for other in destinations:
                if other.kind != kind or other.target != origin.target:
                    continue
                if other.relation in _NON_MATCHING:
                    continue
                if target_version is not None and other.corpus_version is not None and other.corpus_version != target_version:
                    continue
                if not include_approximate and other.relation != "exact":
                    continue
                result.append(Correspondence(origin, other, origin.target))
        return tuple(result)


    def find_across_corpora(
        self, source_corpus: str, *, kind: str = "value",
        node: str | None = None, feature: str | None = None,
        value: str | None = None, from_node: str | None = None,
        to_node: str | None = None, include_approximate: bool = False,
        source_version: str | None = None,
    ) -> tuple[Correspondence, ...]:
        """Find shared ontology-category mappings in every *other* corpus.

        Each destination keeps its native selector and source provenance.
        An ontology-category link never asserts that source and destination
        nodes refer to the same individual token.
        """
        self.load(source_corpus)  # Validate even when no other corpora exist.
        return tuple(
            match
            for destination in self.list_corpora()
            if destination != source_corpus
            for match in self.find_correspondences(
                source_corpus, destination, kind=kind, node=node,
                feature=feature, value=value,
                from_node=from_node, to_node=to_node,
                include_approximate=include_approximate,
                source_version=source_version,
            )
        )


def find_across_corpora(source_corpus: str, **query: Any) -> tuple[Correspondence, ...]:
    return MappingCatalog().find_across_corpora(source_corpus, **query)


def list_corpora() -> tuple[str, ...]:
    return MappingCatalog().list_corpora()


def map_native(corpus: str, **selector: Any) -> tuple[Mapping, ...]:
    return MappingCatalog().map_native(corpus, **selector)


def find_by_target(target: str, **query: Any) -> tuple[Mapping, ...]:
    return MappingCatalog().find_by_target(target, **query)


def find_correspondences(source_corpus: str, target_corpus: str,
                         **query: Any) -> tuple[Correspondence, ...]:
    return MappingCatalog().find_correspondences(source_corpus, target_corpus, **query)


def resolve_nodes(api: Any, mapping: Mapping, *,
                  corpus_version: str | None = None) -> tuple[int, ...]:
    """Execute one mapped value selector against an *already loaded* TF API."""
    if mapping.kind != "value" or mapping.target is None or mapping.relation in _NON_MATCHING:
        raise MappingError("only a positive word/node feature-value mapping can select TF nodes")
    if corpus_version is not None and mapping.corpus_version is not None and corpus_version != mapping.corpus_version:
        raise MappingError("loaded corpus version differs from the mapped source version")
    try:
        nodes = api.F.otype.s(mapping.node)
        feature = api.Fs(mapping.feature)
        return tuple(n for n in nodes
                     if (observed := feature.v(n)) is not None
                     and str(observed) == mapping.value)
    except (AttributeError, KeyError, TypeError) as exc:
        raise MappingError(f"{mapping.corpus}: required TF feature or node type unavailable") from exc
