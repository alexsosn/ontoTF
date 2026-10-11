# Reviewing ontoTF ontology candidate batches

This document explains the **reviewer's** one-time workflow, reused for each new 10–50-row mapping batch. The CLI generates no approval and **never** publishes ontology mappings.

## One-time reviewer setup

The PR author cannot approve their own GitHub PR. Ask the repository owner to invite a **different independent scholarly reviewer** with write, maintain or admin access; a reviewer with only read/triage access will **not** pass ontoTF's authenticated release gate. GitHub App or author-controlled secondary account approval is not implemented or accepted as a shortcut. The reviewer must evaluate the cited original source and its interpretation rather than rubber-stamp the batch's proposals.

Official GitHub UI: [reviewing proposed changes](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews).

## Per-batch workflow

Check out the **exact current candidate PR head** locally, e.g. PR #324 (`gh pr checkout 324`), and install the ontoTF package in your normal isolated environment. Do not execute PR-authored code with privileged GitHub credentials; the separate protected release workflow reads candidate files as data only. Before trusting any local tool, inspect its provenance against protected `main` (the reviewer-handoff tool is intended to be installed from a vetted ontoTF version).

1. Verify the source evidence and candidate scope. For readability, emit the dossier:

   ```bash
   python scripts/mappings/prepare_external_review.py --dossier > review-dossier.md
   ```

   It lists mapping IDs, selectors, original pinned source URI/revision and proposed source-definition line, target (if any), reason and source-bound SHA. **Review the pinned original source and current ontology lock yourself.** Candidate source line citations and `native-only` decisions are not automatically correct.

2. Produce an **unset** worksheet:

   ```bash
   python scripts/mappings/prepare_external_review.py --template > decisions.json
   ```

   Every `"disposition": null` is intentionally invalid for final GitHub approval. Edit each row yourself to precisely one `accept`, `reject` or `needs-evidence`; none is inferred. No missing or extra rows allowed. For PR #324, examine the distinction between BHSA pronoun subtypes and generic Syriac `pron`, and do not infer ontology absence merely from the limited installed OLiA terms.

3. Create the exact structured GitHub review body **after** reviewing and filling every row:

   ```bash
   python scripts/mappings/prepare_external_review.py --review-decisions decisions.json > github-review-body.txt
   ```

   This validates the packet digest, exactly all row IDs and individual explicit dispositions, then copies in the reviewed packet's per-row decision digests. It does **not** authenticate the reviewer, does not invoke GitHub, and does **not** grant release authority. The handoff body has `ontoTF-batch-review-v1` header and JSON, ready to paste; it is NOT a self-authored receipt.

4. Open the **same exact-head** GitHub PR in your **own distinct authorized** account, inspect Files changed, choose **Review changes → Approve** (not Comment), paste the entire body, submit the review. If the PR head or evidence changes, re-run the tools and review again against the new SHA. An ordinary comment, author-supplied JSON, and old-commit approval cannot pass ontoTF's protected gate.

5. Ask a repository maintainer to comment exactly `/ontoTF verify-review` on the labeled PR. With `ontology-batch-review` label, the protected default-branch workflow re-fetches GitHub head/reviews/permissions and independently verifies the review event and all digests; only a separately applied `ontology-batch-publish` label permits the accepted-only handoff job. A CLI-generated body alone is not a signed release; publication remains gated on live GitHub attestation.

## Current tracked acceptance

- Candidate PR: [#324](https://github.com/alexsosn/ontoTF/pull/324), ten unreviewed native POS selectors, full-suite Python 3.10/3.12 green.
- Blocker: [#325](https://github.com/alexsosn/ontoTF/issues/325), provision a truly independent privileged reviewer.
- Protected release integration: [#303](https://github.com/alexsosn/ontoTF/issues/303); no ontology-coverage or released-mapping increase can be claimed until reviewer authentication and accepted-only overlay verification succeed.

The workflow is batch-oriented: one dossier, one review, one final-head verifier, no per-item CI/PR machinery.
