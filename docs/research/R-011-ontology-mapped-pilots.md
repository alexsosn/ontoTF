# R-011: ontology-mapped pilots and cross-corpus semantic coverage

**Status:** research/prototype complete; exact-head CI green; pending fresh logically-independent adversarial review  
**Issue:** #43  
**Recorded:** 2026-09-07  
**Depends on:** accepted R-005/R-006/R-007/R-008/R-009/R-010 and R-012

## Decision

The seven-model common semantic basis is **viable as ontoTF's interoperability pivot**, provided P-003 keeps native semantics, mapping assessment, capability state, authority references, and common ontology projections distinct.

The effective non-production pilot contains all seven required corpora, **52 reviewed mapping rows**, **108 agent-useful weight units**, and **67/108 = 62.0% weighted common-target coverage**. Mapping assessments are: 15 `exact`, 11 `close`, 3 `ambiguous`, 22 `native-only`, 1 `unsupported`, and zero `broader` / `narrower` / `related` in this deliberately conservative sample.

`pilots.json` preserves the original research fixture. Fresh adversarial-review corrections are machine-readable in `mapping-overrides.json` and are applied **before every weighted, raw-schema, and query-portability measurement**. The current effective corrections are:

- exclude `extra-gloss`: the pinned ExtraBiblical R-005 inventory contains no `gloss` node feature, so the row is not counted as reviewed evidence;
- override `oracc-document` to `native-only`: generic ORACC `otype=document` is broader than reproducibly demonstrated physical-carrier identity, so it does not compile to CRM E22 until a reviewed object-bearing selector exists.

The 62.0% weighted figure is **not raw schema coverage**. Raw coverage is measured separately and retains unreviewed schema items as unreviewed rather than silently converting them to `native-only`.

The result is a qualified **GO** for the common pivot and a **NO-GO** for minting a broad ontoTF ontology before R-013–R-017/P-003.

## Reproducible artifacts

- `docs/research/data/r-011/pilots.json` — source research fixture;
- `docs/research/data/r-011/mapping-overrides.json` — exact effective corrections from adversarial review;
- `docs/research/data/r-011/raw-schema-policy.json` — raw denominator and bounded-value policy;
- `docs/research/data/r-011/query-suite.json` — required query intents and fail-closed probes;
- `scripts/research/r011_measure.py` — effective-fixture measurement and prototype query compiler;
- `tests/research/test_r011_measure.py` — executable research contract;
- `.github/workflows/r011-report-validation.yml` — exact-head CI gate.

Run:

```bash
python scripts/research/r011_measure.py
pytest tests/research/test_r011_measure.py
```

Compact targets such as `olia:Noun`, `olia:First`, `crmtex:TX7`, and `crm:E22_Human-Made_Object` are research identifiers for reviewed ontology concepts. R-013 owns final target formal kinds/roles and production IRI handling. Mapping assessment remains a ontoTF runtime concept, not an RDF publication predicate.

## Exact corpus evidence boundary

All seven pilot inputs have explicit revision pins:

| fixture id | corpus | evidence boundary |
|---|---|---|
| `bhsa` | ETCBC/BHSA | `4db00e2157915495e1a4d3d57e41223df24775da`, TF 2021, generated R-005 inventory |
| `cuc` | Copenhagen Ugarit Corpus | `ad69400f5446e1c8217af01659c7c10ab00c015b`, TF 0.2.8, generated R-005 inventory |
| `syriac` | ETCBC Syriac | `bb0eaa7e21b020a26b7566d2e495da9b1f84a919`, TF 0.9, generated R-005 inventory |
| `extrabiblical` | ETCBC ExtraBiblical | `9a56288e6777bad6328856acf055c780e65dd5d9`, TF 0.2, generated R-005 inventory |
| `pseudepigrapha` | Pseudepigrapha-TF | `d098845043897957efee7a42ae4854deddd5a1bd`, curated R-005/R-009 converter contract |
| `oracc` | ORACC-TF | `e8f2b160912e0adaa37b24e68384ac551077a440`, refreshed active-model contract after ADR-0001 |
| `tlhdig` | TLHdig-TF | R-005 pinned generated inventory / converter contract |

The first five machine inventories plus TLHdig's generated inventory provide machine-exhaustive non-warp schema denominators for their R-005 snapshots. Pseudepigrapha and ORACC use explicitly labelled **curated, non-exhaustive** denominators. ORACC is intentionally refreshed to its active `e8f2b160...` model because the older R-005 zero-span sidecar design was superseded; unimplemented translation-M9 node types are excluded from its denominator.

## Coverage

### Agent-useful weighted target coverage

Exact CI measurement on the effective fixture:

| profile | weight | common-target weight | coverage |
|---|---:|---:|---:|
| linguistic | 40 | 34 | 85.0% |
| lexical | 17 | 14 | 82.4% |
| written text | 16 | 10 | 62.5% |
| heritage/object | 14 | 6 | 42.9% |
| textology | 7 | 3 | 42.9% |
| apparatus | 9 | 0 | 0.0% |
| scholarly annotation | 3 | 0 | 0.0% |
| provenance/editorial | 1 | 0 | 0.0% |
| archaeology negative control | 1 | 0 | 0.0% |
| **total** | **108** | **67** | **62.0%** |

