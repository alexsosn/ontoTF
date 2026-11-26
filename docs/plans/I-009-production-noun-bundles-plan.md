# I-009 plan: production OLiA Noun bundles for v0.1

**Issue:** #147  
**Release tracker:** #142  
**Research gate:** #148, merged as `3489db9ee82e49aacf8a181d77a08fc86f08136d`  
**Runtime prerequisite:** I-010/#152 merged as `6e12c1f0f9322855c8811851c87f0eca837ec9d6`  
**Phase:** plan only; no production resource implementation on this branch

## Goal

Ship the smallest release-grade package-resource slice that lets ontoTF load, validate, compile, resolve and execute one shared semantic request — OLiA `Noun` — against exact pinned BHSA, ETCBC Syriac and ExtraBiblical parents.

The semantic target is shared; the reviewed native plans are intentionally heterogeneous:

```text
BHSA          word.sp in {nmpr,subs}  value-set-predicate
Syriac        word.sp = subs           value-predicate
ExtraBiblical word.sp in {nmpr,subs}  value-set-predicate
```

This plan does not add a registry, downloader, materializer, generic query language, generic package manager, RDF runtime, live ontology dereference or R-018 multi-binding composition.

## 1. Production package layout

Use one canonical in-package resource tree under `src/ontotf/resources/`. Do not duplicate resources at repository root.

```text
src/ontotf/resources/
├── profiles/
│   ├── bhsa/0.1.0/
│   │   ├── profile.json
│   │   ├── parent/expected-components.json
│   │   ├── mappings/noun.json
│   │   └── evidence/native-pos.json
│   ├── syriac/0.1.0/
│   │   ├── profile.json
│   │   ├── parent/expected-components.json
│   │   ├── mappings/noun.json
│   │   └── evidence/
│   │       ├── native-pos.json
│   │       └── proper-noun-encoding.json
│   └── extrabiblical/0.1.0/
│       ├── profile.json
│       ├── parent/expected-components.json
│       ├── mappings/noun.json
│       └── evidence/
│           ├── native-pos-enum.json
│           └── feature-authority.json
└── ontologies/
    └── olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/
        ├── lock.json
        ├── noun-evidence.json
        ├── olia.owl
        ├── LICENSE.data
        └── ATTRIBUTION.txt
```

The profile files keep the existing logical child paths:

```text
parent_component_manifest = parent/expected-components.json
mapping_sources = [mappings/noun.json]
```

These strings remain relative to the profile version directory. The loader uses the same logical names as `SemanticArtifact.source_name` prefixes so diagnostics remain deterministic and package-relative.

### Package-data rules

Extend `[tool.setuptools.package-data].ontotf` without a recursive glob assumption. Keep existing `schemas/*.json` and add explicit patterns covering:

- `resources/profiles/*/*/*.json`
- `resources/profiles/*/*/parent/*.json`
- `resources/profiles/*/*/mappings/*.json`
- `resources/profiles/*/*/evidence/*.json`
- `resources/ontologies/*/*/*.json`
- `resources/ontologies/*/*/*.owl`
- `resources/ontologies/*/*/*.txt`
- `resources/ontologies/*/*/*.data`

Runtime lookup must use `importlib.resources.files("ontotf")` Traversables directly, following F-002. No conversion to repository-relative `Path` and no assumption that package resources are ordinary files.

## 2. Public loader surface

Add `src/ontotf/production_bundles.py` and re-export the three public names from `ontotf.__init__`:

```python
PRODUCTION_NOUN_CORPORA = ("bhsa", "syriac", "extrabiblical")

load_production_noun_bundle(corpus_id: str) -> SemanticSourceBundle

load_production_noun_bundles() -> tuple[SemanticSourceBundle, ...]
```

Rules:

- corpus IDs are exact, case-sensitive release IDs;
- unknown/non-string IDs fail deterministically with a narrow `ProductionBundleError(ValueError)` carrying the requested corpus ID;
- `load_production_noun_bundles()` returns the order above;
- the loader reads UTF-8 JSON with `loads_source(..., format="json")`, validates each artifact with existing `validate_source()`, and then constructs `SemanticArtifact` / `SemanticSourceBundle`;
- the loader does **not** call `validate_semantic_bundle()` implicitly: loading/structural validation and semantic validation remain separate existing layers;
- no network, corpus loading, ontology dereference or mutable cache;
- every bundle receives the same shared OLiA lock artifact and shared OLiA Noun evidence artifact by content, while corpus evidence stays corpus-specific;
- no generic registry/config discovery API is introduced in I-009.

## 3. Stable profile and component identities

Freeze:

