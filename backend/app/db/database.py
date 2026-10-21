from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# The hosted database scales to zero when idle and drops its connections. A
# pooled connection from before the pause is dead, and reusing it failed the
# first request after every quiet period (an intermittent 500). pre_ping tests
# each connection before use and replaces dead ones; recycle retires
# connections before they get that old.
engine = create_engine(settings.database_url_for_sqlalchemy, pool_pre_ping=True, pool_recycle=280)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
