# MODELS-MASTER.md

# Lamos Chocolate Platform

## Master Data Model Specification

Version: 1.0

---

# Purpose

This document defines all Django models used in the platform.

Every developer must refer to this document before implementing:

* models.py
* migrations
* services
* forms
* serializers
* views
* tests

This document is considered the single source of truth for the database structure.

---

# Global Domain Overview

Customer
│
├── Orders
│   └── OrderItems
│
├── Cart
│   └── CartItems
│
└── BusinessRequests

Category
│
└── Products
├── ProductImages
├── Stock
└── OrderItems

Order
│
├── OrderItems
└── Payment

Forecast
│
└── Alert

---

# ACCOUNTS APPLICATION

## Customer

Represents a platform user.

### Fields

| Field              | Type          |
| ------------------ | ------------- |
| id                 | UUID          |
| email              | EmailField    |
| password           | CharField     |
| first_name         | CharField     |
| last_name          | CharField     |
| phone              | CharField     |
| company_name       | CharField     |
| is_b2b             | BooleanField  |
| is_staff           | BooleanField  |
| is_active          | BooleanField  |
| preferred_language | CharField     |
| created_at         | DateTimeField |
| updated_at         | DateTimeField |

### Constraints

* email must be unique
* email is required

---

# SHOP APPLICATION

## Category

Product category.

### Fields

| Field       | Type          |
| ----------- | ------------- |
| id          | UUID          |
| name        | CharField     |
| slug        | SlugField     |
| description | TextField     |
| created_at  | DateTimeField |
| updated_at  | DateTimeField |

### Constraints

* slug must be unique

---

## Product

Represents a product sold on the platform.

### Fields

| Field             | Type                 |
| ----------------- | -------------------- |
| id                | UUID                 |
| category          | ForeignKey(Category) |
| name              | CharField            |
| slug              | SlugField            |
| short_description | TextField            |
| description       | TextField            |
| price             | DecimalField         |
| weight            | DecimalField         |
| is_active         | BooleanField         |
| created_at        | DateTimeField        |
| updated_at        | DateTimeField        |

### Constraints

* slug must be unique
* price must be greater than zero

---

## ProductImage

Stores product images.

### Fields

| Field      | Type                |
| ---------- | ------------------- |
| id         | UUID                |
| product    | ForeignKey(Product) |
| image      | ImageField          |
| alt_text   | CharField           |
| is_primary | BooleanField        |

---

## Stock

Tracks inventory levels.

### Fields

| Field             | Type                   |
| ----------------- | ---------------------- |
| id                | UUID                   |
| product           | OneToOneField(Product) |
| quantity          | IntegerField           |
| minimum_threshold | IntegerField           |
| updated_at        | DateTimeField          |

### Constraints

* quantity must be greater than or equal to zero

---

# CART APPLICATION

## Cart

Customer shopping cart.

### Fields

| Field      | Type                 |
| ---------- | -------------------- |
| id         | UUID                 |
| customer   | ForeignKey(Customer) |
| created_at | DateTimeField        |
| updated_at | DateTimeField        |

---

## CartItem

Products inside a cart.

### Fields

| Field    | Type                |
| -------- | ------------------- |
| id       | UUID                |
| cart     | ForeignKey(Cart)    |
| product  | ForeignKey(Product) |
| quantity | IntegerField        |

---

# CHECKOUT APPLICATION

## Order

Customer order.

### Fields

| Field            | Type                 |
| ---------------- | -------------------- |
| id               | UUID                 |
| customer         | ForeignKey(Customer) |
| order_number     | CharField            |
| status           | CharField            |
| total_amount     | DecimalField         |
| shipping_address | TextField            |
| billing_address  | TextField            |
| created_at       | DateTimeField        |
| updated_at       | DateTimeField        |

### Status Values

* pending
* paid
* shipped
* delivered
* cancelled

---

## OrderItem

Order line item.

### Fields

| Field      | Type                |
| ---------- | ------------------- |
| id         | UUID                |
| order      | ForeignKey(Order)   |
| product    | ForeignKey(Product) |
| quantity   | IntegerField        |
| unit_price | DecimalField        |

---

## Payment

Stripe payment transaction.

### Fields

| Field                 | Type                 |
| --------------------- | -------------------- |
| id                    | UUID                 |
| order                 | OneToOneField(Order) |
| stripe_payment_intent | CharField            |
| amount                | DecimalField         |
| status                | CharField            |
| paid_at               | DateTimeField        |

### Status Values

* pending
* succeeded
* failed
* refunded

---

# B2B APPLICATION

## BusinessRequest

Professional partnership request.

### Fields

| Field        | Type                 |
| ------------ | -------------------- |
| id           | UUID                 |
| customer     | ForeignKey(Customer) |
| company_name | CharField            |
| contact_name | CharField            |
| email        | EmailField           |
| phone        | CharField            |
| message      | TextField            |
| status       | CharField            |
| created_at   | DateTimeField        |

### Status Values

* pending
* reviewed
* approved
* rejected

---

# FORECASTING APPLICATION

## Forecast

Sales forecast data.

### Fields

| Field              | Type                |
| ------------------ | ------------------- |
| id                 | UUID                |
| product            | ForeignKey(Product) |
| forecast_date      | DateField           |
| predicted_quantity | IntegerField        |
| confidence_score   | DecimalField        |
| created_at         | DateTimeField       |

---

## Alert

Forecast-based inventory alert.

### Fields

| Field      | Type                 |
| ---------- | -------------------- |
| id         | UUID                 |
| product    | ForeignKey(Product)  |
| forecast   | ForeignKey(Forecast) |
| message    | TextField            |
| severity   | CharField            |
| created_at | DateTimeField        |

### Severity Values

* low
* medium
* high
* critical

---

# BACKOFFICE APPLICATION

The backoffice uses:

* Customer
* Category
* Product
* ProductImage
* Stock
* Order
* OrderItem
* Payment
* BusinessRequest
* Forecast
* Alert

No dedicated models required.

---

# CUSTOMER AREA APPLICATION

The customer area uses:

* Customer
* Order
* OrderItem
* Payment

No dedicated models required.

---

# Migration Order

The migration order must follow:

1. accounts
2. shop
3. cart
4. checkout
5. b2b
6. forecasting

---

# Development Rules

Before creating any Django model:

1. Check this document.
2. Verify relationships.
3. Verify constraints.
4. Verify migration dependencies.

This document is the official reference for the project's database architecture.
