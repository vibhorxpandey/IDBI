# LendLens — RM Dashboard

Bank-grade Relationship-Manager console for LendLens (React + Vite + Tailwind +
Recharts). It renders the ranked leads, a mock Account Aggregator consent flow,
a lead-detail card with SHAP reason codes + the pre-approved offer, portfolio
charts, and the fairness badge.

## Prerequisites

1. Run the Python pipeline so `data/processed/leads.json` exists:
   ```bash
   python run_all.py
   ```
2. Start the API (default port 8000):
   ```bash
   uvicorn api.main:app --port 8000
   ```

## Run the dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open the printed URL (default http://localhost:5173).

## Configuration

The API base URL defaults to `http://127.0.0.1:8000`. Override it with a
`.env` file in `dashboard/`:

```
VITE_API_URL=http://127.0.0.1:8000
```

## What you'll see

- **Mock AA consent flow** (opening move) — link accounts → purpose → OTP →
  consent granted → data fetch. Badged *“Simulated AA flow — DPDP-compliant,
  consent-first.”* Calls the mock `/aa/consent` + `/aa/fetch` endpoints.
- **Lead queue** — grouped Gold / Silver / Bronze, sortable, with a
  *Show suppressed* toggle (leads hidden by the uplift model) and a
  *★ Demo: Priya* jump button.
- **Lead detail card** — conversion %, best time to call, the declared→inferred
  income gap, top-3 reason codes, and the pre-approved offer with a mock
  *Extend offer* (over OCEN) action.
- **Portfolio** — leads by tier, product mix, and the uplift-decile chart.
- **Fairness badge** — reads `/fairness` (disparate-impact ratio vs the 80% rule).

## Build

```bash
npm run build      # outputs to dashboard/dist/
npm run preview    # serve the production build
```
