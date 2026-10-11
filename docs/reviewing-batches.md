# Reviewing ontoTF ontology candidate batches

The development agent performs all scholarly and code reviews. No second authorized GitHub account is required. A separately instantiated non-author review context must challenge every semantic assertion using original pinned corpus definitions, ontology specifications, and conservative alternatives. The existing repository account records this work; authenticated events are an audit trail, not proof of cognitive independence or scholarly truth.

## Trusted tools, candidate data

Install ontoTF from vetted protected main in an isolated environment. Keep the exact candidate PR checkout in a separate directory. Run all commands from the trusted repository root with `--root ../ontoTF-candidate`. Never import or execute candidate Python to perform privileged verification.

```bash
python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --dossier > dossier.md
python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --challenge-template > challenges.json
```

The dossier is explicitly unreviewed. Inspect its primary source URI, immutable revision, source definition and line, proposed ontology target and rationale. Native-only proposals scoped to the installed ontology lock do not prove absence of terms in the broader ontology.

## Challenge, adjudicate, verify

1. Arrange a non-author skeptical review context and give it the exact PR SHA, packet, source evidence, research/plan and ontology lock. It should try to disprove each proposed assertion and inspect the original sources. Record the reviewer context identity, methodology, findings, uncertainties and resolution in the report summary. Fill every worksheet challenge and source check from the actual completed review. Null entries deliberately cannot pass validation. Report text length and citation checks only enforce audit completeness; they cannot assess reasoning quality.
2. Render the completed report:

   ```bash
   python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --review-challenges challenges.json > challenge-body.txt
   ```

   Submit it under the existing repository account as a GitHub PR review with event **COMMENT** and an explicit exact `commit_id`. Ordinary issue comments are insufficient. The `ontoTF-adversarial-review-v1` report binds every row and its decision digest.
3. Resolve material findings with code/data changes and repeat independent review on the new head. After a completed challenge pass at the final head, create the unset decision worksheet and fill each disposition explicitly as accept, reject or needs-evidence, grounded in the review:

   ```bash
   python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --template > decisions.json
   python -m scripts.mappings.prepare_external_review --root ../ontoTF-candidate --review-decisions decisions.json > decision-body.txt
   ```

   Submit this as a **later separate COMMENT review** under the same account at the same exact SHA. Never submit an APPROVE event pretending to be another reviewer. Reject/needs-evidence rows cannot become production mappings.
4. Apply `ontology-batch-review` and `ontology-single-agent-review`. A maintainer comment `/ontoTF verify-review` requests the protected default-branch workflow to read candidate JSON at exact head and freshly read both GitHub reviews, author permissions, labels and PR state. It rejects missing, stale, dismissed, incomplete or changed review events. Any later author review invalidates the pair; perform fresh passes if necessary.
5. Publication additionally requires `ontology-batch-publish`, at least ten accepted rows, unchanged installed bases/coverage/ontology lock, handoff integrity checks and a fresh live recheck. The workflow may sign an accepted-only handoff; registry installation remains a separate validated integration step. Passing a local worksheet validator grants no release authority.

GitHub documents [COMMENT events and exact commit IDs](https://docs.github.com/en/rest/pulls/reviews#create-a-review-for-a-pull-request). The default legacy route without `ontology-single-agent-review` still requires a distinct privileged APPROVED review, for compatibility; it is optional and is not a prerequisite for this development loop.

Current candidate [#324](https://github.com/alexsosn/ontoTF/pull/324) contains ten source-bound proposals. Policy integration is tracked in [#325](https://github.com/alexsosn/ontoTF/issues/325); accepted-only release/registry/wheel integration remains [#303](https://github.com/alexsosn/ontoTF/issues/303). Report exact shared-target mappings separately from reviewed native-only dispositions and unresolved items.
