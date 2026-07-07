import { useState } from "react";
import { api } from "../api";
import { TIER } from "../theme";
import { inr, inrShort, pct, signedPct } from "../format";

function Stat({ label, value, accent }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className={`text-sm font-semibold ${accent || "text-slate-800"}`}>{value}</div>
    </div>
  );
}

export default function LeadDetail({ lead, onClose }) {
  const [extended, setExtended] = useState(null);
  const [busy, setBusy] = useState(false);

  if (!lead) {
    return (
      <div className="flex h-full min-h-[300px] flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white/60 p-6 text-center">
        <div className="text-3xl">👈</div>
        <div className="mt-2 text-sm font-medium text-slate-600">Select a lead</div>
        <div className="text-xs text-slate-400">
          Click any row (or “★ Demo: Priya”) to open the RM card.
        </div>
      </div>
    );
  }

  const t = TIER[lead.tier];
  const gap = lead.declared_income ? lead.estimated_income / lead.declared_income : 1;

  const extend = async () => {
    if (!lead.offer) return;
    setBusy(true);
    try {
      const r = await api.ocenApply({
        customer_id: lead.customer_id,
        product: lead.offer.product,
        amount: lead.offer.amount,
        tenor_years: lead.offer.tenor_years,
      });
      setExtended(r.application_id || "OCEN-MOCK");
    } catch {
      setExtended("OCEN-OFFLINE");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="animate-fade-up rounded-xl border border-slate-200 bg-white shadow-sm">
      {/* header */}
      <div className="flex items-start justify-between border-b border-slate-100 p-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-slate-800">
              {lead.customer_id === "CUST_PRIYA" && <span className="text-amber-500">★ </span>}
              {lead.name}
            </h3>
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${t.badge}`}>{t.label}</span>
          </div>
          <div className="text-xs text-slate-400">
            {lead.city} · {lead.age} yrs · {lead.gender} · rank #{lead.rank}
          </div>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
      </div>

      {/* key metrics */}
      <div className="grid grid-cols-2 gap-3 p-4">
        <Stat label="Suggested product" value={lead.suggested_product} accent="text-idbi-green" />
        <Stat label="Best time to call" value={lead.best_time_to_contact} />
        <Stat label="Conversion (if contacted)" value={pct(lead.conversion_prob)} />
        <Stat
          label="Uplift"
          value={signedPct(lead.uplift_score)}
          accent={lead.uplift_score > 0 ? "text-emerald-600" : "text-slate-500"}
        />
      </div>

      {/* income gap */}
      <div className="mx-4 mb-4 rounded-lg bg-slate-50 p-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase text-slate-400">Declared</div>
            <div className="text-sm font-semibold text-slate-500 line-through">{inr(lead.declared_income)}</div>
          </div>
          <div className="text-idbi-green text-lg">→</div>
          <div className="text-right">
            <div className="text-[11px] uppercase text-idbi-greenDark">Inferred (real)</div>
            <div className="text-sm font-bold text-idbi-green">{inr(lead.estimated_income)}</div>
          </div>
          <div className="rounded-md bg-idbi-green px-2 py-1 text-xs font-bold text-white">{gap.toFixed(1)}×</div>
        </div>
        <div className="mt-2 flex justify-between text-[11px] text-slate-400">
          <span>Max affordable EMI: {inr(lead.max_affordable_emi)}</span>
          <span>Default risk: {pct(lead.default_risk, 1)}</span>
        </div>
      </div>

      {/* reason codes */}
      <div className="px-4 pb-4">
        <div className="text-[11px] uppercase tracking-wide text-slate-400">Why this lead</div>
        <ul className="mt-1.5 space-y-1.5">
          {lead.reason_codes?.map((r, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
              <span className="mt-0.5 text-idbi-green">✓</span>
              {r}
            </li>
          ))}
        </ul>
      </div>

      {/* offer */}
      {lead.offer && (
        <div className="m-4 rounded-xl bg-idbi-greenLight p-4">
          <div className="flex items-center justify-between">
            <div className="text-[11px] font-medium uppercase tracking-wide text-idbi-greenDark">
              Pre-approved offer
            </div>
            <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-idbi-green ring-1 ring-idbi-green/20">
              {lead.offer.product}
            </span>
          </div>
          <div className="mt-1 text-2xl font-bold text-idbi-greenDark">{inr(lead.offer.amount)}</div>
          <div className="mt-1 grid grid-cols-3 gap-2 text-xs text-slate-600">
            <div>EMI <b>{inr(lead.offer.emi)}</b>/mo</div>
            <div>Rate <b>{lead.offer.indicative_rate}%</b></div>
            <div>Tenor <b>{lead.offer.tenor_years}y</b></div>
          </div>
          {extended ? (
            <div className="mt-3 rounded-lg bg-white px-3 py-2 text-xs text-emerald-700 ring-1 ring-emerald-200">
              ✓ Offer sent over OCEN · <b>{extended}</b> <span className="text-slate-400">(mock)</span>
            </div>
          ) : (
            <button
              onClick={extend}
              disabled={busy}
              className="mt-3 w-full rounded-lg bg-idbi-green py-2 text-sm font-medium text-white hover:bg-idbi-greenDark disabled:opacity-50"
            >
              {busy ? "Sending…" : "Extend offer"} <span className="opacity-70">(mock)</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
