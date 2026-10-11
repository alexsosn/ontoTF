# I-033E8 — integrity-only validation for accepted batch handoff

Issue #317, child of #303/#300/#290. Main contains immutable published profile and coverage resources; #316's `build_overlay_handoff` emits compact unsealed additions that are attested by a protected workflow. Existing tests exercise assembler internals but there is **no independently callable structural consumer-side verification** before signing.

Original observed pilot: 10 original BHSA/Syriac POS codes, pinned native-source evidence; BHSA source is ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da, Syriac grammar ETCBC/linksyr@3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6. Exact TF selectors are word.sp values; 0.4.0 installed base profiles and p004-i027c2-* coverage are immutable. Ten native-only dispositions cannot grant OLiA common targets merely because source code glosses resemble standard POS labels.

An attestation signs bytes made by a protected pipeline; it cannot prove their semantic consistency. The producer and consumer should separately validate a **fully self-contained, compact, unsealed handoff** using the same pinned base release and exact sparse coverage accounting. This verification is an integrity predicate, **not** a trust decision. Hand-supplied JSON can pass when internally consistent, and must never be labeled reviewed or eligible for installation merely because it passed.

Security threat cases: self-consistent recomputed envelope digest with swapped observation/rows; unknown extra fields used as stealth approvals; accepted and rejected rows joined incorrectly; duplicated item IDs; native-only payload with exact projections; base profile drift; base coverage already reviewed; evidence record digest mismatch; inherited mapping overwrite; source/corpus swap. All must fail closed. Do not add a new Actions workflow or require network corpus checkout for already pinned immutable data.

Scope boundary: no installed overlay registry implementation and no external attestation verifier. Those remain separate #303 milestones requiring trusted reviewer principal and a real published new batch.
