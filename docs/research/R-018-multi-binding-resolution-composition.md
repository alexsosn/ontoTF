# R-018 research — same-corpus multi-binding composition semantics

**Issue:** #131  
**Baseline:** `main` `b3d6f8b3b9de7a9b55b683e2760ced56d5241ebd`  
**Type:** research only  
**Recorded:** 2026-09-23

## Decision

Keep the current exact resolver fail-closed rule:

> if more than one exact `TargetBindingIR` survives semantic-key, corpus, variant, prerequisite, and assessment selection, execution is refused with `multiple_exact_bindings` unless a future **explicit reviewed composition authority** names the exact members and semantics.

Do **not** infer first-row, OR/union, AND/intersection, priority, equivalence, or applicability from multiple bindings.

No production composition operator should be added yet. The current pilot inventory contains realistic **multi-value** cases, but those are already representable as one reviewed `NativeBindingIR` with `execution_shape=value-set-predicate`. It does not contain a reviewed case where multiple independent bindings must be composed. Freezing generic `single | any-of | all-of` semantics now would therefore design beyond evidence and would overlap with the deliberately narrow I-010 value-set primitive.

Before same-corpus multi-binding execution is enabled, add a separate reviewed composition artifact, compiler IR/index, resolver validation path, typed executable plan shape, and executor support for only the operator(s) justified by concrete corpus cases.

## 1. Existing contract

The current mapping schema separates one mapping/projection from one native execution binding. A `NativeBindingIR` can already represent:

- one scalar feature predicate;
- one finite value-set predicate;
- an edge path;
- other existing typed execution shapes.

I-010 deliberately added `value-set-predicate` as **one binding** so that finite disjunction over one feature does not become generic multi-plan OR.

Current production examples:

- BHSA OLiA Noun: `word.sp in {nmpr, subs}`;
- ExtraBiblical OLiA Noun: `word.sp in {nmpr, subs}`;
- Syriac OLiA Noun: `word.sp == subs`.

The exact resolver currently selects all rows for one full `SemanticKey` + corpus + selected variant, validates them, filters `assessment == exact`, and:

- zero exact rows -> `non_exact_mapping` or an earlier absence diagnostic;
- one exact row -> emit one `ExactNativePlan`;
- more than one exact row -> `multiple_exact_bindings`.

That behavior is semantically conservative and should remain the production contract after this research.

## 2. Evidence baseline

Repository snapshots inspected for this research:

| Corpus/repository | Pinned main | Relevant evidence |
|---|---|---|
| ontoTF | `b3d6f8b3b9de7a9b55b683e2760ced56d5241ebd` | mapping schema v2, I-006 resolver, I-010 value-set research, shipped BHSA/Syriac/ExtraBiblical Noun mappings |
| CUC | `0943158f591512797f6f2575953f420fdfe898d9` | latest TF release inventory under `tf/0.2.8` |
| Pseudepigrapha-TF | `7c4b757bb543a110ae9a252d1281835859136852` | generated feature docs, especially `morph` and `lex` |
| ORACC-TF | `ae5aedb81427ed67302d5d493804501e73de24e4` | generated `epos`, `pos`, lexeme feature docs |
| TLHdig-TF | `bc4a206690c1856d3cfde8b291f626c45a712640` | generated `pos` docs and `programs/tlhdig/morph.py` parser contract |

The production ontoTF tree currently contains only three shipped mapping files:

- `src/tfont/resources/profiles/bhsa/0.1.0/mappings/noun.json`;
- `src/tfont/resources/profiles/syriac/0.1.0/mappings/noun.json`;
- `src/tfont/resources/profiles/extrabiblical/0.1.0/mappings/noun.json`.

There is therefore no hidden production multi-binding mapping set to preserve.

## 3. Corpus inventory

### 3.1 BHSA

The shipped reviewed mapping already demonstrates the most tempting apparent multi-binding case:

```text
olia:Noun
  <- sp=subs
  <- sp=nmpr
```

This is **not** represented as two `TargetBindingIR` rows. I-010 reviewed the semantics and encoded it as one native value-set predicate:

```json
{
  "component_id": "bhsa-tf",
  "node_type": "word",
  "feature": "sp",
  "values": ["nmpr", "subs"],
  "execution_shape": "value-set-predicate"
}
```

