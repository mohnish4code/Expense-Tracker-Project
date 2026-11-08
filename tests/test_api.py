import pytest

EXPENSE = {"date": "2024-03-05", "category": "Transport", "amount": 120.5, "payment_method": "Cash"}


def test_requires_login(tmp_path):
    from tests.conftest import make_client

    with make_client(tmp_path) as c:
        assert c.get("/api/expenses").status_code == 401
        assert c.get("/api/insights/2024/3").status_code == 401
        assert c.get("/", follow_redirects=False).headers["location"] == "/login"


def test_register_login_logout(client):
    assert client.get("/api/auth/me").json()["username"] == "alice"
    assert client.post("/api/auth/register", json={"username": "alice", "password": "secret123"}).status_code == 409
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"username": "alice", "password": "wrong-pass"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "alice", "password": "secret123"}).status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_expense_crud(client):
    created = client.post("/api/expenses", json=EXPENSE)
    assert created.status_code == 201
    expense_id = created.json()["id"]

    listed = client.get("/api/expenses", params={"year": 2024, "month": 3}).json()
    assert [e["id"] for e in listed] == [expense_id]
    assert client.get("/api/expenses", params={"year": 2024, "month": 4}).json() == []

    updated = client.put(f"/api/expenses/{expense_id}", json={**EXPENSE, "amount": 200})
    assert updated.json()["amount"] == 200

    assert client.delete(f"/api/expenses/{expense_id}").status_code == 204
    assert client.delete(f"/api/expenses/{expense_id}").status_code == 404


@pytest.mark.parametrize(
    "change",
    [
        {"amount": 0},
        {"amount": -10},
        {"category": "Groceries"},
        {"date": "2024-02-30"},
        {"date": "yesterday"},
        {"payment_method": "Crypto"},
    ],
)
def test_expense_validation(client, change):
    assert client.post("/api/expenses", json={**EXPENSE, **change}).status_code == 422


def test_users_cannot_touch_each_others_expenses(client):
    expense_id = client.post("/api/expenses", json=EXPENSE).json()["id"]
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json={"username": "bob", "password": "secret123"})

    assert client.get("/api/expenses").json() == []
    assert client.put(f"/api/expenses/{expense_id}", json=EXPENSE).status_code == 404
    assert client.delete(f"/api/expenses/{expense_id}").status_code == 404


def test_budget_upsert(client):
    budget = {"category": "Transport", "year": 2024, "month": 3, "amount": 4000}
    assert client.post("/api/budgets", json=budget).status_code == 201
    assert client.post("/api/budgets", json={**budget, "amount": 5000}).status_code == 200
    budgets = client.get("/api/budgets", params={"year": 2024, "month": 3}).json()
    assert len(budgets) == 1 and budgets[0]["amount"] == 5000
    assert client.post("/api/budgets", json={**budget, "month": 13}).status_code == 422


def test_insights_math(client):
    client.post("/api/budgets", json={"category": "Transport", "year": 2024, "month": 3, "amount": 4000})
    client.post("/api/budgets", json={"category": "Food & Groceries", "year": 2024, "month": 3, "amount": 10000})
    for category, amount, day in [("Transport", 1000, 2), ("Transport", 500, 9), ("Food & Groceries", 12000, 4)]:
        client.post("/api/expenses", json={**EXPENSE, "category": category, "amount": amount, "date": f"2024-03-0{day}"})
    client.post("/api/expenses", json={**EXPENSE, "date": "2024-04-01", "amount": 999})

    data = client.get("/api/insights/2024/3").json()
    assert data["budget"] == 14000
    assert data["spent"] == 13500
    assert data["remaining"] == 500
    assert data["usage_pct"] == pytest.approx(96.4)

    by_category = {c["category"]: c for c in data["categories"]}
    assert by_category["Transport"]["spent"] == 1500
    assert by_category["Transport"]["usage_pct"] == 37.5
    assert by_category["Food & Groceries"]["remaining"] == -2000

    assert [(t["month"], t["spent"]) for t in data["trend"]] == [(3, 13500), (4, 999)]
    assert client.get("/api/months").json() == [{"year": 2024, "month": 4}, {"year": 2024, "month": 3}]


def test_prediction_endpoints(client):
    client.post("/api/budgets", json={"category": "Food & Groceries", "year": 2024, "month": 3, "amount": 10000})
    client.post("/api/expenses", json={**EXPENSE, "category": "Food & Groceries", "amount": 15000})

    anomaly = client.post("/api/predict/anomaly", json={"category": "Food & Groceries", "amount": 15000}).json()
    assert anomaly["anomaly"] is True

    risk = client.get("/api/predict/overspend/2024/3", params={"day": 7}).json()
    assert risk["as_of_day"] == 7
    assert risk["categories"][0]["category"] == "Food & Groceries"
    assert risk["categories"][0]["level"] == "high"

    insights = client.get("/api/insights/2024/3").json()
    assert [a["amount"] for a in insights["anomalies"]] == [15000]

    recs = client.get("/api/recommendations").json()
    assert recs[0]["category"] == "Food & Groceries"
