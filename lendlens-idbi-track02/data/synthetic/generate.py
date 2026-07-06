"""
LendLens — synthetic data generator (Part 2).

Produces a realistic, labelled dataset so the WHOLE pipeline runs standalone
with zero external dependencies (Global Rule 1). Every random draw is seeded
(Global Rule 2), so re-running yields byte-identical CSVs.

Outputs (data/synthetic/):
    customers.csv            customer master (public columns only)
    transactions.csv         6 months of transactions per customer
    behaviour.csv            behavioural / intent signals + life-event flags
    treatment.csv            randomised contact + conversion outcome (uplift label)
    income_ground_truth.csv  hidden TRUE monthly income — validation only, never
                             a model feature (Global Rule 7 keeps it separate)

Design highlights
-----------------
* Self-employed / gig customers deliberately UNDER-DECLARE income, while their
  transactions carry the real recurring inflows — this is the gap Engine A
  (Part 3) recovers, and the crux of the Priya story (Part 9).
* Behavioural intent + life-event flags are co-generated with the transactions
  that justify them (e.g. a `rising_rent_flag` customer really does have rent
  creeping up month over month), so the flags are consistent with the ledger.
* The treatment/outcome model contains a genuine PERSUADABLE segment (positive
  uplift) alongside sure-things and lost-causes, so the uplift model (Part 4)
  has real heterogeneous treatment effect to learn.

Optional Home Credit enrichment: if data/raw/application_train.csv is present,
the customer master is built from its real columns instead (see
ingest_homecredit.py). The pipeline auto-detects and prefers it; otherwise it
falls back to fully synthetic. The synthetic transaction / behaviour / treatment
tables are always used and joined by customer index.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from faker import Faker

import config
from data.synthetic import ingest_homecredit

# As-of date for the 6-month window (fixed for determinism; near "today").
AS_OF = pd.Timestamp("2026-06-30")

# Reference pools -----------------------------------------------------------
BANKS = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "BAJAJ", "IDBI", "INDUSIND"]
GIG_PLATFORMS = ["SWIGGY", "ZOMATO", "UBER", "OLA", "URBANCO",
                 "AMAZONFLEX", "RAPIDO", "PORTER"]

# (template, brand-options, (lo, hi) base amount) for discretionary debits
DISCRETIONARY = [
    ("POS/FUEL/{}",      ["HPCL", "IOCL", "BPCL", "SHELL"],            (800, 4000)),
    ("POS/GROCERY/{}",   ["DMART", "BIGBAZAAR", "RELIANCEFRESH", "MORE"], (500, 6000)),
    ("UPI/FOOD/{}",      ["SWIGGY", "ZOMATO", "DOMINOS", "KFC"],       (150, 1500)),
    ("POS/SHOPPING/{}",  ["MYNTRA", "AJIO", "LIFESTYLE", "CROMA"],     (500, 12000)),
    ("UPI/P2P TRANSFER", None,                                         (200, 8000)),
    ("ATM/CASH WDL",     None,                                         (1000, 15000)),
    ("UPI/UTILITY/{}",   ["ELECTRICITY", "MOBILE", "DTH", "GAS"],      (300, 4000)),
]
CAR_BRANDS = ["MARUTI", "HYUNDAI", "TATA", "MAHINDRA", "TOYOTA", "HONDA"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _month_periods(as_of: pd.Timestamp, n_months: int) -> list[tuple[int, int]]:
    """Return the n most recent (year, month) pairs ending at as_of, ascending."""
    periods: list[tuple[int, int]] = []
    y, m = as_of.year, as_of.month
    for _ in range(n_months):
        periods.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return list(reversed(periods))


def _clean(name: str, width: int = 18) -> str:
    """ASCII-ish, comma-free, upper-case narration token."""
    return name.upper().replace(",", "").replace(".", "").strip()[:width]


def _build_company_pool(size: int) -> list[str]:
    """A seeded pool of company-like names for employers / business clients."""
    fake = Faker("en_IN")
    Faker.seed(config.RANDOM_STATE)
    return [_clean(fake.company()) for _ in range(size)]


# ---------------------------------------------------------------------------
# 1. Customer master (+ hidden true income & life-event helpers)
# ---------------------------------------------------------------------------
def build_master(n: int) -> pd.DataFrame:
    """Synthetic customer master. Returns a DataFrame that also carries hidden
    helper columns (true_income, life-event flags, rng-fixed dates) used by the
    other generators; only a public subset is written to customers.csv."""
    rng = np.random.default_rng(config.RANDOM_STATE)

    customer_id = [f"CUST_{i:05d}" for i in range(1, n + 1)]
    employment = rng.choice(["salaried", "self_employed", "gig"],
                            size=n, p=[0.55, 0.30, 0.15])
    city_tier = rng.choice([1, 2, 3], size=n, p=[0.40, 0.35, 0.25])

    # Age varies by employment type.
    age = np.empty(n, dtype=int)
    for etype, (lo, hi) in {"salaried": (24, 58),
                            "self_employed": (28, 60),
                            "gig": (21, 45)}.items():
        mask = employment == etype
        age[mask] = rng.integers(lo, hi + 1, mask.sum())

    gender = rng.choice(["M", "F"], size=n, p=[0.52, 0.48])

    # TRUE monthly income (hidden): lognormal by employment, scaled by city tier.
    median = np.select(
        [employment == "salaried", employment == "self_employed", employment == "gig"],
        [52000.0, 95000.0, 32000.0])
    sigma = np.select(
        [employment == "salaried", employment == "self_employed", employment == "gig"],
        [0.40, 0.55, 0.40])
    tier_mult = np.select([city_tier == 1, city_tier == 2, city_tier == 3],
                          [1.25, 1.00, 0.80])
    true_income = np.clip(
        rng.lognormal(np.log(median), sigma) * tier_mult, 12000, 500000)
    true_income = np.round(true_income / 500) * 500

    # DECLARED income: salaried ~ truthful; self-employed / gig under-declare
    # (what a salary slip / simple form would show). This is the gap Engine A
    # recovers from transactions.
    declared_factor = np.select(
        [employment == "salaried", employment == "self_employed", employment == "gig"],
        [rng.uniform(0.95, 1.03, n),
         rng.uniform(0.30, 0.55, n),
         rng.uniform(0.45, 0.70, n)])
    declared_income = np.round(true_income * declared_factor / 500) * 500

    # Existing monthly obligations (EMIs). ~60% carry some.
    has_emi = rng.random(n) < 0.60
    emi_frac = rng.uniform(0.05, 0.45, n)
    existing_emi = np.where(has_emi, np.round(true_income * emi_frac / 500) * 500, 0.0)
    foir_true = np.divide(existing_emi, true_income,
                          out=np.zeros(n), where=true_income > 0)

    # Credit bureau score (CIBIL-like 300-900), income-tilted.
    score = rng.normal(720, 70, n) + 8 * (np.log(true_income) - np.log(50000))
    credit_bureau_score = np.clip(np.round(score), 300, 900).astype(int)

    # Default label (~8%, imbalanced) — learnable from score / FOIR / income /
    # employment, plus noise so it is not perfectly separable (Global Rule 8:
    # this is credit-default risk, NOT fraud).
    emp_risk = np.select(
        [employment == "salaried", employment == "self_employed", employment == "gig"],
        [-0.40, 0.15, 0.50])
    risk = (
        -0.9 * (credit_bureau_score - 720) / 70
        + 1.6 * (foir_true - 0.20)
        - 0.4 * (np.log(true_income) - np.log(50000))
        + emp_risk
        + rng.normal(0, 0.8, n)
    )
    defaulted = (risk > np.quantile(risk, 0.92)).astype(int)  # ~8%

    # rng-fixed per-customer helpers (used by transaction generator)
    companies = _build_company_pool(240)
    employer = np.array([companies[i] for i in rng.integers(0, len(companies), n)])
    salary_day = rng.integers(1, 4, n)
    emi_bank = np.array([BANKS[i] for i in rng.integers(0, len(BANKS), n)])

    return pd.DataFrame({
        "customer_id": customer_id,
        "age": age,
        "gender": gender,
        "employment_type": employment,
        "city_tier": city_tier,
        "declared_income": declared_income.astype(int),
        "existing_emi": existing_emi.astype(int),
        "credit_bureau_score": credit_bureau_score,
        "defaulted": defaulted,
        # hidden / helper columns (not written to customers.csv)
        "true_income": true_income.astype(int),
        "employer": employer,
        "salary_day": salary_day,
        "emi_bank": emi_bank,
    })


# ---------------------------------------------------------------------------
# 2. Behaviour / intent signals + life-event flags
# ---------------------------------------------------------------------------
def build_behaviour(df: pd.DataFrame) -> pd.DataFrame:
    """Behavioural intent signals plus life-event flags. Flags are decided here
    and later reflected in the transaction ledger so the two stay consistent."""
    rng = np.random.default_rng(config.RANDOM_STATE + 1)
    n = len(df)
    income = df["true_income"].values
    emi = df["existing_emi"].values
    emp = df["employment_type"].values

    # --- life events -------------------------------------------------------
    is_renter = rng.random(n) < np.where(df["age"].values < 40, 0.65, 0.40)
    rising_rent = (is_renter & (rng.random(n) < 0.28)).astype(int)
    lease_renewal = (is_renter & (rng.random(n) < 0.22)).astype(int)
    car_servicing = (rng.random(n) < 0.16).astype(int)
    salary_hike = ((emp == "salaried") & (rng.random(n) < 0.25)).astype(int)
    foir_true = np.divide(emi, income, out=np.zeros(n), where=income > 0)
    high_cost_emi = ((emi > 0) & (foir_true > 0.32)).astype(int)

    # Mild, ethically-framed engagement gap by gender (a *channel* effect, not a
    # creditworthiness one) so the fairness gate (Part 5) has a real disparity to
    # measure against the 80% rule. Tunable; kept small on purpose.
    gender_factor = np.where(df["gender"].values == "F", 0.92, 1.0)

    renter_aspirant = (is_renter & (income > 40000)).astype(float)
    home = np.clip(rng.poisson(
        (0.15 + 1.6 * rising_rent + 1.3 * lease_renewal + 0.5 * renter_aspirant)
        * gender_factor), 0, 8)
    auto = np.clip(rng.poisson(
        (0.12 + 1.4 * car_servicing + 0.15) * gender_factor), 0, 8)
    personal = np.clip(rng.poisson(
        (0.12 + 1.3 * high_cost_emi + 0.15) * gender_factor), 0, 8)
    emi_calc = np.clip(rng.poisson(0.3 + 0.35 * (home + auto + personal)), 0, 15)

    any_intent = (home + auto + personal) > 0
    app_sessions = np.clip(rng.poisson(np.where(any_intent, 12, 5)), 0, 60)
    days_since = np.where(any_intent,
                          rng.integers(0, 15, n),
                          rng.integers(5, 90, n))

    # rng-fixed helpers for transaction generation
    base_rent = np.where(is_renter,
                         np.round(income * rng.uniform(0.12, 0.25, n) / 500) * 500,
                         0).astype(int)
    car_month = rng.integers(0, config.TRANSACTION_MONTHS, n)

    return pd.DataFrame({
        "customer_id": df["customer_id"].values,
        "emi_calculator_uses": emi_calc,
        "home_loan_page_visits": home,
        "auto_loan_page_visits": auto,
        "personal_loan_page_visits": personal,
        "app_sessions_30d": app_sessions,
        "days_since_last_visit": days_since,
        "rising_rent_flag": rising_rent,
        "lease_renewal_flag": lease_renewal,
        "car_servicing_flag": car_servicing,
        "high_cost_emi_flag": high_cost_emi,
        "salary_hike_flag": salary_hike,
        # helpers (not written to behaviour.csv)
        "is_renter": is_renter.astype(int),
        "base_rent": base_rent,
        "car_month": car_month,
    })


# ---------------------------------------------------------------------------
# 3. Transaction ledger (6 months) — reflects true income + life events
# ---------------------------------------------------------------------------
def build_transactions(df: pd.DataFrame, beh: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(config.RANDOM_STATE + 2)
    periods = _month_periods(AS_OF, config.TRANSACTION_MONTHS)
    companies = _build_company_pool(240)

    cust, dates, amts, dirs, narrs = [], [], [], [], []

    def add(cid, y, m, day, amount, direction, narration):
        cust.append(cid)
        dates.append(f"{y:04d}-{m:02d}-{min(int(day), 28):02d}")
        amts.append(int(round(amount)))
        dirs.append(direction)
        narrs.append(narration)

    merged = df.merge(
        beh[["customer_id", "is_renter", "base_rent", "car_month",
             "rising_rent_flag", "lease_renewal_flag", "car_servicing_flag",
             "salary_hike_flag"]],
        on="customer_id")

    for row in merged.itertuples(index=False):
        cid = row.customer_id
        inc = row.true_income
        emp = row.employment_type
        spend_scale = float(np.clip(inc / 60000.0, 0.5, 1.8))

        for mi, (y, m) in enumerate(periods):
            # --- income inflows ---
            if emp == "salaried":
                amt = inc * (1.12 if (row.salary_hike_flag and mi >= 3) else 1.0)
                add(cid, y, m, row.salary_day, amt, "credit",
                    f"NEFT/SALARY/{row.employer}")
            elif emp == "self_employed":
                k = int(rng.integers(3, 7))
                total = inc * rng.uniform(0.80, 1.20)
                for part in rng.dirichlet(np.ones(k)) * total:
                    client = companies[int(rng.integers(0, len(companies)))]
                    add(cid, y, m, int(rng.integers(1, 28)), part, "credit",
                        f"UPI/{client}")
            else:  # gig
                k = int(rng.integers(4, 9))
                total = inc * rng.uniform(0.85, 1.15)
                for part in rng.dirichlet(np.ones(k)) * total:
                    plat = GIG_PLATFORMS[int(rng.integers(0, len(GIG_PLATFORMS)))]
                    add(cid, y, m, int(rng.integers(1, 28)), part, "credit",
                        f"UPI/GIGPAY/{plat}")

            # --- rent (renters) ---
            if row.is_renter:
                if row.rising_rent_flag:
                    rent = row.base_rent * (1.03 ** mi)
                elif row.lease_renewal_flag:
                    rent = row.base_rent * (1.08 if mi >= 4 else 1.0)
                else:
                    rent = row.base_rent
                add(cid, y, m, 5, rent, "debit", "NEFT/RENT/HOUSING")

            # --- existing EMI ---
            if row.existing_emi > 0:
                add(cid, y, m, 7, row.existing_emi, "debit",
                    f"ACH/EMI/{row.emi_bank}")

            # --- discretionary spends ---
            for _ in range(int(rng.integers(4, 8))):
                template, brands, (lo, hi) = DISCRETIONARY[
                    int(rng.integers(0, len(DISCRETIONARY)))]
                amount = rng.uniform(lo, hi) * spend_scale
                narration = template.format(brands[int(rng.integers(0, len(brands)))]) \
                    if brands else template
                add(cid, y, m, int(rng.integers(1, 28)), amount, "debit", narration)

            # --- car servicing (once, in its month) ---
            if row.car_servicing_flag and mi == row.car_month:
                brand = CAR_BRANDS[int(rng.integers(0, len(CAR_BRANDS)))]
                add(cid, y, m, int(rng.integers(1, 28)),
                    rng.integers(8000, 25000), "debit", f"POS/AUTOSERVICE/{brand}")

        # --- non-income credits (challenge income inference) ---
        if rng.random() < 0.50:
            for _ in range(int(rng.integers(1, 3))):
                y, m = periods[int(rng.integers(0, len(periods)))]
                add(cid, y, m, int(rng.integers(1, 28)),
                    rng.uniform(200, 8000), "credit", "UPI/P2P TRANSFER")
        if rng.random() < 0.15:
            y, m = periods[int(rng.integers(0, len(periods)))]
            add(cid, y, m, int(rng.integers(1, 28)),
                rng.uniform(300, 5000), "credit", "UPI/REFUND/AMAZON")
        if rng.random() < 0.05:  # rare one-off loan disbursal — NOT income
            y, m = periods[int(rng.integers(0, len(periods)))]
            add(cid, y, m, int(rng.integers(1, 28)),
                rng.uniform(50000, 300000), "credit", "NEFT/LOANDISB/BANK")

    txns = pd.DataFrame({
        "customer_id": cust,
        "date": dates,
        "amount": amts,
        "direction": dirs,
        "narration": narrs,
    })
    return txns.sort_values(["customer_id", "date"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 4. Treatment / outcome (uplift label)
# ---------------------------------------------------------------------------
def build_treatment(df: pd.DataFrame, beh: pd.DataFrame) -> pd.DataFrame:
    """Randomised `contacted` (RCT-style, p=0.5) and a `converted` outcome with a
    genuine persuadable segment, so the uplift model learns who converts
    *because* of outreach rather than regardless."""
    rng = np.random.default_rng(config.RANDOM_STATE + 3)
    n = len(df)
    income = df["true_income"].values
    emi = df["existing_emi"].values

    disposable = np.clip(income * config.FOIR_CAP - emi, 0, None)
    afford = np.clip(disposable / (0.45 * income), 0, 1)

    intent_raw = (beh["home_loan_page_visits"].values
                  + beh["auto_loan_page_visits"].values
                  + beh["personal_loan_page_visits"].values
                  + 0.5 * beh["emi_calculator_uses"].values)
    intent = np.clip(intent_raw / 6.0, 0, 1)
    recency = np.exp(-beh["days_since_last_visit"].values / 30.0)

    # Baseline conversion (would happen even without contact).
    base = 1.0 / (1.0 + np.exp(-(-2.3 + 1.6 * intent + 0.8 * afford + 0.9 * recency)))
    # Persuadables: strong intent + recent + affordable. We suppress their base
    # so that *contact* is what tips them over — that is the uplift.
    persuadable = intent * recency * afford
    base = base * (1 - 0.55 * persuadable)
    uplift_true = 0.40 * persuadable

    contacted = rng.binomial(1, 0.5, n)
    p_convert = np.clip(base + contacted * uplift_true, 0, 0.97)
    converted = rng.binomial(1, p_convert)

    return pd.DataFrame({
        "customer_id": df["customer_id"].values,
        "contacted": contacted.astype(int),
        "converted": converted.astype(int),
    })


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def generate() -> None:
    config.ensure_dirs()
    n = config.N_CUSTOMERS

    using_homecredit = ingest_homecredit.is_available()
    if using_homecredit:
        print(f"[data] Home Credit dataset found at {config.RAW_HOMECREDIT_CSV.name} "
              f"-> using it as the customer master (optional enrichment).")
        master = ingest_homecredit.load_master(n)
        n = len(master)
    else:
        print("[data] No Home Credit file -> generating a fully synthetic master.")
        master = build_master(n)

    behaviour = build_behaviour(master)
    transactions = build_transactions(master, behaviour)
    treatment = build_treatment(master, behaviour)

    # --- project to public output tables (drop hidden/helper columns) ---
    customer_cols = ["customer_id", "age", "gender", "employment_type",
                     "city_tier", "declared_income", "existing_emi",
                     "credit_bureau_score", "defaulted"]
    # Home Credit path carries extra EXT_SOURCE_* columns — keep them if present.
    extra = [c for c in master.columns if c.startswith("ext_source")]
    customers = master[customer_cols + extra].copy()

    behaviour_cols = ["customer_id", "emi_calculator_uses", "home_loan_page_visits",
                      "auto_loan_page_visits", "personal_loan_page_visits",
                      "app_sessions_30d", "days_since_last_visit",
                      "rising_rent_flag", "lease_renewal_flag", "car_servicing_flag",
                      "high_cost_emi_flag", "salary_hike_flag"]
    behaviour_out = behaviour[behaviour_cols].copy()

    ground_truth = master[["customer_id", "true_income"]].copy()

    # --- write ---
    customers.to_csv(config.CUSTOMERS_CSV, index=False, encoding="utf-8")
    transactions.to_csv(config.TRANSACTIONS_CSV, index=False, encoding="utf-8")
    behaviour_out.to_csv(config.BEHAVIOUR_CSV, index=False, encoding="utf-8")
    treatment.to_csv(config.TREATMENT_CSV, index=False, encoding="utf-8")
    ground_truth.to_csv(config.INCOME_GROUND_TRUTH_CSV, index=False, encoding="utf-8")

    _print_summary(customers, transactions, behaviour_out, treatment,
                   ground_truth, master, using_homecredit)


def _print_summary(customers, transactions, behaviour, treatment,
                   ground_truth, master, using_homecredit) -> None:
    n = len(customers)
    print("\n" + "=" * 64)
    print(" Synthetic data generated" +
          ("  (Home Credit enriched)" if using_homecredit else "  (fully synthetic)"))
    print("=" * 64)
    print(f"  customers.csv            : {n:,} rows")
    print(f"  transactions.csv         : {len(transactions):,} rows "
          f"(~{len(transactions)/n:.0f}/customer)")
    print(f"  behaviour.csv            : {len(behaviour):,} rows")
    print(f"  treatment.csv            : {len(treatment):,} rows")
    print(f"  income_ground_truth.csv  : {len(ground_truth):,} rows")
    print("-" * 64)
    print(f"  default rate             : {customers['defaulted'].mean():.1%}")
    print("  employment mix           : " +
          ", ".join(f"{k} {v:.0%}" for k, v in
                    customers['employment_type'].value_counts(normalize=True).items()))
    print(f"  gender mix               : " +
          ", ".join(f"{k} {v:.0%}" for k, v in
                    customers['gender'].value_counts(normalize=True).items()))
    print("-" * 64)
    print("  Declared vs TRUE monthly income (median) by employment:")
    gt = ground_truth.set_index("customer_id")["true_income"]
    tmp = customers.set_index("customer_id")
    tmp = tmp.assign(true_income=gt)
    for etype, g in tmp.groupby("employment_type"):
        ratio = (g["declared_income"] / g["true_income"]).median()
        print(f"    {etype:<14}: declared ₹{g['declared_income'].median():>10,.0f}"
              f"  true ₹{g['true_income'].median():>10,.0f}"
              f"  (declared is {ratio:.0%} of true)")
    print("-" * 64)
    print(f"  contacted rate           : {treatment['contacted'].mean():.1%}")
    print(f"  overall conversion       : {treatment['converted'].mean():.1%}")
    conv_c = treatment.loc[treatment.contacted == 1, "converted"].mean()
    conv_u = treatment.loc[treatment.contacted == 0, "converted"].mean()
    print(f"  conversion | contacted   : {conv_c:.1%}")
    print(f"  conversion | not contacted: {conv_u:.1%}")
    print(f"  naive avg treatment effect: {conv_c - conv_u:+.1%}")
    print("-" * 64)
    print("  life-event flags (share of customers):")
    for flag in ["rising_rent_flag", "lease_renewal_flag", "car_servicing_flag",
                 "high_cost_emi_flag", "salary_hike_flag"]:
        print(f"    {flag:<20}: {behaviour[flag].mean():.1%}")
    print("=" * 64)
    print("data OK -> data/synthetic/")


if __name__ == "__main__":
    generate()
