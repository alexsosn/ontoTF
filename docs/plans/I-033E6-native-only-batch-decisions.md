# I-033E6 — no-target proposal/review contract

Research: `docs/research/I-033E6-native-only-batch-decisions.md`.

1. Ledger v1 remains exact-only. Ledger v2 uses the same closed keys, pinned
ontology lock, source registry and word/sp defaults. Each row has an explicit
`assessment` (`exact` or `native-only`) and nonempty rationale. Native-only
requires JSON null `term_key`; exact requires a registered class term. Empty
ontology evidence registry is allowed for a v2 all-native-only cohort; the
trusted batch lock is still validated. No term evidence is fabricated.
2. Generate unreviewed Mapping v2-shaped candidates. Exact identities remain
unchanged. Native-only identity is `mapping:{corpus}:{model}-native-sp-{value}`,
scoped to corpus, native selector and pinned batch ontology model. It has only
native evidence, `native_state: native-only`, and empty projections, ambiguous
candidates and external references. Existing native dependency and capability
identities apply; no runtime adapter or source acquisition is added.
3. Packet version equals ledger version. V1 presentation and bytes remain
unchanged. V2 includes exact/native-only counts; native-only row target, formal
kind and projection digest are null, assessment is native-only. Its semantic
role remains annotation-value, not an implied target. Commit the full candidate,
rationale, source pin, intended coverage identity and version in decision digest.
4. Verification always rebuilds the packet using the same validated resource
loader. Offline predicate recognizes packet v2 but grants no authority; live
protected gate retains fresh permission/review/head checks. Reject assessment
substitution and target injection even if an author recomputes packet hashes.
No workflow, publisher or approval identity changes.
5. TDD: verify RED for conservative/mixed and all-native-only packets; then
GREEN. Exercise exact v1 bytes, injected target/projection, missing source,
duplicates, rationale changes, stale pins, schema downgrade, review rejection
and needs-evidence, and candidate-evidence transport through protected live
revalidation. Existing published parity/coverage negative tests preserve frozen
native-only decisions. Run focused suites, research/full suite and wheel gates.
6. Independently instantiated skeptical reviewer examines source definitions,
no-target contract, compatibility, tests and authority boundaries. Material
corrections require another review; merge only reviewed exact head after CI.
