<div align="center">
  <img src="images/sugar_logo.png" alt="SUGAR Cosmetics" width="190" />
  <h1>Sugar Cosmetics Instagram Analytics</h1>
  <p><strong>From social-content observations to measurable marketing experiments</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Streamlit-Interactive%20Analytics-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit" />
    <img src="https://img.shields.io/badge/Pandas-Data%20Preparation-150458?logo=pandas&logoColor=white" alt="Pandas" />
    <img src="https://img.shields.io/badge/Plotly-Visualization-3F4F75?logo=plotly&logoColor=white" alt="Plotly" />
    <img src="https://img.shields.io/badge/scikit--learn-Model%20Evaluation-F7931E?logo=scikitlearn&logoColor=white" alt="scikit-learn" />
    <img src="https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white" alt="pytest" />
  </p>
</div>

---

> **Data-scope and attribution notice**  
> This project analyzes a supplied 50,000-record Instagram analytics dataset associated with a public Sugar Cosmetics analytics repository. The available materials do **not** verify that the records came from Sugar Cosmetics' official Instagram account, that they represent its actual posting history, or that the sample is representative. Findings in this repository are therefore described as results for the **supplied dataset**, not verified Sugar Cosmetics business performance. No causal or financial impact is claimed.

## Contents

- [Executive overview](#executive-overview)
- [Business context and analytical questions](#business-context-and-analytical-questions)
- [Dataset and provenance](#dataset-and-provenance)
- [Executive performance snapshot](#executive-performance-snapshot)
- [Key analytical findings](#key-analytical-findings)
- [Application and dashboard](#application-and-dashboard)
- [Analytical methodology](#analytical-methodology)
- [Predictive model evaluation](#predictive-model-evaluation)
- [Experiment and business-impact framework](#experiment-and-business-impact-framework)
- [Data quality, reproducibility and governance](#data-quality-reproducibility-and-governance)
- [Technology stack and architecture](#technology-stack-and-architecture)
- [Repository structure](#repository-structure)
- [Getting started](#getting-started)
- [Reproducing the analysis](#reproducing-the-analysis)
- [Testing and continuous integration](#testing-and-continuous-integration)
- [Known limitations and evidence gaps](#known-limitations-and-evidence-gaps)
- [Recommended next steps](#recommended-next-steps)
- [Documentation and deliverables](#documentation-and-deliverables)
- [Data attribution and licensing](#data-attribution-and-licensing)

## Executive overview

**Sugar Cosmetics Instagram Analytics** is an end-to-end analytics case study designed to demonstrate how a social-content dataset can be transformed into an auditable analytical workflow and a practical marketing decision-support application.

The project combines data validation, exploratory analysis, engagement measurement, category-level uncertainty estimation, temporal model evaluation, experiment design, business-impact data validation, and an interactive Streamlit application. It is built to separate what the supplied data shows from what a marketing or finance team would still need to measure before making an investment decision.

The work is organized around four connected questions:

1. **What is recorded?** — How are reach, impressions, interactions, content formats, campaign labels, hashtags and audience-action fields distributed in the supplied records?
2. **Where are the observed differences?** — Do engagement rates differ across content formats or campaign categories, and how uncertain are those comparisons?
3. **Can the available pre-publication fields forecast engagement?** — Does a more complex model improve on a simple baseline when evaluated on later dates?
4. **What evidence would support a business decision?** — How should Marketing and Finance design controlled tests and capture attributed conversion, revenue, cost and contribution data?

The project intentionally does not turn engagement into sales or ROI without attribution evidence. It provides the measurement contract and workflow needed to calculate those outcomes when a validated business export becomes available.

## Business context and analytical questions

Social engagement is an intermediate signal. For a consumer brand, content decisions ultimately need to be evaluated against qualified audience actions, attributable conversions, contribution and cost—not likes or reach alone.

This analysis explores the available social-content measures while identifying the evidence required to connect them to commercial outcomes.

| Business area | Analytical question | Decision-support output |
|---|---|---|
| Content strategy | How do recorded engagement levels vary by content format? | Weighted engagement comparisons and uncertainty intervals |
| Campaign strategy | Are campaign labels associated with different engagement rates? | Campaign-level comparisons against all other campaign records |
| Discovery | How are hashtags used, and what engagement patterns are associated with them? | Hashtag normalization, coverage and performance views |
| Audience actions | How do reach, profile visits and follows relate in the supplied records? | Funnel-style descriptive ratios, explicitly labelled as proxies |
| Publishing operations | How are records distributed across dates and weekdays? | Calendar and cadence views; not verified publication frequency |
| Measurement strategy | What would be required to establish commercial impact? | Attribution data contract, experiment design and Finance measures |
| Forecasting | Do pre-publication metadata features add future predictive value? | Chronological holdout evaluation against a median baseline |

## Dataset and provenance

### Dataset profile

| Attribute | Description |
|---|---|
| Dataset records | 50,000 |
| Fields | 14 |
| Date coverage | 19 April 2024 – 19 April 2025 |
| Calendar span | 366 days |
| Main formats | Image, Reel, Story, Video |
| Campaign labels | Giveaway, Festive Offer, Influencer Collab, Product Launch, Tutorial |
| Primary input | `data/sugar_cosmetics_instagram_data.csv` |
| Workbook source | `data/sugar_cosmetics_instagram_data.xlsx` |
| Cleaned derivative | `data/sugar_cosmetics_instagram_cleaned.csv` |

The available fields are `post_date`, `post_type`, `campaign_type`, `hashtags`, `audience_emotion`, `engagement_source`, `impressions`, `reach`, `likes`, `comments`, `shares`, `saves`, `profile_visits`, and `follows`.

### Source assessment

The local workbook has the same filename as a workbook in the public [`Neeraj08823/Sugar_cosmetics_Instagram_Analytics` project](https://github.com/Neeraj08823/Sugar_cosmetics_Instagram_Analytics/tree/main/Data). The local files contain 50,000 rows over the same date span, and their calculated aggregates align with rounded figures in that upstream project's README. This supports likely source attribution, but the remote workbook bytes were not independently fetched and hash-compared.

The source account identity, collection method, capture permissions, row grain, and sampling procedure remain unverified. There is no stable post identifier or exact publication timestamp. The near-even counts across content and campaign categories are treated as a sampling diagnostic, not evidence of representativeness. See [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) for the full assessment.

### Important interpretation rules

- **Record count is not confirmed post count.** The row grain is undocumented and there is no stable `post_id`.
- **Summed reach is cumulative post-level reach.** It is not unique account reach or deduplicated audience size.
- **Profile visits and follows are recorded audience-action fields.** Their ratios are proxies, not attributable conversion rates.
- **Hashtag groups can overlap.** A record containing multiple hashtags may contribute to more than one hashtag group; hashtag totals should not be summed as if categories were mutually exclusive.
- **A ratio with a zero denominator is missing**, not zero.
- **Descriptive association is not causation.** Category differences cannot establish that a content choice caused an outcome.

## Executive performance snapshot

The following are calculations from the supplied 50,000-record CSV. They are not independently verified brand KPIs.

| Measure | Dataset result | Interpretation |
|---|---:|---|
| Summed reach | 987,423,288 | Sum of record-level reach; not unique people/accounts |
| Impressions | 1,276,045,750 | Sum of supplied record-level impressions |
| Total engagements | 183,164,417 | Likes + comments + shares + saves |
| Weighted engagement rate | **18.55%** | Total eligible engagements ÷ total eligible reach |
| Profile visits | 29,634,798 | Sum of recorded profile visits |
| Follows | 8,866,710 | Sum of recorded follows |
| Profile-visit rate proxy | 3.00% | Profile visits ÷ summed reach |
| Follow-per-visit proxy | 29.92% | Follows ÷ profile visits |

### Engagement mix

Total engagements are defined as likes, comments, shares and saves. The weighted engagement rate is calculated as the sum of eligible engagements divided by the sum of eligible reach. It is not the simple average of record-level engagement rates.

## Key analytical findings

### 1. Content-format comparison

The full-file descriptive analysis compares each format's weighted engagement rate with the weighted rate for all other formats. Simultaneous 95% moving date-block bootstrap intervals use seven-day blocks, with three- and fourteen-day sensitivity checks.

| Format | Weighted engagement rate | Difference vs. all other formats | 7-day simultaneous 95% interval |
|---|---:|---:|---:|
| Story | 18.63% | +0.101 percentage points | -0.032 to +0.234 pp |
| Reel | 18.60% | +0.062 percentage points | -0.070 to +0.195 pp |
| Video | 18.56% | +0.015 percentage points | -0.118 to +0.148 pp |
| Image | 18.42% | -0.179 percentage points | -0.312 to -0.046 pp |

The Image-versus-other-formats contrast remains below zero across the three-, seven- and fourteen-day block-length sensitivity analyses. This is an **observed, sample-specific association**. It may be used to formulate a pre-registered experiment hypothesis, but not as a standalone reason to reduce Image content or reallocate budget. Confounding, unknown sampling, and unverified row grain remain.

### 2. Campaign comparison

Every campaign-versus-all-other-campaigns simultaneous 95% interval includes zero in the seven-day analysis. The observed campaign-rate differences are therefore not sufficiently separated from uncertainty to establish a reliable ranking from this dataset alone.

The dashboard presents the comparisons for exploration, but the project does not recommend choosing a campaign winner on the basis of the highest observed rate.

### 3. Audience-action proxies

The dataset contains reach, profile visits and follows, allowing descriptive ratios to be calculated. Those ratios do not identify unique people, conversion attribution, purchase intent, sales, or retention. A business decision about acquisition efficiency requires deduplicated opportunities and conversions from a source system with a documented attribution window.

### 4. Practical conclusion

The most decision-useful output is not a claim that one format or campaign is a proven winner. It is a measurement plan: retain descriptive findings as hypotheses, define a controlled comparison, capture pre-treatment eligible units, reconcile attributed outcomes and costs, and apply a pre-agreed scale/hold/stop rule.

## Application and dashboard

The Streamlit application has a home page and eight analytical sections. It provides shared filters and interactive charts for exploration of the supplied dataset.

| Section | Purpose | Example questions |
|---|---|---|
| **Executive Overview** | Selected-scope KPIs, trends and key signals | What does the selected dataset slice show? |
| **Content Performance** | Format-level reach, interactions and engagement | How do Image, Reel, Story and Video records compare? |
| **Hashtag Intelligence** | Hashtag parsing, coverage and observed engagement patterns | Which hashtag groups appear most often in the selected data? |
| **Audience & Conversion Funnel** | Reach, profile visits and follow proxies | How do recorded audience-action measures relate? |
| **Posting Strategy** | Calendar cadence, date and weekday comparisons | How are records distributed over the available date range? |
| **Deep Dive & Data Quality** | Record-level inspection, filters, validation and downloads | Which source records or quality checks need review? |
| **Strategic Recommendations** | Uncertainty-aware comparisons, experiment planning and scenario analysis | What would a controlled test need to measure? |
| **Predictive Model Validation** | Temporal model comparison, holdout error and limitations | Do pre-publication signals improve on a simple baseline? |

The app also includes a separate landing page (`Home.py`) that summarizes the dataset and application workflow.

## Analytical methodology

### Data validation and preparation

The validation workflow standardizes field names and types, checks required fields and value ranges, evaluates date validity and duplicate rows, and reports unusual values for review. It preserves source records rather than silently dropping or imputing them. The dashboard reads the original project CSV by default and falls back to the workbook if the CSV is absent; the notebook also writes a cleaned derivative for audit and review.

### Descriptive analytics

The shared analytical layer calculates interaction totals, record-level and weighted engagement rates, reach and audience-action summaries, format and campaign comparisons, weekday patterns, and hashtag-level summaries. Filters are applied to the selected scope, and definitions are centralized in `src/analytics.py` to keep application pages consistent.

### Uncertainty estimation

`src/inference.py` estimates weighted engagement-rate differences between each category and all remaining categories. It uses circular moving calendar-date blocks, a shared max-deviation critical value for simultaneous intervals within each dimension, 5,000 bootstrap replicates by default, and block-length sensitivity checks. The intervals are conditional on the supplied dates and resampling assumptions; they do not adjust for confounding or establish causal effects.

### Feature engineering

The project derives engagement totals and rate measures, normalized hashtag representations, date/calendar features, content/campaign combinations, and category-level summaries. It preserves the distinction between metadata available before publication and metrics observed after exposure so the predictive evaluation can apply a feature-availability contract.

## Predictive model evaluation

Two different modelling questions are deliberately separated.

### A. Pre-publication engagement-rate evaluation

**Question:** Can fields plausibly known before publication predict a record's engagement rate on later dates?

- **Target:** total engagements divided by positive reach.
- **Candidate features:** content type, campaign type, format-campaign interaction, canonical hashtag set, hashtag count, and calendar features.
- **Excluded inputs:** reach, impressions, likes, comments, shares, saves, profile visits, follows, and potentially post-outcome annotations.
- **Validation:** chronological 80/20 split by unique dates; 40,020 development records and 9,980 future-holdout records (5 February–19 April 2025); four expanding-window temporal folds with a seven-day gap.
- **Search:** 58 configurations across 18 scikit-learn model families; preprocessing is fitted inside each validation fold.

The strongest machine-learning candidate's future-holdout MAE is approximately **0.06223516**, versus **0.06223522** for the median baseline. The difference is negligible, the date-block 95% interval includes zero, and the one-standard-error selection rule chooses the median baseline. **The evidence does not justify deploying a more complex pre-publication engagement-rate model.**

### B. Exploratory engagement-volume model conditional on exposure

A separate Ridge regression estimates total likes, comments, shares and saves using already observed reach and impressions, plus content/campaign metadata. On the 9,980-record later-date holdout, it records MAE of approximately **1,240 engagements** and R² of **0.622**, compared with a median-baseline MAE of approximately **2,120**.

This is a different task: it conditions on realized exposure and was selected after reviewing the dataset. It is **exploratory and descriptive**, not a pre-publication forecast, causal estimate, or confirmatory proof of generalizable predictive performance.

### Model governance position

No predictive model is deployed. `MODEL_MONITORING_PLAN.md` defines future release gates, batch checks, review cadence, incident response, retraining criteria and ownership requirements. Those controls are a plan, not an active production monitoring service.

## Experiment and business-impact framework

The Strategic Recommendations page translates descriptive signals into testable hypotheses. It includes sample-size planning, assumed scenario calculations, guardrails, and explicit actions for successful, inconclusive or harmful outcomes.

### Illustrative test portfolio

The current decision portfolio contains three possible Marketing/Finance tests. The values below are **assumptions used for planning**, not observed baseline conversion rates, approved stakeholder targets, campaign results or measured ROI.

| Proposed test | Assumed baseline conversion | Assumed minimum detectable lift | Planned eligible units per arm | Approx. duration at assumed volume |
|---|---:|---:|---:|---:|
| Image vs. Reel creative | 2.0% | +0.30 pp | 48,943 | 2 months |
| Tutorial vs. Product Launch message | 2.5% | +0.20 pp | 132,559 | 6 months |
| Current paid mix vs. capped tested-format reallocation | 2.0% | +0.40 pp | 28,156 | 3 months |

The planner uses 80% power and a Bonferroni-adjusted two-sided per-test alpha of approximately 1.67% to control family-wise error at 5% across three tests. The binary conversion calculation assumes independent outcomes, equal assignment, no clustering and no attrition. It does not power the continuous net-contribution outcome; that requires a separate design.

### Attributed business-impact workflow

The project includes:

- [`BUSINESS_IMPACT_DATA_CONTRACT.md`](BUSINESS_IMPACT_DATA_CONTRACT.md) — required row grain, denominator, attribution window/method, financial definitions and optional experiment fields.
- [`data/business_impact_attribution_template.csv`](data/business_impact_attribution_template.csv) — blank schema template for a validated source-system export.
- `src/business_impact.py` — validates uploaded data and calculates conversion rate, customer acquisition cost, net ROAS, contribution and ROI.
- Randomized-arm analysis — estimates treatment-minus-control conversion and net-contribution differences with unit-level bootstrap intervals when valid experiment identifiers and preregistered fields are supplied.

**No attributed business-outcome file is currently present.** The workflow is implemented, but the project has no observed attributed revenue, variable cost, paid-media cost, incremental conversion or ROI result. Do not populate the template with assumed or fabricated performance data.

## Data quality, reproducibility and governance

### Recorded validation results

The current data-quality report records:

- 50,000 source records and 14 columns.
- Zero missing cells after standardization.
- Zero exact duplicate rows.
- Zero invalid or missing dates.
- No negative values in the checked count fields.
- No records with impressions below reach in the validation output.
- No records with engagement actions above reach in the validation output.

These checks validate consistency against the project's data rules. They do not prove source authenticity, unique post grain, metric correctness, or representativeness. Because there is no stable post ID, zero exact duplicate rows does not prove that every record represents a unique post.

### Reproducibility controls

- Centralized metric and validation functions in `src/analytics.py`.
- Saved model, inference, quality and planning outputs under `reports/`.
- Fixed random seeds and explicit temporal split definitions for resampling/model workflows.
- SHA-256 hashes for source data and code in `reports/reproducibility_manifest.json`.
- Cell-by-cell workbook/CSV consistency check recorded as 50,000 rows × 14 columns with zero mismatched cells after normalization.
- Unit tests for analytics, data validation, inference, modelling, experiment design, business-impact calculations and reproducibility-manifest logic.
- GitHub Actions workflow on pushes and pull requests to run tests and Python compilation checks.

A file hash establishes byte-level identity for the checked file; it does not validate the truth or provenance of the original metrics.

## Technology stack and architecture

| Layer | Tools | Responsibility |
|---|---|---|
| Application | Python, Streamlit | Interactive multi-page analytics interface |
| Data processing | Pandas, NumPy, OpenPyXL | Loading, standardization, feature engineering and validation |
| Visualization | Plotly, Matplotlib | Interactive dashboard charts and analytical plots |
| Statistical analysis | NumPy, SciPy, custom bootstrap routines | Weighted comparisons and uncertainty intervals |
| Predictive analysis | scikit-learn | Temporal model search, baselines, Ridge and regression evaluation |
| Testing | pytest | Unit and application-page smoke tests |
| Automation | GitHub Actions | Test and compile checks on push and pull request |
| Reporting | Python report generator, PDF output | Standalone executive-report generation |

### High-level workflow

```text
Supplied CSV / Excel workbook
              │
              ▼
    Loading & schema validation
              │
              ▼
 Standardization & feature engineering
              │
       ┌──────┼───────────────┐
       ▼      ▼               ▼
 Descriptive Statistical   Temporal model
 analytics    inference    evaluation
       │      │               │
       └──────┼───────────────┘
              ▼
 Saved analysis artifacts / reproducibility manifest
              │
       ┌──────┴────────┐
       ▼               ▼
 Streamlit app     Executive report
       │
       ▼
 Experiment planning and attributed-impact workflow
```

## Repository structure

```text
Sugar Cosmetics Instagram Analytics/
│
├── Home.py                                  # Streamlit home / application entry point
├── pages/                                   # Eight analytical dashboard sections
│   ├── 1_Executive_Overview.py
│   ├── 2_Content_Performance.py
│   ├── 3_Hashtag_Intelligence.py
│   ├── 4_Audience_&_Conversion_Funnel.py
│   ├── 5_Posting_Strategy.py
│   ├── 7_Deep_Dive_and_Data_Quality.py
│   ├── 8_Strategic_Recommendations.py
│   └── 9_Predictive_Model_Validation.py
│
├── src/                                     # Reusable analytical modules and runners
│   ├── analytics.py
│   ├── inference.py
│   ├── modeling.py
│   ├── conditional_engagement_model.py
│   ├── decision_portfolio.py
│   ├── experiment_design.py
│   ├── business_impact.py
│   ├── reproducibility_manifest.py
│   ├── build_eda_notebook.py
│   ├── build_executive_report.py
│   └── run_*.py
│
├── utils/                                   # Shared app components and theme
├── notebooks/                               # Data validation and EDA notebook
├── data/                                    # Input data and attribution template
├── reports/                                 # Saved outputs, diagnostics and predictions
├── tests/                                   # Unit and dashboard smoke tests
├── images/                                  # Project branding assets
├── .github/workflows/ci.yml                 # Automated checks
│
├── BUSINESS_IMPACT_DATA_CONTRACT.md
├── DATA_PROVENANCE.md
├── MODEL_MONITORING_PLAN.md
├── PROJECT_REVIEW_CHECKLIST.md
├── requirements.txt
├── requirements-lock.txt
└── README.md
```

## Getting started

### Prerequisites

- Python 3.12 or a compatible Python version supported by the dependencies.
- Git (for cloning the repository).
- Windows PowerShell, macOS Terminal or Linux shell.

The CI workflow currently runs on Python 3.12. The exact environment lock was captured on Windows with Python 3.14.7; use the dependency-range file for a compatible fresh setup, or the lock file when recreating the captured environment.

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd "Sugar Cosmetics Instagram Analytics"
```

Replace `<YOUR_REPOSITORY_URL>` with the URL of your GitHub repository.

### 2. Create and activate a virtual environment

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

For a standard compatible installation:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For the exact captured Windows/Python 3.14.7 environment:

```bash
python -m pip install -r requirements-lock.txt
```

### 4. Launch the Streamlit application

Run the command from the project root:

```bash
streamlit run Home.py
```

Streamlit prints a local URL in the terminal. Open that URL in a browser to access the home page and the eight analytical sections.

> The project entry point is `Home.py`; do not use `streamlit run app.py` for this repository.

## Reproducing the analysis

Run commands from the repository root with the virtual environment activated.

### Data validation and exploratory analysis

Open `notebooks/01_data_validation_and_eda.ipynb` and execute cells in order. The notebook reads the app CSV, with workbook fallback, standardizes and validates fields, reports data quality and outlier flags, and writes the cleaned derivative and quality outputs.

To rebuild the notebook structure:

```bash
python src/build_eda_notebook.py
```

Outlier flags are retained for review; the workflow does not automatically remove those records.

### Regenerate category uncertainty analysis

```bash
python src/run_descriptive_inference.py
```

This writes `reports/category_rate_inference.json` using weighted category contrasts, simultaneous 95% moving date-block intervals, and block-length sensitivity outputs.

### Regenerate pre-publication model evaluation

```bash
python src/run_model_evaluation.py
```

This writes:

- `reports/model_evaluation.json`
- `reports/model_holdout_predictions.csv`

The workflow uses pre-publication metadata only and maintains chronological separation between development and future holdout dates.

### Regenerate exposure-conditional engagement-volume analysis

```bash
python src/run_conditional_engagement_volume.py
```

This writes the conditional model metrics and row-level predictions under `reports/`. Interpret these as exploratory estimates conditional on observed reach and impressions.

### Regenerate the assumed decision portfolio

```bash
python src/run_decision_portfolio.py
```

This updates `reports/assumed_decision_portfolio.json`. Its assumptions must be replaced with stakeholder-approved values before a real experiment is launched.

### Generate the reproducibility manifest

```bash
python src/reproducibility_manifest.py
```

This records hashes, runtime and package versions, input consistency, record density and category balance. It can also accept custom source and output paths; run `python src/reproducibility_manifest.py --help` for options.

### Build the executive report

```bash
python src/build_executive_report.py
```

The generator creates `reports/Sugar_Cosmetics_Instagram_Executive_Report.docx` from current data and analysis artifacts. A PDF report is included in the repository under `reports/`.

## Testing and continuous integration

Run the automated test suite:

```bash
python -m pytest -q
```

Run Python compilation checks:

```bash
python -m compileall -q Home.py pages src utils tests
```

The GitHub Actions workflow in `.github/workflows/ci.yml` runs dependency installation, pytest and compilation checks on pushes and pull requests. The tests cover core analytics, schema validation, weighted rates, hashtag handling, temporal split behavior, model feature leakage controls, inference reproducibility, experiment-size calculations, attribution validation and dashboard smoke checks.

## Known limitations and evidence gaps

The following constraints should accompany any external presentation of these results:

1. **Source authenticity is unverified.** The supplied dataset is likely associated with a public analytics repository, but no source account ID, official export evidence or independent collection record is available.
2. **Row grain is unknown.** There is no stable post ID or exact publication time. A record is not automatically a unique post.
3. **Sampling is unverified.** Near-even category counts and record density may reflect a constructed or balanced sample; they do not prove representativeness.
4. **Reach is not unique reach.** Summed record-level reach can contain repeated audience members across records.
5. **Commercial attribution is absent.** The source contains no confirmed orders, attributed conversions, net revenue, contribution margin or paid-media spend. ROI and ROAS cannot be calculated from the supplied data.
6. **No causal effect is identified.** Observed format, campaign and hashtag relationships may be confounded.
7. **The pre-publication model has no demonstrated business value.** Its future-holdout performance is effectively tied with a median baseline, so the baseline is retained and no model is recommended for deployment.
8. **The exposure-conditional model is exploratory.** It uses realized reach/impressions and was selected after examining the dataset; it is not a pre-publication model or causal estimate.
9. **No production operations are configured.** There is no scheduled data feed, production prediction service, active drift alerting, named operational owner or retraining process.
10. **Fairness cannot be assessed.** Demographic and other protected-group attributes are not available in the supplied dataset.

## Recommended next steps

A production-grade extension would require the following evidence and operating controls:

1. **Validate the source.** Confirm account identity, collection permissions, extraction method, record grain, sampling frame, timezone and metric definitions with the data owner.
2. **Introduce stable keys.** Obtain a platform post ID and a source extraction timestamp; retain immutable raw extracts and record-level lineage.
3. **Connect business outcomes.** Reconcile attributed conversions, net revenue, refunds, variable costs and paid-media costs under a Finance-approved attribution policy.
4. **Pre-register experiments.** Select one primary outcome, randomization unit, eligibility rules, attribution window, sample-size method, guardrails, stopping rule and analysis plan before treatment exposure.
5. **Evaluate decisions on contribution.** Use net contribution per eligible randomized unit—not engagement rate alone—as the scale-up gate where feasible.
6. **Set model deployment gates.** Require a stable prediction-time source, independently collected future data, material improvement over a baseline, subgroup review, model ownership and rollback approval before operational use.
7. **Operationalize data quality.** Add source reconciliation, automated batch checks, monitoring ownership and an auditable refresh process.

## Documentation and deliverables

| Resource | Description |
|---|---|
| [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) | Dataset source assessment and interpretation limits |
| [`BUSINESS_IMPACT_DATA_CONTRACT.md`](BUSINESS_IMPACT_DATA_CONTRACT.md) | Required attribution and experiment-export schema |
| [`MODEL_MONITORING_PLAN.md`](MODEL_MONITORING_PLAN.md) | Future model release, monitoring and retraining gates |
| [`PROJECT_REVIEW_CHECKLIST.md`](PROJECT_REVIEW_CHECKLIST.md) | Project review and evidence checklist |
| [`notebooks/01_data_validation_and_eda.ipynb`](notebooks/01_data_validation_and_eda.ipynb) | Data validation and exploratory analysis |
| [`reports/Sugar_Cosmetics_Instagram_Executive_Report.pdf`](reports/Sugar_Cosmetics_Instagram_Executive_Report.pdf) | Executive report |
| [`reports/implementation_review.md`](reports/implementation_review.md) | Recorded implementation review and outstanding evidence gates |
| [`reports/reproducibility_manifest.json`](reports/reproducibility_manifest.json) | Data/code hashes and reproducibility metadata |
| [`data/business_impact_attribution_template.csv`](data/business_impact_attribution_template.csv) | Blank template for validated business-outcome data |

## Data attribution and licensing

The available provenance assessment identifies the likely upstream project as [`Neeraj08823/Sugar_cosmetics_Instagram_Analytics`](https://github.com/Neeraj08823/Sugar_cosmetics_Instagram_Analytics). Please preserve that attribution when referencing the dataset.

The upstream README mentions an MIT license for its project, but the dataset's ownership and license scope have not been independently confirmed. Review the upstream repository's current license and obtain any necessary permission before redistributing the workbook or representing the dataset as official brand data. This repository does not claim ownership of the underlying dataset or affiliation with SUGAR Cosmetics / the brand owner.

---

**Project positioning:** This is a portfolio-grade analytics and decision-support implementation. It demonstrates reproducible analysis, cautious statistical interpretation, temporal model validation, experiment planning and business-impact measurement design. It is not an official Sugar Cosmetics performance report or a production marketing attribution system.
