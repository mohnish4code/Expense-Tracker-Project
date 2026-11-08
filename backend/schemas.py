from datetime import date
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from expense_tracker.config import CATEGORIES, PAYMENT_METHODS


def check_category(value):
    if value not in CATEGORIES:
        raise ValueError(f"unknown category, expected one of: {', '.join(CATEGORIES)}")
    return value


def check_payment_method(value):
    if value not in PAYMENT_METHODS:
        raise ValueError(f"unknown payment method, expected one of: {', '.join(PAYMENT_METHODS)}")
    return value


def check_password_bytes(value):
    # bcrypt only accepts up to 72 bytes
    if len(value.encode("utf-8")) > 72:
        raise ValueError("password is too long")
    return value


Category = Annotated[str, AfterValidator(check_category)]
PaymentMethod = Annotated[str, AfterValidator(check_payment_method)]


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    password: Annotated[str, Field(min_length=6), AfterValidator(check_password_bytes)]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class ExpenseIn(BaseModel):
    date: date
    category: Category
    amount: float = Field(gt=0, le=10_000_000)
    payment_method: PaymentMethod = "Cash"
    is_recurring: bool = False
    description: str = Field("", max_length=200)


class ExpenseOut(ExpenseIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class BudgetIn(BaseModel):
    category: Category
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: float = Field(gt=0, le=100_000_000)


class BudgetOut(BudgetIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class AnomalyIn(BaseModel):
    category: Category
    amount: float = Field(gt=0)
    payment_method: PaymentMethod = "Cash"
    is_recurring: bool = False


class AnomalyOut(BaseModel):
    anomaly: bool
    reason: str
