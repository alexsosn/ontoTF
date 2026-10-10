# I-027B1 research — BHSA `sp=verb` to OLiA Verb

**Issues:** #275, parent #274 / #264 / #202  
**Source corpus:** ETCBC/bhsa `4db00e2157915495e1a4d3d57e41223df24775da` (TF 2021)  
**Ontology:** OLiA core snapshot `d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6`  
**Prior release:** `tfont-bhsa` `0.2.0`, immutable

## Question

Can we add a reviewed exact OLiA `Verb` semantic projection to the BHSA production linguistic profile without changing the meaning or identity of the existing 0.2.0 noun/morphology release?

Yes, at the level of a **word-level part-of-speech annotation**. The BHSA source documentation describes `sp` as part-of-speech of a word (or rather lexeme), lists `verb` as the *verb* code, and explicitly states that `sp` exists on `word` and `lex` node types. The execution binding must therefore explicitly select `node_type="word"`, `feature="sp"`, `value="verb"`; it must not silently merge lexical nodes into word-level results.

Evidence:
- `ETCBC/bhsa@4db00e2:docs/features/sp.md`, source tag definitions; `sp=verb` exactly “verb”.
- `docs/research/data/generated/r005/bhsa.json#/node_features/sp`, pinned inventory observed values and 75,451 `verb` observations. Observed counts need not mean 75,451 **word** nodes because the feature also applies to lexemes.
- `http://purl.org/olia/olia.owl#Verb` from OLiA core reference model; use the already locked snapshot, not a floating latest version.
- Historical R-011 research pilot `bhsa-pos-verb` gives a candidate `exact` decision but carries no production authority; independent source review is mandatory.
- Production `0.2.0` baseline already has class `olia:Noun` on value set `nmpr|subs`, class `olia:ProperNoun` on `nmpr` and word-level gender/number projections.

## Semantics and limitations

`Verb` is defensible as exact **annotation-category correspondence** for `word.sp=verb`. It does not prove that the token is verbal in all linguistic theories, or that verb subclasses, finite/nonfinite form, stem, aspect, tense or valency are mapped. In particular, **no** derivation `vs=qal/piel/hif` → OLiA `Verb`, `Voice` or `Tense` is implied. `sp=verb` is a different feature from `vs`.

The ontology term's RDF type and IRI must be verified against the locally vendored snapshot, then locked in a separately versioned ontology-lock manifest listing the newly used term. A generic floating ontology class name is not evidence.

## Release/authority design

- Preserve bytes of each `0.1.0` and `0.2.0` resource. Write a new immutable `0.3.0` production profile with evidence, native-value-present dependency, reviewed mapping and projection, and versioned ontology lock.
- Reuse existing 0.2.0 Noun/ProperNoun/morphology semantics unchanged; no recertification through copying stale review metadata.
- Add new normalized corpus evidence for `sp=verb` and a new OLiA ontology-definition evidence record specific to `Verb`; evidence records and mapping/projection review digests must match the new contents.
- If a source passage or ontology assertion cannot be pinned/verified, leave the exact mapping unshipped and record the blocker.
- A new immutable P-004 BHSA coverage successor should inherit the I-027A native-only reviewed `vs` items, then add exactly one additional production accounting entry for the already bounded `node_value:sp="verb"` without changing the 219-item denominator or prior mapping accounting.

## Acceptance constraints

- 0.2.0 profile semantics and file identities unchanged.
- New profile exports `olia:Verb` exact only at word level and still recognizes old `olia:Noun` constraints.
- Parent component manifest exact identity and dependency semantics validated on the same pinned corpus.
- Review and source evidence must be content-bound, including correct snapshot + source revision.
- Full CI/review gates before merge.
- Residual linguistic work remains in #264; neither this slice nor I-027A closes the 380-item workstream.

## Outcome

Research supports a bounded positive OLiA Verb mapping. Implementation must supply immutable 0.3.0 artifacts and a separate accurate coverage successor. Syriac/ExtraBiblical are independent corpus reviews under #274 and cannot inherit BHSA equivalence automatically.
