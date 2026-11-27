from __future__ import annotations

import copy
import os
from pathlib import Path
import tempfile
import unittest

import ontotf.parent_identity as parent_identity
from ontotf.parent_identity import (
    DIRECTORY_FILES_ALGORITHM,
    FILE_BYTES_ALGORITHM,
    PARENT_COMPONENTS_ALGORITHM,
    TF_FILES_ALGORITHM,
    IdentityError,
    directory_component_digest,
    file_component_digest,
    parent_manifest_digest,
    parent_manifest_projection,
    tf_payload_digest,
)


FILE_ALPHA_DIGEST = "sha256:b6a98d9ce9a2d9149288fa3df42d377c3e42737afdcdaf714e33c0a100b51060"
EMPTY_FILE_DIGEST = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
EMPTY_DIRECTORY_DIGEST = "sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
DIRECTORY_VECTOR_DIGEST = "sha256:d5d2ddbdccc7d67378836747af134ad681996ed0e0c63ec20f0e9e0ae259a323"
TF_VECTOR_DIGEST = "sha256:a3b28b34637f2a2bdba591ed2020c94a2991e4e64643741c804ca4621bd7f83f"
PARENT_VECTOR_DIGEST = "sha256:c8427586f094ade21411843a55a89f88161ab42a7462564905e94599eea57fa9"


class IdentityTestCase(unittest.TestCase):
    def assert_category(self, category: str, func, *args, **kwargs) -> IdentityError:
        with self.assertRaises(IdentityError) as raised:
            func(*args, **kwargs)
        self.assertEqual(raised.exception.problem.category, category)
        return raised.exception

    def make_directory_vector(self, root: Path, reverse_creation: bool = False) -> None:
        entries = [
            (Path("a.txt"), b"alpha\n"),
            (Path("nested") / "b.bin", b"\x00\x01\xff"),
        ]
        if reverse_creation:
            entries.reverse()
        for rel, payload in entries:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

    def make_tf_vector(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / "oslots.tf").write_bytes(b"@edge\n1\t1\n")
        (root / "otext.tf").write_bytes(b"@config\n@sectionTypes=book,chapter,verse\n")
        (root / "otype.tf").write_bytes(b"@node\n1\tword\n")

    def parent_manifest(self) -> dict:
        return {
            "algorithm": PARENT_COMPONENTS_ALGORITHM,
            "components": [
                {
                    "component_id": "bhsa-tf",
                    "kind": "tf-payload",
                    "identity_algorithm": TF_FILES_ALGORITHM,
                    "content_digest": TF_VECTOR_DIGEST,
                    "logical_locator": "/host/path/ignored",
                    "license_ref": "CC-BY-4.0",
                },
                {
                    "component_id": "oracc-sidecar",
                    "kind": "sidecar",
                    "identity_algorithm": DIRECTORY_FILES_ALGORITHM,
                    "content_digest": DIRECTORY_VECTOR_DIGEST,
                    "logical_locator": "relative/ignored",
                    "license_ref": "CC0-1.0",
                },
            ],
        }


class AlgorithmAndFileTests(IdentityTestCase):
    def test_algorithm_identifiers_are_versioned(self):
        self.assertEqual(FILE_BYTES_ALGORITHM, "tfont-file-bytes-sha256-v1")
        self.assertEqual(DIRECTORY_FILES_ALGORITHM, "tfont-directory-files-sha256-v1")
        self.assertEqual(TF_FILES_ALGORITHM, "tfont-tf-files-sha256-v1")
        self.assertEqual(PARENT_COMPONENTS_ALGORITHM, "tfont-parent-components-sha256-v1")

    def test_exact_file_vector_and_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.bin"
            path.write_bytes(b"alpha\n")
            self.assertEqual(file_component_digest(path), FILE_ALPHA_DIGEST)
            path.write_bytes(b"alpha!\n")
            self.assertNotEqual(file_component_digest(path), FILE_ALPHA_DIGEST)

    def test_empty_regular_file_has_explicit_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.bin"
            path.write_bytes(b"")
            self.assertEqual(file_component_digest(path), EMPTY_FILE_DIGEST)

    def test_file_root_type_and_symlink_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assert_category("missing_path", file_component_digest, root / "missing")
            self.assert_category("wrong_path_type", file_component_digest, root)
            target = root / "target.bin"
            target.write_bytes(b"payload")
            link = root / "link.bin"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assert_category("symlink_not_allowed", file_component_digest, link)


