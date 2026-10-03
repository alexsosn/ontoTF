# I-024 research — lossless valued TF edge-path execution

Issue: #249
Parent: P-004 #202, Workstream B
Dependency: I-023 #244 / implementation PR #251
Edge-value predicate follow-up: I-025 #253

## Status and scope

Research only. This branch is based directly on current main after the
reviewed I-023 implementation merged, so the probe inspects the production
typed unvalued edge-path contract. It does not change production schemas, IR,
resolver or execution behavior.

Pinned evidence is Text-Fabric revision 0c45c386916cb52be84098796ec27ce97e5bf9fc,
TLHdig-TF revision 0261d2d46b3419a1f907e231a03f749d133cfb5e
(corpus 0.4.0), BHSA revision
4db00e2157915495e1a4d3d57e41223df24775da, and the committed ontoTF R-005
BHSA inventory.

The reproducible probe is
scripts/research/i024_valued_edge_execution_reconciliation.py. Frozen evidence
is docs/research/data/generated/i024/valued-edge-reconciliation.json.

## Real valued-edge semantics

The three TLHdig valued edges show that valued is a storage property, not one
semantic role.

selected maps word to analysis. TLHdig emits one valued edge per selected
morphological analysis. The value is the source mrp0sel selector token,
preserved verbatim. Real examples include 1, 2a, and 1bR 1bS. Multiple
selected analyses are possible; multiple selector tokens that point to the
same analysis are retained in source order in one edge value because TF
permits one value per ordered node pair. The edge relation carries the fact
that an analysis was selected; the stored token is source evidence for how
that choice was encoded. I-024 therefore classifies this value as
source-evidence.

witness_resolution maps line to fragment and records unique or ambiguous
resolution of a block-local manuscript siglum. The value changes how the
relation should be understood and is useful to textological queries. It is a
semantic-qualifier.

joined maps fragment to fragment with direct or indirect. It is also a
semantic-qualifier, but the edge has a provenance boundary: orientation is
source apparatus order, not a physical directional assertion; no reverse or
transitive relation is inferred; authoritative statement multiplicity remains
on joinstmt nodes. The joined edge is a convenience projection for confident
binary statements, not a lossless replacement for the join ledger.

## Technical valued-edge control

BHSA omap@2017-2021 and omap@c-2021 are valued integer version-mapping edges.
Upstream documentation says the value carries information about how good the
node correspondence is. These are technical version-mapping mechanics, not
authority to project an integer score into a semantic ontology.

They justify a third value role, technical, and are a negative control against
treating every valued edge value as a semantic category.

## Text-Fabric value mechanics

Pinned Text-Fabric establishes that EdgeFeature.f and EdgeFeature.t return
(neighbor, value) pairs when doValues is true, EdgeFeature exposes doValues
and feature metadata, and feature value types are str or int.

An integer-valued edge row with an empty value can decode to None. An empty
string is representable as an actual string value. Generic lossless execution
therefore cannot use None as the only unvalued marker and cannot collapse an
empty string to absence. Evidence needs an explicit value_present flag beside
the native value.

For I-024, value_type=str accepts exact Python str including the empty string.
value_type=int accepts exact Python int and rejects bool. None from an
explicitly valued TF edge is preserved as value_present=false and value=None.
Any other returned value shape or type fails closed.

## Source and IR contract

I-023 step identity is edge + direction + result_node_type + valued=false.

I-024 should generalize valued to a boolean. For valued=false, the existing
four-field shape remains unchanged and value_type/value_role are forbidden.
For valued=true, require exactly two additional reviewed fields:

edge: witness_resolution
direction: outgoing
result_node_type: fragment
valued: true
value_type: str
value_role: semantic-qualifier

Recommended value_type values are str and int.
Recommended value_role values are semantic-qualifier, source-evidence, and
technical.

These roles describe how the native value participates in reviewed source
semantics. They do not assign ontology meaning to a literal.

The new fields are part of native binding identity and mapping/projection
semantic digests. No current packaged production binding is structural, so
existing production digests do not change.

The mapping schema can remain v2 and existing binding/digest algorithms can
remain unchanged because their canonical JSON projections already include
nested step fields. EdgeStepIR gains optional/defaulted value_type and
value_role fields so old unvalued compiled fixtures remain distinguishable.

## No value predicates in I-024

Real TLHdig data makes exact filters useful: joined=direct,
witness_resolution=ambiguous, and similar cases. But a value predicate raises
a separate authority question: what reviewed dependency proves a native edge
value or value domain is available and authorized?

Current dependency-contract v1 path-present attests only ordered edge +
direction APIs. It deliberately does not assert value domains. Treating a
literal in a binding as sufficient runtime authority would be weaker than the
existing node-feature value contracts.

