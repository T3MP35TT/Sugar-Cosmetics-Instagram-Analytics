"""Display the reproducible time-forward engagement-rate evaluation."""

from pathlib import Path
import json
import sys

import numpy as np
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
    "This offline regression evaluates whether format, campaign, their interaction, canonical hashtag combinations, and calendar features "
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
sidebar_gain = holdout["best_ml_candidate"]["mae"] - holdout["median_baseline"]["mae"]
render_sidebar_summary(
    "Predictive Model Validation",
    f,
    detail_metrics=[
        ("Best ML candidate", report["tuning"]["best_ml_candidate_estimator"]),
        ("One-SE supported choice", report["tuning"]["one_se_selected_approach"]),
        ("Holdout MAE change vs baseline", f"{sidebar_gain * 100:+.6f} pp"),
    ],
)

baseline = holdout["median_baseline"]
model = holdout["best_ml_candidate"]
left, middle, right = st.columns(3)
left.metric("Median baseline MAE", f"{baseline['mae'] * 100:.2f} pp")
middle.metric(
    "Best ML candidate MAE",
    f"{model['mae'] * 100:.2f} pp",
    delta=f"{(model['mae'] - baseline['mae']) * 100:+.6f} pp vs baseline",
    delta_color="inverse",
)
right.metric("Holdout R²", f"{model['r2']:.4f}")
st.caption(
    f"Untouched future holdout: {holdout['start_date']} to {holdout['end_date']} "
    f"({holdout['record_count']:,} records). The one-SE rule selects "
    f"{report['tuning']['one_se_selected_approach']} with "
    f"{report['tuning']['selected_parameters']}; the strongest ML candidate was "
    f"{report['tuning']['best_ml_candidate_estimator']} with {report['tuning']['best_ml_candidate_parameters']}. Selection policy: "
    f"{report['tuning']['selection_policy']}"
)

if report["complex_model_justified"]:
    st.success("The selected model improves holdout MAE over the median baseline. Treat this as conditional evidence for this dataset and period.")
else:
    interval = holdout["date_block_bootstrap_mae_difference_interval"]
    st.info(
        f"In this {holdout['record_count']:,}-post future holdout, the best ML candidate's MAE was "
        f"{model['mae'] * 100:.2f} percentage points versus {baseline['mae'] * 100:.2f} for the median baseline. "
        f"The model-minus-baseline difference was {holdout['mae_difference_model_minus_baseline'] * 100:+.6f} pp "
        f"(date-block 95% interval {interval['lower_95'] * 100:+.6f} to {interval['upper_95'] * 100:+.6f} pp). "
        f"Because that interval includes zero, this dataset does not show a measurable advantage for the ML candidate; "
        f"the one-standard-error rule therefore selects {report['tuning']['one_se_selected_approach']} as the supported estimate."
    )

