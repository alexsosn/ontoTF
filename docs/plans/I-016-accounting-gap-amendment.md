# I-016 plan amendment — explicit accounting gaps outside a historical denominator

**Issue:** #204  
**Amends:** `docs/plans/I-016-seven-corpus-coverage-manifests.md` and dual-accounting amendment  
**Trigger:** deterministic baseline generator against I-015 production mappings

## Finding

The historical R-011 denominator is exactly 685 items, but it does not contain every semantic value already used by current production mappings.

Concrete case:

- I-015 Syriac ProperNoun is reviewed exact production mapping `word.ls=prop`;
- R-005 inventory contains `ls=prop`;
- historical R-011 raw-schema policy did **not** declare `ls` a bounded value family;
- therefore historical denominator contains `node_feature:ls` but not `node_value:ls="prop"`.

The generator correctly rejected the prior plan's expected 7 Syriac production-reviewed denominator items.

Mapping `ls=prop` onto `node_feature:ls` would overclaim review of the whole lexical-set feature. Adding `ls=prop` to the immutable historical denominator would mutate the accepted 685-item baseline. Silently dropping it would hide a known denominator deficiency.

## Amendment

Coverage manifest v1 adds an optional/required-empty-capable top-level collection:

```text
accounting_gaps[]:
  item_id
  kind
  authority = research | production
  reason = outside-denominator
  assessments[]
  common_target
  source_ids[]
  optional profiles[]
  optional capabilities[]
```

For I-016 baseline, only production gaps are expected.

Rules:

1. an accounting-gap item ID must not be present in `semantic_items` or `technical_exclusions`;
2. gap identities are unique;
3. accounting layer assessment/target/profile/capability rules are identical to ordinary selected authority;
4. gaps are **excluded** from denominator digest because they describe accounting knowledge outside the immutable denominator;
5. gaps are always visible in coverage reports and block bounded/corpus-wide completion;
6. a new denominator version may later absorb the item; the old manifest remains immutable.

## Baseline consequence

Historical denominator remains **685**.

Production-reviewed items *inside* that denominator become:

- BHSA: 7;
- Syriac: 6;
- ExtraBiblical: 7;
- others: 0;
- aggregate: **20**.

The baseline additionally records exactly one production accounting gap:

- Syriac `node_value:ls="prop"`;
- source mapping: `mapping:syriac:olia-proper-noun`;
- exact, common-target, profile `linguistic`, capability `linguistic.part-of-speech`.

Historical research counts remain 99 / 26.

## Report changes

Add:

- `production_outside_denominator_items`;
- optionally the stable tuple/list of gap item IDs for drill-down.

`bounded_scope_complete` requires:
- every denominator semantic item has production accounting;
- **zero production accounting gaps**.

`corpus_wide_completion_claim_eligible` consequently also requires zero gaps.

## Importer behavior

The I-015 bridge no longer silently skips or hard-fails on a production binding outside the historical denominator.

Instead it emits an explicit production accounting gap. A duplicate/conflicting gap or a gap that is already inside the denominator remains an error.

This is fail-closed for coverage claims: known production semantics outside the denominator can never improve completion percentages or disappear from the report.

## TDD amendment

Keep the original RED head unchanged.

Before GREEN completion, update contract expectations under this reviewed amendment:

- aggregate production-reviewed denominator items = 20, not 21;
- Syriac production-reviewed denominator items = 6;
- aggregate production outside-denominator items = 1;
- Syriac gap is exactly `node_value:ls="prop"`;
- all other corpora have zero production gaps.

Adversarial tests must prove:
- gaps do not change denominator digest;
- gaps block bounded/corpus-wide completion;
- an in-denominator item cannot also be a gap;
- a gap cannot be counted as production-reviewed denominator coverage.

## Follow-up

A future new Syriac denominator version may include `ls=prop` (or a reviewed lexical-set value family) under P-004. It must not rewrite `p004-r011-baseline-v1`.
