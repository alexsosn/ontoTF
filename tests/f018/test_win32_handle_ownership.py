from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ontotf.parent_identity as parent_identity
from ontotf.parent_identity import IdentityError, file_component_digest


@unittest.skipUnless(os.name == "nt", "Win32 trusted-handle contract")
class Win32HandleOwnershipTests(unittest.TestCase):
    def assert_category(self, category: str, func, *args, **kwargs) -> IdentityError:
        with self.assertRaises(IdentityError) as raised:
            func(*args, **kwargs)
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception

    def helper(self):
        helper = getattr(parent_identity, "_open_trusted_file_descriptor", None)
        self.assertTrue(callable(helper), "trusted descriptor helper must exist")
        self.assertTrue(hasattr(parent_identity, "msvcrt"), "trusted Windows path must expose its stdlib msvcrt bridge")
        return helper

    def creator(self):
        creator = getattr(parent_identity, "_win32_create_file_handle", None)
        self.assertTrue(callable(creator), "Win32 CreateFileW wrapper must exist")
        return creator

    def test_createfile_wrapper_passes_open_reparse_point_flag(self):
        creator = self.creator()
        low_level = getattr(parent_identity, "_win32_create_filew", None)
        self.assertTrue(callable(low_level), "Win32 raw CreateFileW seam must be callable")
        open_reparse = getattr(parent_identity, "_FILE_FLAG_OPEN_REPARSE_POINT", None)
        self.assertIs(type(open_reparse), int)
        self.assertNotEqual(open_reparse, 0)

        with patch.object(parent_identity, "_win32_create_filew", return_value=123) as create_filew:
            handle = creator(r"C:\fake\component.bin")

        self.assertEqual(handle, 123)
        create_filew.assert_called_once()
        args = create_filew.call_args.args
        self.assertGreaterEqual(len(args), 6, "raw CreateFileW seam must retain the Win32 argument order")
        flags_and_attributes = args[5]
        self.assertTrue(flags_and_attributes & open_reparse, "CreateFileW is missing FILE_FLAG_OPEN_REPARSE_POINT")

    def test_reparse_result_closes_raw_handle_once_without_conversion(self):
        helper = self.helper()
        with (
            patch.object(parent_identity, "_win32_create_file_handle", return_value=123, create=True),
            patch.object(parent_identity, "_win32_handle_is_reparse", return_value=True, create=True),
            patch.object(parent_identity, "_win32_close_handle", create=True) as close_handle,
            patch.object(parent_identity.msvcrt, "open_osfhandle") as conversion,
            patch.object(parent_identity.os, "read") as read_mock,
        ):
            self.assert_category("symlink_not_allowed", helper, r"C:\fake\link.bin")
        close_handle.assert_called_once_with(123)
        conversion.assert_not_called()
        read_mock.assert_not_called()

    def test_handle_query_failure_closes_raw_handle_once(self):
        helper = self.helper()
        with (
            patch.object(parent_identity, "_win32_create_file_handle", return_value=123, create=True),
            patch.object(parent_identity, "_win32_handle_is_reparse", side_effect=OSError("query failed"), create=True),
            patch.object(parent_identity, "_win32_close_handle", create=True) as close_handle,
            patch.object(parent_identity.msvcrt, "open_osfhandle") as conversion,
        ):
            self.assert_category("filesystem_error", helper, r"C:\fake\file.bin")
        close_handle.assert_called_once_with(123)
        conversion.assert_not_called()

    def test_conversion_failure_closes_raw_handle_once(self):
        helper = self.helper()
        with (
            patch.object(parent_identity, "_win32_create_file_handle", return_value=123, create=True),
            patch.object(parent_identity, "_win32_handle_is_reparse", return_value=False, create=True),
            patch.object(parent_identity, "_win32_close_handle", create=True) as close_handle,
            patch.object(parent_identity.msvcrt, "open_osfhandle", side_effect=OSError("conversion failed")),
        ):
            self.assert_category("filesystem_error", helper, r"C:\fake\file.bin")
        close_handle.assert_called_once_with(123)

    def test_conversion_success_transfers_ownership_and_sets_binary_mode(self):
        helper = self.helper()
        with (
            patch.object(parent_identity, "_win32_create_file_handle", return_value=123, create=True),
            patch.object(parent_identity, "_win32_handle_is_reparse", return_value=False, create=True),
            patch.object(parent_identity, "_win32_close_handle", create=True) as close_handle,
            patch.object(parent_identity.msvcrt, "open_osfhandle", return_value=456) as conversion,
            patch.object(parent_identity.msvcrt, "setmode", return_value=0) as setmode,
        ):
            descriptor = helper(r"C:\fake\file.bin")
        self.assertEqual(descriptor, 456)
        conversion.assert_called_once_with(123, os.O_RDONLY)
        setmode.assert_called_once_with(456, os.O_BINARY)
        close_handle.assert_not_called()

    def test_setmode_failure_closes_descriptor_not_raw_handle(self):
        helper = self.helper()
        with (
            patch.object(parent_identity, "_win32_create_file_handle", return_value=123, create=True),
            patch.object(parent_identity, "_win32_handle_is_reparse", return_value=False, create=True),
            patch.object(parent_identity, "_win32_close_handle", create=True) as close_handle,
            patch.object(parent_identity.msvcrt, "open_osfhandle", return_value=456),
            patch.object(parent_identity.msvcrt, "setmode", side_effect=OSError("setmode failed")),
            patch.object(parent_identity.os, "close") as close_fd,
        ):
            self.assert_category("filesystem_error", helper, r"C:\fake\file.bin")
        close_handle.assert_not_called()
        close_fd.assert_called_once_with(456)

    def test_real_file_uses_same_createfile_handle_for_crt_conversion_and_binary_reads(self):
        import msvcrt

        helper = self.helper()
        creator = self.creator()
        reparse_query = getattr(parent_identity, "_win32_handle_is_reparse", None)
        self.assertTrue(callable(reparse_query), "handle-bound reparse query helper must exist")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            payload = b"windows-handle-path\r\n\x00"
            path.write_bytes(payload)

            created_handles: list[int] = []
            converted_handles: list[int] = []
            mode_set = False
            real_creator = creator
            real_query = reparse_query
            real_open_osfhandle = msvcrt.open_osfhandle
            real_setmode = msvcrt.setmode
            real_read = os.read

            def tracked_creator(target: str):
                handle = real_creator(target)
                created_handles.append(handle)
                return handle

            def tracked_query(handle: int):
                self.assertIn(handle, created_handles)
                return real_query(handle)

            def tracked_open_osfhandle(handle, flags):
                converted_handles.append(handle)
                return real_open_osfhandle(handle, flags)

            def tracked_setmode(fd, flags):
                nonlocal mode_set
                result = real_setmode(fd, flags)
                if flags == os.O_BINARY:
                    mode_set = True
                return result

            def tracked_read(fd, size):
                self.assertTrue(mode_set, "binary mode must be set before the first digest read")
                return real_read(fd, size)

            with (
                patch.object(parent_identity, "_win32_create_file_handle", side_effect=tracked_creator),
                patch.object(parent_identity, "_win32_handle_is_reparse", side_effect=tracked_query),
                patch.object(parent_identity.msvcrt, "open_osfhandle", side_effect=tracked_open_osfhandle),
                patch.object(parent_identity.msvcrt, "setmode", side_effect=tracked_setmode),
                patch.object(parent_identity.os, "read", side_effect=tracked_read),
            ):
                digest = file_component_digest(path)

            self.assertEqual(len(created_handles), 1)
            self.assertEqual(converted_handles, created_handles, "CRT conversion must receive the exact inspected CreateFileW handle")
            self.assertTrue(mode_set)
            self.assertEqual(digest, "sha256:" + hashlib.sha256(payload).hexdigest())


if __name__ == "__main__":
    unittest.main()
