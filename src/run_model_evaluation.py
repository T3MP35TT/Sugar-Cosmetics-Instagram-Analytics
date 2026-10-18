"""Run the chronological engagement-rate model evaluation and write reports."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from modeling import run_model_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data" / "sugar_cosmetics_instagram_data.csv",
        help="Input CSV with the project schema",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "reports",
        help="Directory for JSON evaluation and holdout prediction CSV",
    )
    parser.add_argument("--seed", type=int, default=20261017)
    parser.add_argument("--bootstrap-repetitions", type=int, default=1000)
    args = parser.parse_args()
    report = run_model_evaluation(
        args.input,
        output_dir=args.output_dir,
        seed=args.seed,
        bootstrap_repetitions=args.bootstrap_repetitions,
    )
    result = report["holdout_evaluation"]
    print(f"One-SE selected approach: {report['tuning']['one_se_selected_approach']}")
    print(f"Holdout median-baseline MAE: {result['median_baseline']['mae']:.6f}")
    print(
        f"Best ML candidate ({report['tuning']['best_ml_candidate_estimator']}) holdout MAE: "
        f"{result['best_ml_candidate']['mae']:.6f}"
    )
    print(f"Recommended approach: {report['model_vs_baseline']['recommended_approach']}")
    print(f"Wrote reports to: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
