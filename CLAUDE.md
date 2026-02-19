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
- **`dependencies.py`** — FastAPI dependency injection: `SessionDep`, `CurrentUserDep`, `ProjectDep`, `OwnerProjectDep`, `ProjectIdDep`. All DB access flows through `get_db()` dependency
- **`middleware.py`** — Custom ASGI middleware: logging, metrics timing, security headers
- **`health.py`** — Health check endpoint at `/health`
- **`core/`** — Configuration (`config.py` with pydantic-settings `Settings`), DB engine/session setup (`db.py`), security utilities (`security.py`), rate limiting (`rate_limiter.py`), custom exceptions (`exceptions.py`), logging config
- **`models/`** — SQLAlchemy 2.0 async models: `User`, `Project`, `APIKey`, `Metric`, `UserProject` (junction table)
- **`schemas/`** — Pydantic v2 request/response schemas
- **`services/`** — Business logic layer: `auth_service`, `user_service`, `project_service`, `api_key_service`, `metric_service`, `member_service`
- **`api/v1/routes/`** — Route handlers organized by domain. Projects sub-router includes `projects.py`, `api_keys.py`, `metrics.py`, `members.py`

### Key Patterns

- **Async everywhere**: All DB operations use `async/await` with `asyncpg`. The session factory is `async_sessionmaker`.
- **Dependency injection**: Routes use FastAPI `Depends()` with typed aliases (`SessionDep`, `CurrentUserDep`, `ProjectDep`). Override `get_db` in tests.
- **Settings via pydantic-settings**: `Settings` class loads from `.env` files based on `ENVIRONMENT` env var. Config is a module-level singleton (`settings = Settings()`).
- **Auth flow**: JWT tokens (HS256) for user auth, API keys (hashed with prefix lookup) for metric tracking via `X-API-Key` header.
- **Multi-tenant**: Users own Projects, Projects have API Keys. The `project_key` URL param identifies projects. All project routes are scoped to the authenticated user.
  - **Ownership**: Each project has exactly one owner stored as `Project.user_id` FK. An owner cannot have two projects with the same name.
  - **Membership**: All user-project relationships (including ownership) are recorded in the `user_projects` junction table with roles: `owner`, `member`, `viewer`. Viewers and members may have access to multiple projects with the same name from different owners.
  - **Access control**: `ProjectDep` grants access to any user with a junction table entry. `OwnerProjectDep` restricts to the project owner only (mutating operations).
  - Project-to-api-key relationship is one-to-many.

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

## Development Standards

### Production-Readiness Contract (Non-Negotiable)

Never optimize for "make it work quickly" over long-term quality. All delivered code must be production ready.

- **Root cause first**: Fix the actual issue, not just symptoms.
- **No hacks**: Do not ship temporary patches, brittle workarounds, TODO-based behavior, or placeholder logic.
- **Safe failure modes**: Handle errors explicitly with meaningful exceptions and messages. Never silently swallow errors.
- **Maintainable by default**: Prefer clear, boring, well-factored solutions over clever shortcuts.
- **Respect existing architecture**: Follow established layering (routes -> services -> models/core) and dependency patterns.
- **Security baseline**: No hardcoded secrets, no leaking sensitive values, and no unsafe shortcuts around auth/authorization.
- **Backward compatibility**: Do not introduce breaking API or data behavior unless the task explicitly requires it.

### Implementation Expectations

- **Readable**: Write code that is clear and self-explanatory. Prefer explicit names over abbreviations.
- **No duplication**: Extract shared logic into helpers or services. Do not copy-paste code blocks.
- **Focused**: Each function or method should do one thing. Keep functions small and purposeful.
- **Consistent**: Follow existing patterns in the codebase (naming conventions, error handling, async style).
- **Typed correctly**: Avoid `Any`-driven shortcuts and type ignores unless absolutely necessary and justified in comments.
- **No hidden behavior changes**: When refactoring, preserve semantics unless the task explicitly asks for behavior changes.

### Testing Requirements

Every code change must be backed by tests that prove behavior and guard against regressions.

- **Unit tests** (`tests/unit/`) for isolated business logic, service methods, and utilities.
- **Integration tests** (`tests/`) for route handlers, DB interactions, and multi-component flows.
- **Bug fixes require regression tests**: Add or update a test that would fail before the fix and pass after it.
- **Coverage scope**: Test happy path, failure path, and authorization/validation boundaries when applicable.

Do not submit a change without a corresponding test that covers the new or modified behavior.

### Validation and Quality Gates

To validate and ensure code standards, use the `code-quality-verifier` subagent to check changes. Don't run these commands yourself; have the subagent run and report:

- `uv run ruff check --fix .`
- `uv run ruff format .`
- `uv run mypy .`
- `uv run pytest`

A task is not complete until these checks pass, tests are relevant to the change, and no new lint/type failures are introduced.

### Explicitly Prohibited Shortcuts

- Disabling lint/type/test checks to force a green result.
- Broad `except Exception` blocks without re-raise or deliberate handling.
- Silently returning fallback values that hide failures.
- Hardcoding environment-specific values in application code.
- Shipping dead code, commented-out production logic, or partial implementations.
