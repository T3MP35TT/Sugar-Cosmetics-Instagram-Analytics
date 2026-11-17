<div align="center">
  <img src="images/sugar_logo.png" alt="SUGAR Cosmetics" width="190" />
  <h1>💄 Sugar Cosmetics Instagram Analytics</h1>
  <p><strong>Social Content Intelligence · Engagement Analytics · Experiment Design · Marketing Decision Support</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Streamlit-Interactive%20Analytics-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit" />
    <img src="https://img.shields.io/badge/Pandas-Data%20Preparation-150458?logo=pandas&logoColor=white" alt="Pandas" />
    <img src="https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?logo=plotly&logoColor=white" alt="Plotly" />
    <img src="https://img.shields.io/badge/scikit--learn-Model%20Evaluation-F7931E?logo=scikitlearn&logoColor=white" alt="scikit-learn" />
    <img src="https://img.shields.io/badge/Testing-pytest-0A9EDC?logo=pytest&logoColor=white" alt="pytest" />
    <img src="https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white" alt="GitHub Actions" />
  </p>
</div>

---

> ⚠️ **Data scope and attribution notice**  
> This project analyzes a supplied 50,000-record Instagram analytics dataset associated with a public Sugar Cosmetics analytics repository. The available materials do not independently verify that the records originated from Sugar Cosmetics' official Instagram account, represent its actual publishing history, or form a representative sample. All findings below describe the **supplied dataset**, not verified Sugar Cosmetics business performance. The project does not claim causal impact, attributable sales, or realized ROI.

## 📌 Project Overview

**Sugar Cosmetics Instagram Analytics** is an end-to-end social-media analytics and marketing decision-support project. It transforms a supplied Instagram dataset into a structured workflow covering data validation, exploratory analysis, engagement measurement, statistical inference, temporal model evaluation, experiment planning, and business-impact measurement design.

The project is designed around practical questions that a social-media, brand, or performance-marketing team may need to investigate:

- 💄 Which content formats show different engagement patterns in the available records?
- 📣 Do campaign categories show measurable differences after accounting for uncertainty?
- #️⃣ Which hashtags and hashtag combinations are most commonly observed, and how do their engagement patterns compare?
- 👥 How do recorded reach, profile visits, and follows relate to one another?
- 📅 How are records distributed across the available dates and weekdays?
- 📊 Are apparent category differences large and stable enough to justify a test?
- 🧠 Can information available before publication improve future engagement-rate estimates over a simple baseline?
- 🧪 What controlled experiment would be required before changing creative strategy or media allocation?
- 💰 What additional source-system data is required to measure attributed conversions, contribution, ROAS, and ROI?

The project follows an evidence-first approach: describe the available data, quantify uncertainty, evaluate models against simple baselines, and define the operational data needed before making commercial claims.

## 🎯 Business & Analytical Objectives

The project demonstrates practical analytical workflows across the social-content measurement lifecycle:

- Validate the structure, date coverage, types, and consistency of the supplied dataset.
- Standardize the data without silently dropping records or imputing values.
- Define engagement metrics consistently across the notebook, Python modules, and dashboard.
- Compare content formats and campaign categories using weighted engagement rates.
- Explore hashtag coverage, audience-action fields, and publishing-calendar patterns.
- Quantify uncertainty around category-level engagement differences.
- Evaluate pre-publication prediction using a chronological holdout and temporal cross-validation.
- Separate pre-publication forecasting from exploratory prediction conditional on observed exposure.
- Translate descriptive signals into pre-specified, testable experiment candidates.
- Establish a business-impact data contract for conversion, revenue, costs, contribution, and ROI.
- Deliver an interactive Streamlit application and an executive-facing report.
- Maintain reproducibility through saved outputs, source/code hashes, automated tests, and CI checks.

## 📊 Dataset & Key Metrics

The current analytical dataset contains the following records and fields:

| Dataset attribute | Value |
|---|---:|
| Records | **50,000** |
| Source columns | **14** |
| Date coverage | **19 April 2024 – 19 April 2025** |
| Distinct calendar dates | **366** |
| Content formats | 4 |
| Campaign categories | 5 |
| Missing cells after standardization | **0** |
| Exact duplicate rows | **0** |
| Invalid or missing dates | **0** |

### 📁 Main Dataset Files

