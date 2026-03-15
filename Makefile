.PHONY: dev down \
        be-dev be-test be-lint be-format be-typecheck be-check \
        fe-dev fe-lint fe-build

# ── Docker ────────────────────────────────────────────────────────────────────

dev:
	docker compose up --watch

down:
	docker compose down

# ── Backend ───────────────────────────────────────────────────────────────────

be-dev:
	cd backend && uv run fastapi dev app/main.py

be-test:
	cd backend && uv run pytest

be-lint:
	cd backend && uv run ruff check .

be-format:
	cd backend && uv run ruff format .

be-typecheck:
	cd backend && uv run mypy .

be-check: be-lint be-typecheck be-test

# ── Frontend ──────────────────────────────────────────────────────────────────

fe-dev:
	cd frontend && npm run dev

fe-lint:
	cd frontend && npm run lint

fe-build:
	cd frontend && npm run build
