"""Researcher-facing presentation of the existing progress report."""
from html import escape
from urllib.parse import quote

from scripts.pages.scoped_progress import ONTOLOGIES

LABELS = {
    "node_types": "Node types", "node_features": "Features by node type",
    "node_values": "Measured source values", "edge_pairs": "Directed relationships",
    "edge_values": "Categorical edge values",
}
NAMES = {
    "bhsa": "BHSA", "cuc": "CUC", "syriac": "Syriac",
    "syrnt": "Syriac New Testament", "peshitta": "Peshitta",
    "extrabiblical": "Extra-biblical Hebrew", "tlhdig-tf": "TLHdig",
    "assyrian-royal-inscriptions": "Assyrian royal inscriptions",
    "pseudepigrapha": "Pseudepigrapha",
}
REPO = "https://github.com/alexsosn/ontoTF"


def h(value):
    return escape(str(value), quote=True)


def name(c):
    return h(NAMES.get(c["corpus"], c["corpus"]))


def percent(n, d):
    rounded = f"{100*n/d:.1f}%"
    if 0 < n < d:
        if rounded == "0.0%":
            return "&lt;0.1%"
        if rounded == "100.0%":
            return "&gt;99.9%"
    return rounded


def unknown(label):
    return '<span class="unknown">' + h(label) + '</span>'


def segments(parts, total):
    """Fixed shared scale; adjacent text is the accessible representation."""
    return '<div class="track" aria-hidden="true">' + "".join(
        f'<span class="{css}" style="width:{100*n/total:.8g}%"></span>'
        for css, n in parts if n
    ) + '</div>'


def coverage_bar(stat):
    if stat is None:
        return unknown("Unknown")
    total = stat["total"]
    if not total:
        return unknown("No observed items")
    exact, qualified, nonpositive, unreviewed = (
        stat[k] for k in ("exact", "qualified", "nonpositive", "unreviewed")
    )
    mapped = exact + qualified
    return (f'<div class="reading"><strong>{percent(mapped, total)}</strong>'
            f'<span>{mapped:,} / {total:,} mapped</span></div>'
            + segments([("exact", exact), ("qualified", qualified),
                        ("reviewed", nonpositive), ("remaining", unreviewed)], total)
            + f'<small>{exact:,} exact · {qualified:,} qualified · '
              f'{nonpositive:,} without positive match · {unreviewed:,} unreviewed</small>')


def annotation_bar(stat):
    if stat is None:
        return unknown("Unknown")
    total = stat["occurrences"]
    if not total:
        return unknown("No measured annotations")
    mapped = stat["positive_occurrences"]
    return (f'<div class="reading"><strong>{percent(mapped, total)}</strong>'
            f'<span>{mapped:,} / {total:,} annotations</span></div>'
            + segments([("mapped", mapped), ("remaining", total-mapped)], total))


def ontology_cell(stat, *, detailed=True):
    if stat is None:
        return unknown("Not assessed")
    total = stat["eligible"]
    warning = ('<small class="warning">Unmatched research rules</small>'
               if stat["unmatched_rules"] else "")
    if not total:
        return unknown("Empty scope") + warning
    mapped = stat["exact"] + stat["qualified"]
    pending = total - mapped
    compact = (f'<strong>{percent(mapped, total)}</strong>'
               + segments([("exact", stat["exact"]), ("qualified", stat["qualified"]),
                           ("remaining", pending)], total)
               + f'<small>{mapped:,} / {total:,}</small>')
    if not detailed:
        return compact + warning
    return (f'<strong>{percent(mapped, total)}</strong>'
            + segments([("exact", stat["exact"]), ("qualified", stat["qualified"]),
                        ("remaining", pending)], total)
            + f'<small>{mapped:,} / {total:,}</small>'
              f'<small>{stat["exact"]:,} exact · {stat["qualified"]:,} qualified</small>'
              f'<small>{stat["other_target"]:,} other ontology · '
              f'{stat["ambiguous"]:,} ambiguous · '
              f'{stat["global_nonpositive"]:,} global no-match · '
              f'{stat["unreviewed"]:,} unreviewed</small>' + warning)


