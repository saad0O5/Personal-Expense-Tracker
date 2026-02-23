"""
Integration tests for API route endpoints.

Uses FastAPI TestClient to send HTTP requests and verify responses.
Each test is fully independent with its own in-memory database.
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _expense_payload(
    amount: float = 25.50,
    category: str = "Food",
    expense_date: str = None,
    description: str = "Test expense",
) -> dict:
    """Helper to build a valid expense JSON payload."""
    return {
        "amount": amount,
        "category": category,
        "date": expense_date or date.today().isoformat(),
        "description": description,
    }


class TestCreateRoute:
    """Tests for POST /api/expenses/."""

    def test_POST_create_expense_returns_201(self, client):
        """Creating a valid expense returns 201 and the expense data."""
        payload = _expense_payload(amount=42.00, description="Dinner")
        response = client.post("/api/expenses/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 42.00
        assert data["category"] == "Food"
        assert data["description"] == "Dinner"
        assert "id" in data


class TestGetRoutes:
    """Tests for GET /api/expenses/ and /api/expenses/{id}."""

    def test_GET_all_expenses_returns_200_and_list(self, client):
        """Fetching all expenses returns 200 and a list."""
        client.post("/api/expenses/", json=_expense_payload())
        client.post("/api/expenses/", json=_expense_payload())

        response = client.get("/api/expenses/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_GET_single_expense_returns_correct_data(self, client):
        """Fetching a single expense by ID returns its data."""
        create_resp = client.post(
            "/api/expenses/", json=_expense_payload(description="Specific")
        )
        expense_id = create_resp.json()["id"]

        response = client.get(f"/api/expenses/{expense_id}")
        assert response.status_code == 200
        assert response.json()["description"] == "Specific"

    def test_GET_filter_by_category(self, client):
        """Filtering by category returns only matching expenses."""
        client.post("/api/expenses/", json=_expense_payload(category="Food"))
        client.post("/api/expenses/", json=_expense_payload(category="Transport"))
        client.post("/api/expenses/", json=_expense_payload(category="Food"))

        response = client.get("/api/expenses/?category=Food")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(e["category"] == "Food" for e in data)

    def test_GET_filter_by_date_range(self, client):
        """Filtering by date range returns only expenses within bounds."""
        today = date.today()
        yesterday = (today - timedelta(days=1)).isoformat()
        last_week = (today - timedelta(days=7)).isoformat()

        client.post("/api/expenses/", json=_expense_payload(expense_date=today.isoformat()))
        client.post("/api/expenses/", json=_expense_payload(expense_date=yesterday))
        client.post("/api/expenses/", json=_expense_payload(expense_date=last_week))

        response = client.get(
            f"/api/expenses/?start_date={yesterday}&end_date={today.isoformat()}"
        )
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestUpdateRoute:
    """Tests for PUT /api/expenses/{id}."""

    def test_PUT_update_expense_returns_updated_data(self, client):
        """Updating an expense returns the modified data."""
        create_resp = client.post(
            "/api/expenses/", json=_expense_payload(amount=10.00)
        )
        expense_id = create_resp.json()["id"]

        response = client.put(
            f"/api/expenses/{expense_id}",
            json={"amount": 55.00, "description": "Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 55.00
        assert data["description"] == "Updated"


class TestDeleteRoute:
    """Tests for DELETE /api/expenses/{id}."""

    def test_DELETE_expense_returns_204(self, client):
        """Deleting an expense returns 204 with no content."""
        create_resp = client.post("/api/expenses/", json=_expense_payload())
        expense_id = create_resp.json()["id"]

        response = client.delete(f"/api/expenses/{expense_id}")
        assert response.status_code == 204

        # Confirm it's gone
        get_resp = client.get(f"/api/expenses/{expense_id}")
        assert get_resp.status_code == 404


class TestStatsRoute:
    """Tests for GET /api/expenses/stats."""

    def test_GET_stats_endpoint_returns_correct_structure(self, client):
        """Stats endpoint returns all required fields with correct types."""
        client.post("/api/expenses/", json=_expense_payload(amount=100.00))
        client.post("/api/expenses/", json=_expense_payload(amount=50.00, category="Transport"))

        response = client.get("/api/expenses/stats")
        assert response.status_code == 200
        data = response.json()

        assert "total_all_time" in data
        assert "total_this_month" in data
        assert "highest_expense" in data
        assert "transaction_count" in data
        assert "by_category" in data
        assert "monthly_trend" in data

        assert data["total_all_time"] == 150.00
        assert data["transaction_count"] == 2
        assert isinstance(data["by_category"], dict)
        assert isinstance(data["monthly_trend"], list)
