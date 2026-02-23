"""
Database configuration and session management for the Expense Tracker.

Uses SQLAlchemy with SQLite as the backend database engine.
Provides a session factory and dependency injection helper for FastAPI.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

SQLALCHEMY_DATABASE_URL: str = "sqlite:///./expenses.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and ensure it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
