import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(url: str | None = None):
    url = url or os.getenv("DATABASE_URL", "sqlite:///./aegisrisk.db")
    options = {"check_same_thread": False} if url.startswith("sqlite") else {"connect_timeout": 5}
    return create_engine(url, pool_pre_ping=True, connect_args=options)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine)


def get_session():
    with SessionLocal() as session:
        yield session
