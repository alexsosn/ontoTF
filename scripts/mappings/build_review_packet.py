#!/usr/bin/env python3
"""Produce or verify unapproved JCS-bound batch review packet, never release."""
from __future__ import annotations

import argparse
from pathlib import Path
from tfont.batch_proposals import load_ledger
from tfont.review_packets import build_review_packet, serialized, verify_review_packet

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/research/data/generated/i033d/adj-adv-review-request.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    ledger = load_ledger()
    packet = build_review_packet(ledger)
    verify_review_packet(packet, ledger)
    content = serialized(packet)
    if args.stdout:
        print(content, end="")
    elif args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("I-033D review request missing/stale; no approval is implied")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
