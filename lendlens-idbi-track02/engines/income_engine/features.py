"""
Engine A — affordability feature engineering (Part 3).

Turns the customer master + inferred income + transaction aggregates into the
feature matrix for the default/affordability model, and the affordability meta
fields the decisioning layer needs (FOIR, disposable income, etc.).

If the Home Credit path supplied real EXT_SOURCE_* credit-behaviour columns,
they are included automatically.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config

EMPLOYMENT_CODE = {"salaried": 0, "self_employed": 1, "gig": 2}

# Model feature columns (extended with ext_source_* when present).
BASE_FEATURES = [
    "log_estimated_income",
    "foir",
    "expense_ratio",
    "disposable_income",
    "income_stability",
    "income_confidence",
    "credit_bureau_score",
    "age",
    "employment_code",
    "city_tier",
    "avg_monthly_credit",
    "income_months",
]


def _transaction_aggregates(tx: pd.DataFrame, n_months: int) -> pd.DataFrame:
    debits = (tx[tx["direction"] == "debit"].groupby("customer_id")["amount"]
              .sum().rename("total_debit"))
    credits = (tx[tx["direction"] == "credit"].groupby("customer_id")["amount"]
               .sum().rename("total_credit"))
    agg = pd.concat([debits, credits], axis=1).fillna(0.0)
    agg["avg_monthly_debit"] = agg["total_debit"] / n_months
    agg["avg_monthly_credit"] = agg["total_credit"] / n_months
    return agg.reset_index()


def build_features(customers: pd.DataFrame, tx: pd.DataFrame,
                   estimates: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Return (df, feature_cols). `df` carries the model features, the target
    (`defaulted`), and affordability meta columns used downstream."""
    n_months = config.TRANSACTION_MONTHS
    agg = _transaction_aggregates(tx, n_months)

    df = (customers.merge(estimates, on="customer_id", how="left")
          .merge(agg, on="customer_id", how="left"))
    df[["avg_monthly_debit", "avg_monthly_credit"]] = \
        df[["avg_monthly_debit", "avg_monthly_credit"]].fillna(0.0)

    inc = df["estimated_income"].clip(lower=1)  # guard div-by-zero
    df["log_estimated_income"] = np.log1p(df["estimated_income"])
    df["foir"] = (df["existing_emi"] / inc).clip(0, 5).round(4)
    df["expense_ratio"] = (df["avg_monthly_debit"] / inc).clip(0, 5).round(4)
    df["disposable_income"] = (df["estimated_income"] - df["avg_monthly_debit"]).round()
    df["employment_code"] = df["employment_type"].map(EMPLOYMENT_CODE).astype(int)

    features = list(BASE_FEATURES)
    ext_cols = [c for c in df.columns if c.startswith("ext_source")]
    features += ext_cols  # real Home Credit credit-behaviour features, if present

    # Every model feature must be finite.
    df[features] = df[features].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return df, features


if __name__ == "__main__":
    # Smoke test: build features and show the matrix shape + a few rows.
    from engines.income_engine import income_inference
    customers = pd.read_csv(config.CUSTOMERS_CSV)
    tx = pd.read_csv(config.TRANSACTIONS_CSV)
    estimates = income_inference.estimate_income(customers, tx)
    df, feats = build_features(customers, tx, estimates)
    print(f"features: {feats}")
    print(f"matrix  : {df[feats].shape}")
    print(df[["customer_id", "estimated_income", "foir", "disposable_income"]].head())
