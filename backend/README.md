# API Analytics Service - Backend

This directory contains the FastAPI backend for the API Analytics Service.

For comprehensive project documentation, setup guides, and architectural overview, please refer to the [Root README](../README.md).

## Local Development Quick Start

```bash
uv sync --all-extras
PYTHONPATH=. uv run alembic upgrade head
PYTHONPATH=. uv run fastapi dev app/main.py
```
