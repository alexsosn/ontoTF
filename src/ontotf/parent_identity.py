from __future__ import annotations

import errno
import hashlib
import os
import stat
from dataclasses import dataclass
from typing import Any

from .digests import DigestError, canonical_json_bytes

if os.name == "nt":
    import ctypes
    import msvcrt
    from ctypes import wintypes


FILE_BYTES_ALGORITHM = "tfont-file-bytes-sha256-v1"
DIRECTORY_FILES_ALGORITHM = "tfont-directory-files-sha256-v1"
TF_FILES_ALGORITHM = "tfont-tf-files-sha256-v1"
PARENT_COMPONENTS_ALGORITHM = "tfont-parent-components-sha256-v1"

_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_FILE_SHARE_DELETE = 0x00000004
_GENERIC_READ = 0x80000000
_OPEN_EXISTING = 3
_FILE_ATTRIBUTE_TAG_INFO_CLASS = 9


if os.name == "nt":
    class _FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
        _fields_ = [
            ("FileAttributes", wintypes.DWORD),
            ("ReparseTag", wintypes.DWORD),
        ]


    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _win32_create_filew = _kernel32.CreateFileW
    _win32_create_filew.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _win32_create_filew.restype = wintypes.HANDLE

    _win32_get_file_information_by_handle_ex = _kernel32.GetFileInformationByHandleEx
    _win32_get_file_information_by_handle_ex.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    _win32_get_file_information_by_handle_ex.restype = wintypes.BOOL

    _win32_close_handle_api = _kernel32.CloseHandle
    _win32_close_handle_api.argtypes = [wintypes.HANDLE]
    _win32_close_handle_api.restype = wintypes.BOOL

    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


@dataclass(frozen=True)
class IdentityProblem:
    category: str
    message: str
    path: str | None = None


class IdentityError(ValueError):
    def __init__(self, problem: IdentityProblem):
        self.problem = problem
        super().__init__(f"{problem.category}: {problem.message}")


def _fail(category: str, message: str, path: str | None = None) -> None:
    raise IdentityError(IdentityProblem(category=category, message=message, path=path))


def _native_separators() -> set[str]:
    separators = {os.sep}
    if os.altsep is not None:
        separators.add(os.altsep)
    return separators


def _reject_nonportable_file_path(path: str) -> None:
    separators = _native_separators()
    if path and path[-1] in separators:
        _fail("wrong_path_type", "exact file path must not end in directory syntax", path)

    components = [path]
    for separator in separators:
        components = [part for component in components for part in component.split(separator)]
    nonempty = [component for component in components if component]
    for index, component in enumerate(nonempty):
        if component in {".", ".."}:
            if index == len(nonempty) - 1 and component == ".":
                _fail("wrong_path_type", "exact file path must not end in directory syntax", path)
            continue
        if component.endswith((".", " ")):
            _fail("wrong_path_type", "exact file path has a non-portable component spelling", path)


def _strip_terminal_separators(path: str) -> str:
    separators = _native_separators()
    if path and all(character in separators for character in path):
        return path
    drive, tail = os.path.splitdrive(path)
    while len(tail) > 1 and tail[-1] in separators:
        tail = tail[:-1]
    return drive + tail


def _root_inspection_path(path: str) -> str:
    candidate = _strip_terminal_separators(path)
    while os.path.basename(candidate) == ".":
        parent = os.path.dirname(candidate)
        if not parent or parent == candidate:
            break
        candidate = _strip_terminal_separators(parent)
    return candidate


def _path_string(value: str | os.PathLike[str]) -> str:
    try:
        path = os.fspath(value)
    except TypeError as exc:
        _fail("filesystem_error", f"path is not path-like: {exc}")
    if type(path) is not str:
        _fail("filesystem_error", "path must resolve to an exact string")
    return path


def _lstat(path: str) -> os.stat_result:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        _fail("missing_path", "component path does not exist", path)
    except (OSError, ValueError) as exc:
        _fail("filesystem_error", str(exc), path)


def _stat_no_follow(path: str) -> os.stat_result:
    try:
        return os.stat(path, follow_symlinks=False)
    except (OSError, ValueError, NotImplementedError) as exc:
        _fail("filesystem_error", str(exc), path)


