import pandas as pd

from expense_tracker.recommend import recommend_budgets


def test_recommendation_is_rounded_percentile(expenses_df):
    recs = {r["category"]: r for r in recommend_budgets(expenses_df)}

    # Food monthly totals: Jan 9,000, Feb 12,500 -> 80th percentile 11,800
    food = recs["Food & Groceries"]
    assert food["recommended"] == 11_800
    assert food["recommended"] % 100 == 0
    assert food["months"] == 2
    assert "80th percentile" in food["reason"]

    # Rent has no January payment, so January counts as zero
    assert recs["Rent"]["recommended"] == 17_400


def test_uses_only_recent_months():
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2024-01-15", periods=12, freq="MS") + pd.Timedelta(days=14),
            "Category": "Transport",
            "Amount": [100_000.0] * 6 + [1_000.0] * 6,
        }
    )
    rec = recommend_budgets(df)[0]
    assert rec["months"] == 6
    assert rec["recommended"] == 1_000


def test_empty_history():
    assert recommend_budgets(pd.DataFrame(columns=["Date", "Category", "Amount"])) == []
