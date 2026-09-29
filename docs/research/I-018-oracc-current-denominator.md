# I-018 research — current ORACC semantic denominator

Issue: #207  
Parent: P-004 #202, Workstream A  
Status: evidence collection in progress

## Question

What is the authoritative current ORACC-TF semantic denominator, given that the
historical R-011 denominator contains only 42 curated items and ORACC-TF has not
yet published its planned 1.0 standalone release?

## Boundary established before inventory

The current ORACC-TF repository is explicitly pre-1.0. Therefore I-018 must not
invent a release tag or treat an older ORACC-TF artifact as current ground
truth.

The current registered build contract at ORACC-TF commit
`f6f189bbd99d72bfdc7044555bd3113aa7b54232` defines one publishable dataset:

`assyrian-royal-inscriptions`

with TF schema version `0.4.0`.

`datasets.toml` selects:

- RIAO 1–5;
- RINAP 1–5 plus RINAP 5 Part 1;
- `riao-teiCorpus` for translations.

The registered builder requires the official pinned TEI archive
`riao-teiCorpus-20241202.zip`, SHA-256
`b793d8920db58908e3a044b7f2d1a204c1ba0784e880007e0cd7941333e841bd`.
A registered build fails closed if that archive is missing or has changed.

The checked-in `data/riao` and `data/rinap` trees are part of the exact Git
commit, so the builder commit pins the extracted JSON source bytes even though
ORACC itself supplies no immutable upstream release/checksum identity.

## Candidate artifact definition

For I-018 research, “current materialized ORACC” means the output of
`oracc_tf.publishing.build_registered_tf()` at the exact commit above, using:

- the checked-in RIAO/RINAP source trees at that commit;
- dataset `assyrian-royal-inscriptions`;
- TF version `0.4.0`;
- the SHA-verified official TEI archive above.

This is a current registered-build candidate, not a claim that ORACC-TF 1.0 has
been released.

## Research job

The I-018 research workflow will:

1. check out ontoTF exact head;
2. sparse-check out ORACC-TF at the exact builder commit, including only
   converter/config plus `data/riao` and `data/rinap`;
3. record Git tree identities for the selected source/config paths;
4. download and SHA-verify the pinned TEI archive;
5. build the registered dataset through the production builder;
6. load the resulting TF with Text-Fabric 13.1.0;
7. inventory every materialized TF node type, node feature and edge feature
   using the established R-005 inventory code;
8. record a deterministic digest over the complete candidate build root,
   including non-TF sidecars, separately from the TF-only feature digest;
9. record the build report and explicit sidecar file set.

The network is research/build-time only. TFont runtime remains corpus-acquisition
free.

## Questions still open

Research must determine from the built candidate:

- exact materialized node types/features/edges, including translation units;
- which materialized items are technical rather than semantic;
- which finite value families are closed by converter semantics rather than
  merely small in this candidate;
- whether the semantic TF schema can honestly be marked `machine-exhaustive`;
- how the non-TF `translation-gaps.json` sidecar affects artifact identity
  without pretending omitted/unqueryable translation units are TF schema
  items;
- the exact current denominator arithmetic and immutable ontoTF resource
  identity.

No production coverage manifest or ontology accounting changes during the
research gate.
