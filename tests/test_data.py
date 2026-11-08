import pandas as pd

from expense_tracker.config import BUDGET_CSV, TND_TO_INR, TRANSACTIONS_CSV
from expense_tracker.data import load_budgets, load_expenses
from expense_tracker.features import overspend_dataset


def test_budgets_use_same_rate_as_transactions():
    raw_budget = pd.read_csv(BUDGET_CSV)
    budgets = load_budgets()
    food_jan = budgets[(budgets["Category"] == "Food & Groceries") & (budgets["Month"] == 1)]["Budget"].item()
    assert food_jan == raw_budget.loc[raw_budget["Category"] == "Food & Groceries", "January 2024"].item() * TND_TO_INR


def test_expenses_are_positive_inr():
    raw = pd.read_csv(TRANSACTIONS_CSV)
    raw_expenses = raw[raw["Type"] == "Expense"]
    df_expenses = load_expenses()
    assert len(df_expenses) == len(raw_expenses)
    assert (df_expenses["Amount"] > 0).all()
    expected = raw_expenses["Amount (TND)"].abs().sum() * TND_TO_INR
    assert abs(df_expenses["Amount"].sum() - expected) < 1


def test_overspend_label_has_both_classes():
    dataset = overspend_dataset(load_expenses(), load_budgets())
    counts = dataset["Overspent"].value_counts()
    assert set(counts.index) == {0, 1}
    assert counts.min() / counts.sum() > 0.3