def classification_bar(stat):
    total = stat["candidates"]
    if not total:
        return unknown("No observed items")
    routed, excluded, pending = (stat[k] for k in ("routed", "excluded", "unclassified"))
    return (f'<div class="reading"><strong>{percent(routed+excluded, total)}</strong>'
            f'<span>{routed+excluded:,} / {total:,} classified</span></div>'
            + segments([("exact", routed), ("reviewed", excluded),
                        ("remaining", pending)], total)
            + f'<small>{routed:,} selected for ontology assessment · '
              f'{excluded:,} excluded · {pending:,} unclassified</small>')


def labeled(label, body):
    return '<div class="measure"><h4>' + h(label) + '</h4>' + body + '</div>'


def domain_gaps(scoped):
    # Rank by the number of unreviewed annotations, then categories, within
    # each unit. A frequent native-only value is not a pending mapping.
    sections = []
    for key, title in (("domains", "Node-value gaps"), ("edge_domains", "Edge-value gaps")):
        domains = [d for d in scoped[key] if d["unreviewed"]]
        domains.sort(key=lambda d: (-(d["occurrences"]-d["reviewed_occurrences"]),
                                    -d["unreviewed"], d["feature"]))
        if not domains:
            message = "no unreviewed values in measured domains" if scoped[key] else "no measured domains"
            sections.append(f"<p>{title}: {message}.</p>")
            continue
        rows = []
        for d in domains:
            scope = d["node"] if key == "domains" else d["source"] + " → " + d["target"]
            preview = d["top_unreviewed_values"]
            labels = ", ".join(f"{value} ({freq:,})" for value, freq in preview)
            remainder = d["unreviewed"] - len(preview)
            more = (f'<small>{remainder:,} more · <a href="progress.json">Download full gap data</a></small>'
                    if remainder else "")
            rows.append('<li><strong>' + h(scope + " · " + d["feature"]) + '</strong>'
                        + f'<small>{d["unreviewed"]:,} unreviewed values · '
                          f'{d["occurrences"]-d["reviewed_occurrences"]:,} unreviewed annotations</small>'
                        + '<small class="wrap">' + h(labels) + '</small>' + more + '</li>')
        sections.append(f'<details><summary>{title} ({len(domains):,} domains)</summary>'
                        '<ul class="gaps">' + "".join(rows) + '</ul></details>')
    return "".join(sections)


def corpus_detail(c):
    scoped = c.get("scoped")
    app = c.get("applicability")
    if scoped is None:
        return "<p>Current scoped inventory unavailable.</p>"
    body = '<h3>Coverage by annotation type</h3><div class="detail-grid">' + "".join(
        labeled(label, coverage_bar(scoped[key])) for key, label in LABELS.items()
    ) + '</div><h3>Applicability research</h3>'
    if app is None:
        body += "<p>No compatible applicability research available.</p>"
    else:
        body += '<div class="detail-grid">' + "".join(
            labeled(label, classification_bar(app["classification"][key]))
            for key, label in LABELS.items()
        ) + '</div>'
    if app is not None:
        body += '<h3>Ontology assessment breakdown</h3><div class="detail-grid">' + "".join(
            labeled(model, ontology_cell(stat)) for model, stat in app["ontologies"].items()
        ) + '</div>'
    body += '<h3>Unreviewed native categories</h3>' + domain_gaps(scoped)
    omitted = sum(len(scoped[k]) for k in ("overflow_domains", "edge_overflow_domains"))
    cross = len(scoped["cross_version_edges"])
    if omitted or cross:
        body += (f'<p class="muted">Inventory limitations: {omitted:,} value domains exceed '
                 f'the census limit; {cross:,} cross-version edge features lack local pair coverage.</p>')
    return body



