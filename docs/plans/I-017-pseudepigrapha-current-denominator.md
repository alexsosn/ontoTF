# I-017 plan — publish the current Pseudepigrapha-TF coverage denominator

Issue: #206  
Parent: P-004 #202, Workstream A  
Research: `docs/research/I-017-pseudepigrapha-current-denominator.md`  
Baseline: main `68418645e368534b4996413b232f7f6cf491a014`

## Exit condition

ontoTF ships a second immutable Pseudepigrapha coverage manifest for the
published Pseudepigrapha-TF v1.0.0 / TF 1.0 artifact.

The historical
`p004-r011-baseline-v1/pseudepigrapha.json` remains byte-for-byte unchanged.

The new manifest:

- is `machine-exhaustive` only for the exact materialized TF 1.0 schema;
- contains exactly 113 semantic denominator items;
- records exactly 5 technical exclusions;
- contains no outside-denominator accounting gaps;
- starts with all 113 semantic items production-unreviewed;
- does not promote or silently copy historical R-011 ontology assessments;
- binds the exact release commit and binary/materialized payload identity;
- can be loaded from an installed wheel through a generic packaged-manifest API;
- is deterministically regenerated from repository-local compact evidence and
  explicit denominator policy.

No ontology mapping, resolver or execution behavior changes in I-017.

## Immutable resource identity

Create a new resource set:

`p004-pseudepigrapha-v1.0.0-v1`

with exactly:

`src/tfont/resources/coverage/p004-pseudepigrapha-v1.0.0-v1/pseudepigrapha.json`

Manifest ID:

`coverage:p004-pseudepigrapha-v1.0.0-v1:pseudepigrapha`

Pinned corpus identity:

- repository: `alexsosn/Pseudepigrapha-TF`;
- denominator source revision:
  `7c4b757bb543a110ae9a252d1281835859136852`;
- target corpus revision: same;
- TF version: `1.0`.

The historical resource set is immutable and remains the default only for the
historical baseline loader.

## Artifact identity extension

The I-016 coverage schema currently binds repository/revision/TF version but
does not bind a mutable GitHub release asset. Because the v1.0.0 release is not
GitHub-immutable, I-017 adds an optional closed object under
`denominator_basis`:

```
artifact_identity:
  locator
  sha256
  materialized_sha256
```

For I-017:

- locator: `github-release:v1.0.0/tf-1.0.zip`;
- sha256:
  `d2dfad7e643699617a9493b9f5d724868f8027dd5f2e88bd558451e3e7819b7a`;
- materialized_sha256:
  `9b708add5b9f8ddbfdafa7dd61507956f7987ca6a70b2b9164342bd49003ec61`.

Both digests use lowercase 64-hex SHA-256.

Rules:

1. `artifact_identity` is optional so historical I-016 manifests remain valid.
2. When present, all three fields are required.
3. `coverage_denominator_projection()` includes the complete object.
4. Therefore mutating locator, archive digest or materialized TF digest changes
   the denominator digest.
5. Historical denominator digests must remain unchanged because the field is
   absent from historical manifests.

## Denominator policy input

Add a small explicit repository-local policy file:

`docs/research/data/i017/pseudepigrapha-denominator-policy.json`.

It is implementation input, not runtime data. It records only reviewed choices
that cannot be inferred safely from cardinality:

```
technical_node_features:
  boundary_utf8
  is_gap
  reading_option

technical_warp_node_features:
  otype

technical_warp_edge_features:
  oslots

bounded_node_values:
  generation_marker: ["OCP-Trans"]
  version_kind: ["generated_translation", "source"]
  is_metadata_only: [1]
  is_missing_unit_id: [1]
  is_omission: [1]
  is_primary: [1]
  is_source_anomaly: [1]
  synthetic_witness: [1]
  undefined_manuscript: [1]
```

The file also records stable source IDs for each technical exclusion and
bounded-family decision. It must not contain ontology targets.

The generated manifest's `denominator_basis.bounded_node_features` is exactly
the nine bounded-family feature names from this policy, sorted canonically:
`generation_marker`, `is_metadata_only`, `is_missing_unit_id`,
`is_omission`, `is_primary`, `is_source_anomaly`, `synthetic_witness`,
`undefined_manuscript`, `version_kind`.

## Deterministic builder

Add:

`scripts/coverage/build_i017_pseudepigrapha_v1.py`.

Inputs:

- `docs/research/data/generated/i017/pseudepigrapha-v1.0.0.json`;
- `docs/research/data/i017/pseudepigrapha-denominator-policy.json`.

No network, GitHub API, Text-Fabric import or live corpus acquisition is allowed
in the builder.

Algorithm:

1. validate the compact evidence release identity against exact constants;
2. validate policy references only materialized feature identities, except the
   explicitly listed warp support features;
3. enumerate one `node_type` item per materialized node type;
4. enumerate one `node_feature` item per non-technical materialized node
   feature;
5. enumerate one `edge_feature` item per materialized non-warp edge feature;
6. enumerate `node_value` items only from the explicit bounded-value policy;
7. create technical exclusions for the two warp/support features plus the three
   reviewed non-warp technical features;
8. fail if any materialized feature is neither semantic nor technically
   accounted;
9. fail if any technical identity also appears in the semantic denominator;
10. set semantic research/production accounting to null;
11. set technical exclusions to production authority with reviewed I-017
    source IDs;
12. compute the normal I-016 denominator digest;
13. validate the resulting manifest with the production coverage validator.

