# I-033E5 — candidate evidence across the protected review boundary

Parent #310 / #303 / #300 / #290. Audit at `0890a2a`, 2026-10-11.

## Observed facts

`compile_candidate_batch` already accepts a resource loader. Packet construction
and verification call it without forwarding one. The protected CLI fetches only
a manifest, ledger and packet; its live pass verifies again with installed data.
Thus a source-pinned proposal referencing new evidence cannot reach review.

Actual pinned BHSA `docs/features/sp.md` was fetched by GitHub Contents API at
`4db00e2157915495e1a4d3d57e41223df24775da`; lines 21/30 describe advb/adjv.
Pinned linksyr `data/lib/syriac/word_grammar` at
`3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6` defines these categories at 84/85.
Installed evidence records preserve those source pins and the distinct Syriac
TF target revision `bb0eaa7e21b020a26b7566d2e495da9b1f84a919`. Source pins must
be checked against protected installed evidence, not merely repeated by a PR.
ExtraBiblical enum records have a different evidence shape and do not establish
English definitions; they cannot borrow BHSA's source identity in this pilot.

The installed OLiA RDF SHA256 is
`5983683f27ba524027ffa12a02aead4a115baf9c8933079eabbb4aa71be4e9fd` and Git blob
`5c5e8bda93eaeab2940472a167ff8d3107be8d43`. Adjective has an explicit owl:Class
declaration at line 257. CC-BY-3.0/attribution and the frozen source URI remain
unchanged. Inspect actual RDF declarations, not a candidate's `rdf_type` claim.

`evidence_record_digest` binds source URI/revision, license, normalized content,
kind and identity, but intentionally excludes the optional outer `citation`.
New evidence must put citations/coordinates inside normalized content or this
pilot would allow unreviewed citation changes without invalidating approval.

## Chosen trust boundary

Use a version-2 input manifest referencing at most 32 supplementary evidence JSON
objects under `docs/research/data/batch_review/evidence/`. All reads stay bounded
at exact PR SHA using the existing Content API/blob checksum/no-redirect path.
[GitHub Contents specification](https://docs.github.com/en/rest/repos/contents)
documents ref-pinned content and symlink resolution; path/checksum validation
does not prove a Git file mode. Only JSON data is interpreted, never executable
content, URLs, downloads, imports, or arbitrary corpus files.

Supplementary resource names must be used by that ledger. Never shadow an
installed artifact/evidence identity or supply a new ontology lock. Validate each evidence schema
and canonical digest, reject outer citation, and retain bound source coordinates.
Native source URI/revision/kind/word POS semantics and target revision must match
an installed corpus-specific feature definition from a validated release.
Ontology revision/URI/license/snapshot and original blob/declaration coordinate
must agree with the installed ontology and actual RDF class declaration. The
existing compiler still requires trusted lock membership; new terms/models or
source revisions require a separately reviewed protected pack change.

These checks establish proposal integrity and provenance identity, not the
truth of new native definitions or equivalence to a class. An independently
authenticated reviewer must compare assertions with original source text and
ontology semantics. All packets remain unreviewed; author self-approval and
offline JSON authority remain rejected. Source corpus material is not vendored
by this change; existing metadata/source licensing is preserved.

## Alternatives and limits

Reject loading candidate Python or checking out PR code in the token-bearing
job. Reject fetching source_uri or an ontology API implicitly. Reject accepting
arbitrary candidate locks and self-declared new source pins. Reject changing
historical packet/digest formats just to pass a loader: existing evidence hashes
already bind eligible new records. Reject separate per-term workflows/builders.

Preserve manifest v1 and default packet bytes. New native-only/approximation
templates, lock expansion, overlay publication and actual 10+ new-row production
approval remain unfinished under #303. This slice unblocks data ingestion for
the validated class/POS proposal contract, without claiming production coverage.

## Candidate authoring and protected invocation

Keep one ledger and generated packet per cohort. A manifest using new evidence
names (not copies of immutable profile releases) can contain:

```json
{
  "schema_version": 2,
  "ledger": "src/tfont/resources/batch_pilots/cohort.json",
  "packet": "docs/research/data/generated/i033d/cohort.json",
  "evidence_resources": {
    "resources/profiles/bhsa/batch-candidates/native-sp.json":
      "docs/research/data/batch_review/evidence/native-sp.json"
  }
}
```

Those are example candidate paths, not installed/released resources. Authors can
construct `CandidateEvidenceResources(ledger, evidence_objects)` in memory and
pass it as `resource_loader` to `build_review_packet`/`verify_review_packet`.
Each evidence_objects key is the resource name used by the ledger, and its value
is the parsed evidence object. Put the manifest at the existing fixed
`docs/research/data/batch_review/inputs.json`. Protected CLI `--from-pr-head`
reads every referenced JSON blob at the same exact head and reconstructs that
loader before the live approval pass. Local `--packet/--ledger` continues using
installed resources only. Manifest v1 and frozen default packets remain intact.