def source_link(url, label):
    if not isinstance(url, str) or not url.startswith("https://"):
        return h(label)
    return '<a href="' + h(url) + '">' + h(label) + '</a>'


def corpus_source(c, metadata):
    item = metadata.get("corpora", {}).get(c["corpus"], {})
    scoped = c.get("scoped")
    version = scoped["tf_version"] if scoped else None
    status = "Freshness unverified"
    if (version and version == item.get("checked_tf_version")
            and scoped["revision"] == item.get("checked_revision")):
        status = {"current": "Current at check", "update": "Update available"}.get(
            item.get("status"), status)
    description = '<small>' + h(item.get("description", "Corpus description unavailable.")) + '</small>'
    used = "TF " + h(version) if version else "TF version unverified"
    if c.get("version") and c["version"] != version:
        used += " · catalog " + h(c["version"])
    latest = " · upstream TF " + h(item["latest_tf_version"]) if item.get("latest_tf_version") else ""
    css = "warning" if status == "Update available" else "muted"
    return (description + '<small>' + used + latest + '</small>'
            + '<small class="' + css + '">' + h(status) + '</small>')


def corpus_provenance(c, metadata):
    item = metadata.get("corpora", {}).get(c["corpus"], {})
    scoped = c.get("scoped")
    repo = c.get("source", "").split("@", 1)[0].split(":", 1)[0]
    source = source_link("https://github.com/" + repo, "Corpus repository") if repo else "Source unavailable"
    revision = (source_link("https://github.com/" + repo + "/tree/" + scoped["revision"],
                            scoped["revision"][:12]) if repo and scoped else "Unknown")
    return ('<h3>Source and version</h3><p><strong>' + h(item.get("name", c["corpus"]))
            + '</strong> — ' + source + ' · census revision ' + revision + '</p><p>'
            + h(item.get("note", "No upstream comparison recorded.")) + ' '
            + source_link(item.get("evidence"), "Upstream evidence") + '</p>')


def ontology_sources(metadata):
    registry = metadata.get("ontology_registry", {})
    rows = []
    for model in ONTOLOGIES[:-1]:
        item = metadata.get("ontologies", {}).get(model, {})
        ref = registry.get(item.get("registry_id"), {})
        baseline = ref.get("version_or_date")
        matches = baseline is not None and baseline == item.get("checked_baseline")
        status = ("Current at check" if matches and item.get("status") == "current"
                  else "Update available" if matches and item.get("status") == "update"
                  else "Freshness unverified")
        rows.append('<article class="ontology-info"><h3>' + h(model) + '</h3><p>'
                    + h(ref.get("name", model)) + ' — ' + h(ref.get("scope", "Scope unavailable."))
                    + '</p><small>Reference baseline: ' + h(item.get("reference_version") if matches else baseline or "Unknown")
                    + ' · Latest stable reference: ' + h(item.get("latest_reference", "Unknown"))
                    + '</small><small class="' + ("warning" if status == "Update available" else "muted")
                    + '">' + h(status) + '</small><details><summary>Release evidence</summary><p>'
                    + h(item.get("note", "")) + ' ' + source_link(item.get("evidence"), "Upstream releases")
                    + '</p></details></article>')
    return '<div class="ontology-info-grid">' + "".join(rows) + '</div>'


