# I-016 plan — versioned seven-corpus coverage manifests

**Issue:** #204  
**Parent:** P-004 #202, Workstream A  
**Research:** `docs/research/I-016-seven-corpus-coverage-accounting.md`  
**Baseline:** `main` after research merge `c2d266c064cb46e0239a8323f496d0f6d2077e4c`

## 1. Exit condition

The repository can deterministically build, validate, load and report seven immutable coverage manifests for the historical R-011 denominator while:

- preserving the exact aggregate denominator of 685 semantic items;
- distinguishing `machine-exhaustive` from `bounded-curated` scope;
- distinguishing current from stale source coverage by exact revision identity;
- distinguishing research-reviewed from production-reviewed accounting;
- exposing I-015's 21 production-reviewed denominator items without promoting R-011 pilot mappings to production authority;
- refusing corpus-wide completion claims for stale, curated or incompletely production-reviewed manifests;
- keeping technical exclusions outside semantic denominator counts;
- preserving historical R-005/R-011 inputs unchanged.

No ontology mapping or runtime resolver semantics change in I-016.

## 2. Public/source contract

Add `coverage-manifest.schema.json`, registered in `source_validation.SCHEMA_FILES`.

Manifest v1:

```text
schema_version = 1
manifest_id
corpus_id
repository
denominator_source_revision
target_corpus_revision
optional tf_version
scope_quality = machine-exhaustive | bounded-curated

denominator_basis:
  kind = generated-r005-inventory | curated-r011-baseline
  source
  bounded_node_features[]

semantic_items[]:
  item_id
  kind = node_type | node_feature | node_value | edge_feature |
         edge_value | external_reference | assertion_shape
  accounting:
    authority = unreviewed | research | production
    assessments[]          # accepted R-002 assessment vocabulary
    common_target          # bool
    source_ids[]           # mappings/reviewed sources at selected authority
    optional profiles[]    # controlled R-014 profile IDs
    optional capabilities[]# controlled R-014 capability IDs

technical_exclusions[]:
  item_id
  kind
  reason

denominator_digest
optional generated_at
```

Schema stays closed (`additionalProperties: false`) at every owned object where practical.

### Cross-field rules owned by Python validation

JSON Schema alone is insufficient for:

- duplicate item IDs with non-identical objects;
- semantic-item / technical-exclusion overlap;
- accounting invariants;
- denominator digest verification;
- controlled profile/capability membership consistency;
- source/target revision freshness derivation.

Add a coverage-specific validator in a new module rather than weakening generic I-001 validation.

## 3. Digest contract

Add:

`COVERAGE_DENOMINATOR_ALGORITHM = "tfont-coverage-denominator-jcs-sha256-v1"`.

`coverage_denominator_projection(manifest)` binds:

- schema version;
- corpus ID;
- repository;
- denominator source revision;
- target corpus revision;
- TF version when present;
- scope quality;
- denominator basis;
- canonical semantic item identities/kinds;
- canonical technical exclusions.

It excludes:

- accounting authority/assessment/source IDs;
- `denominator_digest`;
- `generated_at`.

Rationale: ontology review progress may change without changing what the denominator *is*. A later coverage-state digest can be introduced if/when needed; I-016 must not overload denominator identity.

Use existing RFC 8785/JCS and SHA-256 helpers.

Ordering:
- set-like records canonicalized by UTF-16 item ID;
- assessments/profile/capability/source ID collections deduplicated and UTF-16 sorted;
- duplicate canonical item identity fails closed.

## 4. Accounting authority

The manifest explicitly prevents historical research from becoming production authority.

### `unreviewed`

- no assessments;
- `common_target=false`;
- no source IDs required;
- not counted as reviewed at any level.

### `research`

- sourced from effective R-011 mappings/overrides;
- assessment(s) preserved;
- common-target derived only from the effective R-011 target-bearing rows;
- counted as research-reviewed, not production-reviewed;
- never makes P-004 completion eligible.

### `production`

