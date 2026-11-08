import pandas as pd
from fastapi import APIRouter, Depends, Path, Request

from backend.auth import current_user
from backend.db import get_db
from backend.models import budgets_frame, expenses_frame
from expense_tracker.predict import flag_anomalies
from expense_tracker.recommend import recommend_budgets

router = APIRouter(prefix="/api", tags=["insights"])


def money(value):
    return round(float(value), 2)


def usage(spent, budget):
    return round(float(spent / budget * 100), 1) if budget else None


def in_month(df, year, month):
    return df[(df["Date"].dt.year == year) & (df["Date"].dt.month == month)]


@router.get("/months")
def months(user=Depends(current_user), db=Depends(get_db)):
    """Months that have expenses or budgets, newest first."""
    df_expenses = expenses_frame(db, user.id)
    periods = set(zip(df_expenses["Date"].dt.year, df_expenses["Date"].dt.month, strict=True))
    budgets = budgets_frame(db, user.id)
    periods |= set(zip(budgets["Year"], budgets["Month"], strict=True))
    return [{"year": int(y), "month": int(m)} for y, m in sorted(periods, reverse=True)]


@router.get("/insights/{year}/{month}")
def insights(
    request: Request,
    year: int = Path(ge=2000, le=2100),
    month: int = Path(ge=1, le=12),
    user=Depends(current_user),
    db=Depends(get_db),
):
    df_expenses = expenses_frame(db, user.id)
    budgets = budgets_frame(db, user.id)

    month_expenses = in_month(df_expenses, year, month)
    month_budgets = budgets[(budgets["Year"] == year) & (budgets["Month"] == month)]
    spent_by_category = month_expenses.groupby("Category")["Amount"].sum()
    budget_by_category = month_budgets.groupby("Category")["Budget"].sum()

    categories = []
    for category in sorted(set(spent_by_category.index) | set(budget_by_category.index)):
        spent = spent_by_category.get(category, 0.0)
        budget = budget_by_category.get(category, 0.0)
        categories.append(
            {
                "category": category,
                "budget": money(budget),
                "spent": money(spent),
                "remaining": money(budget - spent),
                "usage_pct": usage(spent, budget),
            }
        )

    total_spent = spent_by_category.sum()
    total_budget = budget_by_category.sum()

    trend_spent = df_expenses.groupby([df_expenses["Date"].dt.year, df_expenses["Date"].dt.month])["Amount"].sum()
    trend_budget = budgets.groupby(["Year", "Month"])["Budget"].sum()
    trend = pd.concat([trend_spent.rename("spent"), trend_budget.rename("budget")], axis=1).fillna(0.0).sort_index()

    anomalies = []
    if not month_expenses.empty:
        flagged = flag_anomalies(request.app.state.models["anomaly"], month_expenses)
        flagged = flagged[flagged["Anomaly"]].sort_values("Amount", ascending=False)
        anomalies = [
            {
                "id": int(row["id"]),
                "date": row["Date"].date().isoformat(),
                "category": row["Category"],
                "amount": money(row["Amount"]),
                "description": row["Description"],
                "reason": row["Reason"],
            }
            for _, row in flagged.iterrows()
        ]

    return {
        "year": year,
        "month": month,
        "budget": money(total_budget),
        "spent": money(total_spent),
        "remaining": money(total_budget - total_spent),
        "usage_pct": usage(total_spent, total_budget),
        "categories": categories,
        "anomalies": anomalies,
        "trend": [
            {"year": int(y), "month": int(m), "spent": money(row["spent"]), "budget": money(row["budget"])}
            for (y, m), row in trend.iterrows()
        ],
    }


@router.get("/recommendations")
def recommendations(user=Depends(current_user), db=Depends(get_db)):
    return recommend_budgets(expenses_frame(db, user.id))
