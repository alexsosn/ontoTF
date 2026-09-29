# I-019 plan — publish the current TLHdig-TF denominator

Issue: #208  
Parent: P-004 #202, Workstream A  
Research: `docs/research/I-019-tlhdig-current-denominator.md`  
Baseline: main `16a7e9c4d5cbbb9b8c9ca4396035ae288c6ebceb`

## Exit condition

ontoTF ships a second immutable TLHdig coverage manifest for the exact shipped
TLHdig-TF 0.4.0 core + provenance artifact identified by I-019 research.

The historical
`p004-r011-baseline-v1/tlhdig.json` remains byte-for-byte unchanged.

The new manifest:

- is `machine-exhaustive` only for the complete shipped core +
  `tf-provenance/0.4.0` schema at the pinned TLHdig-TF revision;
- contains exactly 256 semantic denominator items;
- records exactly 4 technical exclusions;
- contains no outside-denominator accounting gaps;
- starts with all 256 semantic items research- and production-unreviewed;
- transfers no historical R-005/R-011 ontology authority by spelling alone;
- binds the complete BUILD-MANIFEST output tree and the exact combined
  materialized TF modules;
- is deterministically regenerated offline from committed I-019 evidence and
  an explicit reviewed denominator policy;
- is loadable through the existing generic packaged coverage loader.

No ontology mapping, resolver, execution or TLHdig corpus-conversion behavior
changes in I-019.

## Immutable resource identity

Create:

`p004-tlhdig-0.4.0-bc4a206-v1`

with exactly:

`src/tfont/resources/coverage/p004-tlhdig-0.4.0-bc4a206-v1/tlhdig.json`

Manifest ID:

`coverage:p004-tlhdig-0.4.0-bc4a206-v1:tlhdig`

Pinned corpus identity:

- repository: `alexsosn/TLHdig-TF`;
- denominator source revision:
  `bc4a206690c1856d3cfde8b291f626c45a712640`;
- target corpus revision: same;
- source version: `0.3`;
- TF version: `0.4.0`.

## Artifact identity

Reuse the optional `denominator_basis.artifact_identity` object introduced by
I-017.

For the new resource:

- locator:
  `shipped-build:alexsosn/TLHdig-TF@bc4a206690c1856d3cfde8b291f626c45a712640:tf/0.4.0+tf-provenance/0.4.0`;
- `sha256`:
  `d0160532d03b86069132681ba68e23d3039bcebb96eb5684507ce660ea3b1634`;
- `materialized_sha256`:
  `fb447193b4f24a753154fbfdd4105cb855953af483b1160984435cf3f6422e6c`.

Here `sha256` is the BUILD-MANIFEST complete output-tree digest with the
`sha256:` algorithm prefix removed to fit the existing schema.
`materialized_sha256` is the module-qualified deterministic digest over both
the core and optional provenance TF files.

Committed research evidence additionally pins:

- BUILD-MANIFEST SHA-256
  `56e47a19b61293f0cec23ba12d884bef3d1e072a87c9acdd9c609bb190f7a6f4`;
- build code commit
  `fb5d93b5d112b77da756893c5561f99c05617c7b`;
- code digest
  `sha256:d8337017e18d9d906521e7c1c4d6fb7c6274b607d9b8118ff9c5cd64c459d403`;
- core TF digest
  `bb946e21f56249738c6b71fe50adbb588c7233d97ebb928a0b3ea83b46650fd6`;
- provenance TF digest
  `f66b1e7c4dd67670d0cc1a0094d8bed95b200740d80eca168ad692601a9e685d`.

The manifest denominator-basis source is
`docs/research/data/generated/i019/tlhdig-0.4.0.json`.

## Coverage schema extension for valued edges

I-019 is the first production denominator that includes bounded
`edge_value` items. The I-016 denominator-basis schema currently records only
`bounded_node_features`.

Add optional:

`denominator_basis.bounded_edge_features`

with the same closed set-like string-array contract as
`bounded_node_features`.

Rules:

1. the field is optional, so all historical/I-017/I-018 manifests remain
   valid;
2. when present it is included in `coverage_denominator_projection()`;
3. when absent it is omitted from the projection, preserving every existing
   denominator digest exactly;
4. the new TLHdig manifest contains exactly:
   `["joined", "witness_resolution"]`;
5. this is schema metadata only; `edge_value` item identities remain the
   authoritative denominator members.

Add regressions proving all existing packaged manifest digests remain
unchanged after the optional schema extension.

## Denominator policy input

Add:

`docs/research/data/i019/tlhdig-denominator-policy.json`.

It is repository/build input, not TFont runtime data. It contains no ontology
targets.

### Technical identities

```json
{
  "technical_node_features": ["anchor", "subcorpus"],
  "technical_warp_node_features": ["otype"],
  "technical_warp_edge_features": ["oslots"]
}
```

Each decision carries a stable I-019 source ID and reason.

### Bounded node values

The policy records exactly these 30 families and 101 values:

