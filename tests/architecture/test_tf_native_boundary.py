import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
P001_RUNTIME_AMENDMENT = ROOT / "docs" / "plans" / "P-001-tf-native-runtime-boundary-amendment.md"
PARENT_SCHEMA = ROOT / "src" / "tfont" / "schemas" / "parent-component-manifest.schema.json"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agents_pins_tf_native_materializer_boundary():
    text = _read("AGENTS.md")
    assert "TF-native runtime boundary" in text
    assert "already materialized Text-Fabric" in text
    assert "corpus materializer" in text
    assert "not an instruction to dereference it" in text
    assert "Do not add a generic sidecar" in text


def test_r005_supersession_amendment_preserves_history_and_corrects_oracc_boundary():
    text = _read("docs/research/A-001-r005-oracc-zero-span-supersession.md")
    assert "Superseded ORACC zero-span architecture" in text
    assert "R-005 remains unchanged" in text
    assert "ADR-0001-empty-slots-not-sidecars.md" in text
    assert "synthetic/empty" in text


def test_r007_supersession_rejects_generic_external_carrier():
    text = _read("docs/research/A-001-r007-external-carrier-supersession.md")
    assert "R-007 remains unchanged" in text
    assert "generic `sidecar/native-adapter` carrier is superseded" in text
    assert "not a baseline TFont runtime carrier" in text
    assert "Slot" in text
    assert "slotLink" in text
    assert "technicalAnchor" in text


def test_r007_supersession_reconciles_oracc_with_current_tf_architecture():
    text = _read("docs/research/A-001-r007-external-carrier-supersession.md")
    assert "ADR-0001-empty-slots-not-sidecars.md" in text
    assert "synthetic/empty" in text
    assert "materialized" in text.lower()
    assert "ORACC" in text


def test_supersession_states_storage_is_not_semantic_carrier_type():
    text = _read("docs/research/A-001-r007-external-carrier-supersession.md")
    assert "Storage location or source format is not a semantic carrier type" in text


def test_a001_does_not_replace_adapter_with_another_generic_runtime_api():
    research = _read("docs/research/A-001-tf-native-runtime-boundary.md")
    plan = _read("docs/plans/A-001-tf-native-runtime-boundary-plan.md")
    combined = research + "\n" + plan
    assert "No production Python runtime" in combined
    assert "does not own generic ingestion/query adapters" in combined
    assert "two independent real corpus cases" in combined


def test_p001_sections_6_and_7_are_explicitly_superseded_for_execution():
    text = P001_RUNTIME_AMENDMENT.read_text(encoding="utf-8")
    lower = text.lower()
    assert "p-001 sections 6 and 7" in lower
    assert "native-adapter" in text
    assert "adapter capability/version invariant" in lower
    assert "sidecar field/path invariant" in lower
    assert "sidecar-zero-span" in lower
    assert "not a baseline executable" in lower
    assert "synthetic/empty" in lower


def test_legacy_v1_component_kinds_are_identity_only_not_runtime_permission():
    schema = json.loads(PARENT_SCHEMA.read_text(encoding="utf-8"))
    kinds = set(
        schema["properties"]["components"]["items"]["properties"]["kind"]["enum"]
    )
    legacy = {"sidecar", "catalogue", "zero-span", "native-adapter"}
    assert legacy <= kinds  # control: v1 really remains backward-readable in this PR

    text = P001_RUNTIME_AMENDMENT.read_text(encoding="utf-8").lower()
    assert "legacy identity compatibility labels" in text
    assert "does not authorize an executable/query carrier" in text
    assert "structural acceptance" in text
    assert "p-002/p-003" in text
    assert "versioned" in text


def test_p001_reconciliation_preserves_still_valid_foundation_contracts():
    text = P001_RUNTIME_AMENDMENT.read_text(encoding="utf-8").lower()
    for phrase in (
        "component-aware parent identity",
        "deterministic compatibility evidence",
        "review/evidence binding",
        "compatibility states",
        "fail-closed activation",
    ):
        assert phrase in text
