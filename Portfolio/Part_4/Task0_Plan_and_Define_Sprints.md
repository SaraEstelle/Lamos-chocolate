# TASK 0 — Plan and Define Sprints

## 0. Planning method
We are two developers: Sara (Owner) and Valentin (Collaborator). We plan and track on:
- **Discord** — morning and evening stand-ups (split the day + clear blockers in the morning,
  review progress in the evening).
- **Notion** — backlog, Kanban board (To do → In progress → In review → Done), meeting notes,
  decision log, deployment tracking.
- **GitHub** — the source of truth for code (branches, Pull Requests, CI). Each Notion card in
  *Done* maps to a reviewed, merged PR.

**Definition of Ready:** a task has a user story, a clear acceptance criterion, an owner, and
its dependencies are delivered.
**Definition of Done:** code + tests written, PR reviewed and merged into `develop`, CI green,
Notion card moved to *Done*.

## 1. Capacity & cadence
- Team: 2 developers. Sprint length: ≈ 1 week.
- Indicative capacity: ~6–12 merged PRs per sprint.
- Time anchor: first PR merged on June 2 (#2); v1.0.0 release around July 3 (#50).

## 2. Sprint calendar (5 sprints)
| Sprint | Theme | Dates (approx.) | Main goal |
|---|---|---|---|
| 0 | Setup | Jun 2 → 8 | Restructure the repo, conventions, clean foundation |
| 1 | Foundations | Jun 9 → 15 | Auth, catalog, customer area, first tests |
| 2 | Commerce & admin | Jun 16 → 22 | Cart, back-office, B2B, forecasting, homepage, emails |
| 3 | Design & payment | Jun 23 → 29 | Design system, Stripe, social login |
| 4 | Compliance & release | Jun 30 → Jul 3 | nLPD, i18n, CI/CD, cockpit, v1.0.0 release |

Note: sprint weeks are accurate (Git merge order); the exact day is approximate (only June 2,
#2, is an explicit date).

## 3. Prioritised backlog (MoSCoW) — 22 user stories
Prioritisation logic: an e-commerce site only earns money if the full purchase funnel exists,
so the whole funnel is a Must.

**MUST HAVE:** US-01/02 homepage + brand page · US-03 language switcher · US-04/05 catalog +
product page · US-06 filters · US-07/08 cart + management · US-09 Stripe payment · US-10
confirmation email · US-11/12/13 account/login/reset · US-14 order history · US-15 B2B form ·
US-17/18/19/20 admin auth + product CRUD + stock + B2B requests · US-22 BI dashboard +
forecasting.
**SHOULD HAVE:** US-06 filters · US-16 B2B offer page · US-21 admin order consultation.
**COULD HAVE (delivered):** Google social login · executive cockpit · analytics events.
**WON'T HAVE (this MVP):** real production deployment · real SMTP (console in dev) · Nginx
enabled · Facebook login (configured, disabled).

## 4. Assignments & dependencies

### Sprint 0 — Setup
| Task | PR | Owner |
|---|---|---|
| Restructure the repo (apps by domain) | #2 | Sara |
| Standardise Python/Django naming | #3 | Sara |

### Sprint 1 — Foundations
| Task | US | PR | Owner | Depends on |
|---|---|---|---|---|
| Django core + settings | — | #4 | Sara | Sprint 0 |
| Checkout: shipping_zone FK + quantity check | US-09 | #5 | Valentin | #4 |
| Model + forecasting unit tests | — | #6, #8 | Valentin | #4 |
| Hybrid backend Payment + ProductImage (+ERD) | US-09 | #9, #10 | Valentin | #4 |
| Option B auth (Customer UUID/email) | US-11/12 | #12, #13, #14 | Valentin/Sara | #4 |
| Public catalog | US-04/05 | #15 | Valentin | #4 |
| Customer area v1/v2 | US-14 | #18, #19 | Sara | auth |

### Sprint 2 — Commerce & admin
| Task | US | PR | Owner | Depends on |
|---|---|---|---|---|
| Session cart | US-07/08 | #20 | Valentin | catalog |
| Data foundations (canton, channel, B2BAccount) | US-22 | #21 | Sara | Customer |
| Catalog data | US-04 | #22 | Sara | catalog |
| Analytics (events + KPI) | US-22 | #23 | Sara | data foundations |
| Back-office (dashboard, orders, stock, B2B) | US-17/18/19 | #25 | Valentin | catalog |
| Forecasting (estimates + alerts) | US-22 | #27 | Valentin | stock |
| B2B module (funnel, portal, configurator) | US-15 | #28 | Sara | data foundations |
| Homepage + static pages | US-01/02 | #30 | Sara | — |
| Marble theme + transactional emails | US-01/10 | #31, #32 | Sara | homepage |

### Sprint 3 — Design & payment
| Task | US | PR | Owner | Depends on |
|---|---|---|---|---|
| "Marbre Blanc" design system (drop Bootstrap) | US-01/02 | #33 | Sara | — |
| allauth Google | Could | #34 | Sara | Customer |
| Canton on addresses + denormalisation | US-14 | #35 | Valentin | customer area |
| Live cart AJAX (navbar badge) | US-08 | #37 | Valentin | cart |
| Fix customer_area (FK) | — | #38 | Valentin | customer area |
| Stripe checkout + webhook | US-09 | #39 | Valentin | cart + Order |

### Sprint 4 — Compliance & release
| Task | US | PR | Owner | Depends on |
|---|---|---|---|---|
| B2B/B2C portal overhaul + checkout | US-15/16 | #41 | Sara | design system |
| B2B pro-account validation | US-20 | #42 | Valentin | B2B module |
| nLPD/GDPR consent + ConsentLog | US-03 (GDPR) | #43 | Sara | — |
| Fix auth contrast | — | #44 | Sara | design |
| CI/CD (lint + tests + security) | — | #45 | Sara | tests |
| i18n 4 languages + switcher | US-03 | #47, #48 | Sara | templates |
| Executive cockpit | Could | #49 | Valentin | data foundations |
| v1.0.0 release | — | #50 | Sara | everything |

## 5. Plan evolution (real)
The internal target was first June 22. When we integrated the client vision (advanced B2B
portal + configurator, executive cockpit, KPIs, production loop), we re-planned to June 3 →
July 3 (18 days), choosing a functional MVP of the three universes (B2C, advanced B2B,
cockpit) on solid data foundations.

Foundations-first strategy (dependencies drove the order):
```
WAVE 1 (foundations)   F-DATA → F-CATALOG + F-EVENTS
WAVE 2 (B2B & steering) F-B2B-PORTAL → F-B2B-CONFIG → F-KPI
WAVE 3 (cockpit & prod) F-COCKPIT → F-PROD-LOOP
WAVE 4 (premium/polish) gifting, i18n, responsive, a11y, SEO, deploy
```
Planned merge order: F-DATA → (F-CATALOG + F-EVENTS) → B2B.

Pre-decided trade-offs if time ran out (least to most critical to keep):
1. Production loop with MAPE → keep a simple recommendation.
2. Interactive canton map → keep a per-canton table.
3. Real-time WebSocket cockpit → keep periodic refresh.
4. Full 4-axis configurator → keep 2 axes (logo + grammage).
5. Keep no matter what: full B2C, B2B area with quotes, cockpit "Pulse", base KPIs, deploy.

## 6. Risks & mitigation
| Risk | Mitigation | Outcome |
|---|---|---|
| Merge conflicts (two devs) | Small PRs + cross-review | #11 closed → redone #12 |
| Feature too large (cockpit) | Split into sub-tasks | #36 draft → delivered #49 |
| Payment security | Delegate PCI to Stripe + signed webhook | OK (#39, #43) |
| Swiss compliance | nLPD in the schema (ConsentLog) | OK (#43) |
