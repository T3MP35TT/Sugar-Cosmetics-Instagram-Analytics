"""Generate reproducible uncertainty intervals for descriptive category contrasts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from analytics import add_features, load_data
from inference import category_rate_contrasts


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records"))


def build_report(source: Path, bootstrap_reps: int, random_state: int) -> dict:
    data = add_features(load_data(source))
    data["post_date"] = pd.to_datetime(data["post_date"], errors="coerce")
    dimensions = ("post_type", "campaign_type")
    results = {
        dimension: safe_records(
            category_rate_contrasts(
                data,
                dimension,
                bootstrap_reps=bootstrap_reps,
                block_days=7,
                confidence_level=0.95,
                random_state=random_state,
            )
        )
        for dimension in dimensions
    }
    block_sensitivity = {
        str(block_days): {
            dimension: safe_records(
                category_rate_contrasts(
                    data,
                    dimension,
                    bootstrap_reps=bootstrap_reps,
                    block_days=block_days,
                    confidence_level=0.95,
                    random_state=random_state,
                )
            )
            for dimension in dimensions
        }
        for block_days in (3, 14)
    }
    dates = data["post_date"].dropna()
    try:
        source_label = str(source.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        source_label = str(source.resolve())
    return {
        "report_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path": source_label,
            "sha256": file_sha256(source),
            "rows": int(len(data)),
            "date_min": str(dates.min().date()) if not dates.empty else None,
            "date_max": str(dates.max().date()) if not dates.empty else None,
        },
        "method": {
            "estimand": "Category weighted engagement rate minus the weighted rate for all other categories, in percentage points.",
            "rate": "Sum of likes, comments, shares, and saves divided by summed post-level reach; positive-reach rows only.",
            "interval": "Simultaneous percentile interval using a shared max-deviation critical value across categories within each dimension.",
            "resampling_unit": "Circular moving calendar-date blocks; zero-activity days remain in the calendar sequence.",
            "selected_block_days": 7,
            "block_length_sensitivity_days": [3, 14],
            "bootstrap_reps": bootstrap_reps,
            "confidence_level": 0.95,
            "random_state": random_state,
            "scope": "Full app CSV, not the dashboard's interactive filters.",
            "limitations": [
                "Inference is conditional on dates being suitable resampling blocks and the supplied values being valid.",
                "The row grain, collection process, and sample representativeness are unverified.",
                "Intervals do not adjust for confounding, prove causality, or establish brand performance.",
                "An interval excluding zero does not justify changing strategy without a controlled test.",
            ],
        },
        "results": results,
        "block_length_sensitivity": block_sensitivity,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "data" / "sugar_cosmetics_instagram_data.csv",
        help="CSV input (defaults to the dashboard CSV)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "category_rate_inference.json",
        help="JSON output path",
    )
    parser.add_argument("--bootstrap-reps", type=int, default=5000)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    source = args.source if args.source.is_absolute() else ROOT / args.source
    output = args.output if args.output.is_absolute() else ROOT / args.output
    report = build_report(source, args.bootstrap_reps, args.random_state)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote descriptive inference report: {output}")


if __name__ == "__main__":
    main()
