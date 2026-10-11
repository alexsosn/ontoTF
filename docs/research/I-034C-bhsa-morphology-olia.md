# I-034C — BHSA morphology → pinned OLiA, 29 observed values (12 positive)

**Scope:** Actual semantics under #264 / #202. Not another infrastructure ticket. Base `90d22551aba675a65f55bb700bede913bd2397bd`.

## Primary evidence independently inspected

Original BHSA source revision `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da`:

| TF feature | Original documentation | Observed values in current installed denominator | Semantic care |
| --- | --- | --- | --- |
| `word.ps` | `docs/features/ps.md` lines 14–18 | p1, p2, p3, NA, unknown | Person of inflected word, not PersonPronoun |
| `word.prs_ps` | `docs/features/prs_ps.md` lines 15–18 | p1, p2, p3, NA | Person of **pronominal suffix** on word, not person of host |
| `word.prs_gn` | `docs/features/prs_gn.md` lines 12–15 | m, f, NA, unknown | Gender of pronominal suffix, not of host |
| `word.prs_nu` | `docs/features/prs_nu.md` lines 15–18 | sg, pl, NA | Number of pronominal suffix; dual is documented but **not in pinned observed denominator**, do not invent its occurrence |
| `word.st` | `docs/features/st.md` lines 17–21 | a, c, e, NA | c construct; a absolute, e emphatic; original docs themselves warn state meanings require clarification |
| `word.vt` | `docs/features/vt.md` lines 14, 20–27 | NA, perf, impf, wayq, impv, infa, infc, ptca, ptcp | Hebrew verbal aspect/tense names are not generally interchangeable with European tense classes |

The frozen production denominator is `src/tfont/resources/coverage/p004-i027c2-bhsa-adj-adv-v1/bhsa.json` (219 items, source revision pinned). These 29 exact `node_value` identifiers are already present; none was production-reviewed in that manifest. Historical 0.4.0 masculine/feminine and singular/plural/double *host-feature* mappings exist and remain unchanged; **pronominal suffix features are different native selectors**.

The actual pinned OLiA `acoli-repo/olia@d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/owl/core/olia.owl` (installed SHA-256 `5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd`) has declaration lines:
`First` **4986**, `Second` **4976**, `Third` **4963** (PersonFeature, **not** FirstPersonPronoun);
`Feminine` **5123**, `Masculine` **5151**,
`Singular` **4183**, `Plural` **4157**,
`StatusConstructus` **6712** (as `rdf:ID`, Semitic construct state),
`ImperativeVerb` **1373** (finite imperative verb).
These are POS/morphosyntactic **class-level value alignments**, not identity assertions about TF word nodes. Original OLiA `Perfect` (5292) means completed action **in the past**; `Imperfect` (5566) is past incomplete/ongoing; neither should be projected as an exact match to BHSA `vt.perf`/`vt.impf` without independent tense/aspect semantics. `Emphatic` in OLiA is emphasis (4951), *not* Semitic emphatic state.

## Batch decision

Precisely **29** source-observed BHSA feature/value items: **12 class-aligned positive proposals** (3 ps, 3 prs_ps, 2 prs_gn, 2 prs_nu, st=c, vt=impv), **17 conservative native-only** pending better evidence. Preserve per-row original source URI, revision, exact line and gloss, original fixed denominator identity, ontology snapshot, class URI and exact original declaration line, and an individual rationale.

**Boundary:** This research-only, unreviewed ledger is a distinct feature-value semantic adjudication; it does NOT mutate protected 0.4.0 source artifacts, create 29 published mappings, sign GitHub review authority, invent morpheme nodes or attach gender/number/person to the host where the original source says the pronominal suffix. Future generalized batch release may consume it after normal review; do not create per-value reviews or CI workflows.

## Adversarial targets

Challenge one-to-many reuse of the OLiA person classes for host and suffix roles; verify that the native feature binding preserves the differing subject. Challenge Hebrew “perfect” vs past `olia:Perfect`, “imperfect” vs past `olia:Imperfect`, noun state "emphatic" vs emphasis, and documented-but-unobserved values. Test every exact class declaration at the pinned XML line and every 29-denominator selector against the original frozen installed inventory.