Expected arithmetic:

- 13 node types;
- 83 semantic node features;
- 7 semantic edge features;
- 10 bounded node values;
- 113 semantic items;
- 5 technical exclusions;
- 0 accounting gaps.

The builder supports write mode and `--check` byte-for-byte regeneration.

## Research-accounting boundary

Do not copy historical R-011 research accounting into the new manifest in
I-017.

Rationale:

- the old 40-item denominator remains available as immutable historical
  research evidence;
- I-017 reviewed the current native schema boundary, not the old ontology
  mappings;
- same item spelling alone is insufficient authority to carry an ontology
  assessment across a changed corpus/release.

Later mapping work may reuse R-011 rows as leads after fresh source/ontology
review.

## Packaged resource API

Generalize the private packaged loader into a public reusable API:

`load_packaged_coverage_manifest(resource_set: str, corpus_id: str)`.

Requirements:

- resource-set and corpus identifiers are restricted to safe simple package
  path components; slash, backslash, `..`, empty names and traversal-like
  input fail closed;
- unsafe components fail as `CoverageError(category="invalid_resource_component")`;
- a safe but absent packaged manifest fails as
  `CoverageError(category="missing_resource")`;
- the function loads one packaged JSON manifest and runs full coverage
  validation;
- `load_p004_r011_baseline_manifests()` delegates to this generic function
  without changing its public behavior;
- export the generic loader at package root.

Add constant:

`P004_PSEUDEPIGRAPHA_V1_RESOURCE = "p004-pseudepigrapha-v1.0.0-v1"`.

No registry/discovery system is introduced in this ticket.

## TDD RED

Before production implementation, add `tests/i017/` asserting that the current
main fails because the new manifest/API/schema extension do not yet exist.

RED contract:

1. generic packaged coverage loader exists and is exported;
2. artifact identity is accepted and bound by denominator digest;
3. the new packaged Pseudepigrapha resource exists and validates;
4. report has:
   - semantic_items = 113;
   - technical_exclusions = 5;
   - production_reviewed_items = 0;
   - production_unreviewed_items = 113;
   - production_outside_denominator_items = 0;
   - scope_quality = machine-exhaustive;
   - freshness = current;
   - bounded_scope_complete = false;
   - corpus_wide_completion_claim_eligible = false;
5. exact expected node-type set is present;
6. exact five technical identities are absent from semantic items and present
   as technical exclusions;
7. all 10 approved bounded value items are present;
8. representative unapproved finite observations are absent as value items,
   including language, ms_language, reading_option, boundary_utf8,
   generated_language, text_structure and linebreak;
9. historical Pseudepigrapha baseline remains 40 semantic items and keeps its
   current denominator digest;
10. builder check is deterministic.

The RED commit must precede production implementation and the failure must be
observed.

## GREEN / adversarial tests

Add explicit regressions for:

- artifact archive digest mutation changes denominator digest;
- materialized TF digest mutation changes denominator digest;
- historical manifest without artifact identity retains its digest;
- malformed artifact SHA-256 is rejected;
- partial artifact identity object is rejected;
- policy technical/semantic overlap fails;
- policy references an absent materialized feature and fails;
- an evidence feature omitted from both semantic and technical accounting
  fails;
- observed-small-domain values are not auto-expanded;
- changing an observed open-domain value does not alter the denominator when
  the feature identity remains present;
- changing the materialized feature set does alter generated denominator
  identity;
- duplicate bounded values fail;
- path traversal and unsafe packaged-loader components fail;
- missing packaged resource fails with a coverage problem;
- wheel contains both the historical resource set and the new I-017 resource.

## Files allowed in implementation

Expected:

- `src/tfont/schemas/coverage-manifest.schema.json`;
- `src/tfont/coverage.py`;
- `src/tfont/__init__.py`;
- `docs/research/data/i017/pseudepigrapha-denominator-policy.json`;
- `scripts/coverage/build_i017_pseudepigrapha_v1.py`;
- `src/tfont/resources/coverage/p004-pseudepigrapha-v1.0.0-v1/pseudepigrapha.json`;
- `tests/i017/**`;
- `.github/workflows/i017-pseudepigrapha-coverage.yml`;
- `pyproject.toml` only if package-data coverage actually requires a change.

Historical R-005/R-011 inputs, the I-016 baseline resources, ontology resources,
production mappings and runtime resolver/executor files are out of scope.

If implementation discovers that one of those must change, stop and amend the
plan.

## CI

Add exact-head Python 3.10/3.12 focused CI that:

1. installs the package;
2. runs `tests/i017`;
3. runs the I-017 builder with `--check`;
4. builds a wheel;
5. verifies the new packaged manifest is present;
6. verifies the historical coverage resources remain present.

The authoritative Full repository suite must pass on the exact final head.

The research workflow remains separate because it is the only networked job:
production builder/tests consume committed evidence only.

## Final adversarial review

Fresh review of the implementation exact head must independently challenge:

- the 113/5 arithmetic;
- exhaustive accounting of every materialized TF schema item;
- the three non-warp technical decisions;
- the 10 closed-value decisions;
- absence of cardinality-derived enum inflation;
- archive/materialized digest binding;
- historical baseline immutability;
- no transfer of historical mapping authority;
- package-resource path safety;
- deterministic offline regeneration;
- no network dependency in TFont runtime or production builder.

Merge only with the reviewed exact head SHA. After merge, verify the new
manifest from main and close #206 only after readback.
