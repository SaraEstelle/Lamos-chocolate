# Entity-Relationship Diagram (ERD)

## Complete Database Schema

```mermaid
erDiagram
    categories ||--o{ products : "has"
    products ||--o{ skus : "has formats"
    skus ||--|| stock : "tracked by"
    skus ||--o{ order_items : "ordered as"
    orders ||--o{ order_items : "contains"
    customers ||--o{ orders : "places"
    customers ||--o{ password_reset_tokens : "requests"
    admin_users ||--o{ b2b_requests : "processes"
    admin_users ||--o{ stock : "updates"

    categories {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        varchar name_fr "NOT NULL"
        varchar name_en "NOT NULL"
        varchar slug UK "UNIQUE"
        timestamptz created_at "DEFAULT NOW()"
    }

    products {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        varchar slug UK "UNIQUE"
        varchar name_fr "NOT NULL"
        varchar name_en "NOT NULL"
        text description_fr
        text description_en
        text ingredients_fr
        text ingredients_en
        varchar allergens_fr
        varchar allergens_en
        int category_id FK "REFERENCES categories"
        varchar image_url
        boolean is_active "DEFAULT TRUE"
        timestamptz created_at "DEFAULT NOW()"
        timestamptz updated_at "AUTO-UPDATE trigger"
    }

    skus {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        int product_id FK "REFERENCES products CASCADE"
        varchar sku_code UK "UNIQUE"
        varchar format "NOT NULL"
        int weight_g
        decimal price "NOT NULL"
        currency_type currency "DEFAULT EUR"
        boolean is_active "DEFAULT TRUE"
        int production_delay_days "DEFAULT 7 (forecasting)"
        int batch_size "DEFAULT 50 (forecasting)"
        timestamptz created_at "DEFAULT NOW()"
    }

    stock {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        int sku_id FK "UNIQUE REFERENCES skus CASCADE"
        int quantity "CHECK >= 0"
        int threshold_alert "DEFAULT 5"
        timestamptz updated_at "AUTO-UPDATE trigger"
        int updated_by FK "REFERENCES admin_users SET NULL"
    }

    shipping_zones {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        varchar zone_name "NOT NULL"
        text_array countries "PostgreSQL ARRAY"
        int delay_days "DEFAULT 5"
        decimal cost "DEFAULT 0"
    }

    customers {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        varchar first_name "NOT NULL"
        varchar last_name "NOT NULL"
        varchar email UK "UNIQUE NOT NULL"
        varchar password_hash "NOT NULL"
        varchar phone
        varchar address_line1
        varchar address_line2
        varchar city
        varchar postal_code
        varchar country
        language_type language_pref "DEFAULT fr"
        boolean is_active "DEFAULT TRUE"
        timestamptz created_at "DEFAULT NOW()"
        timestamptz last_login
    }

    orders {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        int customer_id FK "REFERENCES customers RESTRICT"
        varchar order_number UK "UNIQUE NOT NULL"
        order_status status "DEFAULT pending"
        decimal total_amount "NOT NULL"
        currency_type currency "DEFAULT EUR"
        varchar stripe_payment_id
        varchar stripe_session_id
        varchar shipping_first_name
        varchar shipping_last_name
        varchar shipping_address1
        varchar shipping_address2
        varchar shipping_city
        varchar shipping_postal_code
        varchar shipping_country
        language_type language "DEFAULT fr"
        text notes
        int estimated_delivery_days "(forecasting)"
        timestamptz created_at "DEFAULT NOW()"
        timestamptz updated_at "AUTO-UPDATE trigger"
    }

    order_items {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        int order_id FK "REFERENCES orders CASCADE"
        int sku_id FK "REFERENCES skus RESTRICT"
        int quantity "CHECK > 0"
        decimal unit_price "NOT NULL"
        decimal subtotal "NOT NULL"
    }

    admin_users {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        varchar email UK "UNIQUE NOT NULL"
        varchar password_hash "NOT NULL"
        varchar first_name
        varchar last_name
        admin_role role "DEFAULT admin"
        boolean is_active "DEFAULT TRUE"
        timestamptz created_at "DEFAULT NOW()"
        timestamptz last_login
    }

    b2b_requests {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        varchar company_name "NOT NULL"
        varchar contact_name "NOT NULL"
        varchar contact_email "NOT NULL"
        varchar contact_phone
        varchar sector
        int estimated_qty
        varchar occasion
        text message
        b2b_status status "DEFAULT new"
        language_type language "DEFAULT fr"
        inet ip_address "PostgreSQL INET type"
        timestamptz created_at "DEFAULT NOW()"
        timestamptz processed_at
        int processed_by FK "REFERENCES admin_users SET NULL"
    }

    password_reset_tokens {
        int id PK "GENERATED ALWAYS AS IDENTITY"
        int customer_id FK "REFERENCES customers CASCADE"
        varchar token UK "UNIQUE NOT NULL"
        timestamptz expires_at "NOT NULL"
        boolean used "DEFAULT FALSE"
        timestamptz created_at "DEFAULT NOW()"
    }
```

## PostgreSQL-Specific Features Used

| Feature | Table | Usage |
|---------|-------|-------|
| `GENERATED ALWAYS AS IDENTITY` | All tables | Auto-increment PKs (SQL standard) |
| `CREATE TYPE AS ENUM` | Global | `currency_type`, `order_status`, `b2b_status`, `admin_role`, `language_type` |
| `TEXT[]` (Array) | `shipping_zones` | Country codes list with GIN index |
| `INET` | `b2b_requests` | IPv4/IPv6 storage |
| `TIMESTAMPTZ` | All tables | Timezone-aware timestamps |
| Trigger `update_updated_at()` | `products`, `stock`, `orders` | Automatic `updated_at` on UPDATE |
| Partial Index | `orders`, `password_reset_tokens` | Performance on active records only |
| `CHECK` constraint | `stock`, `order_items` | Data integrity (`quantity >= 0`) |
| `ON DELETE RESTRICT` | `orders → customers` | Prevent accidental customer deletion |
| `ON DELETE CASCADE` | `order_items → orders` | Cascade delete order items with order |
| `ON DELETE SET NULL` | `stock → admin_users` | Keep stock record if admin deleted |
