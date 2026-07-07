"""
Engine B — train propensity + uplift (Part 4).

Trains the calibrated conversion-propensity model and the T-learner uplift model,
saves both, and writes the uplift-decile chart to docs/uplift_curve.png.

The uplift chart is built from CROSS-FITTED (out-of-fold) predictions over all
5,000 customers: every customer is scored by a model that never saw them, so the
decile chart is both honest (no in-sample optimism) and low-noise (500/decile).
The deployed scoring model is then refit on all data.
"""
from __future__ import annotations

import json
import pickle

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

import config
from engines.intent_engine import features as intent_feat
from engines.intent_engine import propensity as prop
from engines.intent_engine import uplift as up


def main() -> None:
    beh = pd.read_csv(config.BEHAVIOUR_CSV)
    treat = pd.read_csv(config.TREATMENT_CSV)
    income = pd.read_json(config.INCOME_SCORES_JSON)  # Engine A affordability context

    df, feats = intent_feat.build_intent_features(beh, income)
    df = df.merge(treat, on="customer_id")

    X = df[feats].reset_index(drop=True)
    y = df["converted"].astype(int).reset_index(drop=True)
    t = df["contacted"].astype(int).reset_index(drop=True)

    # ---- propensity (calibrated P(convert | contacted)) ----
    _, pmetrics = prop.train_propensity(X, y, t)
    prop_final = prop.fit_final(X, y, t)
    with open(config.INTENT_PROPENSITY_PKL, "wb") as fh:
        pickle.dump({"model": prop_final, "features": feats}, fh)

    # ---- uplift (T-learner): cross-fitted evaluation, full-data deployment ----
    oof = np.zeros(len(X))
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.RANDOM_STATE)
    for tr_idx, te_idx in skf.split(X, t):
        m = up.make_uplift_model().fit(
            X.iloc[tr_idx], y.iloc[tr_idx], t.iloc[tr_idx])
        oof[te_idx] = m.predict(X.iloc[te_idx])

    decile = up.uplift_by_decile(oof, t, y)
    ate = float(y[t == 1].mean() - y[t == 0].mean())
    up.save_uplift_curve(decile, ate)
    qini = up.qini_coefficient(oof, t, y)

    # Decile data for the dashboard's Recharts uplift panel (Part 8).
    with open(config.UPLIFT_CURVE_JSON, "w", encoding="utf-8") as fh:
        json.dump({
            "ate": round(ate, 4),
            "qini": round(qini, 4) if qini is not None else None,
            "deciles": [{"decile": int(r.decile),
                         "observed_uplift": round(float(r.observed_uplift), 4),
                         "n": int(r.n)} for r in decile.itertuples(index=False)],
        }, fh, ensure_ascii=False, indent=2)

    up_final = up.make_uplift_model().fit(X, y, t)
    with open(config.INTENT_UPLIFT_PKL, "wb") as fh:
        pickle.dump({"model": up_final, "features": feats}, fh)

    # Plain XGB on P(convert | contacted) for SHAP TreeExplainer (Part 5). Same
    # target as the propensity model, but a bare tree so SHAP is exact & clean.
    explainer = prop._base_estimator()
    mask = (t == 1).to_numpy()
    explainer.fit(X[mask], y[mask])
    with open(config.INTENT_EXPLAINER_PKL, "wb") as fh:
        pickle.dump({"model": explainer, "features": feats}, fh)

    # ---- report ----
    print("=" * 64)
    print(" Engine B — propensity + uplift")
    print("=" * 64)
    print(f"  uplift backend           : "
          f"{'scikit-uplift TwoModels' if up._HAVE_SKLIFT else 'manual T-learner'}")
    print(f"  features ({len(feats)})           : {', '.join(feats)}")
    print(f"  propensity(if contacted) : test AUC {pmetrics['auc']:.3f}")
    print(f"  propensity calibration   : mean pred {pmetrics['mean_pred']:.1%} "
          f"vs actual {pmetrics['actual_rate']:.1%}  (Brier {pmetrics['brier']:.4f})")
    if qini is not None:
        print(f"  uplift Qini coefficient  : {qini:.4f}  (cross-fitted, all 5k)")
    print(f"  overall avg treatment eff: {ate:+.1%}")
    print("  observed uplift by predicted-uplift decile (1 = most persuadable):")
    for r in decile.itertuples(index=False):
        bar = "#" * max(0, int(round(r.observed_uplift * 100)))
        print(f"    decile {r.decile:>2} (n={r.n:>3}): "
              f"{r.observed_uplift*100:+5.1f}%  {bar}")
    top = decile.iloc[0]["observed_uplift"]
    bottom3 = decile["observed_uplift"].iloc[-3:].mean()
    print(f"  top decile vs bottom-3   : {top*100:+.1f}%  vs  {bottom3*100:+.1f}%")
    print(f"  saved                    : propensity.pkl, uplift.pkl, "
          f"{config.UPLIFT_CURVE_PNG.name}")
    print("=" * 64)


if __name__ == "__main__":
    main()
