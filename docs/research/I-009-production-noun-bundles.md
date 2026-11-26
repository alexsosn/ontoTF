# I-009: production OLiA Noun bundle evidence

**Issue:** #147  
**Release tracker:** #142  
**Recorded:** 2026-09-11  
**Phase:** research; production resources and loader are intentionally absent from this branch

## Decision

The v0.1.0 semantic slice can be shipped as three independently identifiable corpus profile bundles sharing one exact OLiA Reference Model lock. The semantic concept is common, while the exact native selector is corpus-specific:

```text
http://purl.org/olia/olia.owl#Noun
    -> BHSA:          word.sp in {subs,nmpr}  / value-set-predicate
    -> ETCBC Syriac:  word.sp = subs           / value-predicate
    -> ExtraBiblical: word.sp in {subs,nmpr}   / value-set-predicate
```

This corrects the earlier research assumption that `word.sp=subs` was coextensive with OLiA `Noun` in all three corpora. The independent exactness review in `I-009-noun-exactness-review.md` established that OLiA `CommonNoun` and `ProperNoun` are direct subclasses of `Noun`; BHSA and ExtraBiblical split common/substantive nouns (`subs`) from proper nouns (`nmpr`), while ETCBC Syriac keeps proper nouns inside `sp=subs` and represents properhood separately with `ls=prop`.

