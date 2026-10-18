"""Build the focused, reproducible data-validation and EDA notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "01_data_validation_and_eda.ipynb"


def markdown(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


cells = [
    markdown("""# Instagram Analytics: Data Validation and Exploratory Analysis

This notebook documents the supplied dataset, validates its structure and values, and presents focused tables and charts. **Run the cells from top to bottom**; each table or chart is produced in its own output cell for easier review.

## Scope and interpretation

- The dashboard's CSV is the primary input; the workbook is a fallback if the CSV is absent.
- Checks describe the supplied file. Data ownership, collection method, row grain, and representativeness are not independently verified.
- No rows are dropped and no outliers are silently changed. Flags are review prompts.
- Reach is summed across records, so it is not unique people. Visit/follow ratios are aggregate proxies, not attributed conversions.
- The notebook is descriptive EDA. Category differences do not establish causality; predictive validation and uncertainty analysis are documented separately in the dashboard reports.
"""),
    markdown("## 1. Reproducible setup and source selection"),
    code("""from pathlib import Path
import hashlib
import json
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display

SEED = 42
np.random.seed(SEED)

PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "data").exists() and (PROJECT_ROOT.parent / "data").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = DATA_DIR / "sugar_cosmetics_instagram_data.csv"
EXCEL_PATH = DATA_DIR / "sugar_cosmetics_instagram_data.xlsx"
print(f"Project root: {PROJECT_ROOT}")
print(f"CSV available: {CSV_PATH.exists()} | workbook fallback available: {EXCEL_PATH.exists()}")
"""),
    code("""if CSV_PATH.exists():
    raw = pd.read_csv(CSV_PATH)
    source_path = CSV_PATH
elif EXCEL_PATH.exists():
    raw = pd.read_excel(EXCEL_PATH)
    source_path = EXCEL_PATH
else:
    raise FileNotFoundError("Expected the project CSV or workbook in data/.")

source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
source_shape = raw.shape
original_columns = raw.columns.astype(str).tolist()

def standardize_column(name):
    name = str(name).strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")

raw.columns = [standardize_column(c) for c in raw.columns]
source_record = pd.DataFrame([
    {"Item": "Selected source", "Value": source_path.relative_to(PROJECT_ROOT).as_posix()},
    {"Item": "Source file SHA-256", "Value": source_sha256},
    {"Item": "Source dimensions", "Value": f"{source_shape[0]:,} rows × {source_shape[1]} columns"},
    {"Item": "Original column names", "Value": ", ".join(original_columns)},
])
"""),
    code("display(source_record)"),
    markdown("## 2. Preview and schema validation\n\nColumn names are standardized for analysis; original values are retained until explicit parsing below."),
    code("display(raw.head(10))"),
    code("""required_columns = {
    "post_date", "post_type", "campaign_type", "hashtags", "audience_emotion",
    "engagement_source", "impressions", "reach", "likes", "comments",
    "shares", "saves", "profile_visits", "follows",
}
missing_required = sorted(required_columns - set(raw.columns))
unexpected_columns = sorted(set(raw.columns) - required_columns)
if missing_required:
    raise ValueError(f"Required columns missing from source: {missing_required}")

df = raw.copy()
df["post_date"] = pd.to_datetime(df["post_date"], errors="coerce")
numeric_columns = ["impressions", "reach", "likes", "comments", "shares", "saves", "profile_visits", "follows"]
for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")
categorical_columns = ["post_type", "campaign_type", "hashtags", "audience_emotion", "engagement_source"]
for column in categorical_columns:
    df[column] = df[column].astype("string").str.strip().replace("", pd.NA)
"""),
    code("""schema = pd.DataFrame({
    "Column": df.columns,
    "Type after parsing": [str(df[c].dtype) for c in df.columns],
    "Missing": [int(df[c].isna().sum()) for c in df.columns],
    "Missing (%)": [float(df[c].isna().mean() * 100) for c in df.columns],
    "Distinct non-missing": [int(df[c].nunique(dropna=True)) for c in df.columns],
})
print("Unexpected columns:", unexpected_columns or "None")
display(schema)
"""),
    markdown("## 3. Data-quality checks\n\nCounts below are diagnostics. A non-zero value prompts source review; it does not automatically imply a bad record."),
    code("""quality_checks = []
