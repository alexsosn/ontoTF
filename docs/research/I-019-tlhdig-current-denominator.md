# I-019 research — current TLHdig-TF semantic denominator

Issue: #208  
Parent: P-004 #202, Workstream A  
Status: research complete; ready for independently reviewed plan

## Question

What is the current reproducible TLHdig-TF semantic denominator, given that the
historical R-005/R-011 manifest describes commit
`4309cf3318c682282c1480b233786362a3083471` and the shipped 0.4.0 artifact has
changed materially since then?

The current denominator can be made machine-exhaustive for the complete shipped
Text-Fabric 0.4.0 schema: the default core module **and** its separately shipped
optional provenance module. The historical 137-item denominator must remain
immutable.

## Authoritative shipped artifact

The evidence boundary is the artifact shipped at TLHdig-TF repository revision:

`bc4a206690c1856d3cfde8b291f626c45a712640`.

The artifact's own `tf/0.4.0/BUILD-MANIFEST.json` binds the build to:

- source version: `0.3`;
- TF version: `0.4.0`;
- build code commit:
  `fb5d93b5d112b77da756893c5561f99c05617c7b`;
- code digest algorithm: `tlhdig-current-code-v1`;
- code digest:
  `sha256:d8337017e18d9d906521e7c1c4d6fb7c6274b607d9b8118ff9c5cd64c459d403`;
- output-tree algorithm: `tlhdig-current-tree-v2`;
- complete output-tree digest:
  `sha256:d0160532d03b86069132681ba68e23d3039bcebb96eb5684507ce660ea3b1634`;
- BUILD-MANIFEST SHA-256:
  `56e47a19b61293f0cec23ba12d884bef3d1e072a87c9acdd9c609bb190f7a6f4`.

The current research inventory independently hashes the materialized TF files:

- core `tf/0.4.0/*.tf`:
  `bb946e21f56249738c6b71fe50adbb588c7233d97ebb928a0b3ea83b46650fd6`;
- optional `tf-provenance/0.4.0/*.tf`:
  `f66b1e7c4dd67670d0cc1a0094d8bed95b200740d80eca168ad692601a9e685d`;
- module-qualified combined TF digest:
  `fb447193b4f24a753154fbfdd4105cb855953af483b1160984435cf3f6422e6c`.

The complete output-tree digest is broader than the combined TF digest and is
therefore appropriate as the artifact-level identity; the combined digest binds
exactly the materialized TF files that define this denominator.

## Why the optional provenance module is in scope

TLHdig-TF intentionally ships `srcxml.tf` and `src_span.tf` separately under
`tf-provenance/0.4.0`. They are not loaded by default, but the generated
feature reference documents them as researcher-facing node features of the
same 0.4.0 artifact:

- `srcxml`: verbatim source fragment of a sign with inline markers at their
  true offsets;
- `src_span`: byte range of the source element, with the documented repaired-
  stream caveat.

P-004's coverage denominator is an accounting boundary over supported native
semantics, not merely the default loader's eager feature set. Silently dropping
the optional provenance layer would make a corpus-wide completion claim
misleading.

I-019 therefore treats the two provenance features as ordinary semantic/native
node features while retaining their optional-module identity in the committed
research evidence.

## Machine schema census

The shipped artifact contains 17 node types:

- `analysis`;
- `cluster`;
- `colon`;
- `column`;
- `docgroup`;
- `document`;
- `edit`;
- `fragment`;
- `joinstmt`;
- `layout`;
- `lex`;
- `line`;
- `note`;
- `paragraph`;
- `sign` (slot type);
- `surface`;
- `word`.

The core module contains:

- 120 non-warp node features;
- 14 non-warp edge features;
- `otype` / `oslots` warp features;
- `otext` configuration.

The optional provenance module contributes two additional node features:
`src_span` and `srcxml`.

Three edges are valued:

- `joined`;
- `selected`;
- `witness_resolution`.

The current schema differs materially from the historical denominator. In
particular, `joinstmt` and the explicit manuscript-join graph now materialize,
while historical `directjoin` / `indirectjoin` feature identities no longer
describe the shipped schema.

The committed machine projection is
`docs/research/data/generated/i019/tlhdig-0.4.0.json`.

## Technical boundary

Four identities are technical rather than semantic denominator items:

1. `node_feature:otype` — Text-Fabric warp typing; node kinds are represented
   directly by `node_type:...` items.
2. `edge_feature:oslots` — Text-Fabric support/extent relation.
3. `node_feature:anchor` — artificial empty sign slot marker used so
   structurally real documents/lines with no readable sign survive Text-Fabric
   serialization.
4. `node_feature:subcorpus` — documented compatibility alias for
   `project`, retained for existing query/application compatibility rather
   than an independent source semantic.

The anchored structural nodes themselves remain semantic. Likewise derived
identifiers, alignment/confidence data, source-path provenance, manuscript
apparatus state, editorial ranges, cuneiform data and the optional provenance
features remain native semantic/research data even when they have no shared
ontology target.

## Closed node-value families

Observed cardinality is not closure evidence. I-019 expands node values only
where current converter code defines the complete value contract.

Thirty bounded node-feature families contribute **101 node-value items**:

- `type`: 11 values — six sign token kinds
  (`reading`, `signname`, `numeral`, `unknown`, `ellipsis`,
  `empty`) plus five bracket-cluster families
  (`del`, `laes`, `ras`, `add`, `quot`);
