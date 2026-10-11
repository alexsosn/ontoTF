#!/usr/bin/env python3
"""Offline candidate-review worksheet; output is NEVER GitHub approval.

Examples (run on the exact candidate PR checkout, never in trusted CI):
  python scripts/mappings/prepare_external_review.py --dossier
  python scripts/mappings/prepare_external_review.py --template > decisions.json
  # Reviewer deliberately replaces EVERY null with accept/reject/needs-evidence.
  python scripts/mappings/prepare_external_review.py --review-decisions decisions.json

An independent authorized GitHub account must paste the last output into the
PR's "Approve" review field, not as an ordinary comment. The protected gate
rechecks current PR head, GitHub reviewer permission, and all decision digests.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from scripts.mappings.build_candidate_review_packet import (
    ROOT, MANIFEST, EVIDENCE_PREFIX, _read_json, _relative_path,
    build_packet,
)
from tfont.batch_proposals import packaged_resource
from tfont.reviewer_handoff import (
    reviewer_template, render_review_body, review_dossier,
)
from tfont.source_validation import loads_source


def load_review_context(root: Path):
    """Only present locally reproducible candidate packet and source records."""
    packet = json.loads(build_packet(root, mode="check"))
    manifest = _read_json(root, MANIFEST)
    candidates = manifest.get("evidence_resources", {})
    resources = {
        name: _read_json(root, _relative_path(path, EVIDENCE_PREFIX))
        for name, path in candidates.items()
    }
    def reader(name: str):
        return resources[name] if name in resources else packaged_resource(name)
    return packet, reader


def _load_choices(path: Path):
    """Explicit local reviewer edits only; never reviewer authentication."""
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 100_000:
        raise ValueError("decision worksheet absent or unsafe size/path")
    content = path.read_text(encoding="utf-8")
    value = loads_source(content, format="json", source_name="reviewer-decisions")
    if type(value) is not dict:
        raise ValueError("decision worksheet must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="Exact candidate PR checkout (local, never trusted approval)")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dossier", action="store_true")
    modes.add_argument("--template", action="store_true")
    modes.add_argument("--review-decisions", type=Path, metavar="FILE")
    args = parser.parse_args()
    packet, reader = load_review_context(args.root)
    if args.dossier:
        output = review_dossier(packet, resource_loader=reader)
    elif args.template:
        output = json.dumps(reviewer_template(packet), indent=2,
                            sort_keys=True, ensure_ascii=False)
    else:
        output = render_review_body(packet, _load_choices(args.review_decisions))
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
