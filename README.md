# Sugar Cosmetics Instagram Analytics

A Streamlit dashboard and reproducible analysis of a supplied Instagram analytics dataset. The project covers content and campaign performance, audience and conversion proxies, posting patterns, data quality, descriptive uncertainty, business decision planning, and predictive model validation.

## Project status and scope

The dashboard analyzes the records in the supplied dataset. It does not verify that the records came from Sugar Cosmetics' official account or represent its actual posting history. The collection process and row grain are undocumented, and there is no post identifier, attributable sales, revenue, or spend data. Describe results as findings about this dataset; do not present them as verified brand performance or causal impact. See [data provenance](DATA_PROVENANCE.md) for the source review.

The analysis can describe observed engagement-rate differences and use them to form hypotheses for controlled tests. It cannot establish that a content change causes more engagement, sales, or profit. Assumed decision scenarios are planning examples, not measured results. Actual financial impact can be calculated only after providing a validated attribution export that follows the [business-impact data contract](BUSINESS_IMPACT_DATA_CONTRACT.md).

## Run the dashboard

From the repository root in Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
streamlit run app.py
```

The exact lock file captures the project environment (Python 3.14.7 on Windows when recorded). To install the supported dependency ranges on another compatible Python version, use `requirements.txt` instead. The app reads `data/sugar_cosmetics_instagram_data.csv` by default and falls back to the workbook if the CSV is absent.

The JSON and prediction CSV files in `reports/` are saved analysis outputs, not temporary caches: dashboard pages and the executive-report workflow load them so expensive model and uncertainty calculations do not need to rerun on every app refresh. The `src/run_*.py` scripts are the reproducible commands that regenerate those outputs.

## Dashboard pages

- **Executive Overview** — selected-scope KPIs, trends, and summary findings.
- **Content Performance** — engagement by post format and campaign.
- **Hashtag Intelligence** — hashtag use and observed engagement patterns.
- **Audience & Conversion Funnel** — reach, engagement, profile-visit, and follow proxies.
- **Posting Strategy** — filtered cadence, monthly patterns, and weekday comparisons.
- **Deep Dive and Data Quality** — validation findings, record inspection, filters, and downloads.
- **Strategic Recommendations** — uncertainty-aware comparisons, assumed Marketing and Finance test portfolio, sample-size planning, scenario calculations, and optional attributed-impact analysis.
- **Predictive Model Validation** — leakage-aware pre-publication model comparison, overfit checks, holdout errors, and a separate exploratory estimate conditional on observed exposure.

## Main analysis and reproducibility

Use a virtual environment and run commands from the repository root. Default input and output paths are listed below; the scripts also accept command-line paths where applicable.

### Data validation and exploratory analysis

Open `notebooks/01_data_validation_and_eda.ipynb` and run its cells in order. It reads the dashboard's source CSV (with workbook fallback), normalizes and checks fields, and presents each table and chart in its own focused cell. It flags outliers for review and writes:

- `data/sugar_cosmetics_instagram_cleaned.csv`
- `reports/data_quality_report.json`
- `reports/data_quality_checks.csv`
- `reports/outlier_screening.csv`

The cleaning workflow preserves source rows; flagged values are for review and are not automatically removed. The dashboard itself reads the original project CSV rather than the notebook's cleaned derivative. To recreate the notebook structure from its generator, run `python src/build_eda_notebook.py` from the repository root.

### Pre-publication engagement-rate model search

```powershell
python src/run_model_evaluation.py
```

The target is total engagements divided by positive reach. Inputs are pre-publication metadata: post type, campaign, their interaction, canonical hashtag set and count, and calendar features. Reach, impressions, engagement counts, visits, follows, and potentially post-outcome annotations are excluded from the features. Preprocessing is fitted inside each fold.

The workflow keeps the latest 20% of unique dates as a future holdout, then uses four expanding-window date-grouped validation folds with a seven-day gap on the earlier data. It compared **58 configurations across 18 scikit-learn model families**, including linear and regularized models, robust and generalized linear models, decision trees, boosting, forests, K-nearest neighbors, and a small neural network. Kernel SVR is excluded because its quadratic training cost is impractical for this dataset size. Candidate selection minimizes temporal-CV MAE. The report separately marks the best ML candidate and the simpler approach selected by the one-standard-error rule; the future holdout is not used for tuning.

For the current report, Poisson regression is the best ML candidate by temporal CV MAE. Its holdout MAE is effectively tied with the median baseline, and the date-block uncertainty interval includes no difference. The one-standard-error rule selects the median baseline, so the results do not establish a useful ML gain. This is an evaluation result, not a deployed forecasting service.

Outputs:

- `reports/model_evaluation.json` — split details, candidate metrics, train-to-validation gaps, model selection, uncertainty interval, and subgroup/monthly error analysis.
- `reports/model_holdout_predictions.csv` — row-level future holdout predictions and residuals.

### Exposure-conditional engagement-volume model

```powershell
python src/run_conditional_engagement_volume.py
```

This separate exploratory Ridge analysis predicts likes, comments, shares, and saves conditional on already observed reach and impressions, alongside hashtag count and content/campaign metadata. Because it uses realized exposure and was selected after reviewing this dataset, it is not a pre-publication forecast or confirmatory evidence of generalizable performance. Outputs are `reports/conditional_engagement_volume.json` and `reports/conditional_engagement_volume_predictions.csv`.

### Descriptive category uncertainty

```powershell
python src/run_descriptive_inference.py
```

This generates weighted engagement-rate contrasts for post types and campaigns with simultaneous 95% moving date-block bootstrap intervals (5,000 resamples by default), plus three- and fourteen-day block-length sensitivity analyses. The report is `reports/category_rate_inference.json`. Intervals are conditional on the supplied data and resampling assumptions; they do not adjust for confounding or establish causality.

### Assumed decision portfolio

```powershell
python src/run_decision_portfolio.py
```

This recreates the illustrative Marketing and Finance test decisions, sample-size calculations, and scenario assumptions shown in the dashboard. The output is `reports/assumed_decision_portfolio.json`. Replace assumptions with stakeholder-approved values and controlled-test results before treating scenarios as business outcomes.

### Reproducibility manifest

```powershell
python src/reproducibility_manifest.py
```

This writes `reports/reproducibility_manifest.json`, recording source-data and code hashes, package and runtime versions, input-file consistency checks, row density, category balance, and available Git revision. To fingerprint another source file, pass `--source path\to\file`; to choose an output path, pass `--output path\to\manifest.json`. A hash identifies file bytes; it does not establish data authenticity or provenance.

Build the standalone executive report after refreshing the analysis outputs:

```powershell
python src/build_executive_report.py
```

This creates `reports/Sugar_Cosmetics_Instagram_Executive_Report.docx`, covering dashboard KPIs, charts, uncertainty-aware category comparisons, audience and posting summaries, data quality, assumed test economics, predictive analyses, limitations, and reproducibility. The report is self-contained; its generator uses the project environment and current data/report artifacts.

## Metrics

- **Total engagements** = likes + comments + shares + saves.
- **Post engagement rate** = total engagements / reach, when reach is positive.
- **Weighted engagement rate** = sum of eligible engagements / sum of eligible reach for the selected group.
- **Profile-visit rate proxy** = profile visits / reach.
- **Follow-per-visit proxy** = follows / profile visits, when profile visits are positive.
- **Record count** = number of dataset rows. It should not be called a post count unless the row grain is verified.

Reach is post-level reach summed across records; it should not be interpreted as unique account reach. Hashtag-level views may include one record in multiple hashtag groups. Ratios with zero denominators are missing.

## Repository map

```text
app.py                         Streamlit entry point
pages/                         Dashboard pages
src/analytics.py               Shared data loading, metrics, and validation
src/modeling.py                Temporal model evaluation
src/inference.py               Descriptive uncertainty calculations
src/conditional_engagement_model.py  Exposure-conditional model
src/decision_portfolio.py      Assumed decisions and scenarios
src/business_impact.py         Attribution-data validation and calculations
src/build_eda_notebook.py      Rebuild the focused validation and EDA notebook
notebooks/                     Data audit and exploratory analysis
data/                          Supplied data and attribution template
reports/                       Reproducible analysis outputs and review notes
tests/                         Unit and dashboard smoke checks
```

`requirements.txt` lists supported dependency ranges; `requirements-lock.txt` records the exact captured environment. The reproducibility manifest is regenerated after source, data, or dependency changes.

## Tests and continuous integration

Run the test suite and Python compilation checks with:

```powershell
python -m pytest -q
python -m compileall -q app.py pages src utils tests
```

GitHub Actions runs these checks on pushes and pull requests. The project does not include a production data feed, deployed model, scheduled retraining, or configured monitoring alerts; see the [model monitoring plan](MODEL_MONITORING_PLAN.md).

## Related documentation

- [Data provenance and verification limits](DATA_PROVENANCE.md)
- [Business-impact attribution data contract](BUSINESS_IMPACT_DATA_CONTRACT.md)
- [Model monitoring and retraining plan](MODEL_MONITORING_PLAN.md)
- [Project review checklist](PROJECT_REVIEW_CHECKLIST.md)
- [Latest implementation review](reports/implementation_review.md)
