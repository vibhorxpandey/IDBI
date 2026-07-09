"""
Vercel serverless entry — serves BOTH the API and the built dashboard.

Vercel's static/function split doesn't play nicely with our frontend living in a
subdirectory, so instead of relying on CDN static hosting we let one function
serve everything:
  * /api/*  -> the FastAPI application (api.main)
  * /*      -> the built SPA (dashboard/dist), incl. index.html + assets

vercel.json rewrites every request here. The build step copies the API's JSON
into dashboard/dist/_data and points the API at it via LENDLENS_PROCESSED_DIR,
so a single `includeFiles: dashboard/dist/**` bundles the SPA *and* the data.

Local dev is unaffected — keep using `uvicorn api.main:app` (serves /leads).
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

_DIST = os.path.join(_ROOT, "dashboard", "dist")
# The API reads its JSON from the copy bundled inside the build output.
os.environ.setdefault("LENDLENS_PROCESSED_DIR", os.path.join(_DIST, "_data"))

from fastapi import FastAPI  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from api.main import app as api_app  # noqa: E402

app = FastAPI(title="LendLens")
app.mount("/api", api_app)  # /api/leads, /api/portfolio, /api/aa/consent, …

# Serve the built SPA at the root (index.html + hashed assets).
if os.path.isdir(_DIST):
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="spa")
