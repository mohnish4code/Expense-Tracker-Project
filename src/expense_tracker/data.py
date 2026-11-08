import pandas as pd

from expense_tracker.config import BUDGET_CSV, TND_TO_INR, TRANSACTIONS_CSV


def load_transactions(path=TRANSACTIONS_CSV):
    df_transactions = pd.read_csv(path, encoding="utf-8")
    df_transactions["Date"] = pd.to_datetime(df_transactions["Date"])
    df_transactions["Amount"] = df_transactions["Amount (TND)"] * TND_TO_INR
    return df_transactions.drop(columns=["Amount (TND)", "Notes"])


def load_expenses(path=TRANSACTIONS_CSV):
    df_transactions = load_transactions(path)
    df_expenses = df_transactions[df_transactions["Type"] == "Expense"].copy()
    df_expenses["Amount"] = df_expenses["Amount"].abs().round(2)
    df_expenses["Is Recurring"] = df_expenses["Is Recurring"].eq("Yes")
    return df_expenses[["Date", "Description", "Category", "Amount", "Payment Method", "Is Recurring"]].reset_index(
        drop=True
    )


def load_budgets(path=BUDGET_CSV):
    df_budget = pd.read_csv(path, encoding="utf-8")
    budget_long = df_budget.melt(id_vars="Category", var_name="Month_Year", value_name="Budget")
    month_start = pd.to_datetime(budget_long["Month_Year"], format="%B %Y")
    budget_long["Year"] = month_start.dt.year
    budget_long["Month"] = month_start.dt.month
    # budget.csv is in TND like the transactions, so it needs the same conversion
    budget_long["Budget"] = budget_long["Budget"] * TND_TO_INR
    return budget_long[["Category", "Year", "Month", "Budget"]]


def monthly_spend(df_expenses):
    return (
        df_expenses.assign(Year=df_expenses["Date"].dt.year, Month=df_expenses["Date"].dt.month)
        .groupby(["Category", "Year", "Month"])["Amount"]
        .sum()
        .reset_index()
    )


if __name__ == "__main__":
    merged_df = load_budgets().merge(monthly_spend(load_expenses()), on=["Category", "Year", "Month"], how="left")
    merged_df["Amount"] = merged_df["Amount"].fillna(0)
    merged_df["Overspent"] = (merged_df["Amount"] > merged_df["Budget"]).astype(int)
    print(merged_df["Overspent"].value_counts())
