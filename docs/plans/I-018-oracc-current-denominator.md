# I-018 plan — publish the current ORACC registered-build denominator

Issue: #207  
Parent: P-004 #202, Workstream A  
Research: `docs/research/I-018-oracc-current-denominator.md`  
Baseline: main `b14708ac9c4a8686a32a3518c76ffc846a90e5fa`

## Exit condition

ontoTF ships a second immutable ORACC coverage manifest for the exact current
ORACC-TF registered-build candidate described by I-018 research.

The historical
`p004-r011-baseline-v1/oracc.json` remains byte-for-byte unchanged.

The new manifest:

- is `machine-exhaustive` only for the exact materialized TF 0.4.0 schema of
  the registered `assyrian-royal-inscriptions` candidate;
- contains exactly 99 semantic denominator items;
- records exactly 6 technical exclusions;
- contains no outside-denominator accounting gaps;
- starts with all 99 semantic items production-unreviewed;
- does not transfer historical R-011 ontology assessments by spelling alone;
- binds both the complete registered candidate tree (including
  `translation-gaps.json`) and the TF-only feature tree;
- can be loaded from an installed wheel through the existing generic packaged
  coverage loader;
- is deterministically regenerated offline from committed I-018 evidence and
  an explicit reviewed denominator policy.

No ontology mapping, resolver, execution or corpus-conversion behavior changes
in I-018.

## Immutable resource identity

Create:

`p004-oracc-0.4.0-f6f189b-v1`

with exactly:

`src/tfont/resources/coverage/p004-oracc-0.4.0-f6f189b-v1/oracc.json`

Manifest ID:

`coverage:p004-oracc-0.4.0-f6f189b-v1:oracc`

Pinned corpus identity:

- repository: `alexsosn/ORACC-TF`;
- denominator source revision:
  `f6f189bbd99d72bfdc7044555bd3113aa7b54232`;
- target corpus revision: same;
- TF version: `0.4.0`;
- registered dataset: `assyrian-royal-inscriptions`.

This name deliberately describes the pre-1.0 registered candidate. It must not
be renamed to imply an ORACC-TF 1.0 release.

## Artifact identity

Use the artifact identity schema introduced by I-017 without changing it.

`denominator_basis.artifact_identity`:

- locator:
  `registered-build:alexsosn/ORACC-TF@f6f189bbd99d72bfdc7044555bd3113aa7b54232:assyrian-royal-inscriptions/tf/0.4.0`;
- `sha256`:
  `cbcc8299c1f5d02bc082ded824452fe3fb0a7857656a0556039a31667c48af1b`;
- `materialized_sha256`:
  `5d23f56eaa9461d7a6f42dc11a8c2f5d7307ba9820f49869400c5ac9af8bf34f`.

For this resource, `sha256` is the deterministic complete candidate-tree
digest, not a release ZIP digest. It includes the one non-TF sidecar
`translation-gaps.json`. `materialized_sha256` is the established R-005
TF-feature-file digest.

The top-level revision plus artifact locator/digests therefore binds the exact
builder/data candidate without inventing a release asset.

## Source identity retained in evidence

The production manifest does not duplicate every research field. Its
denominator source and artifact identity are backed by committed evidence that
also pins:

- RIAO Git tree
  `b03bf0544f4c83710dc6ea88b26b6389e9b85645`;
- RINAP Git tree
  `96ddf1d4e6bbf37b6ec4a3e37f42e8fae899593c`;
- `datasets.toml` blob
  `584d4671959b4f5d35535bc796521299eb6e040e`;
- TEI archive name `riao-teiCorpus-20241202.zip`;
- TEI SHA-256
  `b793d8920db58908e3a044b7f2d1a204c1ba0784e880007e0cd7941333e841bd`;
- complete candidate census, including the 2,509 translation gaps.

The manifest's denominator basis source is:

`docs/research/data/generated/i018/oracc-0.4.0.json`.

## Denominator policy input

Add:

`docs/research/data/i018/oracc-denominator-policy.json`.

It is repository/build input, not TFont runtime data.

Required reviewed technical features:

```json
{
  "technical_node_features": [
    "cuneiform_trailer",
    "lnno",
    "readingu",
    "synthetic"
  ],
  "technical_warp_node_features": ["otype"],
  "technical_warp_edge_features": ["oslots"]
}
```

