# Stage 3 — Task 4: API Specifications
## Lamos Chocolate — European Digital Platform

> **Project**: Lamos Chocolate — European Digital Platform
> **Team**: Sara Rebati · Valentin Planchon
> **Stack**: Django 5.x · PostgreSQL 16 · Docker

---

## 4.1 — External APIs Used

### 4.1.1 — Stripe API

| Attribute | Detail |
|-----------|--------|
| **Provider** | Stripe, Inc. |
| **Documentation** | https://stripe.com/docs/api |
| **Python SDK** | `stripe` (version ≥ 7.x) |
| **Authentication** | Secret API key `sk_test_...` (test) / `sk_live_...` (prod) |
| **Why Stripe?** | Best developer experience on the market, native Python SDK, robust test mode, delegated PCI-DSS compliance, reliable webhooks, exhaustive documentation. Alternatives like PayPal or Mollie were considered but Stripe offers the best DX for a Django MVP. |

**Stripe endpoints used:**

| Stripe Endpoint | Method | Usage in Project |
|-----------------|--------|------------------|
| `/v1/checkout/sessions` | POST | Create a hosted payment session |
| `/v1/payment_intents/{id}` | GET | Verify payment status (admin) |
| Webhook reception | POST | Listen to `payment_intent.succeeded` events |

**Django configuration:**

```python
# lamos/settings/base.py
import os

STRIPE_PUBLIC_KEY     = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY     = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
```

**Stripe checkout session service:**

```python
# apps/checkout/services.py

import stripe
from django.conf import settings
from django.urls import reverse

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(cart_items, customer_email, lang='fr', request=None):
    """
    Creates a Stripe Checkout session for the cart items.

    :param cart_items: list of dicts {sku_id, name, price, quantity, currency, format}
    :param customer_email: logged-in customer's email
    :param lang: active language ('fr' or 'en')
    :param request: Django request object (for building absolute URLs)
    :return: dict {session_id, checkout_url}
    """
    line_items = []
    for item in cart_items:
        line_items.append({
            'price_data': {
                'currency': item['currency'].lower(),
                'unit_amount': int(item['price'] * 100),  # Stripe uses cents
                'product_data': {
                    'name':        item['name'],
                    'description': item.get('format', ''),
                },
            },
            'quantity': item['quantity'],
        })

    success_url = request.build_absolute_uri(
        reverse('checkout:confirmation') + '?session_id={CHECKOUT_SESSION_ID}'
    )
    cancel_url = request.build_absolute_uri(reverse('cart:view'))

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        customer_email=customer_email,
        success_url=success_url,
        cancel_url=cancel_url,
        locale=lang,
        metadata={'customer_email': customer_email},
    )

    return {
        'session_id':    session.id,
        'checkout_url':  session.url,
    }


def handle_payment_success(payment_intent, cart_items, customer, shipping_data,
                            estimated_days):
    """
    Called by the webhook handler after payment_intent.succeeded.
    Creates the order, order items, and decrements stock atomically.
    """
    from apps.shop.models import Order, OrderItem, Stock
    from django.db import transaction

    with transaction.atomic():
        order = Order.objects.create(
            customer=customer,
            order_number=Order.generate_order_number(),
            status='paid',
            total_amount=payment_intent['amount'] / 100,
            currency=payment_intent['currency'].upper(),
            stripe_payment_id=payment_intent['id'],
            estimated_delivery_days=estimated_days,
            **shipping_data,
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                sku_id=item['sku_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                subtotal=item['subtotal'],
            )
            stock = Stock.objects.select_for_update().get(sku_id=item['sku_id'])
            stock.decrement(item['quantity'])

    return order
```

**Stripe webhook handler:**

```python
# apps/checkout/views.py

import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.template.loader import render_to_string


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Receives Stripe webhook events. Must be exempt from CSRF
    (Stripe sends raw POST, not a Django form).
    Signature is verified via STRIPE_WEBHOOK_SECRET.
    """
    payload    = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        _handle_payment_success(payment_intent)

    elif event['type'] == 'payment_intent.payment_failed':
        _log_payment_failure(event['data']['object'])

    elif event['type'] == 'checkout.session.expired':
        _log_session_expiry(event['data']['object'])

    # Always return 200 quickly — Stripe will retry if it gets anything else
    return JsonResponse({'status': 'received'}, status=200)
```

