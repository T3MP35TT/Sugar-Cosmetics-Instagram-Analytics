"""Date-block uncertainty intervals for descriptive category rate contrasts."""

import numpy as np
import pandas as pd


def category_rate_contrasts(
    df,
    dimension,
    *,
    bootstrap_reps=2000,
    block_days=7,
    confidence_level=0.95,
    random_state=42,
):
    """Compare each category's weighted rate with all other categories.

    Percentile intervals use paired circular moving calendar-date blocks. A shared
    max-deviation critical value makes intervals simultaneous across all
    category-versus-rest contrasts for the requested dimension. The result is
    descriptive and conditional on dates being appropriate resampling blocks;
    it does not correct confounding or establish causality.
    """
    required = {dimension, "post_date", "reach", "total_engagements"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Required columns missing: {missing}")
    if not isinstance(bootstrap_reps, int) or bootstrap_reps < 100:
        raise ValueError("bootstrap_reps must be an integer of at least 100")
    if not isinstance(block_days, int) or block_days < 1:
        raise ValueError("block_days must be a positive integer")
    if not 0.8 <= confidence_level < 1:
        raise ValueError("confidence_level must be between 0.8 and 1")

    work = df[[dimension, "post_date", "reach", "total_engagements"]].copy()
    work["post_date"] = pd.to_datetime(work["post_date"], errors="coerce").dt.normalize()
    work["reach"] = pd.to_numeric(work["reach"], errors="coerce")
    work["total_engagements"] = pd.to_numeric(work["total_engagements"], errors="coerce")
    work = work.loc[
        work[dimension].notna()
        & work["post_date"].notna()
        & work["reach"].gt(0)
        & work["total_engagements"].notna()
    ].copy()

    columns = [
        dimension,
        "records",
        "reach",
        "engagements",
        "weighted_rate",
        "other_records",
        "other_weighted_rate",
        "difference_pp",
        "simultaneous_ci_low_pp",
        "simultaneous_ci_high_pp",
        "engagement_gap_equivalent",
        "engagement_gap_equivalent_ci_low",
        "engagement_gap_equivalent_ci_high",
        "confidence_level",
    ]
    if work.empty:
        return pd.DataFrame(columns=columns)

    dates = pd.date_range(work["post_date"].min(), work["post_date"].max(), freq="D")
    categories = sorted(work[dimension].unique(), key=lambda value: str(value))
    date_totals = work.groupby("post_date", sort=True)[["reach", "total_engagements"]].sum()
    date_totals = date_totals.reindex(dates, fill_value=0)
    rng = np.random.default_rng(random_state)
    block_days = min(block_days, len(dates))
    blocks_per_sample = int(np.ceil(len(dates) / block_days))
    starts = rng.integers(0, len(dates), size=(bootstrap_reps, blocks_per_sample))
    offsets = np.arange(block_days)
    sampled_dates = ((starts[:, :, None] + offsets) % len(dates)).reshape(
        bootstrap_reps, -1
    )[:, : len(dates)]

    rows = []
    bootstrap_differences = []
    for category in categories:
        category_work = work.loc[work[dimension].eq(category)]
        category_daily = category_work.groupby("post_date", sort=True)[
            ["reach", "total_engagements"]
        ].sum().reindex(dates, fill_value=0)
        other_daily = date_totals - category_daily

        reach = float(category_daily["reach"].sum())
        engagements = float(category_daily["total_engagements"].sum())
        other_reach = float(other_daily["reach"].sum())
        other_engagements = float(other_daily["total_engagements"].sum())
        rate = engagements / reach if reach > 0 else np.nan
        other_rate = other_engagements / other_reach if other_reach > 0 else np.nan
        difference = (rate - other_rate) * 100 if np.isfinite(rate) and np.isfinite(other_rate) else np.nan

        if np.isfinite(difference):
            sampled_reach = sampled_dates @ category_daily["reach"].to_numpy(dtype=float)
            sampled_engagements = sampled_dates @ category_daily["total_engagements"].to_numpy(dtype=float)
            sampled_other_reach = sampled_dates @ other_daily["reach"].to_numpy(dtype=float)
            sampled_other_engagements = sampled_dates @ other_daily["total_engagements"].to_numpy(dtype=float)
            sampled_rate = np.divide(
                sampled_engagements,
                sampled_reach,
                out=np.full(bootstrap_reps, np.nan),
                where=sampled_reach > 0,
            )
            sampled_other_rate = np.divide(
                sampled_other_engagements,
                sampled_other_reach,
                out=np.full(bootstrap_reps, np.nan),
                where=sampled_other_reach > 0,
            )
            differences = (sampled_rate - sampled_other_rate) * 100
            bootstrap_differences.append((len(rows), difference, differences))
        else:
            bootstrap_differences.append((len(rows), difference, np.array([])))

        rows.append(
            {
                dimension: category,
                "records": int(len(category_work)),
                "reach": reach,
                "engagements": engagements,
                "weighted_rate": rate,
                "other_records": int(len(work) - len(category_work)),
                "other_weighted_rate": other_rate,
                "difference_pp": difference,
                "confidence_level": confidence_level,
            }
        )

    usable = [
        item
        for item in bootstrap_differences
        if item[2].size and np.isfinite(item[2]).mean() >= confidence_level
    ]
    usable_positions = {item[0] for item in usable}
    if usable:
        deviations = np.column_stack([item[2] - item[1] for item in usable])
        has_valid_contrast = np.isfinite(deviations).any(axis=1)
        max_deviations = np.max(
            np.where(np.isfinite(deviations), np.abs(deviations), -np.inf), axis=1
        )[has_valid_contrast]
        critical_value = float(
            np.quantile(max_deviations, confidence_level)
        )
    else:
        critical_value = np.nan

    for position, row in enumerate(rows):
        if (
            position in usable_positions
            and np.isfinite(row["difference_pp"])
            and np.isfinite(critical_value)
        ):
            row["simultaneous_ci_low_pp"] = row["difference_pp"] - critical_value
            row["simultaneous_ci_high_pp"] = row["difference_pp"] + critical_value
        else:
            row["simultaneous_ci_low_pp"] = np.nan
            row["simultaneous_ci_high_pp"] = np.nan
        row["engagement_gap_equivalent"] = (
            row["difference_pp"] / 100 * row["reach"]
            if np.isfinite(row["difference_pp"])
            else np.nan
        )
        row["engagement_gap_equivalent_ci_low"] = (
            row["simultaneous_ci_low_pp"] / 100 * row["reach"]
            if np.isfinite(row["simultaneous_ci_low_pp"])
            else np.nan
        )
        row["engagement_gap_equivalent_ci_high"] = (
            row["simultaneous_ci_high_pp"] / 100 * row["reach"]
            if np.isfinite(row["simultaneous_ci_high_pp"])
            else np.nan
        )

    result = pd.DataFrame(rows, columns=columns)
    return result.sort_values("difference_pp", ascending=False, na_position="last").reset_index(drop=True)
