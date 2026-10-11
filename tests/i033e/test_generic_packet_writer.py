"""I-033E3 TDD: one local authoring tool for a genuine 10-selector source-bound packet.

An offline, unapproved packet is NEVER GitHub approval or a released mapping.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from tfont.review_packets import serialized
from tests.i033e.test_overlay_handoff import cohort

# Deliberately RED until the generic entry point is implemented.
from scripts.mappings import build_candidate_review_packet as writer


MANIFEST = "docs/research/data/batch_review/inputs.json"
LEDGER = "src/tfont/resources/batch_pilots/ten-native-pilot.json"
PACKET = "docs/research/data/generated/i033d/ten-native-review-request.json"


class GenericCandidatePacketWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger, self.loader, self.expected, _report = cohort()
        self.manifest = {
            "schema_version": 2,
            "ledger": LEDGER,
            "packet": PACKET,
            "evidence_resources": {},
        }
        self.write_json(LEDGER, self.ledger)
        for i, (corpus, spec) in enumerate(sorted(self.ledger["source_registry"].items())):
            name = spec["evidence_resource"]
            local = f"docs/research/data/batch_review/evidence/ten-cohort-{i}.json"
            self.manifest["evidence_resources"][name] = local
            self.write_json(local, self.loader(name))
        self.write_json(MANIFEST, self.manifest)

    def write_json(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
        return path

    def test_ten_source_grounded_candidates_generate_one_unapproved_packet(self):
        content = writer.build_packet(self.root, mode="write")
        produced = (self.root / PACKET).read_text(encoding="utf-8")
        self.assertEqual(content, serialized(self.expected))
        self.assertEqual(produced, content)
        self.assertEqual(writer.build_packet(self.root, mode="check"), content)
        result = json.loads(content)
        self.assertEqual(result["count"], 10)
        self.assertEqual(result["authority"], "unreviewed-proposal")
        self.assertIs(result["release_authorized"], False)
        self.assertEqual(len({x["decision_digest"] for x in result["rows"]}), 10)
        self.assertTrue(all(x["assessment"] == "native-only" for x in result["rows"]))

    def test_no_overwrite_and_stale_check_rejects_recomputed_or_missing_packet(self):
        with self.assertRaises(ValueError):
            writer.build_packet(self.root, mode="check")
        writer.build_packet(self.root, mode="write")
        with self.assertRaises((FileExistsError, ValueError)):
            writer.build_packet(self.root, mode="write")
        (self.root / PACKET).write_text("{}\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            writer.build_packet(self.root, mode="check")

    def test_rejects_evidence_mutation_even_when_source_paths_are_valid(self):
        local = next(iter(self.manifest["evidence_resources"].values()))
        altered = copy.deepcopy(self.loader(next(iter(self.manifest["evidence_resources"]))))
        altered["reviewed_content"]["source_definitions"]["adjv"]["line"] = 1999
        self.write_json(local, altered)  # content digest deliberately remains stale
        with self.assertRaises(ValueError):
            writer.build_packet(self.root, mode="stdout")

    def test_unsafe_manifest_paths_shapes_and_duplicate_json_keys_fail_closed(self):
        defects = [
            {"ledger": "../../secrets.json"},
            {"packet": "/tmp/untrusted.json"},
            {"packet": "docs/research/data/generated/i033d/../injection.json"},
            {"evidence_resources": []},
            {"evidence_resources": {next(iter(self.manifest["evidence_resources"])): "/tmp/evil.json"}},
            {"schema_version": 1},  # supplementary evidence requires v2
        ]
        for change in defects:
            with self.subTest(change=change):
                self.write_json(MANIFEST, dict(self.manifest, **change))
                with self.assertRaises(ValueError):
                    writer.build_packet(self.root, mode="stdout")
        raw = '{"schema_version":2,"schema_version":2,"ledger":"'+LEDGER+'","packet":"'+PACKET+'","evidence_resources":{}}'
        (self.root / MANIFEST).write_text(raw, encoding="utf-8")
        with self.assertRaises(ValueError):
            writer.build_packet(self.root, mode="stdout")

    def test_symlink_escape_is_refused_even_for_a_bounded_manifest_path(self):
        # Symlink points outside root; no arbitrary filesystem reads or writes.
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "outside.json"
            target.write_text('{"untrusted":true}', encoding="utf-8")
            path = self.root / LEDGER
            path.unlink()
            path.symlink_to(target)
            with self.assertRaises(ValueError):
                writer.build_packet(self.root, mode="stdout")


if __name__ == "__main__":
    unittest.main()
