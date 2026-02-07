# API Analytics Service

A production-ready, high-performance API analytics backend built with Python 3.14, FastAPI, and PostgreSQL. Track, analyze, and visualize your API performance metrics with ease.

## 🚀 Key Features

- **Multi-tenant Architecture**: Support for multiple users and projects.
- **Secure API Key Management**: Hash-based API key storage with rotation support.
- **High-Performance Tracking**: Asynchronous metric recording using FastAPIs background tasks.
- **Advanced Analytics**: Aggregated statistics for response times, error rates, and throughput.
- **Time-Series Data**: Granular time-series analysis (minute, hour, day).
- **Production Observability**:
  - Structured JSON logging with request tracing (ContextVar-based correlation IDs).
  - Performance monitoring middleware (APM-like timing).
- **Security First**:
  - Argon2 password hashing.
  - IP hashing for privacy-preserving user tracking.
  - Rate limiting using Redis.
- **Scalable Infrastructure**: Containerized with Docker and Docker Compose.

---

## 🛠 Tech Stack

- **Languge**: Python 3.14
- **Framework**: FastAPI (Pydantic v2)
- **Database**: PostgreSQL (SQLAlchemy 2.0 + AsyncPG)
- **Cache/RL**: Redis
- **Tooling**: `uv` (Fast package management)
- **Logging**: `python-json-logger`, `colorlog`

---

## 🏁 Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- _Optional_: [uv](https://github.com/astral-sh/uv) (for running tests/linting outside Docker)

### 2. Local Development (Docker Compose)

We use Docker Compose as the primary way to run the application locally. This sets up Postgres, Redis, and the FastAPI application in a production-like environment.

```bash
docker compose up --watch
```

- **API**: [http://localhost:8000](http://localhost:8000)
- **Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Running Tests (Local)

To run the test suite, you can use `uv` in the backend directory:

```bash
cd backend
uv run pytest
```

### 4. Database Migration Workflow

This workflow helps you manage database schema changes using Alembic.

1. **Navigate to Backend Directory**

   ```bash
   cd backend
   ```

2. **Create a new migration**

   Run this when you change your models in `app/models.py`.

   ```bash
   uv run alembic revision --autogenerate -m "description of change"
   ```

3. **Apply migrations**

   Run this to apply all pending migrations to your database.

   ```bash
   uv run alembic upgrade head
   ```

4. **Check current migration status**
   ```bash
   uv run alembic current
   ```
5. **Rollback last migration**
   ```bash
   uv run alembic downgrade -1
   ```

## 🔌 API Documentation

Detailed OpenAPI documentation is available at `/docs` or `/redoc`.

### Core Endpoints

| Category     | Endpoint                                             | Method            | Description                          |
| :----------- | :--------------------------------------------------- | :---------------- | :----------------------------------- |
| **Auth**     | `/api/v1/auth/register`                              | `POST`            | Create a new user account            |
| **Auth**     | `/api/v1/auth/login`                                 | `POST`            | Get JWT access token                 |
| **Projects** | `/api/v1/projects/`                                  | `GET/POST`        | Manage projects                      |
| **API Keys** | `/api/v1/projects/{project-key}/api-keys/`           | `GET/POST/DELETE` | Manage API keys for a project        |
| **Metrics**  | `/api/v1/projects/{project-key}/metrics/summary`     | `GET`             | Overall project statistics           |
| **Metrics**  | `/api/v1/projects/{project-key}/metrics/time-series` | `GET`             | Aggregated data for charts           |
| **Tracking** | `/api/v1/track`                                      | `POST`            | Record a metric (requires X-API-Key) |

---

## 📊 Monitoring & Observability

### Structured Logging

Logs are output in JSON format (non-local environments) and include:

- `timestamp`: UTC ISO format.
- `levelname`: INFO, ERROR, etc.
- `request_id`: Correlation ID to trace a single request across all logs.
- `message`: Log content.

### Health Checks

A comprehensive health check endpoint is available at `/health` providing:

- Overall status (online/offline).
- Database connectivity status.
- Application version.
- Environment info.

---

## 🧹 Data Management

### Retention Policy

The service includes a maintenance utility to purge old data:

```python
# To manually trigger cleanup (e.g. older than 90 days)
from app.services.metric_service import cleanup_old_metrics
await cleanup_old_metrics(session, retention_days=90)
```

---

## 🧪 Testing

```bash
cd backend
uv run pytest --cov=app --cov-report=term-missing
```

## ⚖️ License

AGPL-3.0
