# TASK 4 — Final Integration and QA Testing

## 1. Integration points
| Integration | How | Where |
|---|---|---|
| Frontend ↔ Backend | Django renders HTML; JS (AJAX/fetch) calls endpoints (cart, consent) | static/js/main.js, apps/cart/urls.py |
| Backend ↔ Database | the Django ORM maps Python objects to PostgreSQL SQL | apps/*/models.py, selectors.py |
| Backend ↔ Stripe | checkout session + signed webhook | apps/checkout/stripe.py, webhooks.py |
| Everything ↔ Docker | postgres + django orchestrated with healthchecks | docker-compose.yml |
The front↔back↔db integration is tested under real conditions on every `docker compose up`, on
the same PostgreSQL as in CI.

## 2. Test strategy (pyramid)
- Unit tests: one isolated function/model (e.g. subtotal = quantity × price; the `quantity > 0`
  constraint).
- Integration tests: several components (e.g. the Stripe webhook creates an order and
  decrements stock).
- Manual E2E tests: the full journeys (§5).
Numbers: 41 test files, ~203 tests (checkout 48, shop 38, accounts 32, cart 20, b2b 17,
backoffice 11, customer_area 10, main 9, forecasting 7, common 6, analytics 5).

## 3. Test configuration
`backend/pytest.ini`:
```ini
DJANGO_SETTINGS_MODULE = config.settings.test   # TEST settings (fast MD5 hashing, dev-only)
testpaths = apps
addopts = --cov=apps --cov-report=term-missing --cov-report=html --cov-fail-under=70
```
The ≥ 70 % coverage gate is enforced: the command fails below it.
`backend/conftest.py` provides shared fixtures (`sample_customer`, `sample_product`,
`sample_admin`) built before each test in an isolated test database.

## 4. CI (`.github/workflows/tests.yml`)
1. starts a throwaway PostgreSQL (same 16-alpine version as local);
2. installs test dependencies;
3. runs `pytest` (with the coverage gate);
4. publishes the HTML coverage report as a downloadable artifact.
Companion workflows: `lint.yml` (black/isort/flake8) and `security.yml` (pip-audit/bandit).
```bash
docker compose exec django pytest                        # whole suite + coverage
docker compose exec django pytest apps/checkout/tests -v # a specific module
```

## 5. Manual E2E checklist (44 checks — Portfolio/task5 §5.2.6)
- Full B2C purchase: homepage → language → catalog → AJAX cart → login → CH address → Stripe
  (4242 4242 4242 4242) → confirmation → email → DB check.
- Customer account: register, login, history, password reset.
- B2B form: submission, notification email, B2BRequest in DB.
- Back-office: KPIs, product CRUD, stock, B2B management, 403 for a plain customer.
- Security: unauthenticated access → redirected; someone else's order → 404 (no leak); webhook
  without signature → 400; CSRF without token → rejected; SQL injection → neutralised by the
  ORM.
Run the checklist and tick it (it has Date / Executed by fields) as final QA evidence.

## 6. Bug-resolution evidence
`fix(...)` PRs: #14 (auth), #29 (UI), #38 (customer_area FK), #44 (auth contrast), #48 (i18n
switcher) + code fixes (CSRF cookie, overselling via select_for_update, Secure cookie in dev).

## 7. Security & Swiss compliance in QA
- Payment: no card data on the server (PCI delegated to Stripe); webhook signature verified.
- nLPD/GDPR: consent is opt-in; analytics only loads after consent; `ConsentLog` is immutable
  (audit trail); consent uses SET_NULL so proof is never lost.
- Access control tested: back-office 403 for non-staff; B2B decorators redirect without leaking
  whether a resource exists.
