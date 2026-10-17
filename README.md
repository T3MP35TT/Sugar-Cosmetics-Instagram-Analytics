# Sugar Cosmetics Instagram Performance Analytics

A Streamlit dashboard and data audit for exploring content records, engagement, campaigns, hashtags, posting patterns, and conversion proxies.

## Decision status

This repository supports **descriptive analysis of the supplied file**. It does not establish that the 50,000 rows are official Sugar Cosmetics account records, that one row equals one post, or that the sample represents real posting activity. The workbook has 14 fields and no source documentation, stable post ID, caption, publication time, follower count, demographic attributes, spend, or sales attribution. Confirm provenance and row grain with the data owner before using findings as brand performance claims.

Summed reach is repeated post-level reach, not unique account reach. Group differences are descriptive associations and do not establish causality. Category counts are unusually balanced: post types occupy 24.8–25.2% of rows and campaign types 19.8–20.4%. This may indicate sampling or generated data; a balanced file is not proof of a representative sample.

## Run the dashboard

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If activation is blocked, call the environment directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Reproduce the data audit

Open `notebooks/01_data_validation_and_eda.ipynb` from the project root and run every cell in order. It prefers the Excel workbook and falls back to the project CSV. It standardizes column names and types, checks data quality, explores distributions and outliers, calculates documented metrics, and writes:

- `data/sugar_cosmetics_instagram_cleaned.csv`
- `reports/data_quality_report.json`
- `reports/data_quality_checks.csv`
- `reports/outlier_screening.csv`

The cleaning policy is non-destructive: rows are not automatically dropped, and IQR outliers are flagged for review rather than removed. The report describes the input and checks; it is not a certification of source authenticity or metric correctness.

Fingerprint the exact source and execution environment with:

```powershell
python src/reproducibility_manifest.py
```

This writes `reports/reproducibility_manifest.json`. The default input is the workbook, with CSV fallback. To fingerprint another input, pass `--source path\to\file`. The manifest records SHA-256 hashes, runtime versions, source-file consistency, record density, category balance, and a Git revision when available. The current CSV and workbook match across all 50,000 rows and 14 fields after normalizing dates and headers. The 50,000 records span 366 calendar days (136.612 records per day); because the row grain is undocumented, this is not a post-frequency estimate. A hash proves file identity only; it cannot prove who supplied the data or whether its contents are true.

## Dashboard pages

- Executive Overview: selected-scope KPIs, trends, and category summaries
- Content Performance: format and campaign comparisons
- Hashtag Intelligence: tag-level summaries; records with multiple tags contribute to multiple groups
- Audience & Conversion Funnel: reach, engagement, profile-visit, and follow proxies
- Posting Strategy: monthly volume and weekday summaries
- Deep Dive & Data Quality: filtered record inspection, export, validation, and outlier review
- Strategic Recommendations: experiment design guidance and next-data recommendations

## Metric definitions

- **Total engagements:** likes + comments + shares + saves.
- **Post engagement rate:** total engagements divided by reach when reach is positive.
- **Weighted engagement rate:** total eligible engagements divided by total eligible reach in the group.
- **Profile-visit rate proxy:** profile visits divided by reach.
- **Follow-per-visit proxy:** follows divided by profile visits when visits are positive.
- **Record volume:** number of rows. Call it post volume only after confirming each row represents one post.

Zero denominators produce missing rates. Aggregate ratios do not link individual visits to follows or prove attribution.

## Code, environment, and sanity checks

Core calculations are in `src/analytics.py`; Streamlit page setup and shared data loading are in `utils/common.py`. `requirements.txt` gives supported dependency ranges. `requirements-lock.txt` captures the installed Windows/Python 3.14.7 environment; refresh it deliberately when dependencies change.

To recreate the captured environment, use Python 3.14.7 and install the lock file:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
```

Run the existing calculation checks with:

```powershell
pytest -q
```

The tests cover core feature calculations, missing values, zero denominators, and summaries. A local Git history is not available in this workspace, so commit provenance cannot be assessed here.

The latest implementation check is recorded in `reports/implementation_review.md`.

## Limitations and approval gates

Before operational or external use:

1. Obtain source owner, extraction date, account identifier, collection method, metric definitions, and permission to use the data.
2. Confirm the row grain and obtain a stable post ID; reconcile a documented sample of source rows and computed metrics.
3. Explain the category balance and sampling method. Assess representativeness before generalizing.
4. Review all non-zero validation and outlier flags against source definitions; do not remove records without a recorded rule.
5. Add paid/organic exposure and attributable conversion, spend, and sales data before estimating ROI.
6. For a causal content recommendation, run a pre-registered randomized experiment with a primary outcome, comparable exposure windows, guardrails, and an agreed stopping rule.

Demographic fairness analysis, time-of-day recommendations, and revenue impact cannot be evaluated from the current fields. Predictive-model criteria such as train/test splitting, tuning, and retraining are not applicable until a predictive model is proposed.