The union semantics belongs to the primitive binding because both alternatives are values of one feature under one mapping/projection review and one dependency closure. Splitting these values into independent mappings and later inferring OR would lose that authority boundary.

**R-018 classification:** disjoint native values whose union realizes one target, already normalized to one binding. No multi-binding operator required.

### 3.2 ETCBC Syriac

The shipped reviewed broad Noun mapping is scalar:

```text
word.sp == subs
```

The I-010 evidence records proper-noun status separately as lexical-set information while proper nouns remain substantives for the POS selector. The broad OLiA Noun execution therefore does not require a second native binding.

**R-018 classification:** one exact binding. No composition case.

### 3.3 ETCBC ExtraBiblical

Like BHSA, the shipped reviewed broad Noun mapping uses one value-set binding:

```text
word.sp in {nmpr, subs}
```

**R-018 classification:** disjoint values already normalized to one binding. No multi-binding operator required.

### 3.4 CUC

The inspected latest shipped TF release, `tf/0.2.8`, contains structural/textual/sign features such as `language`, `line`, `sign`, `g_cons`, `alt`, and tablet metadata, but no normalized POS/morphology/lexical feature comparable to the linguistic pilot mappings.

CUC may gain richer linguistic annotations later, but the current corpus provides no reviewed same-semantic multi-binding execution case for R-018.

**R-018 classification:** no current relevant executable mapping case.

### 3.5 Pseudepigrapha-TF

The current generated feature docs preserve upstream word annotations:

- `morph`: “literal upstream morphological annotation … when present”;
- `lex`: “literal upstream lexical annotation … when present”.

There is no normalized POS feature in the current generated feature inventory. The raw annotations may eventually support linguistic mapping after source-specific review, but composing them now would require the resolver to reinterpret opaque source values or invent cross-field semantics.

**R-018 classification:** no reviewed multi-binding case. Mapping research must precede composition.

### 3.6 ORACC-TF

ORACC-TF supplies strong evidence for the distinction between **multi-value** and **multi-binding**.

At the pinned snapshot:

- word `epos` has 33 observed effective/contextual POS values;
- mixed/lexical `pos` has 35 observed values;
- observed codes that require explicit semantic mapping research include `N`, `PN`, `DN`, `GN`, `SN`, `RN`, `EN`, `TN`, and `WN`; this research does not infer their ontology semantics from code names.

If separate mapping evidence establishes that one semantic target selects several ORACC values of one feature, one node type, one component, one review, and one dependency closure, the existing `value-set-predicate` is the correct primitive. R-018 should not turn that into a list of independent exact plans.

The existence of both lexical `pos` and contextual `epos` could eventually create a genuine heterogeneous case, but no reviewed ontoTF mapping currently states that the two must be unioned, intersected, prioritized, or conditionally dispatched for one semantic target. Their names alone are not composition authority.

**R-018 classification:** concrete future multi-value case; possible future heterogeneous multi-binding case, but no reviewed composition semantics today.

### 3.7 TLHdig-TF

TLHdig-TF exposes the strongest reason to refuse generic composition.

Its parser documents that source morphology field 4 can contain:

- a paradigm/stem-class value;
- a closed-vocabulary POS value;
- logographic morphology;
- or no value.

The normalized `pos` vocabulary is deliberately narrow (`ADV`, `POSP`, `PREV`, `CNJ`, `NEG`, `INTJ`, quantifier/adverb categories, etc.). Nominal and verbal information can instead live in stem-class or morphology strings. The source can also name multiple analyses or multiple alternatives for one analysis.

A future semantic target might therefore require logic involving different native fields or applicability conditions. But the source alternatives are editorial/morphological analyses, not evidence that the intended query semantics are OR, AND, priority, or union. Treating “several available analyses” as “several executable semantic bindings” would be a category error.

**R-018 classification:** plausible future conditional/heterogeneous composition pressure; no reviewed executable case. This is evidence for an explicit composition artifact, not evidence for a default operator.

## 4. Required distinctions

### Semantically equivalent duplicate realizations

Two rows that look equivalent must not be collapsed by row order, matching labels, or even matching target identity. If two reviewed projections have the same native binding identity but distinct mapping/projection provenance, the compiler/resolver still needs explicit authority to call one a duplicate/alias.

A future composition artifact may authorize deduplication/equivalence, but execution should otherwise fail closed. Legacy duplicates should normally be corrected at source rather than turned into an execution operator.

