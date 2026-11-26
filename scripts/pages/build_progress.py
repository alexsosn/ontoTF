"""Build the static, read-only mapping progress page from repository sources.

No generated mapping ledger is committed. A schema item is a type, feature or
edge name; a reviewed selector is a versioned, node-scoped XML selector.
The two units cannot be divided by one another.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from html import escape
import json
import re
from pathlib import Path
import subprocess
from urllib.parse import quote
from xml.etree import ElementTree as ET

from tfont.xml_mappings import MappingCatalog
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
                classification = {label: {
                    "candidates": sum(key[0] == kind for key, _ in items),
                    "routed": sum(key[0] == kind and any(rule_matches(r, key) for r in all_rules)
                                  for key, _ in items),
                } for kind, label in KINDS.items()}
                stats["applicability"] = {"status": "partial", "ontologies": eligible,
                    "classification": classification, "source": spec["source"],
                    "rationale": spec["rationale"]}
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


def h(value):
    return escape(str(value), quote=True)


def link(url, label):
    # Inventory URL can be external only over HTTPS, never an executable URI.
    if not url.startswith("https://"):
        return h(label)
    return '<a href="' + h(url) + '">' + h(label) + '</a>'


def rate(n, d):
    if n is None or d is None or not d:
        return "—"
    return f"{n:,} / {d:,} ({100*n/d:.1f}%)"


def bar(n, d):
    text = rate(n, d)
    if n is None or d is None or not d:
        return text
    # The adjacent numeric text is the accessible label, so the visual bar is decorative.
    return text + f'<meter min="0" max="{d}" value="{n}" aria-hidden="true"></meter>'


def number(value):
    return "—" if value is None else f"{value:,}"


def table(headers, rows, caption):
    head = "".join(f'<th scope="col">{h(x)}</th>' for x in headers)
    body = "".join('<tr><th scope="row">' + cells[0] + '</th>' +
                   "".join("<td>" + cell + "</td>" for cell in cells[1:]) + "</tr>"
                   for cells in rows)
    return ('<div class="scroll"><table><caption>' + h(caption) +
            '</caption><thead><tr>' + head + '</tr></thead><tbody>' + body +
            '</tbody></table></div>')


def render(report):
    totals = report["totals"]
    corpora = report["corpora"]
    commit = report["commit"]
    blob = REPO + "/blob/" + quote(commit, safe="") + "/"
    mapping = lambda c: link(blob + "src/tfont/mappings/" + quote(c["corpus"], safe="") + ".xml",
                             c["corpus"])
    count_rows = []
    matrix = []
    gaps = []
    scoped_rows = []
    eligible_rows = []
    scoped_details = []
    for c in corpora:
        count_rows.append([mapping(c), h(c["version"] or "unpinned"),
                           number(c["exact"]), number(c["qualified"]), number(c["nonpositive"]),
                           rate(c["positive"], c["reviewed"]), bar(c["schema_positive"], c["schema_total"]),
                           bar(c["schema_reviewed"], c["schema_total"])])
        cells = [mapping(c)]
        for name in ONTOLOGIES:
            stat = c["ontologies"][name]
            cells.append(number(stat["selectors"]) +
                         '<small>' + (number(stat["schema"]) + " / " + number(c["schema_total"])
                                       if c["schema_total"] is not None else "—") + '</small>')
        cells.append(number(c["positive"]))
        matrix.append(cells)
        scoped = c.get("scoped")
        if scoped is None:
            scoped_rows.append([mapping(c)] + ["—"] * 6)
        else:
            scoped_rows.append([mapping(c), *[
                rate(scoped[label]["positive"], scoped[label]["total"]) +
                "<small>" + rate(scoped[label]["reviewed"], scoped[label]["total"]) + " reviewed</small>"
                for label in KINDS.values()],
                rate(scoped["node_values"]["positive_occurrences"], scoped["node_values"]["occurrences"])])
            domains = [[h(d["node"]), h(d["feature"]),
                        rate(d["positive"], d["total"]), rate(d["reviewed"], d["total"]),
                        rate(d["positive_occurrences"], d["occurrences"]),
                        h(", ".join(d["unreviewed_values"])) or "—"] for d in scoped["domains"]]
            edge_domains = [[h(d["feature"]), h(d["source"]), h(d["target"]),
                             rate(d["positive"], d["total"]), rate(d["reviewed"], d["total"]),
                             h(", ".join(d["unreviewed_values"])) or "—"] for d in scoped["edge_domains"]]
            guard_rows = [[h(g["node"]), h(g["feature"]), h(g["status"]),
                           rate(g["observations"], g["node_count"])] for g in scoped["guarded_nodes"]]
            outstanding = []
            for label, key in (("Outside observed domain", "outside_values"),
                               ("Unmeasured mapped values", "unmeasured_values"),
                               ("Overflow domains", "overflow_domains"),
                               ("Outside observed edge values", "outside_edge_values"),
                               ("Unmeasured edge values", "unmeasured_edge_values"),
                               ("Edge value overflow", "edge_overflow_domains"),
                               ("Cross-version edges (no local pair types)", "cross_version_edges")):
                if scoped[key]:
                    outstanding.append("<p>" + h(label) + ": " + h("; ".join(
                        " / ".join(v or "*" for v in x) if isinstance(x, list) else x for x in scoped[key])) + "</p>")
            scoped_details.append("<details><summary>" + h(c["corpus"]) +
                " · " + rate(scoped["node_values"]["positive"], scoped["node_values"]["total"]) +
                "</summary><p>" + link(blob + scoped["source"], "Exact source inventory") +
                " · TF " + h(scoped["tf_version"]) + " · SHA-256 <code>" +
                h(scoped["tf_files_sha256"]) + "</code></p>" +
                (table(("Node", "Feature", "Positive values", "Reviewed values",
                        "Positive annotations", "Unreviewed values"), domains,
                       "Every selected complete observed domain, with real node scope.") if domains else
                 "<p>No selected complete node-value domains.</p>") +
                (table(("Edge feature", "Source", "Destination", "Positive values", "Reviewed values", "Unreviewed values"),
                       edge_domains, "Selected complete observed edge-value domains.") if edge_domains else "") +
                (table(("Node", "Presence guard", "Disposition", "Guard-bearing nodes"), guard_rows,
                       "Conditional node mappings (excluded from unconditional node-type counts).") if guard_rows else "") +
                "".join(outstanding) + "</details>")
        applicability = c.get("applicability")
        eligible_cells = [mapping(c)]
        for model in ONTOLOGIES[:-1]:
            stat = applicability["ontologies"].get(model) if applicability else None
            if stat is None:
                eligible_cells.append("—")
            else:
                eligible_cells.append(rate(stat["positive"], stat["eligible"]) +
                    "<small>" + h(f'{stat["exact"]} exact · {stat["qualified"]} qualified') +
                    "</small><small>" + h(f'{stat["global_nonpositive"]} global no-target · {stat["ambiguous"]} ambiguous · {stat["other_target"]} other target · {stat["unreviewed"]} no decision') +
                    "</small>" + ("<small>Unmatched policy rules</small>" if stat["unmatched_rules"] else ""))
        eligible_cells.append("Incomplete" if applicability else "Unclassified")
        eligible_rows.append(eligible_cells)
        if applicability and scoped_details:
            labels = {"node_types": "Node types", "node_features": "Scoped features",
                      "node_values": "Selected node values", "edge_pairs": "Edge pairs",
                      "edge_values": "Selected edge values"}
            classification = applicability["classification"]
            routed = "; ".join(f"{labels[k]}: {v['routed']}/{v['candidates']}"
                              for k, v in classification.items() if v["candidates"])
            details = "<p>" + link(applicability["source"], "Applicability evidence") + " · " + h(applicability["rationale"]) + "</p>"
            details += "<p>Observed units routed to at least one model (separate units, not an overall completion ratio): " + h(routed) + ".</p>"
            scoped_details[-1] = scoped_details[-1].removesuffix("</details>") + details + "</details>"
        inv = c["inventory"]
        source = "No matching inventory."
        if inv:
            url = inv["source"]
            if not url.startswith("https://"):
                url = blob + quote(url, safe="/")
            source = link(url, "Inventory evidence") + " · TF " + h(inv.get("tf_version", inv["version"]))
            if inv.get("tf_version") and inv["tf_version"] != inv["version"]:
                source += " · catalog " + h(inv["version"])
            if inv.get("release_evidence"):
                source += " · " + link(inv["release_evidence"], "Release identity evidence")
            if inv.get("revision"):
                source += " · revision " + h(inv["revision"][:12])
            if inv.get("type_source"):
                source += " · " + link(inv["type_source"], "Node type evidence")
            if c["schema_total"] is None:
                source += " (not comparable to mapping version or explicit revision)"
        details = ""
        if c["schema_unmapped"] is not None:
            details += '<p>Schema items with positive mappings: ' + " · ".join(
                h(label) + " " + rate(c["schema_breakdown"][key]["positive"],
                                       c["schema_breakdown"][key]["total"])
                for key, label in (("type", "Node types"), ("feature", "Node features"), ("edge", "Edge features"))
            ) + '</p>'
            details += '<p>Without positive mapping: ' + ", ".join(h(x) for x in c["schema_unmapped"]) + '</p>'
            details += '<p>Without any schema-linked disposition: ' + ", ".join(h(x) for x in c["schema_unreviewed"]) + '</p>'
        details += '<p>Selectors without a positive target: ' + (
            ", ".join(h(k) + " " + number(v) for k, v in c["nonpositive_status"].items()) or "none"
        ) + '</p>'
        if c["value_domains"]:
            domain_rows = [[h(d["feature"]), h(", ".join(d["scopes"])),
                            rate(d["positive"], d["total"]), rate(d["reviewed"], d["total"]),
                            number(len(d["outside_inventory"]))]
                           for d in c["value_domains"]]
            details += table(("Feature", "Observed scopes", "Positive values", "Reviewed values",
                              "Declared outside list"), domain_rows,
                             "Complete observed value lists for features with XML value dispositions; values pooled across scopes.")
        else:
            details += '<p>No complete comparable observed value lists for mapped features are available in this inventory.</p>'
        gaps.append('<details><summary>' + h(c["corpus"]) + ' · ' +
                    rate(c["schema_positive"], c["schema_total"]) +
                    '</summary><p>' + source + " · " + mapping(c) + '</p>' + details + '</details>')
    scoped_rows.append(["<strong>Total</strong>", *[
        rate(totals["scoped"][label]["positive"], totals["scoped"][label]["total"]) +
        "<small>" + rate(totals["scoped"][label]["reviewed"], totals["scoped"][label]["total"]) + " reviewed</small>"
        for label in KINDS.values()],
        rate(totals["scoped"]["node_values"]["positive_occurrences"], totals["scoped"]["node_values"]["occurrences"])])
    count_rows.append(["<strong>Total</strong>", "—", *[number(totals[k]) for k in
                      ("exact", "qualified", "nonpositive")], rate(totals["positive"], totals["reviewed"]),
                       bar(totals["schema_positive"], totals["schema_total"]),
                       bar(totals["schema_reviewed"], totals["schema_total"])])
    matrix.append(["<strong>Total</strong>", *[
        number(totals["ontologies"][name]["selectors"]) + '<small>' +
        number(totals["ontologies"][name]["schema"]) + " / " + number(totals["schema_total"]) +
        '</small>' for name in ONTOLOGIES], number(totals["positive"])])
    legacy = report["historical_workstreams"]
    old_rows = [[h(c), *[number(counts.get(w, 0)) for w in WORKSTREAMS],
                 number(sum(counts.values()))] for c, counts in sorted(legacy.items())]
    old_rows.append(["<strong>Total</strong>", *[number(sum(x.get(w, 0) for x in legacy.values()))
                    for w in WORKSTREAMS], number(report["historical_total"])])
    cards = [
        ("Positive observed values", rate(totals["scoped"]["node_values"]["positive"], totals["scoped"]["node_values"]["total"]),
         "selected scoped categories · " + number(totals["scoped_corpora"]) + " corpora"),
        ("Reviewed observed values", rate(totals["scoped"]["node_values"]["reviewed"], totals["scoped"]["node_values"]["total"]),
         "selected categorical families only"),
        ("Schema coverage", rate(totals["schema_positive"], totals["schema_total"]),
         "at least one positive mapping · " + number(totals["comparable_corpora"]) + " comparable corpora"),
        ("Positive selectors", number(totals["positive"]), "of " + number(totals["reviewed"]) + " reviewed"),
        ("Core ontologies", number(sum(totals["ontologies"][o]["selectors"] > 0 for o in ONTOLOGIES[:-1])) + " / 7",
         number(totals["corpora"]) + " corpora"),
    ]
    cards_html = "".join('<div class="metric"><span>' + h(label) + '</span><strong>' +
                         h(value) + '</strong><small>' + h(subtitle) + '</small></div>'
                         for label, value, subtitle in cards)
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapping progress · ontoTF</title>
<style>
:root{color-scheme:light dark;--bg:#f7f8fa;--panel:#fff;--ink:#17212a;--muted:#526272;--line:#dce1e6;--link:#075d98;--accent:#17694e}
@media(prefers-color-scheme:dark){:root{--bg:#14191f;--panel:#1b232b;--ink:#e8eef4;--muted:#a9b8c5;--line:#38434d;--link:#8dcaf4;--accent:#83d7b1}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,sans-serif}
main{max-width:1280px;margin:auto;padding:2rem clamp(1rem,3vw,2.5rem) 4rem}a{color:var(--link)}
header{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:1rem}
h1{font-size:clamp(2rem,4vw,2.8rem);line-height:1.15;margin:1.5rem 0 .4rem;letter-spacing:-.04em}
h2{font-size:1.3rem;margin:2.5rem 0 .4rem}p{max-width:95ch;margin:.5rem 0 1rem}
.muted,small{color:var(--muted)}small{display:block;font-size:.78rem}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:.8rem;margin:1.5rem 0}
.metric{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:1rem}
.metric strong{display:block;color:var(--accent);font-size:1.65rem;letter-spacing:-.025em;font-variant-numeric:tabular-nums;margin:.3rem 0}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:.875rem;font-variant-numeric:tabular-nums}
caption{text-align:left;padding:.8rem 1rem;color:var(--muted);font-size:.8rem}
th,td{padding:.75rem .8rem;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child{text-align:left}thead th{background:var(--bg);font-size:.8rem}tbody th{font-weight:500}
tr:last-child td,tr:last-child th{border-bottom:0}tbody tr:last-child{background:var(--bg)}
details{padding:.7rem 0;border-bottom:1px solid var(--line)}summary{cursor:pointer;font-weight:600}details p{overflow-wrap:anywhere;font-size:.88rem}
meter{display:block;width:100%;height:.65rem;min-width:5rem;accent-color:var(--accent);margin-top:.2rem}code{font-size:.85em}footer{margin-top:2rem;color:var(--muted);font-size:.85rem}
</style></head><body><main>
<header><strong>ontoTF / TFont</strong><nav>""" + link(REPO, "GitHub") + """ · <a href="progress.json">Download data</a></nav></header>
<h1>Mapping progress</h1><p class="muted">Current development XML catalog. Mapping counts describe native semantic categories, not individual corpus tokens, identity links, or released-wheel support.</p>
<p class="muted">Source commit """ + link(REPO + "/commit/" + quote(commit, safe=""), commit[:12]) + """</p>
<section class="metrics" aria-label="Summary">""" + cards_html + """</section>
<h2>Corpus coverage</h2><p>Exact takes precedence over qualified when one selector has multiple positive targets. Native-only, ambiguous and unsupported selectors are reviewed dispositions without a positive target. Selector counts include all declared versions; schema counts use only the comparable default version. Individual entity declarations are excluded.</p>""" + table(
        ("Corpus", "Catalog version", "Exact", "Qualified", "No positive target", "Positive / reviewed", "Schema positive", "Schema touched"),
        count_rows, f"Schema totals cover {totals['comparable_corpora']} of {totals['corpora']} corpora with compatible pinned inventories.") + """
<h2>Corpus × ontology</h2><p>Each cell shows distinct positive versioned selectors; the smaller line is schema items with at least one positive mapping to that ontology / all comparable schema items in the corpus. Ontologies can overlap. The schema denominator is not an ontology-specific eligibility count.</p>""" + table(
        ("Corpus", *ONTOLOGIES, "Unique positive"), matrix,
        "Selectors and schema coverage, by ontology. A dash means no comparable inventory.") + """
<h2>Observed scoped coverage</h2><p>Positive / observed, with reviewed counts below. The inventory includes actual node-feature combinations, actual directed edge pairs and selected complete categorical domains from pinned TF artifacts. Guarded node mappings are reported separately. Feature mappings do not cover individual values. Valued edge categories are counted separately from whole-edge mappings. Annotation-weighted coverage counts feature-value observations (not unique tokens).</p>""" + table(
        ("Corpus", "Node types", "Node features by scope", "Selected node values", "Directed edge pairs", "Selected edge values", "Positive annotations"),
        scoped_rows, f"Real scoped evidence for {totals['scoped_corpora']} of {totals['corpora']} corpora; categorical families are selected, not exhaustive.") + """
""" + "".join(scoped_details) + """
<h2>Ontology applicability review (partial)</h2><p>Positive / eligible within explicitly selected research families. These are review domains, not guaranteed ontology matches or complete denominators. A global native-only or unsupported disposition is shown separately; it does not prove that every ontology was evaluated. Ambiguous and other-target counts are separate. A dash indicates no researched scope, not zero applicable items. All corpus-wide applicability inventories remain incomplete.</p><p>""" + link(blob + APPLICABILITY, "Family-level applicability policy and source evidence") + """</p>""" + table(
        ("Corpus", *ONTOLOGIES[:-1], "Eligibility completeness"), eligible_rows,
        "Partial source-grounded review families; no aggregate completion percentage.") + """
<h2>Schema gaps and evidence</h2><p>One schema item is a native node type, node feature or edge feature. A partially mapped feature counts once. TF warp/configuration and optional unloaded provenance features are excluded; other technical or native-only categories can remain in the denominator. A version match is not authentication of source bytes. Complete observed value lists are shown only for already mapped feature families where the inventory provides them; values are pooled across native scopes and may include technical categories. No corpus-wide value completion rate is inferred. The tracker does not assert that every schema item needs an ontology target.</p>""" + "".join(gaps) + """
<h2>Historical semantic work plan</h2><p>The P-004 inventory groups ontology workstreams and includes selected feature values. Its """ + number(report["historical_total"]) + """-item baseline excludes later corpora and uses older revisions for some datasets. It is not the denominator for the XML selector totals above. The historical plan remains separate; the current scoped evidence and partial applicability counts above do not establish exhaustive ontology-specific eligibility.</p>""" + table(
        ("Corpus", *WORKSTREAM_NAMES, "Total"), old_rows,
        "Historical P-004 routed semantic items; planned workload, not current progress ratios.") + """
<footer>Generated from the """ + link(REPO + "/tree/" + quote(commit, safe="") + "/src/tfont/mappings", "authoritative XML catalog") + " and " + link(blob + QUEUE, "historical work queue") + """. No corpus text is redistributed by this page. <a href="progress.json">Machine-readable statistics</a>.</footer>
</main></body></html>
"""


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
