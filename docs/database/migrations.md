# Migrations

Initial migrations exist for every app that owns models:

| App | Migration | Creates |
|-----|-----------|---------|
| `accounts` | `0001_initial` | Customer, PasswordResetToken |
| `backoffice` | `0001_initial` | AdminUser |
| `shop` | `0001_initial` | Category, ShippingZone, Product, SKU, Stock |
| `b2b` | `0001_initial` | B2BRequest |
| `checkout` | `0001_initial` | Order, OrderItem |

The apps without models (`common`, `main`, `cart`, `customer_area`,
`forecasting`) have an empty `migrations/` package and produce no migration.

## Dependency order

Django resolves dependencies automatically from the cross-app foreign keys:

- `shop` depends on `backoffice` (`Stock.updated_by → AdminUser`)
- `b2b` depends on `backoffice` (`B2BRequest.processed_by → AdminUser`)
- `checkout` depends on `accounts` (`Order.customer`) and `shop`
  (`OrderItem.sku`)

So a fresh `migrate` applies them in an order such as:
`backoffice → accounts → shop → b2b → checkout` (interleaved with Django's
own `contenttypes`, `auth`, `sessions`, `admin`).

## Commands

```bash
# Generate migrations after changing a model
docker compose exec django python manage.py makemigrations

# Apply migrations (also run automatically by the entrypoint on boot)
docker compose exec django python manage.py migrate

# Inspect state
docker compose exec django python manage.py showmigrations
```

The Docker entrypoint (`infrastructure/docker/django/entrypoint.sh`) waits for
PostgreSQL, then runs `migrate --noinput` before starting the server, so a
fresh `docker compose up` lands a fully migrated database with no manual step.

## Conventions

- Never edit a migration that has already been shared/applied; add a new one.
- Keep migrations committed to the repo — they are the source of truth for the
  schema, not an artifact.