```json
{
  "type": [
    "reading", "signname", "numeral", "unknown", "ellipsis", "empty",
    "del", "laes", "ras", "add", "quot"
  ],
  "sgr": [0, 1],
  "agr": [0, 1],
  "det": [0, 1],
  "num": [0, 1],
  "missing": [1],
  "laes": [1],
  "ras": [1],
  "add": [1],
  "quot": [1],
  "materlect_anomalous": [1],
  "cu_unrendered": [1],
  "crossesline": [1],
  "nested": [1],
  "siglum_ambiguous": [1],
  "from_open_marker": [0, 1],
  "from_close_marker": [0, 1],
  "mrpsel_kind": [
    "analysis", "none", "unknown", "DEL", "AKK", "HURR", "HAT", "SUM", "LUW"
  ],
  "sel_group": ["all", "sg", "pl"],
  "parse_ok": [0, 1],
  "field4_kind": ["empty", "pos", "stemclass", "morph"],
  "cu_aligned": [0, 1, 2, 3, 4],
  "ruling": ["single", "double"],
  "kind": [
    "kor", "kor2", "kor1kf", "annot", "uebern", "format", "author", "kolon",
    "val", "trlst", "join", "merge", "aufheb", "aufloes", "korof", "koltaf",
    "kolfot", "kolfot2", "cth", "creation-date", "AOxml-creation"
  ],
  "orphan": ["none", "open", "close"],
  "fragment_kind": ["txtpubl", "invnr", "plain"],
  "siglum_source": ["attr", "element-text", "tail", "plain-text", "conflict"],
  "join_kind": [
    "direct", "indirect", "direct-multi", "indirect-multi",
    "uncertain", "malformed", "unknown"
  ],
  "join_encoding": ["xml", "textual"],
  "join_resolved": [0, 1]
}
```

The generated manifest's `bounded_node_features` is exactly those 30 feature
names in canonical order.

### Bounded edge values

The policy records exactly:

```json
{
  "joined": ["direct", "indirect"],
  "witness_resolution": ["unique", "ambiguous"]
}
```

The generated manifest's `bounded_edge_features` is exactly those two names
in canonical order.

Value item identity uses the same canonical JSON scalar encoding for node and
edge values. Examples: `node_value:parse_ok=0` and
`edge_value:joined="direct"`. Strings therefore retain JSON quotes in the
item ID; integers do not.

`selected` is a valued edge but remains open and must not produce
`edge_value` denominator items.

## Deterministic offline builder

Add:

`scripts/coverage/build_i019_tlhdig_current.py`.

Inputs:

- `docs/research/data/generated/i019/tlhdig-0.4.0.json`;
- `docs/research/data/i019/tlhdig-denominator-policy.json`.

The builder must not:

- access the network;
- import Text-Fabric;
- import TLHdig-TF;
- load or rebuild the corpus;
- inspect a live TLHdig checkout.

Algorithm:

1. validate exact research artifact identity against pinned constants;
2. require slot type `sign`;
3. require exactly 17 node types, 120 core non-warp node features, two optional
   provenance node features and 14 non-warp edges;
4. require optional provenance features exactly `src_span` and `srcxml`;
5. require warp exclusions exactly `otype` / `oslots`;
6. validate both technical non-warp features are materialized;
7. enumerate all node types;
8. enumerate all core + provenance node features except technical non-warp
   features;
9. enumerate all 14 non-warp edge features;
10. enumerate `node_value` items only from the 30 explicit policy families;
11. enumerate `edge_value` items only from the two explicit policy families;
12. fail if any bounded family does not refer to a semantic materialized
    feature/edge;
13. fail on duplicate bounded values;
14. fail if semantic and technical identities overlap;
15. fail if any materialized core/provenance feature or edge is omitted from
    accounting;
16. set semantic research/production accounting to null;
17. create four production-authority technical exclusions with reviewed source
    IDs;
18. set `accounting_gaps=[]`;
19. compute and validate the normal denominator digest.

Expected arithmetic:

- 17 node types;
- 120 semantic node features;
- 14 semantic edges;
- 101 bounded node values;
- 4 bounded edge values;
- **256 semantic items**;
- **4 technical exclusions**.

Support write mode and `--check` byte-for-byte regeneration.

## Optional provenance module boundary

The two optional provenance node features are semantic denominator members:

- `node_feature:src_span`;
- `node_feature:srcxml`.

They must not be omitted because the ordinary core loader does not eagerly load
that module.

The denominator does not introduce separate module/container items. Module
identity is retained in committed research evidence and bound into the combined
materialized artifact digest.

## Explicit non-expansions

The builder must never infer bounded values from observed cardinality.

At minimum, adversarial tests prove no value items are produced for:

- `after`;
- `sep`;
- `pos`;
- `cu_method`;
- `lang`;
- `surface`;
- `project`;
- `join_reason`;
- valued edge `selected`.

The policy is the only source of value-family expansion.

## Historical-accounting boundary

Do not copy historical R-005/R-011 research or production accounting into the
new manifest.

