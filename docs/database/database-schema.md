# Database Schema

PostgreSQL 16 schema for the Lamos Chocolate platform, implemented through
Django 5.x models. Models are split across apps but map to flat table names
via each model's `Meta.db_table`.

## Apps → models → tables

| App | Model | Table |
|-----|-------|-------|
| `shop` | Category | `categories` |
| `shop` | Product | `products` |
| `shop` | SKU | `skus` |
| `shop` | Stock | `stock` |
| `shop` | ShippingZone | `shipping_zones` |
| `accounts` | Customer | `customers` |
| `accounts` | PasswordResetToken | `password_reset_tokens` |
| `checkout` | Order | `orders` |
| `checkout` | OrderItem | `order_items` |
| `b2b` | B2BRequest | `b2b_requests` |
| `backoffice` | AdminUser | `admin_users` |

Shared enum-like choices (`CurrencyChoices`, `LanguageChoices`,
`OrderStatusChoices`, `B2BStatusChoices`, `AdminRoleChoices`) live in
`apps/common/constants.py` and are reused across apps.

## Catalog

- **Category** — bilingual (`name_fr`/`name_en`), unique `slug`.
- **Product** — bilingual name/description/ingredients/allergens, FK to
  Category (`RESTRICT`), `is_active` soft-delete flag.
- **SKU** — a sellable format of a product (200g / 80g / 45g…). Holds price,
  currency, and the two forecasting columns `production_delay_days` and
  `batch_size`. FK to Product (`CASCADE`).
- **Stock** — 1:1 with SKU. `quantity`, `threshold_alert`, and an optional
  `updated_by` FK to `backoffice.AdminUser` (`SET NULL`). Helper methods:
  `is_low`, `decrement()`, `increment()`.
- **ShippingZone** — `countries` is a PostgreSQL `ArrayField` of ISO codes;
  `get_zone_for_country()` resolves a zone via `countries__contains`.

## Customers & auth

- **Customer** — standalone model (NOT Django's `AUTH_USER_MODEL`). Passwords
  are stored in `password_hash` via `set_password()` / `check_password()`
  (PBKDF2 through `django.contrib.auth.hashers`).
- **PasswordResetToken** — FK to Customer (`CASCADE`), 1-hour expiry,
  `is_valid` property, `create_for_customer()` factory.

## Orders

- **Order** — FK to `accounts.Customer` (`RESTRICT`), unique `order_number`
  (`LM-YYYYMMDD-XXXXX` via `generate_order_number()`), status, Stripe ids,
  denormalized shipping address snapshot, `estimated_delivery_days`.
- **OrderItem** — FK to Order (`CASCADE`) and `shop.SKU` (`RESTRICT`).
  `subtotal` is recomputed (`quantity * unit_price`) on every save — an
  immutable price snapshot at purchase time.

## B2B & admin

- **AdminUser** — backoffice users with `role` (superadmin/admin/viewer),
  separate from customers, own password hashing.
- **B2BRequest** — corporate gifting leads, status workflow
  (new → in_progress → converted/refused), `ip_address` (`GenericIPAddressField`),
  optional `processed_by` FK to AdminUser (`SET NULL`).

## Cross-app foreign keys

These FKs use string references to avoid circular imports:

- `shop.Stock.updated_by → "backoffice.AdminUser"`
- `checkout.Order.customer → "accounts.Customer"`
- `checkout.OrderItem.sku → "shop.SKU"`
- `b2b.B2BRequest.processed_by → "backoffice.AdminUser"`

See [erd.md](erd.md) for the full entity-relationship diagram and
[indexes.md](indexes.md) for the index strategy.
