"""
Explainability — SHAP reason codes (Part 5).

Runs SHAP TreeExplainer on the Engine A (default/affordability) and Engine B
(intent) XGBoost models, then turns the strongest POSITIVE drivers of each
customer's lead quality into the top-3 plain-English reason codes an RM sees.

Raw feature names never reach the RM (Global Rule 5) — every driver is mapped
through the explicit FEATURE_PHRASES dictionary below, with counts/flags filled
from the customer's actual data (e.g. "3 recent home-loan page visits").

Sign convention
---------------
* Engine A predicts P(default): a feature that REDUCES default is good, so its
  "goodness" = -SHAP.
* Engine B predicts P(convert | contacted): a feature that RAISES conversion is
  good, so its "goodness" = +SHAP.
Contributions are normalised within each engine (per customer) so the two
log-odds scales are comparable before merging.
"""
from __future__ import annotations

import json
import pickle

import numpy as np
import pandas as pd
import shap

import config
from engines.income_engine import features as inc_feat
from engines.income_engine import income_inference
from engines.intent_engine import features as intent_feat

def _pl(n: int, singular: str) -> str:
    """'3 recent home-loan page visits' / '1 recent home-loan page visit'."""
    return f"{n} recent {singular}" + ("" if n == 1 else "s")


# Each entry: model-feature -> callable(behaviour_row, income_row) -> phrase.
# `kind` guards vacuous reasons (a flag that is 0, or a zero count).
FEATURE_PHRASES = {
    # ---- Engine B: intent / behaviour ----
    "home_loan_page_visits_rw": ("count", "home_loan_page_visits",
                                 lambda n, b, i: _pl(n, "home-loan page visit")),
    "auto_loan_page_visits_rw": ("count", "auto_loan_page_visits",
                                 lambda n, b, i: _pl(n, "auto-loan page visit")),
    "personal_loan_page_visits_rw": ("count", "personal_loan_page_visits",
                                     lambda n, b, i: _pl(n, "personal-loan page visit")),
    "emi_calculator_uses_rw": ("count", "emi_calculator_uses",
                               lambda n, b, i: f"{n} EMI-calculator session"
                               + ("" if n == 1 else "s")),
    # total_intent_rw / days_since_last_visit are intentionally NOT surfaced:
    # the first is a vague aggregate, the second duplicates recency_weight. Both
    # still drive the model — they just don't make good RM-facing reason codes.
    "recency_weight": ("plain", None, lambda n, b, i: "Recently active on our channels"),
    "app_sessions_30d": ("plain", None,
                         lambda n, b, i: f"Highly engaged ({int(b['app_sessions_30d'])} app sessions/30d)"),
    "rising_rent_flag": ("flag", "rising_rent_flag",
                         lambda n, b, i: "Rising rent detected — home-buying signal"),
    "lease_renewal_flag": ("flag", "lease_renewal_flag",
                           lambda n, b, i: "Lease renewal detected"),
    "car_servicing_flag": ("flag", "car_servicing_flag",
                           lambda n, b, i: "Recent car servicing — auto-loan signal"),
    "high_cost_emi_flag": ("flag", "high_cost_emi_flag",
                           lambda n, b, i: "High-cost EMI — consolidation opportunity"),
    "salary_hike_flag": ("flag", "salary_hike_flag",
                         lambda n, b, i: "Recent salary hike"),
    # ---- Engine A: affordability / credit ----
    "disposable_income": ("plain", None, lambda n, b, i: "High disposable income"),
    "max_affordable_emi": ("plain", None, lambda n, b, i: "Strong repayment capacity"),
    "foir": ("plain", None, lambda n, b, i: "Comfortable debt-to-income (FOIR)"),
    "credit_bureau_score": ("plain", None, lambda n, b, i: "Strong credit bureau score"),
    "log_estimated_income": ("plain", None, lambda n, b, i: "Healthy verified income"),
    "avg_monthly_credit": ("plain", None, lambda n, b, i: "Healthy monthly account inflows"),
    "income_confidence": ("plain", None, lambda n, b, i: "Consistent, verifiable income"),
    "income_stability": ("plain", None, lambda n, b, i: "Stable income pattern"),
    "income_months": ("plain", None, lambda n, b, i: "6 months of consistent income"),
    "employment_code": ("plain", None, lambda n, b, i: "Stable employment profile"),
    "expense_ratio": ("plain", None, lambda n, b, i: "Prudent spending pattern"),
    "age": ("plain", None, lambda n, b, i: "Prime lending age"),
    "ext_source_1": ("plain", None, lambda n, b, i: "Strong credit behaviour"),
    "ext_source_2": ("plain", None, lambda n, b, i: "Strong credit behaviour"),
    "ext_source_3": ("plain", None, lambda n, b, i: "Strong credit behaviour"),
}