| File | Purpose |
|---|---|
| `data/sugar_cosmetics_instagram_data.csv` | Default CSV used by the dashboard and analytical runners |
| `data/sugar_cosmetics_instagram_data.xlsx` | Workbook source used in the provenance and consistency review |
| `data/sugar_cosmetics_instagram_cleaned.csv` | Cleaned derivative generated for review and downstream use |
| `data/business_impact_attribution_template.csv` | Blank schema template for a validated business-outcome export |

### 🧾 Available Fields

The 14 source fields are:

`post_date`, `post_type`, `campaign_type`, `hashtags`, `audience_emotion`, `engagement_source`, `impressions`, `reach`, `likes`, `comments`, `shares`, `saves`, `profile_visits`, and `follows`.

### 🎞️ Content-Format Distribution

| Format | Records |
|---|---:|
| Reel | 12,599 |
| Story | 12,517 |
| Video | 12,485 |
| Image | 12,399 |

### 📣 Campaign-Category Distribution

| Campaign category | Records |
|---|---:|
| Tutorial | 10,186 |
| Giveaway | 9,998 |
| Festive Offer | 9,990 |
| Product Launch | 9,923 |
| Influencer Collab | 9,903 |

> **Interpretation note:** The near-even distribution across categories is treated as a sampling diagnostic. It does not establish that the records represent the real-world distribution of Sugar Cosmetics' published content.

### 📈 Dataset-Level Engagement Snapshot

The following figures are calculated from the supplied 50,000-record file. They are not independently verified company KPIs.

| Metric | Dataset result | Definition / interpretation |
|---|---:|---|
| Summed reach | 987,423,288 | Sum of record-level reach; not unique audience reach |
| Impressions | 1,276,045,750 | Sum of supplied record-level impressions |
| Total engagements | 183,164,417 | Likes + comments + shares + saves |
| **Weighted engagement rate** | **18.55%** | Eligible total engagements ÷ eligible summed reach |
| Profile visits | 29,634,798 | Sum of recorded profile visits |
| Follows | 8,866,710 | Sum of recorded follows |
| Profile-visit rate proxy | 3.00% | Profile visits ÷ summed reach |
| Follow-per-visit proxy | 29.92% | Follows ÷ profile visits |

The weighted engagement rate is calculated from aggregate eligible engagements and reach. It is not the arithmetic mean of record-level engagement rates.

> ⚠️ Reach, profile visits, and follows are record-level aggregate fields. They must not be interpreted as deduplicated people, attributable conversions, purchases, or retained customers without additional source-system evidence.

## 🧠 Analytical Framework

The project uses multiple analytical perspectives rather than relying on a single engagement leaderboard.

### 💄 1. Content Performance Analytics

Content analysis compares the four recorded formats:

- Image
- Reel
- Story
- Video

Key measures and comparisons include:

- Total likes, comments, shares, and saves
- Total engagements
- Reach and impressions
- Weighted engagement rate
- Format-level comparisons against all other formats
- Engagement mix and distribution
- Format and campaign intersections

The purpose is to identify descriptive patterns and candidate hypotheses—not to claim that a format caused higher engagement.

### 📣 2. Campaign Analytics

Campaign analysis compares the five recorded campaign labels:

- Giveaway
- Festive Offer
- Influencer Collab
- Product Launch
- Tutorial

The dashboard supports category-level comparisons, but the statistical analysis does not establish a reliable campaign winner. All campaign-versus-rest simultaneous confidence intervals include zero in the seven-day analysis.

### #️⃣ 3. Hashtag Intelligence

Hashtag analysis standardizes and parses hashtag strings to support:

- Hashtag frequency and coverage
- Common hashtag groups and combinations
- Hashtag-level engagement summaries
- Comparison of records containing selected hashtag groups
- Exploration of format and campaign context

Hashtag groups can overlap. A record with multiple hashtags may be included in more than one hashtag group, so hashtag group totals must not be added together as if they were mutually exclusive categories.

### 👥 4. Audience & Conversion-Funnel Proxies

The supplied data contains reach, profile visits, and follows. The project uses these fields to explore:

- Profile visits relative to summed reach
- Follows relative to profile visits
- Audience-action patterns by content and campaign categories
- Changes in recorded audience-action metrics across the available date range

These are **descriptive proxies**, not verified conversion rates. The data does not contain unique-user identifiers, attributed orders, customer acquisition cost, or an approved conversion attribution window.

### 📅 5. Posting Strategy & Calendar Analytics

The date field supports analysis of:

