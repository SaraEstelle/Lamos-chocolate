# Stage 3 — Task 3: Sequence Diagrams
## Lamos Chocolate — European Digital Platform

> **Project**: Lamos Chocolate — European Digital Platform
> **Team**: Sara Rebati · Valentin Planchon
> **Stack**: Django 5.x · PostgreSQL 16 · Docker
---

## 3.1 — Introduction

Sequence diagrams describe the **chronological interactions** between system components for critical use cases. They answer the question: *"Who sends what to whom, and in what order?"*

Each diagram is accompanied by a step-by-step description detailing every interaction.

### Common Actors and Participants

| Symbol | Participant | Description |
|--------|-------------|-------------|
| `Browser` | Client browser | User interface (HTML/JS) |
| `Nginx` | Reverse proxy | HTTPS → Gunicorn routing (Docker) |
| `Django` | Django application | Views + Service Layer (Python 3.12) |
| `DB` | PostgreSQL 16 | Relational database (Docker) |
| `Stripe` | Stripe API | External payment service |
| `SMTP` | Mail server | Transactional email sending |
| `Session` | Django Session | Server-side storage (cart, auth) |

---

## 3.2 — Diagram 1: Complete B2C Purchase Flow (Stripe Checkout)

> **Use case**: A logged-in customer adds a product to their cart, proceeds to checkout, pays via Stripe, and receives a confirmation.


```mermaid
sequenceDiagram
    actor Browser
    participant Nginx
    participant Django
    participant Session
    participant DB as PostgreSQL
    participant Stripe
    participant SMTP

    Browser->>Nginx: GET /en/shop/
    Nginx->>Django: forward
    Django->>DB: Product.objects.filter(is_active=True).prefetch_related()
    DB-->>Django: products queryset
    Django-->>Browser: render catalog.html

    Browser->>Django: POST /api/cart/add/ {sku_id, quantity}
    Django->>Session: read cart
    Session-->>Django: cart dict
    Django->>DB: Stock.objects.get(sku=sku)
    DB-->>Django: stock.quantity
    Django->>Session: update cart / session.modified=True
    Django-->>Browser: JsonResponse {cart_count, subtotal}

    Browser->>Django: POST /checkout/create-session/
    Django->>DB: ShippingZone.get_zone_for_country(country)
    DB-->>Django: shipping_zone
    Note over Django: sku.calculate_estimated_days(qty, zone)
    Django->>Stripe: stripe.checkout.Session.create(line_items, locale)
    Stripe-->>Django: {session.id, session.url}
    Django-->>Browser: redirect(session.url) HTTP 303

    Browser->>Stripe: HTTPS — Stripe Hosted Checkout
    Note over Browser,Stripe: Customer enters credit card
    Stripe-->>Browser: redirect to success_url

    Browser->>Django: GET /checkout/confirmation/?session_id=cs_...

    Note over Stripe,Django: ASYNC WEBHOOK
    Stripe->>Django: POST /checkout/webhook/\n{payment_intent.succeeded}
    Note over Django: stripe.Webhook.construct_event() — signature check
    Django->>DB: Order.objects.create(estimated_delivery_days=X)
    Django->>DB: OrderItem.objects.bulk_create(items)
    Django->>DB: stock.decrement() with select_for_update()
    Django->>SMTP: send_mail() — HTML confirmation email
    Django-->>Stripe: JsonResponse {status: received} HTTP 200

    Django-->>Browser: render confirmation.html
```
### Step-by-Step Description