---

### 4.1.2 — SMTP Email (django.core.mail + django-anymail)

| Attribute | Detail |
|-----------|--------|
| **Development** | `django.core.mail.backends.console.EmailBackend` (output to console) |
| **Production** | `anymail.backends.mailgun.EmailBackend` (Mailgun REST API) |
| **Port** | 587 (TLS) for direct SMTP |
| **Why django-anymail?** | Native Django integration, clean configuration, supports Mailgun/SendGrid/Postmark |

**Configuration:**

```python
# lamos/settings/base.py
EMAIL_BACKEND      = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST         = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT         = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS      = True
EMAIL_HOST_USER    = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'Lamos Chocolate <noreply@lamos-eu.com>'

# lamos/settings/production.py
EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
ANYMAIL = {
    'MAILGUN_API_KEY':        os.environ.get('MAILGUN_API_KEY'),
    'MAILGUN_SENDER_DOMAIN':  os.environ.get('MAILGUN_DOMAIN'),
}

# lamos/settings/testing.py
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
# Emails stored in django.core.mail.outbox during tests
```

---

## 4.2 — Internal API — Django Views & URL Patterns

### Naming Convention

| Convention | Format | Example |
|------------|--------|---------|
| i18n URL | `i18n_patterns(...)` | `/fr/shop/`, `/en/shop/` |
| URL variables | `<type:name>` | `<slug:product_slug>`, `<int:pk>` |
| AJAX API | `/api/` prefix | `/api/cart/add/` |
| Custom admin | `/backoffice/` prefix | `/backoffice/products/` |
| Django Admin | `/admin/` | Superusers only |

**Root URL configuration:**

```python
# lamos/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # Django native admin — superusers only
    path('admin/', admin.site.urls),
    # AJAX endpoints — no i18n prefix needed
    path('api/cart/', include('apps.cart.urls_api')),
    # Stripe webhook — must be exempt from i18n and CSRF
    path('checkout/webhook/', include('apps.checkout.urls_webhook')),
    # i18n language prefix for all user-facing routes
] + i18n_patterns(
    path('',             include('apps.main.urls')),
    path('shop/',        include('apps.shop.urls')),
    path('cart/',        include('apps.cart.urls')),
    path('checkout/',    include('apps.checkout.urls')),
    path('accounts/',    include('apps.accounts.urls')),
    path('my-account/',  include('apps.customer_area.urls')),
    path('b2b/',         include('apps.b2b.urls')),
    path('backoffice/',  include('apps.backoffice.urls')),
)
```

---

### MODULE: MAIN (Storefront & Navigation)

---

**`GET /<lang>/`**

| Attribute | Value |
|-----------|-------|
| Django View | `MainIndexView(TemplateView)` |
| URL name | `main:index` |
| Auth required | No |
| Template | `main/index.html` |
| Logic | `Product.objects.filter(is_active=True).prefetch_related('skus__stock')[:3]` — 3 featured products |

---

**`GET /<lang>/about/`**

| Attribute | Value |
|-----------|-------|
| Django View | `AboutView(TemplateView)` |
| URL name | `main:about` |
| Auth required | No |
| Template | `main/about.html` |

---

**`GET/POST /i18n/set_language/`** *(Django built-in)*

| Attribute | Value |
|-----------|-------|
| Mechanism | `django.views.i18n.set_language` (native) |
| Input | `language` (POST field) + `next` (redirect URL) |
| Output | HTTP 302 redirect |
| Logic | Sets `django_language` cookie (30 days) + redirects |

---

### MODULE: SHOP (Catalog)

---

**`GET /<lang>/shop/`**

| Attribute | Value |
|-----------|-------|
| Django View | `CatalogView(ListView)` |
| URL name | `shop:catalog` |
| Auth required | No |
| Query params | `category` (str, optional) — category slug for filtering |
| Template | `shop/catalog.html` |
| Logic | `Product.objects.filter(is_active=True).prefetch_related('skus__stock')` — optional filter by `category__slug` |

**Example request:** `GET /en/shop/?category=coffrets`

---

**`GET /<lang>/shop/<slug:product_slug>/`**