### Disjoint native values whose union realizes one target

When the alternatives are values of the same feature under one reviewed mapping authority, use one `value-set-predicate`. BHSA and ExtraBiblical are the production examples; ORACC supplies a likely future example.

Do not model this as multiple `TargetBindingIR` members merely to obtain OR later.

### Overlapping selectors

Overlap does not imply harmless composition. Union may be extensionally idempotent, but independently reviewed selectors can carry different applicability, dependency, review, or approximation semantics.

No cross-binding union is inferred from overlap. Within a single value-set predicate, duplicate authored values are already invalid and executor result-node overlap is deterministically deduplicated.

### Complementary constraints

Constraints that must jointly hold are a real potential multi-binding case, but none is currently reviewed in the production mapping set.

A future conjunction must be represented by a typed reviewed composition operator over explicit members. The resolver must not infer conjunction because two exact rows coexist.

### Alternatives conditioned by applicability/domain

Different features, node types, languages, subcorpora, or analysis states may require conditional dispatch rather than union. ORACC lexical `pos` vs contextual `epos` and TLHdig's field-4 classification illustrate where this pressure can arise.

Applicability conditions must be explicit reviewed data. They must not be guessed from corpus metadata at resolution time.

### Legacy/duplicate mappings

If multiple rows exist because of migration residue, duplicated source artifacts, or stale mappings, they should fail validation/review and be removed. “Compose them” is not a repair strategy.

## 5. Composition authority

Composition authority should **not** live in:

- resolver code;
- lexical ordering of mapping/projection IDs;
- the profile capability list;
- feature/target name similarity;
- ontology hierarchy traversal;
- generic Context-Fabric query strings.

It should be a **separate reviewed composition artifact** because a composition can reference members owned by different mapping records. Putting the authority inside one member would give that member asymmetric ownership over its peers; putting it in a profile is too coarse.

Conceptual future source record:

```text
SemanticComposition
  composition_id
  variant/release scope
  SemanticKey
  operator
  exact member projection identities
  applicability/domain contract, if required
  evidence
  review
  semantic digest
```

The member set must be exact: extra, missing, stale, reordered, or semantically changed member projections cannot silently inherit the authority.

This research does **not** add that schema. No current production case justifies choosing the operator vocabulary or serialization shape.

## 6. Operator vocabulary

Do not freeze `single | any-of | all-of` as a production enum yet.

- `single` is already the ordinary resolver path, not composition.
- finite OR over one feature is already `value-set-predicate`;
- no reviewed same-semantic-key multi-binding case currently requires heterogeneous `any-of`;
- no reviewed same-semantic-key multi-binding case currently requires `all-of`; R-016's conjunctions are conjunctions of separately required semantic atoms and do not authorize same-key binding composition;
- conditional/applicability dispatch is not equivalent to either plain OR or AND.

When the first genuine case arrives, introduce the smallest typed operator that expresses that case and explicitly exclude a generic boolean query language.

## 7. Deterministic resolver behavior

Until a reviewed composition artifact exists:

1. select one current corpus variant from trusted prerequisites;
2. locate the full semantic key;
3. validate candidate rows against the selected release;
4. retain exact rows only;
5. zero exact rows -> existing fail-closed diagnostic;
6. one exact row -> existing `ExactNativePlan`;
7. more than one exact row -> `multiple_exact_bindings`.

No requested corpus may be silently dropped and no row may win by order.

After a future composition contract exists, step 7 may proceed only if exactly one reviewed composition record matches:

- the selected variant;
- the full semantic key;
- the complete surviving exact member set;
- current member semantic/review identities;
- any required applicability state.

Anything else remains `multiple_exact_bindings` or a more specific stale/invalid-composition diagnostic.

## 8. Provenance and fingerprints

Every member must retain its current mapping/projection provenance:

- mapping/projection IDs;
- semantic digests;
- review fingerprints;
- evidence fingerprints;
- native-binding identity;
- native dependencies;
- ontology lock/bundle identity.

A future composition adds, rather than replaces:

- `composition_id`;
- composition semantic digest;
- composition review/evidence;
- operator/applicability contract.

Composition identity should be canonical and order-independent when member order has no semantics. A future composed-plan fingerprint should include the composition semantic identity plus canonical member plan/semantic identities and prerequisite state.