# Data-grounded generic positives, used only to top up to exactly 3 reasons.
FALLBACK_REASONS = [
    "Verified income via consented data",
    "Existing bank relationship",
    "Meets prudent-lending affordability checks",
]

# Reason codes blend two honest signals: (1) concrete DETECTED signals — the
# suggested product's page-visits and any life-event trigger that is actually
# present — and (2) SHAP-attributed affordability/credit/engagement drivers.
_VISIT_FEATURES = {"home_loan_page_visits_rw", "auto_loan_page_visits_rw",
                   "personal_loan_page_visits_rw"}


ALL_FLAGS = ["lease_renewal_flag", "rising_rent_flag", "car_servicing_flag",
             "high_cost_emi_flag", "salary_hike_flag"]
# suggested product -> its page-visit feature (the intent signal to surface)
PRODUCT_VISIT = {"Home": "home_loan_page_visits_rw",
                 "Auto": "auto_loan_page_visits_rw",
                 "Personal": "personal_loan_page_visits_rw"}
# suggested product -> life-event flags to prefer as the trigger reason
PRODUCT_FLAGS = {"Home": ["lease_renewal_flag", "rising_rent_flag"],
                 "Auto": ["car_servicing_flag"],
                 "Personal": ["high_cost_emi_flag"],
                 "Mortgage": []}
# Slot 3+ (SHAP fill) covers affordability/credit/engagement only — intent and
# life-events are handled by the product-aware slots above.
_SHAP_FILL_SKIP = _VISIT_FEATURES | set(ALL_FLAGS)


def _tree_shap(model, X: pd.DataFrame) -> np.ndarray:
    """SHAP contributions to the positive-class margin, shape (n, n_features)."""
    explainer = shap.TreeExplainer(model)
    vals = explainer.shap_values(X)
    if isinstance(vals, list):          # some shap versions return [neg, pos]
        vals = vals[-1]
    return np.asarray(vals)


def _phrase_for(feature: str, beh_row: pd.Series, inc_row: pd.Series) -> str | None:
    """Build the phrase for a feature, or None if it would be vacuous."""
    entry = FEATURE_PHRASES.get(feature)
    if entry is None:
        return None
    kind, source, fn = entry
    if kind == "flag":
        if int(beh_row.get(source, 0)) != 1:
            return None
        return fn(None, beh_row, inc_row)
    if kind == "count":
        n = int(beh_row.get(source, 0))
        if n <= 0:
            return None
        return fn(n, beh_row, inc_row)
    return fn(None, beh_row, inc_row)


