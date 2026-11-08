import numpy as np
import pandas as pd

from expense_tracker.data import monthly_spend

CUTOFF_DAYS = (7, 14, 21)
KEYS = ["Category", "Year", "Month"]

OVERSPEND_FEATURES = [
    "Category",
    "Budget",
    "Spend To Date",
    "Spend Ratio",
    "Days Elapsed",
    "Days Remaining",
    "Daily Run Rate",
    "Prev Month Ratio",
]


def cutoff_features(df_expenses, budgets, cutoff_day):
    """One row per budget row, using only expenses dated on or before cutoff_day of that month."""
    df = df_expenses.assign(
        Year=df_expenses["Date"].dt.year, Month=df_expenses["Date"].dt.month, Day=df_expenses["Date"].dt.day
    )
    to_date = df[df["Day"] <= cutoff_day].groupby(KEYS)["Amount"].sum().rename("Spend To Date").reset_index()

    features = budgets[KEYS + ["Budget"]].merge(to_date, on=KEYS, how="left")
    features["Spend To Date"] = features["Spend To Date"].fillna(0.0)

    days_in_month = pd.to_datetime(features[["Year", "Month"]].assign(Day=1)).dt.days_in_month
    features["Days Elapsed"] = np.minimum(cutoff_day, days_in_month)
    features["Days Remaining"] = days_in_month - features["Days Elapsed"]
    features["Spend Ratio"] = features["Spend To Date"] / features["Budget"]
    features["Daily Run Rate"] = features["Spend To Date"] / features["Days Elapsed"]
    features["Projected Spend"] = features["Daily Run Rate"] * days_in_month

    # previous month is fully in the past at any cutoff, so its ratio is not leakage
    prev = budgets[KEYS + ["Budget"]].merge(monthly_spend(df_expenses), on=KEYS, how="left")
    prev["Prev Month Ratio"] = prev["Amount"].fillna(0.0) / prev["Budget"]
    next_month = prev["Month"] % 12 + 1
    prev["Year"] = prev["Year"] + (prev["Month"] == 12)
    prev["Month"] = next_month
    features = features.merge(prev[KEYS + ["Prev Month Ratio"]], on=KEYS, how="left")
    return features


def overspend_dataset(df_expenses, budgets, cutoff_days=CUTOFF_DAYS):
    full = budgets[KEYS + ["Budget"]].merge(monthly_spend(df_expenses), on=KEYS, how="left")
    full["Overspent"] = (full["Amount"].fillna(0.0) > full["Budget"]).astype(int)

    frames = []
    for day in cutoff_days:
        features = cutoff_features(df_expenses, budgets, day)
        features["Cutoff Day"] = day
        frames.append(features.merge(full[KEYS + ["Overspent"]], on=KEYS))
    return pd.concat(frames, ignore_index=True)
