# F-004 source-bundle diagnostic path research

**Issue:** #28  
**Recorded:** 2026-09-06  
**Baseline:** current `main` after merged I-002  
**Scope:** research only; no production change in this commit.

## 1. Question

I-002 exposes `DigestProblem.path` so callers can locate projection/input failures. `source_bundle_digest()` receives an iterable of `(logical_path, bytes)` tuples and already reports tuple-local paths for several failures. This research checks whether logical-path syntax/type failures identify the same tuple field.

## 2. Accepted error contract

`docs/plans/I-002-canonicalization-digest-plan.md` defines:

```python
@dataclass(frozen=True)
class DigestProblem:
    category: str
    message: str
    path: tuple[str | int, ...] = ()
```

Tests and implementation use the path as a stable machine-oriented locator. For a source bundle, the input structure is naturally indexed as:

```text
(entry_index, tuple_field_index)
```

where field `0` is the logical path and field `1` is the payload bytes.

## 3. Current source-bundle behavior

Current `source_bundle_digest()` performs:

```python
for index, entry in enumerate(iterator):
    if type(entry) is not tuple or len(entry) != 2:
        _fail(..., (index,))
    path = _validate_logical_path(entry[0])
    if path in seen:
        _fail("duplicate_logical_path", ..., (index, 0))
    ...
    if type(raw) is not bytes:
        _fail("projection_error", ..., (index, 1))
```

Therefore:

- malformed tuple shape -> `(index,)`;
- duplicate logical path -> `(index, 0)`;
- invalid payload type -> `(index, 1)`.

But `_validate_logical_path()` currently has no diagnostic path parameter:

```python
def _validate_logical_path(path: Any) -> str:
    ...
    _fail("projection_error", "...path...characters")
```

Every failure in this helper therefore defaults to `DigestProblem.path == ()`.

## 4. Logical-path failure classes

The helper rejects:

- non-string values;
- empty string;
- characters outside `[A-Za-z0-9._/-]`;
- absolute paths beginning `/`;
- backslashes;
- empty segments (`a//b`, trailing slash);
- `.` segments;
- `..` traversal segments.

All of these describe field `0` of one specific source-bundle tuple and should report `(entry_index, 0)`.

No acceptance or normalization rule needs to change.

## 5. Caller surface

A search of merged `src/ontotf/digests.py` shows `_validate_logical_path()` is private and currently called only by `source_bundle_digest()`.

There is therefore no external helper API compatibility concern. The function signature can safely gain a keyword-only `error_path`/`path` parameter and the sole caller can pass `(index, 0)`.

## 6. Minimal design decision

Use:

```python
def _validate_logical_path(
    path: Any,
    *,
    error_path: tuple[str | int, ...] = (),
) -> str:
```

and pass `error_path` to every `_fail()` inside the helper.

`source_bundle_digest()` calls:

```python
path = _validate_logical_path(entry[0], error_path=(index, 0))
```

A default `()` keeps private direct calls deterministic and avoids coupling the helper solely to bundles.

## 7. Required controls

The repair must preserve:

- valid source-bundle digest bytes/vectors;
- malformed tuple path `(index,)`;
- duplicate logical-path path `(index, 0)`;
- invalid payload path `(index, 1)`;
- all existing categories/messages;
- path acceptance/rejection semantics.

Only `DigestProblem.path` for `_validate_logical_path()` failures changes.

## 8. RED strategy

Before production changes, add tests asserting `(index, 0)` for:

- traversal path such as `../a.yaml` at index 0;
- absolute or backslash path;
- wrong logical path type such as integer;
- invalid path on a later bundle entry, proving the index is caller-derived rather than hard-coded.

Controls assert duplicate-path and payload-type locations, and keep the existing fixed digest vector.

On merged main these new assertions fail because the observed path is `()`.

## 9. Scope boundary

F-004 does not modify source normalization, accepted path grammar, ordering, SHA-256/JCS projection, schemas, parent identity, semantic validation, or compatibility state.

## 10. Research conclusion

This is a localized diagnostic-provenance defect. The source-bundle caller already knows the correct tuple location; `_validate_logical_path()` simply needs to preserve that location through its existing stable `projection_error` failures.