def _is_link_like(st: os.stat_result) -> bool:
    if stat.S_ISLNK(st.st_mode):
        return True
    attributes = getattr(st, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _require_real_directory(path: str) -> None:
    st = _lstat(path)
    if _is_link_like(st):
        _fail("symlink_not_allowed", "link-like component root is not allowed", path)
    if not stat.S_ISDIR(st.st_mode):
        _fail("wrong_path_type", "component root must be a directory", path)


def _sha256_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _file_identity(st: os.stat_result, path: str) -> tuple[int, int]:
    device = getattr(st, "st_dev", None)
    inode = getattr(st, "st_ino", None)
    if type(device) is not int or type(inode) is not int or inode == 0:
        _fail("filesystem_error", "stable file identity is unavailable", path)
    return device, inode


if os.name == "nt":
    def _win32_last_error() -> OSError:
        return ctypes.WinError(ctypes.get_last_error())


    def _win32_create_file_handle(path: str) -> int:
        handle = _win32_create_filew(
            path,
            _GENERIC_READ,
            _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
            None,
            _OPEN_EXISTING,
            _FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if handle == _INVALID_HANDLE_VALUE:
            raise _win32_last_error()
        return handle


    def _win32_handle_is_reparse(handle: int) -> bool:
        info = _FILE_ATTRIBUTE_TAG_INFO()
        succeeded = _win32_get_file_information_by_handle_ex(
            handle,
            _FILE_ATTRIBUTE_TAG_INFO_CLASS,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not succeeded:
            raise _win32_last_error()
        return bool(info.FileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT)


    def _win32_close_handle(handle: int) -> None:
        if not _win32_close_handle_api(handle):
            raise _win32_last_error()


    def _win32_close_handle_ignoring_errors(handle: int) -> None:
        try:
            _win32_close_handle(handle)
        except OSError:
            pass


def _open_trusted_file_descriptor(path: str) -> int:
    if os.name != "nt":
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        nonblock = getattr(os, "O_NONBLOCK", 0)
        if type(nofollow) is not int or nofollow == 0:
            _fail("filesystem_error", "trusted final-component no-follow open is unavailable", path)
        if type(nonblock) is not int or nonblock == 0:
            _fail("filesystem_error", "trusted nonblocking final-component open is unavailable", path)

        flags = os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)
        try:
            return os.open(path, flags)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                try:
                    final_state = os.lstat(path)
                except (OSError, ValueError):
                    final_state = None
                if final_state is not None and _is_link_like(final_state):
                    _fail("symlink_not_allowed", "link-like file object is not allowed", path)
            _fail("filesystem_error", str(exc), path)
        except ValueError as exc:
            _fail("filesystem_error", str(exc), path)

    raw_handle: int | None = None
    try:
        raw_handle = _win32_create_file_handle(path)
        try:
            is_reparse = _win32_handle_is_reparse(raw_handle)
        except (OSError, ValueError) as exc:
            _win32_close_handle_ignoring_errors(raw_handle)
            raw_handle = None
            _fail("filesystem_error", str(exc), path)

        if is_reparse:
            _win32_close_handle_ignoring_errors(raw_handle)
            raw_handle = None
            _fail("symlink_not_allowed", "link-like file object is not allowed", path)

        try:
            descriptor = msvcrt.open_osfhandle(raw_handle, os.O_RDONLY)
        except (OSError, ValueError) as exc:
            _win32_close_handle_ignoring_errors(raw_handle)
            raw_handle = None
            _fail("filesystem_error", str(exc), path)

        raw_handle = None
        try:
            msvcrt.setmode(descriptor, os.O_BINARY)
        except (OSError, ValueError) as exc:
            try:
                os.close(descriptor)
            except OSError:
                pass
            _fail("filesystem_error", str(exc), path)
        return descriptor
    except IdentityError:
        raise
    except (OSError, ValueError) as exc:
        if raw_handle is not None:
            _win32_close_handle_ignoring_errors(raw_handle)
        _fail("filesystem_error", str(exc), path)


def _sha256_descriptor(descriptor: int, path: str) -> str:
    digest = hashlib.sha256()
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _sha256_file(path: str, expected: os.stat_result) -> str:
    expected_identity = _file_identity(expected, path)
    descriptor: int | None = None
    try:
        try:
            descriptor = _open_trusted_file_descriptor(path)
        except IdentityError as exc:
            if exc.problem.category == "symlink_not_allowed":
                _fail("filesystem_error", "file object became link-like between inspection and hashing", path)
            raise

        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            _fail("filesystem_error", "opened file object is not a regular file", path)
        if _file_identity(opened, path) != expected_identity:
            _fail("filesystem_error", "file identity changed between inspection and hashing", path)
        return _sha256_descriptor(descriptor, path)
    except IdentityError:
        raise
    except (OSError, ValueError) as exc:
        _fail("filesystem_error", str(exc), path)
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _validate_segment(segment: str, *, filesystem_path: str) -> str:
    if type(segment) is not str or not segment or segment in {".", ".."}:
        _fail("invalid_logical_path", "invalid component-relative path segment", filesystem_path)
    if "/" in segment or "\\" in segment:
        _fail("invalid_logical_path", "logical path segment contains a non-portable separator", filesystem_path)
    try:
        segment.encode("utf-8")
    except UnicodeEncodeError as exc:
        _fail("unicode_domain", str(exc), filesystem_path)
    return segment


def _utf16_key(value: str) -> bytes:
    try:
        return value.encode("utf-16be")
    except UnicodeEncodeError as exc:
        _fail("unicode_domain", str(exc))


def _file_record(
    relative_logical_path: str,
    filesystem_path: str,
    expected: os.stat_result,
) -> dict[str, str]:
    return {
        "relative_logical_path": relative_logical_path,
        "sha256": _sha256_file(filesystem_path, expected),
    }


def _hash_file_records(records: list[dict[str, str]]) -> str:
    records.sort(key=lambda record: _utf16_key(record["relative_logical_path"]))
    try:
        encoded = canonical_json_bytes(records)
    except DigestError as exc:
        category = "unicode_domain" if exc.problem.category == "unicode_domain" else "projection_error"
        _fail(category, exc.problem.message)
    return _sha256_bytes(encoded)


def _scan_directory(directory: str) -> list[Any]:
    try:
        with os.scandir(directory) as entries:
            return list(entries)
    except OSError as exc:
        _fail("filesystem_error", str(exc), directory)


def file_component_digest(path: str | os.PathLike[str]) -> str:
    filesystem_path = _path_string(path)
    _reject_nonportable_file_path(filesystem_path)
    st = _lstat(filesystem_path)
    if _is_link_like(st):
        _fail("symlink_not_allowed", "link-like file component is not allowed", filesystem_path)
    if not stat.S_ISREG(st.st_mode):
        _fail("wrong_path_type", "file component must be a regular file", filesystem_path)
    return _sha256_file(filesystem_path, st)


def directory_component_digest(path: str | os.PathLike[str]) -> str:
    root = _root_inspection_path(_path_string(path))
    _require_real_directory(root)
    records: list[dict[str, str]] = []

    stack: list[tuple[list[Any], int, tuple[str, ...]]] = [(_scan_directory(root), 0, ())]
    while stack:
        current, index, relative_segments = stack[-1]
        if index >= len(current):
            stack.pop()
            continue

        entry = current[index]
        stack[-1] = (current, index + 1, relative_segments)
        entry_path = entry.path
        segment = _validate_segment(entry.name, filesystem_path=entry_path)
        st = _stat_no_follow(entry_path)
        if _is_link_like(st):
            _fail("symlink_not_allowed", "link-like entry is not allowed", entry_path)

        segments = relative_segments + (segment,)
        if stat.S_ISDIR(st.st_mode):
            stack.append((_scan_directory(entry_path), 0, segments))
        elif stat.S_ISREG(st.st_mode):
            logical_path = "/".join(segments)
            records.append(_file_record(logical_path, entry_path, st))
        else:
            _fail("unsupported_entry", "addressed directory contains a non-file/non-directory entry", entry_path)

    return _hash_file_records(records)


def tf_payload_digest(path: str | os.PathLike[str]) -> str:
    root = _root_inspection_path(_path_string(path))
    _require_real_directory(root)
    records: list[dict[str, str]] = []

    try:
        with os.scandir(root) as entries:
            current = list(entries)
    except OSError as exc:
        _fail("filesystem_error", str(exc), root)

    for entry in current:
        if not entry.name.endswith(".tf"):
            continue
        entry_path = entry.path
        logical_path = _validate_segment(entry.name, filesystem_path=entry_path)
        st = _stat_no_follow(entry_path)
        if _is_link_like(st):
            _fail("symlink_not_allowed", "selected TF entry is link-like", entry_path)
        if stat.S_ISREG(st.st_mode):
            records.append(_file_record(logical_path, entry_path, st))

    if not records:
        _fail("empty_component", "TF payload contains no direct regular .tf files", root)
    return _hash_file_records(records)


def _require_nonempty_string(value: Any, *, field: str) -> str:
    if type(value) is not str or not value:
        _fail("projection_error", f"{field} must be a non-empty exact string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        _fail("unicode_domain", str(exc))
    return value


def parent_manifest_projection(manifest: dict[str, Any]) -> dict[str, Any]:
    if type(manifest) is not dict:
        _fail("projection_error", "parent manifest must be an exact object")
    allowed_top = {"algorithm", "components"}
    unknown_top = sorted(manifest.keys() - allowed_top) if all(type(key) is str for key in manifest) else []
    if any(type(key) is not str for key in manifest):
        _fail("projection_error", "parent manifest keys must be exact strings")
    if unknown_top:
        _fail("projection_error", f"unknown parent manifest fields: {', '.join(unknown_top)}")
    missing_top = sorted(allowed_top - manifest.keys())
    if missing_top:
        _fail("projection_error", f"missing parent manifest fields: {', '.join(missing_top)}")
    if manifest["algorithm"] != PARENT_COMPONENTS_ALGORITHM:
        _fail("projection_error", f"algorithm must be {PARENT_COMPONENTS_ALGORITHM}")

    source_components = manifest["components"]
    if type(source_components) is not list or not source_components:
        _fail("projection_error", "components must be a non-empty exact list")

    required = {"component_id", "kind", "identity_algorithm", "content_digest"}
    optional = {"logical_locator", "license_ref"}
    result: list[dict[str, str]] = []
    seen: set[str] = set()

    for index, source in enumerate(source_components):
        if type(source) is not dict:
            _fail("projection_error", f"components[{index}] must be an exact object")
        if any(type(key) is not str for key in source):
            _fail("projection_error", f"components[{index}] keys must be exact strings")
        missing = sorted(required - source.keys())
        if missing:
            _fail("projection_error", f"components[{index}] missing fields: {', '.join(missing)}")
        unknown = sorted(source.keys() - required - optional)
        if unknown:
            _fail("projection_error", f"components[{index}] unknown fields: {', '.join(unknown)}")

        component_id = _require_nonempty_string(source["component_id"], field=f"components[{index}].component_id")
        if component_id in seen:
            _fail("projection_error", f"duplicate component_id: {component_id}")
        seen.add(component_id)

        for field in optional:
            if field in source:
                _require_nonempty_string(source[field], field=f"components[{index}].{field}")

        result.append(
            {
                "component_id": component_id,
                "kind": _require_nonempty_string(source["kind"], field=f"components[{index}].kind"),
                "identity_algorithm": _require_nonempty_string(
                    source["identity_algorithm"], field=f"components[{index}].identity_algorithm"
                ),
                "content_digest": _require_nonempty_string(
                    source["content_digest"], field=f"components[{index}].content_digest"
                ),
            }
        )

    result.sort(key=lambda component: _utf16_key(component["component_id"]))
    return {"components": result}


def parent_manifest_digest(manifest: dict[str, Any]) -> str:
    projection = parent_manifest_projection(manifest)
    try:
        encoded = canonical_json_bytes(projection)
    except DigestError as exc:
        category = "unicode_domain" if exc.problem.category == "unicode_domain" else "projection_error"
        _fail(category, exc.problem.message)
    return _sha256_bytes(encoded)
