"""STEP 2: build leakage-safe XAUUSD features. Does not modify STEP 1 files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.data.mtf_features import run_step2  # noqa: E402


def main() -> int:
    summary = run_step2(ROOT)
    printable = {k: v for k, v in summary.items() if k != "feature_list"}
    printable["feature_list"] = summary["feature_list"]
    print(json.dumps(printable, indent=2))
    if not summary["ok"]:
        print("STEP 2 validation failed.", file=sys.stderr)
        return 1
    print("STEP 2 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
