"""
scripts/demo_priya.py — print Priya's full LendLens journey end-to-end.

For the 3-minute demo / video: consent -> inferred income -> intent & uplift ->
tier -> pre-approved offer -> plain-English reasons. Reads the pipeline outputs
in data/processed/, so run the pipeline first:

    python run_all.py
    python scripts/demo_priya.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _by_id(records):
    return {r["customer_id"]: r for r in records}


def main() -> None:
    if not config.LEADS_JSON.exists():
        print("leads.json not found — run the pipeline first:  python run_all.py")
        return

    leads = _by_id(_load(config.LEADS_JSON))
    income = _by_id(_load(config.INCOME_SCORES_JSON))
    intent = _by_id(_load(config.INTENT_SCORES_JSON))
    pid = config.PRIYA_ID

    if pid not in leads:
        print(f"{pid} not found in leads.json — is she seeded? Re-run: python run_all.py")
        return

    L, I, N = leads[pid], income[pid], intent[pid]
    inr = config._inr
    line = "=" * 66

    print(line)
    print(f"  LendLens — customer journey :  {L['name']}  ({pid})")
    print(line)

    print("\n[1] CONSENT  (mock Account Aggregator — DPDP-compliant, consent-first)")
    print("    Priya taps 'Check my eligibility' and grants consent to share")
    print("    6 months of bank statements via the AA rail. *Simulated.*")

    print("\n[2] INCOME & REPAYMENT CAPACITY  (Engine A — from her transactions)")
    print(f"    Declared income (form/slip) : {inr(L['declared_income'])} / month")
    print(f"    INFERRED true income        : {inr(L['estimated_income'])} / month"
          f"   [{I['income_method']}, confidence {I['income_confidence']:.0%}]")
    gap = L["estimated_income"] / max(L["declared_income"], 1)
    print(f"    -> her real income is {gap:.1f}x what the form shows")
    print(f"    Existing EMIs               : {inr(L['existing_emi'])} / month")
    print(f"    Max affordable EMI (FOIR {config.FOIR_CAP:.0%}) : {inr(L['max_affordable_emi'])} / month")
    print(f"    Default risk                : {L['default_risk']:.1%}")

    print("\n[3] INTENT & PROPENSITY  (Engine B — behaviour + uplift)")
    print(f"    Suggested product           : {L['suggested_product']}")
    print(f"    Predicted conversion (if contacted) : {L['conversion_prob']:.0%}")
    print(f"    Uplift score                : {L['uplift_score']:+.2f}  "
          f"(genuinely persuadable — worth an RM's time)")
    print(f"    Best time to contact        : {L['best_time_to_contact']}")

    print("\n[4] EXPLAINABILITY & FAIRNESS  (the trust layer)")
    print("    Why this lead (top-3 reasons):")
    for r in L["reason_codes"]:
        print(f"      • {r}")

    print("\n[5] DECISION  ->  ranked lead")
    print(f"    TIER  : {L['tier']}        (queue rank #{L['rank']})")
    o = L["offer"]
    if o:
        print(f"    PRE-APPROVED OFFER : {o['product']} loan  {inr(o['amount'])}")
        print(f"      EMI {inr(o['emi'])}/mo  @ {o['indicative_rate']}% p.a.  "
              f"over {o['tenor_years']} years")
        print(f"      (EMI {inr(o['emi'])} is well within her "
              f"{inr(L['max_affordable_emi'])} capacity)")
    print(line)
    verdict = (L["tier"] == "GOLD" and L["suggested_product"] == "Home"
               and o and 15_00_000 <= o["amount"] <= 20_00_000)
    print(f"  Demo check: Gold + Home + offer ~₹18L  ->  "
          f"{'PASS ✅' if verdict else 'review'}")
    print(line)


if __name__ == "__main__":
    main()
