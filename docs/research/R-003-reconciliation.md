# R-003 reconciliation history

**Status:** historical reconciliation record; the canonical R-003 report is authoritative  
**Recorded:** 2026-09-05

This file records why `docs/research/R-003-ergonomics.md` was consolidated after R-005, R-001, and R-002 were accepted. It is not a second normative contract.

The original R-003 draft was written before the final upstream research contracts stabilized. Independent review then identified four classes of drift:

1. parent compatibility was described using revision/schema shorthand rather than R-001's component-aware parent identity and complete dependency-closure model;
2. mapping assessment and RDF/OWL/SKOS publication formalization were collapsed into one generic relation field;
3. R-005 research-stage candidate strengths risked being read as executable mapping assessments;
4. dense TF empty records needed an explicit non-semantic rule.

Those changes are now folded directly into the canonical R-003 report and its single measurable acceptance-test list.

## Accepted dependencies

- R-005 reviewed head `48c8bd78d0c3a0501b2fdec6946db5df90517bdb`, merged as `a9c4d74d4de2f9a15eb1464dce341ecd2f92f898`.
- R-001 reviewed head `68b88a820f5519ad65d46b732679a6278e9ca3c9`, merged as `a22a95084a1518882d1e3e87d10e9757121f106d`.
- R-002 reviewed head `d82e6ef2726f149f903eb43ddbfb615faf399cd5`, merged as `a554d4fdc36c8854519064f3a7611b80efa29622`.

## Consolidated rules

The canonical report now requires:

- `verified-exact | verified-compatible | unverified | incompatible` compatibility states;
- exact identity over a parent component manifest covering every semantically addressable native component;
- complete dependency-closure validation before a changed component set becomes `verified-compatible`;
- non-executable `unverified` and `incompatible` states;
- ontoTF mapping assessment separated from optional publication relation;
- all eight R-002 assessment meanings preserved;
- no automatic promotion from R-005 `S/C/B/N/R/U/L` evidence to executable mappings;
- dense empty-string/`None` TF records excluded from semantic domains unless the source explicitly assigns them meaning;
- one canonical set of 48 measurable implementation criteria.

Future changes belong in the canonical report. This historical record should only be amended when the reason or dependency trace for a reconciliation changes.
