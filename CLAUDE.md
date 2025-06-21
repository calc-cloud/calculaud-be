# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Procurement Management System backend built with FastAPI. The system manages Purposes, EMFs (procurement
forms), Costs, and Hierarchies with full CRUD operations, advanced filtering, and search capabilities.

## Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy (v2 mode)
- **Migrations**: Alembic
- **Database**: PostgreSQL
- **Testing**: Pytest
- **Deployment**: Docker with .env configuration

## Data Model Architecture

The system has four main entities with relationships:

1. **Purpose** - Main procurement request entity
    - Links to Hierarchy (many-to-one)
    - Contains multiple EMFs (one-to-many)
    - Fields: delivery date, status, supplier, service type, content, description

2. **EMF** - Procurement form details
    - Belongs to Purpose (many-to-one)
    - Contains multiple Costs (one-to-many)
    - Tracks order, demand, and bikushit IDs with dates

3. **Cost** - Financial entries
    - Belongs to EMF (many-to-one)
    - Fields: currency, amount

4. **Hierarchy** - Organizational structure
    - Self-referencing tree structure (parent-child)
    - Fields: type (unit, center, etc.), name

## API Structure

The API follows RESTful patterns with nested resources:

- `/purposes` - Main resource with full CRUD, filtering, search, and pagination
  - EMF operations are handled through purpose routes (create, update, delete EMFs via purpose PATCH)
- `/costs` - Managed through EMFs within purposes
- `/hierarchies` - Manages organizational structure
- `/files` - Optional file upload functionality

### EMF Operations

EMF operations are integrated into the purpose routes:
- **Create EMF**: Include EMFs in `POST /purposes` or add via `PATCH /purposes/{id}`
- **Update EMF**: Use `PATCH /purposes/{id}` with updated EMF data
- **Delete EMF**: Use `PATCH /purposes/{id}` without the EMF (exclude from EMFs list)

## Key Features to Implement

- **Advanced Filtering**: Support filtering by hierarchy_id, emf_id, supplier, service_type, status
- **Search**: Full-text search across description, content, and emf_id fields
- **Sorting**: Support sorting by creation_time, last_modified, expected_delivery
- **Pagination**: Implement for large datasets
- **Cascade Operations**: Proper deletion handling with cascading deletes

## Development Commands

### Common Python Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI development server
uvicorn main:app --reload

# Run tests
pytest
pytest -v                    # verbose output
pytest tests/test_file.py    # run specific test file
pytest -k "test_name"        # run tests matching pattern

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Code formatting and linting (run in this order)
isort .                      # sort imports first
black .                      # format code (may reformat import lines)
flake8 .                     # lint code (check for style issues)

# Build and run with Docker
docker build -t calcloud-back .
docker run -p 8000:8000 calcloud-back
```

### Git Workflow Commands

```bash
# Create and switch to new feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Stage and commit changes
git add .
git status                       # check staged files
git commit -m "feat: add feature description"

# Push branch and create PR
git push -u origin feature/your-feature-name

# Create pull request using GitHub CLI
gh pr create --title "Feature: Description" --body "Detailed description of changes"

# Alternative: Create PR through GitHub web interface
# Visit: https://github.com/username/calcloud-back-remote/compare

# After PR review and merge, cleanup
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

## Configuration Management

- **Global Config**: Use Pydantic BaseSettings for environment variables and application configuration
- **Location**: Create `src/config.py` as the main configuration file using `pydantic_settings.BaseSettings`
- **Environment Variables**: All environment variables should be defined as class attributes in the BaseSettings class
- **Configuration Access**: Import and use the config instance throughout the application (`from app.config import settings`)
- **Module-Specific Configs**: Module-specific configs in each domain folder should extend or reference the global
  config
- **Dynamic Attributes**: Add new configuration attributes to the BaseSettings class as needed for new features


## Code Style Guidelines

- **PEP 8**: Follow Python PEP 8 style guide for code formatting
- **Type Hints**: Use type hints for all function parameters, return values, and class attributes
- **Black**: Use Black for automatic code formatting (line length: 88 characters)
- **Import Organization**: Use isort to organize imports (stdlib, third-party, local)
- **Linting**: Use flake8 for code quality checks and style enforcement
- **Docstrings**: Use Google-style docstrings for functions and classes
- **Variable Naming**: Use snake_case for variables and functions, PascalCase for classes

### Code Quality Workflow

ALWAYS run these commands in order after changing code and before committing code:

1. **isort .** - Sorts and organizes imports according to PEP 8
2. **black .** - Formats code consistently (may reformat import lines from isort)
3. **flake8 .** - Checks for style issues, unused imports, and code quality problems

This ensures consistent code style across the entire project. All three tools are required and should pass without
errors before committing.

## Pydantic v2 Guidelines

Use Pydantic v2 with the new Annotated syntax and modern Python typing exclusively:

### Modern Python Typing (Python 3.10+)

Always use the modern union syntax and built-in collections:

```python
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from enum import Enum

# Use built-in types instead of typing imports
# ✅ Good - Modern syntax
list[str]           # instead of List[str]
dict[str, int]      # instead of Dict[str, int]
tuple[str, int]     # instead of Tuple[str, int]
str | None          # instead of Optional[str]
int | str | None    # instead of Union[int, str, None]

# ❌ Bad - Old syntax (don't import these)
from typing import List, Dict, Tuple, Optional, Union
```

