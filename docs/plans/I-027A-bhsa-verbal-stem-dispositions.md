# I-027A plan — immutable BHSA verbal-stem accounting successor

**Issue:** #272  
**Parent:** I-027 #264 / P-004 #202  
**Research:** `docs/research/I-027A-bhsa-verbal-stem-dispositions.md`  
**Baseline:** `main` `2dafb9573ec5eaeb7a677b47340bd3066530e2f8`

## Contract and exit

Generate a new immutable packaged coverage manifest for BHSA with the same exact 219 semantic item IDs and canonical denominator digest as the historical current baseline. Exactly the 27 `vs` family records receive new production accounting:

```json
{
  "assessments": ["native-only"],
  "common_target": false,
  "source_ids": ["i027a:bhsa-vs-pinned-source-review"],
  "profiles": ["linguistic"],
  "capabilities": ["linguistic.morphology"]
}
```

The source ID resolves to the pinned evidence and semantic review documented in the research file and PR. Existing research/production layers remain unmodified.

## Files

- `docs/research/data/i027a/bhsa-verbal-stem-policy.json` — exact manifest/source pin, selected feature, 26 lexical code spellings, review source ID, expected metrics;
- `scripts/coverage/build_i027a_bhsa_verbal_stems.py` — local deterministic generator with `--check`, no network;
- `src/tfont/resources/coverage/p004-i027a-bhsa-stems-v1/bhsa.json` — immutable generated successor;
- `tests/i027a/test_accounting_red.py` and `tests/i027a/test_accounting_adversarial.py`;
- `.github/workflows/i027a-bhsa-stems.yml` focused exact-head matrix CI.

## Validation

The builder must:

1. Load and validate the historical BHSA manifest through `tfont.coverage`;
2. pin exact repository, TF version, corpus/source revision, denominator digest and inventory evidence location;
3. require the selected `vs` family to match exactly the 27 already-bounded manifest rows;
4. compare the value spellings with the existing R-005 inventory; observed frequencies are evidence, **not** authority to expand the denominator;
5. copy the full historical manifest and modify only its `manifest_id` plus production accounting of the 27 selected rows;
6. preserve research accounting, existing production exact mappings and any technical exclusions;
7. validate the successor using the production coverage schema, digest verifier and `coverage_report`;
8. require 34 production reviewed, 7 common-target, 185 unreviewed, zero accounting gaps.

## TDD and adversarial gate

RED tests before implementation cover builder/artifact absence, exact 27 delta, byte-for-byte `--check`, prior authority preservation, no fabricated ontology target, and denominator identity.

Mutation/negative controls reject: missing/extra code; changed source corpus/revision; changed denominator digest; changed assessment from `native-only` to `exact`; attempts to touch another linguistic feature or historical manifest; `NA` promoted to a positive common target.

GREEN: implement minimal offline builder and generated artifact without altering runtime mappings.

After green: focused + full exact-head CI, fresh logically-independent skeptical review grounded in R-005 inventory and real source meanings, expected-head merge. Do **not** close I-027 #264; this completes only 27/380 of its routed items.
