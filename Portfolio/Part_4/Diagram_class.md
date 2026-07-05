# Class Diagram — single, complete, corrected

## What changed vs the design doc (and why)
The old diagram had two problems:
1. **A fictional `BaseModel`** that all models "inherited" from. It does not exist in the code
   (`apps/common/models.py` has no models, `mixins.py` is empty, and timestamp fields differ
   from model to model — proof there is no shared base). Removed.
2. **Two separate diagrams** (one for auth inheritance, one for the domain), which was
   confusing and left `Customer` shown as an empty box in the domain view.

This is now **one diagram**: every class carries its real attributes and methods, the real
inheritance is shown inline (`Customer` extends Django's auth classes).

## How to read it
- `+attr` = attribute, `+method()` = method. `<|--` = inheritance. `*--` = composition (the
  part cannot exist without the whole). `o--` = aggregation/association. `"1"`, `"*"`, `"0..1"`
  = multiplicity.

```mermaid
classDiagram
    class AbstractBaseUser
    class PermissionsMixin
    class BaseUserManager

    class CustomerManager {
        +create_user(email, password)
        +create_superuser(email, password)
    }
    class Customer {
        +UUID id
        +str email  «USERNAME_FIELD, unique»
        +str first_name
        +str last_name
        +str phone
        +bool is_b2b
        +str customer_type
        +str canton
        +str npa
        +bool consent_nlpd
        +datetime consent_nlpd_at
        +bool is_active
        +bool is_staff
        +datetime created_at
        +set_password(raw)  «PBKDF2 hash»
    }
    class B2BAccount {
        +UUID id
        +str company_name
        +str segment
        +str status  «prospect→active»
        +datetime onboarded_at
    }
    class ConsentLog {
        +UUID id
        +bool necessary
        +bool analytics
        +bool marketing
        +str policy_version
        +inet ip_address
        +str user_agent
        +datetime created_at  «immutable»
    }
    class PasswordResetToken {
        +UUID id
        +str token  «unique»
        +datetime expires_at
        +bool is_used
    }
    class CustomerAddress {
        +UUID id
        +str full_name
        +str line1
        +str city
        +str postal_code
        +str canton
        +str country
        +bool is_default
    }

    class Category {
        +int id
        +str name_fr
        +str name_en
        +str slug  «unique»
    }
    class Product {
        +int id
        +str slug  «unique»
        +str name_fr
        +str name_en
        +text description_fr
        +bool is_active
        +primary_image_url()
    }
    class ProductImage {
        +UUID id
        +str image_url
        +str alt_text
        +bool is_primary
    }
    class SKU {
        +int id
        +str sku_code  «unique»
        +str format
        +decimal price
        +str currency = CHF
        +decimal cost_chf
        +str flavor
        +int production_delay_days
        +int batch_size
        +bool is_active
        +margin()  «property»
        +calculate_estimated_days(qty, zone)
    }
    class Stock {
        +int id
        +int quantity  «CHECK >= 0»
        +int threshold_alert
        +is_low()  «property»
        +decrement(qty)  «raises if not enough»
        +increment(qty)
    }
    class ShippingZone {
        +int id
        +str zone_name
        +str[] countries
        +int delay_days
        +decimal cost
    }

    class Order {
        +int id
        +str order_number  «unique»
        +str status
        +decimal total_amount
        +str currency = CHF
        +str channel  «b2c/b2b»
        +str stripe_session_id
        +datetime created_at
        +generate_order_number()
    }
    class OrderItem {
        +int id
        +int quantity  «CHECK > 0»
        +decimal unit_price
        +decimal subtotal
        +save()  «computes subtotal»
    }
    class Payment {
        +UUID id
        +str stripe_payment_intent  «unique»
        +decimal amount
        +str currency = CHF
        +str status
        +datetime paid_at
    }

    class B2BRequest {
        +int id
        +str company_name
        +str contact_email
        +str sector
        +int estimated_qty
        +str status
        +bool wants_marketing
    }
    class B2BProductInfo {
        +int id
        +bool is_b2b_available
        +int moq = 24
        +decimal b2b_unit_price
    }
    class AdminUser {
        +int id
        +str email  «unique»
        +str role  «superadmin/admin»
        +bool is_active
        +set_password(raw)  «make_password»
        +check_password(raw)
    }

    AbstractBaseUser <|-- Customer
    PermissionsMixin <|-- Customer
    BaseUserManager  <|-- CustomerManager
    Customer "1" -- "1" CustomerManager : managed by

    Customer "1" o-- "0..1" B2BAccount : pro profile
    Customer "1" o-- "*" ConsentLog : consents (SET_NULL)
    Customer "1" o-- "*" PasswordResetToken : resets
    Customer "1" o-- "*" CustomerAddress : saves
    Customer "1" o-- "*" Order : places (RESTRICT)

    Category "1" o-- "*" Product : has
    Product "1" o-- "*" ProductImage : illustrated by
    Product "1" o-- "*" SKU : sold as
    SKU "1" -- "1" Stock : tracked by
    SKU "1" -- "0..1" B2BProductInfo : pro data
    AdminUser "1" o-- "*" Stock : updates (SET_NULL)

    Order "1" *-- "*" OrderItem : contains
    SKU "1" o-- "*" OrderItem : ordered as
    Order "1" -- "1" Payment : paid by (OneToOne)
    ShippingZone "1" o-- "*" Order : delivers (SET_NULL)

    B2BAccount "1" o-- "*" Order : pro orders
```

## Key business methods to explain
- `Customer.set_password()` — hashes with PBKDF2 (never plaintext).
- `SKU.calculate_estimated_days(qty, zone)` — shipping delay if stock is enough, otherwise
  production batches + shipping.
- `Stock.decrement(qty)` — decreases stock, raises `ValueError` if insufficient (no negative
  stock).
- `Order.generate_order_number()` — unique, non-guessable number (based on `secrets`).
- `OrderItem.save()` — auto-computes `subtotal = quantity × unit_price`.
- `AdminUser.set_password()/check_password()` — hashed staff credentials.
