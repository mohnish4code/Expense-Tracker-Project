from datetime import date, datetime

import pandas as pd
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    category: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    payment_method: Mapped[str] = mapped_column(String(30), default="Cash")
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(String(200), default="")


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "category", "year", "month"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float)


def expenses_frame(db, user_id):
    rows = db.execute(select(Expense).where(Expense.user_id == user_id)).scalars().all()
    df_expenses = pd.DataFrame(
        [
            {
                "id": e.id,
                "Date": e.date,
                "Description": e.description,
                "Category": e.category,
                "Amount": e.amount,
                "Payment Method": e.payment_method,
                "Is Recurring": e.is_recurring,
            }
            for e in rows
        ],
        columns=["id", "Date", "Description", "Category", "Amount", "Payment Method", "Is Recurring"],
    )
    df_expenses["Date"] = pd.to_datetime(df_expenses["Date"])
    df_expenses["Amount"] = df_expenses["Amount"].astype(float)
    df_expenses["Is Recurring"] = df_expenses["Is Recurring"].astype(bool)
    return df_expenses


def budgets_frame(db, user_id):
    rows = db.execute(select(Budget).where(Budget.user_id == user_id)).scalars().all()
    return pd.DataFrame(
        [{"Category": b.category, "Year": b.year, "Month": b.month, "Budget": b.amount} for b in rows],
        columns=["Category", "Year", "Month", "Budget"],
    ).astype({"Year": int, "Month": int, "Budget": float})