- Record distribution by date
- Weekday patterns
- Month and calendar trends
- Engagement patterns across the observed calendar
- Selected-scope comparisons through interactive filters

Because exact publication timestamps and stable post identifiers are unavailable, the project avoids treating record density as a verified publishing schedule or posting frequency for the brand.

### 🔎 6. Deep Dive & Data Quality

The deep-dive area supports record-level exploration and review of:

- Selected records and filters
- Data types and schema
- Missing-value checks
- Duplicate-row checks
- Invalid dates and count-field validation
- Impressions-versus-reach checks
- Engagement-actions-versus-reach checks
- Outlier screening and review flags
- Metric definitions and methodology notes

Outliers are retained for review rather than automatically deleted. A statistical flag is not proof that a record is erroneous.

### 📊 7. Statistical Inference

The inference workflow compares each category's weighted engagement rate with the weighted rate for all other categories in the same dimension.

The implementation uses:

- Weighted engagement-rate contrasts, expressed in percentage points
- Circular moving calendar-date block resampling
- Seven-day blocks for the primary interval analysis
- 5,000 bootstrap repetitions by default
- Simultaneous 95% intervals using a shared max-deviation critical value within each dimension
- Three-day and fourteen-day block-length sensitivity checks

The intervals are conditional on the supplied dates and resampling assumptions. They do not correct for unmeasured confounding, unknown sampling, or unclear row grain, and they do not establish causal effects.

## 🔬 Advanced Engagement Analysis

### 📌 Content-Format Comparison

The full-file comparison reports the following weighted engagement rates and differences versus all other formats:

| Format | Weighted engagement rate | Difference vs. all other formats | 7-day simultaneous 95% interval |
|---|---:|---:|---:|
| Story | 18.63% | +0.101 percentage points | -0.032 to +0.234 pp |
| Reel | 18.60% | +0.062 percentage points | -0.070 to +0.195 pp |
| Video | 18.56% | +0.015 percentage points | -0.118 to +0.148 pp |
| Image | 18.42% | -0.179 percentage points | -0.312 to -0.046 pp |

The Image-versus-other-formats contrast remains below zero across the three-, seven-, and fourteen-day block-length sensitivity analyses. This is a sample-specific association and may inform a pre-registered experiment hypothesis. It is not, by itself, a reason to reduce Image content or reallocate marketing spend.

### 📣 Campaign Comparison

Every campaign-versus-all-other-campaigns simultaneous 95% interval includes zero in the seven-day analysis. The observed campaign differences are not sufficiently separated from uncertainty to establish a reliable ranking from this dataset alone.

The project therefore avoids naming a campaign winner based only on the highest observed rate.

### 👥 Audience-Action Interpretation

Profile visits and follows are useful descriptive fields, but the available dataset does not demonstrate:

- Unique people reached across posts
- Unique profile visitors
- Attributed followers or customers
- Verified purchases or orders
- Customer retention or repeat purchase
- Incremental lift caused by a specific creative or campaign

These outcomes require source-system integration and a documented attribution design.

## 🧠 Predictive Analytics & Model Validation

The project separates two modelling questions because they have different information availability and business uses.

### 🎯 A. Pre-Publication Engagement-Rate Evaluation

**Business question:** Can information plausibly available before a post is published help estimate its engagement rate on later dates?

- **Target:** Total engagements divided by positive reach.
- **Candidate features:** Content type, campaign type, format-campaign interaction, canonical hashtag set, hashtag count, and calendar features.
- **Excluded features:** Reach, impressions, likes, comments, shares, saves, profile visits, follows, and potentially post-outcome annotations.
- **Temporal split:** Chronological 80/20 split by unique dates.
- **Development set:** 40,020 records.
- **Future holdout:** 9,980 records, 5 February–19 April 2025.
- **Model search:** 58 configurations across suitable scikit-learn regression families, evaluated using expanding-window temporal folds with a seven-day gap.

| Holdout result | MAE |
|---|---:|
| Median baseline | 0.06223522 |
| Best machine-learning candidate | 0.06223516 |

The difference is negligible. The date-block bootstrap interval includes zero, and the one-standard-error selection rule retains the median baseline.

> **Model governance decision:** The available evidence does not justify deploying a more complex pre-publication engagement-rate model. A new independent future period and a material, stable improvement over the baseline would be required before reconsidering deployment.

### 📊 B. Exploratory Engagement-Volume Model Conditional on Exposure

