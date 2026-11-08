import pandas as pd
import pytest

from expense_tracker.predict import flag_anomalies, load_models


@pytest.fixture(scope="module")
def models():
    return load_models()


def check(models, category, amount, recurring=False, payment="Cash"):
    df = pd.DataFrame(
        [{"Category": category, "Amount": amount, "Payment Method": payment, "Is Recurring": recurring}]
    )
    return flag_anomalies(models["anomaly"], df).iloc[0]


def test_large_food_spend_is_flagged(models):
    row = check(models, "Food & Groceries", 15_000)
    assert row["Anomaly"]
    assert "Food & Groceries" in row["Reason"]


def test_monthly_rent_is_not_flagged(models):
    assert not check(models, "Rent", 21_750, recurring=True, payment="Bank Transfer")["Anomaly"]
    # rent is a fixed category, so it is checked against its usual amount even without the flag
    assert not check(models, "Rent", 21_750)["Anomaly"]


def test_unusual_rent_is_flagged(models):
    assert check(models, "Rent", 45_000, recurring=True)["Anomaly"]


def test_normal_spend_is_not_flagged(models):
    assert not check(models, "Food & Groceries", 2_200)["Anomaly"]
    assert not check(models, "Transport", 600)["Anomaly"]


def test_overspend_model_outputs_probabilities(models, expenses_df, budgets_df):
    from expense_tracker.predict import overspend_risk

    risk = overspend_risk(models["overspend"], expenses_df, budgets_df, 2024, 2, 14)
    assert len(risk) == 2
    assert risk["Risk"].between(0, 1).all()
