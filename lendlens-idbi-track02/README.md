# LendLens — Consent-First Pre-Approved Offer Engine

**IDBI Innovate 2026 · Track 02 (Lead Generation / Behavioural Analytics / Retail Lending) · Round-1 Prototype**

> LendLens ingests **consented** transaction + behavioural data, runs two engines
> (**Income & Repayment Capacity** and **Intent & Propensity**), passes every
> decision through a **SHAP explainability + fairness gate**, and hands the
> Relationship Manager a ranked list of **pre-approved loan offers** — each with a
> plain-English reason, a predicted conversion probability, the best time to call,
> and the offer amount + EMI.

This is a **concept + demo**, not a production system. It runs **end-to-end with
zero external dependencies** — no Kaggle download, no network, no API keys.

> ⚠️ **Mocked in this Round-1 prototype:** the Account Aggregator (AA) consent
> flow, ULI/OCEN interfaces, and core-banking integration are **simulated** and
> clearly labelled as such in both code and UI. No real AA, bank APIs, auth,
> credit-bureau, or fraud-detection calls are made. Fraud detection is
> deliberately **out of scope** (it belongs downstream as a KYC gate).

---

## Quick start

Requires **Python 3.11+** (built & verified on 3.12) and **Node 18+**.

```bash
# 1. Python environment
python -m venv .venv
# Windows:  .venv\Scripts\activate       POSIX: source .venv/bin/activate
pip install -r requirements.txt

# 2. Run the whole pipeline (generates data -> trains -> explains -> scores)
python run_all.py          # or:  make all
#   -> writes data/processed/leads.json

# 3. Serve the API
uvicorn api.main:app --reload      # or:  make api
#   -> GET http://127.0.0.1:8000/leads

# 4. Run the RM dashboard
cd dashboard && npm install && npm run dev
```

The full pipeline is **deterministic** (`RANDOM_STATE = 42`) — the same run
produces the same leads every time.

---

## Repository layout

```
lendlens-idbi-track02/
├── config.py                 # seed, FOIR cap, fairness threshold, all paths
├── run_all.py / Makefile     # one-command pipeline
├── data/
│   ├── raw/                  # optional Home Credit application_train.csv
│   ├── synthetic/            # generate.py + generated CSVs
│   └── processed/            # every stage output lands here
├── engines/
│   ├── income_engine/        # Engine A — income inference + affordability
│   └── intent_engine/        # Engine B — propensity + uplift + product match
├── explainability/           # SHAP reason codes + fairness (80% rule)
├── decisioning/              # lead tiers + pre-approved offer engine
├── api/                      # FastAPI + AA/ULI/OCEN mock stubs
├── dashboard/                # React + Vite + Tailwind RM console
└── docs/                     # architecture, fairness report, uplift curve
```

---

## Guard-rails (hard-coded & visible — see `config.py`)

| Guard-rail | Value | Where |
|---|---|---|
| FOIR cap | **50%** | affordability / max EMI |
| Fairness disparate-impact | **80% rule** | fairness gate |
| Uplift suppression | leads below cutoff hidden | decisioning |
| Random seed | **42** | everywhere |

_A full README (architecture diagram, screenshots, honest metric framing,
compliance notes, Round-2 plan) is completed in Part 10._