### Pydantic v2 with Modern Typing

```python
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from enum import Enum

class StatusEnum(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class UserCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    email: Annotated[str, Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')]
    age: Annotated[int, Field(ge=0, le=120)]
    is_active: Annotated[bool, Field(default=True)]
    status: StatusEnum
    # Use modern union syntax for nullable fields
    bio: Annotated[str | None, Field(default=None, max_length=500)]
    tags: Annotated[list[str], Field(default_factory=list)]
    metadata: Annotated[dict[str, str], Field(default_factory=dict)]
    created_at: Annotated[datetime, Field(default_factory=datetime.utcnow)]

class User(UserCreate):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
```

### Nullable Fields

For nullable/optional fields, use the modern union syntax with `None`:

```python
# ✅ Modern syntax
field: Annotated[str | None, Field(default=None)]
field: Annotated[int | None, Field(default=None)]
field: Annotated[datetime | None, Field(default=None)]

# ❌ Old syntax (avoid)
from typing import Optional
field: Annotated[Optional[str], Field(default=None)]
```

## SQLAlchemy v2 Guidelines

Use SQLAlchemy v2 syntax with Mapped, mapped_column, and modern Python typing:

```python
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"  # Use singular form
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), nullable=False)
    # Use server defaults for timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), server_onupdate=func.now()
    )
    
    # Use modern typing for nullable fields and relationships
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    posts: Mapped[list[Post]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "post"  # Use singular form
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships with modern typing
    user: Mapped[User] = relationship(back_populates="posts")
```

### Modern Typing in SQLAlchemy

```python
# ✅ Modern syntax
field: Mapped[str | None] = mapped_column(String(100), nullable=True)
field: Mapped[int | None] = mapped_column(Integer, nullable=True)
items: Mapped[list[Item]] = relationship(...)
parent: Mapped[Parent | None] = relationship(...)

# ❌ Old syntax (avoid)
from typing import Optional, List
field: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
items: Mapped[List["Item"]] = relationship(...)
```

When implementing:

1. Set up FastAPI project structure with proper dependency injection and SYNC routes
2. Configure SQLAlchemy v2
3. Implement Alembic for database migrations (using alembic commands)
4. Create comprehensive Pytest test suite
5. Configure Docker for deployment
6. Implement proper error handling and validation

## Project Structure

```
fastapi-project
├── alembic/
├── app
│   ├── auth
│   │   ├── router.py
│   │   ├── schemas.py  # pydantic models
│   │   ├── models.py  # db models
│   │   ├── dependencies.py
│   │   ├── config.py  # local configs
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   ├── service.py
│   │   └── utils.py
│   ├── aws
│   │   ├── client.py  # client model for external service communication
│   │   ├── schemas.py
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   └── posts
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   ├── service.py
│   │   └── utils.py
│   ├── config.py  # global configs
│   ├── models.py  # global models
│   ├── exceptions.py  # global exceptions
│   ├── pagination.py  # global module e.g. pagination
│   ├── database.py  # db connection related stuff
│   └── main.py
├── tests/
│   ├── auth
│   ├── aws
│   └── posts
├── templates/
│   └── index.html
├── requirements
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── .env
├── .gitignore
├── logging.ini
└── alembic.ini
```

1. Store all domain directories inside `app` folder
    1. `app/` - highest level of an app, contains common models, configs, and constants, etc.
    2. `app/main.py` - root of the project, which inits the FastAPI app
2. Each package has its own router, schemas, models, etc.
    1. `router.py` - is a core of each module with all the endpoints
    2. `schemas.py` - for pydantic models
    3. `models.py` - for db models
    4. `service.py` - module specific business logic
    5. `dependencies.py` - router dependencies
    6. `constants.py` - module specific constants and error codes
    7. `config.py` - e.g. env vars
    8. `utils.py` - non-business logic functions, e.g. response normalization, data enrichment, etc.
    9. `exceptions.py` - module specific exceptions, e.g. `PostNotFound`, `InvalidUserData`

### Migrations. Alembic

1. Migrations must be static and revertable.
   If your migrations depend on dynamically generated data, then
   make sure the only thing that is dynamic is the data itself, not its structure.
2. Generate migrations with descriptive names & slugs. Slug is required and should explain the changes.
3. Set human-readable file template for new migrations. We use `*date*_*slug*.py` pattern, e.g.
   `2022-08-24_post_content_idx.py`

```
# alembic.ini
file_template = %%(year)d-%%(month).2d-%%(day).2d_%%(slug)s
```

### Set DB naming conventions

Being consistent with names is important. Some rules we followed:

1. lower_case_snake
2. singular form (e.g. `post`, `post_like`, `user_playlist`)
3. group similar tables with module prefix, e.g. `payment_account`, `payment_bill`, `post`, `post_like`
4. stay consistent across tables, but concrete namings are ok, e.g.
    1. use `profile_id` in all tables, but if some of them need only profiles that are creators, use `creator_id`
    2. use `post_id` for all abstract tables like `post_like`, `post_view`, but use concrete naming in relevant modules
       like `course_id` in `chapters.course_id`
5. `_at` suffix for datetime
6. `_date` suffix for date

### SQL-first. Pydantic-second

- It's preferable to do all the complex joins and simple data manipulations with SQL.
- It's preferable to aggregate JSONs in DB for responses with nested objects.