class DirectoryIdentityTests(IdentityTestCase):
    def test_recursive_directory_fixed_vector(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_directory_vector(root)
            self.assertEqual(directory_component_digest(root), DIRECTORY_VECTOR_DIGEST)

    def test_empty_directory_is_hash_of_empty_file_record_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(directory_component_digest(root), EMPTY_DIRECTORY_DIGEST)
            empty_file = root / "empty.bin"
            empty_file.write_bytes(b"")
            self.assertNotEqual(directory_component_digest(root), EMPTY_DIRECTORY_DIGEST)
            self.assertNotEqual(directory_component_digest(root), EMPTY_FILE_DIGEST)

    def test_creation_or_enumeration_order_does_not_affect_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            one = base / "one"
            two = base / "two"
            one.mkdir()
            two.mkdir()
            self.make_directory_vector(one, reverse_creation=False)
            self.make_directory_vector(two, reverse_creation=True)
            self.assertEqual(directory_component_digest(one), directory_component_digest(two))

    def test_relative_path_rename_changes_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_directory_vector(root)
            before = directory_component_digest(root)
            source = root / "nested" / "b.bin"
            target = root / "nested" / "renamed.bin"
            source.rename(target)
            self.assertNotEqual(directory_component_digest(root), before)

    def test_recursive_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.bin"
            target.write_bytes(b"payload")
            link = root / "link.bin"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assert_category("symlink_not_allowed", directory_component_digest, root)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation requires POSIX mkfifo")
    def test_recursive_special_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fifo = root / "pipe"
            os.mkfifo(fifo)
            self.assert_category("unsupported_entry", directory_component_digest, root)

    @unittest.skipIf(os.name == "nt", "literal backslash is a path separator on Windows")
    def test_nonportable_backslash_filename_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bad\\name.bin").write_bytes(b"payload")
            self.assert_category("invalid_logical_path", directory_component_digest, root)


class TFPayloadIdentityTests(IdentityTestCase):
    def test_tf_direct_file_fixed_vector_and_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tf_vector(root)
            (root / "README.md").write_text("ignored transport/source metadata", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "ignored.tf").write_bytes(b"must not enter direct TF payload")
            self.assertEqual(tf_payload_digest(root), TF_VECTOR_DIGEST)

    def test_tf_file_mutation_changes_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tf_vector(root)
            before = tf_payload_digest(root)
            (root / "otype.tf").write_bytes(b"@node\n1\tchanged\n")
            self.assertNotEqual(tf_payload_digest(root), before)

    def test_tf_selected_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tf_vector(root)
            target = root / "real.txt"
            target.write_bytes(b"@node\n1\textra\n")
            link = root / "linked.tf"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assert_category("symlink_not_allowed", tf_payload_digest, root)

    def test_tf_non_tf_symlink_is_outside_payload_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tf_vector(root)
            before = tf_payload_digest(root)
            target = root / "notes.txt"
            target.write_bytes(b"ignored")
            link = root / "notes.link"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assertEqual(tf_payload_digest(root), before)

    def test_empty_tf_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("not TF", encoding="utf-8")
            self.assert_category("empty_component", tf_payload_digest, root)


class ParentManifestIdentityTests(IdentityTestCase):
    def test_parent_manifest_fixed_vector_and_projection(self):
        manifest = self.parent_manifest()
        self.assertEqual(parent_manifest_digest(manifest), PARENT_VECTOR_DIGEST)
        projection = parent_manifest_projection(manifest)
        self.assertEqual(set(projection), {"components"})
        self.assertNotIn("logical_locator", projection["components"][0])
        self.assertNotIn("license_ref", projection["components"][0])

    def test_component_order_and_nonsemantic_metadata_do_not_change_parent_identity(self):
        one = self.parent_manifest()
        two = copy.deepcopy(one)
        two["components"].reverse()
        for component in two["components"]:
            component["logical_locator"] = "C:/different/host/path"
            component["license_ref"] = "different-audit-license-label"
        self.assertEqual(parent_manifest_digest(one), parent_manifest_digest(two))

    def test_each_semantic_component_field_changes_parent_identity(self):
        base = self.parent_manifest()
        base_digest = parent_manifest_digest(base)
        changes = {
            "component_id": "changed-id",
            "kind": "catalogue",
            "identity_algorithm": FILE_BYTES_ALGORITHM,
            "content_digest": "sha256:changed",
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                changed = copy.deepcopy(base)
                changed["components"][0][field] = value
                self.assertNotEqual(parent_manifest_digest(changed), base_digest)

    def test_duplicate_component_ids_fail_closed(self):
        manifest = self.parent_manifest()
        manifest["components"][1]["component_id"] = manifest["components"][0]["component_id"]
        self.assert_category("projection_error", parent_manifest_digest, manifest)

    def test_unknown_projection_field_fails_closed(self):
        manifest = self.parent_manifest()
        manifest["components"][0]["future_semantic_field"] = "must not be silently omitted"
        self.assert_category("projection_error", parent_manifest_digest, manifest)

    def test_unchanged_tf_plus_changed_sidecar_changes_parent_identity(self):
        one = self.parent_manifest()
        two = copy.deepcopy(one)
        self.assertEqual(one["components"][0]["content_digest"], two["components"][0]["content_digest"])
        two["components"][1]["content_digest"] = "sha256:changed-sidecar"
        self.assertNotEqual(parent_manifest_digest(one), parent_manifest_digest(two))

    def test_i003_does_not_expose_compatibility_state_inference(self):
        for name in ("evaluate_compatibility", "compatibility_state", "build_compatibility_report"):
            self.assertFalse(hasattr(parent_identity, name), name)


if __name__ == "__main__":
    unittest.main()
