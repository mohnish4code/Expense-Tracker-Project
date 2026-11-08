from tests.conftest import make_client


def test_empty_database_seeds_trains_and_serves(tmp_path, capsys):
    models_dir = tmp_path / "models"

    with make_client(tmp_path, seed_demo=True, models_dir=models_dir) as c:
        out = capsys.readouterr().out
        assert "Seeded demo user" in out
        assert "Models missing, training them now" in out
        assert "Open http://127.0.0.1:8000 (demo login: demo / demo123)" in out
        assert (models_dir / "anomaly.joblib").exists() and (models_dir / "overspend.json").exists()

        assert c.post("/api/auth/login", json={"username": "demo", "password": "demo123"}).status_code == 200
        assert c.get("/").status_code == 200
        insights = c.get("/api/insights/2024/12")
        assert insights.status_code == 200
        assert insights.json()["spent"] > 0

    with make_client(tmp_path, seed_demo=True, models_dir=models_dir):
        out = capsys.readouterr().out
        assert "skipping demo seed" in out
        assert "skipping training" in out
