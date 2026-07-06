"""
Engine B — inference (Part 4).

Scores every customer for conversion propensity and uplift, matches a loan
product from their life-events, derives the best time to contact from their peak
transaction-activity hour, and writes data/processed/intent_scores.json.
"""
from __future__ import annotations

import json
import pickle

import numpy as np
import pandas as pd

import config
from engines.intent_engine import features as intent_feat

# life-event / intent -> product mapping (Part 4)
#   Home     : home page visits, rising rent, lease renewal
#   Auto     : auto page visits, car servicing
#   Personal : personal page visits, high-cost EMI (consolidation)
#   Mortgage : larger secured need (high affordability, no specific retail intent)


def _time_band(hour: float) -> str:
    if hour < 11:
        return "Morning · 9–11 AM"
    if hour < 14:
        return "Midday · 12–2 PM"
    if hour < 17:
        return "Afternoon · 3–5 PM"
    if hour < 20:
        return "Evening · 6–8 PM"
    return "Night · 8–10 PM"


def _peak_hours(tx: pd.DataFrame) -> pd.Series:
    """Mean transaction hour per customer -> their peak activity time."""
    hours = pd.to_datetime(tx["date"], errors="coerce").dt.hour
    return hours.groupby(tx["customer_id"]).mean()


def suggest_product(row, max_affordable_emi: float, afford_threshold: float) -> str:
    scores = {
        "Home": 2 * row.home_loan_page_visits + 1.5 * row.rising_rent_flag
        + 1.5 * row.lease_renewal_flag,
        "Auto": 2 * row.auto_loan_page_visits + 1.5 * row.car_servicing_flag,
        "Personal": 2 * row.personal_loan_page_visits + 1.5 * row.high_cost_emi_flag,
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        # No explicit retail intent -> secured cross-sell if the affordability is
        # large, otherwise a generic personal loan.
        return "Mortgage" if max_affordable_emi >= afford_threshold else "Personal"
    return best


def main() -> None:
    beh = pd.read_csv(config.BEHAVIOUR_CSV)
    tx = pd.read_csv(config.TRANSACTIONS_CSV)
    income = pd.read_json(config.INCOME_SCORES_JSON)

    df, _ = intent_feat.build_intent_features(beh, income)

    with open(config.INTENT_PROPENSITY_PKL, "rb") as fh:
        prop_bundle = pickle.load(fh)
    with open(config.INTENT_UPLIFT_PKL, "rb") as fh:
        up_bundle = pickle.load(fh)

    model_feats = prop_bundle["features"]  # identical for both models
    conversion_prob = prop_bundle["model"].predict_proba(df[model_feats])[:, 1]
    uplift_score = up_bundle["model"].predict(df[model_feats])

    peak = _peak_hours(tx)
    afford = income.set_index("customer_id")["max_affordable_emi"]
    afford_threshold = float(afford.quantile(0.75))

    beh_indexed = beh.set_index("customer_id")
    records = []
    for i, cid in enumerate(df["customer_id"]):
        max_emi = float(afford.get(cid, 0.0))
        product = suggest_product(beh_indexed.loc[cid], max_emi, afford_threshold)
        peak_hour = float(peak.get(cid, 12.0))
        records.append({
            "customer_id": cid,
            "conversion_prob": round(float(conversion_prob[i]), 4),
            "uplift_score": round(float(uplift_score[i]), 4),
            "suggested_product": product,
            "best_time_to_contact": _time_band(peak_hour),
            "peak_activity_hour": round(peak_hour, 1),
        })
    records.sort(key=lambda d: d["customer_id"])

    config.ensure_dirs()
    with open(config.INTENT_SCORES_JSON, "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)

    prod_counts = pd.Series([r["suggested_product"] for r in records]).value_counts()
    n_missing_prod = sum(1 for r in records if not r["suggested_product"])
    print("\n" + "=" * 64)
    print(" Engine B — intent_scores.json written")
    print("=" * 64)
    print(f"  customers scored          : {len(records):,}")
    print(f"  missing product / time    : {n_missing_prod} / "
          f"{sum(1 for r in records if not r['best_time_to_contact'])}")
    print(f"  mean conversion_prob      : {np.mean(conversion_prob):.1%}")
    print(f"  positive-uplift customers : {(uplift_score > 0).mean():.1%}")
    print("  suggested product mix     :")
    for p, c in prod_counts.items():
        print(f"    {p:<9}: {c:>5,} ({c/len(records):.0%})")
    print("  best-time distribution    :")
    for b, c in pd.Series([r["best_time_to_contact"] for r in records]).value_counts().items():
        print(f"    {b:<16}: {c:>5,}")
    print(f"  output                    : {config.INTENT_SCORES_JSON}")
    print("=" * 64)


if __name__ == "__main__":
    main()
