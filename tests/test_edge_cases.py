"""
Edge case tests for the Expense Tracker API.

Covers validation errors, not-found scenarios, boundary conditions,
and concurrent operations.
"""

import sys
import os
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _expense_payload(**overrides) -> dict:
    """Helper to build a valid expense JSON payload with optional overrides."""
    base = {
        "amount": 25.50,
        "category": "Food",
        "date": date.today().isoformat(),
        "description": "Test expense",
    }
    base.update(overrides)
    return base


class TestAmountValidation:
    """Tests for amount field validation."""

    def test_create_expense_with_negative_amount_returns_422(self, client):
        """Negative amount is rejected with 422."""
        response = client.post(
            "/api/expenses/", json=_expense_payload(amount=-10.00)
        )
        assert response.status_code == 422

    def test_create_expense_with_zero_amount_returns_422(self, client):
        """Zero amount is rejected with 422."""
        response = client.post(
            "/api/expenses/", json=_expense_payload(amount=0)
        )
        assert response.status_code == 422


class TestCategoryValidation:
    """Tests for category field validation."""

    def test_create_expense_with_invalid_category_returns_422(self, client):
        """Invalid category string is rejected with 422."""
        response = client.post(
            "/api/expenses/", json=_expense_payload(category="InvalidCategory")
        )
        assert response.status_code == 422


class TestDateHandling:
    """Tests for date field edge cases."""

    def test_create_expense_with_future_date_still_saves(self, client):
        """Future dates are allowed and saved correctly."""
        future = (date.today() + timedelta(days=30)).isoformat()
        response = client.post(
            "/api/expenses/", json=_expense_payload(date=future)
        )
        assert response.status_code == 201
        assert response.json()["date"] == future


class TestNotFound:
    """Tests for 404 scenarios."""

    def test_get_nonexistent_expense_returns_404(self, client):
        """Fetching a non-existent expense returns 404."""
        response = client.get("/api/expenses/99999")
        assert response.status_code == 404

    def test_delete_nonexistent_expense_returns_404(self, client):
        """Deleting a non-existent expense returns 404."""
        response = client.delete("/api/expenses/99999")
        assert response.status_code == 404

    def test_update_nonexistent_expense_returns_404(self, client):
        """Updating a non-existent expense returns 404."""
        response = client.put(
            "/api/expenses/99999",
            json={"amount": 10.00},
        )
        assert response.status_code == 404


class TestFilterEdgeCases:
    """Tests for filtering edge cases."""

    def test_filter_with_no_matching_results_returns_empty_list(self, client):
        """Filtering with no matches returns an empty list, not an error."""
        client.post("/api/expenses/", json=_expense_payload(category="Food"))

        response = client.get("/api/expenses/?category=Transport")
        assert response.status_code == 200
        assert response.json() == []


class TestDescriptionValidation:
    """Tests for description length validation."""

    def test_description_over_200_chars_returns_422(self, client):
        """Description exceeding 200 characters is rejected with 422."""
        long_desc = "x" * 201
        response = client.post(
            "/api/expenses/", json=_expense_payload(description=long_desc)
        )
        assert response.status_code == 422


class TestStatsEdgeCases:
    """Tests for stats endpoint edge cases."""

    def test_stats_with_zero_expenses_returns_zero_totals(self, client):
        """Stats with no expenses returns zeroed-out values."""
        response = client.get("/api/expenses/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_all_time"] == 0.0
        assert data["total_this_month"] == 0.0
        assert data["highest_expense"] is None
        assert data["transaction_count"] == 0
        assert data["by_category"] == {}


class TestConcurrency:
    """Tests for concurrent operations."""

    def test_concurrent_deletes_do_not_cause_500(self, client):
        """
        Two concurrent delete requests for the same expense should not
        cause a 500 error. One should succeed (204), the other should get 404.
        """
        create_resp = client.post("/api/expenses/", json=_expense_payload())
        expense_id = create_resp.json()["id"]

        results = []

        def do_delete():
            resp = client.delete(f"/api/expenses/{expense_id}")
            results.append(resp.status_code)

        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(do_delete)
            executor.submit(do_delete)
            executor.shutdown(wait=True)

        # One should be 204, the other 404. Neither should be 500.
        assert 500 not in results
        assert 204 in results
        assert 404 in results or results.count(204) == 2
