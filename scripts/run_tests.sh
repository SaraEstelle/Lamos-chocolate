#!/usr/bin/env bash
# Run the test suite (pytest) with coverage inside the django container.
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose exec -T django pytest --cov=apps --cov-report=term-missing "$@"
