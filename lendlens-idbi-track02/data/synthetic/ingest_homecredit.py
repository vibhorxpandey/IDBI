"""
LendLens — optional Home Credit ingestion (Part 2).

OPTIONAL ENRICHMENT — never required (Global Rule 1). If the Kaggle Home Credit
Default Risk file `data/raw/application_train.csv` is present, we build the
customer master from its REAL columns instead of the synthetic one. The pipeline
auto-detects this (`is_available()`), prefers it, and otherwise falls back to
fully synthetic. The synthetic transaction / behaviour / treatment tables are
always used and joined by customer index.

Column mapping (Home Credit -> LendLens master):
    AMT_INCOME_TOTAL / 12   -> declared_income  (and true_income; HC has no
                               declared-vs-true gap, so they coincide here)
    AMT_ANNUITY     / 12    -> existing_emi
    EXT_SOURCE_1/2/3        -> ext_source_1/2/3  (real credit-behaviour features
                               carried through to Engine A, Part 3)
    EXT_SOURCE_2 (0..1)     -> credit_bureau_score rescaled to 300..900
    CODE_GENDER            -> gender
    NAME_INCOME_TYPE       -> employment_type (coarse mapping)
    TARGET                 -> defaulted
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config

# Kept in sync with build_master() so downstream stages see one stable schema.
_BANKS = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "IDBI"]


def is_available() -> bool:
    """True if the optional Home Credit CSV is present on disk."""
    return config.RAW_HOMECREDIT_CSV.exists()


def load_master(n: int) -> pd.DataFrame:
    """Build a LendLens customer master from the first `n` Home Credit rows.

    Returns the SAME schema as data.synthetic.generate.build_master (public
    columns + hidden `true_income` + rng-fixed helpers), plus real
    ext_source_1/2/3 columns for Engine A.
    """
    rng = np.random.default_rng(config.RANDOM_STATE)
    raw = pd.read_csv(config.RAW_HOMECREDIT_CSV, nrows=n).reset_index(drop=True)
    m = len(raw)

    def col(name, default=np.nan):
        return raw[name] if name in raw.columns else pd.Series([default] * m)

    monthly_income = (col("AMT_INCOME_TOTAL").astype(float) / 12.0)
    monthly_income = monthly_income.fillna(monthly_income.median()).clip(12000, 800000)
    monthly_income = (monthly_income / 500).round() * 500

    annuity = (col("AMT_ANNUITY").astype(float) / 12.0).fillna(0).clip(lower=0)
    existing_emi = (annuity / 500).round() * 500

    ext2 = col("EXT_SOURCE_2").astype(float)
    ext2 = ext2.fillna(ext2.median() if ext2.notna().any() else 0.5)
    credit_bureau_score = np.clip((300 + 600 * ext2).round(), 300, 900).astype(int)

    gender = col("CODE_GENDER").replace({"XNA": "F"}).fillna("F")
    gender = gender.where(gender.isin(["M", "F"]), "F")

    income_type = col("NAME_INCOME_TYPE", "Working").fillna("Working")
    employment_type = np.where(
        income_type.isin(["Commercial associate", "Businessman", "Self-employed"]),
        "self_employed",
        np.where(income_type.eq("Pensioner"), "gig", "salaried"))

    age = (-col("DAYS_BIRTH").astype(float) / 365.0)
    age = age.fillna(38).clip(21, 70).round().astype(int)

    companies = [f"EMPLOYER{i:03d}" for i in range(240)]
    employer = np.array([companies[i] for i in rng.integers(0, len(companies), m)])

    master = pd.DataFrame({
        "customer_id": [f"CUST_{i:05d}" for i in range(1, m + 1)],
        "age": age.values,
        "gender": gender.values,
        "employment_type": employment_type,
        "city_tier": rng.choice([1, 2, 3], size=m, p=[0.40, 0.35, 0.25]),
        "declared_income": monthly_income.astype(int).values,
        "existing_emi": existing_emi.astype(int).values,
        "credit_bureau_score": credit_bureau_score,
        "defaulted": col("TARGET").fillna(0).astype(int).values,
        # HC has no hidden-income concept -> true == declared here
        "true_income": monthly_income.astype(int).values,
        "employer": employer,
        "salary_day": rng.integers(1, 4, m),
        "emi_bank": np.array([_BANKS[i] for i in rng.integers(0, len(_BANKS), m)]),
        # real credit-behaviour features for Engine A (Part 3)
        "ext_source_1": col("EXT_SOURCE_1").astype(float).fillna(0.5).values,
        "ext_source_2": ext2.values,
        "ext_source_3": col("EXT_SOURCE_3").astype(float).fillna(0.5).values,
    })
    return master
