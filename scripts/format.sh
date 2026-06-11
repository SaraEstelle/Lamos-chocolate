#!/usr/bin/env bash
# Auto-format the backend code with isort + black.
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose exec -T django isort .
docker compose exec -T django black .