st.subheader("Model selection and overfit check")
st.caption(
    f"Selection searched {report['tuning']['candidate_count']} configurations across "
    f"{len(report['tuning']['model_families_tested'])} model families using the same four date-forward folds. "
    "The best ML candidate is the lowest temporal-CV MAE among ML models; the one-SE result separately identifies the simplest supported choice."
)
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
                "validation_minus_train_mae": "CV minus train MAE",
                "selected_by_one_se_rule": "Selected by one-SE rule",
                "best_ml_candidate": "Best ML candidate",
            }
        ).style.format(
            {
                "Temporal CV MAE": "{:.4f}",
                "CV MAE standard deviation": "{:.4f}",
                "Temporal CV RMSE": "{:.4f}",
                "Temporal CV R²": "{:.3f}",
                "Training MAE": "{:.4f}",
                "CV minus train MAE": "{:+.4f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )
gap = report["overfit_diagnostic"]
st.caption(
    f"Best ML candidate training MAE: {gap['best_ml_candidate_train_mae']:.4f}; "
    f"temporal validation MAE: {gap['best_ml_candidate_validation_mae']:.4f}; "
    f"validation minus training gap: {gap['validation_minus_train_mae']:+.4f}. "
    "The final holdout was excluded from tuning."
)
st.caption(
    "Overfit check by candidate: compare each row’s CV MAE with its CV training MAE. "
    "A larger positive gap means errors rose on later validation dates; the gap is descriptive and is not, by itself, a deployment decision."
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
        {"actual_mean": "Actual", "prediction_mean": "Pre-publication model"}
    )
    monthly_long["month"] = pd.to_datetime(monthly_long["month"] + "-01")

    # Add a time-varying reference forecast based only on prior observed daily
    # engagement rates. Score it on the same later-date rows as the primary model.
    forecast_source = raw.copy()
    forecast_source["post_date"] = pd.to_datetime(forecast_source["post_date"], errors="coerce")
    for column in ["reach", "likes", "comments", "shares", "saves"]:
        forecast_source[column] = pd.to_numeric(forecast_source[column], errors="coerce")
    forecast_source["total_engagements"] = forecast_source[
        ["likes", "comments", "shares", "saves"]
    ].sum(axis=1, min_count=4)
    forecast_source["engagement_rate"] = forecast_source["total_engagements"] / forecast_source["reach"].where(
        forecast_source["reach"] > 0
    )
    forecast_source = forecast_source.dropna(subset=["post_date", "engagement_rate"])
    forecast_source = forecast_source[np.isfinite(forecast_source["engagement_rate"])].copy()
    forecast_source["date"] = forecast_source["post_date"].dt.normalize()
    daily_rates = forecast_source.groupby("date")["engagement_rate"].mean().sort_index()
    holdout_start = pd.Timestamp(holdout["start_date"])
    holdout_end = pd.Timestamp(holdout["end_date"])
    historical_rates = daily_rates.loc[daily_rates.index < holdout_start].tolist()
    test_daily_rates = daily_rates.loc[
        (daily_rates.index >= holdout_start) & (daily_rates.index <= holdout_end)
    ]
    rolling_daily_predictions = {}
    for date, observed_rate in test_daily_rates.items():
        rolling_daily_predictions[date] = float(np.mean(historical_rates[-56:]))
        historical_rates.append(float(observed_rate))

    rolling_rows = forecast_source.loc[
        (forecast_source["date"] >= holdout_start) & (forecast_source["date"] <= holdout_end)
    ].copy()
    rolling_rows["rolling_prediction"] = rolling_rows["date"].map(rolling_daily_predictions)
    rolling_rows = rolling_rows.dropna(subset=["rolling_prediction"])
    rolling_mae = float(np.abs(rolling_rows["engagement_rate"] - rolling_rows["rolling_prediction"]).mean())
    development_rates = forecast_source.loc[
        forecast_source["date"] < holdout_start, "engagement_rate"
    ]
    median_baseline_mae = float(
        np.abs(rolling_rows["engagement_rate"] - development_rates.median()).mean()
    )
    rolling_rows["month"] = rolling_rows["date"].dt.to_period("M").astype(str)
    rolling_monthly = rolling_rows.groupby("month").agg(
        rolling_prediction=("rolling_prediction", "mean")
    ).reset_index()
    rolling_monthly["Series"] = "56-day trailing forecast"
    rolling_monthly["month"] = pd.to_datetime(rolling_monthly["month"] + "-01")
    rolling_trace = rolling_monthly.rename(columns={"rolling_prediction": "Engagement rate"})[
        ["month", "Series", "Engagement rate"]
    ]
    monthly_long = pd.concat([monthly_long, rolling_trace], ignore_index=True)

    figure = px.line(
        monthly_long,
        x="month",
        y="Engagement rate",
        color="Series",
        line_dash="Series",
        symbol="Series",
        markers=True,
        title="Monthly actual and predicted engagement rate on the future holdout",
        color_discrete_map={
            "Actual": "#FF4F9A",
            "Pre-publication model": "#43D9C3",
            "56-day trailing forecast": "#FFC857",
        },
        line_dash_map={
            "Actual": "solid",
            "Pre-publication model": "dash",
            "56-day trailing forecast": "dot",
        },
        symbol_map={
            "Actual": "circle",
            "Pre-publication model": "diamond",
            "56-day trailing forecast": "square",
        },
    )
    line_min = float(monthly_long["Engagement rate"].min())
    line_max = float(monthly_long["Engagement rate"].max())
    line_padding = max((line_max - line_min) * 0.3, 0.0005)
    figure.update_yaxes(
        title="Mean engagement rate",
        tickformat=".2%",
        range=[line_min - line_padding, line_max + line_padding],
        gridcolor="rgba(190, 190, 210, 0.16)",
    )
    figure.update_xaxes(
        title="Holdout month",
        dtick="M1",
        tickformat="%b %Y",
        gridcolor="rgba(190, 190, 210, 0.10)",
    )
    figure.update_traces(line={"width": 3}, marker={"size": 9})
    figure.update_layout(
        template="plotly_dark",
        height=390,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center", "title": ""},
        margin={"t": 90, "r": 30, "b": 55, "l": 65},
    )
    st.plotly_chart(figure, width="stretch")
    st.caption(
        "The gold trace is a rolling one-step forecast from the previous 56 observed daily rates. "
        f"Its holdout MAE is {rolling_mae:.2%}, versus {median_baseline_mae:.2%} for the development-period median; "
        "it adds a data-driven trend line, but does not outperform the flat baseline on this holdout."
    )
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

conditional_report_path = ROOT / "reports" / "conditional_engagement_volume.json"
conditional_prediction_path = ROOT / "reports" / "conditional_engagement_volume_predictions.csv"
if conditional_report_path.is_file() and conditional_prediction_path.is_file():
    with st.container(border=True):
        st.subheader("Exploratory analysis: engagement volume given observed exposure")
        st.caption(
            "This supplemental estimate uses the dataset's observed reach and impressions to predict likes, comments, shares, and saves. "
            "It was added after reviewing this dataset, so treat its measured performance as exploratory. It does not replace the primary pre-publication engagement-rate analysis above."
        )
        try:
            conditional_report = json.loads(conditional_report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            st.error(f"The conditional engagement-volume report could not be read: {error}")
        else:
            conditional_holdout = conditional_report["holdout"]
            volume_baseline = conditional_holdout["median_baseline"]
            volume_model = conditional_holdout["ridge"]
            volume_cols = st.columns(3)
            volume_cols[0].metric("Holdout R²", f"{volume_model['r2']:.3f}")
            volume_cols[1].metric(
                "Ridge MAE", f"{volume_model['mae']:,.0f} engagements",
                f"{conditional_holdout['relative_mae_reduction']:.1%} lower than median baseline",
            )
            volume_cols[2].metric("Median baseline MAE", f"{volume_baseline['mae']:,.0f} engagements")
            st.caption(
                f"Future-date holdout: {conditional_report['split']['holdout_start']} to "
                f"{conditional_report['split']['holdout_end']} · "
                f"{conditional_report['split']['holdout_records']:,} full-dataset records · "
                f"features: reach, impressions, hashtag count, post type, and campaign type."
            )
            interval = conditional_holdout["daily_bootstrap_mae_difference_interval"]
            if interval["lower_95"] is not None:
                st.success(
                    f"Ridge reduced holdout MAE by {abs(conditional_holdout['mae_difference_ridge_minus_baseline']):,.0f} engagements on average. "
                    f"The paired daily 95% interval for the MAE change is "
                    f"[{interval['lower_95']:,.0f}, {interval['upper_95']:,.0f}] engagements "
                    "(negative favors Ridge)."
                )

            conditional_predictions = pd.read_csv(conditional_prediction_path)
            conditional_predictions["actual_decile"] = pd.qcut(
                conditional_predictions["actual_engagements"],
                q=10,
                labels=False,
                duplicates="drop",
            )
            calibration = conditional_predictions.groupby("actual_decile", observed=True).agg(
                records=("actual_engagements", "size"),
                actual_mean=("actual_engagements", "mean"),
                predicted_mean=("predicted_engagements", "mean"),
            ).reset_index()
            calibration_long = pd.concat(
                [
                    calibration.assign(Series="Actual (1:1)", value=calibration["actual_mean"]),
                    calibration.assign(Series="Predicted", value=calibration["predicted_mean"]),
                ],
                ignore_index=True,
            )
            calibration_chart = px.line(
                calibration_long,
                x="actual_mean",
                y="value",
                color="Series",
                markers=True,
                line_dash="Series",
                symbol="Series",
                hover_data={"records": True, "actual_decile": True, "actual_mean": ":,.0f", "value": ":,.0f"},
                title="Holdout calibration by actual engagement decile",
                color_discrete_map={"Actual (1:1)": "#FF4F9A", "Predicted": "#43D9C3"},
                line_dash_map={"Actual (1:1)": "solid", "Predicted": "dash"},
                symbol_map={"Actual (1:1)": "circle", "Predicted": "diamond"},
            )
            axis_max = float(
                max(calibration["actual_mean"].max(), calibration["predicted_mean"].max()) * 1.05
            )
            calibration_chart.update_layout(
                template="plotly_dark",
                height=440,
                hovermode="x unified",
                legend={"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center", "title": ""},
                margin={"t": 85, "r": 25, "b": 60, "l": 70},
            )
            calibration_chart.update_traces(line={"width": 3}, marker={"size": 9})
            calibration_chart.update_xaxes(
                title="Actual engagements (decile mean)", range=[0, axis_max],
                gridcolor="rgba(190, 190, 210, 0.16)",
            )
            calibration_chart.update_yaxes(
                title="Engagements per post", range=[0, axis_max],
                gridcolor="rgba(190, 190, 210, 0.16)",
            )
            st.plotly_chart(calibration_chart, width="stretch")
            st.caption(
                "Each point summarizes one tenth of holdout posts, ordered by actual engagement count. "
                "The Actual line is the 1:1 reference; a Predicted line below it indicates underprediction."
            )

            subgroup_cols = st.columns(2)
            for column, dimension, title in [
                (subgroup_cols[0], "post_type", "Holdout by post type"),
                (subgroup_cols[1], "campaign_type", "Holdout by campaign"),
            ]:
                with column:
                    st.markdown(f"#### {title}")
                    subgroup = pd.DataFrame(conditional_report["subgroup_validation"][dimension])
                    st.dataframe(
                        subgroup.rename(
                            columns={
                                dimension: "Group",
                                "records": "Posts",
                                "actual_mean": "Actual mean",
                                "prediction_mean": "Predicted mean",
                                "mae": "MAE",
                                "mean_error": "Mean error",
                            }
                        ).style.format(
                            {
                                "Actual mean": "{:,.0f}",
                                "Predicted mean": "{:,.0f}",
                                "MAE": "{:,.0f}",
                                "Mean error": "{:+,.0f}",
                            }
                        ),
                        width="stretch",
                        hide_index=True,
                    )

            cv_rows = []
            for fold_result in conditional_report["split"]["cv_folds"]:
                cv_rows.append(
                    {
                        "Model": fold_result["model"],
                        "Mean 4-fold temporal CV MAE": fold_result["mean_mae"],
                        "Fold MAE SD": fold_result["std_mae"],
                    }
                )
            st.dataframe(
                pd.DataFrame(cv_rows).style.format(
                    {"Mean 4-fold temporal CV MAE": "{:,.0f}", "Fold MAE SD": "{:,.1f}"}
                ),
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "The engagement-rate model above remains the primary pre-publication result. "
                "This exploratory estimate answers a separate question using observed exposure; the association does not show that a format or campaign caused the engagement."
            )
            if conditional_prediction_path.is_file():
                st.download_button(
                    "Download conditional engagement-volume predictions",
                    conditional_prediction_path.read_bytes(),
                    file_name=conditional_prediction_path.name,
                    mime="text/csv",
                    key="download_conditional_engagement_predictions",
                    width="stretch",
                )

st.subheader("How to use these predictions")
st.markdown(
    """
    - The pre-publication engagement-rate model has little separation between posts; use its median estimate as a reference, not as a ranking or budget-allocation tool.
    - The engagement-volume model is more informative after reach and impressions are observed. Use its predictions as conditional estimates of total likes, comments, shares, and saves.
    - The model comparison uses a later-date holdout and temporal cross-validation. Its intervals describe performance across resampled dates; they do not measure causal impact.
    - Post-type and campaign results describe this dataset's observed patterns. They do not isolate what would happen if a brand changed its posting strategy.
    """
)
st.caption(
    f"Generated {report['generated_at_utc']} · runtime {report['runtime_seconds']:.1f}s · "
    f"model artifact SHA-256 input: {report['input']['sha256']}"
)