| corpus | profile_id | profile_version | component_id |
|---|---|---|---|
| BHSA | `tfont-bhsa` | `0.1.0` | `bhsa-tf` |
| Syriac | `tfont-syriac` | `0.1.0` | `syriac-tf` |
| ExtraBiblical | `tfont-extrabiblical` | `0.1.0` | `extrabiblical-tf` |

Each profile declares:

```text
schema_version: 2
semantic_domains: [linguistic]
profile_catalog_version: 1
profiles: [linguistic]
capabilities: [linguistic.part-of-speech]
required_components: [<component-id>]
ontology_locks: [olia-reference-model]
dependency_contract_version: 1
minimum_tfont_runtime: 0.1.0
```

### Profile license boundary

Issue #153 is the release-governance blocker for the required profile `license` field. The repository currently has no top-level license, and fixture `CC-BY-4.0` must not be copied into production as if it were an actual project decision.

Implementation may temporarily use exact string `NOASSERTION` only to exercise RED/GREEN package mechanics. **I-009 cannot receive its final semantic review or merge with `NOASSERTION`, `LicenseRef-ontoTF-Unspecified`, fixture licensing, or any inferred corpus license in the profile license field.** #153 must be resolved first. This gate prevents a later license edit from silently changing a supposedly frozen profile/release identity.

## 4. Exact parent manifests

Each parent manifest contains exactly one semantically addressable runtime component, because this v0.1 slice executes only loaded TF `otype` and `sp` features.

Algorithm:

```text
tfont-parent-components-sha256-v1
```

Components:

| corpus | content digest | parent manifest digest |
|---|---|---|
| BHSA | `sha256:5178414e293a743fc98768abcab5b9cb268e14ad56fd2cfbac544ae2869d2e6f` | `sha256:cc2c65cd79b2cb7faf1a34b94feb3cc2d3291e7064cbec942c53b0e05f1b0837` |
| Syriac | `sha256:54a2596d5525f3afb34db0a89d5511e6b8471ce4a93fae4825b22f0945ab62ef` | `sha256:afb5a826b9ebe10cdd4ca23d96e00ee7bf677d06496cfcfcee6bb37d2ecff6c4` |
| ExtraBiblical | `sha256:d0ca9bdf90bfdefe19861c2c68e91071650ed511b8a79270490238b30274aee0` | `sha256:d39fe3f4848cadb14ae5ef453a5150ea6281b2874728566198d7de10d72bec4a` |

Every component uses:

```text
kind: tf-payload
identity_algorithm: tfont-tf-files-sha256-v1
```

Documentation, linksyr grammar, MQL source and ontology files are evidence/semantic dependencies, not runtime parent components for this slice.

## 5. Shared OLiA lock and snapshot

Use one physical lock resource, not one copy per corpus.

Freeze:

```text
lock_id: olia-reference-model
ontology_id: olia
support_tier: supported-profile
term_namespace: http://purl.org/olia/olia.owl#
release: snapshot-d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6
source_uri: https://raw.githubusercontent.com/acoli-repo/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/owl/core/olia.owl
source_revision: d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6
upstream_release_status: git-snapshot
content_digest: sha256:5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd
license: CC-BY-3.0
redistribution_policy: redistributable-with-attribution
snapshot_artifact: resources/ontologies/olia/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/olia.owl
terms_used: [http://purl.org/olia/olia.owl#Noun]
```

The exact `olia.owl` bytes are copied from the researched pinned revision. The installed resource must independently hash to the researched digest. Ship the upstream `LICENSE.data` text and a short ontoTF-authored `ATTRIBUTION.txt` naming OLiA, source repository/revision, exact snapshot path and CC BY 3.0 license URI.

Do not create an ontology-bundle/bridge artifact for this slice: one lock is sufficient and no cross-ontology bridge participates.

## 6. Evidence records

Use `normalized-record` evidence with `evidence_record_digest()`. This binds the exact immutable source URI/revision plus the reviewed scholarly statement without pretending that every semantic conclusion is a byte-for-byte external payload.

All source URIs are exact commit-pinned GitHub/raw URLs; no `example.org`, moving branch URLs or fixture revisions.

### Shared OLiA evidence

ID: `evidence:olia:noun-hierarchy`

Source: exact pinned `owl/core/olia.owl`.
Reviewed content must state only the facts verified by #148 CI:

- target = `http://purl.org/olia/olia.owl#Noun`;
- direct subclasses include `CommonNoun` and `ProperNoun`;
- exact snapshot digest;
- exact CC BY 3.0 license URI.

### BHSA evidence

ID: `evidence:bhsa:word-sp-noun-codes`

Source: exact pinned `docs/features/sp.md`.
Reviewed content:

