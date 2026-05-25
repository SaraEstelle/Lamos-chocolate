# Stage 3 — Task 5: SCM & QA Strategies
## Lamos Chocolate — European Digital Platform

> **Project**: Lamos Chocolate — European Digital Platform
> **Team**: Sara Rebati · Valentin Planchon
> **Stack**: Django 5.x · PostgreSQL 16 · Docker · GitHub Actions

---

## 5.1 — Source Control Management (SCM)

### 5.1.1 — Tool and Platform

| Attribute | Choice |
|-----------|--------|
| **Versioning tool** | Git |
| **Hosting platform** | GitHub |
| **Repository type** | Private repository (collaborators: Sara + Valentin) |
| **URL** | `https://github.com/[org]/lamos-chocolate-platform` |
| **Task tracking** | GitHub Projects (integrated Kanban) + Notion (sprint docs) |
| **Why Git/GitHub?** | Industry standard, native GitHub Actions CI/CD integration, familiar to both team members, Holberton curriculum. |

---

### 5.1.2 — Branching Strategy (Simplified Git Flow)

The project adopts a simplified version of **Git Flow** adapted for a 2-developer team. The goal is to protect the `main` branch (always deployable) while enabling parallel feature development.

```
main (production)
│  Protected branch — merge via PR only, never commit directly
│  Automatic deployment on push (GitHub Actions)
│
staging (pre-prod / review)
│  Merge from develop before going to main
│  Used for UAT and integration testing on real Docker stack
│
develop (integration)
│  All feature branches merged here first
│  CI required before merge
│
feature/*   ← new functionality (lifetime: one sprint)
fix/*       ← bug fix (lifetime: a few hours to 2 days)
hotfix/*    ← urgent production fix (merge directly into main)
docs/*      ← documentation only
refactor/*  ← refactoring without new feature
```

**Permanent branches:**

| Branch | Role | Rules |
|--------|------|-------|
| `main` | Production code — **always deployable** | Protected. Merge only via validated PR. No direct commit. Auto-deployment on push. |
| `staging` | Pre-production test environment | Merge from `develop` before `main`. Integration tests + UAT. |
| `develop` | Continuous integration branch | All features merged here first. CI mandatory before merge. |

**Temporary branches naming:**

| Prefix | Usage | Example |
|--------|-------|---------|
| `feature/` | New functionality | `feature/stripe-checkout` |
| `fix/` | Bug fix | `fix/stock-decrement-race-condition` |
| `hotfix/` | Urgent production fix | `hotfix/webhook-500-error` |
| `docs/` | Documentation only | `docs/stage3-api-specs` |
| `refactor/` | Refactoring | `refactor/cart-service-cleanup` |

**Naming convention:** `prefix/short-descriptor-in-kebab-case`

---

### 5.1.3 — Development Workflow — Step by Step

```
1. Create a GitHub issue for the task
   (label: feature / bug / docs — assign to Sara or Valentin)

2. Create branch from develop:
   $ git checkout develop
   $ git pull origin develop
   $ git checkout -b feature/feature-name

3. Develop with atomic commits:
   $ git add .
   $ git commit -m "feat(shop): add product detail page with estimated delivery display"

4. Push branch to GitHub:
   $ git push origin feature/feature-name

5. Open a Pull Request:
   - Base: develop
   - Compare: feature/feature-name
   - Description: link to issue, summary of changes
   - Assign the other team member as reviewer

6. Code Review:
   - Reviewer reads the diff, leaves comments
   - Author resolves comments
   - Reviewer approves ✓

7. CI must pass (GitHub Actions):
   - pytest + pytest-django ✓ (PostgreSQL 16 service)
   - flake8 linting ✓

8. Squash & Merge into develop

9. Delete the feature branch (auto-deleted by GitHub setting)

10. End of sprint: develop → staging → UAT → staging → main
    (with: docker compose up, manage.py migrate, manage.py collectstatic)
```

---

### 5.1.4 — Commit Message Convention (Conventional Commits)

```
<type>(<scope>): <short description>

[Optional body — explain the why if complex]

[Optional footer — Closes #42]
```

