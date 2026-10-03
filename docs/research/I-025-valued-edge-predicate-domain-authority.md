# I-025 research — exact valued-edge predicates and domain authority

Issue: #253  
Parent: P-004 #202, Workstream B  
Prerequisite: merged I-024 #249 / PR #257

## Status and scope

Research gate only. No production schema, IR, resolver, runtime, packaged mapping,
or dependency behavior is changed by this branch.

The study is pinned to:

- ontoTF main after I-024: `a2c3118c6532cf9df2aa95af7ca65a5e9bd5b480`;
- Text-Fabric: `0c45c386916cb52be84098796ec27ce97e5bf9fc`;
- TLHdig-TF: `0261d2d46b3419a1f907e231a03f749d133cfb5e`
  (TF artifact 0.4.0);
- BHSA: `4db00e2157915495e1a4d3d57e41223df24775da`;
- the committed R-005 BHSA inventory and I-024 reconciliation evidence.

The reproducible probe is
`scripts/research/i025_valued_edge_predicate_reconciliation.py`.
Frozen output is
`docs/research/data/generated/i025/valued-edge-predicate-reconciliation.json`.

## Decision

I-025 should productionize one deliberately narrow predicate:

> **exact finite-set membership on a reviewed valued edge step whose
> `value_role` is `semantic-qualifier`.**

The authored step should gain a non-empty `match_values` array. A singleton is
exact equality; multiple values are exact OR. No fuzzy matching, ordering,
range comparison, regex, coercion, or ontology inference is added.

The initial production slice should not expose matching on
`source-evidence` or `technical` values. Those values remain losslessly
available in I-024 evidence. This keeps selector/provenance tokens and technical
version-mapping scores from silently becoming semantic categories.

A new **dependency-contract v2** kind, `edge-value-domain`, is required.
Dependency-contract v1 cannot safely be stretched to cover edge values:
its `native-value-present` and `value-domain` assertions address
`node_type + node feature`, and its runtime observation enumerates
`F.<feature>.v(node)`. Edge values are attached to ordered source-target
pairs and require different runtime observation mechanics.

Existing v1 profiles remain valid. A profile that authorizes
`match_values` must use dependency contract v2 and a matching reviewed
`edge-value-domain` assertion.

## 1. Current post-I-024 contract

I-024 now gives each valued step:

- native `edge`;
- traversal `direction`;
- reviewed `result_node_type`;
- exact `valued=true`;
- `value_type=str|int`;
- `value_role=semantic-qualifier|source-evidence|technical`.

Runtime validates loaded `doValues`, `meta.valueType`, exact pair shape,
native value type, native source/target orientation, and result-node domain.
Accepted values are retained in deterministic plan-bound
`tfont-edge-path-evidence-v1` evidence.

What it intentionally lacks is a value selection field and a dependency that
authorizes an edge-value domain.

Current dependency-contract v1 contains:

- `component-present`;
- `node-type-present`;
- `feature-present`;
- `edge-present`;
- `path-present`;
- `native-value-present`;
- `value-domain`;
- `extent-interpretation`.

The two value kinds are node-feature contracts. Their assertions include
`node_type` and `feature`, not an edge and its source/target domains.
`LoadedTFObservation.values()` correspondingly reads already-loaded node
features through `F`.

Therefore aliasing an edge to the existing `feature` field would make
runtime authority claim a different native object than the one execution uses.

## 2. Real positive controls

### 2.1 TLHdig `witness_resolution`

This is a valued `line -> fragment` edge with exact string values
`unique | ambiguous`.

The corpus documentation and converter metadata both define that closed domain.
The value changes the interpretation of the witness relation and was classified
by I-024 as `semantic-qualifier`.

A concrete exact predicate is:

```text
witness_resolution = ambiguous
```

This is appropriate for the initial I-025 slice.

### 2.2 TLHdig `joined`

This is a valued `fragment -> fragment` convenience edge with exact string
values `direct | indirect`. Converter source fixes the confident value set,
while the documentation explicitly states that orientation is source apparatus
order rather than physical direction.

A concrete exact predicate is:

```text
joined = direct
```

The filter must not reinterpret edge direction. Native orientation and the
qualifier are independent dimensions.

## 3. Negative controls

### 3.1 TLHdig `selected`

