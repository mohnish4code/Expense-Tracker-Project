import pandas as pd

from expense_tracker.features import cutoff_features, overspend_dataset


def feb_food(features):
    return features[(features["Category"] == "Food & Groceries") & (features["Month"] == 2)].iloc[0]


def test_cutoff_features_ignore_later_expenses(expenses_df, budgets_df):
    before = feb_food(cutoff_features(expenses_df, budgets_df, 14))

    late_spend = pd.DataFrame({"Date": pd.to_datetime(["2024-02-15", "2024-02-28"]), "Category": "Food & Groceries"})
    late_spend["Amount"] = [50_000.0, 70_000.0]
    after = feb_food(cutoff_features(pd.concat([expenses_df, late_spend]), budgets_df, 14))

    for column in ["Spend To Date", "Spend Ratio", "Daily Run Rate", "Days Elapsed", "Days Remaining"]:
        assert before[column] == after[column]
    assert before["Spend To Date"] == 3500


def test_cutoff_feature_values(expenses_df, budgets_df):
    row = feb_food(cutoff_features(expenses_df, budgets_df, 7))
    assert row["Spend To Date"] == 2000
    assert row["Days Elapsed"] == 7
    assert row["Days Remaining"] == 29 - 7
    assert row["Spend Ratio"] == 2000 / 8000
    assert row["Prev Month Ratio"] == 9000 / 8000


def test_label_uses_full_month(expenses_df, budgets_df):
    dataset = overspend_dataset(expenses_df, budgets_df)
    feb = dataset[(dataset["Category"] == "Food & Groceries") & (dataset["Month"] == 2)]
    # Feb total is 12,500 against 8,000, so every cutoff row is labelled overspent
    assert feb["Overspent"].tolist() == [1, 1, 1]
    rent = dataset[dataset["Category"] == "Rent"]
    assert rent["Overspent"].eq(0).all()
