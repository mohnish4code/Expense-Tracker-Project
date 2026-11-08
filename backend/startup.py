from backend.db import Base


def run(app):
    Base.metadata.create_all(app.state.engine)