Required closed semantic values:

```json
{
  "bounded_node_values": {
    "catalogue_present": [0, 1],
    "chunk_type": ["discourse", "phrase", "sentence", "text"],
    "lemmaknown": [0, 1],
    "populated": [0, 1]
  }
}
```

The policy also records stable I-018 source IDs for each technical decision and
each bounded family. It must not contain ontology targets.

The generated manifest's `denominator_basis.bounded_node_features` is exactly
the four sorted feature names:

- `catalogue_present`;
- `chunk_type`;
- `lemmaknown`;
- `populated`.

No observed-cardinality heuristic may add another family.

## Deterministic offline builder

Add:

`scripts/coverage/build_i018_oracc_current.py`.

Inputs:

- `docs/research/data/generated/i018/oracc-0.4.0.json`;
- `docs/research/data/i018/oracc-denominator-policy.json`.

The builder must not:

- access the network;
- import Text-Fabric;
- import ORACC-TF;
- acquire or build a corpus;
- inspect a live Git checkout other than its committed input files.

Algorithm:

1. validate the complete committed candidate identity against exact constants;
2. validate evidence schema counts and slot type `sign`;
3. require the expected sidecar set to be exactly
   `translation-gaps.json` with the committed size from research evidence;
4. validate policy technical node features are actually materialized;
5. validate warp exclusions exactly match `otype` / `oslots`;
6. enumerate one `node_type` item per materialized node type;
7. enumerate one `node_feature` item per non-technical materialized node
   feature;
8. enumerate one `edge_feature` item per materialized non-warp edge feature;
9. enumerate `node_value` items only from the explicit bounded policy;
10. fail if any materialized feature is not accounted as semantic or technical;
11. fail if any semantic identity overlaps a technical exclusion;
12. explicitly fail if any `translation_note*` identity or
    `translation_note_unit` is introduced by documentation rather than
    materialized evidence;
13. set research and production accounting to null for every semantic item;
14. create six production-authority technical exclusions with reviewed source
    IDs;
15. set `accounting_gaps=[]`;
16. compute the normal coverage denominator digest;
17. validate through `validate_coverage_manifest()`.

Expected arithmetic:

- 10 node types;
- 71 semantic node features;
- 8 semantic edge features;
- 10 bounded node values;
- **99 semantic items**;
- **6 technical exclusions**.

Support both write mode and `--check` byte-for-byte regeneration.

## Translation sidecar boundary

The evidence records 6,792 materialized `translation_unit` nodes and 2,509
non-materialized translation gaps.

The new manifest must include the materialized translation schema:

- `node_type:translation_unit`;
- the materialized `translation_*` node features;
- `edge_feature:translation_document`;
- `edge_feature:translation_line`.

It must not invent:

- `node_type:translation_note`;
- `node_feature:translation_note_id`;
- `node_feature:translation_note_text`;
- `edge_feature:translation_note_unit`.

The sidecar records are not TF nodes/features and do not become semantic
denominator items. Their bytes are nevertheless bound by the complete
candidate-tree artifact digest.

## Research-accounting boundary

Do not copy historical R-011 research or production accounting into the new
manifest.

The old 42-item manifest remains available as immutable historical evidence.
The current schema differs materially, including historical identities that no
longer materialize and a translation layer that did not exist in R-011.

Matching spelling is not authority to transfer an ontology assessment across
that boundary.

## Package API

Reuse `load_packaged_coverage_manifest(resource_set, corpus_id)` from I-017.

Add and export:

`P004_ORACC_0_4_0_RESOURCE = "p004-oracc-0.4.0-f6f189b-v1"`.

No new loader, registry or schema version is required.

If implementation discovers a need to alter the coverage manifest schema or
generic loader semantics, stop and amend this plan before production changes.

## TDD RED

Before adding the policy, builder, constant or packaged manifest, add
`tests/i018/` on a dedicated implementation branch.

The tests-only RED must require:

1. `P004_ORACC_0_4_0_RESOURCE` exists and is exported;
2. the new packaged ORACC resource exists and validates;
3. report values are exactly:
   - semantic_items = 99;
   - technical_exclusions = 6;
   - production_reviewed_items = 0;
   - production_unreviewed_items = 99;
   - production_outside_denominator_items = 0;
   - research_outside_denominator_items = 0;
   - scope_quality = `machine-exhaustive`;
   - freshness = `current`;
   - bounded_scope_complete = false;
   - corpus_wide_completion_claim_eligible = false;