| # | Actor | Action | Technical Detail |
|---|-------|--------|-----------------|
| 1 | Browser → Django | `GET /en/shop/` | `CatalogView` — `Product.objects.filter(is_active=True).prefetch_related('skus__stock')` |
| 2 | Django → DB | Products query | `prefetch_related` avoids N+1 queries |
| 3 | Django → Browser | Render `catalog.html` | Django template with i18n context |
| 4 | Browser → Django | `POST /api/cart/add/` — `{sku_id, qty}` | AJAX call from `cart.js` |
| 5 | Django → Session | Read current cart | `request.session.get('cart', {})` |
| 6 | Django → DB | Check stock | `Stock.objects.select_for_update().get(sku=sku)` |
| 7 | Django → Session | Update cart | `request.session['cart'][sku_id] += qty`; `request.session.modified = True` |
| 8 | Django → Browser | `JsonResponse {cart_count, subtotal}` | AJAX response — updates header counter |
| 9 | Browser → Django | `POST /checkout/create-session/` | Triggers Stripe checkout creation |
| 10 | Django → DB | Get customer + shipping zone | `ShippingZone.get_zone_for_country(country)` |
| 11 | Django | Compute delivery | `sku.calculate_estimated_days(qty, shipping_zone)` |
| 12 | Django → Stripe | `stripe.checkout.Session.create(line_items=..., locale=lang)` | Hosted Stripe Checkout session |
| 13 | Stripe → Django | `{session.id, session.url}` | URL to Stripe-hosted payment page |
| 14 | Django → Browser | `redirect(session.url)` HTTP 303 | Customer redirected to Stripe |
| 15 | Stripe → Browser | Stripe payment page | Customer enters card details on Stripe's PCI-DSS compliant interface |
| 16 | Stripe → Browser | Redirect to `success_url` | After payment, Stripe sends customer back |
| 17 | Stripe → Django | `POST /checkout/webhook/` (async) | `payment_intent.succeeded` event |
| 18 | Django | Signature verification | `stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)` |
| 19 | Django → DB | `Order.objects.create(estimated_delivery_days=X)` | Order created with `status='paid'` |
| 20 | Django → DB | `OrderItem.objects.bulk_create(items)` | All order lines in one DB call |
| 21 | Django → DB | `stock.decrement(qty)` with `select_for_update()` | Atomic stock decrement |
| 22 | Django → SMTP | `send_mail()` | HTML confirmation email in session language |
| 23 | Django → Browser | Render `confirmation.html` | Displays order number + estimated delivery |

> **Critical point**: Steps 17–22 are **asynchronous**. The order is **never** created before Stripe webhook confirmation, preventing any unconfirmed order from being recorded.

---

## 3.3 — Diagram 2: Customer Registration and Authentication

> **Use case**: A visitor creates an account, logs in, accesses their order history, and resets their password.



```mermaid
sequenceDiagram
    actor Browser
    participant Django
    participant DB as PostgreSQL
    participant SMTP

    Browser->>Django: GET /accounts/register/
    Django-->>Browser: render register.html

    Browser->>Django: POST {first_name, last_name, email, password1, password2}
    Note over Django: CustomerRegistrationForm.is_valid()
    Django->>DB: Customer.objects.filter(email=email).exists()
    DB-->>Django: False (available)
    Note over Django: make_password(password1)
    Django->>DB: Customer.objects.create(...)
    DB-->>Django: customer.id
    Django->>SMTP: send_mail() welcome email
    Django-->>Browser: redirect /accounts/login/

    Browser->>Django: POST /accounts/login/ {email, password}
    Django->>DB: Customer.objects.get(email=email)
    DB-->>Django: customer object
    Note over Django: check_password(raw, hash) → True
    Note over Django: session['customer_id'] = customer.pk
    Django-->>Browser: redirect /my-account/

    Browser->>Django: GET /my-account/orders/
    Note over Django: @login_required check
    Django->>DB: Order.objects.filter(customer).order_by('-created_at')
    DB-->>Django: orders queryset
    Django-->>Browser: render orders.html

    Note over Browser,SMTP: PASSWORD RESET FLOW
    Browser->>Django: POST /accounts/forgot-password/ {email}
    Note over Django: secrets.token_urlsafe(32)
    Django->>DB: PasswordResetToken.objects.create(expires_at=+1h)
    Django->>SMTP: send_mail() reset link
    Django-->>Browser: redirect (always same response — anti-enumeration)

    Browser->>Django: POST /accounts/reset-password/token/
    Note over Django: token.is_valid → True
    Django->>DB: customer.set_password() + token.used=True
    Django-->>Browser: redirect /accounts/login/
```
### Step-by-Step Description

**Phase 1 — Registration**

| # | Action | Detail |
|---|--------|--------|
| 1 | Display form | `GET /accounts/register/` → `CustomerRegistrationView` |
| 2 | Form submission | `POST` with `CustomerRegistrationForm` |
| 3 | Django validation | `form.is_valid()`: email format, unique check, password length, password match |
| 4 | Email uniqueness | `Customer.objects.filter(email=email).exists()` |
| 5 | Password hashing | `make_password(password)` — PBKDF2 with SHA-256 |
| 6 | Account creation | `Customer.objects.create(...)` |
| 7 | Welcome email | `send_mail()` asynchronous |
| 8 | Redirect | `redirect('accounts:login')` with Django message |

