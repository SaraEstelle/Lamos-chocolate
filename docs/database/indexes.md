# Indexes

Beyond the implicit indexes Django creates for primary keys, unique fields and
foreign keys, the following explicit indexes are declared in the models.

## Unique constraints (implicit unique index)

| Table | Column |
|-------|--------|
| `categories` | `slug` |
| `products` | `slug` |
| `skus` | `sku_code` |
| `stock` | `sku_id` (OneToOne) |
| `customers` | `email` |
| `orders` | `order_number` |
| `admin_users` | `email` |
| `password_reset_tokens` | `token` |

## Declared `Meta.indexes`

| Table | Fields | Purpose |
|-------|--------|---------|
| `products` | `is_active`, `-created_at` | Active catalog listing, newest first |
| `customers` | `email` | Login / lookup by email |
| `orders` | `status` | Backoffice filtering by status |
| `orders` | `customer` | Customer order history |
| `orders` | `-created_at` | Recent orders listing |
| `b2b_requests` | `status` | Backoffice lead filtering |
| `b2b_requests` | `-created_at` | Recent leads listing |

## Partial index

`password_reset_tokens` declares a **partial index** named
`idx_reset_tokens_valid` on `token` with the condition `used = false`. Only
unused tokens are indexed, which keeps the index small and fast for the only
query that matters: validating a fresh token.

```python
models.Index(
    fields=["token"],
    condition=models.Q(used=False),
    name="idx_reset_tokens_valid",
)
```

## Foreign key indexes

PostgreSQL does not auto-index FK columns, but Django does. Every FK
(`product_id`, `category_id`, `customer_id`, `order_id`, `sku_id`,
`updated_by_id`, `processed_by_id`) therefore has its own b-tree index.

## Array search (future)

`shipping_zones.countries` is a `varchar[]`. Lookups use `countries__contains`.
A GIN index can be added later if the table grows; with a handful of zones a
sequential scan is currently cheaper. The `pg_trgm` extension is enabled
(see `init.sql`) for future fuzzy product search.
