"""Write a machine-readable record of the inputs and environment for an audit."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRACKED_PACKAGES = ("numpy", "openpyxl", "pandas", "plotly", "scikit-learn", "scipy", "streamlit")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path, root: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        label = str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        label = str(path.resolve())
    return {
        "path": label,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def compare_project_inputs(root: Path) -> dict:
    """Compare app CSV and preferred audit workbook after schema normalization."""
    csv_path = root / "data" / "sugar_cosmetics_instagram_data.csv"
    excel_path = root / "data" / "sugar_cosmetics_instagram_data.xlsx"
    if not csv_path.is_file() or not excel_path.is_file():
        return {"status": "not_comparable", "reason": "Both project inputs are required."}

    csv = pd.read_csv(csv_path)
    excel = pd.read_excel(excel_path)
    normalize = lambda cols: [
        "_".join("".join(ch.lower() if ch.isalnum() else " " for ch in str(name)).split())
        for name in cols
    ]
    csv.columns = normalize(csv.columns)
    excel.columns = normalize(excel.columns)
    if csv.shape != excel.shape or list(csv.columns) != list(excel.columns):
        return {
            "status": "different",
            "csv_shape": list(csv.shape),
            "excel_shape": list(excel.shape),
            "csv_columns": list(csv.columns),
            "excel_columns": list(excel.columns),
        }

    left, right = csv.copy(), excel.copy()
    for column in left.columns:
        if column == "post_date":
            left[column] = pd.to_datetime(left[column], errors="coerce").dt.strftime("%Y-%m-%d")
            right[column] = pd.to_datetime(right[column], errors="coerce").dt.strftime("%Y-%m-%d")
        elif column in {"impressions", "reach", "likes", "comments", "shares", "saves", "profile_visits", "follows"}:
            left[column] = pd.to_numeric(left[column], errors="coerce")
            right[column] = pd.to_numeric(right[column], errors="coerce")
        else:
            left[column] = left[column].astype("string").str.strip()
            right[column] = right[column].astype("string").str.strip()

    equal = left.eq(right) | (left.isna() & right.isna())
    mismatched_cells = int((~equal).to_numpy().sum())
    return {
        "status": "match" if mismatched_cells == 0 else "different",
        "rows": int(len(left)),
        "columns": int(len(left.columns)),
        "mismatched_cells": mismatched_cells,
        "comparison": "cell-by-cell after normalized headers, dates, numbers, and category whitespace",
    }


def record_density(root: Path) -> dict:
    """Report row density without assuming that rows are posts."""
    path = root / "data" / "sugar_cosmetics_instagram_data.csv"
    if not path.is_file():
        return {"status": "unavailable"}
    frame = pd.read_csv(path, usecols=["post_date"])
    dates = pd.to_datetime(frame["post_date"], errors="coerce").dropna()
    if dates.empty:
        return {"status": "unavailable", "reason": "No parseable dates."}
    calendar_days = int((dates.max().normalize() - dates.min().normalize()).days + 1)
    return {
        "records": int(len(frame)),
        "valid_dates": int(len(dates)),
        "unique_dates": int(dates.dt.normalize().nunique()),
        "calendar_days_in_span": calendar_days,
        "records_per_calendar_day_in_span": round(len(frame) / calendar_days, 3),
        "interpretation": "Record density only; row grain is undocumented, so this is not a posting-frequency estimate.",
    }


def category_balance(root: Path) -> dict:
    """Quantify observed category balance without inferring the sampling method."""
    path = root / "data" / "sugar_cosmetics_instagram_data.csv"
    columns = ["post_type", "campaign_type"]
    if not path.is_file():
        return {"status": "unavailable"}
    frame = pd.read_csv(path, usecols=columns)
    result = {}
    for column in columns:
        counts = frame[column].fillna("<missing>").value_counts(dropna=False)
        result[column] = {
            "counts": {str(key): int(value) for key, value in counts.items()},
            "shares": {str(key): round(float(value / len(frame)), 6) for key, value in counts.items()},
            "largest_to_smallest_count_ratio": (
                round(float(counts.max() / counts.min()), 6) if not counts.empty and counts.min() else None
            ),
        }
    return {
        "records": int(len(frame)),
        "categories": result,
        "interpretation": "Near-even category counts are a sampling diagnostic, not evidence of representativeness.",
    }


def git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def build_manifest(root: Path, source: Path) -> dict:
    source = source.resolve()
    root = root.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Source data not found: {source}")

    versions = {}
    for package in TRACKED_PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None

    code_paths = [root / "app.py"]
    for directory in ("pages", "src", "tests", "utils"):
        code_paths.extend((root / directory).rglob("*.py"))
    code_records = {}
    for path in sorted(code_paths):
        record = file_record(path, root)
        if record:
            code_records[record["path"].replace("\\", "/")] = record

    return {
        "manifest_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_revision": git_revision(root),
        "selected_source": file_record(source, root),
        "project_data_files": {
            "dashboard_default_csv": file_record(
                root / "data" / "sugar_cosmetics_instagram_data.csv", root
            ),
            "audit_preferred_excel": file_record(
                root / "data" / "sugar_cosmetics_instagram_data.xlsx", root
            ),
            "audit_csv_fallback": file_record(
                root / "data" / "sugar_cosmetics_instagram_data.csv", root
            ),
            "business_impact_attribution_template": file_record(
                root / "data" / "business_impact_attribution_template.csv", root
            ),
        },
        "project_code": code_records,
        "project_documentation": {
            "readme": file_record(root / "README.md", root),
            "data_provenance": file_record(root / "DATA_PROVENANCE.md", root),
            "business_impact_data_contract": file_record(
                root / "BUSINESS_IMPACT_DATA_CONTRACT.md", root
            ),
            "review_checklist": file_record(root / "PROJECT_REVIEW_CHECKLIST.md", root),
            "implementation_review": file_record(
                root / "reports" / "implementation_review.md", root
            ),
            "model_monitoring_plan": file_record(
                root / "MODEL_MONITORING_PLAN.md", root
            ),
        },
        "project_environment": {
            "dependency_ranges": file_record(root / "requirements.txt", root),
            "dependency_lock": file_record(root / "requirements-lock.txt", root),
        },
        "project_analysis_artifacts": {
            "model_evaluation": file_record(root / "reports" / "model_evaluation.json", root),
            "category_rate_inference": file_record(
                root / "reports" / "category_rate_inference.json", root
            ),
            "model_holdout_predictions": file_record(
                root / "reports" / "model_holdout_predictions.csv", root
            ),
            "executive_report_docx": file_record(
                root / "reports" / "Sugar_Cosmetics_Instagram_Executive_Report.docx", root
            ),
        },
        "input_consistency": compare_project_inputs(root),
        "record_density": record_density(root),
        "category_balance": category_balance(root),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": versions,
        },
        "manifest_generator_sha256": sha256_file(Path(__file__).resolve()),
        "audit_notebook_sha256": sha256_file(root / "notebooks" / "01_data_validation_and_eda.ipynb"),
        "dependency_lock_sha256": sha256_file(root / "requirements-lock.txt"),
        "provenance_note": (
            "A file hash identifies these exact bytes; it does not establish the data owner, "
            "collection method, authenticity, or permission to use the data."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Input file to fingerprint")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "reproducibility_manifest.json",
        help="Manifest JSON output path",
    )
    args = parser.parse_args()

    default_source = ROOT / "data" / "sugar_cosmetics_instagram_data.xlsx"
    if not default_source.exists():
        default_source = ROOT / "data" / "sugar_cosmetics_instagram_data.csv"
    source = args.source or default_source
    output = args.output if args.output.is_absolute() else ROOT / args.output

    manifest = build_manifest(ROOT, source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote reproducibility manifest: {output}")


if __name__ == "__main__":
    main()
