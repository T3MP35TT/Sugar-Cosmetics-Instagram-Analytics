import re

import numpy as np
import pandas as pd

NUMERIC = [
    "impressions",
    "reach",
    "likes",
    "comments",
    "shares",
    "saves",
    "profile_visits",
    "follows",
]

CATEGORICAL = [
    "post_type",
    "campaign_type",
    "hashtags",
    "audience_emotion",
    "engagement_source",
]

REQUIRED = ["post_date", *NUMERIC, *CATEGORICAL]
ENGAGEMENT_COLUMNS = ["likes", "comments", "shares", "saves"]


def _parse_dates(values):
    """Parse mixed date formats without pandas' format-inference warning."""
    return pd.to_datetime(values, errors="coerce", format="mixed")


def load_data(path):
    """Load a CSV and normalize its date, numeric, and categorical columns."""
    df = pd.read_csv(path)
    missing = [column for column in REQUIRED if column not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing: {missing}")

    df["post_date"] = _parse_dates(df["post_date"])

    for column in NUMERIC:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in CATEGORICAL:
        df[column] = df[column].astype("string").str.strip()
        df[column] = df[column].replace("", pd.NA)

    return df


def _add_flag(flags, check, count):
    if count:
        flags.append({"check": check, "count": int(count)})


def validate_data(df):
    """Check schema and data-quality issues without changing the input."""
    missing_columns = [column for column in REQUIRED if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Required columns missing: {missing_columns}")

    work = df.copy()
    work["post_date"] = _parse_dates(work["post_date"])

    for column in NUMERIC:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    flags = []

    for column in NUMERIC:
        _add_flag(
            flags,
            f"Missing or non-numeric values in {column}",
            work[column].isna().sum(),
        )
        _add_flag(
            flags,
            f"Negative values in {column}",
            (work[column] < 0).fillna(False).sum(),
        )

    for column in CATEGORICAL:
        blank = work[column].isna() | work[column].astype("string").str.strip().eq("").fillna(False)
        _add_flag(flags, f"Missing or blank values in {column}", blank.sum())

    _add_flag(flags, "Invalid or missing post dates", work["post_date"].isna().sum())

    valid_pair = work["impressions"].notna() & work["reach"].notna()
    _add_flag(
        flags,
        "Impressions lower than reach",
        ((work["impressions"] < work["reach"]) & valid_pair).sum(),
    )

    engagements = work[ENGAGEMENT_COLUMNS].sum(axis=1, min_count=len(ENGAGEMENT_COLUMNS))
    valid_pair = engagements.notna() & work["reach"].notna()
    _add_flag(
        flags,
        "Engagements greater than reach",
        ((engagements > work["reach"]) & valid_pair).sum(),
    )

    _add_flag(flags, "Zero reach", work["reach"].eq(0).sum())
    _add_flag(flags, "Zero profile visits", work["profile_visits"].eq(0).sum())

    # If derived fields are already present, verify them against the source
    # columns. The raw source file may not contain these fields, so these
    # checks are conditional rather than treating absent derived columns as errors.
    if "total_engagements" in work.columns:
        supplied_total = pd.to_numeric(work["total_engagements"], errors="coerce")
        expected_total = engagements
        comparable = supplied_total.notna() & expected_total.notna()
        mismatch = comparable & ~np.isclose(
            supplied_total.fillna(0), expected_total.fillna(0), rtol=1e-9, atol=1e-9
        )
        _add_flag(flags, "Total engagements do not match likes + comments + shares + saves", mismatch.sum())

    if "engagement_rate" in work.columns:
        supplied_rate = pd.to_numeric(work["engagement_rate"], errors="coerce")
        expected_rate = engagements / work["reach"].where(work["reach"] > 0)
        comparable = supplied_rate.notna() & expected_rate.notna()
        mismatch = comparable & ~np.isclose(
            supplied_rate.fillna(0), expected_rate.fillna(0), rtol=1e-7, atol=1e-9
        )
        _add_flag(flags, "Engagement rate does not match total engagements / reach", mismatch.sum())

    valid_dates = work["post_date"].dropna()

    return {
        "rows": int(len(work)),
        "columns": int(len(work.columns)),
        "missing_cells": int(work.isna().sum().sum()),
        "duplicate_rows": int(work.duplicated().sum()),
        "date_min": str(valid_dates.min()) if not valid_dates.empty else None,
        "date_max": str(valid_dates.max()) if not valid_dates.empty else None,
        "post_types": int(work["post_type"].nunique(dropna=True)),
        "campaign_types": int(work["campaign_type"].nunique(dropna=True)),
        "flags": flags,
    }


def add_features(df):
    """Return a copy enriched with engagement and conversion metrics."""
    result = df.copy()
    result["post_date"] = _parse_dates(result["post_date"])

    for column in NUMERIC:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    result["total_engagements"] = result[ENGAGEMENT_COLUMNS].sum(
        axis=1, min_count=len(ENGAGEMENT_COLUMNS)
    )

    positive_reach = result["reach"].where(result["reach"] > 0)
    positive_visits = result["profile_visits"].where(result["profile_visits"] > 0)

    result["engagement_rate"] = result["total_engagements"] / positive_reach
    result["profile_visit_rate"] = result["profile_visits"] / positive_reach
    result["follow_per_visit_rate"] = result["follows"] / positive_visits
    result["follow_per_reach_rate"] = result["follows"] / positive_reach

    result["month"] = result["post_date"].dt.strftime("%Y-%m")
    result["weekday"] = result["post_date"].dt.day_name()
    return result


def summarize_data(df):
    """Calculate headline metrics, handling empty and ineligible data safely."""
    if df.empty:
        return {
            "records": 0,
            "total_engagements": 0,
            "cumulative_post_reach": 0,
            "weighted_engagement_rate": np.nan,
            "average_post_engagement_rate": np.nan,
        }

    engagements = pd.to_numeric(df["total_engagements"], errors="coerce")
    reach = pd.to_numeric(df["reach"], errors="coerce")
    valid_engagements = engagements.dropna()
    valid_reach = reach.dropna()

    eligible = engagements.notna() & reach.notna() & reach.gt(0)
    weighted_rate = (
        engagements.loc[eligible].sum() / reach.loc[eligible].sum()
        if eligible.any()
        else np.nan
    )

    if "engagement_rate" in df.columns:
        post_rates = pd.to_numeric(df["engagement_rate"], errors="coerce")
    else:
        post_rates = engagements / reach.where(reach > 0)

    return {
        "records": int(len(df)),
        "total_engagements": float(valid_engagements.sum()) if not valid_engagements.empty else 0,
        # This is summed post-level reach, not unique account-level reach.
        "cumulative_post_reach": float(valid_reach.sum()) if not valid_reach.empty else 0,
        "weighted_engagement_rate": float(weighted_rate) if pd.notna(weighted_rate) else np.nan,
        "average_post_engagement_rate": (
            float(post_rates.mean()) if post_rates.notna().any() else np.nan
        ),
    }


def weekday_table(df):
    """Aggregate records and engagement performance by weekday."""
    columns = [
        "weekday",
        "records",
        "reach",
        "engagements",
        "average_engagement_rate",
        "weighted_engagement_rate",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    work = df.copy()
    if "weekday" not in work.columns or "total_engagements" not in work.columns:
        work = add_features(work)

    result = (
        work.groupby("weekday", dropna=True)
        .agg(
            records=("weekday", "size"),
            reach=("reach", "sum"),
            engagements=("total_engagements", "sum"),
            average_engagement_rate=("engagement_rate", "mean"),
        )
        .reset_index()
    )

    result["weighted_engagement_rate"] = (
        result["engagements"] / result["reach"].where(result["reach"] > 0)
    )
    return result[columns]


def hashtag_table(df):
    """Summarize hashtag performance; posts with multiple tags overlap by design."""
    columns = [
        "hashtag",
        "records",
        "reach",
        "engagements",
        "likes",
        "comments",
        "shares",
        "saves",
        "follows",
        "weighted_engagement_rate",
    ]

    if df.empty or "hashtags" not in df.columns:
        return pd.DataFrame(columns=columns)

    work = df.copy()
    if "total_engagements" not in work.columns:
        work = add_features(work)

    rows = []
    for _, row in work.iterrows():
        raw_tags = row.get("hashtags")
        if pd.isna(raw_tags):
            continue

        # A hashtag is counted at most once per post; matching is case-insensitive.
        tags = {tag.lower() for tag in re.findall(r"#\w+", str(raw_tags))}
        for tag in tags:
            rows.append(
                {
                    "hashtag": tag,
                    "reach": row.get("reach", np.nan),
                    "engagements": row.get("total_engagements", np.nan),
                    "likes": row.get("likes", np.nan),
                    "comments": row.get("comments", np.nan),
                    "shares": row.get("shares", np.nan),
                    "saves": row.get("saves", np.nan),
                    "follows": row.get("follows", np.nan),
                }
            )

    if not rows:
        return pd.DataFrame(columns=columns)

    exploded = pd.DataFrame(rows)
    result = (
        exploded.groupby("hashtag", as_index=False)
        .agg(
            records=("hashtag", "size"),
            reach=("reach", "sum"),
            engagements=("engagements", "sum"),
            likes=("likes", "sum"),
            comments=("comments", "sum"),
            shares=("shares", "sum"),
            saves=("saves", "sum"),
            follows=("follows", "sum"),
        )
    )

    result["weighted_engagement_rate"] = (
        result["engagements"] / result["reach"].where(result["reach"] > 0)
    )

    return result.sort_values(
        ["weighted_engagement_rate", "records"],
        ascending=[False, False],
    ).reset_index(drop=True)
