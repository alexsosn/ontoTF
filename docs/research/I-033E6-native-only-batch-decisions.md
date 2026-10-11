# I-033E6 — conservative batch decisions (#312)

## Observed contracts and source evidence

`batch_proposals.compile_candidate_batch` accepts only exact word/sp class
proposals. `review_packets.build_review_packet` assumes one projection per
candidate. Neither can express a reasoned no-target decision.

Mapping v2 (`src/tfont/schemas/mapping.schema.json`, mapping state rules) already
allows `native_state: native-only` with zero projections and zero ambiguous
candidates. `semantic_validation._validate_record_states` enforces that rule.
The Mapping v2 semantic digest binds native state, native binding and evidence;
the review request additionally binds rationale and the whole candidate.

Frozen `p004-i027b1-bhsa-verb-v1/bhsa.json` has 27 reviewed BHSA `vs` accounting
items with `assessments: [native-only]`, `common_target: false` and authority
`i027a:bhsa-vs-pinned-source-review`. `batch_compiler._compile_native_only`
reproduces these coverage decisions. These are **coverage records, not 27
existing Mapping v2 records**. They must remain immutable. This ticket does not
reinterpret their stems or introduce a `vs` source template.

The bounded initial candidate source template remains word-level `sp`. The
installed BHSA evidence `evidence:bhsa:word-sp-adj-adv-source` points to original
`ETCBC/bhsa` revision `4db00e2157915495e1a4d3d57e41223df24775da`,
`docs/features/sp.md`: line 21 defines `advb` as adverb, line 30 `adjv` as
adjective. The original extract was inspected alongside the packaged record.
It documents word and lex nodes; the production binding is word only. Installed
Syriac evidence retains the independent original and TF target revisions
documented in I-033E5. A withheld projection changes no original definition.

For exact projections, the installed OLiA snapshot remains revision
`d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6`, SHA256
`5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd`.
The packaged evidence and RDF define Adjective/Adverb as owl:Class. Their
existence does not force an author or reviewer to propose a shared projection.
Existing source/ontology licensing and locks are reused unchanged; no new
dependency, ontology snapshot, source revision or redistribution exception.

## Alternatives and recommendation (project choice)

1. Keep every candidate positive: rejected, since this rewards forced ontology
equivalence and excludes legitimate conservative outcomes.
2. Introduce a generic coverage-only decision language: deferred. It would need
new authority, capability and denominator contracts spanning features. The
historical coverage-only cohort cannot be passed off as a mapping cohort.
3. Use existing Mapping v2 native-only state for new, explicitly source-bound
word/sp proposals: recommended bounded slice. Emit no projection, external
reference, ambiguous candidate or ontology evidence binding. The batch's pinned
ontology metadata scopes the proposed interoperability assessment; it is not a
target. Reviewers still decide whether native-only is justified. Uncertainty
awaiting evidence can remain the external `needs-evidence` disposition rather
than a manufactured scholarly conclusion.

## Compatibility and limits

Use opt-in ledger and packet schema version 2 for conservative or mixed cohorts.
Version 1 remains exact-only and byte-identical. Structured review body v1 and
live reviewer identity rules remain valid: they bind packet and row digests,
independent of target presence. The trusted gate must explicitly accept packet
v2 only after rebuilding it from the source ledger.

Tests may withhold a projection for an already documented adjective/adverb
to exercise the contract. That is a test proposal, **not a new semantic decision
or a reversal of a released exact mapping**. There is no publisher in this slice,
and no proposal may delete/promote inherited reviewed native-only decisions.
New source templates, generic coverage decisions, immutable overlay publication
and an externally attested genuinely new 10+ item cohort remain under #303/#290.
