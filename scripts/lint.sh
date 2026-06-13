#!/usr/bin/env bash
# Check code style without modifying files (isort, black, flake8).
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose exec -T django isort --check-only --diff .
docker compose exec -T django black --check --diff .
docker compose exec -T django flake8 .
