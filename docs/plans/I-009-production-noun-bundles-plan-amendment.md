# I-009 plan amendment: MIT licensing and public loader error

**Amends:** `I-009-production-noun-bundles-plan.md`  
**Reason:** merged PR #155 changed the release baseline after the original plan was written; adversarial plan review also found an exception-surface inconsistency.

## 1. Licensing section superseded

PR #155 merged as `320dbe233cd2921ae9a50f8071522e2292830161` and added the repository-root MIT license plus Python package metadata. Issue #153 is therefore resolved.

For I-009 production resources:

- ontoTF-authored `profile.json`, mapping/evidence metadata, loader code and attribution prose use the repository **MIT** license unless explicitly marked otherwise;
- every production profile sets `license: MIT`;
- the pinned third-party OLiA ontology payload remains **CC BY 3.0** and the ontology lock continues to record `license: CC-BY-3.0`;
- the OLiA `LICENSE.data` and attribution notice ship beside the snapshot;
- corpus TF/MQL bytes are not bundled and retain their upstream licenses externally;
- no `NOASSERTION`, fixture `CC-BY-4.0`, or inferred corpus license is permitted in production profile resources.

This supersedes the original plan's `Profile license boundary` subsection and removes #153 from the I-009 merge-blocker list. The resource-truth tests still fail on any placeholder or fixture license.

## 2. Public loader surface correction

The original plan named a narrow `ProductionBundleError(ValueError)` but omitted it from the exported public names. Freeze the public surface as **four** names:

```python
PRODUCTION_NOUN_CORPORA = ("bhsa", "syriac", "extrabiblical")

class ProductionBundleError(ValueError): ...

load_production_noun_bundle(corpus_id: str) -> SemanticSourceBundle

load_production_noun_bundles() -> tuple[SemanticSourceBundle, ...]
```

`ProductionBundleError` is re-exported from `ontotf.__init__`. Unknown or non-string corpus IDs raise this type deterministically; callers are not required to catch an implementation-private exception.

The RED contract must explicitly assert this export and exception type.

## 3. Merge blockers after amendment

The effective merge blockers are now:

- semantic review records do not bind current mapping/projection digests;
- exact OLiA snapshot/license/attribution is absent from the wheel;
- production resources contain synthetic fixture provenance or placeholder/fixture licensing;
- clean-wheel loader/validation depends on the source checkout;
- any corpus plan differs from the corrected research semantics;
- final exact-head adversarial review has a blocker.

No other section of the original plan is changed by this amendment.