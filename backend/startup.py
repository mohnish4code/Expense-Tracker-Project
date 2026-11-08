import time

from sqlalchemy import select

from backend.auth import hash_password
from backend.db import Base
from backend.models import Budget, Expense, User
from expense_tracker import train_anomaly, train_overspend
from expense_tracker.data import load_budgets, load_expenses
from expense_tracker.predict import load_models, models_exist

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"


def seed_demo(session_factory):
    with session_factory() as db:
        if db.execute(select(User.id).limit(1)).first() is not None:
            print("Database already has users, skipping demo seed", flush=True)
            return

        user = User(username=DEMO_USERNAME, password_hash=hash_password(DEMO_PASSWORD))
        db.add(user)
        db.flush()

        df_expenses = load_expenses()
        db.add_all(
            Expense(
                user_id=user.id,
                date=row["Date"].date(),
                category=row["Category"],
                amount=float(row["Amount"]),
                payment_method=row["Payment Method"],
                is_recurring=bool(row["Is Recurring"]),
                description=row["Description"],
            )
            for _, row in df_expenses.iterrows()
        )
        budgets = load_budgets()
        db.add_all(
            Budget(
                user_id=user.id,
                category=row["Category"],
                year=int(row["Year"]),
                month=int(row["Month"]),
                amount=float(row["Budget"]),
            )
            for _, row in budgets.iterrows()
        )
        db.commit()
        print(f"Seeded demo user with {len(df_expenses)} expenses and {len(budgets)} budgets", flush=True)


def train_if_missing(models_dir, results_dir):
    if models_exist(models_dir):
        print(f"Models found in {models_dir}, skipping training", flush=True)
        return
    print("Models missing, training them now", flush=True)
    started = time.perf_counter()
    anomaly = train_anomaly.main(models_dir, results_dir)
    overspend = train_overspend.main(models_dir, results_dir)
    print(
        f"Training finished in {time.perf_counter() - started:.1f}s "
        f"(anomaly F1 {anomaly['model']['f1']}, overspend F1 {overspend['model']['f1']})",
        flush=True,
    )


def run(app, seed=True):
    Base.metadata.create_all(app.state.engine)
    if seed:
        seed_demo(app.state.session_factory)
    train_if_missing(app.state.models_dir, app.state.results_dir)
    app.state.models = load_models(app.state.models_dir)
    print(f"Open http://127.0.0.1:8000 (demo login: {DEMO_USERNAME} / {DEMO_PASSWORD})", flush=True)
