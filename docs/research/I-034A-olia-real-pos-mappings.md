# I-034A — source-grounded BHSA/Syriac POS → OLiA class mappings

**Issues:** #283, #264, #290, #329. **Baseline:** `ec40353132a2339378f80e59b280e1f76ac440c0`.

## Research: actual pinned primary sources, not approximate labels

- **BHSA**: [ETCBC/bhsa `docs/features/sp.md` at `4db00e2`](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/sp.md#L15-L30) labels `word.sp` 9 previously unprojected categories: article `art` (17), preposition `prep` (22), conjunction `conj` (23), personal pronoun `prps` (24), demonstrative pronoun `prde` (25), interrogative pronoun `prin` (26), interjection `intj` (27), negative particle `nega` (28), interrogative particle `inrg` (29).
- **Peshitta Syriac**: [ETCBC/linksyr `word_grammar` at `3ba4243`](https://github.com/ETCBC/linksyr/blob/3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6/data/lib/syriac/word_grammar#L83-L93) labels `word.sp`: `conj` conjunction (86), `inrg` *interrogative* (87), `intj` interjection (88), `nega` *negative* (89), `prep` preposition (90), `pron` pronoun (91).
- **OLiA**: actual [`acoli-repo/olia@d3bd4f1/owl/core/olia.owl`](https://github.com/acoli-repo/olia/blob/d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6/owl/core/olia.owl) includes specific `owl:Class` declarations, not just the ten original `terms_used` in installed `lock-linguistic-0.4.0.json`. Same frozen ontology source blob `5c5e8bda93eaeab2940472a167ff8d3107be8d43`, SHA-256 `5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd`. Relevant exact original 1-based XML class-opening lines: Article 1682, Preposition 525, Conjunction 356, DemonstrativePronoun 1935, InterrogativePronoun 2135, Interjection 307, NegativeParticle 3684, InterrogativeParticle 3812, Pronoun 1860. OLiA also defines `PersonalPronoun` at 2189 but explicitly labels it **irreflexive personal pronoun**, a narrower meaning than BHSA `prps`'s bare *personal pronoun* gloss.

## Decision ledger (15 distinct uninstalled corpus selectors, 12 positive)

| Corpus | `sp` | Source line | Chosen OLiA class | Assessment and caution |
| --- | --- | ---: | --- | --- |
| BHSA | `art` | 17 | Article | exact POS category |
| BHSA | `prep` | 22 | Preposition | exact, Hebrew prepositions can be proclitic; TF POS category, not token segmentation |
| BHSA | `conj` | 23 | Conjunction | exact generic conjunction, not coordinating/subordinating subclass |
| BHSA | `prps` | 24 | *none* | native-only: OLiA PersonalPronoun narrows to irreflexive; source does not specify |
| BHSA | `prde` | 25 | DemonstrativePronoun | exact to source's explicit demonstrative **pronoun** class, not a determiner inference |
| BHSA | `prin` | 26 | InterrogativePronoun | exact, unlike interrogative particle |
| BHSA | `intj` | 27 | Interjection | exact morphosyntactic POS |
| BHSA | `nega` | 28 | NegativeParticle | exact, OLiA explicitly 'particle used to express negation', not abstract Negation |
| BHSA | `inrg` | 29 | InterrogativeParticle | exact, OLiA 'particle used to express a question'; not interrogative pronoun |
| Syriac | `conj` | 86 | Conjunction | exact general POS |
| Syriac | `inrg` | 87 | *none* | native-only: source says 'interrogative', not specifically a particle |
| Syriac | `intj` | 88 | Interjection | exact POS |
| Syriac | `nega` | 89 | *none* | native-only: source says 'negative', not explicitly a particle |
| Syriac | `prep` | 90 | Preposition | exact POS |
| Syriac | `pron` | 91 | Pronoun | exact generic class, NOT PersonalPronoun/DemonstrativePronoun/InterrogativePronoun |

**What 'exact' means here:** exact alignment of a **source-declared POS category** with a named OLiA `owl:Class`, in the system's pre-existing `annotation-value` schema, not formal OWL equivalence of corpus individuals or a proof from occurrence statistics. The ontology defines some classes loosely and at varying granularity; exact proposed mappings require an adversarial challenge before publication. This is not automatic reasoning from spelling.

## The minimal data release approach (no architecture ticket)

1. Add **immutable extra POS ontology lock** `lock-linguistic-i034a-pos.json` with expanded 19 pinned target URIs but the **same exact source owl snapshot digest**; never mutate the published `lock-linguistic-0.4.0.json`. Each of nine new terms has its own normalized evidence record with original declaration line and original blob digest.
2. Add one 15-row `proposal-only` batch ledger using the **existing compiler**, source evidence identities from previous ten-row BHSA/Syriac candidate (which retains original source URLs and target corpus pins) and `ontology_evidence_resources` for all nine used exact target classes. Actual proposed mappings: **12** positive exact + **3** conservatively native-only; no duplicate selected source value.
3. TDD must compile all rows against real installed OLiA snapshot with checked source evidence, assert class existence/pin/URI/digest and source line, 12 nonempty `projections` only for exact matches and no projection for three unresolved rows, no registry installation or invented `release_authorized`. Test semantic distinctions and correct prior status.
4. Protected `check_external_review.py` requires an ontology lock **already packaged in protected main**, while a candidate PR cannot cause protected code to load a new untrusted lock. This **data PR** installs the real ontology-term pins and records the 15 semantic decisions (not a release). After it merges, open one **reviewable 15-row candidate batch PR** with a manifest + packet referencing the now-protected same lock and submit two logically independent GitHub challenge/decision passes using the existing single-agent gate. Do **not** bypass this trust boundary or fork a new review architecture.
5. After reviewing, the existing immutable handoff, installed-release workflow and coverage overlay must be exercised. If native-only entries are already installed, use #329's versioned promotion rather than silently overwriting them. Source #324's prior native-only batch was attested but has **not** been installed in the versioned semantic registry.

**Count:** 15 source-grounded candidate decisions, 12 positive OLiA class mappings, 3 unresolved native-only. **Installed** new positive shared-target mappings are zero until protected release completes.