```text
word/lex feature sp is part of speech;
subs = noun;
nmpr = proper noun;
production execution is intentionally word-scoped.
```

### Syriac evidence

Use two records rather than collapsing independent claims:

1. `evidence:syriac:word-sp-substantive` — pinned `ETCBC/linksyr` `word_grammar`; `sp` is part of speech and `subs` is substantive.
2. `evidence:syriac:proper-inside-subs` — pinned `ETCBC/linksyr` lexicon; proper-name entries use `sp=subs:ls=prop`.

The pinned `ETCBC/syriac` repository remains the supported parent/provenance target; linksyr is evidence only.

### ExtraBiblical evidence

Use two local provenance records plus the shared BHSA definition record:

1. `evidence:extrabiblical:word-sp-enum` — exact compressed MQL source at pinned ExtraBiblical revision; word `sp` is typed `part_of_speech_t`, `subs=2`, `nmpr=3`.
2. `evidence:extrabiblical:feature-authority` — exact ExtraBiblical README; resource is ETCBC/BHSA-family conversion and declares BHSA as core data/feature documentation.
3. Include the BHSA POS-definition evidence in the ExtraBiblical bundle as an additional evidence artifact and bind it to the mapping/projection.

This preserves the two-part chain instead of inferring semantic identity from equal code strings.

## 7. Native dependency closure

All execution dependencies are `native-value-present` with `value_semantics: semantic`, same component/node_type/feature as the executed binding.

IDs:

```text
BHSA:
  dep:bhsa:word-sp:subs
  dep:bhsa:word-sp:nmpr

Syriac:
  dep:syriac:word-sp:subs

ExtraBiblical:
  dep:extrabiblical:word-sp:subs
  dep:extrabiblical:word-sp:nmpr
```

Each dependency binds the relevant corpus-native evidence digest. Set predicates must cover both dependencies; I-010 validation remains the enforcement boundary.

No `closed_values`, value-domain claim, feature-wide closure, node-type-wide ontology claim or compatible-parent fallback is authored.

## 8. Mapping and projection records

Stable IDs:

| corpus | mapping_id | projection_id |
|---|---|---|
| BHSA | `mapping:bhsa:olia-noun` | `projection:bhsa:olia-noun` |
| Syriac | `mapping:syriac:olia-noun` | `projection:syriac:olia-noun` |
| ExtraBiblical | `mapping:extrabiblical:olia-noun` | `projection:extrabiblical:olia-noun` |

Common fields:

```text
profiles: [linguistic]
capabilities: [linguistic.part-of-speech]
native_state: positive
target: http://purl.org/olia/olia.owl#Noun
reference_kind: semantic-pivot
query_role: semantic-constraint
formal_kind: class
semantic_role: annotation-value
profile_id: linguistic
capability_id: linguistic.part-of-speech
assessment: exact
ontology_lock: olia-reference-model
publication_relation: null
```

BHSA/Extra native binding and projection execution binding:

```json
{
  "component_id": "<corpus>-tf",
  "node_type": "word",
  "feature": "sp",
  "values": ["nmpr", "subs"],
  "execution_shape": "value-set-predicate"
}
```

Syriac:

```json
{
  "component_id": "syriac-tf",
  "node_type": "word",
  "feature": "sp",
  "value": "subs",
  "execution_shape": "value-predicate"
}
```

Author the finite values in canonical order `nmpr, subs` even though I-010 identities are order-invariant; source files should themselves be deterministic/human-reviewable.

Mapping/projection evidence binds both the native-semantic evidence and shared OLiA evidence relevant to the exact conclusion.

## 9. Semantic digest and review sequence

Mapping/projection review wrappers are audit-only for the accepted semantic digest algorithms. Use that intentionally; do not fake review data to bootstrap a digest.

Implementation sequence per corpus:

1. author the final semantic mapping/projection body and evidence bindings;
2. compute `projection_semantic_digest_v1` and `mapping_semantic_digest_v2`;
3. expose the exact candidate digests/content in the implementation PR;
4. perform a logically-independent semantic/evidence review specifically against the pinned I-009 research evidence and exact digests;
5. record that review in the PR discussion and obtain its immutable GitHub URL/timestamp;
6. write the mapping/projection `review` objects binding exactly those digests;
7. use truthful machine reviewer identity `openai:gpt-5.6-sol` when this assistant performs the review; never invent a human reviewer;
8. `review_source` is the concrete GitHub review/comment URL; `reviewed_at` is its actual timestamp; `review_method` names the independent evidence/semantics review;
9. any post-review semantic-content change changes the digest and invalidates that review; repeat review before merge.

The final PR-wide adversarial code/release review is a separate gate from the mapping-semantic review above.

## 10. RED contract