The narrow finite-set execution primitive required by that finding is now implemented in merged I-010 (#149/#152). It is one native feature predicate over a finite reviewed set, not generic OR or same-corpus mapping composition. Every selected value in a `value-set-predicate` must be covered by a matching semantic `native-value-present` dependency on the same component/node type/feature.

The profiles target the following exact parent TF payloads:

| corpus | upstream revision | TF version | TF payload digest | parent manifest digest |
|---|---|---|---|---|
| BHSA | `4db00e2157915495e1a4d3d57e41223df24775da` | `2021` | `sha256:5178414e293a743fc98768abcab5b9cb268e14ad56fd2cfbac544ae2869d2e6f` | `sha256:cc2c65cd79b2cb7faf1a34b94feb3cc2d3291e7064cbec942c53b0e05f1b0837` |
| ETCBC Syriac | `bb0eaa7e21b020a26b7566d2e495da9b1f84a919` | `0.9` | `sha256:54a2596d5525f3afb34db0a89d5511e6b8471ce4a93fae4825b22f0945ab62ef` | `sha256:afb5a826b9ebe10cdd4ca23d96e00ee7bf677d06496cfcfcee6bb37d2ecff6c4` |
| ExtraBiblical | `9a56288e6777bad6328856acf055c780e65dd5d9` | `0.2` | `sha256:d0ca9bdf90bfdefe19861c2c68e91071650ed511b8a79270490238b30274aee0` | `sha256:d39fe3f4848cadb14ae5ef453a5150ea6281b2874728566198d7de10d72bec4a` |

The hosted research workflow fetches each exact Git revision, measures the TF payload with the production I-003 identity primitive, recomputes the parent manifest digest, and then repeats the measurement byte-for-byte. These values are measurements of corpus bytes, not repository commit hashes or transport identities.

## 1. Parent component scope

For this first slice the exact parent manifest contains one component per corpus:

```json
{
  "component_id": "<corpus>-tf",
  "kind": "tf-payload",
  "identity_algorithm": "ontotf-tf-files-sha256-v1",
  "content_digest": "sha256:..."
}
```

This is intentionally narrower than the general R-001 parent model. I-008/I-010 execute these mappings through already-loaded TF/Context-Fabric node features only: `otype` establishes the selected node type and `sp` supplies the mapped value or finite selected set. No catalogue, zero-span sidecar, source MQL, documentation page, morphology grammar file, or native adapter outside the TF payload is read during semantic execution.

The documentation and source artifacts below are therefore evidence for the mapping, not semantically addressable runtime parent components. Including them in the parent manifest would make a documentation-only edit invalidate exact corpus compatibility without changing any native value that ontoTF executes.

If a later profile starts reading a native sidecar or catalogue, that artifact enters that profile's parent-component manifest under R-001/I-003. The v0.1 profile must not silently widen its runtime input set without a new reviewed profile version.

## 2. BHSA native semantics

Exact evidence at `ETCBC/bhsa@4db00e2157915495e1a4d3d57e41223df24775da` is unusually strong. `docs/features/sp.md` explicitly states that `sp` is the part-of-speech feature, applies to `word` and `lex`, and defines at least:

```text
subs -> noun
nmpr -> proper noun
```

The exact OLiA payload used by this release has both `CommonNoun` and `ProperNoun` as direct subclasses of `Noun`. Therefore a BHSA exact projection to the OLiA superclass cannot select only `subs`: it would systematically omit the independently encoded proper-noun class. The v0.1 executable binding is consequently the single word-level finite-set predicate:

```text
word.sp in {subs,nmpr}
execution_shape=value-set-predicate
```

with separate semantic `native-value-present` dependencies for `subs` and `nmpr`.

The exact TF payload at `tf/2021` is the payload whose identity is recorded above. The production evidence record should bind the immutable documentation source revision and reviewed semantic statement to the mapping; it should not copy a test-fixture `example.org` URL.

The executable binding deliberately narrows the documented `word`/`lex` applicability to word nodes, because the v0.1 acceptance query and cross-corpus comparison operate on word nodes.

## 3. ETCBC Syriac native semantics

Exact evidence at `ETCBC/syriac@bb0eaa7e21b020a26b7566d2e495da9b1f84a919` establishes:

- the repository is the ETCBC Syriac Corpus;
- dataset version `0.9` is based on its morphologically parsed source;
- the README lists `sp` as a word-level **part of speech** feature;
- the exact `tf/0.9/sp.tf` payload contains `subs` values.

The ETCBC Syriac grammar source in `ETCBC/linksyr@3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6`, `data/lib/syriac/word_grammar`, independently documents the Syriac tag semantics:

```text
sp: "part of speech" =
    ...
    subs: "substantive",
    verb: "verb"
```

and uses `sp=subs` in nominal rules. The same exact source family also contains proper-noun lexicon entries encoded as `sp=subs:ls=prop`. That is the crucial difference from BHSA/ExtraBiblical: properhood does not form a separate `sp=nmpr` exclusion from the Syriac substantive class.

Accordingly the reviewed exact v0.1 selector remains:

```text
word.sp = subs
execution_shape=value-predicate
```

That grammar artifact is scholarly/native semantic evidence; it is not part of the tested runtime parent component set. Production evidence must record both the exact supported Syriac corpus revision and the exact grammar evidence revision rather than infer meaning from a code shared with BHSA.

`substantive` is the nominal POS category used here and is the reviewed native category proposed for exact projection to OLiA `Noun`. The production review must explicitly authorize that projection; ontoTF must not generalize all ETCBC `subs` labels automatically.

## 4. ExtraBiblical native semantics

Exact `ETCBC/extrabiblical@9a56288e6777bad6328856acf055c780e65dd5d9` evidence establishes:

- the repository describes ExtraBiblical as conversion of ETCBC-encoded MQL material to Text-Fabric;
- it explicitly places the resource in the BHSA/ETCBC data family and points to BHSA as core data and feature documentation;
- the conversion notebook reports the MQL `part_of_speech_t` enumeration and the generated `sp` string feature;
- exact `tf/0.2/sp.tf` contains both `subs` and `nmpr` as native values;
- exact source bytes are preserved in `source/0.2/extraBiblical.mql.bz2`.

The hosted research gate opens that exact compressed MQL source and verifies that word `sp` is typed as `part_of_speech_t`, with `subs=2` and `nmpr=3`. Together with the explicit ETCBC/BHSA conversion provenance and BHSA family feature documentation, this supports the same common/proper split independently observed in the generated TF payload.

Because OLiA `Noun` subsumes both common and proper noun subclasses, the exact ExtraBiblical v0.1 selector is therefore:

```text
word.sp in {subs,nmpr}
execution_shape=value-set-predicate
```

with semantic `native-value-present` dependencies for each selected value.

This remains a reviewed corpus-specific conclusion, not a rule that identical ETCBC selector spellings always imply semantic identity. Production evidence must retain the exact ExtraBiblical source/conversion provenance rather than borrowing BHSA semantics without citation.

## 5. OLiA lock

The common pivot is the OLiA Reference Model, not one of the corpus-specific annotation models under `owl/stable`.

Exact ontology source:

```text
repository: acoli-repo/olia
revision: d3bd4f1aef9047b33186bfb2a1795401f3f1a4a6
path: owl/core/olia.owl
term: http://purl.org/olia/olia.owl#Noun
content digest: sha256:5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd
license: CC-BY-3.0
```

The hosted research script parses the exact XML payload and fails unless the canonical `Noun` class resolves to the IRI above and both `CommonNoun` and `ProperNoun` occur among its direct subclasses. OLiA's exact-revision documentation identifies `http://purl.org/olia/olia.owl` as the morphosyntax/morphology/syntax Reference Model and states that, unless otherwise marked, the ontologies are released under CC-BY 3.0. `LICENSE.data` at the same revision contains the Attribution 3.0 Unported license text.

The production lock should be one shared lock resource used by all three profile bundles. It must carry the accepted I-002/R-015 semantic lock fields, including the exact source revision, content digest and `terms_used=[http://purl.org/olia/olia.owl#Noun]`. The plan must freeze the remaining schema values such as release label and support tier from project conventions rather than inventing another lock dialect.

Redistributing the exact ontology snapshot in the ontoTF wheel is permitted under CC-BY 3.0 provided attribution/license obligations are preserved. Corpus TF payloads are not redistributed by ontoTF.

## 6. Corpus licences and redistribution boundary

The supported Syriac and ExtraBiblical repositories document CC-BY-NC 4.0 data licences. ontoTF does not need to ship their TF data to ship this semantic layer. The production package should contain mapping/profile metadata, parent content digests, immutable evidence records and the redistributable OLiA snapshot; corpus acquisition remains outside ontoTF.

A content digest of a corpus payload and an immutable source citation are not a bundled copy of the corpus. Release documentation should still retain the upstream corpus attribution and licence reference so users can understand the dependency and acquisition constraints.

## 7. Evidence and review provenance

The current I-005 fixtures contain deliberately synthetic values such as `example.org`, `fixture-v1` and `reviewer:i005-fixture`. None may appear in production resources.

The existing production schemas already provide the required primitives:

- evidence records can bind an immutable `source_uri`, `source_revision`, content mode, digest, licence reference and citation;
- mapping/projection review records bind a real `reviewed_mapping_digest` to a review status, reviewer identity, timestamp, review source and method.

No signature, organization certificate, MAC or remote trust service is needed for v0.1. The mapping digest itself is deterministic content identity, not authentication.

A production review record cannot be finalized before the production mapping/projection digest exists. The implementation plan should therefore create the mapping source first, compute its semantic digest, run a logically independent evidence review of that exact digest, and only then commit the review binding using the actual review source and reviewer identity. It must not manufacture a reviewer or backdate a review in order to make validation pass.

For evidence that is a normalized scholarly conclusion rather than a byte-for-byte external document, use the existing `normalized-record` mode and bind its `content_digest` with the accepted ontoTF evidence digest primitive. External immutable source bytes may use `external-payload` where the production validator contract supports the intended binding.

## 8. Distribution and package layout boundary

R-001 already selected central ontoTF source with independently versioned per-corpus semantic sidecars. I-009 should implement the smallest in-package realization of that decision, not another package manager.

The existing F-002 packaging solution already ships runtime JSON resources under `src/ontotf/...` as setuptools package data and resolves them with `importlib.resources`. I-009 should reuse that mechanism for profile resources and add an isolated wheel-install regression, rather than access repository-relative paths.

The minimal v0.1 distribution unit is therefore:

- three separate corpus profile resource trees, each with its own profile ID/version, exact parent manifest, mapping and corpus-specific evidence;
- one shared exact OLiA lock/snapshot/attribution resource;
- one narrow loader API that locates these resources through `importlib.resources` and constructs the existing `SemanticSourceBundle` objects;
- no registry, downloader, dependency solver, corpus materializer or Agora-specific protocol inside ontoTF.

The plan gate should freeze exact filenames and package-data globs. Profile independence must be preserved even if all three resources happen to ship inside the first `ontotf` wheel.

## 9. Parent upgrades

A new upstream commit or TF payload is not silently covered by a v0.1 exact profile.

Runtime behavior remains:

```text
same measured parent component identity
    -> eligible for verified-exact evaluation
changed parent identity
    -> never authorized by version/repository name alone
    -> validate complete declared dependency closure if compatible-mode support is intentionally supplied
    -> otherwise fail closed and require a reviewed profile update
```

For the first release it is acceptable for the three shipped production profiles to advertise only the measured exact parent target. A later reviewed profile version may add compatible parent evidence. No nearest-version or same-tag fallback should be introduced in I-009.

## 10. Plan constraints

The implementation plan may proceed only after fresh logically independent research review of this branch. It must preserve these constraints:

1. production resources are package resources and load offline;
2. each corpus profile remains independently identifiable/versioned;
3. all three use the same exact OLiA Noun lock but independent native evidence;
4. exact parent identities above replace fixture hashes;
5. exact execution is heterogeneous but semantically common: BHSA and ExtraBiblical use one `value-set-predicate` over canonical `{nmpr,subs}`, while Syriac uses scalar `value-predicate` `subs`;
6. each selected finite-set value has its own semantic `native-value-present` dependency; the scalar Syriac selector has the corresponding `subs` dependency;
7. review provenance is tied to an actual review of the final semantic digest;
8. no corpus bytes are bundled;
9. no downloader, package manager, generic ontology dereference or certification machinery is introduced;
10. parent drift fails closed;
11. clean wheel tests prove resources are present without a source checkout;
12. the implementation reuses merged I-010 rather than reopening R-018/general boolean composition.

## Research evidence gate

The hosted `I-009 research parent identities` workflow is normative evidence for the measured identities on the reviewed research head. It checks exact Git revisions, corpus semantic evidence assertions for both `subs` and the corpus-specific proper-noun encoding, the OLiA `Noun` hierarchy and licence boundary, deterministic parent/ontology digests, and a repeated identical measurement. The final research review must inspect the exact workflow head rather than relying on values copied into this document alone.
