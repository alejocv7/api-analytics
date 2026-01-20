# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

WORKDIR /app

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
RUN uv sync --locked --no-cache

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Switch to non-root user
USER nonroot

# Run the application.
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "80", "--host", "0.0.0.0"]