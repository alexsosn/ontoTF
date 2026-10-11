# I-033E9 — sparse acceptance within a fully adjudicated batch (#329)

## Observed evidence

At main c4f0be1, `build_overlay_handoff` and its integrity validator require ten accepted rows, although the single-agent review gate requires ten **proposed** source-bound rows. The real #324 packet has nine BHSA POS selectors (`art`, `prep`, `conj`, `prps`, `prde`, `prin`, `intj`, `nega`, `inrg`) and Syriac `pron`. Existing `tests/i033e/test_overlay_handoff.py::cohort` reproduces these original-source definitions at BHSA 4db00e2157915495e1a4d3d57e41223df24775da and linksyr 3ba42432b0ed95c1ad65eb06865c3a5f7175f8b6, with the independent TF Syriac target pin preserved. Reuse the frozen native and OLiA evidence documented in I-033E6/E8 and #324; this contract change adds no scholarly equivalence or ontology terms.

The assembler already filters mappings, dependencies and assignments by accepted IDs; the validator already checks exact correspondence to accepted IDs. The minimum alone prevents an otherwise valid nine-row sparse handoff after one rejection. Relaxing review completeness would permit unadjudicated assertions; relaxing the accepted minimum while retaining a ten-row proposal and complete adjudication removes that incentive.

The live CLI assembles, validates and checks authority again before exclusive file creation. The workflow unconditionally attests/uploads the fixed file after a successful CLI invocation. Therefore a zero-accept audit requires both CLI and workflow changes: success must produce the review observation, no mapping artifact, and no signing/upload step. It must still recheck live authority rather than turn zero acceptance into a stale-review bypass.

## Alternatives and recommendation

1. Retain ten accepts: rejects useful sparse outcomes and pressures inflated acceptance. Reject.
2. Allow fewer than ten proposed rows: reintroduces per-item ceremonies. Reject for this protected publishing pilot.
3. Fully adjudicate 10–50 proposed rows; publish 1–50 accepted rows; zero accepts yields audit only. Adopt. All rejected/needs-evidence rows remain in the bound review observation but contribute no mapping, dependency or coverage assignment. Evidence may retain other source definitions as evidence context, without creating mappings for them.

Historical profile 0.4.0, coverage denominators and TF runtime remain unchanged. A native-only mapping has zero shared targets and is not evidence that no ontology concept could ever apply. No new external dependencies, ontology identifiers, licenses or fetch capabilities are introduced.

## Remaining #329 work

Versioned promotion of an inherited native-only selector is a separate unresolved architectural mechanism. The handoff is not yet a trusted overlay registry or installed release loader (#303/#300). Do not remove inherited-selector protections here or invent supersession semantics before that consumer contract is designed. Historical BHSA stem dispositions are accounting records, not automatically Mapping v2 records. This slice addresses partial acceptance only; #329 stays open for evidence-backed promotion design and seven-model consumer validation.