Create tests first on an implementation branch with production resources/loader absent. RED must fail for the missing production surface/resources, while existing suites remain green.

Required tests:

### Loader/package resources

- public loader names are exported;
- supported corpus order is exact/deterministic;
- unknown/non-string corpus fails deterministically;
- loader uses package resources and returns structurally validated `SemanticSourceBundle` objects;
- logical `source_name` values are package-relative and deterministic;
- no repository-relative path or network dependency;
- all three bundle trees and shared OLiA resources are present in a built wheel;
- install wheel into isolated target, run child Python with cwd outside repo and `PYTHONPATH` only installed target, load and semantically validate all three bundles.

### Resource truth/closure

- exact parent content and parent-manifest digests equal #148 values;
- shipped OLiA snapshot bytes equal researched digest;
- shared lock semantic fields equal section 5 and `terms_used` contains exactly Noun;
- shared lock is identical across all three loaded bundles;
- OLiA license/attribution resources are shipped;
- no corpus TF/MQL payload is bundled;
- no `example.org`, `fixture-v1`, `reviewer:i005-fixture`, synthetic repeated-character parent digest, `NOASSERTION`, or unspecified-license placeholder survives the final production resource tree;
- no moving branch URL is used as normative evidence/source identity.

### Semantic validation/IR

- each loaded bundle passes `validate_semantic_bundle()`;
- all three validated bundles compile together into one `CompiledSemanticIR`;
- compiled variants contain exact researched parent identities;
- BHSA/Extra compiled execution bindings normalize to `values=("nmpr", "subs")`, set shape, word/sp;
- Syriac compiles to scalar `value="subs"`, scalar shape, word/sp;
- every set selected value has its matching semantic dependency/evidence closure;
- all target exactly the one OLiA Noun IRI and one shared lock identity;
- mappings/projections have current semantic digests and current real review bindings.

### Runtime acceptance with loaded API doubles

Construct three loaded APIs whose TF feature behavior reflects the reviewed encoding differences:

- BHSA has `subs` + `nmpr` word nodes;
- Syriac has noun/proper-name word nodes both under `sp=subs` (the fake does not need to expose `ls` because the executable plan does not read it);
- ExtraBiblical has `subs` + `nmpr` word nodes.

One `execute_exact_semantic()` call for OLiA Noun across all three contexts must:

- freshly evaluate I-007 against exact parent identities;
- resolve one exact plan per corpus;
- execute the heterogeneous native plans;
- return deterministic corpus order, node IDs, fresh plan/runtime provenance;
- never call load/network/query-language APIs.

Negative runtime tests:

- one wrong parent digest fails closed before feature selection;
- one missing selected value fails authorization for the corresponding set corpus;
- one missing scalar `subs` fails Syriac authorization;
- a proper noun encoded as BHSA/Extra `nmpr` is included;
- authored value ordering cannot change plan/result identity.

## 11. GREEN implementation boundary

GREEN may add only:

- the package resources listed in section 1;
- `src/ontotf/production_bundles.py` plus package exports;
- required package-data patterns;
- I-009 tests/workflow;
- minimal attribution/license resource text required by OLiA redistribution;
- no generic resource registry/downloader/materializer/index format.

Do not change semantic schema/runtime contracts unless RED proves an actual defect. Any such defect becomes a separately researched/planned issue rather than opportunistic I-009 expansion.

## 12. CI gates

Add focused I-009 workflow covering Python 3.10 and 3.12 for loader/semantic/runtime acceptance plus one isolated wheel job. Keep existing full repository suite authoritative.

Final implementation head requires:

- focused I-009 green on 3.10/3.12;
- isolated wheel install green;
- I-004/I-005/I-006/I-007/I-008/I-010 regressions green;
- full repository suite green;
- no hidden pytest-only tests;
- fresh logically-independent adversarial review anchored to the exact final SHA.

## 13. Merge blockers

I-009 implementation must not merge while any of the following remains true:

- #153 project/profile licensing unresolved or production profile license is a placeholder/inferred corpus license;
- semantic review records do not bind current mapping/projection digests;
- exact OLiA snapshot/license/attribution not present in wheel;
- production resources contain synthetic fixture provenance;
- clean-wheel loader/validation path depends on source checkout;
- any corpus plan differs from the corrected research semantics;
- final exact-head adversarial review has a blocker.

## 14. Out of scope after I-009

Defer to later tickets/releases:

- more OLiA POS terms;
- compatible parent revisions beyond the three exact measured targets;
- R-018 generic composition;
- RDF publication generation/runtime indexes;
- Agora registration/discovery;
- corpus acquisition;
- generic ontology package management;
- v0.1 version bump/README/release notes/tagging, which remain release-polish work under #142.
