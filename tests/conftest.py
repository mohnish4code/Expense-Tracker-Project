import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from expense_tracker.config import MODELS_DIR

SECRET = "test-secret-key-that-is-long-enough-for-hs256"


def make_client(tmp_path, seed_demo=False, models_dir=MODELS_DIR):
    app = create_app(
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        secret_key=SECRET,
        models_dir=models_dir,
        results_dir=tmp_path / "results",
        seed_demo=seed_demo,
    )
    return TestClient(app)


@pytest.fixture
def client(tmp_path):
    with make_client(tmp_path) as c:
        assert c.post("/api/auth/register", json={"username": "alice", "password": "secret123"}).status_code == 201
        yield c


@pytest.fixture
def expenses_df():
    rows = [
        ("2024-01-03", "Food & Groceries", 3000),
        ("2024-01-20", "Food & Groceries", 6000),
        ("2024-02-05", "Food & Groceries", 2000),
        ("2024-02-10", "Food & Groceries", 1500),
        ("2024-02-25", "Food & Groceries", 9000),
        ("2024-02-02", "Rent", 21750),
    ]
    df = pd.DataFrame(rows, columns=["Date", "Category", "Amount"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df


@pytest.fixture
def budgets_df():
    return pd.DataFrame(
        [
            ("Food & Groceries", 2024, 1, 8000.0),
            ("Food & Groceries", 2024, 2, 8000.0),
            ("Rent", 2024, 2, 21750.0),
        ],
        columns=["Category", "Year", "Month", "Budget"],
    )
