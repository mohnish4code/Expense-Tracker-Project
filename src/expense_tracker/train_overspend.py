import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from expense_tracker.config import MODELS_DIR, OVERSPEND_MODEL, SEED
from expense_tracker.data import load_budgets, load_expenses
from expense_tracker.features import OVERSPEND_FEATURES, overspend_dataset

TEST_MONTHS = 3


def build_pipeline():
    preprocess = ColumnTransformer(
        [("category", OneHotEncoder(handle_unknown="ignore"), ["Category"])],
        remainder="passthrough",
    )
    model = RandomForestClassifier(n_estimators=300, min_samples_leaf=3, class_weight="balanced", random_state=SEED)
    return Pipeline([("preprocess", preprocess), ("model", model)])


def time_split(dataset, test_months=TEST_MONTHS):
    period = dataset["Year"] * 12 + dataset["Month"]
    cutoff = sorted(period.unique())[-test_months]
    return dataset[period < cutoff].copy(), dataset[period >= cutoff].copy()


def scores(y_true, y_pred, y_score):
    return {
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 3),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 3),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 3),
        "roc_auc": round(float(roc_auc_score(y_true, y_score)), 3),
    }


def train(df_expenses=None, budgets=None):
    df_expenses = load_expenses() if df_expenses is None else df_expenses
    budgets = load_budgets() if budgets is None else budgets

    dataset = overspend_dataset(df_expenses, budgets)
    train_df, test_df = time_split(dataset)

    pipeline = build_pipeline()
    pipeline.fit(train_df[OVERSPEND_FEATURES], train_df["Overspent"])
    proba = pipeline.predict_proba(test_df[OVERSPEND_FEATURES])[:, 1]

    # naive baseline: project the current daily run-rate to the end of the month
    baseline_score = test_df["Projected Spend"] / test_df["Budget"]

    metrics = {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_positive_rate": round(float(train_df["Overspent"].mean()), 3),
        "test_positive_rate": round(float(test_df["Overspent"].mean()), 3),
        "model": scores(test_df["Overspent"], (proba >= 0.5).astype(int), proba),
        "baseline_run_rate": scores(test_df["Overspent"], (baseline_score > 1).astype(int), baseline_score),
    }

    # refit on every month so the served model has seen the latest data
    pipeline.fit(dataset[OVERSPEND_FEATURES], dataset["Overspent"])
    return pipeline, metrics


def main(models_dir=MODELS_DIR):
    pipeline, metrics = train()
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, models_dir / f"{OVERSPEND_MODEL}.joblib")
    print(metrics)
    return metrics


if __name__ == "__main__":
    main()
