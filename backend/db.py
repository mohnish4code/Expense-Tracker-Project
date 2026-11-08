from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from expense_tracker.config import ROOT

DEFAULT_DATABASE_URL = f"sqlite:///{(ROOT / 'expense_tracker.db').as_posix()}"


class Base(DeclarativeBase):
    pass


def make_session_factory(database_url):
    # Supabase hands out postgres:// URLs; point SQLAlchemy at the psycopg 3 driver
    for prefix in ("postgres://", "postgresql://"):
        if database_url.startswith(prefix):
            database_url = "postgresql+psycopg://" + database_url.removeprefix(prefix)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def get_db(request: Request):
    db = request.app.state.session_factory()
    try:
        yield db
    finally:
        db.close()
