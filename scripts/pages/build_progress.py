"""Build the static, read-only mapping progress page from repository sources.

No generated mapping ledger is committed. A schema item is a type, feature or
edge name; a reviewed selector is a versioned, node-scoped XML selector.
The two units cannot be divided by one another.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import re
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET

from tfont.xml_mappings import MappingCatalog
from scripts.pages.dashboard import render
from scripts.pages.scoped_progress import (
    ONTOLOGIES, POSITIVE, ontology, KINDS, scoped_progress, eligible_progress,
    observed_items, rule_matches,
)


ROOT = Path(__file__).resolve().parents[2]
REPO = "https://github.com/alexsosn/ontoTF"
DATA = "docs/research/data"
QUEUE = DATA + "/generated/i026/p004-work-queue.json"
SNAPSHOTS = DATA + "/pages-current-schema-snapshots.json"
PSEUD = DATA + "/generated/i017/pseudepigrapha-v1.0.0.json"
SCOPED = DATA + "/generated/scoped"
APPLICABILITY = DATA + "/scoped-applicability.json"
WORKSTREAMS = ("C", "D", "E", "F", "G", "H")
WORKSTREAM_NAMES = ("OLiA", "OntoLex + SKOS", "CRM + CRMtex", "LRMoo", "CRMinf", "Residual")
WARP = {"otype", "oslots", "otext"}


def schema_key(row):
    # A surface presence guard on a node mapping is not a feature mapping.
    # An individual entity link is not a schema-level category claim.
    if row.kind == "node":
        return "type:" + row.node
    if row.kind in {"value", "feature"}:
        return "feature:" + row.feature
    if row.kind == "edge":
        return "edge:" + row.feature
    return None


def observed_value_coverage(rows, inventory, version):
    """Count complete observed value lists at feature granularity, not scope products.

    Source censuses aggregate values across node types. A positive disposition
    in one of those types is evidence of a reviewed value somewhere, not every
    occurrence or every type. Only features already having value mappings are
    shown; this is deliberately not a corpus-wide semantic denominator.
    """
    by_feature = defaultdict(list)
    for row in rows:
        if row.kind == "value" and row.corpus_version in (None, version):
            by_feature[row.feature].append(row)
    result = []
    for feature, domain in sorted(inventory.get("value_domains", {}).items()):
        if feature not in by_feature:
            continue
        observed = set(domain["values"])
        scoped = [row for row in by_feature[feature] if row.node in domain["scopes"]]
        reviewed = {row.value for row in scoped} & observed
        positive = {row.value for row in scoped if row.relation in POSITIVE} & observed
        result.append({
            "feature": feature, "scopes": domain["scopes"],
            "total": len(observed), "positive": len(positive), "reviewed": len(reviewed),
            "unreviewed": sorted(observed - reviewed),
            "outside_inventory": sorted({row.value for row in scoped} - observed),
            "ontologies": {name: len({row.value for row in scoped
                if row.relation in POSITIVE and ontology(row.target) == name} & observed)
                for name in ONTOLOGIES},
        })
    return result


def summarize(rows, inventory, version, source_revision=None):
    rows = tuple(rows)
    groups = defaultdict(list)
    for row in rows:
        if row.kind == "entity":
            continue
        groups[(row.corpus_version, row.selector)].append(row)
    positive = {k for k, group in groups.items()
                if any(r.relation in POSITIVE for r in group)}
    exact = {k for k, group in groups.items() if any(r.relation == "exact" for r in group)}
    # Keep inventories that cannot be compared visible but never use them as denominators.
    schema = None
    if (inventory is not None and version is not None and inventory["version"] == version
            and (source_revision is None or inventory.get("revision") == source_revision)):
        schema = {
            prefix + ":" + name
            for prefix, field in (("type", "node_types"), ("feature", "node_features"),
                                  ("edge", "edge_features"))
            for name in inventory[field] if name not in WARP
        }
    touched, schema_positive = set(), set()
    by_ontology = {name: {"selectors": set(), "schema": set(), "targets": set()}
                   for name in ONTOLOGIES}
    unmapped_status = Counter()
    for key, group in groups.items():
        if key not in positive:
            # The loader allows multiple ambiguous candidates; count the selector once.
            unmapped_status[group[0].relation] += 1
        for row in group:
            sk = schema_key(row)
            # Only compare the exact version (or version-independent mappings).
            matches = schema is not None and row.corpus_version in (None, version) and sk in schema
            if matches:
                touched.add(sk)
            if row.relation not in POSITIVE:
                continue
            entry = by_ontology[ontology(row.target)]
            entry["selectors"].add(key)
            entry["targets"].add(row.target)
            if matches:
                schema_positive.add(sk)
                entry["schema"].add(sk)
    return {
        "declarations": len(rows),
        "individual_declarations": sum(row.kind == "entity" for row in rows),
        "reviewed": len(groups),
        "exact": len(exact),
        "qualified": len(positive - exact),
        "positive": len(positive),
        "nonpositive": len(groups) - len(positive),
        "nonpositive_status": dict(sorted(unmapped_status.items())),
        "schema_total": None if schema is None else len(schema),
        "schema_positive": None if schema is None else len(schema_positive),
        "schema_reviewed": None if schema is None else len(touched),
        "schema_unmapped": None if schema is None else sorted(schema - schema_positive),
        "schema_unreviewed": None if schema is None else sorted(schema - touched),
        "schema_breakdown": None if schema is None else {
            prefix: {"total": sum(k.startswith(prefix + ":") for k in schema),
                     "reviewed": sum(k.startswith(prefix + ":") for k in touched),
                     "positive": sum(k.startswith(prefix + ":") for k in schema_positive)}
            for prefix in ("type", "feature", "edge")
        },
        "value_domains": [] if schema is None else observed_value_coverage(rows, inventory, version),
        "ontology_targets": sorted({r.target for r in rows
                                    if r.kind != "entity" and r.relation in POSITIVE}),
        "ontologies": {name: {
            "selectors": len(entry["selectors"]),
            "schema": None if schema is None else len(entry["schema"]),
            "targets": len(entry["targets"]),
        } for name, entry in by_ontology.items()},
        "inventory": None if inventory is None else {
            k: v for k, v in inventory.items() if k not in
            {"node_types", "node_features", "edge_features", "value_domains"}
        },
    }


def read_json(root, path):
    return json.loads((root / path).read_text(encoding="utf-8"))


def complete_value_domains(features):
    return {name: {"values": sorted({str(v) for v in info["observed_values"]}),
                   "scopes": sorted(info["applies_to"])}
            for name, info in features.items()
            if info.get("domain_observation") == "observed_small_domain"
            and isinstance(info.get("observed_values"), list)
            and info.get("applies_to")
            and len({str(v) for v in info["observed_values"]}) == info.get("observed_unique_count")
            and info["observed_values"]}


def inventories(root):
    result = {}
    for path in sorted((root / DATA / "generated/r005").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not {"corpus_id", "tf_version", "node_types", "node_features", "edge_features"} <= data.keys():
            continue
        result[data["corpus_id"]] = {
            "version": data["tf_version"], "revision": data.get("revision"),
            "source": path.relative_to(root).as_posix(),
            "value_domains": complete_value_domains(data["node_features"]),
            **{name: sorted(data[name]) for name in ("node_types", "node_features", "edge_features")},
        }
    data = read_json(root, PSEUD)
    result["pseudepigrapha"] = {
        "version": data["release"]["tf_version"], "revision": data["release"]["commit"],
        "source": PSEUD,
        "value_domains": complete_value_domains(data["node_features"]),
        **{name: sorted(data[name]) for name in ("node_types", "node_features", "edge_features")},
    }
    # Latest available pinned schema-name evidence for these two converter versions.
    # This is a source inventory, not a mapping registry; new XMLs still auto-discover.
    result.update(read_json(root, SNAPSHOTS))
    return result


def build_report(root, commit):
    catalog_path = root / "src/tfont/mappings"
    catalog = MappingCatalog(catalog_path)
    inv = inventories(root)
    scoped_inventories = {}
    for path in sorted((root / SCOPED).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("corpus_id") != path.stem:
            raise ValueError(f"Scoped inventory identity mismatch: {path}")
        scoped_inventories[path.stem] = data
    policy_path = root / APPLICABILITY
    policy = read_json(root, APPLICABILITY) if policy_path.is_file() else {"corpora": {}}
    corpora = []
    for corpus in catalog.list_corpora():
        xml = ET.parse(catalog_path / (corpus + ".xml")).getroot()
        version = xml.get("corpusVersion")
        source = xml.get("source")
        pin = re.search(r"@([a-f0-9]{40})(?::|$)", source)
        rows = catalog.load(corpus)
        stats = summarize(rows, inv.get(corpus), version,
                          source_revision=pin.group(1) if pin else None)
        scoped = scoped_inventories.get(corpus)
        stats["scoped"] = scoped_progress(rows, scoped, source, version)
        stats["applicability"] = None
        spec = policy["corpora"].get(corpus)
        if stats["scoped"] is not None:
            stats["scoped"]["source"] = SCOPED + "/" + corpus + ".json"
            if (spec and spec["revision"] == scoped["revision"]
                    and spec["catalog_version"] == version):
                eligible = eligible_progress(rows, scoped, spec["rules"], version)
                # The inventory contains separate structural and value-level
                # candidate units; report classification by kind, not a summed
                # completion denominator. Several models may share candidates.
                all_rules = [rule for rules in spec["rules"].values() for rule in rules]
                items = list(observed_items(scoped))
                exclusions = spec.get("exclusions", [])
                routed_keys = {key for key, _ in items if any(rule_matches(r, key) for r in all_rules)}
                excluded_keys = {key for key, _ in items if any(rule_matches(r, key) for r in exclusions)}
                if routed_keys & excluded_keys:
                    raise ValueError(f"{corpus}: applicability and exclusion overlap")
                classification = {}
                for kind, label in KINDS.items():
                    candidates = {key for key, _ in items if key[0] == kind}
                    routed = candidates & routed_keys
                    excluded = candidates & excluded_keys
                    classification[label] = {
                        "candidates": len(candidates), "routed": len(routed),
                        "excluded": len(excluded),
                        "unclassified": len(candidates - routed - excluded),
                    }
                stats["applicability"] = {"status": "partial", "ontologies": eligible,
                    "classification": classification, "source": spec["source"],
                    "rationale": spec["rationale"], "exclusions": exclusions,
                    "unclassified_items": [list(key) for key, _ in items
                                           if key not in routed_keys and key not in excluded_keys]}
        stats.update(corpus=corpus, version=version, source=source)
        corpora.append(stats)
    comparable = [c for c in corpora if c["schema_total"] is not None]
    totals = {key: sum(c[key] for c in corpora)
              for key in ("declarations", "individual_declarations", "reviewed", "positive", "exact", "qualified", "nonpositive")}
    totals.update({key: sum(c[key] for c in comparable)
                   for key in ("schema_total", "schema_positive", "schema_reviewed")})
    totals.update(corpora=len(corpora), comparable_corpora=len(comparable),
                  targets=len({t for c in corpora for t in c["ontology_targets"]}))
    totals["ontologies"] = {name: {
        "selectors": sum(c["ontologies"][name]["selectors"] for c in corpora),
        "schema": sum(c["ontologies"][name]["schema"] for c in comparable),
    } for name in ONTOLOGIES}
    scoped_corpora = [c["scoped"] for c in corpora if c["scoped"] is not None]
    totals["scoped_corpora"] = len(scoped_corpora)
    totals["scoped"] = {
        label: {k: sum(c[label][k] for c in scoped_corpora)
                for k in ("total", "positive", "reviewed", "exact", "qualified",
                          "nonpositive", "unreviewed", "occurrences",
                          "positive_occurrences", "reviewed_occurrences")}
        for label in KINDS.values()
    }
    legacy = read_json(root, QUEUE)
    return {"commit": commit, "corpora": corpora, "totals": totals,
            "historical_workstreams": legacy["counts"]["per_corpus"],
            "historical_total": legacy["invariants"]["semantic_items"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    report = build_report(ROOT, commit)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "progress.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "index.html").write_text(render(report), encoding="utf-8")
    print(f"Built {args.out}: {report['totals']['reviewed']} reviewed selectors")


if __name__ == "__main__":
    main()
