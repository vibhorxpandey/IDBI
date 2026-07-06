"""
Fairness gate — 80% (four-fifths) rule (Part 5).

Checks whether LendLens's lead SELECTION is balanced across the protected
attribute `gender`, using Fairlearn. Selection here = "surfaced as an offer-worthy
lead": affordable (FOIR-capped headroom > 0) AND not uplift-suppressed AND
conversion propensity at/above the eligible median.

Reports the disparate-impact ratio (min/max group selection rate) against the
80% threshold. If it fails, applies a fairness-constrained per-group conversion
threshold (demographic-parity postprocessing) and reports before/after.

NOTE: this governs *lead selection / outreach*, not the final credit decision
(which stays subject to full underwriting). It is a lead-gen fairness check.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from fairlearn.metrics import (MetricFrame, demographic_parity_ratio,
                               selection_rate)

import config


def _group_rates(selected: pd.Series, gender: pd.Series) -> dict:
    mf = MetricFrame(metrics=selection_rate, y_true=selected, y_pred=selected,
                     sensitive_features=gender)
    return {str(k): float(v) for k, v in mf.by_group.items()}


def _di_ratio(selected: pd.Series, gender: pd.Series) -> float:
    return float(demographic_parity_ratio(
        selected, y_pred=selected, sensitive_features=gender))


def _select_per_group(df: pd.DataFrame, taus: dict) -> np.ndarray:
    sel = np.zeros(len(df), dtype=bool)
    for g, tau in taus.items():
        m = (df["gender"] == g).to_numpy()
        sel[m] = df.loc[m, "eligible"].to_numpy() & (
            df.loc[m, "conversion_prob"].to_numpy() >= tau)
    return sel


def run() -> dict:
    customers = pd.read_csv(config.CUSTOMERS_CSV)[["customer_id", "gender"]]
    income = pd.read_json(config.INCOME_SCORES_JSON)[["customer_id", "max_affordable_emi"]]
    intent = pd.read_json(config.INTENT_SCORES_JSON)[
        ["customer_id", "conversion_prob", "uplift_score"]]
    df = customers.merge(income, on="customer_id").merge(intent, on="customer_id")

    # Prudent-lending + uplift gates are NOT touched by fairness — only the
    # conversion bar within eligible leads is.
    df["eligible"] = ((df["max_affordable_emi"] > 0)
                      & (df["uplift_score"] >= config.UPLIFT_SUPPRESSION_CUTOFF))
    tau = float(df.loc[df["eligible"], "conversion_prob"].median())
    df["selected"] = df["eligible"] & (df["conversion_prob"] >= tau)

    rates = _group_rates(df["selected"], df["gender"])
    di = _di_ratio(df["selected"], df["gender"])
    passes = di >= config.DISPARATE_IMPACT_MIN

    adjusted, di_after, rates_after, method = False, di, rates, "none required"
    if not passes:
        adjusted = True
        method = "per-group conversion threshold (demographic parity)"
        target = max(rates.values())  # lift the disadvantaged group up
        taus: dict[str, float] = {}
        for g in sorted(df["gender"].unique()):
            gd = df[df["gender"] == g]
            elig_conv = np.sort(gd.loc[gd["eligible"], "conversion_prob"].to_numpy())[::-1]
            need = int(round(target * len(gd)))
            if need <= 0:
                taus[g] = np.inf
            elif need >= len(elig_conv):
                taus[g] = -np.inf  # select every eligible lead in this group
            else:
                taus[g] = float(elig_conv[need - 1])
        df["selected_adj"] = _select_per_group(df, taus)
        rates_after = _group_rates(df["selected_adj"], df["gender"])
        di_after = _di_ratio(df["selected_adj"], df["gender"])

    summary = {
        "protected_attribute": "gender",
        "rule": "80% (four-fifths) rule",
        "threshold": config.DISPARATE_IMPACT_MIN,
        "disparate_impact_ratio": round(di, 3),
        "passes": bool(passes),
        "group_selection_rates": {k: round(v, 4) for k, v in rates.items()},
        "n_selected": int(df["selected"].sum()),
        "n_total": int(len(df)),
        "adjusted": adjusted,
        "method": method,
        "disparate_impact_ratio_after": round(di_after, 3),
        "group_selection_rates_after": (
            {k: round(v, 4) for k, v in rates_after.items()} if adjusted else None),
    }
    return summary


def _write_report(s: dict) -> None:
    verdict = "✅ PASS" if s["passes"] else "⚠️ FAIL (pre-adjustment)"
    lines = [
        "# LendLens — Fairness Report (80% Rule)",
        "",
        f"**Protected attribute:** `{s['protected_attribute']}`  ",
        f"**Rule:** {s['rule']} — disparate-impact ratio must be ≥ "
        f"{s['threshold']:.0%}  ",
        f"**Scope:** lead selection / outreach (not the final credit decision, "
        f"which remains subject to full underwriting).",
        "",
        f"## Result: {verdict}",
        "",
        f"- **Disparate-impact ratio:** {s['disparate_impact_ratio']:.3f} "
        f"(min group rate ÷ max group rate)",
        f"- **Leads selected:** {s['n_selected']:,} of {s['n_total']:,}",
        "",
        "### Selection rate by group",
        "",
        "| Group | Selection rate |",
        "| --- | --- |",
    ]
    for g, r in sorted(s["group_selection_rates"].items()):
        lines.append(f"| {g} | {r:.1%} |")
    if s["adjusted"]:
        lines += [
            "",
            "## Fairness-constrained adjustment applied",
            f"Method: **{s['method']}**. The prudent-lending FOIR cap and the "
            "uplift-suppression gate are left intact; only the conversion bar is "
            "rebalanced across groups.",
            "",
            f"- **Disparate-impact ratio after:** {s['disparate_impact_ratio_after']:.3f}",
            "",
            "### Selection rate by group (after)",
            "",
            "| Group | Selection rate |",
            "| --- | --- |",
        ]
        for g, r in sorted((s["group_selection_rates_after"] or {}).items()):
            lines.append(f"| {g} | {r:.1%} |")
    else:
        lines += ["", "No adjustment required — the 80% rule is satisfied as-is."]
    lines += ["", "_Generated by `explainability/fairness_check.py` (Fairlearn)._", ""]

    config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    config.FAIRNESS_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    s = run()
    _write_report(s)
    config.ensure_dirs()
    with open(config.FAIRNESS_SUMMARY_JSON, "w", encoding="utf-8") as fh:
        json.dump(s, fh, ensure_ascii=False, indent=2)

    print("=" * 64)
    print(" Fairness gate — 80% rule (protected attribute: gender)")
    print("=" * 64)
    for g, r in sorted(s["group_selection_rates"].items()):
        print(f"  selection rate [{g}]      : {r:.1%}")
    print(f"  disparate-impact ratio   : {s['disparate_impact_ratio']:.3f}  "
          f"(threshold {s['threshold']:.0%})")
    print(f"  verdict                  : {'PASS' if s['passes'] else 'FAIL'}")
    if s["adjusted"]:
        print(f"  adjustment               : {s['method']}")
        print(f"  ratio after adjustment   : {s['disparate_impact_ratio_after']:.3f}")
    print(f"  reports                  : {config.FAIRNESS_REPORT_MD.name}, "
          f"{config.FAIRNESS_SUMMARY_JSON.name}")
    print("=" * 64)


if __name__ == "__main__":
    main()
