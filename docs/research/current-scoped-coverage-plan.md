# Current mapping denominator: scoped census and applicability

## Researcher acceptance

A user should be able to open the Pages dashboard and determine, for a pinned
corpus, which actual native semantic items are accounted for, which have
positive ontology mappings, and which remain unreviewed. Every denominator
must be recoverable from a source inventory and an explicit granularity /
applicability policy. Do not equate 100% review with 100% positive matches.

## Existing evidence and observed failures

* R-005's empirical TF loader records feature-wide value domains and separate
  source/target type sets. A Cartesian product of those domains is false:
  ETCBC `typ` has distinct phrase and clause values; `rela` uses distinct
  case-sensitive domains across clauses, phrases, phrase atoms and subphrases.
  For ExtraBiblical 0.2, the pinned clause relation block has 8,908 annotations
  including 727 Adju and 78 Subj (see PR #424's source review). A pooled
  `rela` domain cannot express those scopes.
* `omap@2017-2021` and `omap@c-2021` in BHSA are cross-version node maps;
  interpreting both endpoints with the current `otype` produces spurious
  local edges. Preserve their existence and counts without claiming endpoint
  types for a different version.
* The historical P-004 routing policy
  [I-026](data/i026/p004-routing-policy.json) is valuable prior semantic
  research, but it groups models, uses unscoped names, excludes SyrNT and
  Peshitta, and pins older converter artifacts. Its 934 items are not a current
  node-scoped denominator. Do not edit the frozen policy or historical counts.
* The XML catalog distinguishes exact and qualified mappings, nonpositive
  dispositions, node presence guards, scoped features and directed edges.
  Current XML edge selectors cannot represent an individual valued-edge value:
  census such values, but keep them as a representational gap until real
  researcher use justifies a small XML extension.
* Existing source-generated feature docs supply the current ORACC 1.0.0
  schema but not exhaustive scope/values. At the mapping-pinned
  [builder revision](https://github.com/alexsosn/ORACC-TF/tree/60db4b724a687c0f425e78eae924fce89454e106)
  the README describes a staged candidate and pending public release. The
  committed source tree is not a verified published TF artifact. Acquire the
  versioned candidate with verified provenance or rebuild from exact source
  before claiming a real scoped census; do not silently substitute 0.4.0.

## Implementation stages

### A. Empirical inventory (this change)

Extend the existing R-005 tool with opt-in `--scoped`. Preserve the historical
generator byte contract. For each pinned TF artifact record all node types,
all non-warp feature names (including empty-only features), nonempty scope
counts, actual directed edge pairs and selected observed value frequencies.
Storage empties are not categories; literal `NA`, `unknown`, whitespace and
integer zero are distinct observations. Cross-version edges remain explicit.
The CLI publishes values only for named source-documented categorical families;
no free-text samples, IDs, transliterations or large open-domain values. The
512-value per-scope ceiling is a safety bound, not a closed-vocabulary
inference. Overflow is explicit and has no partial value list.

Reuse the research-inventory workflow. The new read-only PR/dispatch mode
generates the current seven direct/checksummed sources plus TLHdig 0.4.0
(eight total); the old historical verification remains separate. These jobs
run only for census changes or manual refresh, never for normal mapping
batches. Matrix values are initial source-researched selections, derived
from R-005 metadata and R-011/I-017/I-019 bounded-family research, plus the
current documented XML feature families. An omitted feature is **not**
a determination of open-domain status or ontology inapplicability. Expand the
categorical selection when source evidence requires it. Source acquisition
and resource failures must remain explicit.

Acceptance: unit counterexamples plus real corpus counts; for ExtraBiblical,
cross-check the independent clause relation counts and word-slot total.
Generated data are source evidence, not a replacement XML mapping ledger.
Review artifacts and commit the compact evidence snapshots in a subsequent
cohesive PR. Store scope inventories separately from frozen R-005 snapshots.

### B. Semantic granularity and ontology applicability

Use the scoped inventories from A, source codebooks, the R-011/I-026 routes,
and source-specific converter documentation. Classify **feature families**
in batches with evidence:

| Kind | Unit |
| --- | --- |
| Native node category | node type or explicit meaningful guard (do not promote guarded nodes to unconditional mappings) |
| Documented categorical node feature | each actually observed (node type, feature, value) |
| Open feature | (node type, feature), not individual words, glosses, IDs or offsets |
| Typed edge | (edge feature, actual source type, actual target type) |
| Categorical edge | typed edge plus observed value where semantic; show unsupported XML granularity explicitly |
| Technical / empty-only / source-specific | reasoned exclusion or native-only disposition, not positive coverage |

An unclassified family is a visible review gap. Do not automatically treat a
small observed domain as categorical or an old route as current ontology
applicability. Determine applicable ontology sets (which may overlap), using
the seven-model semantic roles and actual source semantics. Use a concise
family-level research policy, never duplicate XML mapping decisions. Allow
scope-specific overrides only where justified by the corpus. Preserve a
separate status for unresolved applicability, so an incomplete denominator
cannot be advertised as final. Apply existing XML selectors by compatible
version and semantic scope; do not count a mapping to ontology A as review
of ontology B without explicit evidence.

### C. Pages integration

Derive the denominators at build time from reviewed inventory and applicability
evidence. The XML catalog remains the only source of mapping dispositions.
Report exact, qualified, reviewed without positive mapping, unreviewed and
unclassified counts independently; per-ontology percentages only when the
eligibility inventory is complete. Show explicit out-of-inventory mappings
and version/revision mismatches. Keep current schema-touch metrics as
secondary measures. No new runtime dependency, profile release ceremony, or
generated mapping ledger. Validate arithmetic on real corpus evidence and
build the actual Pages artifact.

## Scope of this episode

A is the first implementation gate. B and C depend on verified current
inventories; no precise ontology-specific completion claim before then.
ORACC acquisition, large TLHdig memory requirements, and licensing boundaries
may require separately bounded follow-up work. Continue semantic mapping
batches independently; new inventory work must not gate ordinary XML edits.