def build_reason_codes() -> dict[str, list[str]]:
    customers = pd.read_csv(config.CUSTOMERS_CSV)
    tx = pd.read_csv(config.TRANSACTIONS_CSV)
    behaviour = pd.read_csv(config.BEHAVIOUR_CSV)
    income = pd.read_json(config.INCOME_SCORES_JSON)
    intent = pd.read_json(config.INTENT_SCORES_JSON)
    product = dict(zip(intent["customer_id"], intent["suggested_product"]))

    # Engine A model + feature matrix (aligned to training).
    with open(config.INCOME_MODEL_PKL, "rb") as fh:
        a_bundle = pickle.load(fh)
    estimates = income_inference.estimate_income(customers, tx)
    a_df, _ = inc_feat.build_features(customers, tx, estimates)
    feats_a = a_bundle["features"]
    shap_a = _tree_shap(a_bundle["model"], a_df[feats_a])

    # Engine B explainer model + feature matrix.
    with open(config.INTENT_EXPLAINER_PKL, "rb") as fh:
        b_bundle = pickle.load(fh)
    b_df, _ = intent_feat.build_intent_features(behaviour, income)
    feats_b = b_bundle["features"]
    shap_b = _tree_shap(b_bundle["model"], b_df[feats_b])

    # Per-customer lookups for phrase templating.
    beh_idx = behaviour.set_index("customer_id")
    inc_idx = income.set_index("customer_id")

    # goodness = how much a feature argues this is a GOOD lead.
    good_a = -shap_a  # reducing default is good
    good_b = shap_b   # raising conversion is good
    # normalise within each engine per customer so scales are comparable
    norm_a = np.abs(shap_a).sum(axis=1, keepdims=True) + 1e-9
    norm_b = np.abs(shap_b).sum(axis=1, keepdims=True) + 1e-9
    rel_a = good_a / norm_a
    rel_b = good_b / norm_b

    order_a = customers["customer_id"].tolist()
    order_b = b_df["customer_id"].tolist()
    b_pos = {cid: i for i, cid in enumerate(order_b)}

    reasons: dict[str, list[str]] = {}
    for ai, cid in enumerate(order_a):
        bi = b_pos[cid]
        beh_row = beh_idx.loc[cid]
        inc_row = inc_idx.loc[cid]

        picked: list[str] = []
        prod = product.get(cid, "")

        # Slot 1 — the suggested product's own intent signal (page visits).
        pv = PRODUCT_VISIT.get(prod)
        if pv:
            p = _phrase_for(pv, beh_row, inc_row)
            if p and p not in picked:
                picked.append(p)

        # Slot 2 — a detected life-event trigger (product-aligned first).
        flag_order = PRODUCT_FLAGS.get(prod, []) + [
            f for f in ALL_FLAGS if f not in PRODUCT_FLAGS.get(prod, [])]
        for fl in flag_order:
            p = _phrase_for(fl, beh_row, inc_row)
            if p and p not in picked:
                picked.append(p)
                break

        # Slot 3+ — SHAP-attributed affordability / credit / engagement drivers.
        candidates = []
        for j, f in enumerate(feats_a):
            if f not in _SHAP_FILL_SKIP and rel_a[ai, j] > 0:
                candidates.append((rel_a[ai, j], f))
        for j, f in enumerate(feats_b):
            if f not in _SHAP_FILL_SKIP and rel_b[bi, j] > 0:
                candidates.append((rel_b[bi, j], f))
        candidates.sort(key=lambda x: x[0], reverse=True)
        for _, f in candidates:
            if len(picked) == 3:
                break
            phrase = _phrase_for(f, beh_row, inc_row)
            if phrase and phrase not in picked:
                picked.append(phrase)

        for fb in FALLBACK_REASONS:
            if len(picked) == 3:
                break
            if fb not in picked:
                picked.append(fb)
        reasons[cid] = picked[:3]

    return reasons


def main() -> None:
    reasons = build_reason_codes()
    config.ensure_dirs()
    ordered = {cid: reasons[cid] for cid in sorted(reasons)}
    with open(config.REASON_CODES_JSON, "w", encoding="utf-8") as fh:
        json.dump(ordered, fh, ensure_ascii=False, indent=2)

    counts = [len(v) for v in reasons.values()]
    from collections import Counter
    freq = Counter(p for v in reasons.values() for p in v)
    print("=" * 64)
    print(" Explainability — reason_codes.json written")
    print("=" * 64)
    print(f"  customers explained      : {len(reasons):,}")
    print(f"  all have exactly 3 reasons: {all(c == 3 for c in counts)}")
    print("  most common reason codes :")
    for phrase, c in freq.most_common(8):
        print(f"    {c:>5,}  {phrase}")
    print(f"  output                   : {config.REASON_CODES_JSON}")
    print("=" * 64)


if __name__ == "__main__":
    main()
