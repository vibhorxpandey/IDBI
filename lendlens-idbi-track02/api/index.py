"""
Vercel serverless entry for the LendLens API.

Vercel serves this module's `app`. The full FastAPI application (api.main) is
mounted under /api, so the deployed routes are same-origin with the static
dashboard: /api/leads, /api/portfolio, /api/leads/{id}, /api/fairness,
/api/aa/consent, /api/aa/fetch, /api/ocen/loan-application.

Local dev is unaffected — keep using `uvicorn api.main:app` (serves /leads).
This file exists only so Vercel has a single, minimal-dependency entrypoint.
"""
import os
import sys

# Make the repo root importable on Vercel's runtime so `config` and `api.main`
# resolve (this file lives at <root>/api/index.py).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI  # noqa: E402
from api.main import app as _lendlens_app  # noqa: E402

app = FastAPI(title="LendLens (Vercel)")
app.mount("/api", _lendlens_app)  # /api/leads, /api/portfolio, /api/aa/consent, …
