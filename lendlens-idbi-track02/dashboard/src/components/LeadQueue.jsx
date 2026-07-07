import { useMemo, useState } from "react";
import { TIER, TIER_ORDER } from "../theme";
import { inrShort, pct, signedPct } from "../format";

const COLUMNS = [
  { key: "name", label: "Customer", sortable: false, align: "left" },
  { key: "suggested_product", label: "Product", sortable: false, align: "left" },
  { key: "conversion_prob", label: "Conv.", sortable: true, align: "right" },
  { key: "uplift_score", label: "Uplift", sortable: true, align: "right" },
  { key: "offer", label: "Offer", sortable: true, align: "right" },
];

function TierBadge({ tier }) {
  const t = TIER[tier];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${t.badge}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${t.dot}`} />
      {t.label}
    </span>
  );
}

export default function LeadQueue({ leads, showSuppressed, setShowSuppressed, onSelect, selectedId, onJumpPriya }) {
  const [sort, setSort] = useState({ key: "rank", dir: "asc" });

  const groups = useMemo(() => {
    const g = { GOLD: [], SILVER: [], BRONZE: [], SUPPRESSED: [] };
    for (const l of leads) (g[l.tier] || (g[l.tier] = [])).push(l);
    const val = (l) => (sort.key === "offer" ? l.offer?.amount || 0 : l[sort.key]);
    const cmp = (a, b) => {
      if (sort.key === "rank") return a.rank - b.rank;
      const d = (val(a) - val(b)) * (sort.dir === "asc" ? 1 : -1);
      return d;
    };
    for (const k of Object.keys(g)) g[k] = [...g[k]].sort(cmp);
    return g;
  }, [leads, sort]);

  const toggleSort = (key) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "desc" }));

  const visibleTiers = TIER_ORDER.filter((t) => t !== "SUPPRESSED" || showSuppressed);
  const CAP = 40;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-800">Lead queue</h2>
          <p className="text-xs text-slate-400">Ranked by LendLens composite score</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onJumpPriya}
            className="rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs font-medium text-amber-700 ring-1 ring-amber-200 hover:bg-amber-100"
          >
            ★ Demo: Priya
          </button>
          <label className="flex items-center gap-2 text-xs text-slate-500 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showSuppressed}
              onChange={(e) => setShowSuppressed(e.target.checked)}
              className="h-3.5 w-3.5 accent-slate-400"
            />
            Show suppressed
          </label>
        </div>
      </div>

      {/* header row */}
      <div className="grid grid-cols-12 gap-2 border-b border-slate-100 px-4 py-2 text-[11px] font-medium uppercase tracking-wide text-slate-400">
        <div className="col-span-5">Customer</div>
        <div className="col-span-2">Product</div>
        <SortHead className="col-span-2 text-right" label="Conv." active={sort.key === "conversion_prob"} dir={sort.dir} onClick={() => toggleSort("conversion_prob")} />
        <SortHead className="col-span-1 text-right" label="Uplift" active={sort.key === "uplift_score"} dir={sort.dir} onClick={() => toggleSort("uplift_score")} />
        <SortHead className="col-span-2 text-right" label="Offer" active={sort.key === "offer"} dir={sort.dir} onClick={() => toggleSort("offer")} />
      </div>

      <div className="max-h-[560px] overflow-y-auto thin-scroll">
        {visibleTiers.map((tier) => {
          const rows = groups[tier] || [];
          if (rows.length === 0) return null;
          return (
            <div key={tier}>
              <div className="sticky top-0 z-10 flex items-center gap-2 bg-slate-50/95 px-4 py-1.5 backdrop-blur">
                <TierBadge tier={tier} />
                <span className="text-xs text-slate-400">{rows.length.toLocaleString("en-IN")}</span>
                {tier === "SUPPRESSED" && (
                  <span className="text-[11px] text-slate-400">· hidden — suppressed by uplift model</span>
                )}
              </div>
              {rows.slice(0, CAP).map((l) => (
                <button
                  key={l.customer_id}
                  onClick={() => onSelect(l)}
                  className={`grid w-full grid-cols-12 items-center gap-2 px-4 py-2 text-left text-sm transition ${TIER[tier].row} ${
                    selectedId === l.customer_id ? "bg-idbi-greenLight ring-1 ring-inset ring-idbi-green/30" : ""
                  }`}
                >
                  <div className="col-span-5 min-w-0">
                    <div className="truncate font-medium text-slate-800">
                      {l.customer_id === "CUST_PRIYA" && <span className="text-amber-500">★ </span>}
                      {l.name}
                    </div>
                    <div className="truncate text-xs text-slate-400">{l.city} · {l.customer_id}</div>
                  </div>
                  <div className="col-span-2 text-slate-600">{l.suggested_product}</div>
                  <div className="col-span-2 text-right font-medium text-slate-700">{pct(l.conversion_prob)}</div>
                  <div className={`col-span-1 text-right text-xs font-medium ${l.uplift_score > 0 ? "text-emerald-600" : "text-slate-400"}`}>
                    {signedPct(l.uplift_score, 0)}
                  </div>
                  <div className="col-span-2 text-right font-semibold text-slate-800">
                    {l.offer ? inrShort(l.offer.amount) : "—"}
                  </div>
                </button>
              ))}
              {rows.length > CAP && (
                <div className="px-4 py-2 text-center text-xs text-slate-400">
                  + {(rows.length - CAP).toLocaleString("en-IN")} more {TIER[tier].label} leads
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SortHead({ label, active, dir, onClick, className }) {
  return (
    <button onClick={onClick} className={`${className} hover:text-slate-600`}>
      {label}
      <span className="ml-0.5">{active ? (dir === "asc" ? "▲" : "▼") : ""}</span>
    </button>
  );
}
