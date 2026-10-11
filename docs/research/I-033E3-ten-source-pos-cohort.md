# I-033E3 / #303 — source-pinned ten-selector review proposal

**Issue:** #303
**Base:** `02423525a6d814f2f1042950d607a4500203c3c4`
**Scope:** candidate input data only; no runtime release, coverage promotion or attested reviewer signature.

## Primary evidence inspected at immutable Git commits

BHSA `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da`, [docs/features/sp.md](https://github.com/ETCBC/bhsa/blob/4db00e2157915495e1a4d3d57e41223df24775da/docs/features/sp.md): `sp` is a lexical part-of-speech feature present on TF word and lex. The original markdown table lists these native values and descriptions at exact **1-based lines**:

| Feature value | Original gloss | Source line |
| --- | --- | ---: |
| `art` | article | 17 |
| `prep` | preposition | 22 |
| `conj` | conjunction | 23 |
| `prps` | personal pronoun | 24 |
| `prde` | demonstrative pronoun | 25 |
| `prin` | interrogative pronoun | 26 |
| `intj` | interjection | 27 |
| `nega` | negative particle | 28 |
| `inrg` | interrogative particle | 29 |

Syriac grammatical rules: `ETCBC/linksyr@3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6`, [data/lib/syriac/word_grammar](https://github.com/ETCBC/linksyr/blob/3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6/data/lib/syriac/word_grammar) defines `sp` as part of speech; `pron: "pronoun"` is at original **line 91**. The corpus target remains `ETCBC/syriac@bb0eaa7e21b020a26b7566d2e495da9b1f84a919`, not the grammar repository revision.

The existing `src/tfont/resources/profiles/{bhsa,syriac}/0.4.0/evidence/native-adj-adv-pos.json` records provide immutable source URI, revision, node scope, TF target version and existing adjv/advb definitions. This batch creates **new supplemental, digest-bound candidate evidence** at those same frozen source pins and includes the original adjv/advb definitions unchanged. It does **not** mutate the installed historical evidence.

## Scholarly interpretation and non-claims

Ten source-grounded selectors **are not** ten demonstrated `owl:Class` equivalences. The existing OLiA `lock-linguistic-0.4.0.json` explicitly pins only the ten present class targets, including Adjective, Adverb, Noun, ProperNoun, Verb, Singular, Plural, Dual, Masculine, Feminine. That lock does not pin Article, Conjunction, Preposition or pronoun subcategory classes, whether or not broader OLiA defines them. We therefore propose ten `native-only` review decisions with **individual** rationale: a reviewer may reject or request stronger target evidence before approval. `native-only` means no shared-target projection in this candidate release, **not** a claim that no suitable ontology concept exists anywhere.

The Greek and Hebrew terminology of interrogatives, negative particles, pronouns, etc., is not inferred from spelling alone. The Peshitta/ETCBC Syriac `pron` code is a general pronoun, not silently equal to `prps` or any single BHSA subtype. No information is invented for counts/observations that are absent from the cited source; earlier adjv/advb observed counts are preserved as existing evidence.

## Existing architecture and review authority

The generic writer merged in #323 reads a v2 manifest `docs/research/data/batch_review/inputs.json`, one ledger and bounded supplemental evidence JSON, verifies locked source identity and recomputes an unapproved packet. The protected `pull_request_target` gate reads those exact files as JSON DATA at an immutable PR SHA and requires an independently authenticated GitHub APPROVED reviewer, exact-head per-row disposition digests and a separate publish label.

This PR must **not** contain a fabricated GitHub approval or local `released=true` receipt. No successful GitHub workflow run alone can confer semantic approval. Until a distinct authorized reviewer signs off, the candidate PR may have green test CI while its `Protected ontology batch reviewer` approval/publish jobs correctly fail closed or be skipped.

## Risks/alternatives

- Source definition lines and target-corpus pins can drift only if upstream revisions are changed; both are frozen and evidence-checked.
- Misleading native-only finality: all ten decisions explicitly articulate *provisional* scope under the existing OLiA lock. Reviewer may choose reject/needs-evidence per row; only accepted ones may be released by downstream protected attestation.
- Mixed BHSA/Syriac cohort is acceptable for testing safe batch processing but **not** interchangeable source semantics. Evidence bindings remain corpus-specific.
- Avoid copying the old complete coverage manifests and changing old 0.4.0 mappings. New candidate files are additive, not a release.
