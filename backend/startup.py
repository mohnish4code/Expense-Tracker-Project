from backend.db import Base
from expense_tracker.predict import load_models


def run(app):
    Base.metadata.create_all(app.state.engine)
    app.state.models = load_models(app.state.models_dir)
