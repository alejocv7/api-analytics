FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

ENV PYTHONUNBUFFERED=1

LABEL org.opencontainers.image.source="https://github.com/alejo/api-analytics"
LABEL org.opencontainers.image.description="API Analytics Service"

# Setup a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

WORKDIR /app/backend

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/backend/.venv/bin:$PATH"

# Install dependencies only — app code excluded to maximise layer cache reuse.
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the application into the container
COPY pyproject.toml alembic.ini README.md ./
COPY scripts ./scripts
COPY alembic ./alembic
COPY app ./app

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Switch to non-root user
USER nonroot

# Run the application
CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