The historical TLHdig manifest remains:

- 137 semantic items;
- denominator source revision
  `4309cf3318c682282c1480b233786362a3083471`;
- denominator digest
  `sha256:eaf2436a90a85b1e5a8e02b4ad1f7070554d73de084eee589938586eecad2f1d`.

It remains independently loadable and immutable.

## Package API

Reuse `load_packaged_coverage_manifest(resource_set, corpus_id)`.

Add and export:

`P004_TLHDIG_0_4_0_RESOURCE = "p004-tlhdig-0.4.0-bc4a206-v1"`.

No registry/discovery work belongs in this ticket.

## TDD RED

Before production implementation, create `tests/i019/` on a dedicated
implementation branch.

Tests-only RED requires:

1. the current TLHdig resource constant exists and is exported;
2. the new packaged resource exists and validates;
3. report values are exactly:
   - semantic_items = 256;
   - technical_exclusions = 4;
   - production_reviewed_items = 0;
   - production_unreviewed_items = 256;
   - research_reviewed_items = 0;
   - both outside-denominator counts = 0;
   - scope_quality = `machine-exhaustive`;
   - freshness = `current`;
   - bounded_scope_complete = false;
   - corpus_wide_completion_claim_eligible = false;
4. exact 17 node types are present;
5. exact technical identities are
   `otype`, `oslots`, `anchor`, `subcorpus`;
6. `src_span` and `srcxml` are semantic node-feature items;
7. exactly 101 policy-approved node values and four policy-approved edge
   values are present;
8. no `edge_value:selected=...` is present;
9. representative open feature families have no value items;
10. `bounded_node_features` contains exactly 30 families and
    `bounded_edge_features` exactly `joined`, `witness_resolution`;
11. artifact locator and both digests match research evidence;
12. all semantic items start research/production null;
13. historical 137-item resource/digest remains unchanged;
14. offline builder and policy exist.

Record an actual failing exact head before production changes.

## GREEN and adversarial regressions

After RED is observed, implement the minimum contract and add tests for:

- optional `bounded_edge_features` schema acceptance;
- malformed/non-list/duplicate bounded-edge metadata rejection;
- changing bounded-edge metadata changes denominator digest;
- omission of the optional field leaves every existing packaged digest
  unchanged;
- technical policy referencing a non-materialized node feature fails;
- a bounded node family reclassified technical fails;
- a bounded edge family referencing a non-materialized/non-semantic edge
  fails;
- duplicate bounded node or edge values fail;
- missing/extra core node-feature accounting fails;
- missing/extra provenance-feature accounting fails;
- missing/extra edge accounting fails;
- node-type drift fails the fixed 256-item contract;
- changing artifact/output or combined TF identity fails exact evidence
  pinning;
- open-domain observation/cardinality data cannot create denominator values;
- `selected` remains open despite being a valued edge;
- historical 137-item manifest and digest remain unchanged;
- I-017 and I-018 packaged manifests retain their exact current digests;
- builder source has no network, Text-Fabric or TLHdig import/acquisition;
- wheel includes historical and current TLHdig resources.

## Files allowed in implementation

Expected:

- `src/tfont/schemas/coverage-manifest.schema.json`;
- `src/tfont/coverage.py` — optional bounded-edge projection + resource
  constant only;
- `src/tfont/__init__.py` — export only;
- `docs/research/data/i019/tlhdig-denominator-policy.json`;
- `scripts/coverage/build_i019_tlhdig_current.py`;
- `src/tfont/resources/coverage/p004-tlhdig-0.4.0-bc4a206-v1/tlhdig.json`;
- `tests/i019/**`;
- `.github/workflows/i019-tlhdig-coverage.yml`.

No ontology resources, production mappings, resolver/execution behavior,
historical coverage resources, or TLHdig-TF source/data may change.

Any need outside these files requires a plan amendment.

## Focused CI

Add exact-head Python 3.10/3.12 CI that:

1. installs ontoTF;
2. runs `tests/i019`;
3. runs the I-019 builder with `--check`;
4. builds a wheel;
5. verifies historical/current TLHdig coverage resources and the coverage
   schema are packaged.

The authoritative Full repository suite must pass on the exact final head.

The networked/shipped-artifact research workflow remains a separate
reproducibility gate. Production generation consumes committed evidence only.

## Final logically-independent review

Fresh review of the implementation exact head must independently challenge:

- 256/4 arithmetic;
- complete accounting of all 122 core+provenance node features;
- inclusion of optional provenance semantics;
- the two technical non-warp decisions;
- all 30 bounded node families / 101 values;
- the two bounded edge families / four values;
- exclusion of `selected` and other open domains;
- artifact/output-tree and combined TF digest binding;
- historical 137-item baseline immutability;
- preservation of I-017/I-018 digests after schema extension;
- absence of historical authority transfer;
- deterministic offline regeneration;
- wheel resource availability.

Merge only with the reviewed exact head SHA. After merge, read the new manifest
from `main`, reproduce the 256/4 report, and close #208 only after readback.
