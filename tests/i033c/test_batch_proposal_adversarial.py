"""I-033C: adversarial separation between mechanical compilation and review authority."""
from __future__ import annotations

import copy
import unittest

from tfont.batch_proposals import BatchProposalError, compile_candidate_batch, load_ledger


class BatchProposalAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.ledger = load_ledger()

    def bad(self, modifier):
        data = copy.deepcopy(self.ledger)
        modifier(data)
        with self.assertRaises(BatchProposalError):
            compile_candidate_batch(data)

    def test_duplicate_selector_and_unrecognized_native_value_fail(self):
        self.bad(lambda x: x["decisions"].append(copy.deepcopy(x["decisions"][0])))
        self.bad(lambda x: x["decisions"][0].__setitem__("value", "not-a-real-native-code"))

    def test_forbid_self_review_status_and_surplus_approval_fields(self):
        for field, value in (("review", {"status":"reviewed"}), ("reviewed", True),
                             ("approved_by", "compiler"), ("source_digest", "sha256:forged")):
            with self.subTest(field=field):
                self.bad(lambda x, f=field, v=value: x["decisions"][0].__setitem__(f, v))

    def test_original_source_revision_and_ontology_lock_must_match(self):
        self.bad(lambda x: x["source_registry"]["bhsa"].__setitem__("source_revision", "0"*40))
        self.bad(lambda x: x.__setitem__("ontology_revision", "0"*40))
        self.bad(lambda x: x["ontology_evidence_resources"].__setitem__("adjective",
            "resources/ontologies/olia/invalid/adjective-evidence.json"))
        self.bad(lambda x: x["source_registry"]["bhsa"].__setitem__("evidence_resource",
            "resources/profiles/syriac/0.4.0/evidence/native-adj-adv-pos.json"))

    def test_path_traversal_and_unregistered_corpus_rejected(self):
        self.bad(lambda x: x["source_registry"]["bhsa"].__setitem__("evidence_resource",
            "../resources/profiles/bhsa/0.4.0/evidence/native-adj-adv-pos.json"))
        self.bad(lambda x: x["decisions"][0].__setitem__("corpus_id", "unknown"))

    def test_modified_source_content_without_digest_is_rejected(self):
        def forged(path, original_loader):
            record = copy.deepcopy(original_loader(path))
            if path.endswith("/native-adj-adv-pos.json") and "/bhsa/" in path:
                record["reviewed_content"]["source_definitions"]["adjv"]["gloss"]="not-source-evidence"
            return record
        from tfont.batch_proposals import packaged_resource
        with self.assertRaises(BatchProposalError):
            compile_candidate_batch(self.ledger, resource_loader=lambda path: forged(path,packaged_resource))

    def test_forged_ontology_type_and_target_rejected(self):
        from tfont.batch_proposals import packaged_resource
        def forged(path):
            value = copy.deepcopy(packaged_resource(path))
            if path.endswith("/adjective-evidence.json"):
                value["reviewed_content"]["rdf_type"] = "owl:ObjectProperty"
            return value
        with self.assertRaises(BatchProposalError):
            compile_candidate_batch(self.ledger, resource_loader=forged)
        self.bad(lambda x: x["decisions"][0].__setitem__("term_key", "missing-target"))

    def test_row_order_does_not_change_generated_output(self):
        a = compile_candidate_batch(self.ledger)
        reversed_ledger = copy.deepcopy(self.ledger)
        reversed_ledger["decisions"].reverse()
        self.assertEqual(a, compile_candidate_batch(reversed_ledger))


if __name__ == "__main__":
    unittest.main()
