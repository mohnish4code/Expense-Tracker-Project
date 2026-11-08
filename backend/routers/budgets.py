from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select

from backend.auth import current_user
from backend.db import get_db
from backend.models import Budget
from backend.schemas import BudgetIn, BudgetOut

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def set_budget(body: BudgetIn, response: Response, user=Depends(current_user), db=Depends(get_db)):
    """Creates the budget for a category and month, or updates it if one exists."""
    budget = db.execute(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.category == body.category,
            Budget.year == body.year,
            Budget.month == body.month,
        )
    ).scalar_one_or_none()
    if budget is None:
        budget = Budget(user_id=user.id, **body.model_dump())
        db.add(budget)
    else:
        budget.amount = body.amount
        response.status_code = status.HTTP_200_OK
    db.commit()
    return budget


@router.get("", response_model=list[BudgetOut])
def list_budgets(
    year: int | None = Query(None, ge=2000, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    user=Depends(current_user),
    db=Depends(get_db),
):
    query = select(Budget).where(Budget.user_id == user.id)
    if year is not None:
        query = query.where(Budget.year == year)
    if month is not None:
        query = query.where(Budget.month == month)
    return db.execute(query.order_by(Budget.year, Budget.month, Budget.category)).scalars().all()
