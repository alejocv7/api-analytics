# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

API analytics backend: multi-tenant service for tracking and analyzing API performance metrics. Built with Python 3.14, Pydantic v2.12.5, FastAPI 0.128.0, SQLAlchemy 2.0.45, PostgreSQL (async via SQLAlchemy 2.0 + asyncpg), and Redis (rate limiting).

## Commands

All commands run from `backend/` directory using `uv`:

```bash
# Install dependencies
uv sync --all-extras

# Run tests (uses testcontainers - requires Docker running)
uv run pytest

# Run a single test file or test
uv run pytest tests/test_auth.py
uv run pytest tests/test_auth.py::test_name -k "keyword"

# Lint and type check
uv run ruff check .
uv run mypy .

# Auto-fix lint issues
uv run ruff check --fix .

# Database migrations (requires running Postgres)
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head

# Run app locally via Docker Compose (from repo root)
docker compose up --watch
```

## Architecture

### Workspace Layout

Monorepo with a `uv` workspace. Root `pyproject.toml` declares `backend/` as the only workspace member. All current application code lives under `backend/` with /frontend folder reserved for future use.

### Backend Structure (`backend/app/`)

- **`main.py`** — FastAPI app factory with lifespan, middleware stack, and router registration
- **`dependencies.py`** — FastAPI dependency injection: `SessionDep`, `CurrentUserDep`, `ProjectDep`, `ProjectIdDep`. All DB access flows through `get_db()` dependency
- **`middleware.py`** — Custom ASGI middleware: logging, metrics timing, security headers
- **`health.py`** — Health check endpoint at `/health`
- **`core/`** — Configuration (`config.py` with pydantic-settings `Settings`), DB engine/session setup (`db.py`), security utilities (`security.py`), rate limiting (`rate_limiter.py`), custom exceptions (`exceptions.py`), logging config
- **`models/`** — SQLAlchemy 2.0 async models: `User`, `Project`, `APIKey`, `Metric`
- **`schemas/`** — Pydantic v2 request/response schemas
- **`services/`** — Business logic layer: `auth_service`, `user_service`, `project_service`, `api_key_service`, `metric_service`
- **`api/v1/routes/`** — Route handlers organized by domain. Projects sub-router includes `projects.py`, `api_keys.py`, `metrics.py`

### Key Patterns

- **Async everywhere**: All DB operations use `async/await` with `asyncpg`. The session factory is `async_sessionmaker`.
- **Dependency injection**: Routes use FastAPI `Depends()` with typed aliases (`SessionDep`, `CurrentUserDep`, `ProjectDep`). Override `get_db` in tests.
- **Settings via pydantic-settings**: `Settings` class loads from `.env` files based on `ENVIRONMENT` env var. Config is a module-level singleton (`settings = Settings()`).
- **Auth flow**: JWT tokens (HS256) for user auth, API keys (hashed with prefix lookup) for metric tracking via `X-API-Key` header.
- **Multi-tenant**: Users own Projects, Projects have API Keys. The `project_key` URL param identifies projects. All project routes are scoped to the authenticated user. A project-to-user relationship is many-to-mant. Project-to-api-key relationship is one-to-many.

### Testing

- Tests use **testcontainers** to spin up a real Postgres instance (Docker required).
- `conftest.py` applies Alembic migrations to the test DB at session scope.
- Each test gets a rolled-back transaction via savepoint pattern (`db_session` fixture).
- `tests/factories.py` provides `create_user`, `create_project`, etc.
- Integration tests (top-level `tests/`) use `AsyncClient` with `ASGITransport`. Unit tests live in `tests/unit/`.
- pytest-asyncio in **strict** mode — async tests require `@pytest.mark.asyncio` decorator.
- `ENVIRONMENT=test` is set automatically via `pytest_env`.

### Ruff Lint Rules

Configured in `backend/pyproject.toml`. Notable enforced rules: `DTZ` (datetime timezone safety), `T201` (no print statements), `ARG001` (no unused function args). Alembic directory is excluded.
