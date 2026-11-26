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
from pathlib import Path
import subprocess
from urllib.parse import quote
from xml.etree import ElementTree as ET

from tfont.xml_mappings import MappingCatalog


ROOT = Path(__file__).resolve().parents[2]
REPO = "https://github.com/alexsosn/ontoTF"
DATA = "docs/research/data"
QUEUE = DATA + "/generated/i026/p004-work-queue.json"
SNAPSHOTS = DATA + "/pages-current-schema-snapshots.json"
PSEUD = DATA + "/generated/i017/pseudepigrapha-v1.0.0.json"
ONTOLOGIES = ("OLiA", "OntoLex-Lemon", "LRMoo", "CIDOC CRM", "CRMtex", "SKOS", "CRMinf", "Other")
POSITIVE = {"exact", "close", "broader", "narrower", "related"}
# Explicit namespace prefixes, not substring matching or dereferencing.
PREFIXES = {
    "OLiA": ("http://purl.org/olia/", "https://purl.org/olia/"),
    "OntoLex-Lemon": ("http://www.w3.org/ns/lemon/ontolex#", "https://www.w3.org/ns/lemon/ontolex#"),
    "LRMoo": ("http://iflastandards.info/ns/lrm/lrmoo/", "https://iflastandards.info/ns/lrm/lrmoo/"),
    "CIDOC CRM": ("http://www.cidoc-crm.org/cidoc-crm/", "https://www.cidoc-crm.org/cidoc-crm/"),
    "CRMtex": ("http://www.cidoc-crm.org/crmtex/", "https://www.cidoc-crm.org/crmtex/"),
    "SKOS": ("http://www.w3.org/2004/02/skos/core#", "https://www.w3.org/2004/02/skos/core#"),
    "CRMinf": ("http://www.cidoc-crm.org/crminf/", "https://www.cidoc-crm.org/crminf/"),
}
WORKSTREAMS = ("C", "D", "E", "F", "G", "H")
WORKSTREAM_NAMES = ("OLiA", "OntoLex + SKOS", "CRM + CRMtex", "LRMoo", "CRMinf", "Residual")
WARP = {"otype", "oslots", "otext"}


def ontology(iri):
    return next((name for name, prefixes in PREFIXES.items()
                 if any(iri.startswith(prefix) for prefix in prefixes)), "Other")


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


def summarize(rows, inventory, version):
    groups = defaultdict(list)
    for row in rows:
        groups[(row.corpus_version, row.selector)].append(row)
    positive = {k for k, group in groups.items()
                if any(r.relation in POSITIVE for r in group)}
    exact = {k for k, group in groups.items() if any(r.relation == "exact" for r in group)}
    # Keep inventories that cannot be compared visible but never use them as denominators.
    schema = None
    if inventory is not None and version is not None and inventory["version"] == version:
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
        "ontology_targets": sorted({r.target for r in rows if r.relation in POSITIVE}),
        "ontologies": {name: {
            "selectors": len(entry["selectors"]),
            "schema": None if schema is None else len(entry["schema"]),
            "targets": len(entry["targets"]),
        } for name, entry in by_ontology.items()},
        "inventory": None if inventory is None else {
            k: v for k, v in inventory.items() if k not in
            {"node_types", "node_features", "edge_features"}
        },
    }


def read_json(root, path):
    return json.loads((root / path).read_text(encoding="utf-8"))


