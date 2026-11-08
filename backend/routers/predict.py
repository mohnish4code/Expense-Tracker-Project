import calendar
from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, Path, Query, Request

from backend.auth import current_user
from backend.db import get_db
from backend.models import budgets_frame, expenses_frame
from backend.schemas import AnomalyIn, AnomalyOut
from expense_tracker.predict import flag_anomalies, overspend_risk

router = APIRouter(prefix="/api/predict", tags=["predictions"])

# past months are replayed from mid-month so the forecast is still a forecast
PAST_MONTH_DAY = 14


def risk_level(risk):
    if risk >= 0.7:
        return "high"
    if risk >= 0.4:
        return "medium"
    return "low"


@router.post("/anomaly", response_model=AnomalyOut)
def predict_anomaly(body: AnomalyIn, request: Request, user=Depends(current_user)):
    df = pd.DataFrame(
        [
            {
                "Category": body.category,
                "Amount": body.amount,
                "Payment Method": body.payment_method,
                "Is Recurring": body.is_recurring,
            }
        ]
    )
    row = flag_anomalies(request.app.state.models["anomaly"], df).iloc[0]
    return {"anomaly": bool(row["Anomaly"]), "reason": row["Reason"]}


@router.get("/overspend/{year}/{month}")
def predict_overspend(
    request: Request,
    year: int = Path(ge=2000, le=2100),
    month: int = Path(ge=1, le=12),
    day: int | None = Query(None, ge=1, le=31, description="Day of the month to predict from"),
    user=Depends(current_user),
    db=Depends(get_db),
):
    today = date.today()
    if day is None:
        day = today.day if (year, month) == (today.year, today.month) else PAST_MONTH_DAY
    day = min(day, calendar.monthrange(year, month)[1])

    features = overspend_risk(
        request.app.state.models["overspend"], expenses_frame(db, user.id), budgets_frame(db, user.id), year, month, day
    )
    categories = [
        {
            "category": row["Category"],
            "budget": round(float(row["Budget"]), 2),
            "spent_to_date": round(float(row["Spend To Date"]), 2),
            "risk": round(float(row["Risk"]), 3),
            "level": risk_level(row["Risk"]),
        }
        for _, row in features.sort_values("Risk", ascending=False).iterrows()
    ]
    return {"year": year, "month": month, "as_of_day": day, "categories": categories}
