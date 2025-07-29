# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Procurement Management System backend built with FastAPI. Manages Purposes, Purchases, Stages, Costs, and
Hierarchies with full CRUD operations, advanced filtering, and search capabilities.

## Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy (v2 mode)
- **Migrations**: Alembic
- **Database**: PostgreSQL
- **Testing**: Pytest
- **Deployment**: Docker with .env configuration

## Quick Start

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Run tests  
pytest
```

### Essential Commands

**Code Quality (ALWAYS run before commit):**

```bash
isort .     # Sort imports first
black .     # Format code  
flake8 .    # Lint code
```

**Database:**

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

**Testing:**

```bash
# Run tests with Docker (recommended)
docker run --rm -v $(pwd):/app -w /app calculaud-be python -m pytest

# Local testing (if environment is set up)
pytest -v                    # Verbose output
pytest tests/suppliers/      # Test specific domain
pytest -k "test_name"        # Pattern matching
pytest tests/suppliers/test_suppliers_api.py::TestSuppliersApi::test_create_resource  # Specific test
```

## Specialized Agents

This project uses specialized agents for domain-specific tasks:

- **Code Quality Enforcer**: Handles all code quality, formatting, and modern Python syntax enforcement
- **SQLAlchemy Expert**: Manages all database ORM patterns, queries, and relationships  
- **Pytest Testing Expert**: Comprehensive test design, fixtures, and testing patterns
- **Exception Handler Specialist**: Custom exception design and error handling patterns
- **Database Migration Specialist**: Alembic migrations and schema management
- **FastAPI Specialist**: API design, routing, and dependency injection patterns
- **DevOps Specialist**: Docker, deployment, and infrastructure management

## Core Standards (Enforced by Agents)

- Modern Python 3.10+ syntax only (`str | None`, not `Optional[str]`)
- SQLAlchemy v2 patterns exclusively (`select()`, not `db.query()`)
- Mandatory code quality workflow: `isort → black → flake8`
- Custom exceptions for all error handling
- Comprehensive test coverage with domain-based organization

## Data Model

**Core Entities:**

- **Purpose** - Main procurement request (links to Hierarchy, contains Purchases)
- **Purchase** - Procurement form details (belongs to Purpose, contains Stages and Costs)
- **Stage** - Workflow stages with values (belongs to Purchase)
- **Cost** - Financial entries (belongs to Purchase)
- **Hierarchy** - Self-referencing organizational tree structure

## API Patterns

**Main Resources:**

- `/purposes` - Full CRUD, filtering, search, pagination
- `/costs` - Managed through purchases within purposes
- `/hierarchies` - Organizational structure
- `/files` - File upload and management

**Purchase Operations:**

- Create: Include in `POST /purposes` or `PATCH /purposes/{id}`
- Update: Use `PATCH /purposes/{id}` with updated purchase data
- Delete: Use `PATCH /purposes/{id}` without the purchase

**File Upload Workflow:**

1. `POST /api/v1/files/upload` → get `file_id`
2. Include `file_attachment_ids` in purpose create/update
3. Files automatically linked to purpose

## Configuration

- Use Pydantic `BaseSettings` for all config
- Global config: `src/config.py`
- Import: `from app.config import settings`
- Environment variables as class attributes

## Project Structure

```
app/
├── __init__.py            # Import all models for SQLAlchemy registration
├── domain_module/          # Each domain has:
│   ├── router.py          # Endpoints
│   ├── schemas.py         # Pydantic models  
│   ├── models.py          # DB models (use Mapped types)
│   ├── service.py         # Business logic
│   ├── dependencies.py    # Router dependencies
│   ├── exceptions.py      # Custom exceptions
│   └── utils.py           # Helper functions
├── config.py              # Global config
├── database.py            # DB connection
├── pagination.py          # Pagination utilities
└── main.py                # FastAPI app init
```

**Model Registration:**  
All SQLAlchemy models must be imported in `app/__init__.py` to ensure proper registration:

```python
# app/__init__.py - Import all models for SQLAlchemy registration
from .costs.models import Cost, CurrencyEnum  # noqa: F401
from .emfs.models import EMF  # noqa: F401
from .purposes.models import Purpose, StatusEnum  # noqa: F401
# ... import all other models
```


## Git Workflow

```bash
# Feature branch workflow
git checkout main && git pull origin main
git checkout -b feature/your-feature-name

# Commit with proper format
git add . && git commit -m "feat: description"

# Create PR
git push -u origin feature/your-feature-name
gh pr create --title "Feature: Description" --body "Details"

# Cleanup after merge  
git checkout main && git pull origin main
git branch -d feature/your-feature-name
```

## Development Guidelines

**Required Features:**

- Advanced filtering by hierarchy_id, emf_id, supplier, service_type, status
- Full-text search across description, content, emf_id
- Sorting by creation_time, last_modified, expected_delivery
- Pagination for large datasets
- Proper cascade deletion handling

**Implementation Checklist:**

1. FastAPI project structure with dependency injection
2. SQLAlchemy v2 configuration
3. Alembic database migrations
4. Comprehensive Pytest test suite
5. Docker deployment configuration
6. Proper error handling and validation

## Style Guidelines

- **PEP 8** compliance
- **Type hints** for all functions and classes
- **Google-style docstrings**
- **snake_case** for variables/functions, **PascalCase** for classes
- Line length: 120 characters

