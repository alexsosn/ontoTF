# I-033E11 — Batch-preflight for versioned native-only → exact supersession

Parent #329 / #300 / #290 / P-004 #202.

## Observed architecture bottleneck
I-033E10 (`src/tfont/mapping_supersession.py`) provides a fail-closed, **untrusted** plan for one native-only selector promoted to a source-pinned ontology class. `overlay_handoff.py` still forbids collision with inherited selectors, so the accepted-only path only adds new keys. Repeating a separate single-item release for promotions would recreate the original throughput problem.

## Architectural scope
Add a reusable deterministic **multi-transition preflight** for up to 50 accepted corpus-native decisions against one immutable base. Reuse the existing single-transition evidence/ontology/source checks for every row. Explicitly forbid duplicate retired selectors and retired/new mapping/projection IDs across the batch; stable ordering and content digest must be independent of input order. One independently validated base index, one coherent base release version. The batch is source-bound planning data only, never activation or approval.

Two genuine, immutable BHSA `0.4.0` sources anchor the pilot: native `word.sp=adjv` and `word.sp=advb` with original feature evidence and distinct pinned OLiA `Adjective`/`Adverb` class evidence. For tests only, build hypothetical earlier native-only versions of these reviewed mappings; these are **not historical published predecessors or GitHub approvals**.

## Trust boundary
No second reviewer is invented. This preflight neither consults nor impersonates GitHub review state, and its output must never be accepted by a release writer as an attestation. It may compute a hypothetical effective mapping ID/index fingerprint for comparison but must not return a production `SemanticSourceBundle` or mutate installed catalog. A separate protected, authenticated, independently reviewed publisher is necessary (parent #303/#329).

## RED/GREEN/review
TDD asserts a 2-item genuine corpus/ontology-backed synthetic fixture, stable order, zero base mutation, no duplicate active selector, no forged authority and fail-closed stale digest/source/ontology evidence. Implement the smallest pure helper around I-033E10's existing validator. Focused + exact-head full CI, then logically independent skeptical source and code review before merge.

This is a *single shared architecture capability*, not a ticket per corpus or ontology term.
