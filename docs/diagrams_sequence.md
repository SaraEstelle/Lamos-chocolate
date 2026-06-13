# Sequence Diagrams

## Diagram 1 — Complete B2C Purchase Flow

```mermaid
sequenceDiagram
    actor Customer as Customer (Browser)
    participant Nginx
    participant Django
    participant Session as Django Session
    participant DB as PostgreSQL
    participant Stripe
    participant SMTP as Mailgun SMTP

    Note over Customer, SMTP: Phase 1 — Browse & Add to Cart

    Customer->>Nginx: GET /fr/shop/
    Nginx->>Django: proxy_pass
    Django->>DB: SELECT products JOIN skus JOIN stock<br/>WHERE is_active=TRUE
    DB-->>Django: Product list + stock levels
    Django-->>Customer: Render catalog.html (i18n FR)

    Customer->>Nginx: POST /api/cart/add/<br/>{sku_id: 3, quantity: 2}
    Nginx->>Django: proxy_pass (AJAX)
    Django->>Session: Read request.session['cart']
    Django->>DB: SELECT quantity FROM stock<br/>WHERE sku_id=3
    DB-->>Django: quantity: 50 (sufficient)
    Django->>Session: Update cart, session.modified=True
    Django-->>Customer: JSON {success: true, cart_count: 2, subtotal: "25.80"}

    Note over Customer, SMTP: Phase 2 — Checkout & Payment

    Customer->>Nginx: POST /fr/checkout/create-session/<br/>{shipping: {country: "CH", ...}}
    Nginx->>Django: proxy_pass
    Django->>DB: SELECT customer, shipping_zone<br/>WHERE countries @> ARRAY['CH']
    DB-->>Django: zone: Switzerland, delay: 2 days
    Django->>Django: calculate_estimated_days(qty=2, zone)<br/>Stock sufficient → 2 days

    Django->>Stripe: stripe.checkout.Session.create(<br/>line_items, locale='fr',<br/>success_url, cancel_url)
    Stripe-->>Django: {session.id, session.url}
    Django-->>Customer: HTTP 303 Redirect → Stripe URL

    Customer->>Stripe: Enter card details<br/>(4242 4242 4242 4242)
    Stripe-->>Customer: Redirect → success_url

    Note over Customer, SMTP: Phase 3 — Webhook Confirmation (async)

    Stripe->>Nginx: POST /checkout/webhook/<br/>Event: payment_intent.succeeded
    Nginx->>Django: proxy_pass (@csrf_exempt)
    Django->>Django: stripe.Webhook.construct_event()<br/>Verify signature

    Django->>DB: BEGIN TRANSACTION
    Django->>DB: INSERT INTO orders (...,<br/>estimated_delivery_days=2)
    Django->>DB: INSERT INTO order_items
    Django->>DB: UPDATE stock SET quantity = quantity - 2<br/>(select_for_update)
    Django->>DB: COMMIT

    Django->>SMTP: send_mail() — Confirmation<br/>Template: order_confirmation.html (FR)<br/>Includes estimated delivery: 2 days
    SMTP-->>Customer: Email: Order LM-20260515-A3K7F confirmed

    Django-->>Stripe: HTTP 200 {status: "received"}

    Customer->>Nginx: GET /fr/checkout/confirmation/<br/>?session_id=cs_test_...
    Nginx->>Django: proxy_pass
    Django->>DB: SELECT order WHERE stripe_session_id=...
    Django-->>Customer: Render confirmation.html<br/>Order number + estimated delay
```

## Diagram 2 — Customer Registration & Authentication

