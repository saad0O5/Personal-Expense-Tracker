"""
Pydantic schemas for request validation and response serialization.

Enforces business rules: amount > 0, category from an allowed list,
description max 200 characters.
"""

import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List
from enum import Enum


class CategoryEnum(str, Enum):
    """Allowed expense categories."""

    FOOD = "Food"
    TRANSPORT = "Transport"
    HEALTH = "Health"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    UTILITIES = "Utilities"
    OTHER = "Other"


class ExpenseCreate(BaseModel):
    """Schema for creating a new expense."""

    amount: float = Field(..., gt=0, description="Expense amount, must be greater than 0")
    category: CategoryEnum = Field(..., description="Expense category")
    expense_date: datetime.date = Field(..., alias="date", description="Date of the expense")
    description: str = Field(
        default="", max_length=200, description="Short description (max 200 chars)"
    )

    model_config = {"populate_by_name": True}

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        """Strip leading/trailing whitespace from description."""
        return v.strip()


class ExpenseUpdate(BaseModel):
    """Schema for updating an existing expense. All fields optional."""

    amount: Optional[float] = Field(None, gt=0, description="Expense amount")
    category: Optional[CategoryEnum] = Field(None, description="Expense category")
    expense_date: Optional[datetime.date] = Field(None, alias="date", description="Date of the expense")
    description: Optional[str] = Field(
        None, max_length=200, description="Short description (max 200 chars)"
    )

    model_config = {"populate_by_name": True}

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: Optional[str]) -> Optional[str]:
        """Strip leading/trailing whitespace from description if provided."""
        if v is not None:
            return v.strip()
        return v


class ExpenseResponse(BaseModel):
    """Schema for returning expense data in API responses."""

    id: int
    amount: float
    category: str
    date: datetime.date
    description: str

    model_config = {"from_attributes": True}


class MonthlyTrend(BaseModel):
    """Single data point for monthly spending trend."""

    month: str
    total: float


class StatsResponse(BaseModel):
    """Aggregated statistics about expenses."""

    total_all_time: float
    total_this_month: float
    highest_expense: Optional[ExpenseResponse] = None
    transaction_count: int
    by_category: Dict[str, float]
    monthly_trend: List[MonthlyTrend]
