# Reviewing ontoTF batches in a single-agent repository

ontoTF has **one development/review agent and one GitHub account**. It cannot use GitHub's `Approve` action on its own PR. The repository therefore supports **two distinct, auditable modes** without inventing a second reviewer.

## Single-agent mode (explicit opt-in)

For a 10–50-row source-grounded batch, the same GitHub author completes **two logically separate adversarial passes** on the exact same candidate commit:

1. **Challenge first.** Examine every proposed category against the pinned original corpus source, consider alternate ontology targets and attempted counterexamples. Post a structured `ontoTF-adversarial-review-v1` report as a GitHub **COMMENTED pull-request review**, not an ordinary issue comment. Each row needs a separately written `challenge` and `source_check` containing the original source revision and selector. Do not copy the proposal rationale as the counterargument.
2. **Decide second.** Re-evaluate the original source, code, tests, uncertainties and previous skeptical findings without assuming the proposal is correct. Explicitly select `accept`, `reject` or `needs-evidence` for **every** row. Post the `ontoTF-batch-review-v1` body as a **second GitHub COMMENTED PR review** at that exact SHA. The data code never preselects `accept`.

GitHub review IDs/times and commit SHAs establish two distinct events; their existence **does not prove cognitive independence** or a separate reviewer. Protected-main CI only verifies the evidence, chronology, same real author, GitHub permissions, canonical packet/row commitments and current PR head, and records `single-agent-adversarial` provenance rather than claiming external independent approval. The existing external distinct-user `APPROVED` path remains available for projects that actually have such people, but is not required for ontoTF.

### Trusted tools and candidate data in two directories

Run vetted policy and helper code from current protected `main`; the candidate PR checkout contains **untrusted JSON data**, not code to execute:

```bash
git clone https://github.com/alexsosn/ontoTF.git ontoTF-trusted
python -m pip install -e ./ontoTF-trusted
git clone https://github.com/alexsosn/ontoTF.git ontoTF-candidate
cd ontoTF-candidate
gh pr checkout 324
cd ../ontoTF-trusted
```

Confirm the candidate checkout's exact HEAD SHA matches the GitHub PR.

Produce a readable dossier, with per-row original source claims and digest:

```bash
python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --dossier > review-dossier.md
```

In a separate skeptical pass, create an **unfilled** challenge worksheet:

```bash
python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --challenge-template > challenges.json
```

Every `challenge`, `source_check` and overall `summary` initially equals `null`. Research and fill each item individually; the validator requires a nontrivial counterargument, the exact native selector, and its source revision. Format only your *completed* report:

```bash
python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --review-challenges challenges.json > adversarial-review.txt
gh pr review 324 --repo alexsosn/ontoTF --comment --body-file adversarial-review.txt
```

Perform the second pass, independently judging each challenge, and create the (also **unset**) decision worksheet:

```bash
python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --template > decisions.json
```

Manually select `accept`, `reject` or `needs-evidence` for each candidate; do not infer an exact OLiA mapping or permanent lack of one merely from its source gloss.

```bash
python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --review-decisions decisions.json > decision-review.txt
gh pr review 324 --repo alexsosn/ontoTF --comment --body-file decision-review.txt
```

These are **GitHub PR COMMENTED reviews**; a simple `gh pr comment` or a GitHub issue comment will not count as either reviewed event. After the two distinct ordered review events, add both `ontology-batch-review` and `ontology-single-agent-review` labels to the candidate PR. The first label already exists on #324. To request a fresh protected run, comment exactly `/ontoTF verify-review` on the PR as a maintainer; this command **triggers re-evaluation, never counts as approval**. On success, separately add `ontology-batch-publish` only to request an accepted-only pack (10–50 accepted decisions in the current handoff implementation).

The gate re-fetches the current PR SHA, GitHub-authenticated review events, permissions, and all immutable ledger/packet/source data using protected `main` code. No PR code executes with a release token. A stale review, missing challenge, missing decision, unauthorized author, missing opt-in label, or contradictory current event **fails closed**. Any PR head change requires both passes to be redone.

## Distinct-human mode (optional for other deployments)

Without `ontology-single-agent-review`, the original external review gate still requires a different privileged GitHub `User` to submit an exact-head `APPROVED` review with all `ontoTF-batch-review-v1` per-row decisions. GitHub prevents PR author self-approval. Never simulate an external reviewer by renaming the author account, inventing a service principal or writing reviewer JSON locally.

## Candidate #324 / remaining release work

[PR #324](https://github.com/alexsosn/ontoTF/pull/324) holds ten **unreviewed** BHSA/Syriac POS candidates; nine BHSA original definitions are from pinned `sp.md` lines 17 and 22–29, and Syriac general `pron` from pinned `word_grammar` line 91. `native-only` is a scoped claim under today's OLiA lock, not proof that no corresponding ontology concept exists. The review process must independently challenge those ten decisions.

[#325](https://github.com/alexsosn/ontoTF/issues/325) records the architecture correction from second-person to single-agent review; [#303](https://github.com/alexsosn/ontoTF/issues/303) covers accepted-only protected handoff, attestation and release parity. CI/review success does **not** itself increase installed ontology coverage: an actual attested release artifact and registry update must be verified.
