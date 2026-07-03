<!--
  README.md — Lamos Chocolate
  ---------------------------------------------------------------------------
  This file is the entry point of the repository. It is written in English on
  purpose: everything that lives inside the repo (code, comments, commits,
  docs) is in English, so tooling, reviewers and future contributors get a
  single, consistent language. The product UI itself is multilingual
  (fr / en / de-CH / it-CH) — see the "Internationalization" section.
-->

# 🍫 Lamos Chocolate — Swiss Luxury Chocolate E-commerce

A production-oriented **Django 5.2** e-commerce platform for a Swiss luxury
chocolate maker. It ships a **B2C storefront**, a full **B2B professional
portal**, and an internal **executive cockpit**, with **Swiss data-protection
compliance (nLPD / RGPD)** built in from the start rather than bolted on.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Stripe](https://img.shields.io/badge/Payments-Stripe-635BFF?logo=stripe&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-pytest%20%7C%20coverage%20%E2%89%A570%25-0A9EDC)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)

---

## Table of contents

1. [What this project is](#1-what-this-project-is)
2. [Key features](#2-key-features)
3. [Tech stack](#3-tech-stack)
4. [Architecture](#4-architecture)
5. [Project structure](#5-project-structure)
6. [Getting started (Docker)](#6-getting-started-docker)
7. [Running the tests](#7-running-the-tests)
8. [Code quality](#8-code-quality)
9. [CI/CD pipeline](#9-cicd-pipeline)
10. [Internationalization](#10-internationalization)
11. [Swiss compliance (nLPD / RGPD)](#11-swiss-compliance-nlpd--rgpd)
12. [Security](#12-security)
13. [Deployment](#13-deployment)
14. [Team & ownership](#14-team--ownership)
15. [Known limitations](#15-known-limitations)

---

## 1. What this project is

Lamos Chocolate sells premium chocolate through three product families —
**Tablette Kunafa**, **Truffes**, and **Carrés Lamo's** — to two very different
audiences:

- **Individuals (B2C):** browse the catalogue, add to cart, pay online via
  Stripe, and manage their account.
- **Professionals (B2B):** request a professional account, get a moderated
  `prospect → active` lifecycle, access pro-only catalogue data (minimum order
  quantities, professional pricing), configure custom products, and simulate
  quotes.

On top of the shop, an internal **cockpit** lets the business set objectives
per product and per Swiss canton, and a **forecasting** layer produces sales
forecasts and alerts.

> This is a school / portfolio project targeting production-grade quality
> (not a throwaway MVP). The primary market is **Switzerland**, which drives
> the localization and the privacy choices described below.

---

## 2. Key features

### B2C storefront
- Product catalogue with categories, product detail pages, SKUs, stock and
  shipping zones.
- Session- and user-bound **cart** (`Cart` / `CartItem`).
- **Stripe checkout** with server-side `Order` / `OrderItem` / `Payment`
  records and a signed **webhook** endpoint for asynchronous payment events.
- Customer accounts with a **custom user model** (`accounts.Customer`),
  email-based login, Google social login (via allauth), password reset, and a
  personal dashboard with saved addresses and order history.

### B2B professional portal
- Public funnel and gated pro portal, protected by dedicated decorators
  (`b2b_login_required`, `b2b_account_required`).
- Account lifecycle: `prospect → pending → active`, with a **back-office
  validation** screen for pending accounts.
- B2B-specific catalogue data isolated in `B2BProductInfo` (MOQ, pro pricing,
  availability) so it never pollutes the core product models.
- Product **customization requests** and **quote simulation**.
- Orders are tagged with a `channel` field (`b2c` / `b2b`) so revenue can be
  split cleanly for reporting.

### Executive cockpit & analytics
- `cockpit`: business objectives per product (`ProductTarget`) and per canton
  (`CantonTarget`).
- `analytics`: lightweight event tracking (`Event`) with a consent gate.
- `forecasting`: sales `Forecast` and `Alert` generation.

### Compliance & trust
- First-party, granular **cookie consent** with an immutable, timestamped
  audit log (`ConsentLog`) — see [section 11](#11-swiss-compliance-nlpd--rgpd).
- Full **4-language** interface for the Swiss market.

---

## 3. Tech stack

| Layer            | Technology                                                        |
|------------------|-------------------------------------------------------------------|
| Language         | Python 3.12                                                       |
| Framework        | Django 5.2                                                        |
| Database         | PostgreSQL 16                                                     |
| Auth             | django-allauth (email + Google; Facebook configured but disabled)|
| Payments         | Stripe (`stripe` 11.1.0) + signed webhooks                       |
| Frontend         | Django templates + custom **"Marbre Blanc"** CSS design system   |
| Containerization | Docker + Docker Compose                                          |
| Tests            | pytest, pytest-django, pytest-cov (coverage gate ≥ 70%)          |
| Code quality     | black, isort, flake8                                             |
| CI/CD            | GitHub Actions (lint / tests / security / deploy)               |
| Config           | `python-decouple` (12-factor style, values read from `.env`)    |

**Marbre Blanc design system** — a bespoke light theme replacing Bootstrap:
ivory `#FBF7F0`, gold `#C9A063`, cocoa `#1F1813`; typefaces Cormorant Garamond,
Cinzel and Lato.

---

## 4. Architecture

The backend follows Django's **MVT** pattern, extended with an explicit
**service / selector** separation to keep views thin:

- **`services.py`** — write operations and business logic (create an order,
  validate a B2B account, record consent…).
- **`selectors.py`** — read/query logic (fetch catalogue data, dashboard
  aggregates…).
- **`views.py`** — orchestration only: parse the request, call a
  service/selector, render a template.

Cross-cutting concerns live in **`apps.common`** (custom middleware, context
processors, decorators, validators, consent helpers), so no single feature app
owns them.

### The 12 local apps

| App             | Responsibility                                                       |
|-----------------|----------------------------------------------------------------------|
| `common`        | Shared middleware, context processors, decorators, consent, validators |
| `main`          | Homepage, static pages, custom 403/404/500 handlers                 |
| `accounts`      | Custom `Customer` user, `B2BAccount`, `ConsentLog`, allauth adapters |
| `shop`          | `Category`, `Product`, `ProductImage`, `SKU`, `Stock`, `ShippingZone`|
| `cart`          | `Cart`, `CartItem`                                                   |
| `checkout`      | `Order`, `OrderItem`, `Payment`, Stripe integration & webhooks       |
| `customer_area` | Customer dashboard, `CustomerAddress`                               |
| `b2b`           | `B2BRequest`, `B2BProductInfo`, `CustomizationRequest`, `QuoteSimulation`, access decorators |
| `backoffice`    | Staff dashboards and B2B account validation                         |
| `cockpit`       | `CockpitObjective`, `ProductTarget`, `CantonTarget` (standalone)    |
| `forecasting`   | `Forecast`, `Alert`                                                 |
| `analytics`     | `Event` tracking (consent-gated)                                    |

---

## 5. Project structure

```text
Lamos-chocolate/
├── .github/workflows/         # CI/CD: ci, lint, tests, security, deploy-staging, deploy-production
├── backend/
│   ├── apps/                  # The 12 local Django apps (see table above)
│   ├── config/
│   │   ├── settings/          # base.py, dev.py, prod.py, test.py (split settings)
│   │   ├── urls.py            # Root URLconf (i18n + non-i18n routes)
│   │   ├── wsgi.py / asgi.py
│   ├── locale/                # fr, en, de_CH, it_CH translation catalogs
│   ├── static/                # Marbre Blanc CSS, JS, images, video
│   ├── templates/             # Base + per-app templates, emails, error pages
│   ├── requirements/          # base.txt, dev.txt, prod.txt, test.txt
│   ├── manage.py
│   ├── pytest.ini             # pytest config + coverage gate (--cov-fail-under=70)
│   ├── setup.cfg              # flake8 config
│   └── pyproject.toml         # black + isort config
├── infrastructure/
│   ├── docker/                # Dockerfile, entrypoint.sh, nginx, postgres init.sql
│   ├── nginx/                 # nginx site configs (default / production)
│   └── scripts/               # backup / restore / deploy / wait-for-db helpers
├── scripts/                   # setup, lint, format, run_tests, seed_db, reset_db
├── docs/                      # Architecture, decisions, deployment, QA, setup notes
├── docker-compose.yml
└── .env.example               # Copy to .env and fill in
```

---

## 6. Getting started (Docker)

The whole stack runs in Docker, so you only need **Docker** and **Docker
Compose** installed. No local Python or PostgreSQL required.

### Step 1 — Clone and configure

```bash
git clone https://github.com/SaraEstelle/Lamos-chocolate.git
cd Lamos-chocolate

# Create your local .env from the template
cp .env.example .env
```

> **Important — `POSTGRES_HOST`.** Inside Docker, Django reaches the database
> through the Compose service name, so keep `POSTGRES_HOST=postgres`. Only
> switch it to `localhost` if you ever run Django directly on your host
> machine instead of in the container.

### Step 2 — Build and start

```bash
# Build the images and start PostgreSQL + Django in the background
docker compose up -d --build
```

On startup the Django container automatically:
1. waits for PostgreSQL to be ready,
2. applies migrations (`manage.py migrate`),
3. collects static files (`manage.py collectstatic`),
4. starts the dev server on port **8000**.

### Step 3 — Seed demo data (optional but recommended)

```bash
# Load the shop catalogue (categories, products, SKUs, stock, shipping zones)
docker compose exec django python manage.py loaddata \
  apps/shop/fixtures/categories.json \
  apps/shop/fixtures/products.json \
  apps/shop/fixtures/product_images.json \
  apps/shop/fixtures/skus.json \
  apps/shop/fixtures/stock.json \
  apps/shop/fixtures/shipping_zones.json

# Load B2B pro catalogue data (MOQ, pro pricing, availability)
docker compose exec django python manage.py loaddata apps/b2b/fixtures/b2b_product_info.json

# Seed cockpit objectives (custom management command)
docker compose exec django python manage.py seed_cockpit
```

### Step 4 — Create an admin user

```bash
docker compose exec django python manage.py createsuperuser
```

### Step 5 — Open the app

| URL                                | What it is                          |
|------------------------------------|-------------------------------------|
| http://localhost:8000/             | B2C storefront (homepage)           |
| http://localhost:8000/shop/        | Product catalogue                   |
| http://localhost:8000/b2b/         | B2B professional portal             |
| http://localhost:8000/admin/       | Django admin (superuser)            |
| http://localhost:8000/backoffice/  | Staff back-office                   |
| http://localhost:8000/cockpit/     | Executive cockpit (staff)           |

### Full reset

To wipe the database and start clean (this is the **only** approved reset —
never regenerate migrations to "start fresh", as that overwrites shared team
history):

```bash
docker compose down -v      # -v also removes the postgres volume
docker compose up -d --build
```

---

## 7. Running the tests

The suite currently holds **200+ tests** across all apps, run against a real
PostgreSQL engine, with a **coverage gate of 70%** enforced in `pytest.ini`.

```bash
# Run the full suite (from inside the running container)
docker compose exec django pytest

# Run one app only
docker compose exec django pytest apps/checkout

# Run by marker (e.g. payment-related tests)
docker compose exec django pytest -m payment
```

A browsable HTML coverage report is generated in `backend/htmlcov/`.

---

## 8. Code quality

Formatting and linting are enforced both locally and in CI. None of these
tools ever rewrite your files in CI — they only report.

```bash
docker compose exec django black --check .        # formatting (line length 88)
docker compose exec django isort --check-only .   # import ordering (black profile)
docker compose exec django flake8 .               # style / unused imports
```

Convenience wrappers live in `scripts/format.sh` and `scripts/lint.sh`.

---

## 9. CI/CD pipeline

CI/CD runs on **GitHub Actions**. A single orchestrator (`ci.yml`) fans out
into three reusable workflows so the whole status is visible on every branch
and every pull request:

| Workflow                 | Trigger                          | What it does                                                        |
|--------------------------|----------------------------------|---------------------------------------------------------------------|
| `ci.yml`                 | every push + every PR            | Orchestrator: calls lint / tests / security in parallel             |
| `lint.yml`               | called by `ci.yml`               | black, isort, flake8 (report-only)                                  |
| `tests.yml`              | called by `ci.yml`               | pytest against PostgreSQL 16, uploads HTML coverage artifact        |
| `security.yml`           | called by `ci.yml` + weekly cron | `pip-audit` (CVEs), `bandit` (code), `manage.py check --deploy`     |
| `deploy-staging.yml`     | push to `develop`                | Build & push image to GHCR (`:staging`)                             |
| `deploy-production.yml`  | git tag `v*` + manual approval   | Build & push versioned image to GHCR (`:latest`, `:vX.Y.Z`)         |

> **Honest note:** the image build/push steps are real and work out of the box
> (they use the built-in `GITHUB_TOKEN`). The final "deploy to server" step is
> a documented **placeholder** until a real staging/production host and its
> SSH secrets exist. This is intentional — the pipeline demonstrates the full
> shape without pretending to deploy to a machine that isn't there yet.

---

## 10. Internationalization

The interface is available in **four languages** targeting the Swiss market:

| Language | URL prefix  | Locale folder |
|----------|-------------|---------------|
| French   | *(default)* | `fr`          |
| English  | `/en/`      | `en`          |
| German (CH) | `/de-ch/` | `de_CH`      |
| Italian (CH) | `/it-ch/`| `it_CH`      |

Routing uses Django's `i18n_patterns`. Language codes follow Django convention
(lowercase + hyphen in URLs; underscore + region for the folders). Payment
webhooks, admin and consent endpoints are deliberately kept **outside** the
language prefix.

---

## 11. Swiss compliance (nLPD / RGPD)

Privacy is a first-class feature, not an afterthought:

- **Granular, opt-in cookie consent.** A first-party cookie (`lamos_consent`)
  stores three categories — `necessary` (always on), `analytics`, `marketing`.
  Nothing non-essential loads until the visitor decides.
- **Immutable proof of consent.** Every decision is written to `ConsentLog`
  (UUID primary key, timestamp, IP, user agent, policy version). Rows are
  **never updated or deleted** — a new decision creates a new row, so the
  history stays auditable. It works for both anonymous visitors (correlated by
  a random `consent_id`) and authenticated customers.
- **Policy versioning.** `policy_version` is stored with each decision, so a
  future change to the cookie policy can trigger a fresh consent request.
- **No hard deletes of business data.** Accounting-relevant records are kept
  (Swiss CO art. 958f — 10-year retention); accounts are marked dormant rather
  than physically deleted.
- **PCI-DSS is fully delegated to Stripe.** No card data ever touches the
  application or the database.

---

## 12. Security

- **Custom user model** with email-based authentication and Django's password
  validators.
- **UUID primary keys** on sensitive records (`Payment`, `B2BAccount`,
  `ConsentLog`) to avoid enumeration / information leaks.
- **Access-control decorators** for the B2B area (`b2b_login_required`,
  `b2b_account_required`) designed **not** to reveal whether an account exists
  to unauthorized users.
- **CSRF everywhere except the Stripe webhook**, which must accept Stripe's raw
  POST and is instead protected by **signature verification**.
- **Production hardening** (in `config/settings/prod.py`): `SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS.
- **Automated security scanning** in CI: dependency CVEs (`pip-audit`), static
  analysis (`bandit`), and Django's own `check --deploy` audit — plus a weekly
  scheduled run to catch newly disclosed CVEs.
- **Secrets are never committed.** All credentials come from `.env`, which is
  git-ignored; only `.env.example` (with placeholders) is tracked.

---

## 13. Deployment

Split settings modules select the environment via `DJANGO_SETTINGS_MODULE`:

- `config.settings.dev` — local development (DEBUG on, console email, debug
  toolbar).
- `config.settings.prod` — production hardening (DEBUG off, SSL redirect,
  secure cookies, HSTS). Serves with **gunicorn** + **whitenoise**.
- `config.settings.test` — fast test settings (used by pytest and CI).

Production images are published to the GitHub Container Registry by
`deploy-production.yml` on a version tag (e.g. `v1.0.0`). Wiring those images
to a real host is the next step (see [Known limitations](#15-known-limitations)).

---

## 14. Team & ownership

| Area                                                   | Owner       |
|--------------------------------------------------------|-------------|
| Accounts, customer area, B2B portal, frontend          | **Sara**    |
| Cart & checkout (incl. Stripe)                         | **Valentin**|

**Working conventions**
- Code, comments and commit messages: **English**.
- Commits follow the **Conventional Commits** specification.
- Branch strategy: `develop` (stable base) → feature branches → PR into
  `develop`; `develop` → `main` for releases.
- Database resets use `docker compose down -v` only. Migrations are **never**
  regenerated to "start fresh".

---

## 15. Known limitations

These are stated openly so the project state is never misrepresented:

- **Server deployment is a placeholder.** Image build & push work; the actual
  SSH rollout to a staging/production host is stubbed until a host and its
  secrets exist.
- **Facebook social login is configured but disabled**; only email + Google
  are active.
- **`pip-audit` / `bandit` are non-blocking** in CI for now (`|| true`) so an
  unpatched pinned dependency doesn't block the deadline. The reports are still
  printed; the recommendation is to make them blocking once the project is
  stable.
- **Nginx is prepared but not enabled** in `docker-compose.yml` (planned for a
  later phase); the dev server currently serves the app directly.
- **Default `TIME_ZONE` is `Europe/Paris`** (from `.env.example`). For a
  Swiss-first product, consider `Europe/Zurich`. *(No code changed here — flagged
  for a decision.)*

---

<p align="center"><em>Lamos Chocolate — crafted for Switzerland. 🇨🇭</em></p>
