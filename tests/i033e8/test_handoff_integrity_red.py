"""RED/GREEN verification of accepted-only compact handoff integrity.

All data are ten genuine pinned BHSA/Syriac POS source categories in the
previously reviewed #316 contract fixture. No mocked token grants authority.
"""
from __future__ import annotations

import copy
import hashlib
import unittest
from unittest.mock import patch

from tfont.digests import canonical_json_bytes
from tests.i033e.test_overlay_handoff import cohort, assemble


def sealed(pack):
    """Attacker recomputes outer checksum; internal referential checks must fail."""
    result = copy.deepcopy(pack)
    result.pop("content_digest", None)
    result["content_digest"] = "sha256:" + hashlib.sha256(
        canonical_json_bytes(result)
    ).hexdigest()
    return result


class IntegrityRedTests(unittest.TestCase):
    def setUp(self):
        self.ledger, self.read, self.packet, self.observation = cohort()
        self.original = assemble(
            self.ledger, self.read, self.packet, self.observation
        )

    def validate(self, pack):
        from tfont.overlay_handoff import verify_overlay_handoff_integrity
        return verify_overlay_handoff_integrity(pack)

    def test_actual_ten_category_pilot_is_integrity_valid_but_not_approved(self):
        self.assertIsNone(self.validate(self.original))
        self.assertFalse(self.original["release_authorized"])
        self.assertEqual(self.original["counts"], {"exact": 0, "native-only": 10})
        self.assertTrue(all(
            not mapping["projections"]
            for corpus in self.original["corpora"]
            for mapping in corpus["mappings"]
        ))

    def test_pack_fails_even_with_recomputed_envelope_digest(self):
        defects = {
            "untrusted_authority": lambda p: p.update(release_authorized=True),
            "forged_review": lambda p: p["corpora"][0]["mappings"][0].update(
                review={"status":"reviewed"}
            ),
            "dropped_mapping": lambda p: p["corpora"][0]["mappings"].pop(),
            "duplicate_coverage": lambda p: p["corpora"][0]["coverage_assignments"].append(
                copy.deepcopy(p["corpora"][0]["coverage_assignments"][0])
            ),
            "wrong_decision_digest": lambda p: p["corpora"][0]["coverage_assignments"][0].update(
                decision_digest="sha256:"+"0"*64
            ),
            "wrong_base_bundle": lambda p: p["corpora"][0].update(
                base_bundle_digest="sha256:"+"1"*64
            ),
            "wrong_coverage": lambda p: p["corpora"][0]["coverage_base"].update(
                denominator_digest="sha256:"+"a"*64
            ),
            "fabricated_evidence": lambda p: p["corpora"][0]["added_evidence"][0]["record"].update(
                source_revision="b"*40
            ),
            "wrong_native_scope": lambda p: p["corpora"][0]["mappings"][0]["native_binding"].update(
                node_type="lex"
            ),
            "fake_positive_native": lambda p: p["corpora"][0]["mappings"][0].update(
                native_state="positive"
            ),
            "invented_ontology_term": lambda p: p.update(
                ontology_lock_digest="sha256:"+"c"*64
            ),
            "extra_semantic_items": lambda p: p.update(semantic_items=[]),
            "forged_counts": lambda p: p["counts"].update(exact=10),
            "unreviewed_observation": lambda p: p["review_observation"]["rows"][0].update(
                disposition="reject"
            ),
        }
        for name,mutate in defects.items():
            with self.subTest(name=name):
                p=copy.deepcopy(self.original)
                mutate(p)
                with self.assertRaises(ValueError):
                    self.validate(sealed(p))

    def test_nested_identity_collisions_and_selector_overwrite_rejected(self):
        for name,alter in (
            ("duplicate_mapping",lambda p:p["corpora"][0]["mappings"].append(
                copy.deepcopy(p["corpora"][0]["mappings"][0]))),
            ("duplicate_dependency",lambda p:p["corpora"][0]["added_dependencies"].append(
                copy.deepcopy(p["corpora"][0]["added_dependencies"][0]))),
            ("duplicate_evidence",lambda p:p["corpora"][0]["added_evidence"].append(
                copy.deepcopy(p["corpora"][0]["added_evidence"][0]))),
        ):
            with self.subTest(name=name):
                p=copy.deepcopy(self.original)
                alter(p)
                with self.assertRaises(ValueError):
                    self.validate(sealed(p))

    def test_validator_cannot_be_used_to_authenticate_fake_github_receipt(self):
        # A forged but internally identical observation proves only integrity.
        p=copy.deepcopy(self.original)
        p["review_observation"]["reviewer_login"]="forged"
        self.assertIsNone(self.validate(sealed(p)))
        self.assertFalse(p["release_authorized"])

    def test_cli_publish_invokes_integrity_check_before_write(self):
        from tests.i033e import test_protected_pr_batch_gate_red as transport
        from unittest.mock import patch
        import tempfile, os, io
        from pathlib import Path
        cli=transport.cli()
        report=copy.deepcopy(self.observation)
        report["provenance"]="github-live-rest-verified-at-this-run;not-offline-signed"
        with tempfile.TemporaryDirectory() as directory, patch.object(
            cli,"fetch_pr_head_context",return_value=(
                self.packet,self.ledger,self.read,
            )
        ),patch.object(cli,"evaluate_live_gate",return_value=report),patch(
            "tfont.overlay_handoff.verify_overlay_handoff_integrity",
            side_effect=ValueError("structural gate rejected")
        ),patch("sys.argv",["gate","--from-pr-head","--publish-handoff"]),patch(
            "sys.stdout",new=io.StringIO()
        ),patch("sys.stderr",new=io.StringIO()):
            previous=os.getcwd()
            try:
                os.chdir(directory)
                self.assertEqual(cli.main(),1)
                self.assertFalse(Path("batch-review-pack.json").exists())
            finally:
                os.chdir(previous)


if __name__=="__main__":
    unittest.main()