`selected` maps a word to a selected analysis, with a verbatim selector token
such as `1`, `2a`, or `1bR 1bS`. It is source evidence for editorial
selection mechanics and has an open token domain.

I-024 correctly classifies it as `source-evidence`.

The initial I-025 semantic-predicate slice should not allow
`match_values` on this role. Lossless evidence remains available to callers
that need to inspect the selector token.

### 3.2 BHSA `omap@...`

BHSA version-mapping edges are integer-valued and document correspondence
quality. The R-005 inventory shows that:

- `omap@2017-2021` has 74 observed non-missing values and is classified
  `open_or_large_observed_domain`;
- `omap@c-2021` has 34 observed non-missing values but the inventory
  explicitly warns that a small observed domain is not automatically a
  categorical/closed semantic domain;
- both contain very large counts of empty integer edge values represented by
  TF as missing `None`.

These are I-024 `technical` values. Observing a finite set of integers does
not create semantic authority to query those integers as ontology categories.

## 4. Predicate source contract

Recommended valued step:

```json
{
  "edge": "witness_resolution",
  "direction": "outgoing",
  "result_node_type": "fragment",
  "valued": true,
  "value_type": "str",
  "value_role": "semantic-qualifier",
  "match_values": ["ambiguous"]
}
```

Rules:

- `match_values` is allowed only when `valued=true`;
- the initial slice requires `value_role=semantic-qualifier`;
- it is a non-empty unique array;
- every member is exact `str` when `value_type=str`, exact `int` when
  `value_type=int`;
- `bool` is not an integer value;
- integers must fit TFont's portable JCS safe-integer domain;
- `None` is not a matchable value;
- `""` is a real string value and may be matched if it is explicitly
  reviewed in the authorized closed domain;
- order is semantically irrelevant;
- one member means equality; multiple members mean exact membership/OR.

Do not add a second scalar `match_value` field. One finite-set field avoids
two equivalent authored forms and reuses the same execution semantics for
singleton and multi-value filters.

## 5. Canonicalization and identity

`match_values` is set-like and must be canonicalized by JCS bytes.

Two current identity paths need an additive recognition of the new field:

1. `mapping_semantic_digest_v2` recursively sorts only its registered
   set-like list fields;
2. `native_binding_identity()` currently normalizes top-level
   `values` but does not know nested step-level sets.

Production I-025 must add `match_values` to semantic-digest set-like
normalization and normalize it inside each authored step before computing native
binding identity.

No algorithm token needs to change because this is an additive field that is
currently forbidden by the closed schema; no previously valid mapping can
contain it. Existing valid mapping bytes and digests therefore remain unchanged.

`EdgeStepIR` should append one defaulted field:

```python
match_values: tuple[str | int, ...] | None = None
```

Old six-field I-024 positional construction remains valid.

## 6. Edge-value domain authority

Recommended dependency-contract v2 kind:

```json
{
  "dependency_id": "dep:tlhdig:witness-resolution:domain",
  "component_id": "tlhdig-tf",
  "kind": "edge-value-domain",
  "assertion": {
    "edge": "witness_resolution",
    "source_node_type": "line",
    "target_node_type": "fragment",
    "value_type": "str",
    "value_role": "semantic-qualifier",
    "values": ["ambiguous", "unique"],
    "domain_semantics": "closed-reviewed"
  },
  "evidence": [
    {
      "evidence_id": "...",
      "content_digest": "..."
    }
  ]
}
```

The assertion uses **native edge orientation**. It does not include traversal
direction. `value_role` is reviewed semantic provenance: runtime must not try
to infer or rediscover it from the edge name, literal values, or TF metadata.
Runtime observation verifies the loaded mechanical edge/value domain; the
reviewed dependency and mapping/review binding supply the role authority.

For an outgoing step, the current frontier type is the native source and
`result_node_type` is the native target. For an incoming step those roles are
reversed. This lets one reviewed domain authorize either traversal direction,
while the existing `path-present` dependency continues to authorize the
actual ordered edge+direction sequence.

The assertion must bind:

- edge name;
- native source node type;
- native target node type;
- `value_type`;
- `value_role`;
- a non-empty unique allowed `values` set;
- `domain_semantics=closed-reviewed`.

