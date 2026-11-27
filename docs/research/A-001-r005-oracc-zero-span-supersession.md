# A-001 amendment: R-005 ORACC zero-span supersession

**Issue:** #65  
**Recorded:** 2026-09-07  
**Applies to:** `docs/research/R-005-corpus-semantic-census.md`

## Superseded ORACC zero-span architecture

R-005 remains unchanged as the historical record of the corpus census performed on 2026-09-05. Its observations about the then-current ORACC-TF target included zero-span/sidecar cases and allowed the possibility that some ORACC entities would live outside the TF warp.

That architectural inference is no longer current.

Accepted ORACC-TF `docs/reference/architecture/ADR-0001-empty-slots-not-sidecars.md` supersedes the earlier sidecar-first treatment of zero-span **textual** entities. Independently positioned textual source entities without an ordinary semantic sign remain in Text-Fabric through explicit synthetic/empty slots. Those slots preserve source position/order; they do not assert a real grapheme, cuneiform sign, token, or other philological content.

The current interpretation is therefore:

- zero span alone is not evidence for a sidecar;
- textual zero-span objects are materialized into TF using the corpus converter's synthetic/empty-slot policy;
- semantic/source slots and synthetic/empty technical slots remain distinguishable;
- ancestors reuse descendant anchors rather than receiving redundant synthetic slots;
- no neighbouring real slot is borrowed and no visible sign content is fabricated;
- ontoTF consumes the resulting materialized TF structure and does not need an ORACC-specific external-record adapter.

Current merged R-011 already reflects this newer state: its ORACC pilot pin was refreshed against the active ORACC-TF model after ADR-0001 and treats R-005 only as historical semantic-census input for the zero-span question.

This amendment does not claim that arbitrary external files can never exist next to a corpus. It only removes the obsolete inference that ORACC zero-span behavior justifies a generic ontoTF `sidecar` / `native-adapter` runtime abstraction. Data genuinely outside a TF/Context-Fabric corpus remains outside baseline ontoTF unless a separately reviewed architecture extension establishes otherwise.
