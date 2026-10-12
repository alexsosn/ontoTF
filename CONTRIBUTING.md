# Contributing to TFont

TFont prioritizes researcher-facing cross-corpus correspondences. For routine source-supported mapping additions, use **one batch, one PR, one independent adversarial review pass and one final-head CI run**. Reuse existing research and contract tests; do not create separate tickets or releases per value. New runtime/schema behavior still uses research → plan → TDD in the same PR.

## Ticket types

- **Research (`R`)** — evidence gathering and an explicit recommendation; no production implementation.
- **Plan/design (`P`)** — architecture and contracts derived from completed research.
- **Implementation (`I`)** — TDD changes against an approved plan or sufficiently narrow existing contract.
- **Review/follow-up** — defects or questions found by independent review.

## Pull-request contract

Every PR must:

1. name its parent issue;
2. state the gate it satisfies (research, design, implementation);
3. list acceptance criteria and evidence that each is satisfied;
4. preserve native corpus semantics and provenance;
5. document unsupported or approximate mappings rather than hiding them;
6. receive independent skeptical review before merge when it changes research conclusions, architecture, mappings, schemas, runtime behavior, or public documentation.

## Research PRs

If a mapping requires new source research, record the essential source evidence under `docs/research/` **in the same PR as the mapping batch**. Small scripts and inventories are appropriate only when needed for reproducibility; routine mapping batches reuse existing evidence. Independent research-only PRs are optional, not a mandatory stage.

Each research document should contain:

- scope and question;
- sources/evidence inspected, including exact corpus/ontology versions where possible;
- observed requirements and constraints;
- alternatives considered;
- licensing and redistribution implications;
- effects on agent and human users;
- recommendation;
- rejected alternatives;
- unresolved questions;
- acceptance-criteria traceability.

## F-series research ownership

F-series research metadata is the sole allocation authority; plans, workflows, and test packages only claim an existing allocation.

Every `docs/research/F-NNN-*.md` artifact must include exactly one canonical ownership line in its metadata header: `**Issue:** #N`.

Multiple research, evidence, or amendment artifacts may use the same `F-NNN` only when they all declare the same issue owner.

Every F-series plan under `docs/plans/F-NNN-*.md` must repeat the allocated issue in its metadata header as `**Issue:** #N`.

Every focused F-series workflow under `.github/workflows/fNNN-*.yml` or `.github/workflows/fNNN-*.yaml` must carry `# Issue: #N` within its first 12 physical lines. The workflow claim must match the issue allocated by F-series research metadata.

Every present `tests/fNNN` package must contain `tests/fNNN/issue-owner.txt` with exactly `Issue: #N` (an optional final newline is allowed). A test-module comment or package filename does not substitute for the sidecar.

Research-only F-series features are valid: a research allocation does not require a plan, focused workflow, or test package. Conversely, a downstream plan, workflow, or test package does not allocate a feature ID by itself.

Run `python scripts/check_f_series_ownership.py` before opening or finalizing a PR that adds or changes F-series ownership metadata. For an explicit repository root, run `python scripts/check_f_series_ownership.py .`. The checker validates research authority first, then rejects missing, malformed, unknown, or conflicting downstream claims.

## Design PRs

Designs belong in `docs/plans/`. They must define stable contracts before code, including version compatibility, error behavior, provenance, extensibility, serialization, and how approximate mappings are represented.

New public contracts need design evidence before implementation, but the design and implementation belong in one PR whenever feasible. Routine ledger-row additions under a validated contract require no new design artifact.

## Implementation PRs

Use TDD. Tests should make semantic compatibility claims executable. For corpus mappings, include negative tests proving that non-equivalent native concepts are not accidentally treated as exact equivalents.

## Review

The final reviewer should work from the issue, research/design artifact, diff, and upstream evidence rather than trusting the PR description. A mergeable review must address semantic fidelity, licensing, versioning, distribution, ergonomics, and test adequacy where applicable.

Logical independence means a separate evidence-first, counterexample-driven review pass that challenges the mapping claims; it **may be performed by the same agent**, without pretending to be another reviewer. Record concrete objections and their disposition in the PR. Material semantic changes after review require renewed review of the affected final head. An ordinary mapping review does not require a signed packet, identity certificate, or protected attestation workflow.
