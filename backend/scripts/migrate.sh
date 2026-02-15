#!/bin/bash
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Running seed data..."
python -m app.core.seed

echo "Migrations and seeding completed."
