"""
Engine B — uplift model (Part 4).

A T-learner: two independent XGBoost models — one trained on the CONTACTED
(treatment) group, one on the NOT-contacted (control) group. The uplift score is
the difference in predicted conversion probability:

    uplift(x) = P(convert | x, contacted) - P(convert | x, not contacted)

i.e. the *incremental* conversion the outreach causes. This is what lets us skip
"sure things" and "lost causes" and spend RM time only on genuine persuadables.

Uses scikit-uplift's TwoModels when available (the canonical T-learner); falls
back to a hand-rolled equivalent otherwise. Ships an uplift-decile chart and a
Qini coefficient for honest evaluation.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # headless: save PNGs without a display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

import config

try:
    from sklift.models import TwoModels
    _HAVE_SKLIFT = True
except Exception:  # pragma: no cover - defensive
    _HAVE_SKLIFT = False


def _xgb() -> XGBClassifier:
    return XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.06,
        subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0,
        eval_metric="logloss", random_state=config.RANDOM_STATE, n_jobs=4)


class _ManualTLearner:
    """Fallback T-learner if scikit-uplift is unavailable."""

    def __init__(self):
        self.m_treat = _xgb()
        self.m_ctrl = _xgb()

    def fit(self, X, y, treatment):
        t = np.asarray(treatment).astype(int)
        self.m_treat.fit(X[t == 1], np.asarray(y)[t == 1])
        self.m_ctrl.fit(X[t == 0], np.asarray(y)[t == 0])
        return self

    def predict(self, X):
        return (self.m_treat.predict_proba(X)[:, 1]
                - self.m_ctrl.predict_proba(X)[:, 1])


def make_uplift_model():
    """Return a fresh uplift model (sklift TwoModels 'vanilla' == T-learner)."""
    if _HAVE_SKLIFT:
        return TwoModels(estimator_trmnt=_xgb(), estimator_ctrl=_xgb(),
                         method="vanilla")
    return _ManualTLearner()


def uplift_by_decile(uplift_pred, treatment, converted, n_bins=10) -> pd.DataFrame:
    """Observed incremental conversion per predicted-uplift decile.

    Decile 1 = highest predicted uplift. observed_uplift = conversion rate among
    contacted minus conversion rate among not-contacted, within each decile.
    """
    d = pd.DataFrame({"u": np.asarray(uplift_pred),
                      "t": np.asarray(treatment).astype(int),
                      "y": np.asarray(converted).astype(int)})
    ranked = d["u"].rank(method="first", ascending=False)
    d["decile"] = pd.qcut(ranked, n_bins, labels=range(1, n_bins + 1)).astype(int)
    rows = []
    for dec, g in d.groupby("decile"):
        treat = g.loc[g.t == 1, "y"]
        ctrl = g.loc[g.t == 0, "y"]
        obs = (treat.mean() if len(treat) else 0.0) - (ctrl.mean() if len(ctrl) else 0.0)
        rows.append((int(dec), float(obs), int(len(g))))
    return pd.DataFrame(rows, columns=["decile", "observed_uplift", "n"])


def qini_coefficient(uplift_pred, treatment, converted) -> float | None:
    """Qini AUC (normalised) via scikit-uplift, if available."""
    if not _HAVE_SKLIFT:
        return None
    try:
        from sklift.metrics import qini_auc_score
        return float(qini_auc_score(
            np.asarray(converted).astype(int),
            np.asarray(uplift_pred),
            np.asarray(treatment).astype(int)))
    except Exception:
        return None


def save_uplift_curve(decile_df: pd.DataFrame, overall_ate: float,
                      path=config.UPLIFT_CURVE_PNG) -> None:
    """Bar chart of observed uplift by predicted-uplift decile (top decile left)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#0b6b3a" if d == 1 else "#2e8b57" if d <= 3 else "#9bbcae"
              for d in decile_df["decile"]]
    ax.bar(decile_df["decile"], decile_df["observed_uplift"] * 100,
           color=colors, edgecolor="white")
    ax.axhline(overall_ate * 100, color="#b03030", linestyle="--", linewidth=1.5,
               label=f"Overall avg treatment effect ({overall_ate*100:.1f}%)")
    ax.set_xlabel("Predicted-uplift decile  (1 = model's most persuadable)")
    ax.set_ylabel("Observed incremental conversion (%)")
    ax.set_title("LendLens uplift model — targeting the persuadables\n"
                 "top decile shows the highest real lift (cross-fitted, all 5k)")
    ax.set_xticks(range(1, len(decile_df) + 1))
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
