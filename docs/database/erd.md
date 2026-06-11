# Entity-Relationship Diagram

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
        bigint id PK
        varchar name_fr
        varchar name_en
        varchar slug UK
        timestamptz created_at
    }
    products {
        bigint id PK
        varchar slug UK
        varchar name_fr
        varchar name_en
        text description_fr
        text description_en
        text ingredients_fr
        text ingredients_en
        varchar allergens_fr
        varchar allergens_en
        bigint category_id FK
        varchar image_url
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }
    skus {
        bigint id PK
        bigint product_id FK
        varchar sku_code UK
        varchar format
        int weight_g
        decimal price
        varchar currency
        boolean is_active
        int production_delay_days
        int batch_size
        timestamptz created_at
    }
    stock {
        bigint id PK
        bigint sku_id FK "UNIQUE 1:1"
        int quantity
        int threshold_alert
        timestamptz updated_at
        bigint updated_by_id FK "SET NULL"
    }
    shipping_zones {
        bigint id PK
        varchar zone_name
        varchar_array countries
        int delay_days
        decimal cost
    }
    customers {
        bigint id PK
        varchar email UK
        varchar password_hash
        varchar language_pref
        boolean is_active
        timestamptz created_at
        timestamptz last_login
    }
    orders {
        bigint id PK
        bigint customer_id FK "RESTRICT"
        varchar order_number UK
        varchar status
        decimal total_amount
        varchar currency
        varchar stripe_payment_id
        int estimated_delivery_days
        timestamptz created_at
        timestamptz updated_at
    }
    order_items {
        bigint id PK
        bigint order_id FK "CASCADE"
        bigint sku_id FK "RESTRICT"
        int quantity
        decimal unit_price
        decimal subtotal
    }
    admin_users {
        bigint id PK
        varchar email UK
        varchar password_hash
        varchar role
        boolean is_active
        timestamptz created_at
    }
    b2b_requests {
        bigint id PK
        varchar company_name
        varchar contact_email
        varchar status
        inet ip_address
        timestamptz created_at
        bigint processed_by_id FK "SET NULL"
    }
    password_reset_tokens {
        bigint id PK
        bigint customer_id FK "CASCADE"
        varchar token UK
        timestamptz expires_at
        boolean used
        timestamptz created_at
    }
```

> A more detailed conceptual ERD (with native ENUM types and SQL-standard
> identity columns) is kept in [`../diagrams_erd.md`](../diagrams_erd.md).
> This file reflects the Django implementation (`BigAutoField` PKs,
> `TextChoices` stored as `varchar`).
