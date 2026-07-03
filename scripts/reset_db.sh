#!/usr/bin/env bash
# DESTRUCTIVE: drop the database volume, then recreate, migrate and reseed.
set -euo pipefail

cd "$(dirname "$0")/.."

read -r -p "This will DESTROY all database data. Continue? [y/N] " answer
case "$answer" in
    [yY][eE][sS]|[yY]) ;;
    *) echo "Aborted."; exit 1 ;;
esac

echo "Removing containers and database volume..."
docker compose down -v

echo "Rebuilding stack..."
docker compose up -d --build

echo "Applying migrations..."
docker compose exec -T django python manage.py migrate --noinput

echo "Reloading seed data..."
./scripts/seed_db.sh

echo "Database reset complete."
