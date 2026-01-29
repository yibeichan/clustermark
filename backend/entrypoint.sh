#!/bin/bash
set -e

echo "Waiting for database to be ready..."
# Wait for database port to be available
while ! nc -z db 5432; do
  sleep 0.5
done
echo "Database port is open, waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be fully ready (handles recovery after crash)
export PGPASSWORD=clustermark
until psql -h db -U clustermark -d clustermark -c '\q' 2>/dev/null; do
  echo "PostgreSQL is not ready yet, waiting..."
  sleep 2
done
echo "Database is ready!"

echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete!"

echo "Importing speaker data..."
python scripts/import_speakers.py
echo "Speaker import complete!"

echo "Starting application..."
exec "$@"
