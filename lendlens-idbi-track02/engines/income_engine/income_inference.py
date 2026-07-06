"""
Engine A — income inference (Part 3).

Recovers a customer's REAL monthly income from their transaction ledger alone,
using rule + pattern logic. It NEVER reads income_ground_truth.csv for the
estimate — ground truth is used only at the end to honestly report accuracy on
this synthetic data (Global Rule 7).

Method
------
1. Keep credits; drop non-income credits by narration keyword (P2P transfers,
   refunds/reversals, one-off loan disbursals, cashbacks) — the kind of tagging
   a real core-banking narration parser does.
2. If the customer receives labelled SALARY credits -> income is the recurring
   salary: the median of monthly salary totals (robust to a mid-year hike).
3. Otherwise (self-employed / gig) -> income is the recurring net business
   inflow: the median of monthly inflow totals (robust to lumpy months and to
   any noise that slipped through).
4. Confidence rises with month-coverage, inflow stability (low variability), and
   label clarity (a labelled salary is clearer than diffuse business inflows).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config

# Credits whose narration matches any of these are NOT income.
NOISE_KEYWORDS = ["P2P", "REFUND", "REVERSAL", "LOANDISB", "CASHBACK", "REDEMPTION"]
_NOISE_RE = "|".join(NOISE_KEYWORDS)


def _per_customer_stats(monthly: pd.DataFrame) -> pd.DataFrame:
    """Given per-(customer, month) inflow totals, return robust per-customer
    estimate + variability + month coverage."""
    grp = monthly.groupby("customer_id")["amount"]
    stats = pd.DataFrame({
        "estimate": grp.median(),
        "mean": grp.mean(),
        "std": grp.std().fillna(0.0),
        "months": grp.size(),
    })
    return stats


def estimate_income(customers: pd.DataFrame, tx: pd.DataFrame) -> pd.DataFrame:
    """Estimate monthly income per customer from transactions only.

    Returns a DataFrame with columns: customer_id, estimated_income,
    income_confidence, income_stability, income_months, income_method.
    """
    credits = tx[tx["direction"] == "credit"].copy()
    up = credits["narration"].str.upper()
    credits = credits[~up.str.contains(_NOISE_RE, regex=True, na=False)].copy()
    credits["ym"] = pd.to_datetime(credits["date"]).dt.to_period("M").astype(str)
    credits["is_salary"] = credits["narration"].str.upper().str.contains(
        "SALARY", na=False)

    salary_monthly = (credits[credits["is_salary"]]
                      .groupby(["customer_id", "ym"])["amount"].sum().reset_index())
    all_monthly = (credits.groupby(["customer_id", "ym"])["amount"].sum()
                   .reset_index())

    salary_stats = _per_customer_stats(salary_monthly)
    all_stats = _per_customer_stats(all_monthly)

    rows = []
    salary_ids = set(salary_stats.index)
    for cid in customers["customer_id"]:
        if cid in salary_ids:
            s = salary_stats.loc[cid]
            method, label_clarity = "recurring_salary", 1.0
        elif cid in all_stats.index:
            s = all_stats.loc[cid]
            method, label_clarity = "recurring_business_inflow", 0.7
        else:
            # No income-like credits at all -> low-confidence fallback.
            declared = customers.loc[customers["customer_id"] == cid,
                                     "declared_income"].iloc[0]
            rows.append((cid, float(declared), 0.30, 0.0, 0, "fallback_declared"))
            continue

        est = float(s["estimate"])
        cv = float(s["std"] / s["mean"]) if s["mean"] > 0 else 0.0
        stability = float(np.clip(1.0 - cv, 0.0, 1.0))
        coverage = float(s["months"]) / config.TRANSACTION_MONTHS
        confidence = float(np.clip(
            coverage * (0.4 + 0.6 * stability) * label_clarity, 0.30, 0.98))
        rows.append((cid, est, confidence, stability, int(s["months"]), method))

    out = pd.DataFrame(rows, columns=[
        "customer_id", "estimated_income", "income_confidence",
        "income_stability", "income_months", "income_method"])
    out["estimated_income"] = (out["estimated_income"] / 100).round() * 100
    return out


def validate(estimates: pd.DataFrame, customers: pd.DataFrame,
             ground_truth: pd.DataFrame) -> dict:
    """Honest synthetic-validation of inferred income vs the hidden true income."""
    m = (estimates.merge(ground_truth, on="customer_id")
         .merge(customers[["customer_id", "employment_type", "declared_income"]],
                on="customer_id"))
    m["abs_pct_err"] = (m["estimated_income"] - m["true_income"]).abs() / m["true_income"]
    within_15 = float((m["abs_pct_err"] <= 0.15).mean())

    print("\n" + "-" * 64)
    print(" Income inference — synthetic validation (vs hidden true income)")
    print("-" * 64)
    print(f"  within ±15% of true income : {within_15:.1%} of customers")
    print(f"  median abs. pct error      : {m['abs_pct_err'].median():.1%}")
    print(f"  mean abs. pct error (MAPE) : {m['abs_pct_err'].mean():.1%}")
    print("  by employment type (within ±15%):")
    for etype, g in m.groupby("employment_type"):
        print(f"    {etype:<14}: {(g['abs_pct_err'] <= 0.15).mean():.1%}"
              f"   (median declared = {g['declared_income'].median():>9,.0f},"
              f"   median inferred = {g['estimated_income'].median():>9,.0f})")
    print("-" * 64)
    return {"within_15pct": within_15,
            "median_ape": float(m["abs_pct_err"].median())}


def main() -> None:
    customers = pd.read_csv(config.CUSTOMERS_CSV)
    tx = pd.read_csv(config.TRANSACTIONS_CSV)
    estimates = estimate_income(customers, tx)
    if config.INCOME_GROUND_TRUTH_CSV.exists():
        gt = pd.read_csv(config.INCOME_GROUND_TRUTH_CSV)
        validate(estimates, customers, gt)
    # Persist an inspectable intermediate (Global Rule 7).
    out_path = config.PROCESSED_DIR / "income_estimates.csv"
    config.ensure_dirs()
    estimates.to_csv(out_path, index=False, encoding="utf-8")
    print(f"income inference OK -> {out_path.name} ({len(estimates):,} customers)")


if __name__ == "__main__":
    main()
