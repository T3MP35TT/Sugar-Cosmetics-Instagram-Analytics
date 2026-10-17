import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import pytest

from analytics import (
    CATEGORICAL,
    NUMERIC,
    REQUIRED,
    add_features,
    hashtag_table,
    load_data,
    summarize_data,
    validate_data,
    weekday_table,
)


def sample_df():
    return pd.DataFrame({
        "post_date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
        "post_type": ["Reel", "Image"],
        "campaign_type": ["Launch", "Tutorial"],
        "hashtags": ["#beauty #makeup", "#beauty"],
        "audience_emotion": ["happy", "curious"],
        "engagement_source": ["organic", "organic"],
        "impressions": [1000, 500],
        "reach": [800, 400],
        "likes": [80, 40],
        "comments": [8, 4],
        "shares": [4, 2],
        "saves": [8, 4],
        "profile_visits": [40, 20],
        "follows": [8, 4],
    })


def flags_by_check(result):
    return {item["check"]: item["count"] for item in result["flags"]}


# Feature calculations

def test_add_features_calculates_engagement_and_conversion_rates():
    result = add_features(sample_df())
    assert result["total_engagements"].tolist() == [100, 50]
    assert np.isclose(result.loc[0, "engagement_rate"], 100 / 800)
    assert np.isclose(result.loc[0, "profile_visit_rate"], 40 / 800)
    assert np.isclose(result.loc[0, "follow_per_visit_rate"], 8 / 40)
    assert np.isclose(result.loc[0, "follow_per_reach_rate"], 8 / 800)


def test_zero_reach_produces_missing_reach_based_rates():
    df = sample_df()
    df.loc[0, "reach"] = 0
    result = add_features(df)
    assert pd.isna(result.loc[0, "engagement_rate"])
    assert pd.isna(result.loc[0, "profile_visit_rate"])
    assert pd.isna(result.loc[0, "follow_per_reach_rate"])


def test_zero_profile_visits_produces_missing_follow_per_visit_rate():
    df = sample_df()
    df.loc[0, "profile_visits"] = 0
    result = add_features(df)
    assert pd.isna(result.loc[0, "follow_per_visit_rate"])


def test_missing_engagement_metric_does_not_become_zero():
    df = sample_df()
    df.loc[0, "likes"] = np.nan
    result = add_features(df)
    assert pd.isna(result.loc[0, "total_engagements"])
    assert pd.isna(result.loc[0, "engagement_rate"])


def test_missing_one_engagement_metric_keeps_other_rows_calculable():
    df = sample_df()
    df.loc[0, "likes"] = np.nan
    result = add_features(df)
    assert result.loc[1, "total_engagements"] == 50
    assert np.isclose(result.loc[1, "engagement_rate"], 0.125)


def test_features_do_not_modify_input_dataframe():
    df = sample_df()
    original_columns = list(df.columns)
    add_features(df)
    assert list(df.columns) == original_columns
    assert "total_engagements" not in df.columns


def test_date_features_are_created_correctly():
    result = add_features(sample_df())
    assert result["month"].tolist() == ["2025-01", "2025-01"]
    assert result["weekday"].tolist() == ["Wednesday", "Thursday"]


# Dataset summaries

def test_summarize_empty_dataframe():
    df = add_features(sample_df()).iloc[0:0]
    result = summarize_data(df)
    assert result["records"] == 0
    assert result["total_engagements"] == 0
    assert result["cumulative_post_reach"] == 0
    assert np.isnan(result["weighted_engagement_rate"])
    assert np.isnan(result["average_post_engagement_rate"])


def test_summarize_uses_eligible_rows_for_weighted_rate():
    df = add_features(sample_df())
    df.loc[0, "total_engagements"] = np.nan
    result = summarize_data(df)
    assert np.isclose(result["weighted_engagement_rate"], 50 / 400)


def test_summary_reports_cumulative_post_reach_not_unique_reach():
    df = add_features(sample_df())
    result = summarize_data(df)
    assert result["cumulative_post_reach"] == 1200


def test_summary_calculates_average_post_rate_from_available_rates():
    df = add_features(sample_df())
    result = summarize_data(df)
    assert np.isclose(result["average_post_engagement_rate"], (0.125 + 0.125) / 2)


def test_summary_returns_nan_weighted_rate_when_no_positive_eligible_reach():
    df = add_features(sample_df())
    df["reach"] = 0
    result = summarize_data(df)
    assert np.isnan(result["weighted_engagement_rate"])


# Data validation

def test_validate_reports_missing_numeric_and_categorical_values():
    df = sample_df()
    df.loc[0, "likes"] = np.nan
    df.loc[1, "post_type"] = " "
    counts = flags_by_check(validate_data(df))
    assert counts["Missing or non-numeric values in likes"] == 1
    assert counts["Missing or blank values in post_type"] == 1


def test_duplicate_rows_are_counted():
    df = sample_df()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    assert validate_data(df)["duplicate_rows"] == 1


