# TASK 1 — Execute Development Tasks

## 1. Role of each branch (simplified Git Flow)
| Branch | Role |
|---|---|
| `main` | Production / release. Never pushed to directly; only receives merges from `develop`. Releases are tagged here (`v1.0.0`, #50). |
| `develop` | Integration branch. Every feature is merged here after review; it is the shared base we branch from. |
| `feature/<module>` | One branch per feature (e.g. `feature/checkout`). Isolated work, then a Pull Request into `develop`. |
| `fix/<bug>` | A targeted bug fix (e.g. `fix/i18n-switcher`) → PR into `develop`. |
| `docs/<topic>` | Documentation changes (e.g. fixing a diagram). |
| `backup/frontend-demo` | Archive of the reference static frontend, kept but not merged. |

Workflow:
```bash
git checkout develop && git pull origin develop
git checkout -b feature/checkout            # 1 branch = 1 feature
git add .
git commit -m "feat(checkout): add stripe checkout session and webhook fulfillment"
git push origin feature/checkout            # then open a Pull Request into develop
```

## 2. Coding standards
- Conventional Commits: `type(scope): description` (`feat`, `fix`, `docs`, `chore`, `ci`,
  `test`, `refactor`).
- Layered architecture: views stay thin; writes in `services.py`, reads in `selectors.py`.
- Automatic style: `black`, `isort`, `flake8` (blocking in CI from Sprint 4, #45).
- Tests: each app has a `tests/` folder; target ≥ 70 % coverage (enforced by `pytest.ini`).
- Secrets: never in code → environment variables (`.env` git-ignored). Only `.env.example` is
  committed. (Swiss/GDPR: no personal data or keys in the repo.)

## 3. Role of each folder / file
```
backend/apps/            # 12 apps, one per business domain
  common/                # cross-cutting: middleware, constants, decorators, CONSENT (nLPD)
  main/                  # public site: home, static pages, error pages
  accounts/              # AUTH: Customer (UUID+email), ConsentLog (nLPD), B2BAccount
  shop/                  # CATALOG: Category, Product, ProductImage, SKU, Stock, ShippingZone
  cart/                  # CART: cart.py (SESSION cart) + Cart/CartItem models
  checkout/              # PAYMENT: Order, OrderItem, Payment, stripe.py, webhooks.py
  customer_area/         # CUSTOMER AREA: CustomerAddress, dashboard, history
  b2b/                   # PRO PORTAL: B2BRequest, B2BProductInfo, access decorators
  backoffice/            # ADMIN: AdminUser (role-based staff), dashboards, B2B validation
  cockpit/               # DECISION: objectives (Objective, ProductTarget, CantonTarget)
  forecasting/           # FORECASTS: Forecast, Alert
  analytics/             # EVENTS: Event (consent-gated)
backend/config/          # settings (base/dev/prod/test), urls.py, wsgi/asgi
backend/templates/       # HTML templates (one folder per app + emails/ + errors/)
backend/static/          # css/ ("Marbre Blanc" design) + js/ (vanilla)
backend/locale/          # translations fr / en / de_CH / it_CH (.po/.mo)
backend/requirements/    # split dependencies: base / dev / prod / test
.github/workflows/       # 6 CI/CD pipelines
docker-compose.yml       # orchestrates postgres + django
```
Inside each app, fixed file roles: `models.py` (tables), `views.py` (HTTP, thin), `services.py`
(writes), `selectors.py` (reads), `urls.py` (routes + namespace), `forms.py` (forms/validation),
`admin.py` (Django admin), `migrations/` (schema history — never regenerated), `tests/` (tests).

## 4. PR review process (SCM)
1. Open a Pull Request from `feature/*` into `develop`, with a Conventional title.
2. The other developer reviews: consistency, tests present, no secrets, services/selectors
   pattern respected.
3. CI must be green (lint + tests + security) — from Sprint 4.
4. Merge only after review + green CI. The Notion card moves to Done.
Cross-review is real: Valentin merged PRs on Sara's area (e.g. #35, #38) and vice versa.

## 5. Execution per sprint (what each PR delivered)

### Sprint 0 — Setup (2 PRs)
- #2 `refactor(repo)` (Sara) — restructures the tree into apps by domain.
- #3 `fix(structure)` (Sara) — homogeneous Python/Django naming conventions.

### Sprint 1 — Foundations (12 PRs)
- #4 `feat` (Sara) — Django core configuration (settings base/dev/prod/test).
- #5 `feat(checkout)` (Valentin) — `shipping_zone` FK + quantity check on `order_items`.
- #6, #8 `test(core)` (Valentin) — first tests (models + forecasting): QA starts in Sprint 1.
- #9 `feat` (Valentin) — hybrid backend: `Payment` + `ProductImage`.
- #10 `docs(db)` (Valentin) — ERD updated with `Payment` + `ProductImage`.
- #12 `merge` (Valentin) — integrates the hybrid backend into `develop` (after conflicts; #11
  was closed and redone).
- #13 `merge` (Valentin) — integrates `feature/accounts` (Option B auth).
- #14 `fix(accounts)` (Sara) — finalises auth (`AUTH_USER_MODEL`, `PermissionsMixin`, UUID,
  security).
