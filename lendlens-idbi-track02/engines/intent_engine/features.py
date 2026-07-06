"""
Engine B — intent feature engineering (Part 4).

Assembles behavioural + life-event features from behaviour.csv, RECENCY-WEIGHTED
so stale signals fade: a page visit 60 days ago should count for far less than
one yesterday. The weight is exp(-days_since_last_visit / 30), i.e. a ~30-day
half-life on engagement.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RAW_INTENT = ["home_loan_page_visits", "auto_loan_page_visits",
              "personal_loan_page_visits", "emi_calculator_uses"]

LIFE_EVENT_FLAGS = ["rising_rent_flag", "lease_renewal_flag", "car_servicing_flag",
                    "high_cost_emi_flag", "salary_hike_flag"]


def build_intent_features(behaviour: pd.DataFrame,
                          income: pd.DataFrame | None = None
                          ) -> tuple[pd.DataFrame, list[str]]:
    """Return (df, feature_cols). df carries recency-weighted intent signals plus
    the raw life-event flags used by both the propensity and uplift models.

    If `income` (Engine A's income_scores) is supplied, a little affordability
    CONTEXT is added — you don't take a loan you can't service, so this lifts
    propensity quality. In the uplift T-learner it cancels in the treated-minus-
    control difference, so it cannot manufacture fake uplift.
    """
    df = behaviour.copy()
    df["recency_weight"] = np.exp(-df["days_since_last_visit"] / 30.0)

    rw_cols = []
    for c in RAW_INTENT:
        rw = f"{c}_rw"
        df[rw] = df[c] * df["recency_weight"]
        rw_cols.append(rw)
    df["total_intent_rw"] = df[rw_cols].sum(axis=1)

    feature_cols = (rw_cols
                    + ["total_intent_rw", "recency_weight",
                       "app_sessions_30d", "days_since_last_visit"]
                    + LIFE_EVENT_FLAGS)

    if income is not None:
        ctx = income[["customer_id", "estimated_income",
                      "max_affordable_emi", "foir"]].copy()
        ctx["log_estimated_income"] = np.log1p(ctx["estimated_income"])
        df = df.merge(ctx[["customer_id", "log_estimated_income",
                           "max_affordable_emi", "foir"]],
                      on="customer_id", how="left")
        ctx_cols = ["log_estimated_income", "max_affordable_emi", "foir"]
        df[ctx_cols] = df[ctx_cols].fillna(0.0)
        feature_cols += ctx_cols

    return df, feature_cols


if __name__ == "__main__":
    import config
    beh = pd.read_csv(config.BEHAVIOUR_CSV)
    df, feats = build_intent_features(beh)
    print(f"intent features ({len(feats)}): {feats}")
    print(df[["customer_id", "recency_weight", "total_intent_rw"]].head())