Do not hash only the resulting Context-Fabric selector/result; doing so would erase the reviewed path by which the selector became authorized.

## 9. Approximate resolution

R-016 remains authoritative for approximation of already-authorized semantic atoms and for conjunctions of required atoms: every atom must be independently executable, and a conjunction records the conservative union of their reviewed loss-direction tokens.

R-018 owns an earlier question: whether multiple bindings under one semantic key are authorized to compose at all, and by which operator. R-016 does not infer that composition authority.

Consequences:

- if a future reviewed R-018 composition is an actual conjunction/intersection of required atoms, reuse R-016's all-atoms-required rule and conservative loss union after every member passes its own approximation-eligibility and caller-loss gate;
- a union/disjunction or conditional/applicability composition is not covered by R-016's conjunction rule, so its loss behavior needs a separately reviewed operator-specific contract;
- mixed exact/non-exact members never become executable solely because the member rows coexist.

R-018 does not alter the current exact-only I-006 path.

## 10. Context-Fabric execution boundary

A future executor should receive a typed composed plan over materialized native bindings. It must not receive or generate an arbitrary boolean query language as the semantic authority.

For each approved composition operator, execution semantics must be implemented directly and tested against loaded TF/Context-Fabric features. The executor must still perform the R-019/I-008 trust/revalidation boundary before touching the corpus.

## 11. Exact changes required before multi-binding execution

No current production code change is authorized by this research. Before enabling same-corpus multi-binding execution, a future implementation must complete all of the following:

1. add a versioned schema/artifact for reviewed semantic composition, rather than inferring composition from mapping-array multiplicity;
2. bind composition records into release/profile semantic identity and review/digest validation;
3. compile validated records into a `TargetCompositionIR` (name provisional) plus deterministic lookup index;
4. retain every member `TargetBindingIR` and its provenance;
5. extend resolution with an explicit composition match/validation step for >1 exact row;
6. add a typed composed plan/result shape and versioned fingerprint projection;
7. implement only the corpus-justified operator(s) in loaded execution;
8. revalidate composed plans under the same trusted current-IR/current-prerequisite boundary as ordinary plans;
9. reuse R-016 for a reviewed conjunctive composition, and define separate operator-specific approximation/loss behavior before any non-conjunctive composition with non-exact members is executable;
10. add RED/GREEN tests for missing authority, stale/extra/missing members, order invariance, conflicting composition records, provenance preservation, prerequisite failure, and executor semantics.

Until then, `multiple_exact_bindings` is the intended safe behavior.

## 12. Acceptance trace

- [x] Inventoried BHSA, Syriac, ExtraBiblical, CUC, Pseudepigrapha-TF, ORACC-TF, and TLHdig-TF.
- [x] Found concrete multi-value cases and showed why they belong in one native binding rather than multi-binding composition.
- [x] Found no reviewed production case that justifies composing multiple independent exact `TargetBindingIR` rows.
- [x] Therefore chose the issue's allowed evidence-based outcome: keep the POC fail-closed until a genuine case exists.
- [x] Rejects implicit first-row, OR, AND, union, intersection, priority, or applicability inference.
- [x] Places future composition authority in a separate reviewed contract.
- [x] Defines deterministic zero/one/multiple resolver behavior.
- [x] Preserves per-binding assessment/review/evidence/provenance.
- [x] Defines required schema/IR/resolver/executor work before composition can become executable.
- [x] Keeps Context-Fabric execution typed and avoids a generic boolean query language.
- [x] Reuses R-016 conjunction loss composition where applicable and keeps non-conjunctive composition operator-specific and review-gated.

## 13. Review targets

A logically independent reviewer should challenge:

1. whether BHSA/ExtraBiblical value sets are being incorrectly counted as evidence against multi-binding rather than simply a different primitive;
2. whether ORACC `pos`/`epos` supplies enough evidence to authorize conditional or heterogeneous composition now;
3. whether TLHdig multiple analyses could legitimately imply OR, and what source semantics would be needed to prove that;
4. whether a separate composition artifact is preferable to embedding authority in one mapping;
5. whether refusing to freeze `any-of/all-of` is too conservative;
6. whether member provenance and review can survive composition without making fingerprints order-sensitive;
7. whether R-016 loss semantics can be reused directly or need composition-level review;
8. whether any proposed future shape accidentally becomes a generic boolean query language.
