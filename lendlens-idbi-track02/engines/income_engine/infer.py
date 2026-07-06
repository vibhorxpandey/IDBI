"""
Engine A — inference (Part 3).

Loads the trained model, scores every customer, and writes
data/processed/income_scores.json — one record per customer with the inferred
income, affordability guard-rails, and default risk. Also prints the honest
income-inference validation.

max_affordable_emi = estimated_income * FOIR_CAP - existing_emi, floored at 0
(Global Rule 6 — the 50% FOIR cap is applied here and never exceeded).
"""
from __future__ import annotations

import json
import pickle

import numpy as np
import pandas as pd

import config
from engines.income_engine import features as feat
from engines.income_engine import income_inference


def main() -> None:
    customers = pd.read_csv(config.CUSTOMERS_CSV)
    tx = pd.read_csv(config.TRANSACTIONS_CSV)

    estimates = income_inference.estimate_income(customers, tx)

    # Honest synthetic validation of the income inference.
    if config.INCOME_GROUND_TRUTH_CSV.exists():
        gt = pd.read_csv(config.INCOME_GROUND_TRUTH_CSV)
        income_inference.validate(estimates, customers, gt)

    df, feature_cols = feat.build_features(customers, tx, estimates)

    with open(config.INCOME_MODEL_PKL, "rb") as fh:
        bundle = pickle.load(fh)
    model, model_feats = bundle["model"], bundle["features"]
    df["default_risk"] = model.predict_proba(df[model_feats])[:, 1]

    # Affordability guard-rail: FOIR cap applied, EMI headroom floored at 0.
    df["max_affordable_emi"] = np.clip(
        df["estimated_income"] * config.FOIR_CAP - df["existing_emi"], 0, None)

    records = []
    for r in df.itertuples(index=False):
        records.append({
            "customer_id": r.customer_id,
            "declared_income": int(r.declared_income),
            "estimated_income": int(r.estimated_income),
            "existing_emi": int(r.existing_emi),
            "foir": round(float(r.foir), 3),
            "disposable_income": int(r.disposable_income),
            "max_affordable_emi": int(round(r.max_affordable_emi)),
            "default_risk": round(float(r.default_risk), 4),
            "income_confidence": round(float(r.income_confidence), 3),
            "income_stability": round(float(r.income_stability), 3),
            "income_method": r.income_method,
        })
    records.sort(key=lambda d: d["customer_id"])

    config.ensure_dirs()
    with open(config.INCOME_SCORES_JSON, "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)

    neg = sum(1 for r in records if r["max_affordable_emi"] < 0)
    print("\n" + "=" * 64)
    print(" Engine A — income_scores.json written")
    print("=" * 64)
    print(f"  customers scored         : {len(records):,}")
    print(f"  negative max_affordable_emi (must be 0): {neg}")
    print(f"  median inferred income   : ₹{int(df['estimated_income'].median()):,}")
    print(f"  median max affordable EMI: ₹{int(df['max_affordable_emi'].median()):,}")
    print(f"  mean default risk        : {df['default_risk'].mean():.1%}")
    print(f"  output                   : {config.INCOME_SCORES_JSON}")
    print("=" * 64)


if __name__ == "__main__":
    main()
