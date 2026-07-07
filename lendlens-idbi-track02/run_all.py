"""
LendLens — one-command pipeline runner (no `make` required).

Runs every Python stage in order using the *current* interpreter, so it works
identically on Windows (PowerShell) and POSIX. This is the primary entry point
on Windows where GNU make is usually absent.

    python run_all.py            # run the whole pipeline
    python run_all.py --from train   # resume from a stage

Stages (Global Rule 3):
    generate data -> train engines -> explain + fairness -> score -> leads.json
"""
from __future__ import annotations

import subprocess
import sys

# This launcher does not import config, so give it the same UTF-8 console fix
# (stage labels contain non-ASCII like the em-dash).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# (stage-key, human label, module to run with `-m`)
STAGES: list[tuple[str, str, str]] = [
    ("data",    "Generate synthetic data",            "data.synthetic.generate"),
    ("train",   "Train Engine A (income & default)",  "engines.income_engine.train"),
    ("train",   "Infer Engine A (income scores)",     "engines.income_engine.infer"),
    ("train",   "Train Engine B (intent & uplift)",   "engines.intent_engine.train"),
    ("train",   "Infer Engine B (intent scores)",     "engines.intent_engine.infer"),
    ("explain", "Explainability — SHAP reason codes", "explainability.shap_reasons"),
    ("explain", "Fairness — 80% rule check",          "explainability.fairness_check"),
    ("score",   "Decisioning — tiers",                "decisioning.lead_scorer"),
    ("score",   "Offer engine -> leads.json",         "decisioning.offer_engine"),
]

STAGE_ORDER = ["data", "train", "explain", "score"]


def main() -> int:
    start = None
    if "--from" in sys.argv:
        i = sys.argv.index("--from")
        try:
            start = sys.argv[i + 1]
        except IndexError:
            print("--from requires a stage name: data|train|explain|score")
            return 2
        if start not in STAGE_ORDER:
            print(f"unknown stage '{start}'. choose from {STAGE_ORDER}")
            return 2

    started = start is None
    for key, label, module in STAGES:
        if not started:
            if key == start:
                started = True
            else:
                continue
        print("\n" + "=" * 64)
        print(f">> {label}")
        print("=" * 64)
        result = subprocess.run([sys.executable, "-m", module])
        if result.returncode != 0:
            print(f"\n[FAILED] stage '{label}' (module {module}) "
                  f"exited with code {result.returncode}")
            return result.returncode

    print("\n" + "=" * 64)
    print(">> Pipeline complete -> data/processed/leads.json")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