def inventories(root):
    result = {}
    for path in sorted((root / DATA / "generated/r005").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not {"corpus_id", "tf_version", "node_types", "node_features", "edge_features"} <= data.keys():
            continue
        result[data["corpus_id"]] = {
            "version": data["tf_version"], "revision": data.get("revision"),
            "source": path.relative_to(root).as_posix(),
            **{name: sorted(data[name]) for name in ("node_types", "node_features", "edge_features")},
        }
    data = read_json(root, PSEUD)
    result["pseudepigrapha"] = {
        "version": data["release"]["tf_version"], "revision": data["release"]["commit"],
        "source": PSEUD,
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
    corpora = []
    for corpus in catalog.list_corpora():
        xml = ET.parse(catalog_path / (corpus + ".xml")).getroot()
        version = xml.get("corpusVersion")
        stats = summarize(catalog.load(corpus), inv.get(corpus), version)
        stats.update(corpus=corpus, version=version, source=xml.get("source"))
        corpora.append(stats)
    comparable = [c for c in corpora if c["schema_total"] is not None]
    totals = {key: sum(c[key] for c in corpora)
              for key in ("declarations", "reviewed", "positive", "exact", "qualified", "nonpositive")}
    totals.update({key: sum(c[key] for c in comparable)
                   for key in ("schema_total", "schema_positive", "schema_reviewed")})
    totals.update(corpora=len(corpora), comparable_corpora=len(comparable),
                  targets=len({t for c in corpora for t in c["ontology_targets"]}))
    totals["ontologies"] = {name: {
        "selectors": sum(c["ontologies"][name]["selectors"] for c in corpora),
        "schema": sum(c["ontologies"][name]["schema"] for c in comparable),
    } for name in ONTOLOGIES}
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
    for c in corpora:
        count_rows.append([mapping(c), h(c["version"] or "unpinned"),
                           number(c["exact"]), number(c["qualified"]), number(c["nonpositive"]),
                           number(c["reviewed"]), rate(c["schema_positive"], c["schema_total"]),
                           rate(c["schema_reviewed"], c["schema_total"])])
        cells = [mapping(c)]
        for name in ONTOLOGIES:
            stat = c["ontologies"][name]
            cells.append(number(stat["selectors"]) +
                         '<small>' + (number(stat["schema"]) + " / " + number(c["schema_total"])
                                       if c["schema_total"] is not None else "—") + '</small>')
        cells.append(number(c["positive"]))
        matrix.append(cells)
        inv = c["inventory"]
        source = "No matching inventory."
        if inv:
            url = inv["source"]
            if not url.startswith("https://"):
                url = blob + quote(url, safe="/")
            source = link(url, "Inventory evidence") + " · TF " + h(inv["version"])
            if inv.get("revision"):
                source += " · revision " + h(inv["revision"][:12])
            if inv.get("type_source"):
                source += " · " + link(inv["type_source"], "Node type evidence")
            if c["schema_total"] is None:
                source += " (not comparable to mapping version)"
        details = ""
        if c["schema_unmapped"] is not None:
            details += '<p>Without positive mapping: ' + ", ".join(h(x) for x in c["schema_unmapped"]) + '</p>'
            details += '<p>Without any schema-linked disposition: ' + ", ".join(h(x) for x in c["schema_unreviewed"]) + '</p>'
        details += '<p>Selectors without a positive target: ' + (
            ", ".join(h(k) + " " + number(v) for k, v in c["nonpositive_status"].items()) or "none"
        ) + '</p>'
        gaps.append('<details><summary>' + h(c["corpus"]) + ' · ' +
                    rate(c["schema_positive"], c["schema_total"]) +
                    '</summary><p>' + source + " · " + mapping(c) + '</p>' + details + '</details>')
    count_rows.append(["<strong>Total</strong>", "—", *[number(totals[k]) for k in
                      ("exact", "qualified", "nonpositive", "reviewed")],
                       rate(totals["schema_positive"], totals["schema_total"]),
                       rate(totals["schema_reviewed"], totals["schema_total"])])
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
        ("Positive selectors", number(totals["positive"]), "of " + number(totals["reviewed"]) + " reviewed"),
        ("Schema coverage", rate(totals["schema_positive"], totals["schema_total"]),
         "at least one positive mapping"),
        ("Exact selectors", number(totals["exact"]), "qualified: " + number(totals["qualified"])),
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
code{font-size:.85em}footer{margin-top:2rem;color:var(--muted);font-size:.85rem}
</style></head><body><main>
<header><strong>ontoTF / TFont</strong><nav>""" + link(REPO, "GitHub") + """ · <a href="progress.json">Download data</a></nav></header>
<h1>Mapping progress</h1><p class="muted">Current development XML catalog. Mapping counts describe native semantic categories, not individual corpus tokens, identity links, or released-wheel support.</p>
<p class="muted">Source commit """ + link(REPO + "/commit/" + quote(commit, safe=""), commit[:12]) + """</p>
<section class="metrics" aria-label="Summary">""" + cards_html + """</section>
<h2>Corpus coverage</h2><p>Exact takes precedence over qualified when one selector has multiple positive targets. Native-only, ambiguous and unsupported selectors are reviewed dispositions without a positive target.</p>""" + table(
        ("Corpus", "TF version", "Exact", "Qualified", "No positive target", "Reviewed selectors", "Schema positive", "Schema touched"),
        count_rows, f"Schema totals cover {totals['comparable_corpora']} of {totals['corpora']} corpora with version-matching inventories.") + """
<h2>Corpus × ontology</h2><p>Each cell shows distinct positive versioned selectors; the smaller line is schema items with at least one positive mapping to that ontology / all comparable schema items in the corpus. Ontologies can overlap. The schema denominator is not an ontology-specific eligibility count.</p>""" + table(
        ("Corpus", *ONTOLOGIES, "Unique positive"), matrix,
        "Selectors and schema coverage, by ontology. A dash means no comparable inventory.") + """
<h2>Schema gaps and evidence</h2><p>One schema item is a native node type, node feature or edge feature. A partially mapped feature counts once. TF warp/configuration and optional unloaded provenance features are excluded; other technical or native-only categories can remain in the denominator. A version match is not authentication of source bytes. The tracker does not assert that every schema item needs an ontology target.</p>""" + "".join(gaps) + """
<h2>Historical semantic work plan</h2><p>The P-004 inventory groups ontology workstreams and includes selected feature values. Its 934-item baseline excludes later corpora and uses older revisions for some datasets. It is not the denominator for the XML selector totals above. Current ontology-specific eligibility and exhaustive node-scoped value denominators are not yet established.</p>""" + table(
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
