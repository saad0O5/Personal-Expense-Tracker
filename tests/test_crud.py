"""
Unit tests for CRUD operations.

Tests the crud module functions directly against an in-memory SQLite database.
Each test is fully independent with its own database session.
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import ExpenseCreate, ExpenseUpdate, CategoryEnum
import crud


def _make_expense(
    amount: float = 25.50,
    category: CategoryEnum = CategoryEnum.FOOD,
    expense_date: date = None,
    description: str = "Test expense",
) -> ExpenseCreate:
    """Helper to create an ExpenseCreate schema instance."""
    return ExpenseCreate(
        amount=amount,
        category=category,
        date=expense_date or date.today(),
        description=description,
    )


class TestCreateExpense:
    """Tests for crud.create_expense."""

    def test_create_expense(self, db_session):
        """Creating an expense returns a record with correct fields."""
        data = _make_expense(amount=42.99, description="Lunch")
        result = crud.create_expense(db_session, data)

        assert result.id is not None
        assert result.amount == 42.99
        assert result.category == "Food"
        assert result.description == "Lunch"
        assert result.date == date.today()


class TestGetExpenses:
    """Tests for crud.get_expenses."""

    def test_get_all_expenses(self, db_session):
        """Retrieving all expenses returns every record."""
        crud.create_expense(db_session, _make_expense(description="One"))
        crud.create_expense(db_session, _make_expense(description="Two"))
        crud.create_expense(db_session, _make_expense(description="Three"))

        results = crud.get_expenses(db_session)
        assert len(results) == 3

    def test_get_expense_by_id(self, db_session):
        """Fetching by ID returns the correct expense."""
        created = crud.create_expense(db_session, _make_expense(amount=99.99))
        found = crud.get_expense_by_id(db_session, created.id)

        assert found is not None
        assert found.id == created.id
        assert found.amount == 99.99

    def test_filter_by_category(self, db_session):
        """Filtering by category returns only matching expenses."""
        crud.create_expense(db_session, _make_expense(category=CategoryEnum.FOOD))
        crud.create_expense(db_session, _make_expense(category=CategoryEnum.TRANSPORT))
        crud.create_expense(db_session, _make_expense(category=CategoryEnum.FOOD))

        results = crud.get_expenses(db_session, category="Food")
        assert len(results) == 2
        assert all(r.category == "Food" for r in results)

    def test_filter_by_date_range(self, db_session):
        """Filtering by date range returns only expenses within the range."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)

        crud.create_expense(db_session, _make_expense(expense_date=today))
        crud.create_expense(db_session, _make_expense(expense_date=yesterday))
        crud.create_expense(db_session, _make_expense(expense_date=last_week))

        results = crud.get_expenses(db_session, start_date=yesterday, end_date=today)
        assert len(results) == 2


class TestUpdateExpense:
    """Tests for crud.update_expense."""

    def test_update_expense(self, db_session):
        """Updating an expense changes only the specified fields."""
        created = crud.create_expense(
            db_session, _make_expense(amount=10.00, description="Original")
        )
        update_data = ExpenseUpdate(amount=20.00, description="Updated")
        updated = crud.update_expense(db_session, created.id, update_data)

        assert updated is not None
        assert updated.amount == 20.00
        assert updated.description == "Updated"
        assert updated.category == "Food"  # unchanged


class TestDeleteExpense:
    """Tests for crud.delete_expense."""

    def test_delete_expense(self, db_session):
        """Deleting an expense removes it from the database."""
        created = crud.create_expense(db_session, _make_expense())
        assert crud.delete_expense(db_session, created.id) is True
        assert crud.get_expense_by_id(db_session, created.id) is None


class TestGetStats:
    """Tests for crud.get_stats."""

    def test_get_stats_returns_correct_totals(self, db_session):
        """Stats endpoint returns correct aggregate totals."""
        crud.create_expense(db_session, _make_expense(amount=100.00))
        crud.create_expense(db_session, _make_expense(amount=50.00))
        crud.create_expense(db_session, _make_expense(amount=25.00))

        stats = crud.get_stats(db_session)

        assert stats["total_all_time"] == 175.00
        assert stats["transaction_count"] == 3
        assert stats["highest_expense"].amount == 100.00

    def test_get_stats_by_category_breakdown(self, db_session):
        """Stats by_category groups amounts correctly."""
        crud.create_expense(
            db_session, _make_expense(amount=30.00, category=CategoryEnum.FOOD)
        )
        crud.create_expense(
            db_session, _make_expense(amount=20.00, category=CategoryEnum.FOOD)
        )
        crud.create_expense(
            db_session, _make_expense(amount=15.00, category=CategoryEnum.TRANSPORT)
        )

        stats = crud.get_stats(db_session)

        assert stats["by_category"]["Food"] == 50.00
        assert stats["by_category"]["Transport"] == 15.00