| Attribute | Value |
|-----------|-------|
| Django View | `ProductDetailView(DetailView)` |
| URL name | `shop:product_detail` |
| Auth required | No |
| URL params | `product_slug` (str) — unique product identifier |
| Template | `shop/product.html` |
| Error codes | `Http404` if slug unknown or product inactive |
| Logic | `get_object_or_404(Product, slug=product_slug, is_active=True)` with eager loading of skus and stock. If customer is logged in, computes `estimated_delivery_days` using `ShippingZone.get_zone_for_country(customer.country)` |

---

### MODULE: CART

---

**`GET /<lang>/cart/`**

| Attribute | Value |
|-----------|-------|
| Django View | `CartView(View)` |
| URL name | `cart:view` |
| Auth required | No (session-based cart) |
| Template | `cart/cart.html` |
| Logic | Reads `request.session['cart']` dict and enriches it with product data from DB via `SKU.objects.filter(pk__in=cart.keys())` |

---

**`POST /api/cart/add/`**

| Attribute | Value |
|-----------|-------|
| Django View | `CartAddView(View)` — `@require_POST` |
| URL name | `cart:api_add` |
| Auth required | No |
| Content-Type | `application/json` |
| Description | Adds an item to the cart (AJAX endpoint) |

**Request body:**
```json
{
  "sku_id": 3,
  "quantity": 2
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "cart_count": 3,
  "subtotal": "77.80",
  "currency": "EUR",
  "message": "Product added to cart"
}
```

**Response 400 Bad Request:**
```json
{
  "success": false,
  "error": "Insufficient stock",
  "available_quantity": 1
}
```

**Response 404 Not Found:**
```json
{
  "success": false,
  "error": "Product not found"
}
```

**Server logic:**
1. Retrieve SKU from DB — `get_object_or_404(SKU, pk=sku_id, is_active=True)`
2. Check `stock.quantity >= requested_quantity`
3. If `sku_id` already in `request.session['cart']` → increment, else add
4. `request.session.modified = True`
5. Return new total count and subtotal

---

**`POST /api/cart/update/`**

| Attribute | Value |
|-----------|-------|
| Django View | `CartUpdateView(View)` |
| URL name | `cart:api_update` |
| Description | Updates the quantity of a cart item |

**Request body:**
```json
{
  "sku_id": 3,
  "quantity": 1
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "cart_count": 2,
  "item_subtotal": "38.90",
  "total": "51.80",
  "currency": "EUR"
}
```

> If `quantity = 0` → the item is removed from the cart.

---

**`POST /api/cart/remove/`**

| Attribute | Value |
|-----------|-------|
| Django View | `CartRemoveView(View)` |
| URL name | `cart:api_remove` |
| Description | Removes an item from the cart |

**Request body:**
```json
{
  "sku_id": 3
}
```

**Response 200 OK:**
```json
{
  "success": true,
  "cart_count": 1,
  "total": "12.90",
  "currency": "EUR"
}
```

---

### MODULE: CHECKOUT (Stripe Payment)

---

**`GET /<lang>/checkout/`**

| Attribute | Value |
|-----------|-------|
| Django View | `CheckoutView(LoginRequiredMixin, View)` |
| URL name | `checkout:view` |
| Auth required | Yes (`LoginRequiredMixin`) |
| Template | `checkout/checkout.html` |
| Logic | Verifies cart is not empty, pre-fills address from customer profile, **computes estimated delivery days** using `ShippingZone.get_zone_for_country(customer.country)` |

---

**`POST /<lang>/checkout/create-session/`**

| Attribute | Value |
|-----------|-------|
| Django View | `CreateStripeSessionView(LoginRequiredMixin, View)` |
| URL name | `checkout:create_session` |
| Auth required | Yes |
| Content-Type | `application/json` |
| Description | Creates a Stripe Checkout session and returns the redirect URL |

**Request body:**
```json
{
  "shipping_address": {
    "first_name":   "Marie",
    "last_name":    "Dupont",
    "address1":     "12 Rue du Lac",
    "city":         "Genève",
    "postal_code":  "1201",
    "country":      "CH"
  }
}
```

**Response 200 OK:**
```json
{
  "success":      true,
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_...",
  "session_id":   "cs_test_..."
}
```

**Response 400 — Empty cart:**
```json
{
  "success": false,
  "error":   "Your cart is empty"
}
```

---