Closed-reviewed edge domains require evidence exactly as closed-reviewed
node-feature value domains do.

Every authored `match_values` member must be contained in one matching
reviewed `edge-value-domain` dependency. Do not combine several partial domain
claims to manufacture authority for one predicate: one dependency must bind the
same edge, native source/target types, value type, value role, and contain the
whole requested match set.

No `observed` edge domain is sufficient to authorize `match_values` in the
initial production slice. Observation is runtime compatibility evidence, not
scholarly/domain authority.

## 7. Dependency contract versioning

Adding `edge-value-domain` changes the addressable native object and evaluator
semantics of the dependency language. It should therefore be dependency
contract **v2**, rather than silently expanding v1.

The profile schema can remain schema version 2 while permitting dependency
contract 1 or 2. Version-aware validation must enforce:

- v1 accepts exactly the existing dependency kinds;
- v2 accepts the existing kinds plus `edge-value-domain`;
- a mapping step with `match_values` requires a matching v2
  `edge-value-domain`;
- existing v1 profile releases continue to compile and execute unchanged.

The existing profile-release fingerprint already includes
`dependency_contract_version` and canonical dependency records. The
fingerprint algorithm can remain unchanged: a v2 release naturally has a
different release identity.

Runtime prerequisite validation currently rejects any version other than 1.
I-025 production must make that check version-aware rather than weakening it.

## 8. Loaded runtime observation

Text-Fabric's public `EdgeFeature.items()` returns the already-loaded edge
mapping; `f/t` return node-value pairs for valued features. The pinned API
therefore supports complete loaded-domain inspection without loading another
feature or importing corpus-specific code.

Add a narrow runtime observation method conceptually equivalent to:

```text
edge_values(component_id, edge, source_node_type, target_node_type)
  -> state, declared_value_type, present_values, missing_count
```

It must:

1. require the edge to already be present in loaded `Eall()`;
2. require exact `doValues=true`;
3. require exact metadata `valueType`;
4. iterate the public loaded edge items;
5. validate source/target node IDs and use loaded `otype` to retain only the
   reviewed native source/target domain;
6. validate every edge value with the same I-024 `str|int` rules;
7. collect exact present values;
8. count integer `None` values as missing observations, not as a domain member;
9. never autoload a feature, access the network, infer from `oslots`, or use
   source-format sidecars.

Text-Fabric also exposes `EdgeFeature.freqList(nodeTypesFrom,
nodeTypesTo)`, and the pinned implementation performs native source/target type
filtering over the same loaded edge data. It is useful corroborating API
evidence, but it should not be the normative trust-boundary primitive for
I-025: it aggregates values/frequencies and therefore gives less control over
exact raw-shape validation and explicit missing-value accounting than
`items()`.

Complete domain observation is O(edge-domain size). Cache the validated
observation inside one `LoadedTFObservation` instance, keyed by component,
edge, source type and target type, so several dependencies/resolutions in the
same loaded runtime evaluation do not repeatedly rescan a large valued edge.
The cache is an in-memory optimization over already-loaded data, not corpus
autoload or persisted authority.

For `closed-reviewed`, runtime compatibility passes when every **present**
observed value in that native edge/domain is contained in the reviewed set.
A reviewed allowed value need not occur in the current parent snapshot; querying
it is a valid query with an empty result.

Unexpected observed values fail compatibility. Malformed or unreadable loaded
data yields unknown/fail-closed behavior according to the existing prerequisite
model.

## 9. Execution semantics

Filtering belongs inside the shared I-024 path executor so exact/approximate,
authority, identity, identifier, and conjunction surfaces cannot diverge.

For a valued step with `match_values`, each raw native pair should be handled
in this order:

1. validate pair shape;
2. validate neighbor node;
3. validate native value type/presence;
4. inspect loaded `otype` and reject off-domain neighbors from the frontier;
5. compare the exact native value against canonical `match_values`;
6. for accepted neighbors, enforce evidence-node JCS bounds;
7. append accepted frontier/evidence observations.

Malformed edge values on off-domain neighbors still fail before filtering, as
I-024 requires. A well-formed off-domain neighbor is not rejected merely for
evidence-integer bounds because it never enters evidence.