**Phase 2 — Login**

| # | Action | Detail |
|---|--------|--------|
| 9 | Login submission | `POST /accounts/login/` |
| 10 | Account lookup | `Customer.objects.get(email=email)` |
| 11 | Password check | `check_password(raw_password, customer.password_hash)` |
| 12 | If False | Generic error message (no user enumeration: "Email or password incorrect") |
| 13 | If True | `request.session['customer_id'] = customer.pk` |
| 14 | Redirect | To `next` param or `/my-account/` |

**Phase 3 — Password Reset**

| # | Action | Detail |
|---|--------|--------|
| 15 | Reset request | `POST /accounts/forgot-password/` — always same response (anti-enumeration) |
| 16 | Token generation | `secrets.token_urlsafe(32)` |
| 17 | Token storage | `PasswordResetToken.objects.create(expires_at=timezone.now() + timedelta(hours=1))` |
| 18 | Reset email | Link with token, 1-hour expiration |
| 19 | Validation | `token.is_valid` → `not used and timezone.now() < expires_at` |
| 20 | Password update | `customer.set_password(new_password)` + `token.used = True` |

---

## 3.4 — Diagram 3: B2B Request Submission + Admin Notification

> **Use case**: A purchasing manager submits a corporate form. The Lamos team receives a notification, the request is stored, and the admin can view and process it.



```mermaid
sequenceDiagram
    actor B2B as B2B Client
    participant Django
    participant DB as PostgreSQL
    participant SMTP
    actor Admin

    B2B->>Django: GET /fr/b2b/
    Django-->>B2B: render b2b.html

    B2B->>Django: POST /fr/b2b/submit/ {company, contact, email, qty, message}
    Note over Django: B2BRequestForm.is_valid()
    Django->>DB: B2BRequest.objects.create(status='new', ip_address=...)
    DB-->>Django: b2b_request.id
    Django->>SMTP: send_mail() to Lamos team
    Django-->>B2B: redirect /b2b/confirmation/

    Admin->>Django: GET /backoffice/b2b/
    Note over Django: @admin_required check
    Django->>DB: B2BRequest.objects.all().order_by('-created_at')
    DB-->>Django: queryset
    Django-->>Admin: render b2b_requests.html

    Admin->>Django: POST /backoffice/b2b/7/update-status/ {status: in_progress}
    Django->>DB: B2BRequest.objects.filter(pk=7).update(status, processed_at, processed_by)
    DB-->>Django: OK
    Django-->>Admin: redirect /backoffice/b2b/ (flash: Status updated)
```

### Step-by-Step Description

| # | Action | Technical Detail |
|---|--------|-----------------|
| 1 | Display B2B form | `GET /fr/b2b/` → bilingual template via `i18n_patterns` |
| 2 | Form submission | `POST /fr/b2b/submit/` with `B2BRequestForm` |
| 3 | Validation | `form.is_valid()` — required fields: company, contact, email format |
| 4 | Record in DB | `B2BRequest.objects.create(status='new', ip_address=request.META.get('REMOTE_ADDR'))` |
| 5 | Lamos notification | `send_mail()` to internal Lamos address with all form details |
| 6 | User confirmation | `redirect('b2b:confirmation')` with success message |
| 7 | Admin consultation | `GET /backoffice/b2b/` — `@admin_required` decorator verifies `session['admin_id']` |
| 8 | Admin check | `AdminUser.objects.get(pk=session['admin_id'])` — role verification |
| 9 | Data retrieval | `B2BRequest.objects.all().order_by('-created_at')` with optional `?status=new` filter |
| 10 | Status update | `B2BRequest.objects.filter(pk=id).update(status=new_status, processed_at=timezone.now(), processed_by=admin)` |

---

## 3.5 — Diagram 4: Admin — Product Update + Storefront Impact

> **Use case**: A Lamos admin updates a product's stock from the back-office panel. The change is immediately visible on the storefront.

