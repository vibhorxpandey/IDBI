"""
Engine A — train the default / affordability model (Part 3).

Trains an XGBoost classifier on the `defaulted` label using inferred-income
affordability features, prints AUC / Gini, and saves the model bundle. On the
Home Credit dataset AUC is typically ~0.75-0.78; on synthetic data it may differ
— we report whatever it is (Global Rule: honest metrics).
"""
from __future__ import annotations

import pickle

import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

import config
from engines.income_engine import features as feat
from engines.income_engine import income_inference


def main() -> None:
    customers = pd.read_csv(config.CUSTOMERS_CSV)
    tx = pd.read_csv(config.TRANSACTIONS_CSV)

    estimates = income_inference.estimate_income(customers, tx)
    df, feature_cols = feat.build_features(customers, tx, estimates)

    X, y = df[feature_cols], df["defaulted"].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=config.RANDOM_STATE)

    # No class reweighting: keep predicted probabilities ~calibrated to the true
    # ~8% base rate so `default_risk` is believable when shown to an RM. AUC (a
    # threshold-free ranking metric) is unaffected by this choice.
    model = XGBClassifier(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        eval_metric="auc",
        random_state=config.RANDOM_STATE,
        n_jobs=4,
    )
    model.fit(X_tr, y_tr)

    proba_te = model.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, proba_te)
    gini = 2 * auc - 1

    print("=" * 64)
    print(" Engine A — default / affordability model (XGBoost)")
    print("=" * 64)
    print(f"  train / test rows        : {len(X_tr):,} / {len(X_te):,}")
    print(f"  default rate (train)     : {y_tr.mean():.1%}  (no reweighting)")
    print(f"  features ({len(feature_cols)})           : {', '.join(feature_cols)}")
    print(f"  test AUC                 : {auc:.3f}")
    print(f"  test Gini                : {gini:.3f}")
    top = (pd.Series(model.feature_importances_, index=feature_cols)
           .sort_values(ascending=False).head(5))
    print("  top features             : " +
          ", ".join(f"{k} ({v:.2f})" for k, v in top.items()))

    config.INCOME_MODEL_PKL.parent.mkdir(parents=True, exist_ok=True)
    with open(config.INCOME_MODEL_PKL, "wb") as fh:
        pickle.dump({"model": model, "features": feature_cols}, fh)
    print(f"  saved model              : {config.INCOME_MODEL_PKL.name}")
    print("=" * 64)


if __name__ == "__main__":
    main()
