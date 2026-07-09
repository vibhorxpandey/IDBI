"""
LendLens — central configuration.

Single source of truth for the random seed, prudent-lending guard-rails,
product parameters, and every file path in the pipeline. Each stage imports
from here so the demo is (a) deterministic and (b) has its policy thresholds
visible in one place.

Run `python config.py` to print the active configuration.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Windows consoles default to cp1252, which cannot encode the rupee sign (₹)
# used throughout LendLens. Force UTF-8 on the console for every stage (they
# all import config), so prints never crash. File I/O always uses UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

# ---------------------------------------------------------------------------
# Determinism (Global Rule 2)
# ---------------------------------------------------------------------------
RANDOM_STATE = 42            # fixed seed everywhere -> identical leads each run

# ---------------------------------------------------------------------------
# Synthetic dataset size (Part 2)
# ---------------------------------------------------------------------------
N_CUSTOMERS = 5_000
TRANSACTION_MONTHS = 6       # months of transaction history per customer

# ---------------------------------------------------------------------------
# Prudent-lending guard-rails — hard-coded & visible (Global Rule 6)
# ---------------------------------------------------------------------------
FOIR_CAP = 0.50              # Fixed-Obligation-to-Income Ratio cap = 50%
DISPARATE_IMPACT_MIN = 0.80  # fairness "80% rule" minimum acceptable ratio
UPLIFT_SUPPRESSION_CUTOFF = 0.02  # suppress leads whose uplift score < this

# ---------------------------------------------------------------------------
# Tiering thresholds (Part 6 decisioning) — tuned there, centralised here
# ---------------------------------------------------------------------------
TIER_GOLD_CONVERSION = 0.55    # Gold needs strong conversion probability
TIER_SILVER_CONVERSION = 0.30  # Silver floor
TIER_GOLD_UPLIFT = 0.05        # Gold needs clearly positive uplift

# ---------------------------------------------------------------------------
# Loan product parameters (Part 6 offer engine)
#   rate         = indicative annual interest rate
#   tenor_years  = default tenor for the pre-approved offer
#   max_amount   = product ceiling (INR) so offers stay realistic
# ---------------------------------------------------------------------------
# rate = indicative annual interest; tenor_years = default offer tenor;
# max_amount = product ceiling (INR); income_multiple = conservative pre-approved
# starting offer expressed as a multiple of verified ANNUAL income (Part 6/9).
PRODUCTS = {
    "Home":     {"rate": 0.085, "tenor_years": 20, "max_amount": 5_00_00_000, "income_multiple": 1.10},
    "Auto":     {"rate": 0.095, "tenor_years": 7,  "max_amount":   25_00_000, "income_multiple": 0.60},
    "Personal": {"rate": 0.130, "tenor_years": 5,  "max_amount":   40_00_000, "income_multiple": 0.50},
    "Mortgage": {"rate": 0.090, "tenor_years": 15, "max_amount": 3_00_00_000, "income_multiple": 1.50},
}

# The pre-approved *headline* offer is intentionally conservative: the LOWER of
# (a) what the FOIR-capped max affordable EMI supports, and (b) a modest multiple
# of verified annual income (income_multiple above), also within the product cap.
# Full affordability is unlocked only after underwriting — this keeps the
# pre-approved starting number credible (and lands Priya's home loan near ₹18L).

# ---------------------------------------------------------------------------
# Canonical demo persona (Part 9)
# ---------------------------------------------------------------------------
PRIYA_ID = "CUST_PRIYA"

# ---------------------------------------------------------------------------
# Paths — all stage outputs land in data/processed/ (Global Rule 7)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
# Overridable so the deployed API can read JSON bundled at a different path
# (e.g. on Vercel — see api/index.py).
PROCESSED_DIR = Path(os.environ.get("LENDLENS_PROCESSED_DIR", str(DATA_DIR / "processed")))
DOCS_DIR = BASE_DIR / "docs"

# Optional Home Credit enrichment (Global Rule 1) — used only if present
RAW_HOMECREDIT_CSV = RAW_DIR / "application_train.csv"

# Synthetic generator outputs (Part 2)
CUSTOMERS_CSV = SYNTHETIC_DIR / "customers.csv"
TRANSACTIONS_CSV = SYNTHETIC_DIR / "transactions.csv"
BEHAVIOUR_CSV = SYNTHETIC_DIR / "behaviour.csv"
TREATMENT_CSV = SYNTHETIC_DIR / "treatment.csv"
INCOME_GROUND_TRUTH_CSV = SYNTHETIC_DIR / "income_ground_truth.csv"

# Model artefacts
INCOME_MODEL_PKL = BASE_DIR / "engines" / "income_engine" / "model.pkl"
INTENT_PROPENSITY_PKL = BASE_DIR / "engines" / "intent_engine" / "propensity.pkl"
INTENT_UPLIFT_PKL = BASE_DIR / "engines" / "intent_engine" / "uplift.pkl"
# Plain (uncalibrated) XGB on P(convert|contacted), saved purely so SHAP
# TreeExplainer has a clean tree model for Engine B reason codes (Part 5).
INTENT_EXPLAINER_PKL = BASE_DIR / "engines" / "intent_engine" / "intent_explainer.pkl"

# Stage outputs (Global Rule 7 — each stage writes, next stage reads)
INCOME_SCORES_JSON = PROCESSED_DIR / "income_scores.json"
INTENT_SCORES_JSON = PROCESSED_DIR / "intent_scores.json"
REASON_CODES_JSON = PROCESSED_DIR / "reason_codes.json"
FAIRNESS_SUMMARY_JSON = PROCESSED_DIR / "fairness_summary.json"
LEADS_SCORED_JSON = PROCESSED_DIR / "leads_scored.json"  # tiers, pre-offer
LEADS_JSON = PROCESSED_DIR / "leads.json"                # final, with offers

# Docs / charts
UPLIFT_CURVE_PNG = DOCS_DIR / "uplift_curve.png"
UPLIFT_CURVE_JSON = PROCESSED_DIR / "uplift_curve.json"  # decile data for the dashboard
FAIRNESS_REPORT_MD = DOCS_DIR / "fairness_report.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_OUTPUT_DIRS = [RAW_DIR, SYNTHETIC_DIR, PROCESSED_DIR, DOCS_DIR]


def ensure_dirs() -> None:
    """Create every output directory if missing. Safe to call repeatedly."""
    for d in _OUTPUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)


def _inr(amount: float) -> str:
    """Format an INR amount with Indian digit grouping (lakh/crore)."""
    amount = int(round(amount))
    s = str(abs(amount))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        import re
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = f"{head},{tail}"
    return ("-" if amount < 0 else "") + "₹" + s


if __name__ == "__main__":
    ensure_dirs()
    print("=" * 60)
    print(" LendLens configuration")
    print("=" * 60)
    print(f"  RANDOM_STATE              : {RANDOM_STATE}")
    print(f"  N_CUSTOMERS               : {N_CUSTOMERS:,}")
    print(f"  TRANSACTION_MONTHS        : {TRANSACTION_MONTHS}")
    print("-" * 60)
    print(" Prudent-lending guard-rails")
    print(f"  FOIR_CAP                  : {FOIR_CAP:.0%}")
    print(f"  DISPARATE_IMPACT_MIN      : {DISPARATE_IMPACT_MIN:.0%} (80% rule)")
    print(f"  UPLIFT_SUPPRESSION_CUTOFF : {UPLIFT_SUPPRESSION_CUTOFF}")
    print("-" * 60)
    print(" Tier thresholds")
    print(f"  Gold conversion  >= {TIER_GOLD_CONVERSION:.0%}   uplift >= {TIER_GOLD_UPLIFT}")
    print(f"  Silver conversion>= {TIER_SILVER_CONVERSION:.0%}")
    print("-" * 60)
    print(" Loan products")
    for name, p in PRODUCTS.items():
        print(f"  {name:<9}: {p['rate']:.2%}  {p['tenor_years']:>2}y  "
              f"cap {_inr(p['max_amount'])}  pre-appr {p['income_multiple']:.2f}× annual income")
    print("-" * 60)
    print(" Paths")
    print(f"  BASE_DIR       : {BASE_DIR}")
    print(f"  SYNTHETIC_DIR  : {SYNTHETIC_DIR}")
    print(f"  PROCESSED_DIR  : {PROCESSED_DIR}")
    print(f"  Home Credit    : {'FOUND' if RAW_HOMECREDIT_CSV.exists() else 'not present (using synthetic)'}")
    print("=" * 60)
    print("config OK")
