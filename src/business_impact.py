"""Validate attributed business outcomes and summarize observed economics."""

import numpy as np
import pandas as pd


REQUIRED_ATTRIBUTION_COLUMNS = {
    "post_id",
    "post_date",
    "post_type",
    "campaign_type",
    "eligible_opportunities",
    "attributed_conversions",
    "attributed_net_revenue",
    "variable_cost",
    "paid_media_cost",
    "currency_code",
    "attribution_window_days",
    "attribution_method",
}
OPTIONAL_EXPERIMENT_COLUMNS = {"randomization_unit_id", "experiment_arm"}
NUMERIC_ATTRIBUTION_COLUMNS = [
    "eligible_opportunities",
    "attributed_conversions",
    "attributed_net_revenue",
    "variable_cost",
    "paid_media_cost",
    "attribution_window_days",
]
DIMENSIONS = {"post_type", "campaign_type"}


def _normalized_attribution_data(frame):
    work = frame.copy()
    for column in (
        "post_id",
        "post_type",
        "campaign_type",
        "currency_code",
        "attribution_method",
        *OPTIONAL_EXPERIMENT_COLUMNS,
    ):
        if column in work.columns:
            work[column] = work[column].astype("string").str.strip()
    if "post_date" in work:
        work["post_date"] = pd.to_datetime(work["post_date"], errors="coerce")
    for column in NUMERIC_ATTRIBUTION_COLUMNS:
        if column in work:
            work[column] = pd.to_numeric(work[column], errors="coerce")
    if "currency_code" in work:
        work["currency_code"] = work["currency_code"].str.upper()
    if "experiment_arm" in work:
        work["experiment_arm"] = work["experiment_arm"].str.lower()
    return work


