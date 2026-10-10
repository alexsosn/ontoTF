#!/usr/bin/env python3
"""Reproduce a 30-decision reviewed POS parity report, without authorizing new rows."""
from __future__ import annotations

import argparse
from pathlib import Path
from tfont.batch_compiler import ROOT, load_pilot, parity_report, serialized

OUTPUT = ROOT / "docs/research/data/generated/i033a/pos-pilot-summary.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = serialized(parity_report(load_pilot()))
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != result:
            raise SystemExit("I-033A batch parity summary missing or stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