Weights express pilot research usefulness, not corpus frequency or ontology confidence. `native-only` remains legitimate reviewed content and is intentionally excluded from common-target weight.

### Raw native schema coverage

The executable denominator includes node types, edge features, feature concepts, and explicitly bounded feature values. Exact CI reports:

- **685 raw schema items** in the combined denominator;
- **209 bounded-value items**;
- **99 reviewed items = 14.5%** of that mixed-quality denominator;
- **26 items with a common target = 3.8%**;
- **586 items remain unreviewed**.

Per-corpus denominator quality is intentionally visible:

- 5 corpus denominators are machine-exhaustive for their R-005 non-warp inventories;
- 2 are curated non-exhaustive baselines (Pseudepigrapha and ORACC).

Therefore **14.5% and 3.8% are descriptive aggregate figures, not a uniform exhaustive cross-corpus coverage estimate**. They must not be compared to the 62.0% agent-useful weighted metric as though the denominators represented the same question.

The fail-closed policy is important: a row may only review a raw item that actually exists in its denominator. This gate caught and removed the unsupported ExtraBiblical `gloss` row rather than allowing the metric to absorb an invented feature.

## Query portability

The prototype now contains **19 query intents** covering the required positive and negative cases. Seven common-target intents compile to reviewed native plans for at least two corpora:

1. **Noun — `olia:Noun`**: exact in BHSA, Syriac, and ExtraBiblical via `sp=subs`.
2. **Plural verb — `olia:Verb AND olia:Plural`**: exact conjunction in the same three corpora.
3. **First person — `olia:First`**: exact from BHSA/ExtraBiblical `ps=p1` and Syriac `ps=first`.
4. **Masculine gender — `olia:Masculine`**: exact in BHSA and Syriac via `gn=m`.
5. **Lexical entry — `ontolex:LexicalEntry`**: BHSA exact candidate; Syriac, ExtraBiblical, ORACC, and TLHdig are `close` because their native identity construction differs.
6. **Written-text line — `crmtex:TX7`**: `close` candidates for CUC, ORACC, and TLHdig where line semantics denote a segment of physical written text.
7. **Physical textual object — `crm:E22_Human-Made_Object`**: `close` candidates for **CUC tablet and TLHdig document only** in the current effective fixture.

ORACC deliberately fails closed for the generic physical-object request. The active pinned target has 2,078 document identities but only 2,075 catalogue joins, while R-010 requires native/catalogue evidence that the identity denotes a physical artefact. `otype=document` alone is therefore not an accepted E22 selector. A future reviewed object-bearing predicate can restore that projection without changing this failure mode retrospectively.

Pseudepigrapha is also deliberately absent from the generic physical-object query. Its native `manuscript` node is a textual witness identity, including citation-only synthesized witnesses; physical carrier identity requires separate evidence.

A compiled `close` plan is **not execution authorization**. The prototype marks it `approximate-candidate-R016-required`; R-016 owns production approximate-mode rules.

## Lexical depth controls

The expanded query suite now tests the distinctions required by R-008:

- lemma/headword representation lookup remains native where no reviewed OntoLex Form identity exists;
- ORACC explicit source sense IDs remain source-sense identities and are not promoted automatically to a shared OntoLex sense/concept;
- no shared `ontolex:LexicalConcept` query resolves from gloss/guide-word string equality.

Pseudepigrapha `version -> lrmoo:F2_Expression` remains a conservative `close` candidate after source-level review of the pinned converter contract: top-level textual versions have stable version identities, multi-version work retrieval, and explicit `available` / `not_present` / `metadata_only` state. The mapping is not inferred merely from the label `version` and remains distinct from physical witness carriers.

## Structural and carrier controls

- CUC, ORACC, and TLHdig expose native structural-navigation probes without pretending their TF section/embedding paths are one universal containment predicate.
- TLHdig `surface` is explicitly `native-only`: it belongs to the physical carrier spine `... line -> column -> surface -> document` and is **not** a CRMtex TX7 written-text segment.
- TLHdig `line -> TX7` remains a separate close candidate because the line is a written-text segment, not the physical support surface.

## Fail-closed probes and recurrent gaps

Every reported query outcome includes capability, mapping strength, native selectors/path, execution status, and reason for non-execution.

The current prototype records **5 recurrent gap query families** that have meaningful native support in more than one place but no reusable accepted common target/path:

1. damage/restoration semantics;
2. unsafe cross-linguistic verbal-stem comparison;
3. lemma/form representation lookup;
4. structural navigation;
5. physical witness/manuscript/fragment roles.

Additional single-corpus or deliberately unsupported controls include apparatus reading/witness attestation, material, period, provenience, archaeology, and source lexical sense/shared lexical concept cases.

