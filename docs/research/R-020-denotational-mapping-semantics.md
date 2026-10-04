# R-020 — denotational semantics for TFont mappings and query results

**Issue:** #231  
**Type:** research / feasibility only  
**Production behavior changed:** no  
**Baseline:** `main` after merged I-025 (#260)  
**Prototype:** `scripts/research/r020_denotational_semantics.py`  
**Frozen evidence:** `docs/research/data/generated/r020/denotational-semantics.json`

## Decision

Adopt a **small denotational verification model** for reasoning, tests, and explanations, but **defer a public/normative runtime API** until the adjacent composition/bounds/query-language studies R-021, R-022, and R-023 are complete.

The useful core is smaller than a general ontology semantics:

- every executable TFont semantic query for one corpus returns a set of corpus nodes;
- a reviewed native binding denotes a set of nodes in that corpus/query domain;
- a shared semantic target has a **reviewed represented corpus-relative extension** against the same node domain;
- that represented extension is distinct from any hypothetical annotation-independent “truth set” in the text;
- `exact`, `broader`, and `narrower` impose equality/inclusion constraints against the represented extension;
- reviewed approximation losses constrain how the actual answer may differ from that represented extension;
- refusal states such as unsupported, ambiguous, or absent capability are not empty denotations;
- `close` and `related` remain intentionally under-specified unless a separate reviewed loss contract provides a directional execution guarantee.

This model does not require RDF materialization, target-instance enumeration, a description-logic reasoner, or new corpus annotation.

## 1. Why “denotational” is useful here

Scott and Strachey's denotational-programming-language program separates implementation details from mathematical meaning by assigning mathematical objects to language constructs. TFont has a similar local need: separate the concrete TF feature/edge plan from the semantic claim the plan is reviewed to implement.

The analogy must not be overstretched. TFont is not defining a programming-language semantics in this ticket. The useful borrowing is the discipline:

```text
concrete native selector  ->  mathematical answer relation
```

rather than treating feature names, ontology labels, or implementation paths as meaning.

Primary background:

- Dana Scott and Christopher Strachey, *Toward a Mathematical Semantics for Computer Languages*, Oxford PRG-6, 1971: https://www.cs.ox.ac.uk/publications/publication3723-abstract.html
- Maurizio Lenzerini, *Data Integration: A Theoretical Perspective*, PODS 2002, DOI 10.1145/543613.543644.
- Ronald Fagin, Phokion Kolaitis, Renée Miller, Lucian Popa, *Data exchange: Semantics and query answering*, Theoretical Computer Science 336 (2005).
- Jérôme Euzenat and Pavel Shvaiko, *Ontology Matching*, 2nd ed., Springer 2013, DOI 10.1007/978-3-642-38721-0.
- W3C, *OWL 2 Web Ontology Language: Direct Semantics*, 2012: https://www.w3.org/TR/owl2-direct-semantics/
- W3C, *RDF Schema 1.1*, 2014: https://www.w3.org/TR/rdf-schema/

Database integration is especially relevant because it distinguishes source data, mappings, target semantics, and query answers rather than assuming one shared physical representation. Data exchange/certain-answer work is also a warning: query semantics under incomplete knowledge is a statement over possible interpretations/solutions, not a claim that one materialized representation is the target meaning.

Ontology-matching work is relevant because correspondences need not all mean equivalence; subsumption and other relations must remain distinct.

## 2. Do not identify ontology resources with result node sets

OWL/RDFS formally distinguish a class/resource from its extension. TFont needs the same distinction.

For a corpus `c`, corpus snapshot `s`, and reviewed query node domain:

```text
U(c,s) = the relevant TF node universe
```

For a native executable binding `b`:

```text
N(c,s,b) ⊆ U(c,s)
```

is the set of corpus nodes selected by that binding.

For a common semantic target `t`, distinguish two notions.

The **represented target extension** is:

```text
T_rep(c,s,t) ⊆ U(c,s)
```

It is the target meaning **as represented by the reviewed active TFont profile** on that corpus snapshot.

A stronger hypothetical set would be:

```text
T_truth(c,s,t) ⊆ U(c,s)
```

meaning every corpus node that would satisfy the semantic concept under an independent truth criterion, whether or not the corpus annotated it.

Current production profiles do not assert such total annotation completeness. Their linguistic dependencies are `native-value-present` claims; no current BHSA/Syriac/ExtraBiblical 0.2.0 profile asserts that every semantically eligible node is annotated with the mapped feature/value. Therefore R-020 must **not** identify `T_rep` with `T_truth`.

Usually TFont can enumerate `N`. It does not independently enumerate either target extension. `T_rep` is the semantic variable constrained by the reviewed mapping/profile contract. `T_truth` is outside current TFont authority unless a future evidence-backed coverage/quality contract explicitly relates it to represented annotations.

This matters for OLiA class mappings. The URI
`http://purl.org/olia/olia.owl#Noun` denotes an ontology class/resource under the ontology semantics. TFont's result is a set of TF nodes reviewed as realizing that target **within the profile's represented annotation semantics**. The ontology class, its ontology-model extension, `T_rep`, and any external ground-truth set are distinct objects.

## 3. Minimal mapping relation

Use the current TFont direction fixed by R-016:

```text
native/source concept -> external/common target
```

For executable unary semantic constraints, the smallest safe corpus-local relation is between the native binding and `T_rep`:

| TFont state | Corpus-local represented-denotation constraint |
|---|---|
| `exact` | `N = T_rep` |
| `broader` | `N ⊆ T_rep` |
| `narrower` | `T_rep ⊆ N` |
| `close` | no inclusion follows from assessment alone |
| `related` | non-substitutive; no inclusion follows |
| `ambiguous` native state | no unique represented target is authorized |
| `native-only` | `N` may exist, but there is no shared target projection |
| `unsupported` | no authorized shared execution denotation |

No row above states a relation to `T_truth`.

The use of non-strict `⊆` is deliberate. A reviewed `broader` or `narrower` relation is intensional: on one concrete corpus snapshot represented extensions can accidentally coincide. The runtime guarantee should not claim a strict set difference that the current snapshot need not exhibit.

### Direction check against R-016

R-016 says:

- `broader`: target is broader than native; reverse execution can miss represented target members -> undercoverage.
- `narrower`: target is narrower than native; reverse execution can include members outside the represented requested target -> overcoverage.

The set relations above are exactly that orientation.

The common naming hazard is to read “broader” as “the native answer is broader”. That is the opposite of TFont's mapping direction.

## 4. Query answer relation

Let the executed node set be `A`.

For a reviewed executable plan, relative to `T_rep`:

| Reviewed loss set | Answer guarantee |
|---|---|
| none | `A = T_rep` |
| `undercoverage` | `A ⊆ T_rep` |
| `overcoverage` | `T_rep ⊆ A` |
| both | no inclusion direction is guaranteed |

This is the most useful denotational projection of current I-020 state. It is a guarantee about the **reviewed represented semantics**, not a corpus-annotation completeness theorem.

Important separation:

- the **assessment** is a reviewed relation between native and common semantics;
- the **approximation contract** says whether that relation may be executed and which answer loss is accepted;
- the **actual result** is the native node set produced under current runtime prerequisites.

For `broader` and `narrower`, R-016 already fixes the directional loss vocabulary.

For `close`, the assessment alone does not justify a set-theoretic relation. If a separately reviewed approximation contract authorizes `close` with only undercoverage or only overcoverage, then the answer guarantee comes from that reviewed loss contract, not from the word `close`.

For `related`, no substitutive answer relation should be manufactured.

## 5. Refusal is not the empty set

A semantic API must distinguish:

```text
Executable(∅)
```

from:

```text
Refused(unsupported)
Refused(ambiguous)
Refused(capability-absent)
Refused(prerequisite-failed)
Refused(non-substitutive)
```

This is already operationally important in TFont and becomes essential in a formal model.

A successful empty result means:

> the reviewed query was expressible and executable on this corpus snapshot, and no node satisfied it.

An unsupported or ambiguous result means:

> TFont has no authorized denotation for that common request on this corpus.

Collapsing the second class into `∅` would turn “unknown/unavailable semantics” into the false scholarly statement “there are no such instances”.

This distinction directly supports R-024's later refinement-type question.

## 6. Cross-corpus semantics uses separate universes

For BHSA, Syriac, and ExtraBiblical:

```text
U_bhsa != U_syriac != U_extrabiblical
```

in the ordinary set-theoretic sense. The node identifiers do not live in one common entity universe.

Therefore a common target does **not** imply:

```text
N_bhsa = N_syriac
```

It means each corpus has a reviewed local realization of the same semantic request:

```text
N_bhsa = T_bhsa(Noun)
N_syriac = T_syriac(Noun)
N_extra = T_extra(Noun)
```

for current exact mappings.

Cross-corpus interoperability is equality of the **query meaning under each corpus interpretation**, not equality of node sets or native feature names.

## 7. Current production OLiA controls

The executable research probe reads all current `0.2.0` production mapping files for BHSA, Syriac, and ExtraBiblical:

- `noun.json`;
- `noun-morphology.json`.

It finds 21 projections total, seven per corpus:

- Noun;
- ProperNoun;
- Masculine;
- Feminine;
- Singular;
- Plural;
- Dual.

All 21 are current `exact` OLiA class / `annotation-value` projections.

This is a useful real test because the same target denotation is implemented by different native representations.

### Noun

BHSA:

```text
word.sp in {nmpr, subs}
```

ExtraBiblical:

```text
word.sp in {nmpr, subs}
```

Syriac:

```text
word.sp == subs
```

The denotational statement is not “`subs` means the same everywhere.” It is:

```text
N_bhsa(binding) = T_bhsa(OLiA:Noun)
N_syriac(binding) = T_syriac(OLiA:Noun)
N_extra(binding) = T_extra(OLiA:Noun)
```

under the reviewed exact mapping claims.

### ProperNoun

BHSA and ExtraBiblical use `sp == nmpr`.

Syriac uses:

```text
ls == prop
```

The native feature itself changes. The target semantics does not.

This is exactly the kind of case where a denotational explanation is better than feature-name matching.

## 8. What is proved, reviewed, observed, or assumed

The model is useful only if these epistemic levels stay separate.

### Mechanically provable from validated TFont state

Given trusted validated source/IR/runtime state, TFont can prove mechanically that:

- a plan uses a particular reviewed mapping/projection;
- the mapping assessment is one of the closed supported states;
- an approximation contract has a particular reviewed loss set;
- caller acceptance covers that loss set;
- the native binding selected a deterministic set of current TF nodes;
- exact/broader/narrower loss-direction metadata is internally coherent;
- conjunction/result fingerprints bind the selected plans and loss metadata.

### Human-reviewed semantic authority

TFont does not derive from first principles that:

```text
BHSA sp in {nmpr,subs} = OLiA Noun
```

That is a reviewed semantic correspondence supported by evidence.

Likewise a reviewed `broader` mapping supplies the semantic authority for the inclusion orientation. The runtime can verify the contract and execute it; it does not independently prove the philological equivalence/inclusion claim.

### Empirically observable

For a concrete corpus snapshot TFont can enumerate:

```text
N(c,s,b)
```

and compare results from different native bindings within the same node universe.

It normally cannot enumerate `T(c,s,t)` independently, because no separate gold-standard target annotation exists.

Therefore empirical equality of native selectors is not the general proof method for mapping correctness.

### Ontology-derived facts

Pinned ontology semantics can establish facts such as class/subclass relations **inside the ontology interpretation**.

Those facts do not automatically authorize a new native mapping or execution route. R-016's ban on free ontology traversal remains intact.

## 9. Conjunction has a useful small algebra

The prototype checks finite-set witnesses for conjunction/intersection.

### Uniform undercoverage

If:

```text
A1 ⊆ T1
A2 ⊆ T2
```

then:

```text
A1 ∩ A2 ⊆ T1 ∩ T2
```

So an all-undercoverage conjunction remains a lower approximation.

### Uniform overcoverage

If:

```text
T1 ⊆ A1
T2 ⊆ A2
```

then:

```text
T1 ∩ T2 ⊆ A1 ∩ A2
```

So an all-overcoverage conjunction remains an upper approximation.

### Mixed undercoverage + overcoverage

There is no inclusion guarantee in general.

The committed finite witness uses:

```text
T1 = {a,b,c}   A1 = {a,b}       # under
T2 = {b,c}     A2 = {a,b,c}     # over
```

Then:

```text
T1 ∩ T2 = {b,c}
A1 ∩ A2 = {a,b}
```

The result has both:

- false positive `a`;
- false negative `c`.

Neither set contains the other.

This validates R-016's conservative `heterogeneous-loss` treatment. Unioning loss tokens is not merely bookkeeping; mixed directions genuinely destroy a one-sided answer bound.

This result also directly motivates R-022's abstract-bound study.

## 10. Why `close` should remain opaque

It is tempting to formalize `close` as:

```text
N ∩ T != ∅
```

or even “large overlap”.

Do not do that in the current contract.

Reasons:

1. current schema stores no overlap threshold;
2. no metric or universe size is defined;
3. substantial semantic similarity does not automatically imply extensional overlap in one corpus snapshot;
4. current execution authority already requires a separately reviewed loss shape.

Therefore:

```text
assessment=close
```

is intentionally not a set-theoretic theorem.

If a `close` mapping is authorized with reviewed undercoverage/overcoverage, use the loss contract to derive the answer bound. Do not derive it from `close` itself.

## 11. Relation to database/data-integration semantics

Lenzerini's data-integration framework is relevant because mappings mediate between source and global schema meanings while queries are stated at the mediated/global level.

TFont differs in important ways:

- its semantic mappings are human-reviewed scholarly claims, not only logical dependencies;
- a TF binding is executable against one materialized corpus;
- the common ontology is a semantic pivot, not a target database instance;
- TFont deliberately refuses unreviewed ontology traversal.

Fagin et al.'s data-exchange/certain-answer framework is a stronger reminder about incomplete knowledge: one should state what follows under allowed interpretations rather than confuse one generated structure with meaning.

TFont should borrow the discipline, not copy the machinery. It currently does not need chase algorithms, universal solutions, or a target database.

## 12. Relation to ontology matching

Ontology matching explicitly treats correspondences as potentially different relation types: equivalence, subsumption, and others.

That aligns with TFont's refusal to collapse:

```text
exact
broader
narrower
close
related
```

into a generic similarity score.

A major TFont-specific addition is execution policy:

- a reviewed correspondence may remain informative-only;
- direction-specific loss is explicit;
- runtime prerequisites and caller acceptance are separate gates.

Thus TFont's denotational model should describe the semantics of **authorized query execution**, not become a generic ontology matcher.

## 13. Concrete benefits

### 13.1 Resolver correctness checks

A small verifier can statically reject incoherent combinations such as:

- `broader` with reviewed overcoverage-only execution;
- `narrower` with undercoverage-only execution;
- `exact` with non-empty loss;
- executable non-substitutive states.

Much of this is already encoded operationally. A single mathematical relation makes the reason testable and reviewable.

### 13.2 Better explanations

Instead of only:

```text
losses = ["undercoverage"]
```

an explanation can derive:

```text
answer_relation = "subset-of-requested-denotation"
```

without adding new semantic authority.

This is useful for agent-facing APIs and notebooks.

### 13.3 Query-composition research

The finite conjunction proofs expose exactly which loss patterns compose to lower/upper bounds and which become unbounded.

R-021 and R-022 can start from a checked relation algebra rather than prose.

### 13.4 Regression analysis

A profile change from:

```text
exact -> broader
```

can be described as:

```text
equality guarantee -> lower-answer guarantee
```

which is more informative than a changed enum token.

This is relevant to R-026.

### 13.5 Cross-corpus explanation

The model makes clear that shared semantics does not require identical TF feature names or identical node universes.

The production ProperNoun example demonstrates this directly.

## 14. Risks and failure modes

### 14.1 False extensional precision

The biggest risk is presenting reviewed semantic correspondence as if TFont independently enumerated the target class extension.

It usually cannot.

### 14.2 Overformalizing `close`

Giving `close` an invented overlap percentage or intersection axiom would freeze semantics not present in the source contract.

### 14.3 Confusing refusal with empty result

This would produce wrong research conclusions and wrong agent behavior.

### 14.4 Treating ontology hierarchy as runtime authority

A formal model can make unsafe inference look respectable. Existing review/lock/mapping authority must remain the only execution source.

### 14.5 Cross-corpus set comparison

Node sets from different corpora are not subsets of one shared universe. Only the semantic query type is shared.

### 14.6 Premature public API surface

Adding public fields/classes now could force R-021/R-022/R-023 to preserve a model before composition and bounds are settled.

## 15. Utility assessment

### What current problem does this solve?

Immediately:

1. gives R-016's broader/narrower orientation a single mathematical statement;
2. explains the difference between executable empty and semantic refusal;
3. proves why homogeneous and heterogeneous conjunction losses behave differently;
4. gives reviewers a way to distinguish trusted semantic claims from runtime-observed sets;
5. supplies a common vocabulary for the next formal-semantics research tickets.

### User-visible improvement today?

Mostly explanation and correctness infrastructure, not a new query capability.

A derived `answer_relation` could eventually improve user-facing explanations, but adding it to a public runtime contract is not yet necessary.

### Does the benefit justify runtime complexity now?

No.

The useful model can currently be derived from existing:

- assessment;
- approximation loss set;
- execution/refusal state.

A new runtime semantic object would mostly duplicate information before R-021/R-022/R-023 settle how composition and bounds should be exposed.

## 16. Recommended production posture

### GO: verification model

Keep the model as a machine-checkable research/test abstraction.

A future pure helper could derive:

```text
equal
answer-subset-target
target-subset-answer
unbounded
refused
```

from trusted existing TFont state.

A static checker could additionally enforce assessment/loss coherence.

### DEFER: public runtime semantics

Do not add a public schema/IR/runtime field yet.

Wait for:

- R-021 mapping-composition algebra;
- R-022 approximate lower/upper-bound model;
- R-023 typed query calculus.

Those studies may establish the right common representation.

### REJECT for now

Do not:

- materialize target ontology extensions;
- add an RDF/triplestore runtime;
- use ontology reasoning to create unreviewed execution authority;
- treat `close` as a quantified overlap;
- compare node sets directly across corpora;
- introduce new corpus semantic annotation solely to satisfy this model.

## 17. Estimated smallest later implementation

If R-021/R-022/R-023 converge on this model, the smallest implementation is likely:

1. one pure internal enum/dataclass for derived answer relation;
2. one assessment/loss coherence helper;
3. focused tests over existing mapping/projection IR;
4. optional explanation/provenance rendering.

Expected scope: small; no corpus migration and no ontology reasoner.

If the derived relation is exposed in public resolver/execution result contracts, that becomes an additive public-contract design ticket and needs a separate design/TDD/review cycle.

## 18. Acceptance trace

- [x] minimal formal domains for native binding, common target query meaning, result and refusal;
- [x] exact/broader/narrower direction formalized;
- [x] R-016 undercoverage/overcoverage direction reconciled;
- [x] reviewed claims separated from mechanical proof and empirical enumeration;
- [x] current production BHSA/Syriac/ExtraBiblical OLiA controls checked;
- [x] prior denotational/database/data-integration/ontology-matching work compared;
- [x] resolver, explanation, testing, cross-corpus and composition benefits evaluated;
- [x] false-precision cases identified;
- [x] executable finite-set examples committed;
- [x] go/defer recommendation and likely implementation scope stated;
- [x] no production behavior changed.

## 19. Review targets

Independent review should challenge:

1. whether `broader` / `narrower` inclusion direction is exactly aligned with R-016;
2. whether non-strict inclusion is safer than strict inclusion for corpus-local extensions;
3. whether reviewed loss tokens really justify the proposed answer bound;
4. whether `close` is kept sufficiently opaque;
5. whether “latent target query denotation” accidentally claims target annotations exist;
6. whether any refusal state is being smuggled into set semantics;
7. whether the mixed-direction conjunction counterexample is valid;
8. whether production OLiA examples genuinely demonstrate semantic abstraction beyond feature-name matching;
9. whether a public API should remain deferred until R-021/R-022/R-023;
10. whether the proposal would accidentally authorize ontology inference or RDF materialization.