**Commit types:**

| Type | Usage | Example |
|------|-------|---------|
| `feat` | New feature | `feat(checkout): add estimated delivery days to confirmation page` |
| `fix` | Bug fix | `fix(stock): prevent negative stock on concurrent orders` |
| `docs` | Documentation only | `docs(stage3): update architecture diagram for Django/PostgreSQL` |
| `style` | Formatting, CSS, no logic | `style(nav): adjust header responsive breakpoints` |
| `refactor` | Refactoring, no functional change | `refactor(cart): extract CartService class` |
| `test` | Add or modify tests | `test(auth): add unit tests for password reset token validation` |
| `chore` | Build, dependencies, CI config | `chore(ci): switch MySQL service to PostgreSQL 16 in GitHub Actions` |
| `perf` | Performance improvement | `perf(db): add partial index on orders WHERE status NOT IN (cancelled, refunded)` |

**Recommended scopes:** `main`, `shop`, `cart`, `checkout`, `accounts`, `customer_area`, `b2b`, `backoffice`, `forecasting`, `db`, `ci`, `docker`, `config`

**Rules:**
- Description in lowercase, no trailing period
- Maximum 72 characters on the first line
- Present imperative: "add" not "added" / "adds"
- Atomic commits: one commit = one logical change

---

### 5.1.5 — Branch Protection & Merge Rules

| Rule | GitHub Configuration |
|------|---------------------|
| **`main` branch protected** | `Require pull request reviews before merging: 1 approval minimum` |
| **CI mandatory before merge** | `Require status checks to pass: ci/pytest, ci/lint` |
| **No force push** | `Do not allow force pushes` |
| **Auto-delete branch after merge** | `Automatically delete head branches` |
| **Squash merge** | Preferred — keeps a clean `develop`/`main` history |

---

### 5.1.6 — Secrets & Environment Variables Management

Secrets are **never** committed to the Git repository.

```bash
# .gitignore
.env
.env.*
*.pyc
__pycache__/
*.sqlite3
instance/
.vscode/
.DS_Store
staticfiles/
mediafiles/
```

**`.env.example` (committed — template without values):**

```bash
# Django
DJANGO_SETTINGS_MODULE=lamos.settings.development
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL — Docker service name is "db"
DB_NAME=lamos_db
DB_USER=lamos_app
DB_PASSWORD=your_password
DB_HOST=db
DB_PORT=5432

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email — development
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Email — production (Mailgun via django-anymail)
MAILGUN_API_KEY=key-...
MAILGUN_DOMAIN=mg.lamos-eu.com
```

**Production secrets**: Stored in **GitHub Actions Secrets** and injected as environment variables during deployment. Never in plain text in `docker-compose.yml` or source code.

---

## 5.2 — Quality Assurance (QA) Strategy

### 5.2.1 — Test Pyramid Overview

```
                    ┌───────┐
                    │  UAT  │  ← Manual tests with real users (Sprint 9)
                   ┌┴───────┴┐
                   │  E2E    │  ← Manual end-to-end — critical path checklist
                  ┌┴─────────┴┐   (staging Docker environment)
                  │Integration│  ← pytest-django + Django test client
                 ┌┴───────────┴┐   (real PostgreSQL test DB)
                 │  Unit Tests │  ← pytest — models, services, utilities
                 └─────────────┘  (fast, no DB required where possible)
```

| Level | Tools | Target Coverage | Owner | Timing |
|-------|-------|----------------|-------|--------|
| **Unit Tests** | pytest + pytest-django | ≥ 85% models/services | Sara (backend) + Valentin (BI) | Continuous (parallel to dev) |
| **Integration Tests** | pytest + Django test client + PostgreSQL | Routes, DB, emails | Sara | Sprint 8 |
| **End-to-End Tests** | Manual + structured checklist | Critical paths + forecasting | Team | Sprint 8–9 |
| **UAT** | External users on staging | Full experience | Team + peers | Sprint 9 |

---

