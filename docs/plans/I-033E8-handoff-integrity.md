# I-033E8 plan

1. RED: add focused Python tests constructing the already-existing actual 10-category unsealed handoff; assert new `verify_overlay_handoff_integrity` exists, returns no approval, checks content digest, and rejects crafted cross-reference/corpus/coverage/evidence/base mismatches even if attacker recomputes outer canonical checksum.
2. GREEN: implement a strict, read-only, fail-closed validator that reads only installed immutable `load_profile` and packaged coverage/evidence/lock. Validate closed shapes, JCS digest, review observation row joins, unique identifiers, `native-only` vs `exact` shape, semantic digests, dependencies, evidence, exact base/denominator, sparse selected item ID and no prior production review. Avoid author-controlled release fields and any GitHub credential/network path.
3. Hook into trusted `check_external_review.py --publish-handoff`: after assembler, before fresh live observation and exclusive write. Keep both live GitHub checks and OIDC signing unchanged.
4. `python -m unittest tests.i033e8` and full Python 3.10/3.12 suite under existing full-suite CI; no new ticket workflow.
5. Independent adversarial code/data review on exact head against the ten real original corpus codes, immutable base release IDs, and forced digest recomputation. Re-review final head if changed. Expected-head squash only after full CI green.
