"""STEP 1: audit and clean LiteFinance XAUUSD files. Does not modify data/raw."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.data.litefinance import run_step1  # noqa: E402


def main() -> int:
    summary = run_step1(ROOT)
    print(json.dumps(summary, indent=2))
    if not summary["ok"]:
        print("STEP 1 validation failed.", file=sys.stderr)
        return 1
    print("STEP 1 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