### 5.2.2 — pytest-django Configuration

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = lamos.settings.testing
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --cov=apps --cov-report=term-missing
```

```python
# lamos/settings/testing.py
from .base import *
import os

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ.get('DB_NAME', 'lamos_test_db'),
        'USER':     os.environ.get('DB_USER', 'lamos_app'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'test_password'),
        'HOST':     os.environ.get('DB_HOST', 'localhost'),
        'PORT':     '5432',
    }
}

# Emails stored in django.core.mail.outbox — no real sending
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
```

---

### 5.2.3 — Test Fixtures and Shared Helpers

```python
# tests/conftest.py

import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def sample_category(db):
    from apps.shop.models import Category
    return Category.objects.create(
        name_fr='Test', name_en='Test', slug='test-category'
    )


@pytest.fixture
def sample_shipping_zone(db):
    from apps.shop.models import ShippingZone
    return ShippingZone.objects.create(
        zone_name='Switzerland', countries=['CH'], delay_days=2, cost='8.90'
    )


@pytest.fixture
def sample_product(db, sample_category):
    from apps.shop.models import Product, SKU, Stock
    product = Product.objects.create(
        slug='test-pistachio', name_fr='Test Pistache',
        name_en='Test Pistachio', category=sample_category, is_active=True
    )
    sku = SKU.objects.create(
        product=product, sku_code='TST-PIK-100', format='Bar 100g',
        price='12.90', currency='EUR',
        production_delay_days=7, batch_size=50
    )
    stock = Stock.objects.create(sku=sku, quantity=50, threshold_alert=5)
    return product, sku, stock


@pytest.fixture
def sample_customer(db):
    from apps.shop.models import Customer
    customer = Customer(
        first_name='Marie', last_name='Test',
        email='marie.test@example.com', language_pref='fr'
    )
    customer.set_password('testpassword123')
    customer.save()
    return customer


@pytest.fixture
def logged_in_client(client, sample_customer):
    """HTTP client with active customer session."""
    session = client.session
    session['customer_id'] = sample_customer.pk
    session.save()
    return client


@pytest.fixture
def sample_admin(db):
    from apps.shop.models import AdminUser
    admin = AdminUser(
        email='admin@lamos-eu.com', first_name='Sara',
        last_name='Rebati', role='superadmin'
    )
    admin.set_password('adminpassword123')
    admin.save()
    return admin


@pytest.fixture
def admin_client(client, sample_admin):
    """HTTP client with active admin session."""
    session = client.session
    session['admin_id'] = sample_admin.pk
    session.save()
    return client
```

---

### 5.2.4 — Unit Tests

```python
# tests/unit/test_models.py
import pytest
from django.utils import timezone
from datetime import timedelta


class TestStockModel:
    def test_decrement_success(self, db, sample_product):
        _, sku, stock = sample_product
        initial_qty = stock.quantity
        stock.decrement(5)
        stock.refresh_from_db()
        assert stock.quantity == initial_qty - 5

    def test_decrement_insufficient_stock_raises(self, db, sample_product):
        _, sku, stock = sample_product
        stock.quantity = 2
        stock.save()
        with pytest.raises(ValueError, match="Insufficient stock"):
            stock.decrement(5)

    def test_is_low_when_at_threshold(self, db, sample_product):
        _, sku, stock = sample_product
        stock.quantity = 5
        stock.threshold_alert = 5
        assert stock.is_low is True

    def test_is_low_when_above_threshold(self, db, sample_product):
        _, sku, stock = sample_product
        stock.quantity = 10
        stock.threshold_alert = 5
        assert stock.is_low is False


class TestSKUForecastingModel:
    def test_estimated_days_stock_sufficient(
        self, db, sample_product, sample_shipping_zone
    ):
        """Stock covers order → return shipping delay only."""
        _, sku, stock = sample_product
        # stock=50, order=10 → sufficient → 2 days (zone delay)
        result = sku.calculate_estimated_days(10, sample_shipping_zone)
        assert result == 2

    def test_estimated_days_stock_insufficient(
        self, db, sample_product, sample_shipping_zone
    ):
        """Stock < order → compute production batches + shipping."""
        _, sku, stock = sample_product
        stock.quantity = 5
        stock.save()
        # deficit=50, batches=1, production=7d, shipping=2d → 9 days
        result = sku.calculate_estimated_days(55, sample_shipping_zone)
        assert result == 9

    def test_estimated_days_zero_stock(
        self, db, sample_product, sample_shipping_zone
    ):
        """Zero stock → full production from scratch."""
        _, sku, stock = sample_product
        stock.quantity = 0
        stock.save()
        # order=50, batch_size=50 → 1 batch → 7d + 2d = 9 days
        result = sku.calculate_estimated_days(50, sample_shipping_zone)
        assert result == 9