**`POST /checkout/webhook/`**

| Attribute | Value |
|-----------|-------|
| Django View | `stripe_webhook` (function-based, `@csrf_exempt`) |
| URL name | `checkout:webhook` |
| Auth required | No (Stripe signature via `STRIPE_WEBHOOK_SECRET`) |
| Note | Must be outside `i18n_patterns` — Stripe sends raw POST |

**Required header:**
```
Stripe-Signature: t=...,v1=...,v0=...
```

**Events handled:**

| Event | Action |
|-------|--------|
| `payment_intent.succeeded` | Create order + create order items + decrement stock + send confirmation email |
| `payment_intent.payment_failed` | Log failure (monitoring) |
| `checkout.session.expired` | Log expiry |

**Response:** `HTTP 200 {"status": "received"}` — Stripe always expects a fast 200.

---

**`GET /<lang>/checkout/confirmation/`**

| Attribute | Value |
|-----------|-------|
| Django View | `OrderConfirmationView(LoginRequiredMixin, View)` |
| URL name | `checkout:confirmation` |
| Auth required | Yes |
| Query params | `session_id` (str) — `cs_test_...` |
| Template | `checkout/confirmation.html` |
| Logic | `get_object_or_404(Order, stripe_session_id=session_id, customer=customer)` — verifies ownership |

---

### MODULE: ACCOUNTS (Customer Authentication)

---

**`GET /accounts/register/`** / **`POST /accounts/register/`**

| Attribute | Value |
|-----------|-------|
| Django View | `CustomerRegistrationView(View)` |
| Mixin | None (public route) |
| Form | `CustomerRegistrationForm(forms.Form)` |

**POST fields expected:**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `first_name` | string | Yes | 1–100 chars |
| `last_name` | string | Yes | 1–100 chars |
| `email` | string | Yes | Valid email format, unique in DB |
| `password1` | string | Yes | Min 8 chars |
| `password2` | string | Yes | Must match `password1` |

**Responses:**
- `302 redirect /accounts/login/` — successful registration
- `200` + re-render with inline errors if validation fails

---

**`GET /accounts/login/`** / **`POST /accounts/login/`**

| Attribute | Value |
|-----------|-------|
| Django View | `CustomerLoginView(View)` |
| Form | `CustomerLoginForm(forms.Form)` |

**POST fields:**

| Field | Required |
|-------|----------|
| `email` | Yes |
| `password` | Yes |
| `remember` | No (checkbox, bool — extends session duration) |

**Responses:**
- `302 redirect /my-account/` (or `next` param) — successful login
- `200` + re-render with generic error message if failed (no user enumeration)

---

**`GET /accounts/logout/`**

| Description | Logs out the customer, clears Django session |
|-------------|----------------------------------------------|
| Auth required | Yes |
| Logic | `del request.session['customer_id']` + `request.session.flush()` |
| Response | `302 redirect /` |

---

**`POST /accounts/forgot-password/`**

| POST field | `email` (string) |
|------------|------------------|
| Response | Always `302` to confirmation page (even if email unknown — anti-enumeration) |
| Logic | Generates `secrets.token_urlsafe(32)` + `PasswordResetToken.objects.create(expires_at=+1h)` |

---

**`GET /accounts/reset-password/<str:token>/`** / **`POST /accounts/reset-password/<str:token>/`**

| GET | Validates token, displays reset form |
|-----|--------------------------------------|
| POST | Applies new password |
| Logic | `get_object_or_404(PasswordResetToken, token=token)` + `token.is_valid` check |
| Error codes | `400` if token invalid, expired, or already used |

---

### MODULE: CUSTOMER AREA

---

**`GET /<lang>/my-account/`**

| Auth required | Yes (`@login_required` or `LoginRequiredMixin`) |
|---------------|------------------------------------------------|
| Django View | `CustomerDashboardView(LoginRequiredMixin, TemplateView)` |
| Template | `customer_area/dashboard.html` |
| Description | Customer dashboard — profile summary + quick order access |

---

**`GET /<lang>/my-account/orders/`**

| Auth required | Yes |
|---------------|-----|
| Django View | `OrderListView(LoginRequiredMixin, ListView)` |
| Template | `customer_area/orders.html` |
| Logic | `Order.objects.filter(customer=customer).order_by('-created_at').prefetch_related('items__sku')` |

