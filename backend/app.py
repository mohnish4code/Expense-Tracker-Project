import os
import secrets
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from backend import auth, startup
from backend.db import DEFAULT_DATABASE_URL, make_session_factory
from backend.routers import budgets, expenses, insights, predict
from expense_tracker.config import MODELS_DIR, RESULTS_DIR


def create_app(database_url=None, secret_key=None, models_dir=MODELS_DIR, results_dir=RESULTS_DIR):
    load_dotenv()
    database_url = database_url or os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
    secret_key = secret_key or os.getenv("SECRET_KEY")
    if not secret_key:
        print("WARNING: SECRET_KEY is not set, using a random dev key. Logins reset on every restart.", flush=True)
        secret_key = secrets.token_urlsafe(32)

    @asynccontextmanager
    async def lifespan(app):
        startup.run(app)
        yield
        app.state.engine.dispose()

    app = FastAPI(title="Expense Tracker", version="1.0.0", lifespan=lifespan)
    app.state.engine, app.state.session_factory = make_session_factory(database_url)
    app.state.secret_key = secret_key
    app.state.models_dir = models_dir
    app.state.results_dir = results_dir

    app.include_router(auth.router)
    app.include_router(expenses.router)
    app.include_router(budgets.router)
    app.include_router(insights.router)
    app.include_router(predict.router)
    return app
