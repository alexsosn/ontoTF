# I-010 research: exact finite value-set native execution

**Issue:** #149  
**Recorded:** 2026-09-11  
**Phase:** research only

## Decision

Add one deliberately narrow native execution shape for an exact finite set of values on one loaded TF node feature:

```text
component_id + node_type + feature + values[] + execution_shape=value-set-predicate
```

The field is `values`, not `closed_values`. `closed_values` already means a reviewed claim that the listed set is the **complete feature domain** and is guarded by a `value-domain` dependency with `domain_semantics=closed-reviewed`. The release Noun selector `{subs,nmpr}` is a selected subset of the POS domain, not the POS domain itself.

This shape is one native binding. It does not introduce generic OR expressions, arbitrary boolean query composition, or same-corpus multi-binding composition from R-018.

## Semantic blocker that motivated the ticket

Fresh adversarial review of I-009 found that the earlier research fixture `sp=subs -> olia:Noun` is not coextensive across all three intended release corpora.

At the pinned OLiA revision `d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6`, the generated OLiA hierarchy places `CommonNoun` under `Noun` and also exposes `ProperNoun` as a noun category. OLiA's own Universal POS conversion explicitly documents the broad `NOUN -> olia:Noun` mapping as covering common and proper nouns.

Corpus-native evidence differs:

- **BHSA** `4db00e...`: `sp` is POS; `subs` is noun and `nmpr` is proper noun. Exact broad Noun selection therefore needs `sp in {subs,nmpr}`.
- **ExtraBiblical** `9a5628...`: exact MQL declares `part_of_speech_t` with distinct `subs` and `nmpr` members and types word `sp` with that enum. Its BHSA-family documentation supplies the human glosses. Exact broad Noun selection therefore needs `sp in {subs,nmpr}`.
- **ETCBC Syriac** `bb0eaa...`: word grammar defines `sp=subs` as substantive while proper-noun status is represented separately by lexical-set `ls=prop`; source examples show `sp=subs:ls=prop`. Here the broad nominal POS selector remains scalar `sp=subs`.

Therefore I-009 production bundles cannot honestly ship one scalar selector for all three corpora.

## Contract choice

### Mapping schema

Extend `nativeBinding` with:

```json
{
  "values": ["subs", "nmpr"],
  "execution_shape": "value-set-predicate"
}
```

Rules:

1. `values` is non-empty and unique under JSON equality;
2. every member is a JSON scalar accepted by the existing native-binding scalar vocabulary;
3. `value-set-predicate` requires non-empty `component_id`, `node_type`, `feature`, and `values`;
4. it forbids `value`, `closed_values`, edge/path fields and extent interpretation;
5. scalar `value-predicate` remains unchanged;
6. malformed or mixed shapes fail closed before execution.

Canonical identity must preserve semantic set behavior. The implementation should canonicalize `values` deterministically using the repository's existing canonical-JSON byte ordering before NativeBindingIR identity/fingerprinting, so source list order cannot change query meaning or result ordering.

### IR

Extend `NativeBindingIR` with `values: tuple[JSON scalar, ...] | None`. Compilation converts a validated source list into its deterministic canonical tuple. Reconstruction/fingerprinting emits the canonical list.

### Runtime prerequisites

No new P-002/I-007 dependency kind is required.

A profile that executes `{subs,nmpr}` declares two ordinary `native-value-present` dependencies, one for each selected native value. I-007 already evaluates those against the loaded corpus. The binding itself remains authorized only when the complete mapping dependency closure passes.

Do not use `value-domain`: selected query values are not a claim about the complete feature domain.

### Resolver

I-006 exact resolution may carry the new IR binding unchanged after its normal exact-assessment and prerequisite gates. It must not expand one set binding into multiple semantic plans; that would make result semantics depend on plan composition and collide with R-018.

### Loaded execution

For a validated set binding:

1. obtain the already-loaded feature selector and `otype` lookup exactly as I-008 does;
2. call `F.<feature>.s(value)` once for every canonical selected value;
3. normalize every returned node ID through the existing strict integer/positive checks;
4. union nodes by ID;
5. validate `F.otype.v(node) == node_type` for every candidate;
6. return unique node IDs in deterministic ascending numeric order.

The executor performs no network access, corpus loading, ontology lookup, generated CF query strings, or arbitrary boolean expression evaluation.

A node returned for more than one selected value is not an error; finite-set semantics is mathematical union, so it appears once. Duplicates *inside the authored `values` list* are invalid source data and should be rejected before IR.

## R-018 boundary

R-018 concerns multiple independently reviewed bindings for the same semantic request and the semantics of composing them. I-010 instead adds a primitive predicate over one feature:

```text
feature value ∈ finite reviewed set
```

It has one component, one node type, one feature, one mapping/projection review, one prerequisite closure, and one resulting plan. It therefore does not decide union/intersection/precedence between independent mappings.

If future work needs `sp in {...} OR another_feature=...`, that remains outside I-010 and should go through R-018 or another explicit composition design.

## Failure and regression requirements

The plan/TDD gate must cover at least:

- schema rejects empty `values` and duplicate authored values;
- schema/policy rejects `value` + `values` and `closed_values` + `values` mixed shapes;
- IR canonicalizes set order deterministically;
- native-binding identity/fingerprint is invariant to authored set ordering;
- exact resolver returns one plan carrying the finite set;
- missing/failed `native-value-present` dependency prevents exact authorization;
- executor unions selector results, deduplicates cross-value overlap, filters by node type, and returns deterministic numeric order;
- malformed selector results still fail closed under existing I-008 rules;
- scalar `value-predicate` behavior and fingerprints remain unchanged for existing artifacts;
- no generic OR/multi-binding behavior appears in the public API.

## Scope recommendation

This is justified for v0.1 because it corrects a real false-equivalence in the intended release demo while adding the smallest executable primitive needed to express the reviewed semantics. Do not switch the release demo to `olia:Verb` merely to avoid the issue: doing so would leave the already-discovered Noun mapping bug in research fixtures and would make the first public interoperability example less representative of the semantic distinctions ontoTF is intended to preserve.

Proceed to plan only after a logically independent review challenges: OLiA breadth, the three corpus POS encodings, `values` vs `closed_values`, deterministic set identity, I-007 dependency reuse, and the R-018 boundary.