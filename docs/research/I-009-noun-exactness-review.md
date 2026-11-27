# I-009 adversarial review: OLiA Noun exactness correction

**Recorded:** 2026-09-11  
**Review role:** logically independent semantic challenge of the I-009 production premise  
**Original result:** **BLOCKER on the original `word.sp=subs -> olia:Noun` exact claim; parent/lock/evidence measurements remain valid**  
**Resolution status:** the blocker is resolved by merged I-010 (#149/#152); I-009 research may proceed with heterogeneous native selectors

## Finding

The original I-009 research premise copied the R-011 pilot statement that OLiA `Noun` is exact in BHSA, Syriac and ExtraBiblical through the same native predicate `word.sp=subs`. Production evidence falsifies that simplification.

R-002 defines ontoTF `assessment=exact` as semantic coextensiveness. Under that contract, the same string selector cannot be called exact in all three corpora.

## 1. Exact OLiA hierarchy

The pinned OLiA Reference Model is:

```text
acoli-repo/olia@d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6
owl/core/olia.owl
```

On this exact payload, both:

```text
http://purl.org/olia/olia.owl#CommonNoun
http://purl.org/olia/olia.owl#ProperNoun
```

are direct subclasses of:

```text
http://purl.org/olia/olia.owl#Noun
```

The hosted I-009 measurement parses the exact OWL payload and fails unless both subclass relations are present. The generated OLiA tree at the same revision independently exposes the same Noun hierarchy.

Therefore an exact native selector for `olia:Noun` must cover both ordinary/common nouns and proper nouns when the native tagset distinguishes them.

## 2. BHSA partitions the category

At the exact supported BHSA revision, `docs/features/sp.md` defines:

```text
subs -> noun
nmpr -> proper noun
```

as separate `sp` values.

Consequences:

- `word.sp=subs -> olia:Noun` is **not exact** under R-002, because the target includes proper nouns while the native selector excludes `sp=nmpr`;
- interpreted directionally from native to target, `olia:Noun` is broader than `sp=subs`;
- `word.sp in {subs,nmpr}` is the minimal native selector that matches the broad OLiA Noun category evidenced by this tagset.

The original I-008 single-value executor could not express that finite union. Merged I-010 adds the required narrow finite-set primitive without generic boolean composition.

## 3. ExtraBiblical has the same split

The exact ExtraBiblical MQL source declares `part_of_speech_t` with separate members:

```text
subs = 2
nmpr = 3
```

and the word `sp` feature is typed as this enumeration. The exact generated TF `sp` payload contains both values. ExtraBiblical's README explicitly places the corpus in the BHSA family and points to BHSA as core data and feature documentation.

Therefore the same production conclusion applies:

```text
ExtraBiblical olia:Noun
    -> word.sp in {subs,nmpr}
```

not `word.sp=subs` alone.

## 4. Syriac does not use the same partition

The exact Syriac grammar source at:

```text
ETCBC/linksyr@3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6
data/lib/syriac/word_grammar
```

defines:

```text
sp: part of speech
subs: substantive
```

while proper-noun status is separately represented in lexical set:

```text
ls=prop -> proper noun
```

The exact source lexicon contains proper-name entries with the combination:

```text
sp=subs:ls=prop
```

Thus, unlike BHSA/ExtraBiblical, Syriac proper nouns are not excluded from the `sp=subs` POS category. For the broad noun-class request, the simple Syriac selector remains `word.sp=subs`; `olia:CommonNoun` would instead require excluding the `ls=prop` subset and is outside this v0.1 slice.

A production review must still bind the final Syriac projection digest, but the evidence rules out the tempting cross-corpus rewrite `subs -> CommonNoun` as a universal fix.

## 5. Corrected three-corpus exact execution shape

The narrow corrected release request is still OLiA Noun, but the corpus-native selectors differ:

| corpus | exact native selector for reviewed OLiA Noun slice |
|---|---|
| BHSA | `word.sp in {subs,nmpr}` |
| Syriac | `word.sp=subs` |
| ExtraBiblical | `word.sp in {subs,nmpr}` |

This preserves the actual purpose of ontoTF: one semantic request may compile to different reviewed native plans.

Changing the release showcase to a different category merely to preserve an accidentally uniform selector would hide the interoperability problem rather than demonstrate it.

## 6. Merged runtime amendment

The required executor extension is a **finite value-set predicate on one feature**, not generic boolean planning and not R-018 same-corpus multi-binding composition.

The production Noun bindings use the shape:

```json
{
  "component_id": "bhsa-tf",
  "node_type": "word",
  "feature": "sp",
  "values": ["nmpr", "subs"],
  "execution_shape": "value-set-predicate"
}
```

Merged I-010 generalized this narrow primitive slightly beyond the original review sketch: the schema accepts one or more unique JSON-scalar selected values, canonicalizes their order, and keeps scalar `value-predicate` as the existing single-value form. The production BHSA/ExtraBiblical Noun profiles nevertheless use exactly the two reviewed string values `nmpr` and `subs`.

Execution is the deterministic set union of the loaded feature selectors for the reviewed values, followed by exact node-type filtering.

Accepted guardrails from I-010 now include:

- non-empty unique JSON-scalar `values` with canonical value ordering;
- one feature, one node type, one component only;
- each selected native value must be covered by the profile's semantic `native-value-present` dependency closure; no new dependency kind is used;
- source value order cannot change semantic digest, native-binding identity, plan fingerprint, resolution fingerprint, or result nodes;
- each selector result is validated before cross-value union; overlap between different values is deduplicated deterministically;
- feature disappearance, failed prerequisites, malformed binding state or selector failure still fails closed;
- scalar `value-predicate` semantics remain unchanged;
- no query strings, `S.search`, arbitrary AND/OR/NOT tree, path composition, approximation or caller-supplied execution authority.

### Do not reuse `closed_values`

The existing `native_binding.closed_values` field has a different accepted meaning. `semantic_child_validation.validate_native_semantics()` treats it as a **complete reviewed value-domain claim** and requires a matching `value-domain` dependency with `domain_semantics=closed-reviewed` and evidence.

Using `closed_values=[subs,nmpr]` to mean "select these two values" would corrupt that contract. I-010 therefore uses the distinct `values` + `value-set-predicate` shape.

## 7. Scope assessment

This amendment is smaller and semantically safer than either alternative:

- keeping `sp=subs` and falsely labelling BHSA/ExtraBiblical exact;
- switching the common target to `olia:CommonNoun`, which makes Syriac require a negative/conjunctive `ls != prop` predicate;
- replacing Noun with a different demo term solely to avoid a heterogeneous native plan.

The finite value-set primitive is generically useful without creating a generic query language: many tagsets encode one common semantic class as several mutually exclusive native enum values.

## 8. Effect on I-009

The following I-009 research products remain valid and reusable unchanged:

- all three exact parent TF payload digests;
- all three parent manifest digests;
- the exact OLiA snapshot/revision/digest/license;
- package/distribution conclusions;
- corpus licence boundaries;
- evidence and review-provenance requirements.

The following statements are superseded:

- any claim that `word.sp=subs -> olia:Noun` is exact in BHSA or ExtraBiblical;
- the original main research document's one-selector decision line;
- any implementation plan that assumes all three production bundles have identical native execution bindings.

The runtime precondition that originally blocked I-009 is now satisfied by merged I-010. I-009 planning may therefore proceed only from the corrected selectors above and must reuse the merged finite-set contract rather than inventing local composition machinery.

## Review disposition

**Historical FAIL / BLOCKER on the original exact mapping premise.**

**PASS on the corrected semantic conclusion:** BHSA/ExtraBiblical use `word.sp in {subs,nmpr}`; Syriac uses `word.sp=subs`.

**PASS on the measured parent identities, OLiA lock identity, evidence provenance, redistribution boundary and package-resource direction.**

The blocker is resolved by merged I-010. No production mapping or review record may use the superseded `sp=subs`-for-all-three premise.
