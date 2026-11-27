# F-019 evidence note — CPython filesystem path conversion

**Issue:** #94  

This note closes the version/platform evidence question left deliberately conservative in the main F-019 report.

## File-open path

`pathlib.Path.read_bytes()` is a concrete filesystem operation and opens the pointed-to file. CPython's `_io.FileIO` filename constructor uses filesystem converters before calling the OS open primitive:

- on Windows, `PyUnicode_FSDecoder(nameobj, ...)` followed by wide-character conversion;
- on non-Windows, `PyUnicode_FSConverter(nameobj, ...)`.

Current CPython source: https://github.com/python/cpython/blob/main/Modules/_io/fileio.c

Python's C-API filesystem-converter contract explicitly states that embedded null bytes/characters are not allowed in the result and conversion fails with an exception. The same filesystem-converter family is documented in the 3.10 and 3.12 C-API documentation:

- https://docs.python.org/3.10/c-api/unicode.html
- https://docs.python.org/3.12/c-api/unicode.html

The 3.10 `path_converter` implementation also explicitly raises `ValueError` for an embedded null character on the Windows path-conversion branch, demonstrating that `ValueError` is an established CPython filesystem-path rejection category rather than a ontoTF-specific assumption.

Reference implementation snapshot:

- https://github.com/python/cpython/blob/v3.10.12/Modules/posixmodule.c

## Contract consequence

F-019 does **not** need to standardize CPython's exact exception message or claim that every filesystem API on every future Python release uses the same exception class. It only needs to contain the supported source-loading failure surface.

For the currently supported Python 3.10/3.12 matrix, RED must execute real embedded-NUL `Path.read_bytes()` paths on Ubuntu and Windows and pin the ontoTF result:

- raw Python `ValueError` must not escape;
- ontoTF category is `decode_error`;
- exact authored `source_name` is retained;
- parser/schema validation is not reached.

If a particular supported runner/version instead surfaces an `OSError`, the existing code path already translates it to the same `decode_error`; the public F-019 contract therefore remains stable. Tests should not assert the underlying CPython exception type or text, only containment at the ontoTF boundary.
