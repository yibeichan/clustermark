#!/bin/bash
set -e

echo "Waiting for database to be ready..."
# Wait for database to be available
while ! nc -z db 5432; do
  sleep 0.5
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