def test_validate_flags_negative_values():
    df = sample_df()
    df.loc[0, "likes"] = -1
    counts = flags_by_check(validate_data(df))
    assert counts["Negative values in likes"] == 1


def test_validate_flags_invalid_and_missing_dates():
    df = sample_df()
    df["post_date"] = df["post_date"].astype(object)
    df.loc[0, "post_date"] = "not-a-date"
    df.loc[1, "post_date"] = None
    counts = flags_by_check(validate_data(df))
    assert counts["Invalid or missing post dates"] == 2


def test_validate_flags_impressions_lower_than_reach():
    df = sample_df()
    df.loc[0, "impressions"] = 700
    counts = flags_by_check(validate_data(df))
    assert counts["Impressions lower than reach"] == 1


def test_validate_flags_engagements_greater_than_reach():
    df = sample_df()
    df.loc[0, ["likes", "comments", "shares", "saves"]] = [790, 20, 10, 5]
    counts = flags_by_check(validate_data(df))
    assert counts["Engagements greater than reach"] == 1


def test_validate_flags_zero_reach_and_zero_profile_visits():
    df = sample_df()
    df.loc[0, "reach"] = 0
    df.loc[1, "profile_visits"] = 0
    counts = flags_by_check(validate_data(df))
    assert counts["Zero reach"] == 1
    assert counts["Zero profile visits"] == 1


def test_validate_reports_row_column_and_date_summary():
    result = validate_data(sample_df())
    assert result["rows"] == 2
    assert result["columns"] == len(sample_df().columns)
    assert result["date_min"] is not None
    assert result["date_max"] is not None
    assert result["post_types"] == 2
    assert result["campaign_types"] == 2


def test_validate_rejects_missing_required_columns():
    df = sample_df().drop(columns=["likes"])
    with pytest.raises(ValueError, match="Required columns missing"):
        validate_data(df)


def test_load_data_rejects_missing_required_columns(tmp_path):
    df = sample_df().drop(columns=["reach"])
    path = tmp_path / "missing_column.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Required columns missing"):
        load_data(path)


def test_load_data_coerces_invalid_dates_and_numeric_values(tmp_path):
    df = sample_df()
    df["post_date"] = df["post_date"].astype(object)
    df.loc[0, "post_date"] = "invalid-date"
    df["likes"] = df["likes"].astype(object)
    df.loc[1, "likes"] = "not-a-number"
    df.loc[0, "post_type"] = " Reel "
    path = tmp_path / "dirty_data.csv"
    df.to_csv(path, index=False)

    loaded = load_data(path)
    assert pd.isna(loaded.loc[0, "post_date"])
    assert pd.isna(loaded.loc[1, "likes"])
    assert loaded.loc[0, "post_type"] == "Reel"


def test_load_data_converts_blank_categories_to_missing(tmp_path):
    df = sample_df()
    df.loc[0, "post_type"] = "   "
    path = tmp_path / "blank_category.csv"
    df.to_csv(path, index=False)

    loaded = load_data(path)
    assert pd.isna(loaded.loc[0, "post_type"])


# Weekday aggregation

def test_weekday_table_calculates_weighted_engagement_rate():
    df = add_features(sample_df())
    result = weekday_table(df).set_index("weekday")
    assert np.isclose(result.loc["Wednesday", "weighted_engagement_rate"], 100 / 800)
    assert np.isclose(result.loc["Thursday", "weighted_engagement_rate"], 50 / 400)


def test_weekday_table_preserves_record_counts():
    df = add_features(sample_df())
    result = weekday_table(df)
    assert result["records"].sum() == len(df)


# Hashtag analysis

def test_hashtag_totals_overlap_for_multi_hashtag_posts():
    df = add_features(sample_df())
    result = hashtag_table(df).set_index("hashtag")
    assert result.loc["#beauty", "records"] == 2
    assert result.loc["#makeup", "records"] == 1
    assert result.loc["#beauty", "reach"] == 1200
    assert result.loc["#makeup", "reach"] == 800


def test_hashtag_parsing_is_case_insensitive_and_deduplicates_per_post():
    df = add_features(sample_df().iloc[[0]].copy())
    df.loc[df.index[0], "hashtags"] = "#Beauty #beauty #MAKEUP"
    result = hashtag_table(df).set_index("hashtag")
    assert result.loc["#beauty", "records"] == 1
    assert result.loc["#makeup", "records"] == 1


def test_hashtag_table_ignores_rows_without_hashtags():
    df = add_features(sample_df())
    df["hashtags"] = ["", "no hashtag here"]
    result = hashtag_table(df)
    assert result.empty
    assert "weighted_engagement_rate" in result.columns


def test_hashtag_table_has_expected_output_columns():
    result = hashtag_table(add_features(sample_df()))
    expected = {
        "hashtag", "records", "reach", "engagements", "likes", "comments",
        "shares", "saves", "follows", "weighted_engagement_rate",
    }
    assert expected.issubset(set(result.columns))


def test_schema_constants_cover_expected_fields():
    assert set(REQUIRED) == {"post_date", *CATEGORICAL, *NUMERIC}