---

**`GET /<lang>/my-account/orders/<int:pk>/`**

| Auth required | Yes |
|---------------|-----|
| Django View | `OrderDetailView(LoginRequiredMixin, DetailView)` |
| Logic | `get_object_or_404(Order, pk=pk, customer=customer)` |
| Error codes | `404` if order unknown or `customer` mismatch (no 403 leak — always 404) |

---

### MODULE: B2B

---

**`GET /<lang>/b2b/`**

| Description | Presentation page + B2B form |
|-------------|------------------------------|
| Django View | `B2BView(TemplateView)` |
| Auth required | No |
| Template | `b2b/b2b.html` |

---

**`POST /<lang>/b2b/submit/`**

| Attribute | Value |
|-----------|-------|
| Django View | `B2BSubmitView(View)` |
| Auth required | No |
| Form | `B2BRequestForm(forms.Form)` |

**POST fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_name` | string | Yes | Company name |
| `contact_name` | string | Yes | Contact name |
| `contact_email` | string | Yes | Professional email |
| `contact_phone` | string | No | Phone number |
| `sector` | string | No | Business sector |
| `estimated_qty` | integer | No | Estimated quantity |
| `occasion` | string | No | Occasion / use case |
| `message` | text | No | Free-form message |

**Responses:**
- `302 redirect /b2b/confirmation/` — successful submission
- `200` + re-render with errors — validation failed

**Server logic:**
1. `B2BRequestForm(request.POST).is_valid()`
2. `B2BRequest.objects.create(status='new', ip_address=request.META.get('REMOTE_ADDR'), language=lang)`
3. `send_mail()` to `contact@lamos-chocolate.com` with full request details
4. `redirect('b2b:confirmation')`

---

### MODULE: BACKOFFICE (Custom Admin Panel)

---

**`GET /backoffice/dashboard/`**

| Auth required | Yes — `@admin_required` custom decorator |
|---------------|------------------------------------------|
| Django View | `BackofficeDashboardView(View)` |
| Template | `backoffice/dashboard.html` |
| Data displayed | Orders today, monthly revenue, pending B2B requests, low stock alerts, **production relaunch alerts** (new — forecasting) |

```python
# apps/backoffice/decorators.py

from functools import wraps
from django.http import HttpResponseForbidden
from apps.shop.models import AdminUser