A separate Ridge regression estimates engagement volume (likes + comments + shares + saves) using observed reach and impressions together with content and campaign metadata.

| Future-holdout metric | Ridge model | Median baseline |
|---|---:|---:|
| MAE | ~1,240 engagements | ~2,120 engagements |
| R² | 0.622 | -0.059 |

The Ridge model reduces holdout MAE by approximately 41.5% relative to the median baseline in this supplied file. However, this analysis is explicitly **exploratory**: it conditions on realized exposure, and the target/features were selected after reviewing the dataset. It is not a pre-publication forecast, causal estimate, or confirmatory proof of generalizable model performance.

### 🛡️ Model Governance Position

- No predictive model is deployed in production.
- The median baseline remains the selected approach for the pre-publication engagement-rate task.
- Exposure-conditional engagement-volume estimates are retained as exploratory analysis only.
- `MODEL_MONITORING_PLAN.md` defines future release, review, monitoring, and retraining gates; it is a governance plan, not an active production monitoring service.

## 🧪 Experiment Design & Marketing Decision Support

The Strategic Recommendations section converts descriptive findings into testable hypotheses. It includes sample-size planning, assumptions, guardrails, scenario calculations, and scale/hold/stop decision rules.

### 🧪 Illustrative Test Portfolio

The following tests are planning examples. Their baseline rates, minimum detectable effects, volume assumptions, and durations are **not observed campaign outcomes or approved stakeholder targets**.

| Proposed test | Assumed baseline conversion | Assumed minimum detectable lift | Planned eligible units per arm | Approx. duration at assumed volume |
|---|---:|---:|---:|---:|
| Image vs. Reel creative | 2.0% | +0.30 pp | 48,943 | 2 months |
| Tutorial vs. Product Launch message | 2.5% | +0.20 pp | 132,559 | 6 months |
| Current paid mix vs. capped tested-format reallocation | 2.0% | +0.40 pp | 28,156 | 3 months |

The planner uses 80% power and a Bonferroni-adjusted two-sided per-test alpha of approximately 1.67% to control family-wise error at 5% across three tests. The binary conversion calculation assumes independent outcomes, equal assignment, no clustering, and no attrition. It does not power the continuous net-contribution outcome; that requires a separate design.

### 💰 Business-Impact Measurement

The project includes a business-impact workflow designed to validate an export containing the financial and attribution fields required for decision-making.

Potential outputs include:

- Conversion rate
- Customer acquisition cost
- Net return on ad spend (ROAS)
- Net contribution
- Return on investment (ROI)
- Treatment-versus-control conversion difference
- Treatment-versus-control net-contribution difference
- Unit-level bootstrap uncertainty intervals when experiment identifiers and preregistered fields are supplied

**No attributed business-outcome file is currently present.** There is no observed attributed revenue, variable cost, paid-media cost, incremental conversion, or ROI result in the supplied project data. The template must be populated only from a validated source-system export; assumptions must not be presented as actual outcomes.

## 🌐 Streamlit Analytics Platform

The project provides a multi-page Streamlit application with a home page and eight analytical sections. The application uses shared utilities for loading, metric calculation, filtering, and theme presentation.

| Application section | Analytical purpose |
|---|---|
| 💼 **Executive Overview** | Selected-scope KPIs, trends, performance signals, and management readout |
| 🎨 **Content Performance** | Compare Image, Reel, Story, and Video records using reach, interactions, and engagement metrics |
| #️⃣ **Hashtag Intelligence** | Explore hashtag frequency, coverage, and observed engagement patterns |
| 👥 **Audience & Conversion Funnel** | Examine reach, profile visits, and follows as aggregate audience-action proxies |
| 📅 **Posting Strategy** | Explore date distribution, calendar patterns, weekday comparisons, and cadence signals |
| 🔎 **Deep Dive & Data Quality** | Filter records, inspect data, review data quality, and explore methodology |
| 🧪 **Strategic Recommendations** | Review category uncertainty, proposed experiments, scenario assumptions, and business-impact inputs |
| 🧠 **Predictive Model Validation** | Inspect temporal evaluation, baseline comparisons, model errors, and conditional engagement-volume analysis |

The separate `Home.py` page introduces the project, displays a dataset snapshot, describes the analytical workflow, and provides navigation context.

## 🎨 Context-Aware Dashboard Experience

The application uses a shared visual theme and reusable utilities to keep page behavior consistent.

### 🧭 Shared Application Components

