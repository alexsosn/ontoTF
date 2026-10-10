# I-027B3 plan: reproducible original MQL evidence acquisition

**Issue:** #279. **Research:** `docs/research/I-027B3-extrabiblical-mql-evidence.md`.

## TDD contract

A strictly offline Python script `scripts/research/i027b3_extract_mql.py` consumes one explicit path to the pinned compressed MQL file. No network access, dependencies, or source corpus installed at runtime.

It shall:
- verify file size **1,992,719** bytes and exact Git blob SHA **4ba717b1716b747bb94d0359b950a55d8624b109**;
- fail closed on corrupt bzip2 input, changed source file or untrusted argument mode;
- decode UTF-8 strictly; if decoding fails, record a controlled failure rather than guessing the text;
- produce deterministic compact JSON with Git blob SHA, compressed + decompressed SHA256, source revision and limited declaration context including `part_of_speech_t`, `sp`, and `verb` matches;
- keep every excerpt bounded and avoid storing the full source or leaking long text to CI logs;
- expose `--input` and optional `--json-output`, with dry extraction writing only to stdout by default.

## RED
Use `tests/i027b3` synthetic bz2 fixtures and a separately injected *test-only* expected blob hash/size to prove:
- real pinned hash/size checks are enabled by default;
- strict checksum mismatch rejection;
- corrupt bzip2 rejection;
- bounded deterministic excerpt extraction and UTF-8 error;
- no XML/JSON/data blob used as a substitute for source MQL.

## GREEN
Implement only the offline extractor and a workflow which checks out the exact upstream revision and runs it on `upstream/source/0.2/extraBiblical.mql.bz2` with no ability to write back upstream.

## Review/next gate
After CI, independently inspect the extracted declaration. If the native `verb` class is clearly evidenced, freeze an independently reviewed evidence record and proceed to immutable ExtraBiblical 0.3.0. If ambiguous, leave #279 blocked with evidence. Do not automatically publish an `exact` mapping based on a matching source string.
