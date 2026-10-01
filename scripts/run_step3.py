"""STEP 3: leakage-safe labels and baseline models. Does not modify STEP 2 features."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.step3 import run_step3  # noqa: E402


def main() -> int:
    summary = run_step3(ROOT)
    skip = {"feature_list", "label_candidates", "models"}
    printable = {k: v for k, v in summary.items() if k not in skip}
    printable["label_candidates"] = summary["label_candidates"]
    printable["models"] = summary["models"]
    print(json.dumps(printable, indent=2, default=str))
    if not summary["ok"]:
        print("STEP 3 validation failed.", file=sys.stderr)
        return 1
    print("STEP 3 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