- #15 `feat(shop)` (Valentin) — public catalog (catalog, detail, category, search).
- #18, #19 `feat(customer-area)` (Sara) — customer area v1 then v2 (addresses, filtered
  history, status timeline).

### Sprint 2 — Commerce & admin (12 PRs)
- #20 `feat(cart)` (Valentin) — session cart.
- #21 `feat(data)` (Sara) — data foundations: canton, customer_type, margin, channel,
  `B2BAccount`.
- #22 `feat(catalog)` (Sara) — catalog data (products, SKUs, stock, images, zones).
- #23 `feat(analytics)` (Sara) — analytics app (events, KPI selectors, admin, tests).
- #24 `chore(dev)` (Valentin) — django-debug-toolbar.
- #25 `feat(backoffice)` (Valentin) — back-office (dashboard, orders/stock/B2B).
- #27 `feat(forecasting)` (Valentin) — forecasting + stockout alerts.
- #28 `feat(b2b)` (Sara) — full B2B module (funnel, portal, configurator).
- #29 `fix(ui)` (Sara) — logout, sticky footer, register errors.
- #30 `feat(main)` (Sara) — homepage + static pages (home no longer 404s).
- #31 `feat(brand)` (Sara) — marble theme (fonts, gold buttons, navbar/footer).
- #32 `feat(emails)` (Sara) — transactional emails (order, shipped, B2B).

### Sprint 3 — Design & payment (6 PRs)
- #33 `feat(frontend)` (Sara) — "Marbre Blanc" design system (drops Bootstrap).
- #34 `feat(auth)` (Sara) — allauth Google/Facebook.
- #35 `feat(accounts)` (Valentin) — canton on addresses + client denormalisation.
- #37 `feat(cart)` (Valentin) — live cart (navbar badge + AJAX add/update/remove).
- #38 `fix(customer_area)` (Valentin) — resolves the client model via FK on address save.
- #39 `feat(checkout)` (Valentin) — Stripe checkout + webhook (payment core; signed webhook,
  idempotent, atomic).

### Sprint 4 — Compliance & release (10 PRs)
- #40 (Sara) — accounts + customer area improvements (registration/layout).
- #41 (Sara) — B2B/B2C portal overhaul (Marbre UI) + checkout improvements.
- #42 `feat(backoffice)` (Valentin) — B2B pro-account validation + channel-revenue selector.
- #43 `feat(compliance)` (Sara) — GDPR/nLPD consent framework (`ConsentLog`, opt-in banner).
- #44 `fix(ui)` (Sara) — auth form contrast + B2B register theming.
- #45 `ci` (Sara) — GitHub Actions pipelines + lint-clean codebase.
- #47 `feat(i18n)` (Sara) — 4 languages (FR/EN/DE-CH/IT-CH) + native switcher (#46 was closed
  and redone).
- #48 `fix(i18n, shop)` (Sara) — switcher logic + product photos.
- #49 `feat` (Valentin) — executive cockpit + back-office marble shell.
- #50 `chore(release)` (Sara) — v1.0.0 release.

## 6. More informations
Tests were introduced from Sprint 1 (#6, #8), then grown per app (~203 tests total: checkout
48, shop 38, accounts 32, cart 20, b2b 17, backoffice 11, customer_area 10, main 9,
forecasting 7, common 6, analytics 5). From Sprint 4 (#45), lint + tests + security run in CI
on every PR; a red PR cannot be merged.
Evidence: the GitHub Pull Requests tab (42 merged PRs, Conventional Commits).