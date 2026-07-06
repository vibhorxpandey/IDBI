# LendLens — one-command pipeline (Global Rule 3)
#
# On Windows without GNU make, use the pure-Python equivalent instead:
#     python run_all.py
#
# PYTHON defaults to `python`; activate the venv first, or override:
#     make all PYTHON=.venv/Scripts/python.exe      (Windows)
#     make all PYTHON=.venv/bin/python              (POSIX)

PYTHON ?= python

.PHONY: all data train explain score api dashboard clean

## all: run the full pipeline -> data/processed/leads.json
all: data train explain score
	@echo ""
	@echo "Pipeline complete -> data/processed/leads.json"

## data: generate the synthetic dataset (Part 2)
data:
	$(PYTHON) -m data.synthetic.generate

## train: train + infer both engines (Parts 3 & 4)
train:
	$(PYTHON) -m engines.income_engine.train
	$(PYTHON) -m engines.income_engine.infer
	$(PYTHON) -m engines.intent_engine.train
	$(PYTHON) -m engines.intent_engine.infer

## explain: SHAP reason codes + fairness gate (Part 5)
explain:
	$(PYTHON) -m explainability.shap_reasons
	$(PYTHON) -m explainability.fairness_check

## score: decisioning tiers + pre-approved offers (Part 6)
score:
	$(PYTHON) -m decisioning.lead_scorer
	$(PYTHON) -m decisioning.offer_engine

## api: serve the leads API (Part 7)
api:
	$(PYTHON) -m uvicorn api.main:app --reload

## dashboard: run the React dashboard dev server (Part 8)
dashboard:
	cd dashboard && npm install && npm run dev

## clean: remove generated data, models and charts (keeps source)
clean:
	$(PYTHON) -c "import shutil, glob, os; \
[shutil.rmtree(p, ignore_errors=True) for p in ['data/processed','data/synthetic/__pycache__']]; \
[os.remove(f) for f in glob.glob('data/synthetic/*.csv')]; \
[os.remove(f) for f in glob.glob('engines/**/*.pkl', recursive=True)]; \
print('cleaned generated artefacts')"
