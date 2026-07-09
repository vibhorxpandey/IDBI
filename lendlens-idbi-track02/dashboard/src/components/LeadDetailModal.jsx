import { useState } from "react";
import { api } from "../api";
import { TIER } from "../theme";
import { inr, pct, signedPct } from "../format";

function Stat({ label, value, accent }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-slate-400 dark:text-ll-txt3">{label}</div>
      <div className={`text-sm font-semibold ${accent || "text-slate-800 dark:text-ll-txt"}`}>{value}</div>
    </div>
  );
}

export default function LeadDetailModal({ lead, onClose, notify }) {
  const [extended, setExtended] = useState(null);
  const [busy, setBusy] = useState(false);
  if (!lead) return null;

  const t = TIER[lead.tier];
  const gap = lead.declared_income ? lead.estimated_income / lead.declared_income : 1;

  const extend = async () => {
    if (!lead.offer) return;
    setBusy(true);
    try {
      const r = await api.ocenApply({ customer_id: lead.customer_id, product: lead.offer.product, amount: lead.offer.amount, tenor_years: lead.offer.tenor_years });
      setExtended(r.application_id || "OCEN-MOCK");
      notify?.("Offer extended over OCEN (mock)", "ok");
    } catch { setExtended("OCEN-OFFLINE"); notify?.("OCEN offline — saved locally", "warn"); }
    finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} className="glass w-full max-w-md animate-scale-in overflow-hidden">
        <div className="flex items-start justify-between border-b border-slate-100 p-4 dark:border-white/[0.06]">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-800 dark:text-ll-txt">{lead.customer_id === "CUST_PRIYA" && <span className="text-amber-500 dark:text-ll-amber">★ </span>}{lead.name}</h3>
              <span className={`chip ${t.badge}`}><span className={`h-1.5 w-1.5 rounded-full ${t.dot}`} />{t.label}</span>
            </div>
            <div className="text-xs text-slate-400 dark:text-ll-txt3">{lead.city} · {lead.age} yrs · {lead.gender} · rank #{lead.rank}</div>
          </div>
          <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:text-ll-txt3 dark:hover:bg-white/[0.06] dark:hover:text-ll-txt">✕</button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto thin-scroll">
          <div className="grid grid-cols-2 gap-3 p-4">
            <Stat label="Suggested product" value={lead.suggested_product} accent="text-idbi-green dark:text-ll-green" />
            <Stat label="Best time to call" value={lead.best_time_to_contact} />
            <Stat label="Conversion (if contacted)" value={pct(lead.conversion_prob)} />
            <Stat label="Uplift" value={signedPct(lead.uplift_score)} accent={lead.uplift_score > 0 ? "text-emerald-600 dark:text-ll-green" : "text-slate-500 dark:text-ll-txt2"} />
          </div>

          <div className="mx-4 mb-4 rounded-xl border border-slate-200 bg-white/50 p-3 dark:border-white/[0.06] dark:bg-white/[0.03]">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[11px] uppercase text-slate-400 dark:text-ll-txt3">Declared</div>
                <div className="text-sm font-semibold text-slate-500 line-through dark:text-ll-txt3">{inr(lead.declared_income)}</div>
              </div>
              <div className="text-lg text-idbi-green dark:text-ll-green">→</div>
              <div className="text-right">
                <div className="text-[11px] uppercase text-idbi-greenDark dark:text-ll-green">Inferred (real)</div>
                <div className="text-sm font-bold text-idbi-green dark:text-ll-green">{inr(lead.estimated_income)}</div>
              </div>
              <div className="rounded-md bg-idbi-green px-2 py-1 text-xs font-bold text-white dark:bg-ll-green dark:text-[#062015]">{gap.toFixed(1)}×</div>
            </div>
            <div className="mt-2 flex justify-between text-[11px] text-slate-400 dark:text-ll-txt3">
              <span>Max affordable EMI: {inr(lead.max_affordable_emi)}</span>
              <span>Default risk: {pct(lead.default_risk, 1)}</span>
            </div>
          </div>

          <div className="px-4 pb-4">
            <div className="text-[11px] uppercase tracking-wide text-slate-400 dark:text-ll-txt3">Why this lead</div>
            <ul className="mt-1.5 space-y-1.5">
              {lead.reason_codes?.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700 dark:text-ll-txt2"><span className="mt-0.5 text-idbi-green dark:text-ll-green">✓</span>{r}</li>
              ))}
            </ul>
          </div>

          {lead.offer && (
            <div className="m-4 rounded-xl bg-idbi-greenLight p-4 dark:bg-ll-green/[0.08] dark:ring-1 dark:ring-ll-green/15">
              <div className="flex items-center justify-between">
                <div className="text-[11px] font-medium uppercase tracking-wide text-idbi-greenDark dark:text-ll-green">Pre-approved offer</div>
                <span className="chip bg-white text-idbi-green ring-1 ring-idbi-green/20 dark:bg-white/10 dark:text-ll-green dark:ring-ll-green/25">{lead.offer.product}</span>
              </div>
              <div className="mt-1 text-2xl font-bold text-idbi-greenDark dark:text-ll-green">{inr(lead.offer.amount)}</div>
              <div className="mt-1 grid grid-cols-3 gap-2 text-xs text-slate-600 dark:text-ll-txt2">
                <div>EMI <b className="dark:text-ll-txt">{inr(lead.offer.emi)}</b>/mo</div>
                <div>Rate <b className="dark:text-ll-txt">{lead.offer.indicative_rate}%</b></div>
                <div>Tenor <b className="dark:text-ll-txt">{lead.offer.tenor_years}y</b></div>
              </div>
              {extended ? (
                <div className="mt-3 rounded-lg bg-white px-3 py-2 text-xs text-emerald-700 ring-1 ring-emerald-200 dark:bg-white/[0.06] dark:text-ll-green dark:ring-ll-green/25">✓ Offer sent over OCEN · <b>{extended}</b> <span className="text-slate-400 dark:text-ll-txt3">(mock)</span></div>
              ) : (
                <button onClick={extend} disabled={busy} className="mt-3 w-full rounded-lg bg-idbi-green py-2 text-sm font-medium text-white hover:bg-idbi-greenDark disabled:opacity-50 dark:bg-gradient-to-r dark:from-ll-green dark:to-emerald-500 dark:text-[#062015]">{busy ? "Sending…" : "Extend offer"} <span className="opacity-70">(mock)</span></button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
