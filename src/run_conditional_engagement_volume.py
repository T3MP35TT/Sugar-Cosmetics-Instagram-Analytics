"""Run the exposure-conditional engagement volume evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from conditional_engagement_model import evaluate_conditional_engagement_volume


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "sugar_cosmetics_instagram_data.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    report = evaluate_conditional_engagement_volume(args.input, args.output_dir)
    holdout = report["holdout"]
    print(f"Holdout records: {report['split']['holdout_records']:,}")
    print(f"Median baseline MAE: {holdout['median_baseline']['mae']:,.2f} engagements")
    print(f"Ridge MAE: {holdout['ridge']['mae']:,.2f} engagements")
    print(f"Ridge holdout R²: {holdout['ridge']['r2']:.3f}")
    print(f"Wrote report and predictions to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
