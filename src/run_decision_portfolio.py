"""Generate the illustrative decision portfolio and sample-size scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from decision_portfolio import build_decision_portfolio


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "assumed_decision_portfolio.json")
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    portfolio = build_decision_portfolio()
    output.write_text(json.dumps(portfolio, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(portfolio['decisions'])} illustrative decisions to {output}")
    for decision in portfolio["decisions"]:
        sample = decision["sample_size"]
        impact = decision["impact_scenario"]
        print(
            f"{decision['sequence']}. {decision['decision']}: "
            f"{sample['total']:,} total units ({sample['per_arm']:,}/arm); "
            f"scenario net contribution {portfolio['currency']} {impact['net_contribution_after_cost']:,.0f}/month"
        )


if __name__ == "__main__":
    main()