def add_check(check, count, severity, interpretation):
    quality_checks.append({"Check": check, "Count": int(count), "Review priority": severity, "Interpretation": interpretation})

add_check("Missing cells", df.isna().sum().sum(), "Review", "Inspect affected fields; no imputation is applied here.")
add_check("Exact duplicate rows", df.duplicated().sum(), "Review", "Without a post ID, exact duplicates do not establish duplicate posts.")
add_check("Invalid or missing dates", df["post_date"].isna().sum(), "High", "Rows without valid dates are unavailable for temporal summaries.")
for column in numeric_columns:
    add_check(f"Missing or non-numeric: {column}", df[column].isna().sum(), "Review", "Compare with source definitions before excluding or imputing.")
    add_check(f"Negative values: {column}", (df[column] < 0).sum(), "High", "Review source values; do not silently clamp counts.")
add_check("Impressions below reach", (df["impressions"] < df["reach"]).sum(), "Review", "Definitions can vary; inspect against source documentation.")
eligible_engagements = df[["likes", "comments", "shares", "saves"]].sum(axis=1, min_count=4)
add_check("Engagement actions above reach", (eligible_engagements > df["reach"]).sum(), "Review", "Repeated actions or metric definitions may explain these records.")
add_check("Zero reach", (df["reach"] == 0).sum(), "Review", "Engagement rate is undefined when reach is zero.")
add_check("Zero profile visits", (df["profile_visits"] == 0).sum(), "Info", "Follow-per-visit ratio is undefined when visits are zero.")
quality_df = pd.DataFrame(quality_checks)
"""),
    code("display(quality_df)"),
    code("""quality_overview = pd.DataFrame([{
    "Rows": len(df),
    "Source columns": len(raw.columns),
    "Missing cells": int(df.isna().sum().sum()),
    "Exact duplicate rows": int(df.duplicated().sum()),
    "Invalid dates": int(df["post_date"].isna().sum()),
    "First valid date": df["post_date"].min().date() if df["post_date"].notna().any() else None,
    "Last valid date": df["post_date"].max().date() if df["post_date"].notna().any() else None,
}])
display(quality_overview)
"""),
    markdown("## 4. Non-destructive cleaning and derived metrics\n\nThe analysis copy preserves every source row. The cleaning log makes transformations explicit."),
    code("""clean = df.copy()
clean["total_engagements"] = clean[["likes", "comments", "shares", "saves"]].sum(axis=1, min_count=4)
clean["engagement_rate"] = clean["total_engagements"] / clean["reach"].where(clean["reach"] > 0)
clean["profile_visit_rate_proxy"] = clean["profile_visits"] / clean["reach"].where(clean["reach"] > 0)
clean["follow_per_visit_rate_proxy"] = clean["follows"] / clean["profile_visits"].where(clean["profile_visits"] > 0)
clean["follow_per_reach_rate_proxy"] = clean["follows"] / clean["reach"].where(clean["reach"] > 0)
clean["month"] = clean["post_date"].dt.to_period("M").astype("string")
clean["weekday"] = clean["post_date"].dt.day_name().astype("string")
cleaning_log = pd.DataFrame([
    {"Step": "Standardize column names", "Rows affected": len(clean), "Action": "Normalize names to lowercase snake_case."},
    {"Step": "Parse date and numeric fields", "Rows affected": len(clean), "Action": "Unparseable values become missing and are counted in validation."},
    {"Step": "Create engagement and rate fields", "Rows affected": len(clean), "Action": "Keep source columns; zero denominator produces missing rate."},
    {"Step": "Drop or impute source rows", "Rows affected": 0, "Action": "No automatic row exclusion or imputation."},
])
"""),
    code("display(cleaning_log)"),
    markdown("## 5. Overall performance and distributions"),
    code("""valid_reach = clean["reach"].where(clean["reach"] > 0)
