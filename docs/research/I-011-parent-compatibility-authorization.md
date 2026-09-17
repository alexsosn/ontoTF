# I-011 research: explicit parent-compatibility authorization

**Issue:** #158  
**Discovered by:** I-009/#156 adversarial review  
**Phase:** research only

## Problem reproduced

I-007 intentionally implemented four runtime states: `verified-exact`, `verified-compatible`, `unverified`, and `incompatible`. Its original TDD contract says a changed parent with a complete passing dependency closure *may* yield `verified-compatible`.

The implementation currently turns that possibility into an unconditional rule:

```text
any dependency fail       -> incompatible
any dependency unknown    -> unverified
parent digest exact       -> verified-exact
otherwise                 -> verified-compatible
```

I-006 then accepts both verified states. No compiled release field says whether dependency closure was actually reviewed as sufficient to authorize execution on a changed parent.

The I-009 review-RED demonstrated the consequence with production-shaped inputs: a BHSA context with the wrong parent-manifest digest but the same observed `sp` values resolves and executes instead of failing closed.

This is a missing authority distinction between:

1. a release reviewed for one exact measured parent; and
2. a release whose authors intentionally reviewed dependency closure as sufficient for compatible-parent execution.

## Existing trust boundaries

These should remain unchanged:

- `BundleVariantKey.expected_parent_manifest_digest` is exact parent identity.
- `ProfileReleaseSignature` is compiled release authority and participates in release fingerprints / stale-prerequisite detection.
- I-007 derives current runtime observations; it must not invent semantic authority.
- I-006 consumes prerequisites but validates them against current compiled release authority.
- I-008 derives a fresh I-007 report internally; callers cannot supply execution plans or prerequisite authority.
- dependency observations prove reviewed native prerequisites still hold; they do not by themselves prove that the release author intended compatibility across arbitrary parent identities.

Compatibility authorization therefore belongs in the profile/release authority, not in a request, executor flag, observation, or caller-supplied prerequisite.

## Alternatives

### Request/executor flag

Rejected as the authority mechanism. `require_exact_parent=True` makes the caller responsible for tightening a release; a forgotten/false flag widens execution beyond reviewed scope. A request may eventually further restrict authority, but must never grant compatibility.

### New dependency kind for parent identity

Rejected. Exact identity is already represented by `BundleVariantKey`. Re-encoding it as a dependency duplicates authority and confuses exact identity with semantic compatibility checks.

### Explicit compatible-parent allowlist

Potential future extension, but stronger than needed now. It would require reviewed alternate parent digests/evidence. I-009 has no reviewed compatible parents.

### Release-authored compatibility policy

Recommended. Add a profile field:

```json
"parent_compatibility": "exact-only"
```

Allowed values:

- `exact-only`
- `dependency-verified`

Semantics:

- `exact-only`: parent-manifest mismatch is unauthorized even if every dependency observation passes;
- `dependency-verified`: the release explicitly authorizes the existing I-007 compatible-parent rule, so a mismatch with complete passing closure may become `verified-compatible`.

The field is release semantics and must be compiled into `ProfileReleaseSignature` and `profile_release_fingerprint()`.

## Source-schema migration

Add `parent_compatibility` as an optional profile-schema-v2 property with fail-closed semantic default:

```text
missing parent_compatibility -> exact-only
```

This keeps existing source files structurally parseable while removing implicit compatibility authority. Tests/releases intentionally exercising changed-parent compatibility must opt in explicitly with `dependency-verified`.

The compiler must always materialize the normalized value into `ProfileReleaseSignature`, so omitted and explicit `exact-only` have the same runtime authority.

No schema-version bump is needed for this additive source field before v0.1; the behavioral tightening is deliberate and fingerprinted in compiled release authority.

## Enforcement points

### I-007 evaluator

Keep dependency precedence unchanged. Once all dependencies pass:

```text
parent digest exact
    -> verified-exact
parent digest differs + parent_compatibility == dependency-verified
    -> verified-compatible
parent digest differs + parent_compatibility == exact-only
    -> incompatible
```

### I-006 resolver

Do not rely solely on the evaluator. `_prerequisite_problem()` must reject a `verified-compatible` prerequisite when the current release signature is not `dependency-verified`.

This prevents manually constructed/cached prerequisites from creating compatibility authority.

### Release fingerprints

`parent_compatibility` must participate in `profile_release_fingerprint()`. A policy change must invalidate prior prerequisites even when mappings, dependencies and exact target parent are otherwise unchanged.

No new runtime-report field is needed because `profile_release_fingerprint` binds the policy and the report already records the resulting compatibility state.

## Existing I-007 compatibility behavior

Do not delete the existing compatibility feature. Migrate the I-007 test "changed parent + passing closure yields verified-compatible" to an explicitly `dependency-verified` fixture. Add a new default/exact-only test showing the same changed parent is `incompatible`.

Exact-parent behavior and dependency fail/unknown precedence stay unchanged under both policies.

## I-009 effect

All production profiles should explicitly author:

```json
"parent_compatibility": "exact-only"
```

Then I-009's `wrong_exact_parent_fails_closed_before_native_selection` becomes an end-to-end acceptance test.

No mapping/projection digest changes are required because this is profile/release authority. Profile release fingerprints change, intentionally.

## Minimal implementation surface

Expected changes:

- `src/tfont/schemas/profile.schema.json`: optional enum property;
- `src/tfont/semantic_ir.py`: normalize policy into `ProfileReleaseSignature`;
- `src/tfont/semantic_resolver.py`: release-fingerprint projection and resolver guard;
- `src/tfont/runtime_prerequisites.py`: evaluator policy gate/signature validation;
- focused I-011 tests and deliberate migration of the I-007 compatibility test/fixture.

No new dependency kind, request flag, execution API, registry, network behavior or parent-discovery mechanism.

## Required TDD cases

1. absent policy compiles as `exact-only`;
2. explicit `exact-only` compiles to the same policy authority;
3. explicit `dependency-verified` compiles distinctly;
4. invalid policy is structurally rejected;
5. exact parent + passing closure -> `verified-exact` under both policies;
6. changed parent + passing closure -> `incompatible` under exact-only;
7. changed parent + passing closure -> `verified-compatible` only under dependency-verified;
8. dependency failure/unknown still dominates policy;
9. release fingerprint changes when policy changes;
10. manually constructed `verified-compatible` prerequisite against exact-only release is rejected by I-006;
11. changing policy makes an older prerequisite stale;
12. I-008 execution inherits the policy without a caller flag;
13. existing compatible-parent behavior remains available only through explicit opt-in.

## Conclusion

The smallest correct fix is a **release-authored `parent_compatibility` policy**, defaulting fail-closed to `exact-only`, compiled into release authority and enforced independently by I-007 and I-006.

This restores the intended meaning of I-007's wording that a changed parent *may* be compatible: passing dependency closure is necessary, but compatibility is granted only when the reviewed release explicitly says that closure is sufficient.