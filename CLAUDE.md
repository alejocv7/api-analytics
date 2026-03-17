# Project Overview

Multi-tenant API analytics backend built with: Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2 async, PostgreSQL (asyncpg), Redis

## Common Commands

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run a single test file or test
uv run pytest tests/test_auth.py

# Lint and type check
uv run ruff check .
uv run mypy .

# Database migrations (requires running docker service from compose)
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head

# Run app locally via Docker Compose (from repo root)
docker compose up --watch
```

## Architecture

### Workspace Layout

Monorepo with `uv` workspace. All app code in `backend/app/`:

| Path              | Purpose                                                                         |
| ----------------- | ------------------------------------------------------------------------------- |
| `main.py`         | App factory, middleware, router registration                                    |
| `dependencies.py` | `SessionDep`, `CurrentUserDep`, `ProjectDep`, `OwnerProjectDep`, `ProjectIdDep` |
| `middleware.py`   | Logging, metrics timing, security headers                                       |
| `core/`           | Config, DB setup, security, rate limiting, exceptions, logging                  |
| `models/`         | `User`, `Project`, `APIKey`, `Metric`, `UserProject`                            |
| `schemas/`        | Pydantic v2 request/response schemas                                            |
| `services/`       | Business logic (auth, user, project, api_key, metric, member)                   |
| `api/v1/routes/`  | Route handlers (projects, api_keys, metrics, members)                           |

### Key Patterns

- Async everywhere via `asyncpg` and `async_sessionmaker`
- All DB access through `get_db()` dependency injection; override in tests
- Config via pydantic-settings `Settings` singleton, loaded from `.env` by `ENVIRONMENT`
- Auth: JWT (HS256) for users, hashed API keys with prefix lookup via `X-API-Key`
- Multi-tenancy: Users own Projects (one owner per project, unique name per owner). All relationships including ownership recorded in `user_projects` junction table with roles `owner`/`member`/`viewer`. `ProjectDep` = any member; `OwnerProjectDep` = owner only.

## Testing

- Real Postgres via **testcontainers** (Docker required); Alembic migrations at session scope
- Each test gets a rolled-back transaction via savepoint (`db_session` fixture)
- Factories in `tests/factories.py`; integration tests use `AsyncClient` + `ASGITransport`
- pytest-asyncio **strict** mode — async tests need `@pytest.mark.asyncio`
- `ENVIRONMENT=test` set automatically via `pytest_env`
- Ruff rules: `DTZ`, `T201` (no print), `ARG001` (no unused args); Alembic excluded

## Standards

**Production-readiness (non-negotiable):** Fix root causes, not symptoms. No hacks, TODOs, or placeholder logic. Handle errors explicitly — never swallow them or return fallback values that hide failures. No hardcoded secrets or auth shortcuts. No breaking changes unless explicitly required.

**Architecture:**

- Routes are thin — validate input, call a service, return a response. No business logic in routes.
- Services are stateless and own all business logic. Be explicit about side effects (DB, network, I/O).
- Prefer composition over inheritance. Introduce abstractions only when they remove real duplication or hide genuine complexity — don't over-engineer.
- Depend on abstractions (`Protocol` types) over concretions where dependencies could vary or be mocked.
- Avoid primitive obsession — wrap meaningful domain values in types.
- Follow existing layering strictly: routes → services → models/core.
- When in doubt, prefer the boring solution.

**Code quality:**

- Single-responsibility functions and modules.
- Use explicit, descriptive names — no abbreviations, no comments to explain what a name should.
- Do not duplicate logic; extract shared helpers or services.
- When refactoring, preserve behavior unless explicitly instructed otherwise.

**Testing:** Every change needs tests. Unit tests (`tests/unit/`) for logic and services. Integration tests (`tests/integration/`) for routes and DB. Bug fixes need a regression test that fails before the fix and passes after. Cover happy path, failure path, and auth/validation boundaries.

**Quality gates** (run via `code-quality-verifier` subagent, not directly):

```bash
uv run ruff check --fix .
uv run ruff format .
uv run mypy .
uv run pytest
```

A task is not done until all four pass with no new failures.

**Prohibited:**

- Disabling lint, type, or test checks
- `except Exception` without deliberate handling or re-raise
- Silent fallback values that hide failures
- Hardcoded environment-specific values
- Dead code, commented-out production logic, or partial implementations
- Changing public API or data contracts without explicit instruction
- `Any` type shortcuts unless all possible options are exhausted
