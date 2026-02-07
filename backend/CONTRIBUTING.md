# Contributing to API Analytics

Thank you for your interest in contributing! We want to make contributing to this project as easy and transparent as possible.

## Development Workflow

### 1. Environment Setup

We use **Docker Compose** for the entire local development stack (Database, Redis, and Backend).

1.  **Clone the repository**:

    ```bash
    git clone <repository_url>
    cd api-analytics
    ```

2.  **Create Environment Variables**:
    Copy the example environment file (or create one):

    ```bash
    cp .env.example .env
    ```

    Ensure you set secure values for `SECURITY_KEY`, `POSTGRES_PASSWORD`, etc.

3.  **Start Services**:
    ```bash
    docker compose up --watch
    ```
    This will start Postgres, Redis, and the FastAPI backend. Changes to your code will automatically sync to the container and trigger a reload.

### 2. Local Python Setup (Optional / for Testing)

Use `uv` to manage dependencies:

```bash
cd backend
uv sync --all-extras
```

You can now run `uv run` to execute commands:

```bash
cd backend
uv run pytest
uv run ruff check .
uv run mypy .
...
```

### 3. Making Changes

1.  Create a new branch for your feature or fix: `git checkout -b feature/my-new-feature`.
2.  Write clean, maintainable code.
3.  Add tests for your changes.
4.  Ensure existing tests pass.

## Testing

We use `pytest` for our test suite. All new features **must** include tests.

**Run all tests:**

```bash
cd backend
uv run pytest
```

**Run with coverage:**

```bash
cd backend
uv run pytest --cov=app --cov-report=term-missing
```

## Code Quality

We use modern Python tooling to ensure code quality:

- **Ruff** for linting and formatting.
- **Mypy** for static type checking.

Run checks before submitting a PR:

```bash
cd backend
uv run ruff check .
uv run mypy .
```

## Database Migrations

If you modify `app/models`, you must generate a migration script using Alembic.

1.  **Generate Migration**:

    ```bash
    cd backend
    uv run alembic revision --autogenerate -m "Describe your changes"
    ```

2.  **Review Migration**: Check the generated file in `backend/alembic/versions/`.

3.  **Apply Migration** (Locally):
    ```bash
    uv run alembic upgrade head
    ```

## Pull Request Guidelines

1.  Keep PRs small and focused on a single change.
2.  Update documentation if you change behavior or add features.
3.  Ensure the CI pipeline passes (tests, linting).
4.  Describe your changes clearly in the PR description.

## License

By contributing, you agree that your contributions will be licensed under the project's [AGPL-3.0 License](../README.md#license).
