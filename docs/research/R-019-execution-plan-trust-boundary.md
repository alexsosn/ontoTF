# R-019 research — execution-plan trust boundary beyond deterministic fingerprints

**Issue:** #134  
**Baseline:** `main` `f0a82fce8d69695a21b5d64e74f9666c1352cd7e`  
**Type:** architecture / runtime trust boundary

## Question

What must a future Context-Fabric executor trust before it executes an `ExactNativePlan`, given that I-006 intentionally uses public deterministic JCS/SHA-256 fingerprints for reproducibility and cache identity rather than producer authentication?

## Standards evidence

RFC 8785 defines JCS as a deterministic, hashable representation of JSON. It explicitly treats canonicalization as an input to cryptographic operations such as hashing and signing; when signatures are used, signature verification remains a separate step. Canonicalization therefore provides reproducible bytes, not producer authenticity by itself.

NIST terminology draws the same boundary. A cryptographic hash value is the result of applying a hash function to data. By contrast, a MAC is keyed and can provide data-origin authentication plus integrity, while a digital signature can provide origin authenticity and integrity. A public unkeyed SHA-256 digest therefore cannot prove that ontoTF, I-006, I-007, an MCP server, or any particular process produced an object.

Sources consulted:

- RFC 8785, *JSON Canonicalization Scheme (JCS)*, RFC Editor: https://www.rfc-editor.org/rfc/rfc8785.html
- NIST CSRC, *Cryptographic Hash Value*: https://csrc.nist.gov/glossary/term/cryptographic_hash_value
- NIST CSRC, *Message Authentication Code (MAC)*: https://csrc.nist.gov/glossary/term/message_authentication_code
- NIST CSRC, *Digital Signature*: https://csrc.nist.gov/glossary/term/digital_signature

## Threat and trust model

The execution handoff must distinguish three environments.

### 1. Same-process trusted composition

A caller invokes the trusted ontoTF compiler/resolver/runtime-evaluator in one process and passes the resulting immutable values directly to a trusted executor. The relevant threat is accidental stale/mismatched state or API misuse, not hostile object forgery inside the trusted process.

In this environment, signatures or MACs add no useful security boundary: code that can access the same process can generally construct Python objects and may also reach any in-process signing secret. The executor should instead revalidate the plan against the current trusted `CompiledSemanticIR` and trusted I-007 prerequisite attestation immediately before execution.

### 2. Serialized but locally revalidated handoff

A plan crosses a persistence, plugin, MCP, queue, cache, or process boundary and later returns as serialized data. The serialized object is untrusted regardless of whether its supplied public fingerprint recomputes successfully.

The receiving executor must reconstruct only through a strict parser/validator and then establish authorization from current trusted state: current compiled IR plus a current trusted I-007 runtime prerequisite result. The supplied plan is evidence/a cache hint, not execution authority.

The safest v1 behavior is to re-resolve from the requested semantic key/corpus set against that current trusted state, or equivalently perform a complete plan-equivalence revalidation against what the trusted resolver would produce. Re-resolution is simpler and less likely to duplicate resolver invariants.

### 3. Remote producer whose identity must itself be trusted

If a future architecture requires an executor to accept a plan produced by another security principal without independently re-establishing its semantic/runtime state, public hashes are insufficient. That architecture needs an authenticated channel or an authenticated object mechanism such as a MAC/signature plus key/trust management and replay/freshness policy.

No current ontoTF requirement establishes this need. Introducing keys now would add deployment, rotation, revocation, secret-storage, and cross-plugin trust complexity without solving the more immediate semantic freshness problem. Therefore signatures/MACs are not part of the recommended v1 handoff.

## What I-006 fingerprints do prove

When recomputed from a value under the documented algorithm, the I-006 JCS/SHA-256 fingerprints provide:

- deterministic content identity for the fields included in the projection;
- stable cache/deduplication keys;
- reproducible comparison across implementations that honor the same contract;
- evidence that two projections with the same digest are intended to represent the same canonical projected bytes, subject to the normal security assumptions of SHA-256.

They do **not** prove:

- which process, user, plugin, MCP server, or library instance produced the value;
- that the value ever passed through `semantic_resolve()`;
- that an I-007 evaluator observed a real current corpus;
- that the plan is currently executable;
- that the caller is authorized to execute it;
- freshness or replay resistance.

Documentation and API naming must never call these hashes signatures, attestations of producer identity, authorization tokens, or proof that an object came from ontoTF.

## Recommended execution authorization path

For the first production Context-Fabric execution handoff, use **state-based revalidation**, not object-origin authentication.

A trusted executor should require all of the following at execution time:

