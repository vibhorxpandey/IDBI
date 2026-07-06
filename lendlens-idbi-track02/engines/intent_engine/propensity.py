"""
Engine B — conversion propensity (Part 4).

An XGBoost classifier predicting `converted`, wrapped in isotonic calibration
(CalibratedClassifierCV) so the output `conversion_prob` is a trustworthy
probability the RM can act on — not just a ranking score.

conversion_prob is modelled as P(convert | contacted): the probability the lead
converts IF the RM reaches out — the actionable number the console shows. It is
therefore trained on the contacted (treatment) population. Paired with the
separate uplift score, this makes the Part 6 rule coherent: a lead can have a
high conversion_prob yet low uplift (a "sure thing" who converts regardless) —
and gets suppressed so the RM isn't spent on it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

import config


def _base_estimator() -> XGBClassifier:
    return XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        eval_metric="logloss",
        random_state=config.RANDOM_STATE,
        n_jobs=4,
    )


def train_propensity(X: pd.DataFrame, y: pd.Series,
                     treatment: pd.Series) -> tuple[CalibratedClassifierCV, dict]:
    """Fit an isotonically-calibrated P(convert | contacted) model on the
    contacted population. Returns (model, held-out metrics)."""
    mask = np.asarray(treatment) == 1
    Xc, yc = X[mask], y[mask]
    X_tr, X_te, y_tr, y_te = train_test_split(
        Xc, yc, test_size=0.25, stratify=yc, random_state=config.RANDOM_STATE)

    # cv=3 internally fits the base learner on folds and calibrates on held-out
    # folds — clean isotonic calibration with no manual prefit juggling.
    model = CalibratedClassifierCV(
        estimator=_base_estimator(), method="isotonic", cv=3)
    model.fit(X_tr, y_tr)

    proba_te = model.predict_proba(X_te)[:, 1]
    metrics = {
        "auc": float(roc_auc_score(y_te, proba_te)),
        "brier": float(brier_score_loss(y_te, proba_te)),
        "mean_pred": float(proba_te.mean()),
        "actual_rate": float(y_te.mean()),
        "n_test": int(len(y_te)),
    }
    return model, metrics


def fit_final(X: pd.DataFrame, y: pd.Series,
              treatment: pd.Series) -> CalibratedClassifierCV:
    """Calibrated P(convert | contacted) model fit on ALL contacted customers —
    used to score every customer (held-out metrics come from train_propensity)."""
    mask = np.asarray(treatment) == 1
    model = CalibratedClassifierCV(
        estimator=_base_estimator(), method="isotonic", cv=3)
    model.fit(X[mask], y[mask])
    return model


if __name__ == "__main__":
    from engines.intent_engine import features as intent_feat
    beh = pd.read_csv(config.BEHAVIOUR_CSV)
    treat = pd.read_csv(config.TREATMENT_CSV)
    df, feats = intent_feat.build_intent_features(beh)
    df = df.merge(treat, on="customer_id")
    model, m = train_propensity(df[feats], df["converted"].astype(int),
                                df["contacted"].astype(int))
    print(f"propensity(if contacted) AUC={m['auc']:.3f} brier={m['brier']:.4f} "
          f"mean_pred={m['mean_pred']:.1%} actual={m['actual_rate']:.1%}")
