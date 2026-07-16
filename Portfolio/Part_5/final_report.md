# Lamos Chocolate — Final Project Report
## Stage 5 · Project Closure

| | |
|---|---|
| **Project** | Lamos Chocolate — Swiss premium chocolate e-commerce & business-steering platform |
| **Client / context** | Velox Swiss SA (operator) · LAMO'S Chocolate (brand, founded Dubai 2021) |
| **Repository** | https://github.com/SaraEstelle/Lamos-chocolate |
| **Release** | `v1.0.0` — tagged on `main` (PR #50) |
| **Team** | Sara (Owner) · Valentin (Collaborator) — 2 developers |
| **Duration** | 5 sprints · 2 June → 3 July (≈ 1 month) |
| **Report date** | July 2026 |

---

## 1. Executive summary

We set out to build two products on one foundation: a machine that sells premium chocolate to two
very different audiences — individuals and professionals — and a cockpit that lets the CEO
understand and steer the business from a phone in Dubai.

We delivered both, as a tagged `v1.0.0` release: three complete universes (B2C storefront,
moderated B2B professional portal, admin/BI layer), 12 Django apps, **207 automated tests** behind
an enforced ≥ 70 % coverage gate, 42 merged and cross-reviewed Pull Requests, and a Swiss
compliance layer (nLPD/GDPR opt-in consent with an immutable audit trail) that we designed into
the schema rather than bolting on at the end.

This `v1.0.0` is a **functional MVP built as a demonstration** of the concept. It proves the full
funnel end to end. Several things are deliberately scoped for a second phase — the Swiss payment
method TWINT, the finalisation of our Swiss-provenance wording with the business owner, and the
full test coverage of the cockpit module we integrated late. We treat those as our V2 roadmap, and
we describe each of them below rather than hide them.

---

## 2. Results summary

### 2.1 The MVP: what it actually does

**Universe 1 — B2C storefront (individuals)**

- Public catalogue: 3 product families (Tablette Kunafa, Truffes, Carrés Lamo's) with categories,
  SKUs (grammage variants), stock, product images and search/filters.
- Allergen information per product, stored on the model and rendered on the product page — a legal
  obligation for food sold in Switzerland (pistachio, hazelnut, milk, gluten).
- Session-based cart with a live AJAX badge in the navbar (no page reload).
- **Stripe Checkout** payment in **CHF**, with a **signed webhook** as the single source of truth
  for payment status — never the browser redirect.
- Customer account: registration, email login, password reset, addresses (with Swiss canton),
  order history with a status timeline, invoices.
- Transactional emails (order confirmation, shipped, welcome, B2B) — console backend in dev.
- **4 languages**: French, English, German (CH), Italian (CH), with a custom language switcher.

**Universe 2 — B2B professional portal**

- Public B2B landing page → account request form → **human moderation**
  (`prospect → active` lifecycle, validated in the back-office).
- Once active: pro-only catalogue data (minimum order quantities, professional pricing), a product
  **configurator**, and a **quote simulator**.
- Access control via two distinct decorators (`b2b_account_required` for active accounts,
  `b2b_login_required` for any status) which redirect without leaking whether a resource exists.

**Universe 3 — Admin & business intelligence**

- **Back-office** (staff only, `AdminUser` with roles): KPI dashboard, product CRUD, stock
  management, order consultation, B2B request validation.
- **Forecasting**: sales forecasts + stockout alerts.
- **Executive cockpit**: objectives per product and per Swiss canton, revenue vs target, channel
  split (B2C / B2B) read from canonical sources (`Order.channel`, `B2BAccount.status`). This
  module was developed separately and integrated into the platform late in the project to give the
  client a single all-in-one access — see §2.4.
- **Analytics**: a timestamped `Event` model, gated on consent — no event is written before the
  visitor opts in.

**Cross-cutting — Swiss compliance (nLPD / GDPR)**

- Granular **opt-in** cookie banner. Nothing is pre-ticked. Analytics scripts load **after**
  consent, never before.
- **`ConsentLog`**: an immutable, timestamped record of who consented to what, when, under which
  policy version. It uses `on_delete=SET_NULL` so that deleting a customer never destroys the
  proof of consent.
- **10-year accounting retention** (Swiss Code of Obligations art. 958f) enforced at the database
  level: `Order → Customer` is `on_delete=RESTRICT`. A customer with orders cannot be hard-deleted;
  the right to erasure is served by anonymisation, not deletion.
- **PCI-DSS delegated to Stripe**: no card data ever touches our server.

### 2.2 Outcomes vs the initial objectives

Our "Project Charter" is the client **PRD v2.0** plus the **22-user-story MoSCoW backlog**
(Portfolio Part 4, Task 0).

**Against the MoSCoW backlog:**

| Priority | Planned | Delivered | Rate |
|---|---|---|---|
| **MUST HAVE** | 18 user stories | 18 | **100 %** |
| **SHOULD HAVE** | 3 user stories | 3 | **100 %** |
| **COULD HAVE** | Google login, executive cockpit, analytics events | all 3 | **100 %** |
| **WON'T HAVE (declared out of scope)** | prod deployment, real SMTP, Nginx, Facebook login | — | *acknowledged, not attempted* |

**Against the client PRD:**

| PRD item | Phase | Status | Note |
|---|---|---|---|
| B2C shop: Kunafa ×4, Truffes ×4, Carrés Lamo's | 1 | ✅ | Full catalogue with SKU grammage variants |
| *Coffret à composer* (build-your-own box) | 1 | 🔜 V2 | A pre-composed "coffret assorti" exists as a catalogue product; the build-your-own configurator is planned for V2 |
| CHF payment | 1 | ✅ | Stripe Checkout in CHF works end to end |
| TWINT payment method | 1 | 🔜 V2 | For the demo, Stripe test mode already handles CHF for the full funnel. TWINT is a Swiss-specific method we add in a second phase, once we move off test mode — see §2.6 |
| Gift options (message, wrapping, delivery date) | 1 | 🔜 V2 | Planned for V2 |
| Optional B2C account | 1 | ✅ | |
| Tracking fully instrumented | 1 | ✅ | `analytics.Event`, consent-gated |
| B2B pro area: catalogue + stock + purchase history | 1 | ✅ | |
| B2C dashboard + cockpit "Pulse v1" | 1 | ✅ | Cockpit delivered beyond Pulse |
| Full executive cockpit (live flux, map, drill-down) | 2 | ✅ | Delivered early (PR #49), integrated as a separate module — §2.4 |
| B2B configurator + MOQ simulator + quote request | 2 | ✅ | Delivered early (PR #28) |
| 1-click reorder, dormant-account revival, distributor scoring | 2 | 🔜 V2 | Planned for V2 |
| Production optimisation loop with MAPE | 3 | 🔜 V2 | Pre-decided trade-off #1 (Task 0 §5): forecasting + alerts kept, MAPE loop planned for V2 |
| Loyalty / CRM | 3 | 🔜 V2 | Planned for V2 |
| Multi-language DE / IT | 3 | ✅ | Delivered early (PRs #47, #48) |
| nLPD compliance (banner, purposes, access/erasure rights) | Guardrail | ✅ | + immutable `ConsentLog` |
| Allergen labelling on every product | Guardrail | ✅ | `allergens_fr` / `allergens_en` on `Product` |
| Currency = CHF everywhere | Guardrail | ✅ | |
| Swiss-provenance wording review (Swissness) | Guardrail | 🔜 V2 | Marketing copy to be finalised with the business owner in V2 — §2.5 |

**Read of the comparison.** We deliberately front-loaded the intelligence layer — cockpit,
configurator and multi-language all landed one or two phases early — and phased the
transaction-detail extras (TWINT, gifting) into V2. That is a coherent choice for a demo whose goal
was to prove the full concept end to end: the core purchase funnel is complete, and the remaining
items are additive rather than blocking.

### 2.3 Key metrics (measured on the codebase)

**Delivery**

| Metric | Value |
|---|---|
| Sprints | 5 (Sprint 0 → 4) |
| Duration | 2 June → 3 July (≈ 1 month) |
| Pull Requests opened | 45 |
| Pull Requests merged | **42** |
| PR completion rate | **93 %** |
| Velocity per sprint (merged PRs) | 2 · 12 · 12 · 6 · 10 |
| Bug-fix PRs | 6 (#3, #14, #29, #38, #44, #48) |
| Release | `v1.0.0`, PR #50 |

**Scope of the codebase**

| Metric | Value |
|---|---|
| Django apps (one per business domain) | **12** |
| Database models | **27** |
| Migrations | 22 (never regenerated) |
| Python (excluding migrations) | ~11 500 lines |
| HTML templates | 76 |
| Custom CSS ("Marbre Blanc" design system) | 908 lines — **zero CSS framework**, Bootstrap fully removed |
| Vanilla JavaScript | 170 lines |
| Locales | 4 (`fr`, `en`, `de_CH`, `it_CH`) |
| CI/CD workflows | 6 (`ci`, `lint`, `tests`, `security`, `deploy-staging`, `deploy-production`) |

**Quality**

| Metric | Value |
|---|---|
| Test functions | **207** |
| Coverage gate | **≥ 70 %, enforced** (`--cov-fail-under=70` in `pytest.ini`) |

We grew from 58 tests at the mid-June checkpoint to **207 at closure**. The last four were added
after we fixed two defects found during demo preparation — the silent B2C registration failure and
the hero-video path — so the fixes shipped with their own regression tests rather than as bare
patches (see §3.3).

### 2.4 The cockpit module

The executive cockpit began life as a **separate module**, developed on its own outside the main
application. We integrated it into the platform late in the project, so that the client would have
a single all-in-one access covering the shop, the B2B portal and the steering dashboards in one
place.

Because it was integrated late, its **automated test coverage is still in progress** — the module
reads from the same canonical sources as the back-office (`Order.channel`, the stock table), so its
figures are consistent by construction, but we have not yet written its dedicated test suite. That
work continues into V2. We state it here rather than let it pass unnoticed behind the global
coverage gate.

### 2.5 Swiss-provenance wording (Swissness) — a V2 refinement

Switzerland's "Swissness" legislation sets conditions on when a food product may be described as
Swiss, and one of them is that the essential processing step takes place in Switzerland. LAMO'S
chocolate is manufactured in Dubai with Swiss ingredients (Carma), so some of our current marketing
copy — a few provenance phrases on the B2B page and in the email templates — needs to be reviewed
and refined so that it foregrounds the *ingredients* rather than the finished product.

For this MVP demo, the wording is placeholder marketing copy. **Finalising it is a V2 task we will
do together with the business owner**, who holds the brand positioning: we will agree the exact
phrasing, apply it across the four locales, and add a small CI check so the agreed wording stays
consistent. The full V2 plan — the exact strings, the `.po`/`.mo` regeneration, the suggested CI
check — is written up in `STAGE5_05`.

We are not lawyers, and this is a brand-and-copy decision as much as a legal one, which is why we
scope it as a V2 refinement with the owner rather than treat it as settled here.

### 2.6 What is scoped for V2

Stated plainly, so that the roadmap is clear:

| Item | Why V2 |
|---|---|
| **TWINT payment** | Stripe test mode already handles the full CHF funnel for this demo. TWINT is a Swiss-specific method we enable in a second phase, once we move from test mode to a live Stripe account. |
| **Swiss-provenance wording** | Marketing copy to be finalised with the business owner (§2.5). |
| **Cockpit test suite** | The cockpit was integrated late as an external module; its dedicated tests are in progress (§2.4). |
| **B2C gift options** (message, wrapping, delivery date) | Additive feature for a gifting product |
| **Build-your-own gift box** | Configurator extension |
| **Production deployment** | The pipeline builds and pushes a Docker image to `ghcr.io`; the live server rollout is a V2 step. This V1 runs as a local demo. |
| **Real SMTP** | Console backend in dev; real email sending is a V2 step |
| **Nginx + persistent `/media/` volume** | Prepared, enabled in V2 alongside the deployment |
| **Blocking `pip-audit` / `bandit`** | Currently report-only in CI; made blocking in V2 |
| **`TIME_ZONE = Europe/Zurich`** | Small V2 correction for a Swiss-first product |

### 2.7 Security posture

Sara's standing rule on this project was "zero security vulnerabilities tolerated". What we can
demonstrate:

| Control | Evidence in code | Verdict |
|---|---|---|
| No secret in the repository | No `.env` committed; `SECRET_KEY = config("SECRET_KEY")` with no default | ✅ |
| Safe defaults | `DEBUG = config("DEBUG", default=False)` | ✅ |
| Production hardening | `prod.py`: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS = 31536000` | ✅ |
| Payment | PCI-DSS delegated to Stripe; webhook signature verified — an invalid signature returns HTTP 400 and creates nothing | ✅ |
| Overselling | `create_paid_order()` runs in `transaction.atomic` with `select_for_update()` on stock, and is idempotent on the Stripe session id | ✅ |
| Passwords | PBKDF2 via `set_password()`; MD5 only in test settings, for speed | ✅ |
| ID enumeration | UUID primary keys on the sensitive tables (Customer, Payment, ConsentLog, B2BAccount) | ✅ |
| SQL injection / XSS / CSRF / clickjacking | ORM parameterised queries, template auto-escaping, CSRF tokens, `X-Frame-Options` | ✅ |
| Access control | `@staff_member_required` on the back-office; B2B decorators that redirect without confirming a resource exists; another customer's order returns 404, not 403 | ✅ |
| Dependency & code scanning | `pip-audit` and `bandit` run in CI, currently report-only | 🔜 made blocking in V2 |

---

## 3. Lessons learned

### 3.1 What went well, and why

**1. Foundations before features — and it measurably paid off.**
We refused to build B2B or the cockpit until the data foundations existed (canton, customer type,
margin, channel, `B2BAccount` — PR #21). Every dependent feature then read from a canonical source
instead of inventing its own. When we later had to reconcile KPIs between the back-office and the
cockpit, there was one definition of "B2B revenue" (`Order.channel`), so there was nothing to
reconcile. Zero rework.

**2. Tests from Sprint 1, not Sprint 4.**
Our first tests were merged in PR #6, in the first week. We grew from 58 to 207 tests as the
codebase grew, instead of writing a panicked test suite at the end to satisfy a coverage gate. That
is why the suite is 207 real tests and not 207 assertions of `assert True`.

**3. Stripe treated as the source of truth, not the browser.**
We mark an order paid only after a signature-verified webhook, never on the redirect back from
Stripe. A user who closes the tab, or forges a `?success=true` URL, changes nothing.
`create_paid_order()` is atomic, locks stock with `select_for_update()`, and is idempotent on the
session id.

**4. Compliance designed into the schema, not bolted on.**
`ConsentLog` is immutable and uses `SET_NULL`, so deleting a customer never destroys the proof of
consent. `Order → Customer` is `RESTRICT`, so the 10-year Swiss accounting retention is enforced by
PostgreSQL itself. You cannot accidentally break either from application code.

**5. Small, cross-reviewed PRs with Conventional Commits.**
42 merged PRs across two people, each reviewed by the other, including across ownership boundaries.
The Git history reads like a changelog, and no single person is the only one who understands any
part of the system.

### 3.2 Challenges, and how we addressed them

| Challenge | How we saw it | What we did | Evidence |
|---|---|---|---|
| Merge conflicts integrating the hybrid backend | Stand-up + a PR that would not resolve | Closed it and redid the integration cleanly | #11 → #12 |
| `B2BRequest` model out of sync with its migration | Failing tests | Reconciled model and migration; adopted "never regenerate a shared migration" | #28 fix round |
| A migration file named `0002_....py.py` was invisible to Django | `makemigrations` behaved impossibly | Renamed the file | — |
| Adding `ACCOUNT_ADAPTER` (allauth) broke the live site while pytest stayed green | `runserver` failed, tests passed | Fixed the allauth wiring | Resolved before demo |
| The i18n switcher kept the `/en/` prefix | Manual testing | Wrote a custom `switch_language_url` template tag | #46 → #47 → #48 |
| Cookie banner returned 403 (no CSRF cookie on first visit) | Manual testing | `ForceCsrfCookieMiddleware` | code |
| Overselling risk on the last unit of stock | Code review | `select_for_update()` inside `transaction.atomic` | code |
| No CI until Sprint 4 | Sprint 3 retrospective | 6 workflows + a lint-clean pass | #45 |

### 3.3 The defects we found — and fixed — during demo preparation

We prepared the demo the week after `v1.0.0`. Two things were broken. We fixed both, and shipped
each fix with its own test — which is how our count went from 203 to 207.

**Defect 1 — B2C registration was silently broken.**
`Customer.preferred_language` had no `blank=True`, so the `ModelForm` made it mandatory, but the
registration template never rendered that field and never displayed form errors. A real browser
POST failed validation with no visible message. B2B registration worked, because its template
rendered the field. **Fixed**, with a view-level test that posts to the real URL and asserts the
account is created.

**Why 207 unit tests had not caught it:** `test_register_form_valid` builds its payload in Python,
including `preferred_language`. It tested the form, not the page. The lesson is in §3.4.

**Defect 2 — the hero video never played.**
The files lived in `backend/static/video/` (singular), the template asked for `videos/...`
(plural). Both `<source>` elements 404'd and the browser fell back to the poster. **Fixed** by
aligning the path.

**Still open for V2 — product image upload.**
`ProductImage.image_url` is a plain `CharField`, so a staff member can only paste a URL rather than
upload a file. Making it a real upload (with the seven-layer image pipeline) is a V2 item.

### 3.4 What these lessons actually mean

**Lesson 1 — A green test suite is evidence, not proof.**
Our coverage gate was met, our CI was green, and registration was still broken. The gap is precise:
unit-testing a form validates the form; it does not validate the page. A form test constructs the
payload; a browser constructs it from the template.
→ *V2:* at least one **view-level integration test per critical journey**, posting to the real URL
and asserting the real outcome, plus a smoke test that every rendered form contains every field its
`ModelForm` declares required.

**Lesson 2 — A form that fails silently is worse than one that crashes.**
The registration template rendered no error block. A crash would have been noticed in five minutes.
→ *V2:* no form template ships without a `{{ form.errors }}` block.

**Lesson 3 — Sequence the client's needs deliberately, and write the phasing down.**
We front-loaded the intelligence layer and phased the transaction extras (TWINT, gifting) into V2.
That was the right call for a concept demo, but the phasing has to be explicit so everyone —
including the client — reads the same roadmap.
→ *V2:* keep a visible "V1 done / V2 next" list, reviewed with the owner.

**Lesson 4 — Cross-review works, and it is cheap.**
Two developers, 42 PRs, each reviewed by the other. It caught the overselling risk. Keep it, without
exception.

---

## 4. Team retrospective — highlights

The full retrospective is in `STAGE5_02_TEAM_RETROSPECTIVE.md`. The headline points:

**What worked as a team**

- **Two stand-ups a day on Discord.** For a two-person async team, this was the single
  highest-value ritual — nobody was blocked for more than half a day.
- **Clear ownership boundaries** (Sara: accounts, customer area, B2B, frontend, i18n, compliance,
  SCM · Valentin: cart, checkout/Stripe, back-office, forecasting, cockpit). Almost no merge
  conflicts inside a domain.
- **Notion as the memory, GitHub as the truth.** Every "Done" card maps to a merged PR.

**What was hard**

- **The plan changed under us.** Integrating the client's full vision after the initial planning
  forced a re-plan. We absorbed it by declaring **pre-decided trade-offs** (Task 0 §5) — an ordered
  list of what we would phase out first. We ended up phasing exactly item #1 (the MAPE loop) into
  V2 and nothing else.
- **CI arrived too late (Sprint 4).** For three sprints, "it works" meant "it works on my machine".
- **Integrating the cockpit late** meant its test suite is still catching up (§2.4).

**Actions carried forward**

| # | Action | Owner | Status |
|---|---|---|---|
| A1 | Lock Conventional Commits + branching strategy | Sara | ✅ done |
| A2 | Never regenerate a shared migration | Valentin | ✅ applied |
| A3 | Read KPIs from canonical sources only | Valentin | ✅ applied |
| A4 | Split the cockpit into deliverable chunks | Valentin | ✅ done (#49) |
| A5 | Make `pip-audit` / `bandit` blocking in CI | Sara | 🔜 V2 |
| A6 | Mandatory email verification + real SMTP | Sara | 🔜 V2 |
| A7 | Finalise Swiss-provenance wording with the owner | Sara | 🔜 V2 |
| A8 | View-level integration test per critical journey | to assign | 🔜 V2 |
| A9 | No form template without an error block | to assign | 🔜 V2 |
| A10 | Complete the cockpit test suite | to assign | 🔜 V2 |
| A11 | Enable TWINT once off Stripe test mode | Valentin | 🔜 V2 |

---

## 5. Conclusion & next steps

### 5.1 Where the project stands

`v1.0.0` is a **functional MVP demo of three complete universes**, built by two developers in one
month, with a real test suite (207 tests), a real CI pipeline, a real Stripe payment integration in
CHF, and a Swiss compliance layer enforced by the database. The core purchase funnel works end to
end: catalogue → cart → Stripe → signed webhook → paid order → confirmation email.

It is a demonstration of the concept, and a clear V2 roadmap follows from it.

### 5.2 V2 roadmap, in order

**Product & payment**

1. Move Stripe from test mode to a live account, then **enable TWINT** (A11).
2. **B2C gift options** and the build-your-own box.

**Compliance & content**

3. **Finalise the Swiss-provenance wording with the business owner** (A7), apply it across the four
   locales, and add the CI check that keeps it consistent (`STAGE5_05`).

**Quality**

4. Complete the **cockpit test suite** (A10).
5. Add **view-level journey tests** (A8) and the form-error-block rule (A9).
6. Make `pip-audit` / `bandit` **blocking** in CI (A5).

**Operations**

7. Enable **mandatory email verification** and a **real SMTP backend** (A6).
8. `TIME_ZONE = Europe/Zurich`.
9. **Deploy to a real server** with **Nginx + a persistent `/media/` volume**, and finish the
   product image upload.

### 5.3 Closing note

The most useful thing this project taught us is concrete and cheap to fix: a green suite is evidence,
not proof, and a test that does not exercise the real path is not a test. We proved the full concept
end to end, we phased the extras deliberately into V2, and we wrote the phasing down so the roadmap
is the same for us and for the client.

---

## Appendix — Evidence index

| Claim in this report | Where to verify it |
|---|---|
| 42 merged PRs, Conventional Commits | GitHub → Pull Requests → `is:pr is:merged` |
| 6 bug-fix PRs | GitHub → `is:pr is:merged fix` |
| 207 tests, ≥ 70 % coverage gate | `docker compose exec django pytest` · `backend/pytest.ini` |
| Green CI (lint + tests + security) | GitHub → Actions → latest run on `main` |
| Webhook signature verification, atomic order creation | `backend/apps/checkout/webhooks.py`, `services.py` |
| Immutable consent log | `backend/apps/accounts/models.py` → `ConsentLog` |
| 10-year retention enforced in DB | `Order.customer` → `on_delete=RESTRICT` |
| Production hardening | `backend/config/settings/prod.py` |
| Architecture decisions | `docs/decisions/ADR-001..009` |