- Dataset loading and fallback handling
- Common metric and analytical functions
- Shared filters and scope-aware summaries
- Reusable page and visual components
- Consistent theme and layout settings
- Data-quality and interpretation notices

### 🧩 User Workflow

```text
📥 Select the analytical scope
              ↓
📊 Review the selected-scope summary
              ↓
🔎 Compare content, campaign, hashtag and audience patterns
              ↓
🛡️ Inspect data quality and uncertainty
              ↓
🧪 Evaluate experiment candidates
              ↓
💰 Validate business outcomes when attributed data is available
```

The dashboard is designed as an exploration and decision-support interface. It does not automate media allocation or deploy predictive decisions.

## 🛡️ Data Quality, Reproducibility & Governance

### ✅ Recorded Data-Quality Checks

The current validation report records:

- 50,000 records and 14 source columns.
- Zero missing cells after standardization.
- Zero exact duplicate rows.
- Zero invalid or missing dates.
- No negative values in the checked count fields.
- No records with impressions below reach in the validation output.
- No records with engagement actions above reach in the validation output.
- No zero-reach rows in the validation output.

These checks establish consistency against the project's validation rules. They do not prove source authenticity, correct metric definitions, a unique-post row grain, or sample representativeness. Since a stable post identifier is not available, zero exact duplicate rows does not prove every record represents a unique post.

### 🔁 Reproducibility Controls

- Centralized metric and validation functions in `src/analytics.py`.
- Saved inference, model, quality, and planning outputs in `reports/`.
- Fixed random seeds and explicit temporal split definitions for resampling and model workflows.
- SHA-256 hashes for source data and code in `reports/reproducibility_manifest.json`.
- Workbook/CSV consistency check recorded as 50,000 rows × 14 columns, with zero mismatched cells after normalization.
- Unit tests for analytics, inference, modelling, experiment design, business-impact calculations, and reproducibility-manifest logic.
- GitHub Actions workflow configured to run tests and Python compilation checks on pushes and pull requests.

A file hash confirms byte-level identity for the checked file; it does not independently validate the truth or provenance of the original metrics.

## 🌐 Data & Analytical Architecture

### 🔄 End-to-End Workflow

```text
          📄 Supplied CSV / Excel Workbook
                         │
                         ▼
              🔍 Schema & Data Validation
                         │
                         ▼
             🧹 Standardization / Features
                         │
              ┌──────────┼──────────────┐
              ▼          ▼              ▼
        📊 Descriptive  📐 Statistical  🧠 Temporal
          Analytics     Inference      Evaluation
              │          │              │
              └──────────┼──────────────┘
                         ▼
              📁 Saved Analytical Outputs
                         │
                ┌────────┴────────┐
                ▼                 ▼
          ⚡ Streamlit App   📑 Executive Report
                │
                ▼
       🧪 Experiment & Business-Impact
             Measurement Design
```

### 🧱 Architecture Layers

| Layer | Components | Responsibility |
|---|---|---|
| Input | CSV, Excel workbook | Supplied dataset and source comparison |
| Validation | `src/analytics.py`, notebook, quality reports | Schema checks, standardization, data-quality diagnostics |
| Analytics | `src/analytics.py` | Shared descriptive metrics and feature preparation |
| Inference | `src/inference.py` | Weighted category contrasts and date-block uncertainty intervals |
| Modelling | `src/modeling.py`, `src/conditional_engagement_model.py` | Temporal pre-publication evaluation and exposure-conditional exploratory model |
| Decision support | `src/experiment_design.py`, `src/decision_portfolio.py`, `src/business_impact.py` | Sample-size planning, scenarios, and business-outcome validation |
| Application | `Home.py`, `pages/`, `utils/` | Interactive Streamlit experience |
| Reporting | `src/build_executive_report.py`, `reports/` | Executive report and supporting analysis artifacts |
| Quality controls | `tests/`, `.github/workflows/ci.yml` | Automated checks and reproducibility controls |

## 🛠️ Technical Stack

| Technology | Purpose |
|---|---|
| 🐍 Python | Data preparation, analytics, modelling, and application logic |
| 🐼 pandas | Data loading, tabular transformation, and aggregation |
| 🔢 NumPy | Numerical operations and statistical computation |
| ⚡ Streamlit | Multi-page interactive dashboard |
| 📊 Plotly | Interactive visualizations |
| 📈 Matplotlib | Analytical plots and report visuals |
| 🧠 scikit-learn | Regression models, baselines, preprocessing, and temporal evaluation |
| 📗 OpenPyXL | Excel workbook ingestion |
| 🧪 pytest | Unit tests and application smoke tests |
| 🔁 GitHub Actions | Automated CI checks |
| 📝 Jupyter | Notebook-based validation and exploratory analysis |

