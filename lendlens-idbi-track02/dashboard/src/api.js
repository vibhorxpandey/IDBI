// LendLens API client. Base URL is configurable; defaults to the local uvicorn.
const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function get(path) {
  const res = await fetch(BASE + path);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function post(path, body) {
  const res = await fetch(BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

export const api = {
  base: BASE,
  leads: (params = {}) => get("/leads?" + new URLSearchParams(params).toString()),
  lead: (id) => get("/leads/" + encodeURIComponent(id)),
  portfolio: () => get("/portfolio"),
  fairness: () => get("/fairness"),
  aaConsent: (body) => post("/aa/consent", body),
  aaFetch: (body) => post("/aa/fetch", body),
  ocenApply: (body) => post("/ocen/loan-application", body),
};
