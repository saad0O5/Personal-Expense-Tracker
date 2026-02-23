"""
FastAPI application entry point for the Personal Expense Tracker.

Configures middleware, mounts static files, includes API routers,
and serves the Jinja2-templated frontend.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from database import engine, Base
from routers import expenses

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Personal Expense Tracker",
    description="A full-stack expense tracking application with interactive dashboard.",
    version="1.0.0",
)

# CORS middleware — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Include API router
app.include_router(expenses.router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})