## 📊 Data Analyst Skills Demonstrated

### 🔍 Data Preparation & Quality

- File ingestion from CSV and Excel
- Schema inspection and type standardization
- Missing-value and duplicate checks
- Date validation and calendar feature creation
- Range and consistency checks
- Outlier screening without automatic deletion
- Data provenance and interpretation documentation

### 📈 Business & Descriptive Analytics

- KPI definition and metric contracts
- Engagement-rate calculation
- Weighted aggregation
- Content and campaign segmentation
- Hashtag normalization and grouping
- Audience-action proxy analysis
- Calendar and weekday analysis
- Comparative performance analysis

### 📐 Statistical Analysis

- Weighted category contrasts
- Percentage-point interpretation
- Moving date-block bootstrap
- Simultaneous confidence intervals
- Sensitivity analysis
- Sampling and uncertainty caveats
- Separation of association from causation

### 🧠 Predictive Analytics

- Feature-availability contracts
- Leakage-aware modelling
- Chronological train/holdout separation
- Expanding-window temporal cross-validation
- Baseline comparison
- MAE, RMSE, and R² evaluation
- Model complexity and deployment assessment

### 🧪 Experiment & Business Measurement

- Hypothesis development
- Minimum detectable effect assumptions
- Sample-size planning
- Power and multiple-testing considerations
- Guardrail and stopping-rule design
- Attribution data requirements
- Conversion, CAC, ROAS, contribution, and ROI validation framework

### 🎨 Analytics Communication

- Executive KPI summaries
- Interactive dashboard design
- Analytical storytelling
- Decision-support framing
- Limitations and governance communication
- Reproducible reporting

## 📁 Project Structure

```text
Sugar-Cosmetics-Instagram-Analytics/
│
├── Home.py                                  # Streamlit home / application entry point
│
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
├── utils/                                   # Shared app utilities and theme
│   ├── common.py
│   └── theme.py
│
├── src/                                     # Reusable analytical modules and runners
│   ├── analytics.py
│   ├── inference.py
│   ├── modeling.py
│   ├── conditional_engagement_model.py
│   ├── experiment_design.py
│   ├── decision_portfolio.py
│   ├── business_impact.py
│   ├── reproducibility_manifest.py
│   ├── build_eda_notebook.py
│   ├── build_executive_report.py
│   └── run_*.py
│
├── notebooks/
│   └── 01_data_validation_and_eda.ipynb
│
├── data/                                    # Supplied data and attribution template
│   ├── sugar_cosmetics_instagram_data.csv
│   ├── sugar_cosmetics_instagram_data.xlsx
│   ├── sugar_cosmetics_instagram_cleaned.csv
│   └── business_impact_attribution_template.csv
│
├── reports/                                 # Saved metrics, diagnostics and reports
│   ├── category_rate_inference.json
│   ├── conditional_engagement_volume.json
│   ├── data_quality_report.json
│   ├── model_evaluation.json
│   ├── reproducibility_manifest.json
│   ├── Sugar_Cosmetics_Instagram_Executive_Report.pdf
│   └── ...
│
├── tests/                                   # Automated unit and application tests
│   ├── test_analytics.py
│   ├── test_app_pages.py
│   ├── test_business_impact.py
│   ├── test_experiment_design.py
│   ├── test_inference.py
│   ├── test_modeling.py
│   └── test_reproducibility_manifest.py
│
├── images/                                  # Project brand assets
├── .github/workflows/ci.yml                 # GitHub Actions checks
│
├── BUSINESS_IMPACT_DATA_CONTRACT.md
├── DATA_PROVENANCE.md
├── MODEL_MONITORING_PLAN.md
├── PROJECT_REVIEW_CHECKLIST.md
├── requirements.txt
├── requirements-lock.txt
└── README.md
```

## 🚀 Getting Started

### ✅ Prerequisites

- Python 3.12 (the GitHub Actions workflow uses Python 3.12).
- Git, if cloning the repository.
- Windows PowerShell, macOS Terminal, or Linux shell.

The project includes `requirements.txt` for compatible dependency ranges and `requirements-lock.txt` for the captured Windows/Python 3.14.7 environment. For a fresh supported setup, use the dependency-range file with Python 3.12.

