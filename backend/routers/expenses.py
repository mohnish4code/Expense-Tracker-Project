from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from backend.auth import current_user
from backend.db import get_db
from backend.models import Expense
from backend.schemas import ExpenseIn, ExpenseOut

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


def month_range(year, month=None):
    if month is None:
        return date(year, 1, 1), date(year + 1, 1, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return date(year, month, 1), end


def owned_expense(db, user, expense_id):
    expense = db.get(Expense, expense_id)
    if expense is None or expense.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")
    return expense


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(body: ExpenseIn, user=Depends(current_user), db=Depends(get_db)):
    expense = Expense(user_id=user.id, **body.model_dump())
    db.add(expense)
    db.commit()
    return expense


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    year: int | None = Query(None, ge=2000, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    category: str | None = None,
    user=Depends(current_user),
    db=Depends(get_db),
):
    query = select(Expense).where(Expense.user_id == user.id)
    if year is not None:
        start, end = month_range(year, month)
        query = query.where(Expense.date >= start, Expense.date < end)
    if category:
        query = query.where(Expense.category == category)
    return db.execute(query.order_by(Expense.date.desc(), Expense.id.desc())).scalars().all()


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, body: ExpenseIn, user=Depends(current_user), db=Depends(get_db)):
    expense = owned_expense(db, user, expense_id)
    for field, value in body.model_dump().items():
        setattr(expense, field, value)
    db.commit()
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, user=Depends(current_user), db=Depends(get_db)):
    db.delete(owned_expense(db, user, expense_id))
    db.commit()