```mermaid
sequenceDiagram
    actor Visitor as Visitor (Browser)
    participant Django
    participant DB as PostgreSQL
    participant SMTP as Mailgun SMTP

    Note over Visitor, SMTP: Phase 1 — Registration

    Visitor->>Django: GET /fr/accounts/register/
    Django-->>Visitor: Render register.html (empty form)

    Visitor->>Django: POST /fr/accounts/register/<br/>{first_name, last_name,<br/>email, password1, password2}
    Django->>Django: CustomerRegistrationForm.is_valid()<br/>Email format, password strength (min 8)
    Django->>DB: SELECT 1 FROM customers<br/>WHERE email='alice@test.com'
    DB-->>Django: 0 rows (email available)
    Django->>Django: make_password(password) → PBKDF2 hash
    Django->>DB: INSERT INTO customers<br/>(email, password_hash, ...)
    DB-->>Django: Created (id=42)

    Django->>SMTP: send_mail() — Welcome email
    Django-->>Visitor: HTTP 302 → /fr/accounts/login/<br/>+ Django flash message "Compte créé"

    Note over Visitor, SMTP: Phase 2 — Login

    Visitor->>Django: POST /fr/accounts/login/<br/>{email, password}
    Django->>DB: SELECT * FROM customers<br/>WHERE email='alice@test.com'
    DB-->>Django: Customer record
    Django->>Django: check_password(input, hash)

    alt Password correct
        Django->>Django: login(request, customer)<br/>Create session, set sessionid cookie
        Django->>DB: UPDATE customers<br/>SET last_login=NOW()
        Django-->>Visitor: HTTP 302 → /fr/mon-compte/<br/>Set-Cookie: sessionid=abc123 (httpOnly)
    else Password incorrect
        Django-->>Visitor: HTTP 200 Render login.html<br/>"Email ou mot de passe incorrect"<br/>(generic — no user enumeration)
    end

    Note over Visitor, SMTP: Phase 3 — Password Reset

    Visitor->>Django: POST /fr/accounts/forgot-password/<br/>{email: "alice@test.com"}
    Django->>DB: SELECT * FROM customers WHERE email=...
    
    alt Customer exists
        Django->>Django: Generate secure token<br/>secrets.token_urlsafe(48)
        Django->>DB: INSERT INTO password_reset_tokens<br/>(token, expires_at=NOW()+1h)
        Django->>SMTP: send_mail() — Reset link<br/>/accounts/reset-password/<token>/
    end
    
    Django-->>Visitor: HTTP 302 (always — anti-enumeration)<br/>"Si ce compte existe, un email a été envoyé"

    Visitor->>Django: GET /fr/accounts/reset-password/<token>/
    Django->>DB: SELECT FROM password_reset_tokens<br/>WHERE token=... AND used=FALSE
    Django->>Django: Check expires_at > NOW()
    Django-->>Visitor: Render reset_password.html

    Visitor->>Django: POST /fr/accounts/reset-password/<token>/<br/>{new_password1, new_password2}
    Django->>Django: Validate password strength
    Django->>DB: UPDATE customers SET password_hash=...<br/>UPDATE tokens SET used=TRUE
    Django-->>Visitor: HTTP 302 → /fr/accounts/login/<br/>"Mot de passe mis à jour"
```

## Diagram 3 — B2B Request Submission + Admin Notification

```mermaid
sequenceDiagram
    actor PM as Purchasing Manager
    participant Django
    participant DB as PostgreSQL
    participant SMTP as Mailgun SMTP
    actor Admin as Lamos Admin

    Note over PM, Admin: Phase 1 — B2B Form Submission

    PM->>Django: GET /fr/b2b/
    Django-->>PM: Render b2b.html<br/>(presentation + form)

    PM->>Django: POST /fr/b2b/submit/<br/>{company_name: "Hôtel Beau-Rivage",<br/>contact_name: "Jean Dupont",<br/>contact_email: "j.dupont@beaurivage.ch",<br/>sector: "Hôtellerie 5*",<br/>estimated_qty: 200,<br/>occasion: "Cadeaux clients VIP",<br/>message: "Coffrets personnalisés logo"}

    Django->>Django: B2BRequestForm.is_valid()<br/>Validate required fields
    Django->>DB: INSERT INTO b2b_requests<br/>(status='new',<br/>ip_address=request.META['REMOTE_ADDR'],<br/>language='fr')
    DB-->>Django: Created (id=15)

    Django->>SMTP: send_mail()<br/>To: contact@lamos-eu.com<br/>Subject: "Nouvelle demande B2B — Hôtel Beau-Rivage"<br/>Body: all form details

    Django-->>PM: HTTP 302 → /fr/b2b/confirmation/<br/>Render confirmation page

    Note over PM, Admin: Phase 2 — Admin Processing

    Admin->>Django: GET /backoffice/b2b/<br/>(@admin_required decorator)
    Django->>DB: SELECT * FROM b2b_requests<br/>ORDER BY created_at DESC
    DB-->>Django: List including new request
    Django-->>Admin: Render backoffice/b2b_requests.html

    Admin->>Django: POST /backoffice/b2b/15/update-status/<br/>{status: "in_progress"}
    Django->>DB: UPDATE b2b_requests<br/>SET status='in_progress',<br/>processed_at=NOW(),<br/>processed_by=admin.id<br/>WHERE id=15
    Django-->>Admin: JSON {success: true}
```