4. exact node types are:
   `chunk`, `column`, `document`, `face`, `lex`, `line`, `phrase`,
   `sign`, `translation_unit`, `word`;
5. exact technical identities are:
   - `node_feature:otype`;
   - `edge_feature:oslots`;
   - `node_feature:cuneiform_trailer`;
   - `node_feature:lnno`;
   - `node_feature:readingu`;
   - `node_feature:synthetic`;
6. all ten bounded value items are present;
7. documented-but-unmaterialized translation-note identities are absent;
8. representative open/small domains do not get `node_value` items, including
   `translation_subtype`, `translation_rows`, `chunk_subtype`,
   `implicit`, `lang`, `language`, `pos`, `epos`, `period`,
   `script`, and the `translation_source_*` provenance fields;
9. artifact locator and both digests match research evidence;
10. historical ORACC baseline remains exactly 42 items with denominator digest
    `sha256:019d19e1248a19238fc3eadc1fd6e05ae0d1c0f596f0a6ef991a93c09bd65685`;
11. the offline builder and policy files exist.

The RED commit must precede any production change. Record a real failing exact
head before implementing GREEN.

## GREEN and adversarial tests

After RED is recorded, implement the minimum contract and add regressions for:

- technical policy referencing a non-materialized feature fails;
- a bounded feature reclassified technical fails;
- duplicate bounded values fail;
- missing/extra materialized node feature accounting fails;
- missing/extra edge accounting fails;
- node-type drift changes/fails the fixed denominator contract;
- adding a documented-only `translation_note` identity without materialized
  evidence fails;
- changing observed values/cardinality of an open-domain feature does not
  change the denominator;
- changing a materialized schema identity does change/fail denominator
  generation;
- mutating candidate-tree identity fails exact evidence pinning;
- mutating TF-only digest fails exact evidence pinning;
- mutating the sidecar set/size fails exact evidence pinning;
- changing a `translation_source_*` singleton value does not auto-create a
  value item;
- builder source contains no network acquisition, Text-Fabric import or
  ORACC-TF import;
- historical 42-item ORACC manifest remains unchanged;
- wheel includes both historical ORACC and current ORACC resources.

## Files allowed in implementation

Expected:

- `src/tfont/coverage.py` — resource constant only;
- `src/tfont/__init__.py` — export only;
- `docs/research/data/i018/oracc-denominator-policy.json`;
- `scripts/coverage/build_i018_oracc_current.py`;
- `src/tfont/resources/coverage/p004-oracc-0.4.0-f6f189b-v1/oracc.json`;
- `tests/i018/**`;
- `.github/workflows/i018-oracc-coverage.yml`.

No changes are expected to:

- coverage-manifest schema;
- generic packaged loader behavior;
- historical `p004-r011-baseline-v1/oracc.json`;
- ontology resources;
- production mappings;
- resolver/execution behavior;
- ORACC-TF source/converter/data.

Any such need requires an explicit plan amendment before implementation.

## Focused CI

Add exact-head Python 3.10/3.12 CI that:

1. installs ontoTF;
2. runs `tests/i018`;
3. runs the I-018 builder with `--check`;
4. builds a wheel;
5. verifies both historical and current ORACC coverage resources are packaged.

The authoritative Full repository suite must also pass on the final exact head.

The networked registered-build workflow remains a research reproducibility
gate. Production build/tests consume only committed evidence.

## Final logically-independent review

Fresh review of the final implementation exact head must independently
challenge:

- 99/6 arithmetic;
- completeness of all 75 materialized non-warp node features and eight edges;
- the four non-warp technical classifications;
- the four bounded semantic families / ten values;
- exclusion of observed-only small domains;
- actual materialization of translation schema versus documented capability;
- treatment of the 2,509 gap records as sidecar/artifact data rather than TF
  nodes;
- candidate-tree and TF-only digest binding;
- historical 42-item manifest immutability;
- absence of historical authority transfer;
- deterministic offline regeneration;
- wheel resource availability.

Merge only with the reviewed exact head SHA. After merge, read the packaged
manifest from main and close #207 only after the 99/6 report is reproduced.
