# Sequence Diagrams — 5 key flows

Here's fives cases of Sequence diagrams
---

## 1) B2C purchase (Stripe) — the order is confirmed only by the signed webhook
Why it matters: the success page must NOT create the order (a user could open it without
paying). The signed webhook is the source of truth.
```mermaid
sequenceDiagram
    autonumber
    actor U as Customer
    participant D as Django checkout view
    participant S as Stripe
    participant W as Webhook handler
    participant SVC as Service create_paid_order
    participant DB as PostgreSQL
    participant M as Email SMTP
    U->>D: POST /checkout (session cart + address)
    D->>S: create Checkout Session (metadata SKUs, shipping, currency CHF)
    S-->>U: hosted payment page (no card data on our server)
    U->>S: pays on Stripe
    S-->>U: redirect to success_url (UI only, not trusted)
    S->>W: POST checkout.session.completed (+ Stripe-Signature)
    W->>W: verify signature (else HTTP 400)
    W->>SVC: create_paid_order(session data)
    Note over SVC,DB: atomic transaction, select_for_update locks stock, idempotent on session id
    SVC->>DB: insert Order + OrderItems + Payment, decrement stock
    DB-->>SVC: success
    SVC-->>W: order (created or existing)
    W->>M: send order confirmation email
    M-->>U: confirmation email
    W-->>S: HTTP 200
```

---

## 2) Registration + login (email account, nLPD consent recorded)
```mermaid
sequenceDiagram
    autonumber
    actor U as Visitor
    participant D as Django accounts
    participant DB as PostgreSQL
    U->>D: POST /account/register (email, password, consent)
    D->>D: validate form
    D->>DB: create_user() -> set_password hashes with PBKDF2
    D->>DB: insert ConsentLog (necessary, analytics, marketing, policy_version, ip, timestamp)
    DB-->>D: user created
    D-->>U: redirect + session cookie (logged in)
    Note over U,D: Later login
    U->>D: POST /account/login (email, password)
    D->>DB: check_password (compare hash)
    DB-->>D: match
    D-->>U: session established
```

---

## 3) Password reset (single-use, time-limited token)
```mermaid
sequenceDiagram
    autonumber
    actor U as Customer
    participant D as Django accounts
    participant DB as PostgreSQL
    participant M as Email
    U->>D: POST /account/password/reset (email)
    D->>DB: create PasswordResetToken (unique, expires_at, is_used false)
    D->>M: send reset link with token
    M-->>U: email (console backend in dev)
    U->>D: GET /reset/<token> then POST new password
    D->>DB: token valid? (exists, not used, not expired)
    alt valid
        D->>DB: set_password() and mark token is_used true
        D-->>U: success, redirect to login
    else invalid or expired
        D-->>U: error (no info leak)
    end
```

---

## 4) B2B request then staff validation (prospect to active)
```mermaid
sequenceDiagram
    autonumber
    actor P as Pro visitor
    participant D as Django b2b
    participant DB as PostgreSQL
    actor A as Staff back-office
    P->>D: POST /b2b/register (company, email, sector) with honeypot and rate-limit
    D->>DB: create B2BAccount status prospect and B2BRequest
    D-->>P: pending page
    A->>D: back-office approve_accounts action
    D->>DB: set B2BAccount status active, onboarded_at
    D->>P: notification email (account validated)
    Note over P,D: Now b2b_account_required grants access
    P->>D: GET /b2b/portal (catalog, configurator, quotes)
    D->>DB: read B2BProductInfo (MOQ, pro price)
    DB-->>P: pro portal
```

---

## 5) Add to cart (AJAX, session cart, live navbar badge)
```mermaid
sequenceDiagram
    autonumber
    actor U as Customer
    participant JS as Browser JS main.js
    participant D as Django cart
    participant SES as Session server-side
    U->>JS: click Add to cart
    JS->>D: POST /cart/add (sku_id, qty) with CSRF token
    D->>SES: Cart(request).add(sku, qty) session-based
    SES-->>D: updated cart (count, total)
    D-->>JS: JSON response count and total
    JS->>U: update navbar badge (no page reload)
```
