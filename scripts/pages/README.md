# Mapping progress dashboard

This page is a static report generated from the same authoritative XML files that the development package reads. It neither changes mappings nor ships corpus text.

## Build and preview

From the repository root with Python 3.12 or newer:

```sh
python -m pip install -e .
python -m unittest tests.test_progress_tracker -v
python -m scripts.pages.build_progress --out /tmp/ontotf-pages
python -m http.server 8000 --directory /tmp/ontotf-pages
```

Open http://localhost:8000. The output contains only `index.html` and `progress.json`; no API credentials, JavaScript, or external runtime dependencies are required. The source commit and inventory evidence links are shown on the page.

## Accounting

- A reviewed category selector (excluding individual entity-kind declarations) is a distinct (corpus, corpus version, kind, node, feature, value, from, to) key. Multiple target IRIs do not multiply this count. Exact takes precedence over qualified; ambiguous candidates, native-only and unsupported are not positive.
- An ontology column counts distinct positive selectors and distinct schema items. A selector may belong to multiple ontology columns; the unique-positive total is a union. Unrecognized namespaces are grouped as Other.
- A schema item is a node type, node feature or edge feature, counted once by name and kind. Mapping one feature value counts as touching the feature, not as completing its entire value domain. A node mapping's surface-feature guard is not a mapping of the feature itself. Entity-kind links are not schema mappings.
- Schema inventories use existing pinned R-005 censuses, the Pseudepigrapha I-017 census, and the [pinned current ORACC/TLHdig schema snapshots](../../docs/research/data/pages-current-schema-snapshots.json) extracted from the upstream generated feature/type references. TLHdig's optional unloaded provenance features are excluded; TF warp/configuration names are excluded. Other native or technical features remain in the denominator.
- A missing, version-mismatched, or explicitly revision-mismatched inventory produces no schema rate; selector counts still appear. The combined schema rate uses only comparable corpora, explicitly labeled. Version strings alone do not authenticate corpus bytes.
- For mapped feature families only, complete observed value lists from compatible censuses show positive/reviewed values against their observed domain. Values are pooled across native scopes; this is neither full node-scoped coverage nor a claim that every observed value is semantic. Missing/truncated domain lists are not extrapolated. The JSON includes unreviewed and outside-inventory values and per-ontology intersections.
- The historical P-004 routed inventory is shown separately, preserving its original seven-corpus and grouped ontology counts. It cannot be divided into the current node-scoped selector counts. The dashboard does not invent an ontology-specific eligibility or exhaustive value denominator.

New mapping rows and corpus XML files appear automatically. An additional corpus inventory is optional; when absent the schema denominator remains unknown until source evidence is available. If upstream versions change, refresh the corresponding source inventory, not a manually maintained progress total.

## Pages deployment

The [Pages workflow](../../.github/workflows/pages-progress.yml) builds on relevant changes to main and on tracker PRs; only main can deploy. PR artifacts can be downloaded from Actions to preview the generated page. Enable **Settings → Pages → Build and deployment → Source: GitHub Actions** once if it is not already enabled. This repository's intended URL is https://alexsosn.github.io/ontoTF/. The workflow does not modify repository settings, publish a package, or commit generated reports.

The page should show the exact source commit used by the build. If the deployment fails, inspect the Pages workflow; a successful build artifact does not prove that the public site is live.
