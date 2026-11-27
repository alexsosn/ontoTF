# Research index

ontoTF begins with research-only tickets. Production mappings and runtime code are intentionally blocked until the foundational architecture questions are resolved.

## Required initial research

The initial research phase must establish:

1. **Distribution architecture** — where mappings live, how they bind to parent corpus versions, whether they are TF feature modules or semantic sidecars, whether one central repository or per-corpus repositories are preferable, and what Agora should own. Tracked by #1.
2. **Ontology governance** — supported ontology set, openness/licensing requirements, version pinning, deprecation, term stability, optional profiles, and policy for local concepts. Tracked by #2.
3. **Agent and human ergonomics** — semantic query discovery, capability reporting, mapping confidence/strength, explainability, error behavior, reproducibility, and scholar-facing inspection/editing workflows. Tracked by #3.
4. **Documentation architecture** — normative specifications versus generated reference material, per-corpus mapping documentation, ontology/version manifests, examples, machine-readable schemas, and how docs stay synchronized with mappings. Tracked by #4.
5. **Cross-corpus coverage baseline** — empirical inventory of the initial target corpora so later architecture is tested against real TF node/feature/edge semantics rather than BHSA alone. Tracked by #5.

## Research dependency order

Start #5 immediately. Tickets #1–#4 may gather external/architectural evidence in parallel, but they must not finalize recommendations that depend on corpus semantics until the relevant #5 census evidence is available. If #5 contradicts an assumption in another research draft, the draft must be revised before merge.

All five research tickets must be complete before the first POC design is approved. The later design ticket will reconcile their conclusions into one coherent architecture rather than treating each research recommendation as independently normative.

Each completed ticket should produce `R-XXX-*.md` with a recommendation and rejected alternatives.

## Research artifacts ready for review

- [R-005 corpus semantic census](R-005-corpus-semantic-census.md) — pinned empirical inventory of the initial TF corpus family, cross-corpus semantic matrix, Syriac compatibility decision, stress cases, and interoperability-query probes. Machine-readable pins and core counts are in [`data/R-005-corpus-pins.json`](data/R-005-corpus-pins.json).
