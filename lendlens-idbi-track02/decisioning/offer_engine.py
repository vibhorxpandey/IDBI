"""
Decisioning — pre-approved offer engine (Part 6).

For every non-suppressed lead, builds a coherent pre-approved offer for the
suggested product. The headline amount is the LOWER of:
  (a) affordability principal — back-solved from the FOIR-capped max affordable
      EMI at the product's rate/tenor, and
  (b) a conservative multiple of verified annual income (config income_multiple),
also clipped to the product ceiling. Because the final amount never exceeds the
affordability principal, the resulting EMI is guaranteed ≤ max_affordable_emi
(Global Rule 6).

Writes the final data/processed/leads.json.
"""
from __future__ import annotations

import json
import math

import config

# Headline amounts are rounded DOWN to these units (keeps EMI ≤ affordability).
ROUND_UNIT = {"Home": 100_000, "Mortgage": 100_000, "Auto": 25_000, "Personal": 25_000}


def _annuity_factor(monthly_rate: float, n_months: int) -> float:
    if monthly_rate <= 0:
        return float(n_months)
    return (1 - (1 + monthly_rate) ** -n_months) / monthly_rate


def principal_from_emi(emi: float, annual_rate: float, tenor_years: int) -> float:
    return emi * _annuity_factor(annual_rate / 12, tenor_years * 12)


def emi_from_principal(principal: float, annual_rate: float, tenor_years: int) -> float:
    return principal / _annuity_factor(annual_rate / 12, tenor_years * 12)


def build_offer(product: str, max_affordable_emi: float,
                estimated_income: float) -> dict | None:
    """Return an offer dict, or None if the product is unknown."""
    p = config.PRODUCTS.get(product)
    if p is None:
        return None
    rate, tenor = p["rate"], p["tenor_years"]

    affordability_principal = principal_from_emi(max_affordable_emi, rate, tenor)
    income_cap = p["income_multiple"] * estimated_income * 12       # annual income
    raw = min(affordability_principal, income_cap, p["max_amount"])

    unit = ROUND_UNIT.get(product, 50_000)
    amount = math.floor(raw / unit) * unit
    if amount < unit:  # tiny-capacity fallback, still ≤ raw so EMI stays capped
        amount = math.floor(raw / 10_000) * 10_000
    amount = max(amount, 0)

    emi = emi_from_principal(amount, rate, tenor) if amount > 0 else 0.0
    return {
        "product": product,
        "amount": int(amount),
        "emi": int(round(emi)),
        "indicative_rate": round(rate * 100, 2),   # percent, e.g. 8.5
        "tenor_years": tenor,
    }


def main() -> None:
    with open(config.LEADS_SCORED_JSON, encoding="utf-8") as fh:
        leads = json.load(fh)

    n_offered = 0
    emi_violations = 0
    for lead in leads:
        if lead["tier"] == "SUPPRESSED":
            lead["offer"] = None
            continue
        offer = build_offer(lead["suggested_product"],
                            lead["max_affordable_emi"],
                            lead["estimated_income"])
        lead["offer"] = offer
        if offer:
            n_offered += 1
            if offer["emi"] > lead["max_affordable_emi"]:
                emi_violations += 1

    config.ensure_dirs()
    with open(config.LEADS_JSON, "w", encoding="utf-8") as fh:
        json.dump(leads, fh, ensure_ascii=False, indent=2)

    # --- report ---
    offered = [l for l in leads if l["offer"]]
    by_product: dict[str, list[int]] = {}
    for l in offered:
        by_product.setdefault(l["offer"]["product"], []).append(l["offer"]["amount"])

    print("=" * 64)
    print(" Decisioning — offers built -> leads.json")
    print("=" * 64)
    print(f"  total leads              : {len(leads):,}")
    print(f"  offers built             : {n_offered:,}")
    print(f"  EMI > max affordable EMI : {emi_violations}  (must be 0)")
    print("  median pre-approved offer by product:")
    for prod in ["Home", "Mortgage", "Auto", "Personal"]:
        amts = sorted(by_product.get(prod, []))
        if amts:
            med = amts[len(amts) // 2]
            print(f"    {prod:<9}: {len(amts):>5,} offers   median ₹{med:,}")
    top = next((l for l in leads if l["tier"] == "GOLD"), None)
    if top:
        o = top["offer"]
        print(f"  top GOLD lead            : {top['name']} ({top['city']}) — "
              f"{o['product']} ₹{o['amount']:,} @ {o['indicative_rate']}% / "
              f"{o['tenor_years']}y, EMI ₹{o['emi']:,}")
    print(f"  output                   : {config.LEADS_JSON}")
    print("=" * 64)


if __name__ == "__main__":
    main()