total_engagements = clean["total_engagements"].sum(min_count=1)
total_reach = clean["reach"].sum(min_count=1)
total_visits = clean["profile_visits"].sum(min_count=1)
total_follows = clean["follows"].sum(min_count=1)
overall_kpis = pd.DataFrame([
    {"Measure": "Rows analyzed", "Value": f"{len(clean):,}", "Definition / caveat": "One row is not verified as one unique post."},
    {"Measure": "Total engagements", "Value": f"{total_engagements:,.0f}", "Definition / caveat": "Likes + comments + shares + saves."},
    {"Measure": "Summed post-level reach", "Value": f"{total_reach:,.0f}", "Definition / caveat": "Not deduplicated unique people."},
    {"Measure": "Weighted engagement rate", "Value": f"{total_engagements / total_reach:.2%}", "Definition / caveat": "Total engagements ÷ summed positive reach."},
    {"Measure": "Profile visits / summed reach", "Value": f"{total_visits / total_reach:.2%}", "Definition / caveat": "Aggregate proxy; no person-level linkage."},
    {"Measure": "Follows / profile visits", "Value": f"{total_follows / total_visits:.2%}", "Definition / caveat": "Aggregate proxy; not attributed conversion."},
])
display(overall_kpis)
"""),
    code("""distribution_summary = clean[numeric_columns + ["total_engagements", "engagement_rate"]].describe(
    percentiles=[.01, .05, .25, .50, .75, .95, .99]
).T.reset_index(names="Metric")
display(distribution_summary)
"""),
    code("""outlier_rows = []