class TestOrderModel:
    def test_order_number_format(self):
        import re
        from apps.shop.models import Order
        order_number = Order.generate_order_number()
        assert re.match(r'^LM-\d{8}-[A-Z0-9]{5}$', order_number)

    def test_order_number_uniqueness(self):
        from apps.shop.models import Order
        numbers = {Order.generate_order_number() for _ in range(100)}
        assert len(numbers) == 100  # All unique


class TestCustomerModel:
    def test_password_hashing(self, db):
        from apps.shop.models import Customer
        customer = Customer(
            first_name='Test', last_name='User', email='test@example.com'
        )
        customer.set_password('securepassword')
        assert customer.password_hash != 'securepassword'
        assert customer.check_password('securepassword') is True
        assert customer.check_password('wrongpassword') is False

    def test_full_name_property(self, db):
        from apps.shop.models import Customer
        customer = Customer(first_name='Marie', last_name='Dupont',
                            email='m@test.com')
        assert customer.full_name == 'Marie Dupont'


class TestPasswordResetToken:
    def test_is_valid_fresh_token(self, db, sample_customer):
        from apps.shop.models import PasswordResetToken
        token = PasswordResetToken.objects.create(
            customer=sample_customer,
            token='valid-token-abc',
            expires_at=timezone.now() + timedelta(hours=1)
        )
        assert token.is_valid is True

    def test_is_valid_expired_token(self, db, sample_customer):
        from apps.shop.models import PasswordResetToken
        token = PasswordResetToken.objects.create(
            customer=sample_customer,
            token='expired-token-xyz',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        assert token.is_valid is False

    def test_is_valid_used_token(self, db, sample_customer):
        from apps.shop.models import PasswordResetToken
        token = PasswordResetToken.objects.create(
            customer=sample_customer,
            token='used-token-def',
            expires_at=timezone.now() + timedelta(hours=1),
            used=True
        )
        assert token.is_valid is False


class TestShippingZone:
    def test_get_zone_for_country_found(self, db, sample_shipping_zone):
        from apps.shop.models import ShippingZone
        zone = ShippingZone.get_zone_for_country('CH')
        assert zone is not None
        assert zone.zone_name == 'Switzerland'
        assert zone.delay_days == 2

    def test_get_zone_for_country_not_found(self, db, sample_shipping_zone):
        from apps.shop.models import ShippingZone
        zone = ShippingZone.get_zone_for_country('XX')
        assert zone is None
```

---

### 5.2.5 — Integration Tests

```python
# tests/integration/test_auth_views.py
import pytest


class TestRegistration:
    def test_register_success(self, client, db):
        response = client.post('/en/accounts/register/', {
            'first_name': 'Alice', 'last_name':  'Martin',
            'email':      'alice@test.com',
            'password1':  'securePass123', 'password2': 'securePass123'
        }, follow=True)
        assert response.status_code == 200
        from apps.shop.models import Customer
        customer = Customer.objects.get(email='alice@test.com')
        assert customer.check_password('securePass123')

    def test_register_duplicate_email(self, client, db, sample_customer):
        response = client.post('/en/accounts/register/', {
            'email':     'marie.test@example.com',
            'password1': 'pass123', 'password2': 'pass123'
        })
        assert response.status_code == 200
        # Form re-rendered with validation error

    def test_register_password_mismatch(self, client, db):
        response = client.post('/en/accounts/register/', {
            'email':     'new@test.com',
            'password1': 'password123',
            'password2': 'different456'
        })
        assert response.status_code == 200


class TestLogin:
    def test_login_success(self, client, db, sample_customer):
        response = client.post('/en/accounts/login/', {
            'email':    'marie.test@example.com',
            'password': 'testpassword123'
        }, follow=True)
        assert response.status_code == 200

    def test_login_wrong_password(self, client, db, sample_customer):
        response = client.post('/en/accounts/login/', {
            'email':    'marie.test@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert b'incorrect' in response.content.lower() \
            or b'invalid' in response.content.lower()

    def test_protected_route_redirects_anonymous(self, client):
        response = client.get('/en/my-account/')
        assert response.status_code == 302
        assert 'accounts/login' in response['Location']


# tests/integration/test_cart_api.py
class TestCartAPI:
    def test_add_to_cart_success(self, client, db, sample_product):
        _, sku, _ = sample_product
        response = client.post(
            '/api/cart/add/',
            data=f'{{"sku_id": {sku.pk}, "quantity": 2}}',
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['cart_count'] == 2

    def test_add_exceeds_stock(self, client, db, sample_product):
        _, sku, stock = sample_product
        stock.quantity = 1
        stock.save()
        response = client.post(
            '/api/cart/add/',
            data=f'{{"sku_id": {sku.pk}, "quantity": 5}}',
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['available_quantity'] == 1

    def test_add_nonexistent_sku(self, client):
        response = client.post(
            '/api/cart/add/',
            data='{"sku_id": 99999, "quantity": 1}',
            content_type='application/json'
        )
        assert response.status_code == 404


# tests/integration/test_checkout_webhook.py
from unittest.mock import patch


class TestStripeWebhook:
    def test_valid_webhook_returns_200(self, client, db):
        mock_event = {
            'type': 'payment_intent.succeeded',
            'data': {'object': {
                'id': 'pi_test_123', 'amount': 1290,
                'currency': 'eur',
                'metadata': {'customer_email': 'test@example.com'}
            }}
        }
        with patch('stripe.Webhook.construct_event', return_value=mock_event):
            response = client.post(
                '/checkout/webhook/',
                data=b'{}',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='t=123,v1=abc'
            )
        assert response.status_code == 200
        assert response.json()['status'] == 'received'

    def test_invalid_signature_returns_400(self, client):
        import stripe
        with patch(
            'stripe.Webhook.construct_event',
            side_effect=stripe.error.SignatureVerificationError('msg', 'sig')
        ):
            response = client.post(
                '/checkout/webhook/',
                data=b'{}',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='invalid'
            )
        assert response.status_code == 400

    def test_invalid_payload_returns_400(self, client):
        with patch(
            'stripe.Webhook.construct_event',
            side_effect=ValueError('No payload')
        ):
            response = client.post(
                '/checkout/webhook/',
                data=b'not-json',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='t=123,v1=abc'
            )
        assert response.status_code == 400
```

---

### 5.2.6 — End-to-End Test Checklist (Manual)

```markdown
# E2E CHECKLIST — LAMOS CHOCOLATE PLATFORM
Environment  : staging.lamos-eu.com (Docker Compose)
Date         : ___________
Executed by  : ___________

## PATH 1 — Complete B2C Purchase
[ ] 1.  Access homepage (FR)
[ ] 2.  Switch to EN — all texts change language
[ ] 3.  Navigate to /en/shop/ — catalog loaded in English
[ ] 4.  Click a product — detail page with estimated delivery displayed
[ ] 5.  Add 2 items — header cart counter updated (AJAX)
[ ] 6.  Access cart — items listed, quantities correct, total accurate
[ ] 7.  Edit quantity — total recalculated
[ ] 8.  Remove an item — cart updated
[ ] 9.  Attempt checkout without login → redirect to login
[ ] 10. Log in → redirect to checkout
[ ] 11. Fill in shipping address (country: CH)
[ ] 12. Estimated delivery recalculated based on Switzerland zone (2 days)
[ ] 13. Click "Pay" → redirect to Stripe Checkout
[ ] 14. Enter Stripe test card (4242 4242 4242 4242, future expiry, any CVC)
[ ] 15. Payment confirmed → redirect to confirmation page
[ ] 16. Confirmation page shows: order number + estimated delivery (2 days)
[ ] 17. Confirmation email received with estimated delivery included
[ ] 18. Check DB: order created status='paid', stock decremented,
         estimated_delivery_days=2

## PATH 2 — Customer Account & History
[ ] 19. Register with valid email
[ ] 20. Log in → access /my-account/
[ ] 21. Order history — order from path 1 visible
[ ] 22. Order detail — correct items, amount, status
[ ] 23. Password reset — email received, link works, new password active

## PATH 3 — B2B Form
[ ] 24. Access /fr/b2b/
[ ] 25. Submit form with all required fields
[ ] 26. Confirmation page displayed
[ ] 27. Notification email received at Lamos address
[ ] 28. DB: B2BRequest created status='new', ip_address recorded

## PATH 4 — Backoffice Admin Panel
[ ] 29. Admin login
[ ] 30. Dashboard — KPIs visible (orders, revenue, low stock alerts)
[ ] 31. Dashboard — production relaunch alerts visible (forecasting)
[ ] 32. Create a new product (CRUD form with production_delay_days, batch_size)
[ ] 33. New product visible in /shop/ catalog
[ ] 34. Update SKU stock quantity
[ ] 35. Stock change immediately visible on product page
[ ] 36. View B2B requests — request from path 3 present
[ ] 37. Change B2B request status → 'in_progress'
[ ] 38. Access /backoffice/ with customer session → 403 Forbidden

## SECURITY TESTS
[ ] 39. Access /my-account/ without login → redirect to login
[ ] 40. Access another customer's order → 404 (no leak)
[ ] 41. Webhook without Stripe signature → 400
[ ] 42. CSRF: form submission without token → rejected (Django built-in)
[ ] 43. Direct SQL injection attempt in form fields → safe (Django ORM)

## FORECASTING VALIDATION
[ ] 44. Product page (sufficient stock): estimated delivery = zone delay only
[ ] 45. Product page (insufficient stock): estimated delivery = production + zone
[ ] 46. Admin dashboard: SKU alert if days_until_stockout ≤ production_delay + 3
[ ] 47. Confirmation email contains correct estimated delivery days

## RESPONSIVE TESTS
[ ] 48. Homepage at 375px (mobile) — hamburger menu visible
[ ] 49. Catalog at 768px (tablet) — responsive grid
[ ] 50. Checkout on mobile — form usable, no horizontal scroll

## i18n VALIDATION
[ ] 51. All pages visited above in EN: no visible FR text
[ ] 52. Confirmation email sent in session language
[ ] 53. B2B confirmation email in customer's language

## PERFORMANCE
[ ] 54. Homepage < 3s load time (Chrome DevTools Network)
[ ] 55. Catalog < 3s
[ ] 56. Product images: WebP format, < 200KB each
```

---

### 5.2.7 — User Acceptance Testing (UAT) — Sprint 9

**UAT Protocol:**

| Attribute | Detail |
|-----------|--------|
| **When** | Sprint 9 — Weeks 10–11 (June 22 – July 11, 2026) |
| **Who** | Minimum 2 external testers (Holberton peers or network) |
| **Environment** | Staging — realistic data, Stripe in test mode |
| **Duration** | 30–45 minutes per tester |

**UAT scenario for tester:**

> *"You are Marie, a French expatriate living in Geneva. You heard about Lamos Chocolate from a friend. You want to buy a gift box for your mother's birthday. Explore the site freely, create an account, buy something, and tell us what you think."*

**UAT feedback form:**

| Question | Scale |
|----------|-------|
| Navigation on the site was intuitive | 1 (not at all) → 5 (completely) |
| I easily found the product I was looking for | 1 → 5 |
| The payment process was simple and reassuring | 1 → 5 |
| The site gives a premium / luxury brand feel | 1 → 5 |
| The delivery time information was clear | 1 → 5 |
| I encountered technical issues | Yes / No + description |
| What I liked most | Free text |
| What bothered me or seemed to be missing | Free text |

---

### 5.2.8 — GitHub Actions CI Configuration

```yaml
# .github/workflows/ci.yml

name: CI — Lamos Chocolate Platform (Django + PostgreSQL 16)

on:
  push:
    branches: [ main, develop, staging ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB:       lamos_test_db
          POSTGRES_USER:     lamos_app
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements/development.txt') }}

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements/development.txt
          pip install pytest pytest-django pytest-cov

      - name: Run tests with coverage
        env:
          DJANGO_SETTINGS_MODULE: lamos.settings.testing
          DB_NAME:     lamos_test_db
          DB_USER:     lamos_app
          DB_PASSWORD: test_password
          DB_HOST:     localhost
          DB_PORT:     5432
          SECRET_KEY:  ci-test-secret-key-not-for-production
          STRIPE_SECRET_KEY:     ${{ secrets.STRIPE_TEST_SECRET_KEY }}
          STRIPE_WEBHOOK_SECRET: ${{ secrets.STRIPE_TEST_WEBHOOK_SECRET }}
        run: |
          pytest tests/ -v \
            --cov=apps \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=70

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install flake8
        run: pip install flake8
      - name: Run linting
        run: |
          flake8 apps/ lamos/ \
            --max-line-length=100 \
            --ignore=E501,W503 \
            --exclude=migrations

  deploy:
    needs: [test, lint]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host:     ${{ secrets.PROD_SERVER_HOST }}
          username: ${{ secrets.PROD_SERVER_USER }}
          key:      ${{ secrets.PROD_SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/lamos-platform
            git pull origin main
            docker compose build --no-cache
            docker compose up -d
            docker compose exec -T app python manage.py migrate --no-input
            docker compose exec -T app python manage.py collectstatic --no-input
            echo "✅ Deployment successful at $(date)"
```

---

### 5.2.9 — Test Coverage Targets

| Module | Target Coverage | Priority |
|--------|----------------|----------|
| `apps/shop/models.py` | ≥ 85% | Critical |
| `apps/checkout/services.py` | ≥ 80% | Critical |
| `apps/cart/services.py` | ≥ 75% | Critical |
| `apps/forecasting/services.py` | ≥ 80% | Critical (new) |
| `apps/accounts/views.py` | ≥ 80% | Critical |
| `apps/backoffice/views.py` | ≥ 70% | Important |
| `apps/b2b/views.py` | ≥ 70% | Important |
| `apps/shop/views.py` | ≥ 65% | Normal |
| **Global** | **≥ 70%** | **CI threshold — build fails below** |

---

### 5.2.10 — Production Monitoring & Logging

| Aspect | Tool / Method |
|--------|--------------|
| **Application logs** | `logging` Python → `/var/log/lamos/django.log` + rotation |
| **ERROR/CRITICAL logs** | Immediate email alert to the team |
| **Uptime monitoring** | UptimeRobot (free) — email alert if site goes down |
| **DB performance** | `pg_stat_statements` PostgreSQL extension — slow query detection |
| **Custom 500 page** | `handler500 = 'apps.main.views.server_error_view'` |
| **Docker health checks** | `healthcheck` defined for `db` service in `docker-compose.yml` |

---

## 5.3 — SCM & QA Summary

| Domain | Decision | Justification |
|--------|----------|---------------|
| Versioning | Git + GitHub | Standard, Holberton curriculum, native CI/CD |
| Branch strategy | Simplified Git Flow (main/staging/develop/feature) | Production protection, parallel development |
| Commit messages | Conventional Commits | Readable history, automatable changelog |
| Tests | pytest + pytest-django | Python standard, powerful fixtures, native Django integration |
| CI | GitHub Actions + PostgreSQL 16 Alpine | Built into GitHub, free, exact production DB version |
| Minimum coverage | 70% (CI threshold) | Quality/speed balance in MVP context |
| E2E | Manual tests with structured checklist | Covers critical paths including forecasting |
| UAT | 2 external testers on staging Docker | Real-world experience validation |
| Secrets | Environment variables + GitHub Actions Secrets | Never in plain text in code |
| Docker | Unified dev/staging/prod environment | Full reproducibility, no "works on my machine" |

---