1. a current trusted `CompiledSemanticIR` selected by the host/runtime;
2. a current runtime prerequisite result produced by the trusted I-007 evaluator from the actually selected materialized corpus;
3. an exact semantic request or a candidate plan tied to that request;
4. successful I-006 resolution/revalidation against (1) and (2);
5. equality of the execution-relevant plan fields with the freshly authorized plan, including variant, profile release fingerprint, parent identity, prerequisite fingerprint/source contract, mapping/projection IDs and semantic digests, reviewed authority, ontology lock/bundle identity, native dependencies, native binding identity and native execution binding;
6. any host/user/session authorization required to access the corpus, enforced outside semantic fingerprints.

For an in-process plan directly returned by `semantic_resolve()`, step 4 may be implemented as a lightweight executor-side revalidation helper rather than serializing and re-resolving. It must nevertheless derive trust from current IR + current I-007 state, not from Python object identity or the public plan fingerprint.

For a serialized/deserialized plan, the preferred v1 rule is stricter: **re-resolve and compare, or ignore the supplied plan and execute only the freshly resolved plan**. A matching `plan_fingerprint` alone is never sufficient.

## Relationship to I-007

I-007 should produce deterministic resolver-facing prerequisite state from observed corpus/runtime facts, but its public deterministic fingerprint has the same limitation: it identifies content; it does not authenticate the evaluator that produced it.

Inside one trusted host process, the trust root is the host's invocation of the I-007 evaluator over the selected corpus and its direct handoff of the result. If the prerequisite result crosses an untrusted process boundary, the receiver must either recompute/re-establish it locally or rely on a separately authenticated transport/object mechanism.

`prerequisite_source_contract` identifies the evaluator contract/version or source semantics used for the result. It is necessary for deterministic provenance and cache invalidation, but it is not an authentication credential.

## Authorization is separate from semantic identity

MCP user identity, session IDs, filesystem permissions, corpus ACLs and service authorization should not enter I-006 semantic or plan fingerprints. They are volatile deployment facts and would destroy reproducibility of semantic identities.

A later executor may require a separate host authorization context before touching Context-Fabric or filesystem state. That check should happen alongside execution authorization, but outside the semantic digest projections.

## Freshness and replay

Revalidation against current IR and freshly established I-007 state naturally rejects stale plans when the parent manifest, profile release, dependency results, ontology bundle, resolver contract or other execution-relevant state changes.

A timestamp in a plan would not solve authenticity and would make deterministic semantic identity volatile. If a remote authenticated handoff is introduced later, replay policy belongs to that authenticated channel/capability layer and may use expirations/nonces there without contaminating semantic fingerprints.

## Consequences for current work

### I-006

No authenticity mechanism is required in I-006. Its fingerprints should remain deterministic public identities. I-006 should continue to validate internal/release/prerequisite coherence fail-closed and avoid language implying producer authentication.

### I-007

I-007 should define a deterministic prerequisite/report identity and a trusted evaluator API. It must state explicitly that a reconstructed public report object is not trusted merely because its fingerprint recomputes. Execution authority arises from the trusted evaluator invocation or later authenticated boundary.

### Context-Fabric execution ticket

The eventual executor must have an explicit authorization/revalidation gate before any query or corpus read. It should consume current trusted IR + current trusted I-007 state and either freshly resolve the semantic request or fully compare a supplied plan to a fresh resolver result. It must reject a hand-constructed lookalike plan even if the public digest is internally consistent.

If future deployment requires accepting remote pre-resolved plans without local revalidation, create a separate security-design ticket for authenticated transport/capabilities, key lifecycle, replay resistance and principal authorization. Do not silently repurpose I-006 hashes for that job.

## Rejected alternatives

### Treat `plan_fingerprint` as an authenticity token

Rejected. It is publicly recomputable and contains no secret/private-key proof.

### Rely on Python dataclass object identity or constructor privacy

Rejected. Public Python values can be reconstructed, and object identity is neither serializable nor a security boundary.

### Add an in-process secret MAC now

Rejected for v1. It does not materially improve a same-process trust boundary and creates secret management. It also would not establish semantic/runtime freshness by itself.

### Sign every plan now

Rejected absent a remote-producer requirement. Signatures answer origin-authentication questions but still require trust anchors, key lifecycle and replay/freshness handling; local revalidation already satisfies the current execution need more directly.

### Put user/session identity into plan fingerprint

Rejected. Authorization principals are deployment facts, not semantic identity, and would make deterministic plans non-reproducible across hosts/sessions.

## Exit decision

The minimal production-safe handoff is **revalidation against current trusted state**:

- I-006 hashes remain deterministic identity/integrity/cache keys only;
- I-007 establishes current runtime prerequisite state inside the trusted execution host;
- the executor authorizes a plan only by re-resolving/revalidating it against current trusted `CompiledSemanticIR` + I-007 state;
- serialized plans are untrusted inputs and cannot authorize themselves by recomputing their public hashes;
- signatures/MACs are deferred unless a later remote-principal architecture makes producer authentication necessary;
- user/session/corpus access authorization remains a separate host concern.

This prevents a hand-constructed lookalike plan from becoming executable solely because its deterministic fingerprint is valid while preserving reproducibility and avoiding premature key-management infrastructure.
