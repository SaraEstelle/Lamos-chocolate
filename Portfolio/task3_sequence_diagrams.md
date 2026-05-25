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

```
Browser       Nginx      Django       Session       DB            Stripe       SMTP
   │             │          │             │           │               │           │
   │─ GET /shop/ ►          │             │           │               │           │
   │             │─ forward ►             │           │               │           │
   │             │          │─ Product.objects.filter(is_active=True) ►           │
   │             │          │  .prefetch_related('skus__stock')        │           │
   │             │          │◄─ products queryset ─────────────────────┘           │
   │             │◄─ render catalog.html ─┘            │               │           │
   │◄────────────┘          │             │             │               │           │
   │                        │             │             │               │           │
   │─ POST /api/cart/add/ ──►             │             │               │           │
   │  {sku_id, quantity}     │             │             │               │           │
   │             │          │─ read cart ─►             │               │           │
   │             │          │◄─ cart dict ┘             │               │           │
   │             │          │─ Stock.objects.get(sku=sku) ────────────►  │           │
   │             │          │◄─ stock.quantity ─────────────────────────┘           │
   │             │          │─ update cart ►            │               │           │
   │             │          │  session.modified = True  │               │           │
   │             │◄─ JsonResponse {cart_count, subtotal} ┘              │           │
   │◄────────────┘          │             │             │               │           │
   │                        │             │             │               │           │
   │─ POST /checkout/create-session/ ──────►            │               │           │
   │             │          │─ read cart ─►             │               │           │
   │             │          │◄─ cart items ┘            │               │           │
   │             │          │─ Customer.objects.get() ───────────────►  │           │
   │             │          │◄─ customer data ─────────────────────────┘           │
   │             │          │─ ShippingZone.get_zone_for_country(country)           │
   │             │          │◄─ shipping_zone ──────────────────────────┘           │
   │             │          │─ sku.calculate_estimated_days(qty, zone)              │
   │             │          │  → estimated_delivery_days                            │
   │             │          │                            │               │           │
   │             │          │─── stripe.checkout.Session.create(line_items) ────────►
   │             │          │    {locale, success_url, cancel_url,       │           │
   │             │          │     customer_email, metadata}              │           │
   │             │          │◄── {session.id, session.url} ──────────────────────────┘
   │             │          │                            │               │           │
   │             │◄─ redirect(session.url) HTTP 303 ─────┘              │           │
   │◄────────────┘          │             │             │               │           │
   │                        │             │             │               │           │
   │──── redirect → Stripe Hosted Checkout Page ──────────────────────►            │
   │                        │             │             │               │           │
   │      [CUSTOMER ENTERS CREDIT CARD ON STRIPE'S PAGE]               │           │
   │                        │             │             │               │           │
   │◄──── Stripe redirects to success_url ?session_id=cs_... ──────────┘           │
   │─ GET /checkout/confirmation/ ─────────►            │               │           │
   │             │          │             │             │               │           │
   │             │          │──── [ASYNC WEBHOOK] ────────────────────────►         │
   │             │          │◄─── POST /checkout/webhook/ ────────────────┘         │
   │             │          │     {event: payment_intent.succeeded,      │           │
   │             │          │      payment_intent_id, amount, metadata}  │           │
   │             │          │                            │               │           │
   │             │          │─ stripe.Webhook.construct_event()          │           │
   │             │          │  (signature verification)                  │           │
   │             │          │                            │               │           │
   │             │          │─ Order.objects.create(     │               │           │
   │             │          │    estimated_delivery_days=X) ─────────────►           │
   │             │          │─ OrderItem.objects.bulk_create(items) ──────►          │
   │             │          │─ Stock.decrement(qty) via select_for_update() ─────────►
   │             │          │◄─ OK ────────────────────────────────────────┘          │
   │             │          │─── send_mail() confirmation email ─────────────────────►
   │             │          │    (bilingual, includes estimated_delivery_days)         │
   │             │          │◄─── email sent ─────────────────────────────────────────┘
   │             │◄─ render confirmation.html ──────────┘              │           │
   │◄────────────┘          │             │             │              │           │
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

```
Browser       Django       DB          Django Auth    SMTP
   │             │           │               │           │
   │─ GET /accounts/register/ ────────────────►          │
   │◄─ render register.html ──────────────────┘          │
   │                         │              │            │
   │─ POST /accounts/register/ ────────────────────────── │
   │  {first_name, last_name, email,         │            │
   │   password1, password2}                 │            │
   │             │            │              │            │
   │             │─ CustomerRegistrationForm.is_valid()   │
   │             │  (email format, min length,            │
   │             │   password match validation)           │
   │             │            │              │            │
   │             │─ Customer.objects.filter(email=email).exists() ─►
   │             │◄─ False (email available) ──────────────┘        │
   │             │            │              │            │
   │             │─ make_password(password1) → password_hash        │
   │             │─ Customer.objects.create(...) ──────────────────►│
   │             │◄─ customer.id ──────────────────────────────────┘│
   │             │─── send_mail() welcome email ───────────────────►│
   │             │◄─── sent ──────────────────────────────────────── │
   │◄─ redirect /accounts/login/ (flash: "Account created!") ────── │
   │                         │              │            │
   │─ POST /accounts/login/ ─────────────────►           │
   │  {email, password}       │              │            │
   │             │─ Customer.objects.get(email=email) ─────────────►│
   │             │◄─ customer object ─────────────────────────────── │
   │             │            │              │            │
   │             │─ check_password(password, customer.password_hash)  │
   │             │  → True                   │            │
   │             │                           │            │
   │             │─ request.session['customer_id'] = customer.pk      │
   │             │─ customer.last_login = timezone.now()              │
   │             │─ customer.save()          │            │
   │◄─ redirect /my-account/ (flash: "Welcome Sara!") ──── │
   │                         │              │            │
   │─ GET /my-account/orders/ ──────────────►            │
   │             │─ @login_required → check session['customer_id']    │
   │             │─ Order.objects.filter(customer=customer) ─────────►│
   │             │  .order_by('-created_at')               │          │
   │             │◄─ orders queryset ─────────────────────────────────┘
   │◄─ render orders.html ───────────────────┘           │
   │                         │              │            │
   │                         │              │            │
   │   [--- PASSWORD RESET FLOW ---]        │            │
   │                         │              │            │
   │─ POST /accounts/forgot-password/ ───────►           │
   │  {email}                │              │            │
   │             │─ Customer.objects.filter(email=email).first()       │
   │             │◄─ customer (or None)      │            │
   │             │─ if customer:             │            │
   │             │   token = secrets.token_urlsafe(32)                 │
   │             │   PasswordResetToken.objects.create(               │
   │             │     token=token, expires_at=now()+1h) ───────────►  │
   │             │◄─ OK ───────────────────────────────────────────── │
   │             │─── send_mail() reset link ──────────────────────────►
   │             │    (link: /accounts/reset-password/<token>/)       │
   │◄─ redirect (flash: "Email sent if account exists") — always ─────  │
   │                         │              │            │
   │─ GET /accounts/reset-password/<token>/ ──────────────►          │
   │             │─ PasswordResetToken.objects.get(token=token)       │
   │             │  .is_valid → True (not used + not expired)         │
   │◄─ render reset_password_form.html ──────────────────── │
   │                         │              │            │
   │─ POST /accounts/reset-password/<token>/ ──────────────►         │
   │  {new_password, confirm_password}       │            │
   │             │─ form validation          │            │
   │             │─ customer.set_password(new_password) ────────────►  │
   │             │─ token.used = True; token.save() ──────────────────►│
   │◄─ redirect /accounts/login/ (flash: "Password updated") ──────── │
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