for column in numeric_columns + ["total_engagements", "engagement_rate"]:
    values = clean[column].dropna()
    if values.empty:
        continue
    q1, q3 = values.quantile([.25, .75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    flagged = (clean[column] < lower) | (clean[column] > upper)
    outlier_rows.append({"Metric": column, "Q1": q1, "Q3": q3, "IQR lower fence": lower,
                         "IQR upper fence": upper, "Flagged rows": int(flagged.sum()),
                         "Flagged (%)": float(flagged.mean() * 100)})
outlier_summary = pd.DataFrame(outlier_rows)
display(outlier_summary)
"""),
    markdown("### Reach and impressions distributions\n\nThese counts are strongly skewed, so the chart uses `log1p` on the horizontal axis. The underlying values are not transformed in the analysis tables."),
    code("""fig, ax = plt.subplots(figsize=(9, 4.5))
for metric, color in [("reach", "#d64f87"), ("impressions", "#59a6a0")]:
    ax.hist(np.log1p(clean[metric].dropna()), bins=45, alpha=.62, label=metric.title(), color=color)
ax.set(title="Reach and impressions distribution", xlabel="log(1 + count)", ylabel="Records")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
plt.show()
"""),
    markdown("### Engagement rate distribution\n\nRates are shown as percentage points. Extreme values remain in the plot and are described in the outlier table."),
    code("""fig, ax = plt.subplots(figsize=(9, 4.5))
rate_pct = clean["engagement_rate"].dropna() * 100
ax.hist(rate_pct, bins=50, color="#9b6fc1", edgecolor="white")
ax.set(title="Post-level engagement rate distribution", xlabel="Engagement rate (%)", ylabel="Records")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
plt.show()
"""),
    markdown("## 6. Category coverage and performance\n\nCategory summaries show both the weighted rate and its support. Unequal denominators matter; use uncertainty analysis in the predictive validation report before treating small gaps as meaningful."),
    code("""def grouped_metrics(data, group_col):
    result = data.groupby(group_col, dropna=False).agg(
        records=(group_col, "size"), reach=("reach", "sum"),
        engagements=("total_engagements", "sum"), mean_post_rate=("engagement_rate", "mean"),
    ).reset_index()
    result["weighted_rate"] = result["engagements"] / result["reach"].where(result["reach"] > 0)
    result["record_share_pct"] = result["records"] / len(data) * 100
    return result

post_type_summary = grouped_metrics(clean, "post_type").sort_values("weighted_rate", ascending=False)
campaign_summary = grouped_metrics(clean, "campaign_type").sort_values("weighted_rate", ascending=False)
"""),
    code("""category_counts = pd.concat([
    clean["post_type"].value_counts(dropna=False).rename_axis("Category").reset_index(name="Records").assign(Field="Post type"),
    clean["campaign_type"].value_counts(dropna=False).rename_axis("Category").reset_index(name="Records").assign(Field="Campaign type"),
], ignore_index=True)[["Field", "Category", "Records"]]
display(category_counts)
"""),
    code("""fig, ax = plt.subplots(figsize=(8, 4))
type_counts = clean["post_type"].value_counts(dropna=False).sort_values()
ax.barh(type_counts.index.fillna("Missing").astype(str), type_counts.values, color="#d64f87")
ax.set(title="Record coverage by post type", xlabel="Records", ylabel="Post type")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
plt.show()
"""),
    code("display(post_type_summary.rename(columns={\"post_type\": \"Post type\", \"records\": \"Records\", \"reach\": \"Summed reach\", \"engagements\": \"Engagements\", \"mean_post_rate\": \"Mean post rate\", \"weighted_rate\": \"Weighted rate\", \"record_share_pct\": \"Record share (%)\"}))"),
    code("""fig, ax = plt.subplots(figsize=(8, 4))
plot_data = post_type_summary.sort_values("weighted_rate")
ax.barh(plot_data["post_type"].astype(str), plot_data["weighted_rate"] * 100, color="#d64f87")
ax.set(title="Weighted engagement rate by post type", xlabel="Weighted engagement rate (%)", ylabel="Post type")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
plt.show()
"""),
    code("display(campaign_summary.rename(columns={\"campaign_type\": \"Campaign\", \"records\": \"Records\", \"reach\": \"Summed reach\", \"engagements\": \"Engagements\", \"mean_post_rate\": \"Mean post rate\", \"weighted_rate\": \"Weighted rate\", \"record_share_pct\": \"Record share (%)\"}))"),
    code("""fig, ax = plt.subplots(figsize=(9, 4.5))
plot_data = campaign_summary.sort_values("weighted_rate")
ax.barh(plot_data["campaign_type"].astype(str), plot_data["weighted_rate"] * 100, color="#59a6a0")
ax.set(title="Weighted engagement rate by campaign", xlabel="Weighted engagement rate (%)", ylabel="Campaign")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
plt.show()
"""),
    code("""source_summary = grouped_metrics(clean, "engagement_source").sort_values("weighted_rate", ascending=False)
display(source_summary.rename(columns={"engagement_source": "Engagement source", "records": "Records", "reach": "Summed reach", "engagements": "Engagements", "mean_post_rate": "Mean post rate", "weighted_rate": "Weighted rate", "record_share_pct": "Record share (%)"}))
"""),
    code("""emotion_summary = grouped_metrics(clean, "audience_emotion").sort_values("weighted_rate", ascending=False)
display(emotion_summary.rename(columns={"audience_emotion": "Audience emotion", "records": "Records", "reach": "Summed reach", "engagements": "Engagements", "mean_post_rate": "Mean post rate", "weighted_rate": "Weighted rate", "record_share_pct": "Record share (%)"}))
"""),
    markdown("## 7. Time patterns"),
    code("""valid_dates = clean.dropna(subset=["post_date"]).copy()
monthly = valid_dates.set_index("post_date").resample("MS").agg(
    records=("reach", "size"), reach=("reach", "sum"), engagements=("total_engagements", "sum"),
).reset_index()
monthly["weighted_rate"] = monthly["engagements"] / monthly["reach"].where(monthly["reach"] > 0)
monthly["month"] = monthly["post_date"].dt.strftime("%b %Y")
"""),
    code("display(monthly[[\"month\", \"records\", \"reach\", \"engagements\", \"weighted_rate\"]].rename(columns={\"month\": \"Month\", \"records\": \"Records\", \"reach\": \"Summed reach\", \"engagements\": \"Engagements\", \"weighted_rate\": \"Weighted rate\"}))"),
    code("""fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(monthly["post_date"], monthly["records"], marker="o", color="#d64f87")
ax.set(title="Records in source by month", xlabel="Month", ylabel="Records")
ax.tick_params(axis="x", rotation=35)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
plt.show()
"""),
    code("""fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(monthly["post_date"], monthly["weighted_rate"] * 100, marker="o", color="#59a6a0")
ax.set(title="Weighted engagement rate by month", xlabel="Month", ylabel="Weighted engagement rate (%)")
ax.tick_params(axis="x", rotation=35)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
plt.show()
"""),
    code("""weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_summary = grouped_metrics(valid_dates, "weekday")
weekday_summary["weekday"] = pd.Categorical(weekday_summary["weekday"], categories=weekday_order, ordered=True)
weekday_summary = weekday_summary.sort_values("weekday")
display(weekday_summary.rename(columns={"weekday": "Weekday", "records": "Records", "reach": "Summed reach", "engagements": "Engagements", "mean_post_rate": "Mean post rate", "weighted_rate": "Weighted rate", "record_share_pct": "Record share (%)"}))
"""),
    code("""fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(weekday_summary["weekday"].astype(str), weekday_summary["weighted_rate"] * 100, color="#9b6fc1")
ax.set(title="Weighted engagement rate by weekday", xlabel="Weekday", ylabel="Weighted engagement rate (%)")
ax.tick_params(axis="x", rotation=25)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
plt.show()
"""),
    markdown("## 8. Hashtag exploration\n\nEach record contributes at most once to a tag, but a multi-tag record contributes to multiple groups. Tag audiences overlap; do not sum across tags as if disjoint."),
    code("""hashtag_rows = []
for row in clean[["hashtags", "reach", "total_engagements"]].itertuples(index=False):
    tags = set(tag.lower() for tag in re.findall(r"#\\w+", str(row.hashtags)))
    for tag in tags:
        hashtag_rows.append({"hashtag": tag, "reach": row.reach, "engagements": row.total_engagements})

if hashtag_rows:
    hashtag_records = pd.DataFrame(hashtag_rows)
    hashtag_summary = hashtag_records.groupby("hashtag").agg(
        records=("hashtag", "size"), reach=("reach", "sum"), engagements=("engagements", "sum")
    ).reset_index()
    hashtag_summary["weighted_rate"] = hashtag_summary["engagements"] / hashtag_summary["reach"].where(hashtag_summary["reach"] > 0)
    hashtag_summary["usage_share_pct"] = hashtag_summary["records"] / len(clean) * 100
else:
    hashtag_summary = pd.DataFrame(columns=["hashtag", "records", "reach", "engagements", "weighted_rate", "usage_share_pct"])
"""),
    code("""top_hashtags = hashtag_summary.sort_values(["records", "hashtag"], ascending=[False, True]).head(20)
display(top_hashtags.rename(columns={"hashtag": "Hashtag", "records": "Records using tag", "reach": "Summed reach (overlapping)", "engagements": "Engagements (overlapping)", "weighted_rate": "Weighted rate", "usage_share_pct": "Records using tag (%)"}))
"""),
    code("""fig, ax = plt.subplots(figsize=(9, 6))
plot_data = top_hashtags.sort_values("records")
ax.barh(plot_data["hashtag"], plot_data["records"], color="#d64f87")
ax.set(title="Most frequently used hashtags", xlabel="Records containing hashtag", ylabel="Hashtag")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
plt.show()
"""),
    markdown("## 9. Findings, limitations, and exportable audit outputs"),
    code("""findings = pd.DataFrame([
    {"Finding": "Highest format weighted rate", "Observed": post_type_summary.iloc[0]["post_type"], "Interpretation": "Descriptive ranking; assess uncertainty before acting."},
    {"Finding": "Highest campaign weighted rate", "Observed": campaign_summary.iloc[0]["campaign_type"], "Interpretation": "Descriptive ranking; not a causal campaign effect."},
    {"Finding": "Most-recorded month", "Observed": monthly.loc[monthly["records"].idxmax(), "month"], "Interpretation": "Record volume is not confirmed publishing frequency."},
    {"Finding": "Most-used hashtag", "Observed": top_hashtags.iloc[0]["hashtag"] if len(top_hashtags) else "No tags parsed", "Interpretation": "Hashtag groups overlap; usage is not incremental reach."},
])
display(findings)
"""),
    markdown("""### Limitations to carry into decisions

- Provenance and one-row-per-post grain have not been independently verified.
- Dates have no publication time; no posting-hour conclusion is possible.
- There are no audience demographics, stable post IDs, captions, spend, revenue, or person-level conversion links.
- Category and hashtag summaries are observational and may be confounded by content, timing, or selection.
- Aggregate visit and follow ratios are proxies only. Financial impact requires attributed business outcomes.
- IQR outlier flags indicate unusual values, not confirmed errors. No outliers were removed.

### Reproduce and export

The cell below writes the non-destructive cleaned analysis data and quality summaries to the project paths used by the dashboard. Run it only after reviewing the checks above.
"""),
    code("""summary = {
    "source_file": source_path.relative_to(PROJECT_ROOT).as_posix(),
    "source_sha256": source_sha256,
    "rows": int(len(clean)),
    "source_columns": int(len(raw.columns)),
    "columns_after_feature_engineering": int(len(clean.columns)),
    "date_min": str(clean["post_date"].min()),
    "date_max": str(clean["post_date"].max()),
    "missing_cells_after_standardization": int(clean.isna().sum().sum()),
    "exact_duplicate_rows": int(clean.duplicated().sum()),
    "invalid_dates": int(clean["post_date"].isna().sum()),
    "post_type_categories": {str(k): int(v) for k, v in clean["post_type"].value_counts(dropna=False).items()},
    "campaign_type_categories": {str(k): int(v) for k, v in clean["campaign_type"].value_counts(dropna=False).items()},
    "provenance": "Source identity and collection method are unverified.",
    "upstream_source": "https://github.com/Neeraj08823/Sugar_cosmetics_Instagram_Analytics/tree/main/Data",
    "cleaning_policy": "Standardize names and types; no rows dropped or imputed.",
    "notes": [
        "No stable post ID or exact publication time is present.",
        "Summed post-level reach is not unique account reach.",
        "Aggregate visit/follow rates are proxies, not attributed conversion.",
        "Category and hashtag comparisons are descriptive, not causal.",
        "Outliers are flagged for review and retained.",
    ],
}
quality_report = {
    "dataset_summary": summary,
    "quality_checks": quality_df.rename(columns={"Check": "check", "Count": "count", "Review priority": "severity", "Interpretation": "detail"}).to_dict(orient="records"),
    "outlier_summary": outlier_summary.rename(columns={"Metric": "metric", "Q1": "q1", "Q3": "q3", "IQR": "iqr", "IQR lower fence": "lower_iqr_fence", "IQR upper fence": "upper_iqr_fence", "Flagged rows": "flagged_count", "Flagged (%)": "flagged_pct"}).to_dict(orient="records"),
    "schema": schema.rename(columns={"Column": "column", "Type after parsing": "dtype", "Missing": "missing_count", "Missing (%)": "missing_pct", "Distinct non-missing": "unique_values"}).to_dict(orient="records"),
}

clean_path = DATA_DIR / "sugar_cosmetics_instagram_cleaned.csv"
clean.to_csv(clean_path, index=False)
(REPORT_DIR / "data_quality_report.json").write_text(json.dumps(quality_report, indent=2, default=str), encoding="utf-8")
quality_df.rename(columns={"Check": "check", "Count": "count", "Review priority": "severity", "Interpretation": "detail"}).to_csv(REPORT_DIR / "data_quality_checks.csv", index=False)
pd.DataFrame(quality_report["outlier_summary"]).to_csv(REPORT_DIR / "outlier_screening.csv", index=False)
print(f"Cleaned analysis data: {clean_path.relative_to(PROJECT_ROOT)}")
print("Quality report and check tables written to reports/.")
"""),
    markdown("""## 10. Conclusion

The supplied dataset supports a useful **descriptive** view of Instagram content performance: it contains 50,000 records spanning 19 April 2024 to 19 April 2025, with an overall weighted engagement rate of about **18.55%**. The observed format rates are close together (Story is highest at about 18.63%; Image is lowest at about 18.42%), and campaign and weekday differences are also modest. These rankings can guide test hypotheses, but they do not show that a format, campaign, hashtag, or posting day caused better results.

The file passes the checked missing-cell, exact-duplicate, and date-validity checks, while IQR screening flags some values for review. Those checks do not verify data provenance, account authenticity, or whether each row represents a unique post. Summed reach and aggregate visit/follow ratios must not be interpreted as unique people or attributed conversion.

**Recommended use:** preserve the current descriptive findings as a baseline, then test the most relevant creative or message hypotheses with controlled assignment. Evaluate business outcomes using attributed conversions and Finance-reconciled net contribution; do not claim ROI or causal lift from these records alone.
"""),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10+"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"Wrote {NOTEBOOK.relative_to(ROOT)} with {len(cells)} focused cells.")