- only from currently reviewed production mapping resources;
- initial importer supports I-015 0.2.0 scalar/value-set mappings;
- mapping and projection review status must be `reviewed`;
- selected native bindings must map deterministically to denominator item IDs;
- an item referenced by production authority but absent from the denominator fails closed.

When a production item also has R-011 research authority, production wins as the selected accounting authority; historical research identity does not become a second production source.

## 5. Baseline importer

Add `scripts/coverage/build_p004_r011_baseline.py`.

Inputs are repository-local only:

- `docs/research/data/r-011/pilots.json`;
- `mapping-overrides.json`;
- `raw-schema-policy.json`;
- five generated R-005 inventories;
- current I-015 production linguistic resources.

No network access and no live GitHub lookup.

### Historical denominator

Build exactly:

| corpus | semantic items |
| --- | ---: |
| bhsa | 219 |
| cuc | 37 |
| syriac | 74 |
| extrabiblical | 136 |
| tlhdig | 137 |
| pseudepigrapha | 40 |
| oracc | 42 |
| **total** | **685** |

Bounded node values are expanded only from the explicit R-011 `bounded_features` policy.

### Manifest target revisions

The baseline records the exact research-time target revisions from I-016 research:

- BHSA: `4db00e2157915495e1a4d3d57e41223df24775da`;
- CUC: `ad69400f5446e1c8217af01659c7c10ab00c015b`;
- Syriac: `bb0eaa7e21b020a26b7566d2e495da9b1f84a919`;
- ExtraBiblical: `9a56288e6777bad6328856acf055c780e65dd5d9`;
- Pseudepigrapha: `7c4b757bb543a110ae9a252d1281835859136852`;
- ORACC: `85d2f131202882d40b05b65bfb4c83e8b1238426`;
- TLHdig: `bc4a206690c1856d3cfde8b291f626c45a712640`.

These are immutable manifest inputs, not runtime lookups.

Expected freshness:
- current: BHSA, CUC, Syriac, ExtraBiblical;
- stale: Pseudepigrapha, ORACC, TLHdig.

Expected scope:
- machine-exhaustive: BHSA, CUC, Syriac, ExtraBiblical, TLHdig;
- bounded-curated: Pseudepigrapha, ORACC.

## 6. Research accounting baseline

Reuse the R-011 effective fixture after applying `mapping-overrides.json`.

Expected research-reviewed item counts:

| corpus | total | research-reviewed | research common-target |
| --- | ---: | ---: | ---: |
| bhsa | 219 | 34 | 6 |
| cuc | 37 | 9 | 3 |
| syriac | 74 | 11 | 6 |
| extrabiblical | 136 | 22 | 5 |
| tlhdig | 137 | 8 | 3 |
| pseudepigrapha | 40 | 8 | 1 |
| oracc | 42 | 7 | 2 |
| **aggregate** | **685** | **99** | **26** |

These counts remain descriptive research authority.

## 7. I-015 production bridge

The importer additionally reads the three production linguistic 0.2.0 mapping resources.

Supported binding-to-item projection in I-016:

- `value-predicate` → one `node_value:<feature>=<canonical JSON scalar>`;
- `value-set-predicate` → one denominator item per selected value.

Only exact, reviewed production projections are used.

Expected unique production-reviewed items:

- BHSA: 7;
- Syriac: 7;
- ExtraBiblical: 7;
- others: 0;
- aggregate: 21.

The seven per ETCBC-family corpus are the native denominator items used by current Noun/ProperNoun/gender/number production mappings.

This bridge is deliberately narrow. Future graph-shaped production mappings extend the coverage importer under their own tickets rather than being guessed now.

## 8. Coverage report API

Add immutable report dataclasses/functions in `src/tfont/coverage.py`:

- `CoverageProblem`;
- `CoverageError`;
- `load_coverage_manifest(...)`;
- `validate_coverage_manifest(...)`;
- `coverage_denominator_projection(...)`;
- `coverage_denominator_digest(...)`;
- `coverage_report(...)`;
- `load_p004_r011_baseline_manifests()`.

