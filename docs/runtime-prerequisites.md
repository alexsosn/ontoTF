# Runtime prerequisite evaluation

ontoTF derives runtime prerequisite state from the **currently observed materialized corpus** and the selected compiled semantic release. Callers do not choose `verified-exact`, `verified-compatible`, `unverified`, or `incompatible`; the I-007 evaluator derives those states from the observed parent identity and the complete dependency closure recorded in the selected `ProfileReleaseSignature`.

## Compatibility states

`verified-exact` means the observed parent manifest digest is exactly the expected digest and every release dependency deterministically passes. `verified-compatible` means the parent digest changed but every reviewed dependency still deterministically passes. A changed digest alone is not evidence of compatibility.

`unverified` means at least one required observation cannot be established, while no dependency is known to fail. `incompatible` means at least one reviewed dependency deterministically fails. A known failure dominates unknown observations.

The ontology bundle is a separate runtime axis. A release that requires no bundle reports `not-required`. A required locally selected bundle is `verified` only when its digest exactly matches the release. A missing required bundle is `unavailable`. An explicitly wrong or malformed bundle identity is invalid/stale runtime input; it is not rewritten as corpus incompatibility. Parent compatibility therefore remains meaningful even when ontology bundle readiness differs.

## Dependency semantics

The evaluator checks every dependency in the selected release, not a target-local subset. The supported P-002 kinds are `component-present`, `node-type-present`, `feature-present`, `edge-present`, `path-present`, `native-value-present`, `value-domain`, and `extent-interpretation`.

`native-value-present` uses exact JSON-scalar identity: null, booleans, numbers, and strings are not coerced into one another. For `value-domain`, `observed` requires all declared support values to occur while allowing additional observed values. `closed-reviewed` has different semantics: it is an allowed reviewed closure, so the completely observed domain must be a subset of the reviewed closed domain. An allowed value does not have to occur in every materialized corpus. Incomplete value enumeration yields `unverified`, not a guessed pass.

`path-present` means the ordered edge/direction execution shape is available; it does not run an arbitrary semantic query to prove that a result row happens to exist. `extent-interpretation` is never inferred from graph topology or node counts. It requires explicit deterministic local metadata for tokens such as `textualExtent`, `occurrenceSet`, `technicalAnchor`, or `noSlot`; absent metadata yields an unknown observation.

## Already loaded Text-Fabric observation

`LoadedTFObservation` is a narrow read-only adapter over an **already loaded** Text-Fabric/Context-Fabric-like API. The host supplies the observed parent digest, component identities and loaded API objects. The adapter inspects loaded node and edge features and exact feature values, but it never imports Text-Fabric as a required dependency, never invokes feature/corpus loading, never executes semantic search, and never fetches a corpus or ontology from the network. Missing or unreadable loaded API capabilities become `unknown` observations rather than triggering hidden I/O.

Extent interpretation is supplied explicitly by the local corpus/native-adapter contract rather than guessed from `oslots` or topology.

## Deterministic identities and trust

Known observations receive deterministic evidence digests; the runtime report receives a deterministic report fingerprint. These identities include execution-relevant facts such as the full variant key, profile-release fingerprint, observed parent digest, sorted dependency results and rule versions, ontology bundle state, and source contract. Volatile metadata such as timestamps, local paths, process IDs, hosts, users, sessions, and Python/Text-Fabric object identities are excluded.

These public hashes identify content; a matching fingerprint **does not authenticate** the producer and does not by itself authorize execution. Within one trusted process, the intended path is to invoke the evaluator over current trusted release and observed corpus state and pass its `RuntimePrerequisiteState` projection directly to the resolver/executor. A serialized report crossing an untrusted boundary must be re-established locally or protected by a separately designed authenticated mechanism.

## Legacy compatibility reports

The legacy v1 compatibility report and its `profile_semantic_digest` belong to an older authority model. They are not interchangeable with the current profile-release fingerprint and cannot be supplied as I-007 runtime execution authority. Any future migration path must re-establish the current release, parent, complete dependency closure, and ontology bundle facts instead of trusting legacy field-name similarity.
