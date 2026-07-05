# TASK 6 — Technical Manual Review

Before starting, We launch the app and open our evidence:
```bash
docker compose up -d --build
docker compose exec django python manage.py createsuperuser
```
Open: the site (/), the GitHub README + Pull Requests tab, the architecture diagram, the ERD, and the Notion board.

---

## 1. Completion of the project (functional MVP, minor or no bugs)
The MVP covers three universes: a **B2C storefront** (catalog, cart, Stripe payment, customer area), a **B2B professional portal** (request → validation → pro catalog, configurator, quotes),
and an **admin/BI layer** (back-office, forecasting, executive cockpit). The full purchase funnel
works end to end: catalog → cart → Stripe → signed webhook → paid order → confirmation email.
It is a **release** (tag v1.0.0, PR #50), with **42 merged PRs** and **~203 tests** at a
**≥ 70 % coverage** gate.
Known minor limitations we state openly: no production server is deployed (the pipeline only
builds and pushes a Docker image); the security scanners (pip-audit/bandit) run non-blocking in
CI; the DB `Cart`/`CartItem` models are partly unused because the real checkout cart is
session-based; `TIME_ZONE` defaults to Europe/Paris (should be Europe/Zurich). No blocking bug remains in the core flows.

## 2. Demonstration of the MVP
We run: homepage → switch language (FR/EN/DE-CH/IT-CH) → catalog → add to cart (the navbar badge updates via AJAX, no reload) → checkout with the Stripe test card `4242 4242 4242 4242` →
confirmation page → the confirmation email prints in the Docker logs (console backend in dev).
We also show the **cookie consent banner** (Swiss argument), then `/admin/`, `/backoffice/`
(KPIs, product CRUD, stock, B2B validation) and the cockpit.

## 3. Quality of code, commits and documentation
Code: 12 apps organised **by business domain**; a strict pattern of **thin views** calling
`services.py` (writes) and `selectors.py` (reads); docstrings on modules and key functions;
style enforced automatically by **black + isort + flake8** in CI.
Commits: **Conventional Commits** (`feat`, `fix`, `docs`, `chore`, `ci`, `test`), so the history
reads like a changelog.
Documentation: a 450-line **README** (setup, architecture, structure, i18n, compliance,
security, known limitations), Architecture Decision Records (`docs/decisions/ADR-001..009`),
and corrected diagrams (ERD, class, sequence, architecture).

## 4. Explaining my technical decisions (with reasoning)
- **Database design:** a hybrid model (ADR-006) — the spec backbone (SKU, ShippingZone,
  bilingual fields) plus production additions: a **separate `Payment`** model, a separate
  `ProductImage`, and **UUID** keys on sensitive tables (Customer, Payment, ConsentLog,
  B2BAccount) so IDs cannot be enumerated. Currency defaults to **CHF** for Switzerland.
- **Architecture:** a layered modular monolith (presentation → HTTP → business
  services/selectors → data/ORM → PostgreSQL), with cross-cutting concerns in `apps.common`.
- **Technology choices:** Django (batteries-included: ORM, admin, auth, i18n, security defaults),
  PostgreSQL 16 (ACID, constraints, UUID/JSON, needed for accounting retention), Docker (parity
  dev/prod), Stripe (delegates PCI-DSS), django-allauth (email + Google), pytest (fixtures +
  coverage). Each is recorded as an ADR.
- **Auth decision (ADR-007):** native Django auth (`AbstractBaseUser + PermissionsMixin`,
  email login, UUID) rather than a hand-rolled `password_hash` — I diverge from the design doc
  here and document why (never roll your own crypto).

## 5. Explaining my code and features in detail
- `apps/checkout/webhooks.py` — I **verify the Stripe signature** (else HTTP 400) before
  trusting anything; the webhook is the source of truth, not the browser redirect.
- `apps/checkout/services.py` — `create_paid_order()` runs in a **`transaction.atomic`** block,
  uses **`select_for_update()`** to lock stock (no overselling) and is **idempotent** on the
  Stripe session id (a replayed webhook creates no duplicate).
- `apps/accounts/models.py` — `Customer` (UUID, email login), `set_password()` hashes with
  PBKDF2; `ConsentLog` is an immutable consent audit trail.
- `apps/b2b/decorators.py` — RBAC: `b2b_account_required` (active accounts only) vs
  `b2b_login_required` (any status), redirecting without leaking whether a resource exists.

## 6. How does the application work?
A request enters through the URLconf (`i18n_patterns` adds a language prefix for non-French
pages; the webhook and admin are outside i18n). Middleware runs (locale, sessions, CSRF, a
custom `ForceCsrfCookieMiddleware`). A **thin view** parses the request and calls a **service**
(write) or a **selector** (read); those hold the business logic and use the **ORM** (models),
which maps to **PostgreSQL**. External calls (Stripe, email) are made from the service layer.
Templates render the HTML; vanilla JS handles AJAX (cart, consent).

## 7. How did I test the application?
With **pytest**. I have **41 test files / ~203 tests**: unit tests (models, services) and
integration tests (auth views, cart API, the Stripe webhook). Shared **fixtures** live in
`conftest.py` and run against an isolated test database. `pytest.ini` enforces a **≥ 70 %
coverage** gate (`--cov-fail-under=70`). In **CI**, `tests.yml` spins up a real PostgreSQL,
runs the suite, and publishes an HTML coverage report as an artifact. For the webhook I also
test manually with the **Stripe CLI** (`stripe listen`). My strongest test is
`test_webhooks.py`: an invalid signature returns 400 with no order created, a completed session
creates a paid order and decrements stock (50 → 48), and a re-delivered event stays idempotent
(one order). A 44-point manual **E2E checklist** covers the full journeys and security cases.
During the review I run `docker compose exec django pytest` live to show the green result.

## 8. How did I collaborate with my team?
We are two: I (Sara, Owner) handled accounts, customer area, B2B, frontend, i18n, compliance and
the SCM setup; Valentin (Collaborator) handled the cart, checkout/Stripe, back-office,
forecasting and cockpit. We ran **morning and evening Discord stand-ups**, tracked everything on
**Notion** (Kanban board + decision log + deployment tracking), and used **GitHub** as the code
source of truth with **cross-reviewed Pull Requests** (42 merged). When a PR was too
conflict-prone or too large we closed and redid it (#11 → #12, #46 → #47, #36 → #49).

## 9. Git & GitHub best practices
Simplified **Git Flow**: `main` (release, tagged v1.0.0), `develop` (integration),
`feature/*` (one per feature), `fix/*`. No direct pushes to `main`/`develop` — everything goes
through a **reviewed Pull Request**. **Conventional Commits** throughout. From Sprint 4, **CI**
(lint + tests + security) runs on every PR and must be green before merge.

## 10. Explaining the technical notions I applied
- **DB relations:** ForeignKey (one-to-many, e.g. Category→Product), OneToOne (Payment↔Order,
  Stock↔SKU), and `on_delete` semantics — **RESTRICT** on Order→Customer (accounting retention),
  **CASCADE** on OrderItem→Order, **SET_NULL** on ConsentLog→Customer (keep the proof).
- **Frontend design:** a custom "Marbre Blanc" design system (Bootstrap removed) built on CSS
  **design tokens**; effects in pure CSS/JS (scrolling marquee, hover zoom, reveal-on-scroll via
  IntersectionObserver with a fallback) and `prefers-reduced-motion` for accessibility.
- **Authentication:** custom user on `AbstractBaseUser + PermissionsMixin`, **email login**,
  **UUID** key; Google via django-allauth.
- **Hashing:** passwords hashed with **PBKDF2** via `set_password()` (never stored in plaintext);
  MD5 is used only in tests for speed.
- **Security:** Django CSRF tokens, template **auto-escaping** (XSS), the ORM's parameterised
  queries (SQL injection), clickjacking protection; in production HTTPS redirect, secure cookies
  and HSTS; secrets kept in `.env` (git-ignored).
- **RBAC:** `@staff_member_required` for the back-office; two B2B decorators (active vs any
  status) with no information leak.
- **Swiss nLPD / GDPR:** a granular, **opt-in** cookie banner (nothing pre-ticked); analytics
  only loads **after** consent; an **immutable `ConsentLog`** (who/what/when/policy version) as
  proof; 10-year accounting retention enforced by `on_delete=RESTRICT`; PCI delegated to Stripe.

## 11. Explaining frontend, backend, database and other concepts
- **Frontend:** server-rendered Django templates + vanilla JS + a custom CSS design system;
  4-language i18n via `.po`/`.mo` and a custom language-switch template tag.
- **Backend:** Django (MVT) with a services/selectors business layer; a few JSON/AJAX endpoints
  (cart, consent) — not a full REST API.
- **Database:** PostgreSQL 16, chosen for ACID transactions, DB constraints (`CHECK quantity >
  0`), indexes and UUID/JSON support; accessed via the ORM (and `psql`/`dbshell` for inspection).
- **Other:** Docker Compose (postgres + django) for reproducible environments; Stripe as the
  external payment API integrated via Checkout Sessions + a signed webhook; email via SMTP
  (console backend in dev).