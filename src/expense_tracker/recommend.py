import math

import pandas as pd

from expense_tracker.data import load_expenses, monthly_spend

RECENT_MONTHS = 6
QUANTILE = 0.8
ROUND_TO = 100


def recommend_budgets(df_expenses, months=RECENT_MONTHS, quantile=QUANTILE):
    if df_expenses.empty:
        return []

    latest = df_expenses["Date"].max().to_period("M")
    first = df_expenses["Date"].min().to_period("M")
    months = min(months, (latest - first).n + 1)
    periods = pd.period_range(end=latest, periods=months, freq="M")
    spend = monthly_spend(df_expenses)
    spend["Period"] = pd.PeriodIndex.from_fields(year=spend["Year"], month=spend["Month"], freq="M")
    spend = spend[spend["Period"].isin(periods)]

    # months with no spend in a category count as zero
    table = spend.pivot_table(index="Period", columns="Category", values="Amount", aggfunc="sum")
    table = table.reindex(periods).fillna(0.0)

    recommendations = []
    for category in table.columns:
        values = table[category]
        recommended = math.ceil(values.quantile(quantile) / ROUND_TO) * ROUND_TO
        recommendations.append(
            {
                "category": category,
                "recommended": recommended,
                "median": round(float(values.median()), 2),
                "months": months,
                "reason": f"{int(quantile * 100)}th percentile of the last {months} month{'s' if months > 1 else ''} "
                f"(median {values.median():,.0f}, highest {values.max():,.0f})",
            }
        )
    return sorted(recommendations, key=lambda r: r["recommended"], reverse=True)


if __name__ == "__main__":
    for row in recommend_budgets(load_expenses()):
        print(f"{row['category']:<25} {row['recommended']:>8,}  {row['reason']}")
