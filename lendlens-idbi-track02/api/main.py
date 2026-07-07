"""
LendLens API (Part 7) — serves the ranked leads and represents the AA/ULI/OCEN
rails (mock, see integrations_stub.py).

Endpoints:
    GET  /                     service info + health
    GET  /leads                ranked leads (?tier=GOLD &product=Home
                               &include_suppressed=false &limit=N)
    GET  /leads/{customer_id}  full detail for one lead (RM card)
    GET  /fairness             fairness (80% rule) summary
    GET  /portfolio            aggregate counts + uplift curve for the charts
    POST /aa/consent, /aa/fetch, /uli/..., /ocen/...   MOCK integration rails

Run:  uvicorn api.main:app --reload      (or: make api)
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import config
from api.integrations_stub import router as integrations_router

app = FastAPI(
    title="LendLens API",
    description="Consent-first pre-approved-offer engine — IDBI Track 02 (Round-1). "
                "AA / ULI / OCEN rails are mocked and clearly labelled.",
    version="1.0.0",
)

# Dashboard runs on a different origin (Vite dev server) — allow CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(integrations_router)

# --- lightweight file cache: reload only when a file changes on disk ---
_CACHE: dict[str, tuple[float, object]] = {}


def _load(path: Path, default):
    key = str(path)
    mtime = path.stat().st_mtime if path.exists() else 0.0
    cached = _CACHE.get(key)
    if cached is None or cached[0] != mtime:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
        _CACHE[key] = (mtime, data)
    return _CACHE[key][1]


def _leads() -> list[dict]:
    leads = _load(config.LEADS_JSON, None)
    if leads is None:
        raise HTTPException(
            status_code=503,
            detail="leads.json not found — run the pipeline first: python run_all.py")
    return leads


@app.get("/", summary="Service info + health")
def root() -> dict:
    leads = _load(config.LEADS_JSON, None)
    return {
        "service": "LendLens API",
        "status": "ok" if leads is not None else "pipeline-not-run",
        "leads_loaded": len(leads) if leads else 0,
        "endpoints": ["/leads", "/leads/{customer_id}", "/fairness", "/portfolio",
                      "/aa/consent", "/aa/fetch", "/uli/borrower/{id}",
                      "/ocen/loan-application", "/docs"],
        "note": "AA / ULI / OCEN endpoints are MOCK (see /docs).",
    }


@app.get("/leads", summary="Ranked leads (filterable)")
def get_leads(
    tier: str | None = Query(None, description="GOLD | SILVER | BRONZE | SUPPRESSED"),
    product: str | None = Query(None, description="Home | Auto | Personal | Mortgage"),
    include_suppressed: bool = Query(False, description="include uplift-suppressed leads"),
    limit: int | None = Query(None, ge=1, description="cap the number returned"),
) -> list[dict]:
    rows = _leads()
    if not include_suppressed:
        rows = [l for l in rows if l["tier"] != "SUPPRESSED"]
    if tier:
        rows = [l for l in rows if l["tier"] == tier.upper()]
    if product:
        rows = [l for l in rows if l["suggested_product"].lower() == product.lower()]
    return rows[:limit] if limit else rows


@app.get("/leads/{customer_id}", summary="Full detail for one lead (RM card)")
def get_lead(customer_id: str) -> dict:
    for lead in _leads():
        if lead["customer_id"] == customer_id:
            return lead
    raise HTTPException(status_code=404, detail=f"lead '{customer_id}' not found")


@app.get("/fairness", summary="Fairness (80% rule) summary")
def get_fairness() -> dict:
    summary = _load(config.FAIRNESS_SUMMARY_JSON, None)
    if summary is None:
        raise HTTPException(status_code=503, detail="fairness_summary.json not found")
    return summary


@app.get("/portfolio", summary="Aggregates + uplift curve for the dashboard charts")
def get_portfolio() -> dict:
    leads = _leads()
    surfaced = [l for l in leads if l["tier"] != "SUPPRESSED"]
    by_tier = Counter(l["tier"] for l in leads)
    by_product = Counter(l["suggested_product"] for l in surfaced)
    total_offer_value = sum(
        l["offer"]["amount"] for l in surfaced if l.get("offer"))

    uplift = _load(config.UPLIFT_CURVE_JSON, {}) or {}
    fairness = _load(config.FAIRNESS_SUMMARY_JSON, {}) or {}
    return {
        "total_leads": len(leads),
        "surfaced": len(surfaced),
        "suppressed": by_tier.get("SUPPRESSED", 0),
        "by_tier": {t: by_tier.get(t, 0)
                    for t in ["GOLD", "SILVER", "BRONZE", "SUPPRESSED"]},
        "by_product": dict(by_product),
        "total_offer_value": total_offer_value,
        "uplift_curve": uplift.get("deciles", []),
        "uplift_ate": uplift.get("ate"),
        "uplift_qini": uplift.get("qini"),
        "fairness": {
            "disparate_impact_ratio": fairness.get("disparate_impact_ratio"),
            "passes": fairness.get("passes"),
            "threshold": fairness.get("threshold"),
        },
    }