These are evidence for P-003 profile/capability design, not automatically evidence that ontoTF should mint local ontology classes.

## Mapping-strength and multiple-projection result

The effective mapping distribution is:

- `exact`: 15
- `close`: 11
- `ambiguous`: 3
- `native-only`: 22
- `unsupported`: 1
- `broader`: 0
- `narrower`: 0
- `related`: 0

This representative fixture has **0 rows with multiple simultaneously asserted complementary common targets**. That is a measured pilot result, not a schema recommendation. R-006/R-009 still require P-003 to support complementary projections because physical carrier, textual/intellectual role, lexical identity, grammatical annotation, and scholarly inference can coexist as different semantic dimensions. R-011 refuses to invent second targets merely to make this count non-zero.

## False-equivalence hazards confirmed

1. `lex` does not imply identical lexical identity construction.
2. `line` storage does not automatically imply CRMtex TX7 semantics.
3. `surface` is not a written-text segment merely because text is written on a surface.
4. `sign` does not select glyph vs grapheme without source evidence.
5. Pseudepigrapha `reading` is not CRMtex `TX14 Reading`.
6. Pseudepigrapha `manuscript` is a textual witness identity, not automatically a physical carrier.
7. TLHdig physical fragment cannot be collapsed into an LRMoo symbolic fragment.
8. `witness` has materially different assertion shapes across corpora.
9. material/period strings are authority values, not ontology classes by default.
10. catalogue/source facts are not CRMinf inference events.
11. ancient-object metadata does not imply CRMarchaeo excavation capability.
12. common feature names do not make language-specific verbal categories equivalent.
13. generic ORACC `document` identity does not by itself prove CRM physical-object identity.

## P-003 requirements demonstrated

P-003 must support:

- typed projections and native selector/path identity;
- per-projection mapping assessment;
- controlled profile/capability state separate from rows;
- first-class `native-only`, `unsupported`, and ambiguity;
- common-target -> corpus-native plan indexes;
- conjunction compilation;
- explanations exposing exact native plan and assessment;
- role-sensitive witness/carrier distinctions rather than `otype`-name projection;
- exact parent corpus revision/evidence boundaries;
- R-015 bundle/bridge identity;
- R-016 approximate execution authorization;
- R-017 authority-resource separation;
- R-013 target-kind/role vocabulary and R-014 agent-facing capability IDs.

The resolver must never manufacture mappings from label similarity, shared TF feature names, ontology hierarchy traversal alone, or a physical-object assumption not encoded in the native selector.

## Go/no-go

**GO:** the common pivot shows real reuse across heterogeneous corpora: OLiA across three linguistic corpora, OntoLex lexical-entry semantics across five, CRMtex line semantics across three, CRM physical-object semantics across two, and an LRMoo textual-version candidate with source-level evidence.

**NO-GO for a broad new ontoTF ontology:** the most important residual gaps remain profile/role/assertion-shape problems. Apparatus/witness-attestation is still represented fully by only Pseudepigrapha; structural navigation is intentionally native; material/period authority semantics await R-017. Keep these native/profile-local until recurrence and governance justify a shared target.

## Exact-head validation

The R-011 workflow executes the measurement and dedicated contract tests on pull requests touching this research package. The current validated head reports:

- measurement completed successfully;
- **10/10 R-011 contract tests passed**;
- 52 effective rows / 108 weight / 67 common-target weight;
- 685 raw items / 99 reviewed / 26 common-target / 209 bounded values;
- 19 queries, including 7 multi-corpus common-target intents;
- 5 recurrent gap query families;
- 0 complementary-projection rows.

## Acceptance trace

- [x] all seven required corpora represented with exact revision pins;
- [x] ExtraBiblical retained as high-similarity control;
- [x] raw schema coverage measures node/edge/feature concepts and bounded values, with denominator quality disclosed;
- [x] weighted common-target coverage measured independently: 67/108 = 62.0%;
- [x] all eight assessment categories reported, including zero-count categories and explicit `unsupported` control;
- [x] 19 query intents cover the required linguistic, lexical, structural, witness, heritage, authority, and negative cases;
- [x] seven common-target intents compile to valid native plans for 2+ corpora;
- [x] every query outcome reports capability, mapping strength, native selectors/path, and non-execution reason where applicable;
- [x] recurrent gaps and the zero complementary-projection-row result are measured explicitly;
- [x] native-only / unsupported / ambiguous states are preserved rather than optimized away;
- [x] false-equivalence hazards discovered by review are encoded in the effective fixture/probes;
- [x] P-003 schema/IR/runtime requirements identified;
- [x] qualified GO for the pivot and NO-GO for a broad local ontology.

## Review targets

A fresh reviewer should challenge the exact OLiA mappings, lexical-entry identity strength, CRMtex TX7 preconditions, CUC/TLH CRM E22 projections, Pseudepigrapha LRMoo F2 use, witness/carrier separation, raw-denominator quality, R-016 execution boundary, effective mapping overrides, and every fixture reference against its exact pinned native evidence.