### 1. 📥 Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd "Sugar Cosmetics Instagram Analytics"
```

Replace `<YOUR_REPOSITORY_URL>` with the GitHub repository URL.

### 2. 🐍 Create a Virtual Environment

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

### 3. 📦 Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For the captured Windows/Python 3.14.7 environment, the lock file is also available:

```bash
python -m pip install -r requirements-lock.txt
```

### 4. ⚡ Launch the Streamlit Dashboard

Run this command from the project root:

```bash
streamlit run Home.py
```

Streamlit will print a local URL in the terminal. Open it in your browser to access the home page and the eight analytical sections.

> The actual application entry point in this project is `Home.py`.

## 🔁 Reproducing the Analysis

Run commands from the project root with the virtual environment activated.

### 📓 Data Validation & Exploratory Analysis

Open and execute:

```text
notebooks/01_data_validation_and_eda.ipynb
```

To rebuild the notebook structure:

```bash
python src/build_eda_notebook.py
```

The validation workflow standardizes and checks the supplied data, records quality findings, and writes the cleaned derivative and supporting outputs. Outlier flags are retained for review; records are not automatically removed.

### 📐 Regenerate Category Inference

```bash
python src/run_descriptive_inference.py
```

This updates `reports/category_rate_inference.json` with weighted category contrasts, simultaneous date-block intervals, and block-length sensitivity results.

### 🧠 Regenerate Pre-Publication Model Evaluation

```bash
python src/run_model_evaluation.py
```

This updates:

- `reports/model_evaluation.json`
- `reports/model_holdout_predictions.csv`

The evaluation uses pre-publication metadata, chronological separation, and expanding-window temporal validation.

### 📊 Regenerate Exposure-Conditional Engagement-Volume Analysis

```bash
python src/run_conditional_engagement_volume.py
```

This updates the conditional-model metrics and predictions under `reports/`. Interpret the result as exploratory analysis conditional on observed reach and impressions.

### 🧪 Regenerate the Assumed Decision Portfolio

```bash
python src/run_decision_portfolio.py
```

This updates `reports/assumed_decision_portfolio.json`. Replace planning assumptions with stakeholder-approved inputs before conducting a real experiment.

### 🔁 Generate the Reproducibility Manifest

```bash
python src/reproducibility_manifest.py
```

This records file hashes, runtime and package versions, input consistency, record density, and category balance. Use `python src/reproducibility_manifest.py --help` to inspect available options.

### 📑 Build the Executive Report

```bash
python src/build_executive_report.py
```

The project includes an executive report PDF under `reports/` and the source generator in `src/`.

## 🧪 Testing & Continuous Integration

Run the automated test suite:

```bash
python -m pytest -q
```

Run Python compilation checks:

```bash
python -m compileall -q Home.py pages src utils tests
```

The GitHub Actions workflow in `.github/workflows/ci.yml` is configured to run on pushes and pull requests. It installs supported dependencies, runs pytest, and compiles the project Python files.

Test coverage includes:

- Core metric calculations and analytical functions
- Data standardization and validation
- Hashtag handling and weighted-rate calculations
- Temporal split and leakage-control behavior
- Statistical inference and reproducibility
- Experiment sample-size and planning logic
- Business-impact input validation
- Dashboard-page smoke checks

## 🛡️ Data Attribution, Security & Responsible Use

### Dataset Attribution

The available provenance assessment identifies [`Neeraj08823/Sugar_cosmetics_Instagram_Analytics`](https://github.com/Neeraj08823/Sugar_cosmetics_Instagram_Analytics) as the likely upstream project. Preserve this attribution when referencing the supplied dataset.

The upstream README mentions an MIT license for its project, but the ownership and license scope of the dataset have not been independently confirmed. Review the upstream repository's current license and obtain any necessary permission before redistributing the workbook or representing it as official brand data.

### Security

The project does not require API keys for the supplied local analysis workflow. Keep local credentials, private exports, and unrelated personal data out of source control. Do not add unverified customer-level or financial data to the public repository.

### Responsible Interpretation

- Do not describe the dataset as an official Sugar Cosmetics export without independent verification.
- Do not present record-level reach as unique people reached.
- Do not describe profile visits or follows as attributed purchases.
- Do not present assumed experiment scenarios as realized campaign impact.
- Do not deploy the pre-publication engagement-rate model based on the current evaluation.
- Do not interpret exploratory conditional model results as causal lift.

## 💡 Key Design Principles

### 1. 📥 Data First

Validate the supplied files, understand the field definitions, and establish the record grain before interpreting performance.

### 2. 📏 Consistent Metrics

Keep metric definitions centralized so the same denominator and eligibility rules are used across the notebook, application, inference, and reports.

### 3. 🛡️ Evidence Before Claims

Separate descriptive findings, statistical uncertainty, predictive evaluation, experiment assumptions, and verified business outcomes.

### 4. 📊 Multiple Measures

Use reach, impressions, interactions, engagement rates, and audience-action proxies together rather than relying on one headline metric.

### 5. 🧠 Baseline Before Complexity

Require a meaningful and stable out-of-sample gain over a simple baseline before recommending a more complex predictive model.

### 6. 🧪 Test Before Reallocation

Treat category patterns as hypotheses. Use controlled experiments and pre-agreed guardrails before changing strategy or spend.

### 7. 💰 Finance-Ready Measurement

Require attributed conversion, net revenue, variable cost, media cost, and contribution definitions before reporting ROAS or ROI.

### 8. 🔁 Reproducibility

Preserve source files, analysis artifacts, hashes, tests, and documented execution steps so that results can be reviewed and regenerated.

## 📈 Why This Project Matters

Sugar Cosmetics Instagram Analytics demonstrates a complete analytical workflow rather than a static social-media dashboard:

```text
📄 Supplied Data
      ↓
