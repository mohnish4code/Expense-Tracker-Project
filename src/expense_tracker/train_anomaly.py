import json

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from expense_tracker.config import ANOMALY_MODEL, MODELS_DIR, RESULTS_DIR, SEED
from expense_tracker.data import load_expenses
from expense_tracker.features import ANOMALY_FEATURES, CategoryAmountFeatures, robust_stats
from expense_tracker.predict import flag_anomalies, save_model

TEST_MONTHS = 3
RECURRING_SHARE = 0.8
CONTAMINATION = 0.03
INJECTED_SHARE = 0.1


def build_pipeline():
    preprocess = ColumnTransformer(
        [
            ("amount", CategoryAmountFeatures(), ["Category", "Amount"]),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Category", "Payment Method"]),
        ]
    )
    model = IsolationForest(n_estimators=300, contamination=CONTAMINATION, random_state=SEED)
    return Pipeline([("preprocess", preprocess), ("model", model)])


def fit_model(df_expenses):
    recurring_share = df_expenses.groupby("Category")["Is Recurring"].mean()
    recurring_categories = sorted(recurring_share[recurring_share >= RECURRING_SHARE].index)
    fixed = df_expenses["Is Recurring"] | df_expenses["Category"].isin(recurring_categories)

    pipeline = build_pipeline()
    pipeline.fit(df_expenses.loc[~fixed, ANOMALY_FEATURES])
    return {
        "pipeline": pipeline,
        "recurring_categories": recurring_categories,
        "recurring_stats": robust_stats(df_expenses[fixed]),
    }


def inject_anomalies(df, rng):
    """Labels real rows 0 and adds copies of random rows with the amount scaled 5-15x, labelled 1."""
    df = df.assign(Label=0)
    injected = df.sample(frac=INJECTED_SHARE, random_state=SEED).copy()
    injected["Amount"] = injected["Amount"] * rng.uniform(5, 15, len(injected))
    injected["Label"] = 1
    return pd.concat([df, injected], ignore_index=True)


def zscore_rule(train_df, test_df, limit=3.0):
    stats = train_df.groupby("Category")["Amount"].agg(["mean", "std"])
    mean = test_df["Category"].map(stats["mean"])
    std = test_df["Category"].map(stats["std"])
    return ((test_df["Amount"] - mean) / std > limit).fillna(False).astype(int)


def scores(y_true, y_pred):
    return {
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 3),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 3),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 3),
    }


def train(df_expenses=None):
    df_expenses = load_expenses() if df_expenses is None else df_expenses
    period = df_expenses["Date"].dt.year * 12 + df_expenses["Date"].dt.month
    split = sorted(period.unique())[-TEST_MONTHS]
    train_df, test_df = df_expenses[period < split], df_expenses[period >= split]

    model = fit_model(train_df)
    variable = ~(test_df["Is Recurring"] | test_df["Category"].isin(model["recurring_categories"]))
    test_df = inject_anomalies(test_df[variable], np.random.default_rng(SEED))
    flagged = flag_anomalies(model, test_df)["Anomaly"].astype(int)

    metrics = {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "injected_anomalies": int(test_df["Label"].sum()),
        "model": scores(test_df["Label"], flagged),
        "baseline_category_zscore": scores(test_df["Label"], zscore_rule(train_df, test_df)),
        "recurring_categories": model["recurring_categories"],
    }
    return fit_model(df_expenses), metrics


def main(models_dir=MODELS_DIR, results_dir=RESULTS_DIR):
    model, metrics = train()
    features = ANOMALY_FEATURES + ["Is Recurring (routes to recurring rule)"]
    save_model(model, ANOMALY_MODEL, features, metrics, models_dir, results_dir)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    main()