```
Browser(B2B)   Django       DB           SMTP(Lamos)   Browser(Admin)
    │             │           │               │              │
    │─ GET /fr/b2b/ ──────────►              │              │
    │◄─ render b2b.html ───────┘             │              │
    │                          │             │              │
    │─ POST /fr/b2b/submit/ ────►            │              │
    │  {company_name,           │            │              │
    │   contact_name,           │            │              │
    │   contact_email,          │            │              │
    │   contact_phone,          │            │              │
    │   sector,                 │            │              │
    │   estimated_qty,          │            │              │
    │   occasion,               │            │              │
    │   message,                │            │              │
    │   language}               │            │              │
    │             │             │            │              │
    │             │─ B2BRequestForm.is_valid()              │
    │             │  (required: company_name, contact_name, │
    │             │   contact_email — email format)         │
    │             │             │            │              │
    │             │─ B2BRequest.objects.create(             │
    │             │    status='new',          │             │
    │             │    ip_address=request     │             │
    │             │    .META['REMOTE_ADDR']) ─────────────►  │
    │             │◄─ b2b_request.id ────────────────────── │
    │             │             │            │              │
    │             │─── send_mail() notification ────────────►
    │             │    TO: contact@lamos-chocolate.com      │
    │             │    Subject: "New B2B Request — [Company]"
    │             │    Body: full request details           │
    │             │◄─── sent ───────────────────────────────┘
    │◄─ redirect /b2b/confirmation/ ───────── │              │
    │                          │             │              │
    │                          │             │              │
    │   [--- ADMIN REVIEWS B2B REQUESTS ---]                │
    │                          │             │   ┌──────────┘
    │                          │             │   │
    │                          │   GET /backoffice/b2b/ ◄──┘
    │                          │◄──────────────────────────
    │                          │─ @admin_required → check session['admin_id']
    │                          │  + admin.role in ('admin', 'superadmin')
    │                          │─ B2BRequest.objects.all() ───────────────►
    │                          │  .order_by('-created_at')  │
    │                          │◄─ queryset ───────────────────────────────┘
    │                          │─── render backoffice/b2b_requests.html ────────────►
    │                          │                            │              │
    │                          │   POST /backoffice/b2b/<id>/update-status/ ◄───────┘
    │                          │◄──────────────────────────────────────────
    │                          │    {status: 'in_progress'} │              │
    │                          │─ B2BRequest.objects.filter(pk=id).update( │
    │                          │    status='in_progress',    │             │
    │                          │    processed_at=timezone.now(),           │
    │                          │    processed_by=admin) ────────────────────►
    │                          │◄─ OK ─────────────────────────────────────┘
    │                          │─── redirect /backoffice/b2b/ (flash: "Status updated") ──────────────►
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

```
Browser(Admin)   Django(Backoffice)   DB         Browser(Customer)  Django(Shop)
    │                │                 │                │               │
    │─ POST /backoffice/login/ ──────────►               │               │
    │  {email, password}               │                │               │
    │              │─ AdminUser.objects.get(email=email) ►               │
    │              │◄─ admin found ────────────────────── │               │
    │              │─ admin.check_password(password) → True              │
    │              │─ request.session['admin_id'] = admin.pk             │
    │◄─ redirect /backoffice/dashboard/ ─────────────────┘               │
    │                                  │                │               │
    │─ GET /backoffice/products/ ────────►               │               │
    │              │─ Product.objects.all() ─────────────►               │
    │              │  .prefetch_related('skus__stock')   │               │
    │              │◄─ full product list ──────────────── │               │
    │◄─ render backoffice/products.html ─┘               │               │
    │                                  │                │               │
    │─ POST /backoffice/stock/<sku_id>/update/ ────────────►              │
    │  {quantity: 75}                  │                │               │
    │              │─ Stock.objects.select_for_update() ─►               │
    │              │  .get(sku_id=sku_id)                │               │
    │              │◄─ stock object ───────────────────── │               │
    │              │─ stock.quantity  = 75               │               │
    │              │─ stock.updated_by = admin           │               │
    │              │─ stock.save() ─────────────────────►│               │
    │              │◄─ OK ─────────────────────────────── │               │
    │◄─ JsonResponse {success: true, new_quantity: 75, is_low: false} ── │
    │                                  │                │               │
    │                                  │          [INDEPENDENT REQUEST] │
    │                                  │                │               │
    │                                  │   GET /shop/lamos-pistachio/ ──►
    │                                  │                │─ Product.objects.get(slug=slug)
    │                                  │                │  .prefetch_related('skus__stock')
    │                                  │                │─ sku.available_quantity → 75
    │                                  │                │◄─ product + stock data ──────────┘
    │                                  │                │─ sku.calculate_estimated_days(1, zone)
    │                                  │◄─ render product.html (badge: "Available", est: 2 days) ─────┘
    │                                  │                │               │
    │─ POST /backoffice/products/new/ ─────────────────────►             │
    │  {name_fr, name_en,              │                │               │
    │   description_*, price,          │                │               │
    │   category_id, sku_code,         │                │               │
    │   format, production_delay_days, │                │               │
    │   batch_size, initial_stock,     │                │               │
    │   image}                         │                │               │
    │              │─ ProductCreateForm.is_valid()       │               │
    │              │─ Product.objects.create(...) ────────►               │
    │              │◄─ product.id ─────────────────────── │               │
    │              │─ SKU.objects.create(product=product) ►               │
    │              │◄─ sku.id ─────────────────────────── │               │
    │              │─ Stock.objects.create(sku=sku,        │               │
    │              │    quantity=initial_stock) ───────────►               │
    │              │◄─ OK ─────────────────────────────── │               │
    │◄─ redirect /backoffice/products/ (flash: "Product created") ─────── │