## Diagram 4 — Admin Product CRUD + Stock Management

```mermaid
sequenceDiagram
    actor Admin as Lamos Admin
    participant Django
    participant DB as PostgreSQL
    actor Customer as Customer (Storefront)

    Note over Admin, Customer: Product Creation

    Admin->>Django: GET /backoffice/products/<br/>(@admin_required)
    Django->>DB: SELECT products JOIN categories
    Django-->>Admin: Render products.html (list + create form)

    Admin->>Django: POST /backoffice/products/<br/>{name_fr, name_en, slug,<br/>description_fr, description_en,<br/>category_id, image_url, ...}
    Django->>Django: ProductForm.is_valid()
    Django->>DB: INSERT INTO products (...)
    DB-->>Django: Created (id=4)
    Django->>DB: INSERT INTO skus<br/>(product_id=4, sku_code, format,<br/>price, production_delay_days, batch_size)
    Django->>DB: INSERT INTO stock<br/>(sku_id, quantity=0, threshold_alert=5)
    Django-->>Admin: HTTP 302 → /backoffice/products/<br/>"Produit créé"

    Note over Admin, Customer: Stock Update

    Admin->>Django: POST /backoffice/stock/4/update/<br/>{quantity: 75}
    Django->>DB: UPDATE stock<br/>SET quantity=75, updated_by=admin.id<br/>WHERE sku_id=4
    Django-->>Admin: JSON {success: true, new_quantity: 75, is_low: false}

    Note over Admin, Customer: Impact on Storefront (real-time)

    Customer->>Django: GET /fr/shop/lamos-pistachio-kunafa-bar/
    Django->>DB: SELECT product JOIN skus JOIN stock<br/>WHERE slug='lamos-pistachio-kunafa-bar'
    DB-->>Django: Product + SKUs + stock.quantity=75
    Django->>Django: calculate_estimated_days()<br/>Stock sufficient → zone delay only
    Django-->>Customer: Render product.html<br/>Badge: "En stock" / Estimated delivery: 2 days

    Note over Admin, Customer: Stock Alert (Dashboard)

    Admin->>Django: GET /backoffice/dashboard/
    Django->>DB: SELECT FROM forecast_view<br/>WHERE days_until_stockout <= production_delay + 3
    DB-->>Django: Alert: SKU LM-DRS-100 → 5 days until stockout
    Django-->>Admin: Dashboard with production relaunch alerts
```

## Diagram 5 — CI/CD Pipeline (GitHub Actions)

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant GitHub
    participant Actions as GitHub Actions
    participant Postgres as PostgreSQL (Service)
    participant Server as Production Server
    participant Docker

    Note over Dev, Docker: Push triggers CI pipeline

    Dev->>GitHub: git push origin main

    GitHub->>Actions: Trigger workflow ci.yml<br/>(on push: main, develop, staging)

    Note over Actions, Postgres: Job 1 — Test

    Actions->>Postgres: Start service container<br/>postgres:16-alpine<br/>DB: lamos_test_db
    Actions->>Actions: Checkout code
    Actions->>Actions: Setup Python 3.12
    Actions->>Actions: pip install -r requirements/development.txt

    Actions->>Postgres: Run pytest<br/>DJANGO_SETTINGS_MODULE=lamos.settings.testing
    
    alt Tests pass (coverage >= 70%)
        Postgres-->>Actions: All tests green ✅
        Actions->>Actions: Upload coverage to Codecov
    else Tests fail
        Postgres-->>Actions: Failures ❌
        Actions-->>GitHub: Job failed — block merge
        GitHub-->>Dev: Email: CI failed
        Note over Dev: Fix and re-push
    end

    Note over Actions, Docker: Job 2 — Lint (parallel)

    Actions->>Actions: flake8 apps/ lamos/<br/>--max-line-length=100

    Note over Actions, Docker: Job 3 — Deploy (only on main, after test+lint)

    alt Branch is main AND test+lint passed
        Actions->>Server: SSH connect<br/>(appleboy/ssh-action)
        Server->>Server: cd /var/www/lamos-platform
        Server->>GitHub: git pull origin main
        Server->>Docker: docker compose build
        Server->>Docker: docker compose up -d
        Docker->>Docker: app: python manage.py migrate --no-input
        Docker->>Docker: app: python manage.py collectstatic --no-input
        Docker-->>Server: Deployment successful ✅
        Server-->>Actions: Exit 0
        Actions-->>GitHub: Deploy complete
        GitHub-->>Dev: Notification: deployed to production
    end
```
