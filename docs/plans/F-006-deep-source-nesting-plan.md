# F-006 plan: fail closed on excessively deep source nesting

**Issue:** #32  
**Research:** `docs/research/F-006-deep-source-nesting.md`  
**Production scope:** `src/ontotf/source_validation.py` only.

## 1. Public contract

Add public module constant:

```python
MAX_SOURCE_NESTING = 128
```

Container nesting is counted uniformly for JSON and YAML:

- scalar root: 0;
- root list/dict: 1;
- each nested list/dict increments depth;
- depth `MAX_SOURCE_NESTING` is accepted;
- depth `MAX_SOURCE_NESTING + 1` fails.

Failure is:

```text
SourceValidationError
category = decode_error
message = source nesting exceeds maximum depth 128
source_name = caller/file source name
```

No parser-specific recursion/depth text is exposed as API.

## 2. RED tests

Add `tests/f006/test_deep_source_nesting.py` before production edits.

Helpers generate deterministic nested structures/text without recursive test construction that itself reaches interpreter limits.

Required tests:

1. deeply nested JSON does not satisfy the planned stable ontoTF depth contract on pre-fix main;
2. deeply nested YAML does not satisfy the planned stable ontoTF depth contract on pre-fix main;
3. boundary JSON: depth 128 accepted, 129 rejected after GREEN;
4. boundary YAML: depth 128 accepted, 129 rejected after GREEN;
5. rejection preserves explicit `source_name`;
6. moderate nested JSON/YAML values are unchanged;
7. duplicate JSON/YAML keys remain `duplicate_key`;
8. JSON/YAML non-finite behavior remains unchanged;
9. recursive YAML alias remains `non_json_value`.

RED is acceptable if pre-fix leaks `RecursionError` or returns another outcome instead of the planned `SourceValidationError(decode_error)`.

## 3. Minimal implementation

### `_plain_json`

Add keyword-only `depth: int = 0`.

For list/dict:

```text
container_depth = depth + 1
if container_depth > MAX_SOURCE_NESTING:
    _raise(decode_error, stable depth message, source_name)
```

Recursive calls receive `depth=container_depth`.

Existing recursive-alias detection remains unchanged and has priority when encountered before the depth limit.

### JSON parsing

Extend the JSON load exception boundary to catch `RecursionError` and convert it to the stable depth `decode_error`.

Do not alter duplicate-key or non-finite numeric handling.

### YAML parsing

Do **not** make F-006 depend on ruamel.yaml's parser-specific `max_depth` exception contract. The pinned 0.19.x parser may expose early depth hardening, but coupling ontoTF's public behavior to its exception taxonomy would create a second, format-specific policy surface and make the stable message sensitive to dependency details.

Instead:

- catch `RecursionError` from `parser.load()` and normalize it to the same stable ontoTF depth `decode_error` used for JSON;
- preserve `DuplicateKeyError` precedence;
- preserve generic `YAMLError` -> ordinary parse `decode_error` behavior;
- rely on `_plain_json()` as the deterministic format-independent `MAX_SOURCE_NESTING` authority for successfully parsed documents.

This still fails early for extreme YAML that exhausts parser recursion, while ordinary 129-level documents are rejected deterministically by ontoTF rather than by a parser-specific depth exception.

## 4. Test workflow

Add a focused F-006 workflow triggered by:

- `src/ontotf/source_validation.py`
- `tests/f006/**`
- F-006 research/plan
- workflow itself.

Matrix Python 3.10 and 3.12.

Steps:

1. install editable package;
2. run `tests/f006`;
3. run `tests/i001`;
4. run full repository suite.

Record exact RED run before production implementation and exact GREEN run afterward.

## 5. Non-goals / invariants

- no schema changes;
- no source data transformation beyond existing plain-JSON normalization;
- no byte/string-size limits;
- no parser replacement;
- no Python recursion-limit mutation;
- no I-002 digest changes;
- no semantic changes;
- ordinary accepted sources produce byte-for-byte equivalent Python JSON values to pre-fix behavior.

## 6. Independent review attack surface

Fresh exact-head review must challenge:

- off-by-one depth semantics;
- whether JSON can still leak `RecursionError` before ontoTF enforcement;
- whether YAML parser recursion failure is normalized robustly for pinned 0.19.x without depending on parser-specific depth exceptions;
- whether recursive aliases were accidentally reclassified;
- whether duplicate/non-finite error precedence changed;
- whether a 128-level accepted document can itself cause later schema/canonicalization recursion problems;
- whether exposing `MAX_SOURCE_NESTING` is appropriate or should remain module-private;
- whether source-name diagnostics remain stable.

Any change to the threshold, error category, or boundary semantics after review requires a fresh exact-head review.
