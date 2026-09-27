# I-016 plan amendment — independent research and production accounting

**Issue:** #204  
**Amends:** `docs/plans/I-016-seven-corpus-coverage-manifests.md`  
**Trigger:** implementation preparation after RED head `a54fdefd19fe85e7e7363387b4094017b7e26d02`

## Finding

The accepted plan modeled one selected per-item authority:

`authority = unreviewed | research | production`.

That shape cannot simultaneously preserve both required baseline facts when the same denominator item has both R-011 research authority and I-015 production authority:

- historical research-reviewed aggregate must remain **99**;
- current production-reviewed aggregate must independently report **21**.

Replacing research authority with production authority would make the historical research count depend on later production work. Treating production as a second source under one authority token would blur the exact boundary that I-016 is meant to enforce.

This is a design contradiction, not an implementation detail.

## Amendment

Per semantic item, replace the single selected authority with independent optional layers:

```text
accounting:
  research: null | {
    assessments[]
    common_target
    source_ids[]
  }
  production: null | {
    assessments[]
    common_target
    source_ids[]
    optional profiles[]
    optional capabilities[]
  }
```

At least one of the layers may be null. Both null means the item is unreviewed for both authority tiers.

The two layers are semantically independent:

- R-011 import populates only `research`;
- I-015 import populates only `production`;
- when the same item appears in both, both records remain;
- research counts never change merely because production coverage advances;
- production completion counts only the `production` layer.

## Accounting invariants

For either non-null layer:

- `source_ids` is non-empty and unique;
- `assessments` is non-empty, unique and restricted to the accepted eight assessment tokens;
- `common_target` equals whether at least one target-bearing assessment is present:
  `exact|close|broader|narrower|related`.

For null layers, no hidden assessment/source fields exist.

Production-only classification:

- `profiles` and `capabilities` are allowed only inside the production layer;
- every token must belong to the controlled R-014 vocabulary;
- a capability prefix must be represented by its owning profile when both arrays are present.

## Report definitions

- `research_reviewed_items`: items with non-null research layer;
- `research_common_target_items`: research layer with `common_target=true`;
- `production_reviewed_items`: items with non-null production layer;
- `production_common_target_items`: production layer with `common_target=true`;
- `production_unreviewed_items = semantic_items - production_reviewed_items`.

Expected baseline remains:

- research-reviewed: 99;
- research common-target: 26;
- production-reviewed: 21.

## Denominator digest

No change.

Both accounting layers remain excluded from `coverage_denominator_projection`, so research/production progress cannot mutate denominator identity.

## TDD consequence

The existing RED head remains valid and is not rewritten.

GREEN/adversarial tests must additionally prove:

1. one item can carry both research and production layers;
2. adding/removing production accounting does not change research-reviewed count;
3. adding/removing either accounting layer does not change denominator digest;
4. research-only exact/common-target content never counts as production coverage;
5. a production layer cannot inherit source IDs/assessment from research implicitly.

## Scope

No new runtime or ontology semantics. This amendment only repairs the I-016 accounting data model before production code is written.
