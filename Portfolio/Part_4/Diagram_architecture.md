# Architecture Diagram — layered, with business logic

## 1) Layered view (the important one — the data flow)
Each request crosses well-separated layers. Business logic lives in the **service layer**
(`services.py` for writes, `selectors.py` for reads), never in the views.
```mermaid
flowchart TB
    subgraph CLIENT [Client]
        B["Browser — HTML/CSS + vanilla JS (AJAX)"]
    end
    subgraph PRES [Presentation layer]
        T["Templates (Django) + static (Marbre Blanc)"]
    end
    subgraph HTTP [HTTP layer]
        V["Views (apps/*/views.py) — thin: parse request, call service/selector, render"]
        MW["Middleware (LocaleMiddleware, ForceCsrfCookie, sessions, auth)"]
        URL["URLconf (i18n_patterns + webhook/admin outside i18n)"]
    end
    subgraph BIZ [Business logic layer]
        SVC["services.py — writes: create_paid_order, validate B2B account…"]
        SEL["selectors.py — reads: catalog, KPIs, order history…"]
        DEC["decorators — RBAC: staff_member_required, b2b_account_required"]
    end
    subgraph DATA [Data layer]
        MOD["Models (ORM) — Customer, SKU, Order, Payment, ConsentLog…"]
        DB[("PostgreSQL 16")]
    end
    subgraph CROSS [Cross-cutting: apps.common]
        CON["consent (nLPD)"]
        CST["constants (cantons, channels, roles)"]
        CTX["context processors (cart summary, feature flags)"]
    end
    subgraph EXT [External services]
        STR["Stripe (Checkout + Webhook)"]
        SMTP["Email (console dev / SMTP prod)"]
    end

    B --> T --> URL --> MW --> V
    V --> DEC
    V --> SVC
    V --> SEL
    SVC --> MOD
    SEL --> MOD
    MOD --> DB
    SVC --> STR
    SVC --> SMTP
    CON -.-> V
    CTX -.-> T
```

## 2) Domain map (12 apps grouped by business area)
```mermaid
flowchart LR
    subgraph Storefront [B2C storefront]
        main["main (home/static)"]
        shop["shop (catalog)"]
        cart["cart (session)"]
        checkout["checkout (Stripe)"]
        ca["customer_area"]
    end
    subgraph Pro [B2B]
        b2b["b2b (portal, configurator)"]
    end
    subgraph Admin [Admin & BI]
        back["backoffice (AdminUser, dashboards)"]
        cockpit["cockpit (targets)"]
        fore["forecasting (alerts)"]
        ana["analytics (events)"]
    end
    subgraph Core [Core]
        acc["accounts (Customer, ConsentLog, B2BAccount)"]
        common["common (middleware, consent, constants)"]
    end
    shop --> cart --> checkout --> ca
    b2b --> acc
    checkout --> acc
    back --> shop
    cockpit --> ana
    fore --> shop
    acc --- common
```

## 3) Runtime: live (dev) vs target (prod)
```mermaid
flowchart LR
    subgraph DEV [Live today - dev]
        Bd[Browser] -->|:8000| Dj[Django dev server]
        Dj --> Pg[(PostgreSQL 16)]
        Dj --> St[Stripe]
    end
    subgraph PROD [Target - prod]
        Bp[Browser] -->|HTTPS| Ng[Nginx SSL + static]
        Ng --> Gu[Gunicorn WSGI]
        Gu --> Dp[Django]
        Dp --> Pb[PgBouncer] --> Pp[(PostgreSQL 16)]
        Dp --> Sp[Stripe]
        Dp --> Sm[SMTP]
    end
```
Note: Nginx / Gunicorn / PgBouncer are the production targets, not enabled in the dev compose (only `django` + `postgres` run today).

## 4) More to know about data flow
A request enters via the URLconf (with a language prefix for non-French), passes through
middleware (locale, sessions, CSRF), reaches a thin view. The view calls a **service** (write)
or a **selector** (read); those hold the business logic and talk to the models (ORM), which map
to PostgreSQL. Cross-cutting concerns (consent, constants, context) live in `apps.common`.
External calls (Stripe, email) are made from the service layer.