def admin_required(view_func):
    """Custom decorator verifying admin session on every backoffice request."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        admin_id = request.session.get('admin_id')
        if not admin_id:
            from django.shortcuts import redirect
            return redirect('backoffice:login')
        try:
            admin = AdminUser.objects.get(pk=admin_id, is_active=True)
        except AdminUser.DoesNotExist:
            return HttpResponseForbidden()
        request.current_admin = admin
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

**`GET /backoffice/products/`**

| Description | Lists all products with their SKUs and stock levels |
|-------------|-----------------------------------------------------|
| Logic | `Product.objects.all().prefetch_related('skus__stock')` |

---

**`GET /backoffice/products/new/`** / **`POST /backoffice/products/new/`**

| Description | Creates a new product + SKU + initial stock |
|-------------|----------------------------------------------|
| Content-Type | `multipart/form-data` (image upload) |

**Key POST fields:**

| Field | Required | Note |
|-------|----------|------|
| `name_fr`, `name_en` | Yes | |
| `description_fr`, `description_en` | No | |
| `ingredients_fr`, `allergens_fr` | No | |
| `category_id` | Yes | FK to `categories` |
| `sku_code` | Yes | Must be unique |
| `format` | Yes | e.g. "Bar 100g" |
| `price` | Yes | DECIMAL |
| `currency` | Yes | EUR or CHF |
| `production_delay_days` | Yes | Default 7 — forecasting |
| `batch_size` | Yes | Default 50 — forecasting |
| `initial_stock` | Yes | `Stock.quantity` initial value |
| `image` | No | Uploaded file — saved to `MEDIA_ROOT` |

---

**`GET /backoffice/products/<int:pk>/edit/`** / **`POST /backoffice/products/<int:pk>/edit/`**

| Description | Updates an existing product |
|-------------|------------------------------|
| Input | Same fields as creation |
| Response | `302 redirect /backoffice/products/` with success flash |

---

**`POST /backoffice/products/<int:pk>/delete/`**

| Description | Soft-deletes a product (`is_active=False`) |
|-------------|---------------------------------------------|
| Logic | `Product.objects.filter(pk=pk).update(is_active=False)` — preserves historical order integrity |
| Input | CSRF token in form |

---

**`POST /backoffice/stock/<int:sku_id>/update/`**

| Description | Updates the stock quantity of a SKU |
|-------------|--------------------------------------|
| Auth required | Yes — `@admin_required` |

**Request body (JSON or form):**
```json
{
  "quantity": 75
}
```

**Response 200 OK:**
```json
{
  "success":      true,
  "sku_id":       3,
  "new_quantity": 75,
  "is_low":       false
}
```

**Server logic:**
```python
stock = get_object_or_404(Stock, sku_id=sku_id)
stock.quantity   = int(request.POST.get('quantity', 0))
stock.updated_by = request.current_admin
stock.save(update_fields=['quantity', 'updated_at', 'updated_by'])
```

---

**`GET /backoffice/orders/`**

| Description | Lists all orders, filterable by status |
|-------------|----------------------------------------|
| Query params | `status` (optional): paid, shipped, delivered, etc. |
| Logic | `Order.objects.all().order_by('-created_at').select_related('customer')` |

---

**`POST /backoffice/orders/<int:pk>/update-status/`**

| Description | Updates an order's status |
|-------------|---------------------------|

**Request body:**
```json
{
  "status": "shipped"
}
```

**Response 200 OK:**
```json
{
  "success":    true,
  "order_id":   42,
  "new_status": "shipped"
}
```

---

**`GET /backoffice/b2b/`**

| Description | Lists all B2B requests |
|-------------|------------------------|
| Query params | `status` (optional): new, in_progress, converted, refused |

---

**`POST /backoffice/b2b/<int:pk>/update-status/`**

**Request body:**
```json
{
  "status": "in_progress"
}
```

**Response 200 OK:**
```json
{
  "success":    true,
  "request_id": 7,
  "new_status": "in_progress"
}
```

---

## 4.3 — HTTP Status Codes Used

| Code | Meaning | Usage in Project |
|------|---------|-----------------|
| `200 OK` | Success | HTML responses, AJAX JSON responses |
| `302 Found` | Redirect | After POST (PRG pattern), auth redirects |
| `400 Bad Request` | Invalid request | Form validation failed, empty cart, invalid JSON |
| `403 Forbidden` | Access denied | Non-admin tries to access `/backoffice/` |
| `404 Not Found` | Resource not found | Unknown product, order not owned by customer |
| `500 Internal Server Error` | Server error | Unexpected error (logged + alerted) |

---

## 4.4 — Endpoint Security

| Mechanism | Endpoints | Implementation |
|-----------|-----------|----------------|
| **CSRF Protection** | All POST forms | `django.middleware.csrf.CsrfViewMiddleware` (built-in, always active) — `@csrf_exempt` **only** for `/checkout/webhook/` |
| **`LoginRequiredMixin`** | `/checkout/`, `/my-account/*` | Django mixin or `@login_required` decorator |
| **`@admin_required`** | `/backoffice/*` | Custom decorator checking `session['admin_id']` + `admin.role` |
| **Ownership check** | `/my-account/orders/<pk>/` | `get_object_or_404(Order, pk=pk, customer=customer)` — no information leak |
| **Webhook signature** | `/checkout/webhook/` | `stripe.Webhook.construct_event()` with `STRIPE_WEBHOOK_SECRET` |
| **Environment variables** | All API keys | `.env` + `python-decouple`, never hardcoded |
| **Atomic stock decrement** | Webhook handler | `Stock.objects.select_for_update().get(...)` inside `transaction.atomic()` |

---

## 4.5 — Environment Variables Reference

```bash
# .env.example

# Django
DJANGO_SETTINGS_MODULE=lamos.settings.development
SECRET_KEY=your-very-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL (Docker service name: db)
DB_NAME=lamos_db
DB_USER=lamos_app
DB_PASSWORD=your_password
DB_HOST=db
DB_PORT=5432

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email — development (console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Email — production (Mailgun via django-anymail)
MAILGUN_API_KEY=key-...
MAILGUN_DOMAIN=mg.lamos-eu.com
```

---