🛡️ Data Validation & Provenance Review
      ↓
🧹 Standardization & Feature Engineering
      ↓
📊 Descriptive Analytics
      ↓
📐 Statistical Inference
      ↓
🧠 Temporal Model Evaluation
      ↓
🧪 Experiment Design
      ↓
💰 Business-Impact Measurement Framework
      ↓
⚡ Interactive Streamlit Application
      ↓
📑 Executive Reporting & Decision Support
```

The same analytical discipline can be adapted to other domains, including:

- 💄 Brand and social-media analytics
- 🛍️ E-commerce and product analytics
- 📣 Digital marketing performance
- 👥 Customer and audience analytics
- 💰 Campaign and financial measurement
- 📈 Growth and experimentation analytics

## 🎓 What This Project Demonstrates

The project demonstrates practical experience with:

- 📥 Structured data ingestion
- 🛡️ Data quality assessment and provenance review
- 🧹 Data standardization and feature engineering
- 📊 KPI design and descriptive analytics
- #️⃣ Text normalization and hashtag analysis
- 📅 Calendar and time-based analysis
- 📐 Statistical inference and uncertainty estimation
- 🧠 Predictive model evaluation and leakage controls
- 🧪 Experiment design and sample-size planning
- 💰 Business-impact and attribution requirements
- ⚡ Streamlit application development
- 📈 Interactive visualization and storytelling
- 🧪 Unit testing and CI automation
- 🔁 Reproducible analytical workflows
- 📑 Executive communication and decision-support design

The broader objective is to demonstrate the ability to move from data to a defensible business question, validate the evidence, communicate uncertainty, and identify the next measurement action.

## ⭐ Project Highlights

```text
💄 50,000 Supplied Records
          +
📅 366 Calendar Dates
          +
📊 14 Source Fields
          +
🎨 4 Content Formats
          +
📣 5 Campaign Categories
          +
📐 Date-Block Statistical Inference
          +
🧠 Chronological Model Validation
          +
🧪 Experiment Sample-Size Planning
          +
💰 Business-Impact Data Contract
          +
⚡ 8 Streamlit Analytics Sections
          +
🛡️ Automated Tests & GitHub Actions
          +
📑 Executive Reporting
```

---

## 👤 Author

**Kartikey Singh**  
**Data Analyst | Python | SQL | Power BI | Data Visualization**

- 💻 GitHub: [T3MP35TT](https://github.com/T3MP35TT)
- 🔗 LinkedIn: [Kartikey Singh](https://www.linkedin.com/in/btwitskartiksinghdatanalyst/)
- 💼 Portfolio: [Kartikey Singh](https://sites.google.com/view/kartikeysingh09/home)

---

⭐ If you find this project useful, consider giving the repository a star.

**Project positioning:** This is a portfolio-grade analytics and decision-support implementation based on a supplied social-media dataset. It is not an official Sugar Cosmetics performance report, a verified marketing attribution system, or a production model deployment.