STYLE = """
:root{color-scheme:light dark;--bg:#f7f8fa;--panel:#fff;--ink:#17212a;--muted:#526272;--line:#dce1e6;--link:#075d98;--exact:#17694e;--qualified:#4d7da6;--reviewed:#b28b42;--remaining:#dce1e6;--warn:#795300}
@media(prefers-color-scheme:dark){:root{--bg:#14191f;--panel:#1b232b;--ink:#e8eef4;--muted:#a9b8c5;--line:#38434d;--link:#8dcaf4;--exact:#70c8a4;--qualified:#8ab9df;--reviewed:#e4b85e;--remaining:#48535e;--warn:#f3cd85}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}
main{max-width:1200px;margin:auto;padding:1.5rem clamp(1rem,3vw,2.5rem) 4rem}a{color:var(--link);text-underline-offset:.2em}
a:focus-visible,summary:focus-visible{outline:2px solid var(--link);outline-offset:4px}
header,nav,.reading,.legend{display:flex;align-items:baseline;gap:.8rem;flex-wrap:wrap}
header{justify-content:space-between}nav{font-size:.875rem}
h1{font-size:clamp(2rem,4vw,2.75rem);letter-spacing:-.04em;margin:1.75rem 0 .4rem;line-height:1.15}
h2{font-size:1.4rem;letter-spacing:-.02em;margin:2.4rem 0 .5rem}
h3{font-size:1.05rem;margin:.5rem 0}h4{font-size:.85rem;margin:0 0 .35rem;font-weight:600}
p{max-width:80ch;margin:.4rem 0 1rem}.muted,small,.unknown{color:var(--muted)}
small{display:block;font-size:.75rem;line-height:1.45;margin-top:.25rem}
.snapshot{display:flex;gap:1.25rem;flex-wrap:wrap;margin:1.25rem 0;padding:1rem 0;border-block:1px solid var(--line)}
.snapshot .measure{flex:1 1 17rem}.snapshot .reading strong{font-size:1.65rem;font-variant-numeric:tabular-nums}
.legend{font-size:.8rem;margin:.8rem 0}.legend span{display:inline-flex;align-items:center;gap:.3rem}
.legend i{width:.75rem;height:.75rem;border-radius:2px;display:inline-block}
.mapped{background:var(--qualified)}.exact{background:var(--exact)}.qualified{background:var(--qualified)}.reviewed{background:var(--reviewed)}.remaining{background:var(--remaining)}
.track{display:flex;height:.65rem;background:var(--remaining);border-radius:3px;overflow:hidden;margin:.35rem 0}
.track span{flex:none}.reading{justify-content:space-between;gap:.25rem .75rem;font-variant-numeric:tabular-nums}
.reading strong{font-size:1.25rem}.reading span{font-size:.78rem;color:var(--muted)}
.corpus{padding:1rem 0;border-top:1px solid var(--line)}
.corpus-head{display:grid;grid-template-columns:minmax(9rem,1fr) repeat(2,minmax(0,2fr));gap:1.5rem;align-items:start}
.corpus-head h3{margin:0}.corpus-head h4{color:var(--muted)}
details{margin-top:.7rem}summary{cursor:pointer;color:var(--link);font-size:.875rem;padding:.35rem 0}
.detail-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,15rem),1fr));gap:1rem;margin:.75rem 0 1.25rem}
.morph-summary{margin:.8rem 0 0;padding:.6rem 0 0;border-top:1px solid var(--line)}.morph-summary p{font-size:.8rem;margin:.25rem 0}.morph-summary .detail-grid{margin:.5rem 0}.measure{min-width:0}.gaps{padding-left:1.3rem}.gaps li{margin:.5rem 0}.wrap{overflow-wrap:anywhere}
.ontology-row,.matrix-header{display:grid;grid-template-columns:minmax(8rem,1fr) minmax(0,7fr);gap:.8rem;align-items:center}
.ontology-row{border-top:1px solid var(--line);padding:.5rem 0}
.matrix-header{font-size:.75rem;color:var(--muted);font-weight:600;margin:.8rem 0}
.matrix-header .ontology-grid span{text-align:center}
.ontology-row h3{margin:0;font-size:.95rem}
.research-row{display:grid;grid-template-columns:minmax(9rem,1fr) minmax(0,3fr);gap:1rem;align-items:center;padding:.7rem 0;border-top:1px solid var(--line)}
.ontology-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:.5rem}
.ontology-cell{background:var(--panel);background:color-mix(in srgb,var(--exact) var(--strength),var(--panel));border:1px solid var(--line);border-radius:5px;padding:.55rem;min-width:0;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}
.ontology-cell strong{font-size:1.1rem}.ontology-cell h4{font-size:.75rem;position:absolute;clip-path:inset(50%);width:1px;height:1px;overflow:hidden}
.ontology-info-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,19rem),1fr));gap:1rem}.ontology-info{border-top:1px solid var(--line);padding:.6rem 0}.ontology-info p{font-size:.875rem;margin:.25rem 0}.ontology-info details{margin:.25rem 0}.unknown{font-size:.85rem}.warning{color:var(--warn)}
footer{border-top:1px solid var(--line);margin-top:2rem;padding-top:1rem;font-size:.85rem}
@media(max-width:900px){.ontology-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.matrix-header{display:none}.ontology-row{grid-template-columns:1fr;gap:.45rem}.ontology-cell h4{position:static;clip-path:none;width:auto;height:auto;overflow:visible}}
@media(max-width:650px){.corpus-head,.research-row{grid-template-columns:1fr;gap:.8rem}.ontology-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.ontology-cell h4{min-height:0}}
@media(max-width:320px){.ontology-grid{grid-template-columns:1fr}}
"""


