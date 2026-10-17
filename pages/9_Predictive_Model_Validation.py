"""Display the reproducible time-forward engagement-rate evaluation."""

from pathlib import Path
import json
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from utils.common import initialize


context = initialize("Predictive Model Validation")
globals().update(context)

page_kpis("Predictive Model Validation", f)
st.subheader("Can pre-publication signals forecast engagement rate?")
st.caption(
    "This offline regression evaluates whether format, campaign, hashtag count, and calendar features "
    "forecast recorded engagement rate for later dates. It excludes reach, impressions, interaction "
    "counts, profile visits, follows, and labels that may encode post-publication information."
)

report_path = ROOT / "reports" / "model_evaluation.json"
prediction_path = ROOT / "reports" / "model_holdout_predictions.csv"
if not report_path.is_file():
    st.info("No model evaluation report exists yet.")
    st.code("python src/run_model_evaluation.py", language="powershell")
    st.stop()

try:
    report = json.loads(report_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as error:
    st.error(f"The model evaluation report could not be read: {error}")
    st.stop()

holdout = report["holdout_evaluation"]
baseline = holdout["median_baseline"]
model = holdout["selected_model"]
left, middle, right = st.columns(3)
left.metric("Median baseline MAE", f"{baseline['mae']:.4f}")
middle.metric("Selected ML candidate MAE", f"{model['mae']:.4f}", delta=f"{model['mae'] - baseline['mae']:+.4f}", delta_color="inverse")
right.metric("Holdout R²", f"{model['r2']:.3f}")
st.caption(
    f"Untouched future holdout: {holdout['start_date']} to {holdout['end_date']} "
    f"({holdout['record_count']:,} records). Best CV model: "
    f"{report['tuning']['best_estimator']} with "
    f"{report['tuning']['selected_parameters']}. Selection policy: "
    f"{report['tuning']['selection_policy']}"
)

if report["complex_model_justified"]:
    st.success("The selected model improves holdout MAE over the median baseline. Treat this as conditional evidence for this dataset and period.")
else:
    st.warning(
        "The ML candidate does not improve consistently over the median baseline. "
        f"Recommended approach: {report['model_vs_baseline']['recommended_approach']}."
    )

st.subheader("Model selection and overfit check")
st.caption(
    f"The median baseline was fixed before tuning: temporal CV MAE "
    f"{report['baseline']['temporal_cv_mae_mean']:.4f} "
    f"(SD {report['baseline']['temporal_cv_mae_std']:.4f})."
)
candidates = pd.DataFrame(report["cross_validation_candidates"])
if not candidates.empty:
    candidates["parameters"] = candidates["parameters"].map(str)
    st.dataframe(
        candidates.rename(
            columns={
                "model": "Model",
                "parameters": "Parameters",
                "cv_mae": "Temporal CV MAE",
                "cv_mae_std": "CV MAE standard deviation",
                "cv_rmse": "Temporal CV RMSE",
                "cv_r2": "Temporal CV R²",
                "train_mae": "Training MAE",
            }
        ).style.format(
            {
                "Temporal CV MAE": "{:.4f}",
                "CV MAE standard deviation": "{:.4f}",
                "Temporal CV RMSE": "{:.4f}",
                "Temporal CV R²": "{:.3f}",
                "Training MAE": "{:.4f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )
gap = report["overfit_diagnostic"]
st.caption(
    f"Best-candidate training MAE: {gap['best_candidate_train_mae']:.4f}; "
    f"temporal validation MAE: {gap['best_candidate_validation_mae']:.4f}; "
    f"validation minus training gap: {gap['validation_minus_train_mae']:+.4f}. "
    "The final holdout was excluded from tuning."
)
st.info(report["fit_diagnosis"])

interval = holdout["date_block_bootstrap_mae_difference_interval"]
if interval["lower_95"] is not None:
    st.markdown("#### Conditional date-block uncertainty interval")
    st.write(
        f"Model-minus-baseline MAE difference: "
        f"[{interval['lower_95']:+.4f}, {interval['upper_95']:+.4f}] "
        f"from {interval['repetitions']:,} date-block resamples."
    )
    st.caption(interval["interpretation"])

st.subheader("Error analysis by content and time")
subgroup_rows = []
for dimension, groups in report["subgroup_error_analysis"].items():
    for item in groups:
        subgroup_rows.append({"Dimension": dimension.replace("_", " ").title(), **item})
if subgroup_rows:
    subgroup_frame = pd.DataFrame(subgroup_rows).rename(
        columns={
            "group": "Group",
            "records": "Records",
            "mean_actual": "Mean actual rate",
            "mean_prediction": "Mean predicted rate",
            "model_mae": "Model MAE",
            "median_baseline_mae": "Baseline MAE",
            "mae_delta_vs_baseline": "MAE difference vs baseline",
        }
    )
    st.dataframe(
        subgroup_frame.style.format(
            {
                "Mean actual rate": "{:.2%}",
                "Mean predicted rate": "{:.2%}",
                "Model MAE": "{:.4f}",
                "Baseline MAE": "{:.4f}",
                "MAE difference vs baseline": "{:+.4f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )

monthly = pd.DataFrame(report["monthly_holdout_error_analysis"])
if not monthly.empty:
    monthly_long = monthly.melt(
        id_vars="month",
        value_vars=["actual_mean", "prediction_mean"],
        var_name="Series",
        value_name="Engagement rate",
    )
    monthly_long["Series"] = monthly_long["Series"].replace(
        {"actual_mean": "Actual", "prediction_mean": "Predicted"}
    )
    figure = px.line(
        monthly_long,
        x="month",
        y="Engagement rate",
        color="Series",
        markers=True,
        title="Monthly actual and predicted engagement rate on the future holdout",
        color_discrete_sequence=["#F05291", "#9B4D78"],
    )
    figure.update_yaxes(tickformat=".1%")
    figure.update_layout(template="plotly_dark", height=390)
    st.plotly_chart(figure, width="stretch")
    st.dataframe(
        monthly.rename(
            columns={
                "month": "Month",
                "records": "Records",
                "mae": "MAE",
                "mean_residual": "Mean residual",
                "actual_mean": "Actual mean rate",
                "prediction_mean": "Predicted mean rate",
            }
        ).style.format(
            {
                "MAE": "{:.4f}",
                "Mean residual": "{:+.4f}",
                "Actual mean rate": "{:.2%}",
                "Predicted mean rate": "{:.2%}",
            }
        ),
        width="stretch",
        hide_index=True,
    )

if prediction_path.is_file():
    st.download_button(
        "Download future-holdout predictions and residuals",
        prediction_path.read_bytes(),
        file_name=prediction_path.name,
        mime="text/csv",
        width="stretch",
    )

st.subheader("Limitations and deployment gate")
st.markdown(
    """
    - The evaluation is descriptive evidence about this supplied file. It does not establish performance on future official brand data.
    - The one-year time span limits seasonal and distribution-shift conclusions. A new data period is needed for external validation.
    - The date-block interval is conditional on calendar dates being valid resampling units; it is not a causal test.
    - Content/campaign subgroup errors are not demographic fairness analysis.
    - Do not deploy or use forecasts for budget decisions until the data owner confirms row grain and collection, and a later period reproduces useful performance against the baseline.
    - `MODEL_MONITORING_PLAN.md` defines production gates, ownership, checks, and rollback once a model is eligible.
    """
)
st.caption(
    f"Generated {report['generated_at_utc']} · runtime {report['runtime_seconds']:.1f}s · "
    f"model artifact SHA-256 input: {report['input']['sha256']}"
)
