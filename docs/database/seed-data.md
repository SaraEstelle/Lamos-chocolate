# Seed Data

Development seed data lives as Django fixtures under
`backend/apps/shop/fixtures/` and is loaded by `scripts/seed_db.sh`.

## Fixtures

| File | Model | Rows |
|------|-------|------|
| `categories.json` | shop.Category | 3 (Tablettes, Coffrets, Pralinés) |
| `products.json` | shop.Product | 5 (pistache, café, matcha, praliné pécan, coffret) |
| `skus.json` | shop.SKU | 7 |
| `stock.json` | shop.Stock | 7 |
| `shipping_zones.json` | shop.ShippingZone | 3 (France, UE, Suisse) |

Total: **25 objects**.

## Load order

Fixtures must be loaded respecting FK dependencies:

```
categories → products → skus → stock
shipping_zones (independent)
```

`scripts/seed_db.sh` passes them to `loaddata` in this order.

## Important: explicit timestamps

`loaddata` saves objects with `raw=True`, which **bypasses** `auto_now_add`
and `auto_now`. Any `NOT NULL` timestamp column (`created_at`, `updated_at`)
must therefore be set explicitly in the fixture, otherwise PostgreSQL raises a
`NotNullViolation`. All fixtures here include the relevant timestamps.

## Sample data highlights

The stock values are intentionally varied to exercise the forecasting model:

- `PIST-45` has `quantity = 4`, `threshold_alert = 25` → flagged **low stock**.
- `PECAN-150` has `quantity = 0` → flagged **low stock** (full production lead
  time on order).
- A 30-unit order of `PIST-45` shipped to Switzerland estimates **12 days**
  (1 production batch × 5 days + 7 days shipping).

## Usage

```bash
# Load (stack must be up)
./scripts/seed_db.sh

# Reload from scratch (DESTRUCTIVE — drops the volume)
./scripts/reset_db.sh
```