```

---

## 3.6 — Diagram 5: CI/CD Pipeline — Automated Deployment

> **Use case**: A developer pushes code to `main` after a validated pull request. GitHub Actions triggers the full deployment pipeline.

```
Developer    GitHub        GitHub Actions        Docker          Server(Prod)   Nginx
    │           │                │                  │                │           │
    │─ git push feature/xxx ──────►                 │                │           │
    │           │─ PR opened ────►                  │                │           │
    │           │  [Peer code review]               │                │           │
    │           │─ PR merged to main ───────────────►                │           │
    │           │                │                  │                │           │
    │           │──── trigger CI/CD workflow ────────►               │           │
    │           │                │                  │                │           │
    │           │         ┌──────┴──────┐           │                │           │
    │           │         │  JOB: test  │           │                │           │
    │           │         ├─────────────┤           │                │           │
    │           │         │ postgres:16 │           │                │           │
    │           │         │ service     │           │                │           │
    │           │         │ (Alpine)    │           │                │           │
    │           │         │             │           │                │           │
    │           │         │ pip install │           │                │           │
    │           │         │ pytest      │           │                │           │
    │           │         │ pytest-django           │                │           │
    │           │         │             │           │                │           │
    │           │         │ pytest tests/ ──────────►                │           │
    │           │         │ --cov=apps               │                │           │
    │           │         │ --cov-fail-under=70      │                │           │
    │           │         │ ✓ passed    │           │                │           │
    │           │         └──────┬──────┘           │                │           │
    │           │                │                  │                │           │
    │           │         ┌──────┴──────┐           │                │           │
    │           │         │  JOB: lint  │           │                │           │
    │           │         │  (flake8)   │           │                │           │
    │           │         │  ✓ passed   │           │                │           │
    │           │         └──────┬──────┘           │                │           │
    │           │                │                  │                │           │
    │           │         ┌──────┴────────────┐     │                │           │
    │           │         │  JOB: deploy      │     │                │           │
    │           │         │  (needs test+lint)│     │                │           │
    │           │         ├───────────────────┤     │                │           │
    │           │         │ SSH to server     │     │                │           │
    │           │         │ git pull main     │     │                │           │
    │           │         │ docker compose    │─────►                │           │
    │           │         │   build           │     │ build images   │           │
    │           │         │ docker compose    │─────►                │           │
    │           │         │   up -d           │     │ restart all    │           │
    │           │         │                   │     │ containers     │           │
    │           │         │ manage.py migrate │─────►                │           │
    │           │         │ manage.py         │─────►                │           │
    │           │         │ collectstatic     │     │                │           │
    │           │         │                   │     │                │──────────►│
    │           │         │ nginx -s reload   │     │                │           │ reload
    │           │         │  ✓ deployed       │     │                │◄──────────┘
    │           │         └──────┬────────────┘     │                │
    │           │                │                  │                │
    │◄───────────────── Slack notification: "✅ Deploy successful — lamos-eu.com" ──
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