Per-corpus report fields:

- corpus ID;
- denominator digest;
- semantic item count;
- technical exclusion count;
- research-reviewed count;
- production-reviewed count;
- production-unreviewed count;
- production common-target count;
- production assessment counts;
- scope quality;
- freshness = current | stale;
- `bounded_scope_complete`;
- `corpus_wide_completion_claim_eligible`.

Definitions:

`bounded_scope_complete`:
- every semantic item has production authority.

`corpus_wide_completion_claim_eligible`:
- scope quality = machine-exhaustive;
- freshness = current;
- bounded scope complete.

Initial baseline must report all seven as corpus-wide ineligible because no corpus has full production review yet.

## 9. Baseline resource layout

Commit immutable generated manifests under:

`src/tfont/resources/coverage/p004-r011-baseline-v1/<corpus>.json`

for exactly seven corpus IDs.

Add package-data inclusion for `resources/coverage/*/*.json`.

The builder supports:
- normal write mode;
- `--check` mode that regenerates canonical data in memory and fails if committed resources differ byte-for-byte.

This prevents hand-edited drift.

Historical R-005/R-011 files remain unchanged.

## 10. TDD sequence

### RED commit

Before production code/resources:

Create `tests/i016/` contract tests requiring:

1. `coverage-manifest` registered schema;
2. coverage public/module API exists;
3. seven baseline resources are loadable;
4. aggregate denominator = 685;
5. exact per-corpus totals above;
6. research-reviewed aggregate = 99 and common-target = 26;
7. production-reviewed aggregate = 21;
8. stale/current and scope-quality states match research;
9. no initial corpus-wide completion eligibility.

RED must fail because the coverage schema/module/resources do not yet exist.

### GREEN behavior/adversarial tests

Add tests for:

- duplicate semantic item ID;
- semantic/technical overlap;
- missing/invalid exact revision;
- digest mismatch;
- semantic item mutation changes denominator digest;
- accounting-only mutation does **not** change denominator digest;
- `generated_at` mutation does not change denominator digest;
- bounded-curated never corpus-wide eligible;
- stale never corpus-wide eligible;
- unreviewed never production-reviewed;
- invalid assessment rejected;
- research authority not counted as production;
- production binding absent from denominator fails importer/check;
- finite observed value not expanded unless explicitly listed in bounded policy;
- builder `--check` equivalent output is deterministic.

## 11. Files allowed in implementation

Expected implementation scope:

- `src/tfont/schemas/coverage-manifest.schema.json`
- `src/tfont/source_validation.py`
- `src/tfont/coverage.py`
- `src/tfont/__init__.py`
- `src/tfont/resources/coverage/p004-r011-baseline-v1/*.json`
- `scripts/coverage/build_p004_r011_baseline.py`
- `tests/i016/**`
- `.github/workflows/i016-coverage.yml`
- `pyproject.toml`

If implementation needs to modify historical R-005/R-011 input artifacts or current production mapping/profile resources, stop and amend the plan instead.

## 12. CI

Add narrow exact-head PR gate on Python 3.10 and 3.12:

1. install editable package;
2. run `tests/i016`;
3. run builder `--check`.

The authoritative full repository suite must also pass on the exact GREEN head.

## 13. Independent review gate

Final adversarial review must challenge:

- the 685 denominator arithmetic;
- research vs production authority separation;
- exact I-015 item projection;
- stale/current derivation;
- curated-scope claim boundary;
- digest projection independence from accounting/timestamps;
- denominator mutation sensitivity;
- generated-resource reproducibility;
- historical R-005/R-011 immutability;
- package inclusion in a clean wheel;
- no network/runtime dependency introduced.

Merge only with expected exact head SHA. After merge, verify main full suite and close #204 only after readback.

## 14. Follow-up handoff

I-017/#206, I-018/#207 and I-019/#208 own fresh denominators for Pseudepigrapha, ORACC and TLHdig respectively.

They must create new immutable coverage-manifest versions. They may not edit `p004-r011-baseline-v1` in place.
