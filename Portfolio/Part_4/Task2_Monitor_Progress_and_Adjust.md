# TASK 2 — Monitor Progress and Adjust

## 1. Tracking setup

### Discord stand-ups (morning & evening)
We synced twice a day. Morning: what each of us will do today, blockers, task/dependency
split. Evening: what got done, what's left, next-day prep.
Format:
```
1) Done since the last sync?
2) Planned until the next sync?
3) Blockers / dependencies?
```

### Notion board
Backlog (MoSCoW), Kanban (To do → In progress → In review → Done, each card linked to its PR),
meeting notes, decision log, and a deployment-tracking page.

### GitHub
Each Notion *Done* card maps to a reviewed, merged PR with a CI status (from Sprint 4). This is
our objective proof of progress.

## 2. Metrics

Velocity (merged PRs per sprint):
| Sprint | Merged PRs |
|---|---|
| 0 | 2 |
| 1 | 12 |
| 2 | 12 |
| 3 | 6 |
| 4 | 10 |
| Total | 42 |

PR completion rate: 42 merged / 45 opened = 93 %. The 3 non-merged (#11, #36, #46) were redone
and delivered another way (see §5).

% complete vs planned (MoSCoW): Must 18/18 (100 %) · Should 3/3 (100 %) · Could (Google,
cockpit, analytics) delivered · Won't (prod deploy, real SMTP, Nginx, Facebook) acknowledged.

Bugs — count & resolution:
| Fix PR | Bug |
|---|---|
| #3 | conventions/structure |
| #14 | auth finalisation |
| #29 | logout / footer / register errors |
| #38 | customer area FK resolution |
| #44 | auth form contrast |
| #48 | i18n switcher logic |
Resolution rate: 100 % (all merged before the release).

## 3. Written checkpoints (dated monitoring artifacts)
| Date | Artifact | Captured |
|---|---|---|
| ~Jun 15 | Revised master plan | 18-day plan; deadline moved Jun 22 → Jul 3 to absorb the client vision (advanced B2B + cockpit) |
| ~mid-Jun | Coach checkpoint | Backend ~55 %, 58 tests green, 4 architecture decisions taken (§6) |
| Jun 23 | Progress report (develop) | ~55–60 %, 128 test functions; blockers: Stripe, home 404, B2B not yet merged, analytics not wired, cookie/nLPD, empty CI |
| Jun 24 | Full audit (develop) | ~70 %, 152 test functions; B2B merged, home routed, 6 email templates, B2BProductInfo. Remaining: Stripe (0-byte files), design/content, social login, cookies, CI, i18n |
| Jun 30 | Master plan (final push) | UI fixes, checkout, i18n, emails, deploy |
| Jul 2 | develop report | Repo structure + i18n routing |
| Jul 3 | Status report + demo guide | i18n switcher bug, missing product photos, Stripe local setup, cookie-banner behaviour, console emails |

## 4. Progress trend (measured)
Test-count growth (a QA proxy for progress):
| Date | Tests | Completion |
|---|---|---|
| ~mid-Jun | 58 | backend ~55 % / global ~40 % |
| Jun 23 | 128 | develop ~55–60 % |
| Jun 24 | 152 | develop ~70 % |
| Jul 3 (v1.0.0) | ~203 | MVP scope 100 % |

Reconciliation: items flagged "missing" on Jun 23–24 (Stripe, cookie/nLPD, CI, i18n) were
delivered before release (PRs #39 Stripe, #43 consent, #45 CI, #47 i18n). The reports are
point-in-time snapshots; the final `main` (v1.0.0) is complete.

## 5. Blockers & adjustments
| Blocker | How seen | Adjustment | Evidence |
|---|---|---|---|
| Conflicts integrating the hybrid backend | stand-up + PR | close and redo cleanly | #11 → #12 |
| `B2BRequest` model desync (cascade of bugs) | tests | reconcile model + migration | #28 round of fixes |
| Migration `0002_...py.py` double extension (invisible to Django) | makemigrations | rename to `.py` | fixed |
| Site-access bug (allauth `ACCOUNT_ADAPTER`/middleware blocks runserver, not pytest) | runserver | fix allauth wiring | resolved before demo |
| Cockpit too large in one go | sprint review | split, deliver later | #36 → #49 |
| i18n switcher (URL stays `/en/`) | manual test | template tag computed at render | #46 → #47 → #48 |
| Missing product photos (fixtures point to non-existent files) | demo prep | add image files | Jul 3 |
| Cookie banner 403 (missing CSRF cookie) | manual test | ForceCsrfCookieMiddleware | code |
| Overselling risk (last stock) | code review | select_for_update + atomic | code |
| No CI at first | Sprint 3 retro | add 6 workflows + lint-clean | #45 |

## 6. Decision log
| # | Decision | Why | Trade-off |
|---|---|---|---|
| D1 | Hybrid DB model ("Option C") | Spec backbone (SKU, ShippingZone, bilingual) + production additions (separate Payment, ProductImage, UUID) | Finished product over minimal MVP |
| D2 | Native Django auth ("Option B") | Customer on AbstractBaseUser + PermissionsMixin instead of a hand-rolled password_hash | We diverge from the design doc (documented as an addendum) |
| D3 | Address on Order, not Customer | An order can ship to a different address; historical accuracy | Some denormalised fields |
| D4 | AdminUser stays custom | Django allows one AUTH_USER_MODEL (= Customer); staff use a separate model | Two auth surfaces |
Full text: `docs/decisions/ADR-006..009`.

## 7. Deployment tracking
| Environment | Status | Evidence |
|---|---|---|
| Local (Docker Compose) | works (`docker compose up -d`) | containers lamos_postgres + lamos_django |
| CI (GitHub Actions) | green (lint + tests + security) | Actions tab |
| Production image | built & pushed to ghcr.io | deploy-production.yml |
| Production server | not deployed (rollout placeholder) | — |
| Release | v1.0.0 tagged | #50 |

Release checklist (v1.0.0): develop merged into main ✅ · CI green on main ✅ · no secret in
repo (.env ignored) ✅ · README up to date ✅ · tag v1.0.0 ✅ · deploy to a server ☐ (planned).

Note: the deployment tracking followed the preparation for deployment (image build + release
checklist), not a live production server — there is none.