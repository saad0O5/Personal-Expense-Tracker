"""
API routes for expense operations.

Provides RESTful endpoints for creating, reading, updating, and deleting
expenses, plus a stats endpoint for dashboard data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database import get_db
from schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse, StatsResponse
import crud

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate, db: Session = Depends(get_db)
) -> ExpenseResponse:
    """Create a new expense record."""
    db_expense = crud.create_expense(db, expense)
    return db_expense


@router.get("/", response_model=List[ExpenseResponse])
def get_expenses(
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    keyword: Optional[str] = Query(None, description="Search keyword in description"),
    sort_by: Optional[str] = Query(None, description="Sort column"),
    sort_dir: Optional[str] = Query("asc", description="Sort direction: asc or desc"),
    db: Session = Depends(get_db),
) -> List[ExpenseResponse]:
    """Retrieve all expenses with optional filtering, searching, and sorting."""
    expenses = crud.get_expenses(
        db,
        category=category,
        start_date=start_date,
        end_date=end_date,
        keyword=keyword,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return expenses


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    """Return aggregated expense statistics for the dashboard."""
    stats = crud.get_stats(db)
    return stats


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db)) -> ExpenseResponse:
    """Retrieve a single expense by ID. Returns 404 if not found."""
    db_expense = crud.get_expense_by_id(db, expense_id)
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )
    return db_expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int, expense: ExpenseUpdate, db: Session = Depends(get_db)
) -> ExpenseResponse:
    """Update an existing expense. Returns 404 if not found."""
    db_expense = crud.update_expense(db, expense_id, expense)
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )
    return db_expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an expense by ID. Returns 404 if not found."""
    deleted = crud.delete_expense(db, expense_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )
    return None