def morphology_summary(scoped):
    if not scoped:
        return ""
    domain = next((d for d in scoped["domains"]
                   if d["node"] == "analysis" and d["feature"] == "morph"), None)
    if domain is None:
        return ""
    return ('<div class="morph-summary"><h4>Morphological analysis tags</h4>'
            '<p class="muted">Raw HFR tags, including alternatives. Frequencies count candidate analyses, not unique words or selected readings.</p>'
            '<div class="detail-grid">' + labeled("Distinct tags", coverage_bar(domain))
            + labeled("Candidate annotations", annotation_bar(domain)) + '</div></div>')


def render(report):
    corpora = report["corpora"]
    commit = report["commit"]
    metadata = report.get("source_status", {})
    commit_url = REPO + "/commit/" + quote(commit, safe="")
    scoped_count = sum(c.get("scoped") is not None for c in corpora)
    research_count = sum(c.get("applicability") is not None for c in corpora)
    pooled = report["totals"]["scoped"]["node_values"] if scoped_count else None
    rows, matrix, research_rows = [], [], []
    for c in corpora:
        scoped = c.get("scoped")
        values = scoped["node_values"] if scoped else None
        rows.append('<article class="corpus"><div class="corpus-head"><div><h3>'
                    + name(c) + '</h3>' + corpus_source(c, metadata)
                    + '</div>' + labeled("Source-value coverage", coverage_bar(values))
                    + labeled("Annotation coverage", annotation_bar(values))
                    + '</div>' + (morphology_summary(scoped) if c['corpus'] == 'tlhdig-tf' else '')
                    + '<details><summary>Structure, applicability and remaining work — '
                    + name(c) + '</summary>' + corpus_provenance(c, metadata) + corpus_detail(c) + '</details></article>')
        app = c.get("applicability")
        research_rows.append('<article class="research-row"><h3>' + name(c) + '</h3>'
                             + (classification_bar(app["classification"]["node_values"])
                                if app else unknown("Not assessed")) + '</article>')
        cells = []
        for model in ONTOLOGIES[:-1]:
            stat = app["ontologies"].get(model) if app else None
            strength = 0 if not stat or not stat["eligible"] else (
                22 * (stat["exact"] + stat["qualified"]) / stat["eligible"]
            )
            cells.append(f'<div class="ontology-cell" style="--strength:{strength:.5g}%"><h4>'
                         + h(model) + '</h4>' + ontology_cell(stat, detailed=False) + '</div>')
        matrix.append('<article class="ontology-row"><h3>' + name(c)
                      + '</h3><div class="ontology-grid">' + "".join(cells) + '</div></article>')
    return ("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapping progress · ontoTF</title><style>""" + STYLE + """</style></head>
<body><main><header><strong>ontoTF</strong><nav><a href="#coverage">Corpora</a>
<a href="#ontologies">Ontologies</a><a href="#models">Ontology guide</a><a href="#research">Research gaps</a><a href="#method">Method</a></nav></header>
<h1>Mapping progress</h1><p class="muted">Semantic coverage of Text-Fabric corpora in the current development catalog.</p>
<div class="snapshot">""" + (
        labeled("Mapped source values · pooled", coverage_bar(pooled))
        + labeled("Mapped annotations · pooled", annotation_bar(pooled))
    ) + """</div><p class="muted">""" +
    h(f"Compatible scoped inventories for {scoped_count} of {len(corpora)} corpora; partial applicability research for {research_count}. "
      "Pooled percentages weight larger measured domains more heavily.") + """</p><p class="muted">Upstream version checks: """ + h(metadata.get("checked_at", "not recorded")) + """. Status is based on the latest observed TF data release or published stable ontology reference; source editions and converter releases may differ.</p>
<section id="coverage"><h2>Coverage by corpus</h2>
<p>Compare mapped source values and the share of their observed annotations. Measured domains vary by corpus. TLHdig includes thousands of raw morphology tags, including composite alternatives; these count as distinct source values and may dominate the pooled value denominator. Compare across snapshots only when measured scopes match. The annotation bar combines exact and qualified mappings.</p>
<div class="legend"><span><i class="exact"></i>Exact</span><span><i class="qualified"></i>Qualified</span>
<span><i class="reviewed"></i>Reviewed without positive match</span><span><i class="remaining"></i>Unreviewed</span></div>
""" + "".join(rows) + """</section>
<section id="ontologies"><h2>Ontology coverage</h2>
<p>Mapped share of the researched scope for each corpus and ontology. All applicability research is partial; the percentages do not establish overall ontology completion. Other-ontology mappings do not contribute. Gray shows the researched share without a positive mapping to that ontology.</p><div class="matrix-header"><span>Corpus</span><div class="ontology-grid">""" +
    "".join('<span>' + h(model) + '</span>' for model in ONTOLOGIES[:-1]) +
    """</div></div>
""" + "".join(matrix) + """</section>
<section id="models"><h2>Ontology guide and versions</h2><p>Reference baselines used for mapping research. A current reference does not establish that every catalog mapping was validated against a version-locked ontology artifact.</p>""" + ontology_sources(metadata) + """</section>
<section id="research"><h2>Applicability research</h2>
<p>Share of measured node-feature values assigned to ontology research or explicitly excluded. Classification measures the scope of research; mapping coverage is tracked separately. Structural and edge categories are available in corpus details.</p>
""" + "".join(research_rows) + """</section>
<section id="method"><h2>Method and limitations</h2><details><summary>How coverage is calculated</summary>
<p>Each distinct observed node-scoped value or directed edge value is counted once, including a composite tag as one source value rather than multiple atomic grammatical categories. Exact and qualified (close, broader, narrower or related) mappings contribute to mapped coverage. Native-only, ambiguous and unsupported dispositions do not contribute. A whole-feature mapping does not cover its values. Annotation coverage weights selected node values by their frequency; it measures feature-value observations and may count multiple annotations of the same word. Guarded node mappings are excluded from unconditional node-type counts.</p>
<p>Applicability classification measures research of observed units within each kind. Selected units may be relevant to several ontologies. Exclusions follow the current granularity policy. Unclassified units require further research. Unknown scopes and empty measured scopes have no percentage. Open or overflowing value domains are not extrapolated. The report tracks development mappings; release readiness and execution support require separate tests.</p>
<p>Only one snapshot is available. Trend comparisons require comparable inventories over time.</p></details></section>
<footer>Source revision """ + '<a href="' + h(commit_url) + '">' + h(commit[:12]) + """</a> ·
<a href="progress.json">Download underlying statistics</a> · <a href="https://github.com/alexsosn/ontoTF">Project repository</a></footer>
</main></body></html>
""")
