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

- **Code Quality Enforcer**: Handles all code quality, formatting, and modern Python syntax enforcement
- **SQLAlchemy Expert**: Manages all database ORM patterns, queries, and relationships  
- **Pytest Testing Expert**: Comprehensive test design, fixtures, and testing patterns
- **Exception Handler Specialist**: Custom exception design and error handling patterns
- **Database Migration Specialist**: Alembic migrations and schema management
- **FastAPI Specialist**: API design, routing, and dependency injection patterns
- **DevOps Specialist**: Docker, deployment, and infrastructure managemen

## Do Not Touch

- Never use legacy SQLAlchemy `db.query()` - use `select()` statements only
- Never import old typing (`List`, `Dict`, `Optional`, `Union`) - use modern syntax
- Never skip the code quality workflow (isort → black → flake8)
- Never commit without running tests
- Never use generic exceptions - always create custom exceptions
- Never inherit from existing test classes that already test the same functionality - this causes duplicate test execution
- Never import modules inside functions (unless explicitly instructed or required to avoid circular imports)

## Code Standards

### Must Use Modern Syntax

**Python Typing (3.10+):**

```python
# ✅ Use
list[str]  # not List[str]  
dict[str, int]  # not Dict[str, int]
str | None  # not Optional[str]

# ✅ Pydantic v2
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    email: Annotated[str | None, Field(default=None)]
    
    model_config = ConfigDict(from_attributes=True)
```

**SQLAlchemy v2:**

```python
# ✅ Use
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column


# Model definition with Mapped types
class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)


def get_user(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalars().first()


# ❌ Never use
return db.query(User).filter(User.id == user_id).first()
```

### Code Quality Workflow

**REQUIRED before every commit:**

1. `isort .` - Sort imports
2. `black .` - Format code
3. `flake8 .` - Lint code

All three must pass without errors.

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

## Custom Exceptions Pattern

```python
# exceptions.py
class ModuleException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ResourceNotFound(ModuleException):
    def __init__(self, resource_id: int):
        self.message = f"Resource with ID {resource_id} not found"
        super().__init__(self.message)


# service.py  
def get_resource(db: Session, resource_id: int):
    resource = db.execute(select(Resource).where(Resource.id == resource_id)).scalar_one_or_none()
    if not resource:
        raise ResourceNotFound(resource_id)
    return resource


# router.py
@router.get("/{resource_id}")
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    try:
        return service.get_resource(db, resource_id)
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail=e.message)
```

## Database Guidelines

**Naming Conventions:**

- `lower_case_snake` for all names
- Singular table names (`user`, not `users`)
- `_at` suffix for datetime fields
- `_date` suffix for date fields
- **String field lengths**: Always use `String(255)` for name fields, `Text` for longer content

**Query Rules:**

1. Always use `select()` statements, never `db.query()`
2. Use `.where()` instead of `.filter()`
3. Use `db.execute(stmt).scalars().first/all()`
4. Use `paginate_select()` for pagination
5. Use `.unique()` with `joinedload`

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

## Testing Guidelines

### Structure

- **Domain-based organization**: Each domain has `tests/domain_name/fixtures.py` for fixtures and `test_*.py` for tests
- **Fixture registration**: Global `conftest.py` uses `pytest_plugins` to register domain fixtures
- **Base test classes**: Inherit from `BaseAPITestClass` in `tests/base.py` for standard CRUD/pagination/search tests
- **Test utilities**: Use helpers from `tests/utils.py` for consistent assertions

### Test Class Pattern

```python
class TestResourceAPI(BaseAPITestClass):
    resource_name = "resources"
    resource_endpoint = f"{settings.api_v1_prefix}/resources"
    create_data_fixture = "sample_resource_data"
    instance_fixture = "sample_resource"

    # Configure other fixture names as needed

    def _get_update_data(self) -> dict:
        return {"name": "Updated Name"}

    # Add only resource-specific tests here
    # CRUD/pagination/search inherited automatically
```

**Reference**: See `tests/suppliers/test_suppliers_api.py` for complete example pattern.

## Event Listeners for Purpose Updates

**Required**: Add event listeners to models that relate to Purpose to update `last_modified` timestamps.

Models requiring event listeners: Cost, Stage, Purchase, FileAttachment, and any new models with purpose relationships.

**Pattern**: Reference `app/costs/models.py` for implementation. Use `@event.listens_for()` with `after_insert`, `after_update`, `after_delete` to call `update_purpose_last_modified()`.