A non-matching but otherwise valid in-domain pair is simply excluded from the
next frontier and evidence. The existing evidence shape is sufficient:
accepted observations already carry the exact native value that justified the
result. A separate predicate-evidence contract is unnecessary.

When a filter empties the frontier, the result is a normal valid empty result
with the existing layered evidence rules.

## 10. Missing values and empty strings

The pinned TF integer representation can decode an empty edge value as `None`.
I-024 records that as `value_present=false`.

I-025 should **not** overload `None` as a predicate literal. Querying absence
would require an explicit presence/absence predicate with separate semantics and
authority. It is outside the initial slice.

An empty string is different: for `value_type=str`, `""` is an actual
present native value. It can be selected if the closed-reviewed dependency
explicitly authorizes it.

## 11. Exact vs approximate semantic execution

Native edge-value matching remains exact on every resolver surface.

An approximate ontology mapping may still execute the same exact native
`match_values` predicate while separately reporting the already-reviewed
mapping loss. No edge literal is fuzzily compared, broadened, narrowed, or
substituted.

This preserves the separation established by I-020 and I-024:

```text
native selector precision != ontology mapping assessment
```

## 12. Conjunction and reference execution

The I-024 shared path executor is already reused by semantic, authority,
identity, identifier, and conjunction execution. I-025 should extend that
single path mechanism rather than add a second filtered traversal.

Conjunction continues to intersect only each constituent's filtered final node
set. Each constituent retains its own plan-bound path evidence. Reference
execution uses the same exact filter and evidence rules.

## 13. Versioning recommendation

Recommended production boundary:

- mapping schema stays v2;
- profile schema stays v2;
- dependency contract adds v2 while v1 remains accepted;
- mapping semantic algorithm token stays unchanged;
- native-binding identity algorithm token stays unchanged;
- resolver plan fingerprint algorithms stay unchanged;
- outer execution contracts stay unchanged;
- I-024 edge-path evidence contract stays v1;
- `match_values` becomes part of binding/digest/plan identity through existing
  projections plus explicit set normalization;
- no packaged production mapping needs migration merely to keep working.

## 14. RED gate for production work

The later tests-only RED head should cover at minimum:

1. singleton and multi-value `match_values`;
2. canonical order-insensitivity and duplicate rejection;
3. str/int exact typing, bool rejection, safe-JCS integer bounds;
4. `None` not matchable and `""` matchable only as reviewed str;
5. source schema rejection on unvalued, source-evidence, and technical steps;
6. defensive IR/resolver rejection of forged predicate tuples/types;
7. dependency v1 remains valid for existing profiles;
8. v1 cannot authorize edge-value predicates;
9. v2 `edge-value-domain` exact source/target/value-type/value-role matching;
10. incoming traversal uses reversed current/result domains but the same native
    domain assertion;
11. closed-reviewed evidence is mandatory;
12. observed unexpected domain value fails runtime compatibility;
13. reviewed-but-currently-absent value is compatible and returns empty;
14. integer missing `None` is excluded from the domain and counted separately;
15. malformed loaded pair/value data remains fail-closed;
16. filter occurs after result-node-domain validation;
17. I-024 evidence contains only accepted matching observations;
18. mixed valued/unvalued paths and empty trailing layers remain reconstructible;
19. exact and approximate semantic surfaces use identical native matching;
20. authority/identity/identifier use identical native matching;
21. exact/approximate conjunction preserve plan-aligned evidence;
22. all existing I-023/I-024 unfiltered paths remain byte/behavior compatible;
23. full v1 packaged profile/runtime regression;
24. repeated edge-domain dependencies reuse one loaded-observation scan;
25. no Text-Fabric runtime dependency/autoload/network regression.

## Plan handoff

The production plan should decompose:

1. dependency-contract v2 schema/validation/IR/runtime observation;
2. conditional step-level `match_values` schema + canonicalization + IR;
3. mapping dependency-authority validation using native edge orientation;
4. exact filtering in the shared I-024 path executor;
5. focused RED/GREEN tests and reproducible real-data controls;
6. full exact-head regression and fresh logically-independent adversarial review.

Any attempt to reuse v1 node-feature `value-domain`, fuzzily match edge
literals, infer a closed domain from observed values, or enable initial
source-evidence/technical predicates should be treated as a plan deviation and
re-reviewed before production implementation.