- always-materialized binary sign flags `sgr`, `agr`, `det`, `num`:
  `0 | 1`;
- sparse positive flags `missing`, `laes`, `ras`, `add`, `quot`,
  `materlect_anomalous`, `cu_unrendered`, `crossesline`, `nested`,
  `siglum_ambiguous`: value `1`;
- bracket-boundary flags `from_open_marker`, `from_close_marker`:
  `0 | 1`;
- `mrpsel_kind`:
  `analysis | none | unknown | DEL | AKK | HURR | HAT | SUM | LUW`;
- `sel_group`: `all | sg | pl`;
- `parse_ok`: `0 | 1`;
- `field4_kind`: `empty | pos | stemclass | morph`;
- `cu_aligned`: `0 | 1 | 2 | 3 | 4`.
  Level 4 is currently unobserved but remains an explicitly supported converter
  result for the numeral mechanism;
- `ruling`: `single | double`;
- `kind`: the 21 explicitly recognized editorial-event kinds in
  `_EDIT_KINDS`;
- `orphan`: `none | open | close`;
- `fragment_kind`: `txtpubl | invnr | plain`;
- `siglum_source`:
  `attr | element-text | tail | plain-text | conflict`;
- `join_kind`:
  `direct | indirect | direct-multi | indirect-multi | uncertain | malformed | unknown`;
- `join_encoding`: `xml | textual`;
- `join_resolved`: `0 | 1`.

Some listed values are valid code-defined states absent from the current corpus
instance (for example `cu_aligned=4`, `siglum_source=conflict`, and some
join kinds). They belong to the pinned 0.4.0 feature contract and are justified
by source semantics rather than inferred from observation.

## Closed valued-edge families

Two valued-edge families are bounded and contribute **4 edge-value items**:

- `joined`: `direct | indirect`;
- `witness_resolution`: `unique | ambiguous`.

`selected` is deliberately not expanded. Its values are source selector
tokens/combinations and form an open corpus-dependent domain.

## Explicit non-expansions

I-019 does not turn the following into value items merely because a current
artifact might show a small set:

- `after` — serialized token separation can preserve compound boundary state;
- `sep` — the morphology separator preserves source spacing/forms and is not
  a canonical finite scalar vocabulary;
- `pos` — atomic POS labels may be combined into compound values;
- `cu_method` — space-separated combinations of mechanisms;
- `lang`, `surface`, `project`, source paths and identifiers;
- `selected` valued-edge tokens;
- source/editorial strings and diagnostic fields such as `join_reason`.

An earlier experimental I-019 probe attempted to infer domains by treating raw
TF body lines as decoded values. That is invalid for general Text-Fabric
serialization/compression and was removed before the evidence freeze. The
final research workflow uses TF bodies only for the narrow `otype` census;
closed families are source-reviewed.

## Proposed current denominator

For the complete shipped TLHdig-TF 0.4.0 core + provenance schema:

- node types: 17;
- materialized node features: 122 (120 core + 2 provenance);
- technical non-warp node features: 2;
- **semantic node features: 120**;
- semantic non-warp edges: 14;
- source-proven bounded node values: 101;
- source-proven bounded edge values: 4;
- **semantic denominator: 256 items**;
- **technical exclusions: 4 items**.

The denominator is eligible for `scope_quality=machine-exhaustive` within this
explicit shipped-schema scope.

That claim does not mean every TLH source/XML concept has a TF representation,
that every native item has a shared ontology target, or that future converter
versions may not add schema. It means every currently shipped core/provenance
TF identity plus every explicitly reviewed closed value family is accounted.

## Reproducibility contract

The I-019 research workflow:

1. checks out the exact ontoTF research head;
2. sparse-checks out the exact TLHdig-TF shipped core and provenance modules at
   `bc4a206690c1856d3cfde8b291f626c45a712640`;
3. verifies the artifact's BUILD-MANIFEST code/output identities and the
   expected 137 core / 2 provenance TF-file census;
4. inventories feature headers and the `otype` census without importing
   Text-Fabric or loading the multi-million-node graph;
5. independently hashes core, provenance and combined materialized TF files;
6. projects the regenerated inventory into the compact committed evidence and
   requires exact equality.

TFont runtime does not acquire or build TLHdig.

## Plan handoff

The implementation plan should publish a new immutable coverage resource and
must not edit `p004-r011-baseline-v1/tlhdig.json`.

Required properties:

- bind repository revision, TF/source versions, BUILD-MANIFEST identity,
  complete output-tree digest and combined materialized TF digest;
- use the committed I-019 schema projection as the denominator basis;
- emit exactly 256 semantic items and 4 technical exclusions;
- include `srcxml` and `src_span` as semantic node features while preserving
  their optional-module provenance in research evidence;
- expand exactly the 101 node values and 4 edge values described above;
- keep all current semantic items research/production-unreviewed unless a new
  current-revision ontology review supplies authority;
- transfer no historical R-005/R-011 assessment by spelling alone;
- prove `anchor` and `subcorpus` remain technical and cannot overlap the
  semantic denominator;
- prove open domains such as `sep`, `pos`, `cu_method` and `selected`
  are not auto-expanded;
- deterministically regenerate the manifest offline from committed evidence
  plus an explicit reviewed policy;
- retain the historical 137-item manifest and denominator digest unchanged.

The plan must choose the immutable resource name and exact artifact locator.
