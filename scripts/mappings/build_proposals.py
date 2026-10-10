#!/usr/bin/env python3
"""Emit or check four unapproved POS proposals without a per-mapping release."""
from __future__ import annotations

import argparse
from pathlib import Path

from tfont.batch_proposals import compile_candidate_batch, load_ledger, serialized


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/research/data/generated/i033c/adj-adv-candidates.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    result = serialized(compile_candidate_batch(load_ledger()))
    if args.stdout:
        print(result, end="")
    elif args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != result:
            raise SystemExit("I-033C generated unapproved batch candidates missing/stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
