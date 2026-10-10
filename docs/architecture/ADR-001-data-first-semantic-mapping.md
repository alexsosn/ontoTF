# ADR-001 — Data-first ontology mapping, batched review and release generation

**Status:** Proposed for architecture review, 2026-10-10  
**Scope:** ontoTF P-004 (#202), #290 (mapping factory), #291 (CI consolidation), #225 (Agora packaging).  
**Decision authority:** this ADR is a proposed migration contract, **not** a claim that the new compiler already exists.

## 1. Evidence-based problem statement

The production semantic runtime is not the main bottleneck: source bundle validation, content-bound semantic digests, compiled indexes (`native_index`, `semantic_index`), exact resolver and TF-native executor already exist. The **authoring/release path** couples every new correspondence to handwritten Mapping v2, duplicated profile/dependency resources, a new immutable coverage manifest, a one-off Python coverage builder and a new workflow.

At audit time:
- `main` contained **82 separate GitHub Actions workflow YAML files**, **214 Python test files**, nine full versioned corpus-profile trees (0.1/0.2/0.3 for BHSA/Syriac/ExtraBiblical), and hard-coded `PRODUCTION_*_CORPORA` / version / evidence dictionaries in `src/tfont/production_bundles.py`.
- Draft #289: **four** POS mappings required **30 files**, **32 commits**, **6,298 inserted lines** and triggered **26 workflows on its head**. Its 0.4.0 releases copy historic noun/morphology/verb mapping documents, parent manifests and whole coverage manifests.
- Past #282 full suite ran **1,065 tests in approximately 191 seconds** on a Python runner; old Syriac-specific tests also asserted permanent absence of future ExtraBiblical functionality. A newly supported corpus broke that obsolete test, requiring another exact-head CI/review cycle.
- P-004 current queue: **934 semantic identities**, 15 technical exclusions; 50 production-reviewed dispositions (23 with shared targets and 27 native-only), **884 not yet production reviewed**. 934 identities are *not* 934 OWL classes or 934 justified target equivalences.
- Only OLiA is currently vendored under `src/tfont/resources/ontologies`, although P-004 targets seven models (OLiA, OntoLex-Lemon, SKOS, CIDOC CRM, CRMtex, LRMoo, CRMinf). Further target-ontology onboarding must not require seven separate bespoke runtime implementations.

This overhead is caused by data representation, release granularity and repeated CI—not by the necessity of native-source or ontology review.

## 2. Decision: three authority planes, two stages of publication

### Plane A: pinned *source facts* (append-only per source revision)

- `registry/corpora/{corpus}/{source_rev}.json`: TF component ID, exact parent/content digest, licensed source pin, available node/feature/value scopes.
- `registry/evidence/{corpus}/{source_rev}/*.json`: extracted native definitions, original source coordinates, checksums, explicit gloss/enum-only distinction, source-to-target-revision relationship. One registry entry can serve many mappings.
- `registry/ontologies/{model}/{snapshot}.json`: exact source ontology file(s), license and integrity lock, term/class/property catalogue and term-level evidence. Include cross-model bridges only when independently reviewed, do not assume OWL classes for every textual annotation.
- `registry/coverage/baselines/{corpus}.json`: **immutable** denominators and original research accounting, with 934-item P-004 routing identity preserved.

The source corpora remain external. Do not store raw licensed corpus data in ontoTF and do not convert TF into a triplestore.

### Plane B: compact *semantic decisions* (the only ordinary hand-edited mapping data)

A stable, schema-checked append-only ledger under `decisions/{corpus}/{workstream}.yaml` (or JSONL if diffs prove better). A representative conceptual entry:

```yaml
id: bhsa:sp:adjv
corpus: bhsa
component: bhsa-tf
source_revision: 4db00e2157915495e1a4d3d57e41223df24775da
native: {node_type: word, feature: sp, value: adjv}
disposition: exact
target: {ontology: olia, term: "http://purl.org/olia/olia.owl#Adjective"}
evidence: [bhsa:sp:source-table, olia:Adjective:class]
coverage_ids: ['node_value:sp="adjv"']
rationale: "Source definition and target ontology both denote adjective POS category"
```

A different item may be `native-only`, `ambiguous`, `unsupported` or `needs-research` with **no** shared target. A decision's target/assessment must never be inferred from identical value names across corpora (notably ExtraBiblical MQL enum-only POS codes). Approximations (`close`, `broader`, `narrower`, `related`) keep direction, loss notes and execution eligibility separate from `exact`.

The identity `coverage_ids` makes accounting explicit; not every native feature and all its values receive automatic coverage just because one mapping exists. A row may be reviewed without creating a runtime projection.

### Plane C: *review authority*, separate from declaration

A proposed `disposition: exact` is **not** authoritative simply because someone wrote `review.status: reviewed` into JSON. The mapping compiler computes canonical row/mapping/projection digests; an independently recorded review must bind to those digests and the pinned evidence. Require **PR-level independent adversarial review with per-row decisions**, and verify exact-head approval identity at the release gate. The developer's own self-declared review metadata cannot substitute for independent approval. Store immutable review receipts in released artifacts so fully offline installed packages still validate digests and provenance.

Use independent reviewers to evaluate *semantic assertions*, not to repeatedly inspect 2,500 lines of unchanged coverage JSON. The reviewer can approve a group of homogeneous low-risk rows but records exceptions individually; high-risk LRMoo/CRMinf assertions require specific rationales. Failed/uncertain rows remain unreviewed, never silently promoted by CI.

## 3. One deterministic compiler, ordinary changes are data changes

Implement the following as CLI and importable Python APIs. **These are new target interfaces, not existing commands.**

```text
tfont mappings validate [--changed]      # source/term/shape/denominator/approval gates
tfont mappings build [--check]            # Mapping v2, Projection v1, digest, dependency IR
tfont mappings diff <base> <candidate>    # semantic-only changed rows + evidence
tfont mappings coverage [--check]         # current counts from baseline + decisions
tfont mappings release <release-id>       # immutable published snapshots only at gate
```

The compiler must preserve existing `SemanticSourceBundle`, `validate_semantic_bundle`, `compile_semantic_ir` and execution contracts. **Do not first rewrite the working runtime.** Generated Mapping v2/Projection v1 output must be byte-for-byte deterministic, identical in semantics to present hand-built resources, including RFC8785 digests and content-bound reviews.

- No ordinary per-mapping Python builder or GitHub Actions YAML.
- No ordinary copying of previous `noun.json`, `noun-morphology.json`, `verb.json` or parent manifest. New bundle profiles **reference immutable resource IDs** and add only new ledger rows.
- A single generated `current` coverage view joins exactly the immutable corpus denominator with published review decisions, while retaining historical releases and their original digests. Do not re-emit complete 934-row queue snapshots for ordinary mapping edits.
- Build native→semantic and semantic→native indexes from the same accepted rows; no second hand-maintained reverse mapping.
- No false `common_target` for native-only assessments; inspect both disposition count and unique target families.

## 4. Generic ontology/profile loader — no OLiA switch in core code

After compiler parity, replace new-feature-specific loaders with:

```python
load_profile(corpus_id, release_id="current", models=("olia",))
load_mapping_catalog(corpus_id, *, release_id="current", include_native_only=True)
```

The corpus/ontology/release registry resolves profile, evidence and ontology resource references from a versioned pack manifest. Preserve `load_production_noun_bundle`, `load_production_linguistic_bundle`, `load_production_verb_bundle` and other existing public entrypoints as **immutable historical compatibility wrappers**, not copies of the same profile in every new release.

One ontology adapter contract should support OLiA, OntoLex-Lemon, SKOS, CIDOC CRM, CRMtex, LRMoo and CRMinf by registering their distinct domain/range and semantic relations. Do not flatten these models into `owl:Class` equality: e.g., manuscript objects, bibliographic expressions, inference acts and linguistic word categories have different ontological semantics. Keep TF data/native query execution unmodified.

Design registry packs to be optionally installed per model/corpus via Agora, importing nothing from an unavailable corpus. Exact ontology locks and licensing must remain inspectable.

## 5. CI and review: one batch, one PR, one final-head gate

**Change classes:**
1. **Decision-only batch:** 10–50 corpus-specific homogeneous reviewed candidates in **one PR**, not one ticket/PR per value. Pinned source facts and ontology terms are reused. For difficult cases, individually review rows inside the same PR.
2. **New source revision / ontology snapshot:** perform source research and add reusable evidence registry; deep external checkout tests only when those source locks change.
3. **Schema/runtime/compiler architectural changes:** normal research + design + TDD RED→GREEN gate, negative/fuzz tests and separately accountable implementation review.

Consolidate 82 per-ticket workflow files into **one always-running PR workflow** with stable named checks: fast contract (~<90 seconds goal, not measured), evidence/source job when needed, final-head Python 3.10 and 3.12 full regression plus wheel packaging. Full suite must run on the exact SHA that is merged, and no skipped path-filter check may satisfy branch protection accidentally. Cache installs and deduplicate test discovery. CI should validate final output, not manufacture its review approval.

**TDD RED is local or an exploratory draft check**, not a purposely broken final PR. Generator changes get RED unit/contract tests; ordinary row additions run existing parametric tests and evidence checks. Avoid permanent “corpus X is unsupported” tests; assert historical release stability and unknown-corpus failure instead.

The independent reviewer receives a generated **semantic diff**:
`source text / code → selected TF selector → candidate ontology term + RDF kind → relation/qualification → evidence + reviewer objections → expected coverage delta`. The changed-row digest is bound to the review. A release PR merges by expected head only after fresh independent review and all required checks.

## 6. Migration / acceptance (ordered; keep old outputs readable)

**Phase 0 — Stop amplification now.** Do not create new ticket-specific workflows/builders/profile versions for each new POS value. Batch nearby work, reuse frozen source and ontology facts. Complete existing #289 under current safety gates rather than rewriting it mid-PR. Document current CI/test baselines.

**Phase 1 — Compiler parity pilot (#290).** In one PR, create schema, ledger and generator with at least ten real candidate native items (positive and conservative). Import existing reviewed mappings without semantic change; compare compiled vs existing `mapping`, `projection`, `evidence`, `profile` and coverage semantics. Mutate missing evidence, wrong ontology term kind, altered source pin, stale digest, forged approval, wrong native selector and denominator to prove fail-closed behavior. Migrate no legacy public API yet.

**Phase 2 — Single CI owner (#291).** Enumerate unique tests in all 82 workflows, preserve failure coverage, replace overlapping workflows with one stable CI ownership map. Run controlled PR head before/after to measure workflow starts, runner-minutes, critical path and failure detection. Never delete an unaccounted-for unique test or required check.

**Phase 3 — Registry loader / multi-model packs (#290 / P-004).** Ship `load_profile` with old loader compatibility. Add at least one non-OLiA model as a real ontology pack before claiming multi-model architecture is mature; record class/property/role semantics and redistribution constraints.

**Phase 4 — Bulk semantic throughput.** Workstream-specific batches following the source-evidence queue. Full P-004 means 934 individually accountable native items, **not** 934 exact ontology targets. Distinguish complete-reviewed-denominator, usable positive mappings, actual cross-corpus resolvability and remaining native-only/unsupported/research states.

## 7. Measurable exit criteria

- An ordinary **10-item** mapping batch edits at most three authored semantic artifact files; no new bespoke workflow/builder, no copied full historic coverage manifest or profile tree.
- ≥10 reviewed corpus-native decisions per ordinary PR (target 20–50 for homogeneous families); semantic accuracy and conservative uncertainty remain non-negotiable.
- A new POS value must not trigger core Python changes or copy previous mappings just to become discoverable.
- A normal candidate head triggers ~3–5 CI jobs rather than 26 historical workflows; Python 3.10/3.12 final-head full regression is still required.
- Compiler reproduces legacy reviewed bundle semantics and exact current coverage metrics with **zero unreviewed auto-promotions**.
- Runtime uses a registry of pinned source/ontology packs while preserving the old API and TF-native execution.
- Final accepted review corresponds to the exact approved content digest and evidence; independent skepticism remains a gate.

## Explicitly rejected alternatives

1. **Loosen schema/review integrity** to gain speed — this sacrifices the reason ontoTF exists.
2. **Flatten all seven ontologies into one vocabulary** — false equivalence.
3. **Keep handwritten versioned copy-forward for every value** — demonstrated to be unscalable.
4. **Replace the TF-native query runtime with RDF storage** — unnecessary and out of scope.
5. **Treat 934 denominator rows as 934 direct OLiA mappings** — incorrect task model.
6. **Remove full regression entirely** — keep it, run once on the final head rather than redundantly for every intermediate authoring step.

## Status / unresolved design choices

- Ledger format (YAML vs JSONL) and review-receipt trust implementation require an empirical pilot. The reviewer must not be replaceable by an unchecked `reviewed: true` literal.
- Whether to commit generated runtime output in the repository, publish it as build artifacts, or both: choose after comparing wheel reproducibility, offline corpus deployments and Git review ergonomics.
- Version identifiers should name **coherent immutable mapping packs**, not increment for each noun/adjective/verb value.
- Keep license validation (including BY-NC source data) separate from metadata publication; review ontology/data redistribution before registering non-OLiA packs.

**Disposition:** Replace the per-item authoring/release architecture incrementally via #290 and #291, preserving today's runtime semantics and historical audit trail.
