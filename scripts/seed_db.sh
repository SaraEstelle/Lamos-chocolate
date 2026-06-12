#!/usr/bin/env bash
# Load development seed data (fixtures) into the database.
set -euo pipefail

cd "$(dirname "$0")/.."

FIXTURES=(
    apps/shop/fixtures/categories.json
    apps/shop/fixtures/products.json
    apps/shop/fixtures/product_images.json
    apps/shop/fixtures/skus.json
    apps/shop/fixtures/stock.json
    apps/shop/fixtures/shipping_zones.json
)

echo "Loading fixtures..."
docker compose exec -T django python manage.py loaddata "${FIXTURES[@]}"

echo "Seed data loaded."
