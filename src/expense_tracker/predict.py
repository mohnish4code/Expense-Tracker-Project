import json
from datetime import UTC, datetime

import joblib
import numpy as np
import pandas as pd
import sklearn

from expense_tracker.config import ANOMALY_MODEL, MODELS_DIR, OVERSPEND_MODEL, RESULTS_DIR
from expense_tracker.features import ANOMALY_FEATURES, OVERSPEND_FEATURES, cutoff_features

RECURRING_Z_LIMIT = 3.5


def save_model(model, name, features, metrics, models_dir=MODELS_DIR, results_dir=RESULTS_DIR):
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, models_dir / f"{name}.joblib", compress=3)
    meta = {
        "name": name,
        "sklearn_version": sklearn.__version__,
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "features": features,
        "metrics": metrics,
    }
    (models_dir / f"{name}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    results_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = results_dir / "metrics.json"
    all_metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    all_metrics[name] = metrics
    metrics_path.write_text(json.dumps(all_metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def models_exist(models_dir=MODELS_DIR):
    return all((models_dir / f"{name}.joblib").exists() for name in (ANOMALY_MODEL, OVERSPEND_MODEL))


def load_models(models_dir=MODELS_DIR):
    return {
        "anomaly": joblib.load(models_dir / f"{ANOMALY_MODEL}.joblib"),
        "overspend": joblib.load(models_dir / f"{OVERSPEND_MODEL}.joblib"),
    }


def flag_anomalies(anomaly_model, df):
    """Returns a copy of df with Anomaly (bool) and Reason columns.

    Recurring or fixed-amount payments are checked against their usual amount; everything
    else goes through the Isolation Forest pipeline.
    """
    df = df.copy()
    stats = anomaly_model["recurring_stats"]
    fixed = df["Is Recurring"].astype(bool) | df["Category"].isin(anomaly_model["recurring_categories"])

    df["Anomaly"] = False
    df["Reason"] = ""

    if fixed.any():
        rows = df[fixed]
        median = rows["Category"].map(stats["median"])
        scale = rows["Category"].map(stats["scale"])
        z = (rows["Amount"] - median) / scale
        known = median.notna()
        df.loc[rows.index, "Anomaly"] = known & (z.abs() > RECURRING_Z_LIMIT)
        df.loc[rows.index[known], "Reason"] = [
            f"usual recurring amount is {m:,.0f}" for m in median[known]
        ]

    variable = ~fixed
    if variable.any():
        pipeline = anomaly_model["pipeline"]
        rows = df.loc[variable, ANOMALY_FEATURES]
        df.loc[variable, "Anomaly"] = pipeline.predict(rows) == -1
        medians = rows["Category"].map(pipeline.named_steps["preprocess"].named_transformers_["amount"].stats_["median"])
        df.loc[variable, "Reason"] = [
            f"{a / m:.1f}x the usual {c} amount" if pd.notna(m) else "unfamiliar category"
            for a, m, c in zip(rows["Amount"], medians, rows["Category"], strict=True)
        ]

    df["Anomaly"] = df["Anomaly"].astype(bool)
    return df


def overspend_risk(overspend_model, df_expenses, budgets, year, month, as_of_day):
    month_budgets = budgets[(budgets["Year"] == year) & (budgets["Month"] == month)]
    if month_budgets.empty:
        return month_budgets.assign(Risk=np.nan)
    features = cutoff_features(df_expenses, budgets, as_of_day)
    features = features[(features["Year"] == year) & (features["Month"] == month)].copy()
    features["Risk"] = overspend_model.predict_proba(features[OVERSPEND_FEATURES])[:, 1]
    return features
