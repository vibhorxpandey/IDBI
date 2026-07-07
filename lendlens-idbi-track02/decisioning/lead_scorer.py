"""
Decisioning — lead scoring & tiering (Part 6).

Joins Engine A (income_scores), Engine B (intent_scores), the SHAP reason codes,
and the customer master into one ranked, tiered lead list. Writes
data/processed/leads_scored.json (no offers yet — offer_engine.py adds those).

Guard-rails (Global Rule 6):
* SUPPRESS a lead if it can't afford anything (max_affordable_emi <= 0) or the
  uplift model says outreach won't move it (uplift < UPLIFT_SUPPRESSION_CUTOFF)
  — don't waste RM time even if raw propensity looks high.
* GOLD = affordable + positive uplift + (top-decile conversion OR top-decile
  uplift). SILVER / BRONZE split the rest of the eligible pool by composite.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import config

TIER_RANK = {"GOLD": 0, "SILVER": 1, "BRONZE": 2, "SUPPRESSED": 3}


def _composite(df: pd.DataFrame) -> pd.Series:
    """Blended 0-1 lead-quality score for ranking within the eligible pool."""
    conv = df["conversion_prob"].clip(0, 1)
    upl = (df["uplift_score"] / 0.30).clip(0, 1)            # 0.30 ~ very high uplift
    afford = (df["max_affordable_emi"] / 40000).clip(0, 1)  # 40k EMI ~ strong capacity
    risk = df["default_risk"].clip(0, 1)
    return (0.35 * conv + 0.40 * upl + 0.25 * afford - 0.10 * risk).clip(0, 1)


def score_leads() -> pd.DataFrame:
    customers = pd.read_csv(config.CUSTOMERS_CSV)
    income = pd.read_json(config.INCOME_SCORES_JSON)
    intent = pd.read_json(config.INTENT_SCORES_JSON)
    with open(config.REASON_CODES_JSON, encoding="utf-8") as fh:
        reasons = json.load(fh)

    df = (customers[["customer_id", "name", "city", "age", "gender"]]
          .merge(income, on="customer_id")
          .merge(intent, on="customer_id"))
    df["reason_codes"] = df["customer_id"].map(reasons)

    # --- suppression gates ---
    df["eligible"] = ((df["max_affordable_emi"] > 0)
                      & (df["uplift_score"] >= config.UPLIFT_SUPPRESSION_CUTOFF))
    df["composite"] = _composite(df)

    elig = df[df["eligible"]]
    conv_p90 = elig["conversion_prob"].quantile(0.90)
    uplift_p90 = elig["uplift_score"].quantile(0.90)
    composite_med = elig["composite"].median()

    def _tier(r) -> str:
        if not r.eligible:
            return "SUPPRESSED"
        top_conv = r.conversion_prob >= conv_p90
        top_uplift = r.uplift_score >= uplift_p90
        if r.uplift_score >= config.TIER_GOLD_UPLIFT and (top_conv or top_uplift):
            return "GOLD"
        if r.composite >= composite_med:
            return "SILVER"
        return "BRONZE"

    df["tier"] = df.apply(_tier, axis=1)
    df["tier_rank"] = df["tier"].map(TIER_RANK)

    df = df.sort_values(["tier_rank", "composite"],
                        ascending=[True, False]).reset_index(drop=True)
    df["rank"] = np.arange(1, len(df) + 1)
    return df


def main() -> None:
    df = score_leads()

    records = []
    for r in df.itertuples(index=False):
        records.append({
            "rank": int(r.rank),
            "customer_id": r.customer_id,
            "name": r.name,
            "city": r.city,
            "age": int(r.age),
            "gender": r.gender,
            "tier": r.tier,
            "suggested_product": r.suggested_product,
            "conversion_prob": round(float(r.conversion_prob), 4),
            "uplift_score": round(float(r.uplift_score), 4),
            "composite_score": round(float(r.composite), 4),
            "best_time_to_contact": r.best_time_to_contact,
            "declared_income": int(r.declared_income),
            "estimated_income": int(r.estimated_income),
            "max_affordable_emi": int(r.max_affordable_emi),
            "existing_emi": int(r.existing_emi),
            "default_risk": round(float(r.default_risk), 4),
            "income_confidence": round(float(r.income_confidence), 3),
            "reason_codes": list(r.reason_codes),
        })

    config.ensure_dirs()
    with open(config.LEADS_SCORED_JSON, "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)

    counts = df["tier"].value_counts()
    print("=" * 64)
    print(" Decisioning — leads scored & tiered")
    print("=" * 64)
    for tier in ["GOLD", "SILVER", "BRONZE", "SUPPRESSED"]:
        c = int(counts.get(tier, 0))
        print(f"  {tier:<11}: {c:>5,}  ({c/len(df):.0%})")
    surfaced = df[df["tier"] != "SUPPRESSED"]
    print(f"  surfaced leads          : {len(surfaced):,}")
    print(f"  suppressed (low uplift / not affordable): {int(counts.get('SUPPRESSED', 0)):,}")
    print("  GOLD product mix        : " +
          ", ".join(f"{k} {v}" for k, v in
                    df[df.tier == 'GOLD']['suggested_product'].value_counts().items()))
    print(f"  output                  : {config.LEADS_SCORED_JSON.name}")
    print("=" * 64)


if __name__ == "__main__":
    main()