def validate_attribution_data(frame):
    """Return a structured validation report without changing the input."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")

    missing_columns = sorted(REQUIRED_ATTRIBUTION_COLUMNS.difference(frame.columns))
    if missing_columns:
        return {
            "valid": False,
            "rows": int(len(frame)),
            "errors": [f"Missing required columns: {', '.join(missing_columns)}"],
            "warnings": [],
        }

    work = _normalized_attribution_data(frame)
    errors = []
    warnings = []
    if work.empty:
        errors.append("No outcome rows were supplied")

    for column in ("post_id", "post_type", "campaign_type", "currency_code", "attribution_method"):
        missing_count = int(work[column].isna().sum() + work[column].astype("string").str.strip().eq("").fillna(False).sum())
        if missing_count:
            errors.append(f"{column} is missing or blank in {missing_count} row(s)")

    if work["post_id"].duplicated(keep=False).any():
        errors.append("post_id must be unique: duplicate IDs were found")
    if work["post_date"].isna().any():
        errors.append(f"post_date is invalid or missing in {int(work['post_date'].isna().sum())} row(s)")

    for column in NUMERIC_ATTRIBUTION_COLUMNS:
        invalid = ~np.isfinite(work[column].to_numpy(dtype=float, na_value=np.nan))
        if invalid.any():
            errors.append(f"{column} is missing or non-numeric in {int(invalid.sum())} row(s)")
        elif work[column].lt(0).any():
            errors.append(f"{column} cannot contain negative values")

    for column in ("eligible_opportunities", "attributed_conversions", "attribution_window_days"):
        values = work[column].dropna()
        if len(values) and not np.allclose(values, np.round(values)):
            errors.append(f"{column} must contain whole-number counts or days")

    if not work["eligible_opportunities"].isna().any() and not work["attributed_conversions"].isna().any():
        if work["attributed_conversions"].gt(work["eligible_opportunities"]).any():
            errors.append("attributed_conversions cannot exceed eligible_opportunities")

    if not work["attribution_window_days"].isna().any():
        if not work["attribution_window_days"].gt(0).all():
            errors.append("attribution_window_days must be greater than zero")
        if work["attribution_window_days"].nunique(dropna=True) > 1:
            errors.append("Use one consistent attribution_window_days value per upload")

    currency_codes = work["currency_code"].dropna().unique()
    if any(len(str(code)) != 3 or not str(code).isalpha() for code in currency_codes):
        errors.append("currency_code must contain valid three-letter codes")
    if len(currency_codes) > 1:
        errors.append("Use one currency_code per upload; convert amounts before combining currencies")

    attribution_methods = work["attribution_method"].dropna().unique()
    if len(attribution_methods) > 1:
        errors.append("Use one attribution_method per upload so results are comparable")

    present_experiment_columns = OPTIONAL_EXPERIMENT_COLUMNS.intersection(work.columns)
    if present_experiment_columns and present_experiment_columns != OPTIONAL_EXPERIMENT_COLUMNS:
        errors.append("randomization_unit_id and experiment_arm must be supplied together")
    elif present_experiment_columns == OPTIONAL_EXPERIMENT_COLUMNS:
        for column in OPTIONAL_EXPERIMENT_COLUMNS:
            if work[column].isna().any() or work[column].astype("string").str.strip().eq("").any():
                errors.append(f"{column} cannot be blank when experiment fields are supplied")
        arms = set(work["experiment_arm"].dropna().unique())
        if arms != {"control", "treatment"}:
            errors.append("experiment_arm must contain both 'control' and 'treatment' arms")
        if work.groupby("randomization_unit_id", dropna=False)["experiment_arm"].nunique().gt(1).any():
            errors.append("Each randomization_unit_id must stay in one experiment_arm")

    return {
        "valid": not errors,
        "rows": int(len(work)),
        "errors": errors,
        "warnings": warnings,
        "currency_code": str(currency_codes[0]) if len(currency_codes) == 1 else None,
        "attribution_method": str(attribution_methods[0]) if len(attribution_methods) == 1 else None,
        "attribution_window_days": (
            float(work["attribution_window_days"].iloc[0])
            if len(work) and work["attribution_window_days"].notna().all()
            else None
        ),
        "experiment_fields_available": present_experiment_columns == OPTIONAL_EXPERIMENT_COLUMNS,
    }


def _require_valid_attribution_data(frame):
    validation = validate_attribution_data(frame)
    if not validation["valid"]:
        raise ValueError("Invalid attribution data: " + "; ".join(validation["errors"]))
    return _normalized_attribution_data(frame)


def aggregate_business_impact(frame, dimension):
    """Summarize observed, attributed economics by post or campaign type."""
    if dimension not in DIMENSIONS:
        raise ValueError(f"dimension must be one of {sorted(DIMENSIONS)}")
    work = _require_valid_attribution_data(frame)
    work["contribution_before_paid_media"] = (
        work["attributed_net_revenue"] - work["variable_cost"]
    )
    work["net_contribution"] = (
        work["contribution_before_paid_media"] - work["paid_media_cost"]
    )
    result = (
        work.groupby([dimension, "currency_code"], observed=True, dropna=False)
        .agg(
            records=("post_id", "size"),
            eligible_opportunities=("eligible_opportunities", "sum"),
            attributed_conversions=("attributed_conversions", "sum"),
            attributed_net_revenue=("attributed_net_revenue", "sum"),
            variable_cost=("variable_cost", "sum"),
            paid_media_cost=("paid_media_cost", "sum"),
            contribution_before_paid_media=("contribution_before_paid_media", "sum"),
            net_contribution=("net_contribution", "sum"),
        )
        .reset_index()
    )
    result["conversion_rate"] = result["attributed_conversions"] / result[
        "eligible_opportunities"
    ].where(result["eligible_opportunities"] > 0)
    result["customer_acquisition_cost"] = result["paid_media_cost"] / result[
        "attributed_conversions"
    ].where(result["attributed_conversions"] > 0)
    result["net_roas"] = result["attributed_net_revenue"] / result[
        "paid_media_cost"
    ].where(result["paid_media_cost"] > 0)
    result["roi"] = result["net_contribution"] / result["paid_media_cost"].where(
        result["paid_media_cost"] > 0
    )
    return result.sort_values("net_contribution", ascending=False, na_position="last").reset_index(drop=True)


def compare_randomized_arms(
    frame, *, bootstrap_reps=5000, random_state=42, confidence_level=0.95
):
    """Estimate treatment-minus-control outcomes by randomization unit.

    The interval is a cluster bootstrap that resamples assigned units within
    each arm. It estimates an intention-to-treat contrast only when the design
    and treatment assignment are in fact randomized; the input data alone
    cannot verify that design claim.
    """
    if not isinstance(bootstrap_reps, int) or bootstrap_reps < 100:
        raise ValueError("bootstrap_reps must be an integer of at least 100")
    if not np.isfinite(confidence_level) or not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be finite and between zero and one")
    work = _require_valid_attribution_data(frame)
    if not OPTIONAL_EXPERIMENT_COLUMNS.issubset(work.columns):
        raise ValueError("randomization_unit_id and experiment_arm are required for arm comparison")

    work["net_contribution"] = (
        work["attributed_net_revenue"] - work["variable_cost"] - work["paid_media_cost"]
    )
    units = (
        work.groupby(["randomization_unit_id", "experiment_arm"], observed=True)
        .agg(
            eligible_opportunities=("eligible_opportunities", "sum"),
            attributed_conversions=("attributed_conversions", "sum"),
            net_contribution=("net_contribution", "sum"),
        )
        .reset_index()
    )
    arms = {}
    for arm in ("control", "treatment"):
        arm_units = units.loc[units["experiment_arm"].eq(arm)]
        if len(arm_units) < 2:
            raise ValueError(f"At least two randomized units are required in the {arm} arm")
        if arm_units["eligible_opportunities"].le(0).any():
            raise ValueError(
                f"Every {arm} randomization unit needs a positive pre-treatment outcome denominator"
            )
        arms[arm] = arm_units

    def rate(data):
        denominator = data["eligible_opportunities"].sum()
        return data["attributed_conversions"].sum() / denominator if denominator > 0 else np.nan

    control_rate = rate(arms["control"])
    treatment_rate = rate(arms["treatment"])
    observed_rate_difference_pp = (treatment_rate - control_rate) * 100
    control_contribution = float(arms["control"]["net_contribution"].mean())
    treatment_contribution = float(arms["treatment"]["net_contribution"].mean())
    observed_contribution_difference = treatment_contribution - control_contribution

    rng = np.random.default_rng(random_state)
    bootstrap_rate_differences = np.empty(bootstrap_reps, dtype=float)
    bootstrap_contribution_differences = np.empty(bootstrap_reps, dtype=float)
    for index in range(bootstrap_reps):
        resampled = {}
        for arm in ("control", "treatment"):
            arm_units = arms[arm]
            positions = rng.integers(0, len(arm_units), size=len(arm_units))
            resampled[arm] = arm_units.iloc[positions]
        bootstrap_rate_differences[index] = (
            rate(resampled["treatment"]) - rate(resampled["control"])
        ) * 100
        bootstrap_contribution_differences[index] = (
            resampled["treatment"]["net_contribution"].mean()
            - resampled["control"]["net_contribution"].mean()
        )

    tail_probability = (1 - confidence_level) / 2
    return {
        "control_units": int(len(arms["control"])),
        "treatment_units": int(len(arms["treatment"])),
        "control_conversion_rate": float(control_rate),
        "treatment_conversion_rate": float(treatment_rate),
        "treatment_minus_control_conversion_rate_pp": float(observed_rate_difference_pp),
        "confidence_level": float(confidence_level),
        "conversion_rate_difference_ci_low_pp": float(
            np.quantile(bootstrap_rate_differences, tail_probability)
        ),
        "conversion_rate_difference_ci_high_pp": float(
            np.quantile(bootstrap_rate_differences, 1 - tail_probability)
        ),
        "control_net_contribution_per_unit": control_contribution,
        "treatment_net_contribution_per_unit": treatment_contribution,
        "net_contribution_difference_per_unit": float(observed_contribution_difference),
        "net_contribution_difference_ci_low": float(
            np.quantile(bootstrap_contribution_differences, tail_probability)
        ),
        "net_contribution_difference_ci_high": float(
            np.quantile(bootstrap_contribution_differences, 1 - tail_probability)
        ),
        "interpretation": (
            "Treatment-minus-control intention-to-treat estimate, conditional on verified random assignment, "
            "consistent attribution, and the randomization unit being independent. The file cannot verify these assumptions."
        ),
    }
