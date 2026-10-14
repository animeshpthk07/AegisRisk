# Execution tracker

Started 2026-10-13. Updated 2026-10-14. Public GitHub publication approved by the owner. No external AI enabled.

## Current activity — live development

The frontend-to-backend-to-database flow was verified locally. The foundation source is now published at https://github.com/animeshpthk07/AegisRisk. Current work uses VS Code for the Web and GitHub in the visible browser, as requested. The local preview is not a public deployment.

### What is saved

- Separate Git repository at `work/AegisRisk`; Finance Workbench is untouched.
- Next.js 16.4 / React 19.3 / TypeScript / Tailwind / Recharts frontend.
- FastAPI / SQLAlchemy / Alembic backend, explicit seed of 40 fictional INR facilities.
- Decimal EL calculation, EAD weights, borrower HHI, industry breakdown, search and scenario sensitivity.
- Deterministic narrative. No external AI provider or API credentials.
- PostgreSQL Compose and CI definitions. Docker/PostgreSQL runtime remains unverified; CI results must be checked in GitHub Actions.

### How it works

Browser → fixed Next.js API proxy → FastAPI validation → SQLAlchemy database reads → Decimal calculations → dashboard.

### Actual checks so far

- Backend: **25 tests passed**, one dependency deprecation warning (Starlette's httpx test-client integration).
- Backend lint: **passed**, after fixing import/format issues.
- Frontend type checking: **passed**.
- Frontend formatting unit tests: **3 passed**.
- Next.js production build: **passed**.
- Live frontend → API → database readiness: **passed**.
- Browser verified: 40 facilities, INR 115,000,000 EAD, INR 2,769,125 expected loss.
- Browser search: `SYN-001` returns exactly one facility.
- Browser stress: PD ×1.5, LGD ×1.1, EAD ×1 returns a 65% EL increase (display-rounded INR 4,569,056).
- Browser preview visibly confirmed at narrow pane width. Full accessibility/E2E suite and security scans remain outstanding.
- Docker/PostgreSQL runtime: not tested; Docker is not installed.
- Public hosted deployment: not verified. GitHub Actions: workflow being published; no passing result claimed yet.

### What you can inspect

`apps/web/app/page.tsx` contains the dashboard. `apps/api/aegisrisk/main.py` exposes API endpoints. `risk.py` contains the formulas. `docs/ARCHITECTURE.md` explains the system, `docs/DEVELOPMENT.md` shows how to run it, and `docs/SECURITY.md` records limits.

This is a foundation slice, not the completed AegisRisk product. ML, imports, reports, full security verification and career materials remain incomplete.

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 Foundation | In progress | Local isolated workspace; integration contract |
| M1 Data layer | Partial | SQLAlchemy facilities, Alembic migration and 40 synthetic records; imports pending |
| M2 Risk mathematics | Partial | Decimal EL, weighted metrics and HHI implemented and tested; full scope pending |
| M3 ML | Not started | No model performance claims |
| M4 Stress | Partial | Bounded PD/LGD/EAD sensitivity verified; broader scenarios pending |
| M5 API | Partial | Versioned foundation endpoints and validation tests; full scope pending |
| M6 Full frontend | Partial | Portfolio dashboard and scenario controls; full workbench pending |
| M7 Explanations | Not complete | Deterministic only; external AI deferred |
| M8 Reports | Not started | |
| M9 Security | In progress | Local-only, synthetic-only, no API credentials |
| M10 Full verification | Not started | |
| M11 Deployment | Not complete | Public source published; no hosted application verified or paid service purchased |
| M12 Release | Not started | |
| Career presentation and learning | Not started | Begin after credible verified application |

## Visible workflow requested by user

1. **Code:** visible browser editor at https://vscode.dev/github/animeshpthk07/AegisRisk (`apps/web`, `apps/api`). Browser-only work is the current instruction.
2. **Run:** local frontend http://127.0.0.1:3000, backend http://127.0.0.1:8000/docs.
3. **Verify:** tests, browser interactions, and recorded results here. Never label checks passed just because files exist.
4. **GitHub:** public MIT repository created with approval; backend and dashboard committed. Review commits and Actions through the visible browser.
5. **Release:** deployment only after required verification and user approval; no hosting account or expense created.
6. **LinkedIn:** case study/project/launch drafts after verification; show exact content before publishing.

Earlier local runtime checks are historical results, not a claim that those processes are still running. No paid services or external AI credentials have been configured.
