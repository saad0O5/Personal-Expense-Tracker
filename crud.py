"""
CRUD operations for the Expense model.

All database interactions are encapsulated here. Route handlers
call these functions and never touch SQLAlchemy directly.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional, Dict
from datetime import date, datetime
from models import Expense
from schemas import ExpenseCreate, ExpenseUpdate, StatsResponse, MonthlyTrend, ExpenseResponse


def create_expense(db: Session, expense_data: ExpenseCreate) -> Expense:
    """Create a new expense record and return it."""
    db_expense = Expense(
        amount=expense_data.amount,
        category=expense_data.category.value,
        date=expense_data.expense_date,
        description=expense_data.description,
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def get_expenses(
    db: Session,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    keyword: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "asc",
) -> List[Expense]:
    """
    Retrieve expenses with optional filtering, searching, and sorting.

    Args:
        db: Database session.
        category: Filter by exact category name.
        start_date: Filter expenses on or after this date.
        end_date: Filter expenses on or before this date.
        keyword: Search description (case-insensitive contains).
        sort_by: Column name to sort by (date, amount, category, description).
        sort_dir: Sort direction - 'asc' or 'desc'.

    Returns:
        List of matching Expense records.
    """
    query = db.query(Expense)

    if category:
        query = query.filter(Expense.category == category)
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if keyword:
        query = query.filter(Expense.description.ilike(f"%{keyword}%"))

    # Sorting
    allowed_sort_columns = {
        "date": Expense.date,
        "amount": Expense.amount,
        "category": Expense.category,
        "description": Expense.description,
    }
    if sort_by and sort_by in allowed_sort_columns:
        column = allowed_sort_columns[sort_by]
        if sort_dir == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    else:
        query = query.order_by(Expense.date.desc(), Expense.id.desc())

    return query.all()


def get_expense_by_id(db: Session, expense_id: int) -> Optional[Expense]:
    """Retrieve a single expense by its primary key, or None if not found."""
    return db.query(Expense).filter(Expense.id == expense_id).first()


def update_expense(
    db: Session, expense_id: int, expense_data: ExpenseUpdate
) -> Optional[Expense]:
    """
    Update an existing expense with the provided fields.

    Only non-None fields in expense_data are applied.
    Returns the updated Expense, or None if not found.
    """
    db_expense = get_expense_by_id(db, expense_id)
    if not db_expense:
        return None

    update_dict = expense_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if value is not None:
            # Map schema field name to model column name
            db_key = "date" if key == "expense_date" else key
            if key == "category":
                setattr(db_expense, db_key, value.value if hasattr(value, "value") else value)
            else:
                setattr(db_expense, db_key, value)

    db.commit()
    db.refresh(db_expense)
    return db_expense


def delete_expense(db: Session, expense_id: int) -> bool:
    """
    Delete an expense by its ID.

    Returns True if the record was deleted, False if not found.
    """
    db_expense = get_expense_by_id(db, expense_id)
    if not db_expense:
        return False

    db.delete(db_expense)
    db.commit()
    return True


def get_stats(db: Session) -> dict:
    """
    Compute aggregated expense statistics.

    Returns a dict containing:
    - total_all_time: Sum of all expense amounts.
    - total_this_month: Sum of expenses in the current month.
    - highest_expense: The single largest expense record.
    - transaction_count: Total number of expense records.
    - by_category: Dict mapping category name to total amount.
    - monthly_trend: List of {month, total} for the last 6 months.
    """
    # Total all time
    total_all_time = db.query(func.coalesce(func.sum(Expense.amount), 0.0)).scalar()

    # Total this month
    now = datetime.now()
    total_this_month = (
        db.query(func.coalesce(func.sum(Expense.amount), 0.0))
        .filter(
            extract("year", Expense.date) == now.year,
            extract("month", Expense.date) == now.month,
        )
        .scalar()
    )

    # Highest single expense
    highest_expense = db.query(Expense).order_by(Expense.amount.desc()).first()

    # Transaction count
    transaction_count = db.query(func.count(Expense.id)).scalar()

    # Spending by category
    category_rows = (
        db.query(Expense.category, func.sum(Expense.amount))
        .group_by(Expense.category)
        .all()
    )
    by_category: Dict[str, float] = {row[0]: round(row[1], 2) for row in category_rows}

    # Monthly trend (last 6 months)
    monthly_trend: List[dict] = []
    for i in range(5, -1, -1):
        # Calculate month offset
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1

        month_total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                extract("year", Expense.date) == year,
                extract("month", Expense.date) == month,
            )
            .scalar()
        )
        month_label = date(year, month, 1).strftime("%b %Y")
        monthly_trend.append({"month": month_label, "total": round(float(month_total), 2)})

    return {
        "total_all_time": round(float(total_all_time), 2),
        "total_this_month": round(float(total_this_month), 2),
        "highest_expense": highest_expense,
        "transaction_count": transaction_count,
        "by_category": by_category,
        "monthly_trend": monthly_trend,
    }