```mermaid
sequenceDiagram
    actor Admin
    participant Django_Back as Django Backoffice
    participant DB as PostgreSQL
    actor Customer
    participant Django_Shop as Django Shop

    Admin->>Django_Back: POST /backoffice/login/ {email, password}
    Django_Back->>DB: AdminUser.objects.get(email=email)
    DB-->>Django_Back: admin object
    Note over Django_Back: session['admin_id'] = admin.pk
    Django_Back-->>Admin: redirect /backoffice/dashboard/

    Admin->>Django_Back: GET /backoffice/products/
    Django_Back->>DB: Product.objects.all().prefetch_related('skus__stock')
    DB-->>Django_Back: product list
    Django_Back-->>Admin: render backoffice/products.html

    Admin->>Django_Back: POST /backoffice/stock/3/update/ {quantity: 75}
    Django_Back->>DB: Stock.objects.select_for_update().get(sku_id=3)
    DB-->>Django_Back: stock object
    Django_Back->>DB: stock.quantity=75 / stock.save()
    DB-->>Django_Back: OK
    Django_Back-->>Admin: JsonResponse {success: true, new_quantity: 75}

    Note over Customer,Django_Shop: INDEPENDENT REQUEST
    Customer->>Django_Shop: GET /shop/lamos-pistachio/
    Django_Shop->>DB: Product.objects.get(slug=slug).prefetch_related()
    DB-->>Django_Shop: product + stock (qty=75)
    Note over Django_Shop: calculate_estimated_days(1, zone) = 2 days
    Django_Shop-->>Customer: render product.html (Available — 2 days delivery)
```
---

## 3.6 — Diagram 5: CI/CD Pipeline — Automated Deployment

> **Use case**: A developer pushes code to `main` after a validated pull request. GitHub Actions triggers the full deployment pipeline.

```mermaid
flowchart TD
    DEV["👩‍💻 Developer\ngit push feature/xxx"]
    GH["GitHub\nPull Request"]
    MERGE["main branch\nPR merged"]

    subgraph Actions["GitHub Actions"]
        T["JOB: test\n• postgres:16 service\n• pytest + pytest-django\n• --cov-fail-under=70"]
        L["JOB: lint\n• flake8 apps/ lamos/"]
        D["JOB: deploy\n• needs: test + lint\n• if: branch == main"]
    end

    subgraph Server["Linux Ubuntu Server"]
        PULL["git pull origin main"]
        BUILD["docker compose build"]
        UP["docker compose up -d"]
        MIG["manage.py migrate"]
        STATIC["manage.py collectstatic"]
        NGINX["nginx -s reload"]
    end

    SLACK["✅ Slack notification\nlamos-eu.com live"]

    DEV --> GH
    GH --> MERGE
    MERGE --> T
    MERGE --> L
    T --> D
    L --> D
    D --> PULL
    PULL --> BUILD
    BUILD --> UP
    UP --> MIG
    MIG --> STATIC
    STATIC --> NGINX
    NGINX --> SLACK
```
### CI/CD Step Description

| Phase | Step | Action | Detail |
|-------|------|--------|--------|
| **Test** | 1 | PostgreSQL 16-alpine service | GitHub Actions spins up a PostgreSQL container automatically |
| **Test** | 2 | Dependencies | `pip install -r requirements/development.txt` + `pytest pytest-django pytest-cov` |
| **Test** | 3 | Test run | `pytest tests/ --cov=apps --cov-fail-under=70` — fails if coverage < 70% |
| **Lint** | 4 | Code quality | `flake8 apps/ lamos/ --max-line-length=100` |
| **Deploy** | 5 | SSH connection | `appleboy/ssh-action` — connects to production server securely |
| **Deploy** | 6 | Docker build | `docker compose build` — rebuilds all container images |
| **Deploy** | 7 | Container restart | `docker compose up -d` — zero-downtime restart |
| **Deploy** | 8 | DB migrations | `docker compose exec app python manage.py migrate --no-input` |
| **Deploy** | 9 | Static files | `docker compose exec app python manage.py collectstatic --no-input` |
| **Deploy** | 10 | Nginx reload | `nginx -s reload` — picks up new static files without downtime |

---

## 3.7 — Diagrams Summary

| # | Use Case | Components Involved | Criticality |
|---|----------|--------------------|-|
| 1 | B2C Purchase + Stripe | Browser, Nginx, Django, DB, Stripe, SMTP | 🔴 Critical |
| 2 | Registration & Authentication | Browser, Django, DB, Django Auth, SMTP | 🔴 Critical |
| 3 | B2B Request + Admin notification | Browser, Django, DB, SMTP, Admin Browser | 🟡 Important |
| 4 | Admin — Stock update + CRUD | Browser (admin), Django, DB | 🟡 Important |
| 5 | CI/CD — Automated deployment | GitHub, Actions, Docker, Server, Nginx | 🟠 Infrastructure |

---
