import hashlib
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reproducibility_manifest import (
    category_balance,
    compare_project_inputs,
    file_record,
    record_density,
)


def write_project_inputs(root: Path, *, workbook_post_type="Reel"):
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    frame = pd.DataFrame(
        {
            "post_date": ["2025-01-01", "2025-01-03"],
            "post_type": ["Reel", "Image"],
            "campaign_type": ["Launch", "Tutorial"],
            "hashtags": ["#beauty", "#makeup"],
            "audience_emotion": ["happy", "curious"],
            "engagement_source": ["organic", "organic"],
            "impressions": [100, 200],
            "reach": [80, 160],
            "likes": [10, 20],
            "comments": [1, 2],
            "shares": [1, 2],
            "saves": [2, 4],
            "profile_visits": [5, 10],
            "follows": [1, 2],
        }
    )
    frame.to_csv(data_dir / "sugar_cosmetics_instagram_data.csv", index=False)
    workbook = frame.copy()
    workbook.loc[0, "post_type"] = workbook_post_type
    workbook.rename(columns=lambda value: value.replace("_", " ").title()).to_excel(
        data_dir / "sugar_cosmetics_instagram_data.xlsx", index=False
    )


def test_file_record_includes_sha256_and_relative_path(tmp_path):
    sample = tmp_path / "sample.csv"
    sample.write_bytes(b"row\n1\n")

    result = file_record(sample, tmp_path)

    assert result["path"] == "sample.csv"
    assert result["size_bytes"] == sample.stat().st_size
    assert result["sha256"] == hashlib.sha256(sample.read_bytes()).hexdigest()


def test_compare_project_inputs_matches_normalized_headers_and_dates(tmp_path):
    write_project_inputs(tmp_path, workbook_post_type="Reel")

    result = compare_project_inputs(tmp_path)

    assert result["status"] == "match"
    assert result["rows"] == 2
    assert result["mismatched_cells"] == 0


def test_compare_project_inputs_reports_cell_mismatches(tmp_path):
    write_project_inputs(tmp_path, workbook_post_type="Story")

    result = compare_project_inputs(tmp_path)

    assert result["status"] == "different"
    assert result["mismatched_cells"] == 1


def test_record_density_reports_records_without_assuming_post_grain(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    pd.DataFrame({"post_date": ["2025-01-01", "2025-01-03"]}).to_csv(
        data_dir / "sugar_cosmetics_instagram_data.csv", index=False
    )

    result = record_density(tmp_path)

    assert result["records"] == 2
    assert result["unique_dates"] == 2
    assert result["calendar_days_in_span"] == 3
    assert result["records_per_calendar_day_in_span"] == 0.667
    assert "row grain is undocumented" in result["interpretation"]


def test_category_balance_reports_shares_and_warns_against_representativeness(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    pd.DataFrame(
        {
            "post_type": ["Reel", "Reel", "Image", "Image"],
            "campaign_type": ["Launch", "Launch", "Launch", "Tutorial"],
        }
    ).to_csv(data_dir / "sugar_cosmetics_instagram_data.csv", index=False)

    result = category_balance(tmp_path)

    assert result["records"] == 4
    assert result["categories"]["post_type"]["shares"] == {"Reel": 0.5, "Image": 0.5}
    assert result["categories"]["post_type"]["largest_to_smallest_count_ratio"] == 1.0
    assert "not evidence of representativeness" in result["interpretation"]
