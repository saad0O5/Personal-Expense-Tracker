# Personal Expense Tracker

A full-stack web application for tracking personal expenses with an interactive dashboard, real-time filtering, and dynamic charts. Built as a capstone project using Python, FastAPI, and vanilla JavaScript.

## Features

- **Add, Edit, Delete Expenses** via modal forms with no page reload
- **Interactive Dashboard** with animated stat cards and Chart.js visualizations
- **Doughnut Chart** showing spending breakdown by category (clickable legend)
- **Line Chart** displaying monthly spending trend for the last 6 months
- **Real-time Filtering** by category, date range, and keyword search (debounced)
- **Sortable Table** with click-to-sort columns (ascending/descending)
- **Toast Notifications** for every add, edit, and delete action
- **Client-side Validation** with Bootstrap visual feedback
- **Responsive Design** optimized for mobile, tablet, and desktop
- **SQLite Persistence** for all expense data
- **Auto-generated API docs** at `/docs` (Swagger UI)

## Screenshots

[Screenshot: Dashboard with stat cards and charts]

[Screenshot: Expense table with filter bar]

[Screenshot: Add Expense modal with validation]

[Screenshot: Mobile responsive view]

## Tech Stack

| Layer        | Technology                          |
|------------- |-------------------------------------|
| Backend      | Python 3.10+, FastAPI               |
| Frontend     | HTML5, CSS3, Vanilla JavaScript     |
| UI Framework | Bootstrap 5 (CDN)                   |
| Charts       | Chart.js 4.x (CDN)                  |
| Database     | SQLite with SQLAlchemy ORM          |
| Validation   | Pydantic v2                         |
| Testing      | pytest, httpx, TestClient           |
| Docs         | FastAPI auto-generated Swagger UI   |

## Setup & Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd expense-tracker
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

5. Open your browser and navigate to `http://127.0.0.1:8000`

## How to Run

```bash
# Start the development server
uvicorn main:app --reload

# The app will be available at:
# - Main UI:     http://127.0.0.1:8000
# - API Docs:    http://127.0.0.1:8000/docs
# - ReDoc:       http://127.0.0.1:8000/redoc
```

## How to Run Tests

```bash
# Run all tests with verbose output and coverage
pytest tests/ -v --cov

# Run specific test files
pytest tests/test_crud.py -v
pytest tests/test_routes.py -v
pytest tests/test_edge_cases.py -v
```

## API Endpoints

| Method   | Route                    | Description                                      |
|----------|--------------------------|--------------------------------------------------|
| `GET`    | `/`                      | Render the main dashboard page                   |
| `POST`   | `/api/expenses/`         | Create a new expense                             |
| `GET`    | `/api/expenses/`         | List all expenses (with optional filters/sorting)|
| `GET`    | `/api/expenses/stats`    | Get aggregated statistics for the dashboard      |
| `GET`    | `/api/expenses/{id}`     | Get a single expense by ID                       |
| `PUT`    | `/api/expenses/{id}`     | Update an existing expense                       |
| `DELETE` | `/api/expenses/{id}`     | Delete an expense                                |

### Query Parameters for `GET /api/expenses/`

| Parameter    | Type   | Description                          |
|------------- |--------|--------------------------------------|
| `category`   | string | Filter by category name              |
| `start_date` | date   | Filter expenses on or after this date|
| `end_date`   | date   | Filter expenses on or before this date|
| `keyword`    | string | Search in description (case-insensitive)|
| `sort_by`    | string | Sort column: date, amount, category, description |
| `sort_dir`   | string | Sort direction: asc or desc          |

### Expense Categories

Food, Transport, Health, Entertainment, Shopping, Utilities, Other

## How I Used GitHub Copilot

GitHub Copilot was used as an AI pair-programming assistant throughout this project:

- **Code Generation**: Copilot helped scaffold boilerplate code for FastAPI routes, SQLAlchemy models, and Pydantic schemas.
- **Test Writing**: Copilot suggested test cases and helped write comprehensive test assertions, including edge cases for validation errors and concurrent operations.
- **JavaScript Logic**: Copilot assisted with Chart.js configuration, debounce utilities, and DOM manipulation patterns.
- **CSS Styling**: Copilot provided suggestions for responsive layout adjustments and animation keyframes.
- **Documentation**: Copilot helped draft docstrings, type hints, and this README structure.

## Project Structure

```
expense-tracker/
├── main.py                    # FastAPI app entry point
├── database.py                # SQLAlchemy engine & session config
├── models.py                  # ORM model (Expense table)
├── schemas.py                 # Pydantic validation schemas
├── crud.py                    # Database CRUD operations
├── routers/
│   └── expenses.py            # API route handlers
├── templates/
│   ├── base.html              # Bootstrap 5 layout, navbar, modals
│   ├── index.html             # Dashboard + expense table page
│   └── partials/
│       └── expense_row.html   # Single table row partial
├── static/
│   ├── style.css              # Custom CSS styles
│   └── app.js                 # Frontend JavaScript logic
├── tests/
│   ├── conftest.py            # Test fixtures & configuration
│   ├── test_crud.py           # Unit tests for CRUD operations
│   ├── test_routes.py         # Integration tests for API routes
│   └── test_edge_cases.py     # Edge case & validation tests
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

## Known Limitations / Future Improvements

1. **No User Authentication**: The app currently has no login system. Adding user accounts with JWT authentication would allow multi-user support and secure access.

2. **No Data Export**: Users cannot currently export their expense data. Adding CSV/PDF export functionality would improve data portability and reporting.

3. **No Budget Setting**: There is no way to set monthly budgets or spending limits. Adding budget tracking with alerts when approaching limits would enhance financial planning.

4. **No Recurring Expenses**: The app does not support automatic recurring expenses (e.g., monthly subscriptions). Adding this feature would reduce manual data entry.

5. **SQLite Limitations**: SQLite works well for single-user scenarios but would need to be replaced with PostgreSQL or MySQL for production multi-user deployments.
