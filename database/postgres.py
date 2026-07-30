"""SQLAlchemy engine/session management for the enterprise PostgreSQL store."""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings
from database.models import Base


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.sqlalchemy_dsn, pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provides a transactional session, committing on success and rolling
    back on error. Use as: `with session_scope() as db: ...`.
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Creates all tables that don't yet exist. Idempotent."""
    Base.metadata.create_all(bind=get_engine())


def reset_db() -> None:
    """Drops and recreates all tables. Used by the seed script for a clean slate."""
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())