I-024 therefore preserves every native edge value but does not filter on it.
I-025 #253 owns exact edge-value predicates, closed/observed domains, and any
dependency-contract extension. Semantic approximation remains the existing
mapping-assessment/loss mechanism and never fuzzily approximates a native edge
literal.

Dependency-contract version 1 remains unchanged in I-024.

## Lossless result evidence

Returning final node IDs while dropping (node, value) pairs is not acceptable.
Enumerating every complete multi-step path can expand combinatorially under
fan-out and fan-in.

Use a deterministic layered edge-evidence DAG. For any edge path containing at
least one valued step, record canonical start nodes, one evidence layer per
reviewed step, every accepted native edge observation in that layer, and final
nodes.

Each observation records step index, native source node, native target node,
value_present, and native value when present. The reviewed plan already
carries edge name, traversal direction, result_node_type, valued state,
value_type and value_role.

Evidence retains native edge orientation even for incoming traversal. For an
incoming step, the returned neighbor is the native source and the current
frontier node is the native target.

All step layers are recorded when any step is valued, including unvalued
steps. Otherwise a valued observation separated from start/final nodes by an
unvalued traversal would not be enough to reconstruct execution
justification.

This graph representation preserves every traversed native pair without
materializing the Cartesian product of complete paths.

## Evidence identity and public result shape

Introduce a nested evidence contract tfont-edge-path-evidence-v1 and a
JCS/SHA-256 evidence fingerprint over the **fresh execution plan fingerprint**,
native binding identity, start nodes, ordered layers, ordered native edge
observations, and final nodes.

Binding only to native binding identity is insufficient: the same native
binding shape can occur in distinct corpus/profile/parent variants, and node
integers are corpus-local. Every current semantic, authority, identity and
identifier native plan already exposes a deterministic `plan_fingerprint`
that binds corpus ID, variant/profile identity, observed parent state,
prerequisite state and reviewed mapping/reference authority. Edge-path evidence
must carry that exact plan fingerprint and include it in its own fingerprint.
For conjunction, each constituent evidence object binds the corresponding
constituent plan fingerprint.

Current public corpus-execution records return nodes, plan and runtime report.
They have no place for path evidence. The smallest additive public change is an
optional edge_path_evidence field on single-plan corpus execution records and
a constituent_edge_path_evidence tuple aligned with plans on conjunction
records.

Existing value-predicate/membership execution keeps the default empty
evidence. Pure I-023 unvalued edge paths may also keep it empty; if any step
is valued, evidence is mandatory.

Because the field is additive and the nested evidence has its own versioned
contract, I-024 need not change outer exact/approximate/reference execution
contract strings. The plan gate must explicitly test positional/default
compatibility of public dataclasses before accepting this.

For conjunction, each constituent keeps its own complete evidence and
final-node set; the existing node intersection remains the conjunction result.
Evidence is not flattened across semantic atoms.

## Runtime trust boundary

A valued step is revalidated after fresh prerequisite/resolver evaluation:
the edge is loaded; requested f/t is callable; doValues is true; metadata
declares the reviewed value_type; every return member is exactly a two-item
(node, value) pair; node normalization/domain checks remain I-023-safe; value
type and presence are validated as above.

An unvalued step in the same path still requires doValues=false and plain
nodes. Full-path preflight remains required before traversal so an invalid
later step cannot hide behind an earlier empty frontier.

No corpus autoload, network access, oslots inference, or Text-Fabric runtime
dependency is introduced.

## Versioning consequences

Recommended I-024 boundary:
- mapping schema version stays v2;
- dependency contract stays v1;
- mapping/projection digest algorithms stay unchanged;
- native binding identity algorithm stays unchanged;
- resolver plan fingerprint algorithms stay unchanged;
- outer execution contract strings stay unchanged;
- new nested edge-path evidence contract/fingerprint starts at v1 and binds the fresh execution plan fingerprint.

The new valued step fields are semantic identity, so future valued mappings
naturally produce different digests from otherwise identical unvalued
bindings. Current packaged production resources have no structural execution
bindings, so there is no shipped digest migration.

## Plan handoff

The reviewed plan should decompose conditional valued-step schema/IR,
defensive value_type/value_role validation, evidence dataclasses and
fingerprint, mixed valued/unvalued traversal with native orientation, and
evidence propagation through exact/approximate semantic,
authority/identity/identifier and conjunction results.

Real-data controls must cover all three TLHdig value roles plus BHSA omap as a
technical negative control. Production mapping digests and dependency-contract
v1 remain frozen. Any edge-value filter field is rejected in I-024.

Tests must cover None, empty string, integer/bool distinction, incoming valued
traversal, fan-in/fan-out, mixed paths, empty post-traversal frontiers,
malformed pair shapes, metadata/type drift, deterministic evidence
fingerprints, the same binding/node trace under two distinct plan fingerprints,
rejection of evidence replay under the wrong plan, conjunction evidence
alignment, and forged IR/evidence attempts.
