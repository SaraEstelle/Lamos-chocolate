# TASK 3 — Sprint Reviews & Retrospectives

Format per sprint: a Review (demo of what was delivered) and a Retrospective (what worked /
challenges / improvements, each with an action and an owner). End-of-sprint reviews were run on
Discord (screen-share demo) and logged in Notion.

## Sprint 0 — Setup
- Review: restructured `backend/apps/*` tree and naming conventions (#2, #3).
- Retro: 👍 a clean structure from the start · ⚠️ agreeing on conventions as a pair · 🔧 lock
  Conventional Commits + branching strategy (owner: Sara).

## Sprint 1 — Foundations
- Review: create an account (email), log in, browse the catalog, see the customer area; first
  passing tests.
- Retro: 👍 custom user model (UUID + email) and tests from Sprint 1 · ⚠️ merge conflicts
  integrating the hybrid backend → PR #11 closed · 🔧 redo the integration cleanly (#12); never
  regenerate shared migrations (owner: Valentin).

## Sprint 2 — Commerce & admin
- Review: add to cart, back-office with KPIs, B2B funnel, forecasting alerts, homepage,
  transactional emails (console backend).
- Retro: 👍 data foundations laid before dependent features → no rework · ⚠️ `B2BRequest` model
  desync caused a cascade of bugs; KPI consistency (B2B/B2C) across back-office and cockpit ·
  🔧 reconcile the B2B model + migration; read KPIs from canonical sources (`Order.channel`,
  `B2BAccount.status`) (owner: Valentin).

## Sprint 3 — Design & payment
- Review: full purchase journey — catalog → AJAX cart (badge) → Stripe checkout (test card
  4242…) → webhook → paid order.
- Retro: 👍 fully removed Bootstrap for the "Marbre Blanc" design; end-to-end purchase · ⚠️ the
  Stripe webhook runs without a session; the cockpit was too large → left as a draft (#36) ·
  🔧 mark an order "paid" only after the signed webhook (source of truth = Stripe); split the
  cockpit to deliver later (#49) (owner: Valentin).

## Sprint 4 — Compliance & release
- Review: granular consent banner, language switch across 4 languages, green CI, executive
  cockpit, v1.0.0 release.
- Retro: 👍 nLPD/GDPR compliance in the schema (immutable `ConsentLog`) and in the code
  (analytics only after consent); CI protects quality · ⚠️ the i18n switcher took two passes
  (#46 closed → #47 → fix #48) · 🔧 make `pip-audit`/`bandit` blocking; enable mandatory email
  verification in production (owner: Sara).

## Improvement actions (tracking)
| # | Action | Sprint | Owner | Status |
|---|---|---|---|---|
| A1 | Lock commits + branches | 0 | Sara | done |
| A2 | Don't regenerate migrations | 1 | Valentin | applied |
| A3 | KPIs from canonical sources | 2 | Valentin | applied |
| A4 | Split the cockpit | 3 | Valentin | done (#49) |
| A5 | Blocking security CI + email verification | 4 | Sara | planned (post-MVP) |