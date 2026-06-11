#!/usr/bin/env bash
# Bootstrap the full local stack: build images, start services,
# apply migrations and load seed data.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "No .env found — creating one from .env.example"
    cp .env.example .env
fi

echo "Building and starting containers..."
docker compose up -d --build

echo "Applying migrations..."
docker compose exec -T django python manage.py migrate --noinput

echo "Loading seed data..."
./scripts/seed_db.sh

echo "Setup complete. App available at http://localhost:8000"
