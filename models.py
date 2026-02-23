"""
SQLAlchemy ORM model for the Expense entity.

Defines the `expenses` table schema with columns for amount,
category, date, description, and auto-generated timestamps.
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from database import Base
import datetime


class Expense(Base):
    """ORM model representing a single expense record."""

    __tablename__ = "expenses"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amount: float = Column(Float, nullable=False)
    category: str = Column(String(50), nullable=False)
    date: datetime.date = Column(Date, nullable=False)
    description: str = Column(String(200), nullable=False, default="")
    created_at: datetime.datetime = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: datetime.datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
