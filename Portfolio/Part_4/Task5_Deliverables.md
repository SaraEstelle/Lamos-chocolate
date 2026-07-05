# TASK 5 — Deliverables

## 1. Deliverables index
| Deliverable | Where it lives / link | Status |
|---|---|---|
| Source repository (code) | https://github.com/SaraEstelle/Lamos-chocolate | ✅ |
| Sprint planning | Notion (backlog + Kanban): Notion + Task 0 | ✅ |
| Sprint reviews | Notion (meeting notes): Notion + Task 3 | ✅ |
| Retrospectives | Notion (meeting notes): Notion + Task 3 | ✅ |
| Daily stand-ups | Discord (morning/evening): Discord  + Notion notes | ✅ |
| Bug tracking | GitHub fix(...) PRs (#14, #29, #38, #44, #48): https://github.com/SaraEstelle/Lamos-chocolate/pulls?q=is%3Apr+sort%3Acreated-asc | ✅ |
| Testing evidence | GitHub Actions (green run) + coverage-html artifact + E2E checklist (task5 §5.2.6) | ✅ |
| Deployment tracking | Notion ("Deployment" page): Notion | ✅ (preparation) |
| Production environment | no server deployed — image ghcr.io/SaraEstelle/Lamos-chocolate:latest | ⚠️ not deployed |
| Release | Tag v1.0.0 (#50): https://github.com/SaraEstelle/Lamos-chocolate/pull/50 | ✅ |

## 2. Where to find each proof
- Testing evidence: GitHub Actions tab → a green "CI" run → shareable link; in the run,
  Artifacts → download `coverage-html`.
- Bug tracking: on GitHub, filter `is:pr is:merged fix` → the fix PRs.
- Planning & tracking: the Notion workspace (backlog, Kanban, stand-up notes, decision log,
  Deployment page).
- Team communication: the Discord server (morning/evening stand-ups).

## 3. Written checkpoints & guides (dated deliverables to attach)
| Date | Document | Type |
|---|---|---|
| ~Jun 15 | Revised master plan (18-day, 3-universe MVP) | Planning |
| ~mid-Jun | Coach checkpoint (backend ~55 %, 58 tests, 4 decisions) | Status |
| Jun 23 | Progress report on develop (~55–60 %, 128 tests) | Monitoring |
| Jun 24 | Full audit of develop (~70 %, 152 tests) | Audit |
| Jun 30 | Master plan (final push) | Planning |
| Jul 2 | develop report (structure + i18n) | Monitoring |
| Jul 3 | Status report + demo guide | Demo prep |
| — | Implementation guides (django-core, F-DATA, F-CATALOG, F-EVENTS…) | How-to |
| — | ADRs (docs/decisions/ADR-001..009) | Decisions |

Keep these under `docs/reports/` and `docs/decisions/`; they complement the Notion tracking and
the GitHub history.

## 4. Production environment (status)
There is no live production server. The `deploy-production.yml` pipeline builds and pushes a
Docker image to ghcr.io, but the server rollout step is a placeholder (no host/secrets). The
deployment tracking on Notion followed the preparation (image build, v1.0.0 release checklist),
not a live deployment.
