import { useMemo, useState } from "react";
import { TIER } from "../theme";
import { inrShort, pct, signedPct } from "../format";

const FILTERS = [
  { key: "ALL", label: "All" },
  { key: "GOLD", label: "Gold" },
  { key: "SILVER", label: "Silver" },
  { key: "BRONZE", label: "Bronze" },
];
const SORTS = [
  { key: "rank", label: "Rank" },
  { key: "conversion_prob", label: "Conversion" },
  { key: "uplift_score", label: "Uplift" },
  { key: "offer", label: "Offer" },
];

function TierPill({ tier }) {
  const t = TIER[tier];
  return <span className={`chip ${t.badge}`}><span className={`h-1.5 w-1.5 rounded-full ${t.dot}`} />{t.label}</span>;
}

export default function LeadQueueTable({ leads, query, onSelect, selectedId, onJumpPriya }) {
  const [filter, setFilter] = useState("ALL");
  const [sort, setSort] = useState("rank");
  const [showSuppressed, setShowSuppressed] = useState(false);

  const rows = useMemo(() => {
    let r = leads.filter((l) => (showSuppressed ? true : l.tier !== "SUPPRESSED"));
    if (filter !== "ALL") r = r.filter((l) => l.tier === filter);
    const q = query.trim().toLowerCase();
    if (q) r = r.filter((l) => l.name.toLowerCase().includes(q) || l.city.toLowerCase().includes(q) || l.customer_id.toLowerCase().includes(q));
    const val = (l) => (sort === "offer" ? l.offer?.amount || 0 : l[sort]);
    r = [...r].sort((a, b) => (sort === "rank" ? a.rank - b.rank : val(b) - val(a)));
    return r.slice(0, 60);
  }, [leads, filter, sort, query, showSuppressed]);

  return (
    <div className="glass flex flex-col p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-[15.5px] font-bold tracking-tight text-slate-800 dark:text-ll-txt">Lead queue</h3>
          <p className="mt-0.5 text-xs text-slate-400 dark:text-ll-txt3">Ranked by composite score · {rows.length} shown</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onJumpPriya} className="rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs font-medium text-amber-700 ring-1 ring-amber-200 hover:bg-amber-100 dark:bg-ll-amber/10 dark:text-ll-amber dark:ring-ll-amber/25 dark:hover:bg-ll-amber/20">★ Demo: Priya</button>
        </div>
      </div>

      {/* controls */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <div className="flex rounded-[10px] border border-slate-200 bg-white/50 p-0.5 backdrop-blur dark:border-white/[0.07] dark:bg-white/[0.03]">
          {FILTERS.map((f) => (
            <button key={f.key} onClick={() => setFilter(f.key)}
              className={`rounded-[8px] px-2.5 py-1.5 text-xs font-medium transition ${filter === f.key ? "bg-slate-800 text-white dark:bg-white/[0.12] dark:text-ll-txt" : "text-slate-500 hover:text-slate-800 dark:text-ll-txt2 dark:hover:text-ll-txt"}`}>{f.label}</button>
          ))}
        </div>
        <div className="flex items-center gap-1.5 rounded-[10px] border border-slate-200 bg-white/50 px-2.5 py-1.5 backdrop-blur dark:border-white/[0.07] dark:bg-white/[0.03]">
          <span className="text-[11px] text-slate-400 dark:text-ll-txt3">Sort</span>
          <select value={sort} onChange={(e) => setSort(e.target.value)} className="bg-transparent text-xs font-medium text-slate-700 outline-none dark:text-ll-txt [&>option]:text-slate-800">
            {SORTS.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
          </select>
        </div>
        <label className="ml-auto flex cursor-pointer select-none items-center gap-2 text-xs text-slate-500 dark:text-ll-txt2">
          <input type="checkbox" checked={showSuppressed} onChange={(e) => setShowSuppressed(e.target.checked)} className="h-3.5 w-3.5 accent-idbi-green dark:accent-ll-blue" />Show suppressed
        </label>
      </div>

      {/* header */}
      <div className="mt-3 grid grid-cols-12 gap-2 border-b border-slate-100 px-2 pb-2 text-[11px] font-medium uppercase tracking-wide text-slate-400 dark:border-white/[0.06] dark:text-ll-txt3">
        <div className="col-span-5">Customer</div>
        <div className="col-span-2">Product</div>
        <div className="col-span-2 text-right">Conv.</div>
        <div className="col-span-1 text-right">Uplift</div>
        <div className="col-span-2 text-right">Offer</div>
      </div>

      <div className="thin-scroll max-h-[420px] overflow-y-auto">
        {rows.map((l) => (
          <button key={l.customer_id} onClick={() => onSelect(l)}
            className={`grid w-full grid-cols-12 items-center gap-2 rounded-[10px] px-2 py-2.5 text-left text-sm transition ${TIER[l.tier].row} ${selectedId === l.customer_id ? "bg-idbi-greenLight ring-1 ring-inset ring-idbi-green/30 dark:bg-white/[0.06] dark:ring-white/10" : ""}`}>
            <div className="col-span-5 flex min-w-0 items-center gap-2.5">
              <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-[10px] text-[11px] font-bold ${TIER[l.tier].badge}`}>{l.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}</span>
              <div className="min-w-0">
                <div className="truncate font-medium text-slate-800 dark:text-ll-txt">{l.customer_id === "CUST_PRIYA" && <span className="text-amber-500 dark:text-ll-amber">★ </span>}{l.name}</div>
                <div className="truncate text-[11px] text-slate-400 dark:text-ll-txt3">{l.city} · <TierPillInline tier={l.tier} /></div>
              </div>
            </div>
            <div className="col-span-2 text-slate-600 dark:text-ll-txt2">{l.suggested_product}</div>
            <div className="col-span-2 text-right font-medium text-slate-700 dark:text-ll-txt">{pct(l.conversion_prob)}</div>
            <div className={`col-span-1 text-right text-xs font-medium ${l.uplift_score > 0 ? "text-emerald-600 dark:text-ll-green" : "text-slate-400 dark:text-ll-txt3"}`}>{signedPct(l.uplift_score, 0)}</div>
            <div className="col-span-2 text-right font-semibold text-slate-800 dark:text-ll-txt">{l.offer ? inrShort(l.offer.amount) : "—"}</div>
          </button>
        ))}
        {rows.length === 0 && <div className="py-10 text-center text-sm text-slate-400 dark:text-ll-txt3">No leads match your filters.</div>}
      </div>
    </div>
  );
}

function TierPillInline({ tier }) {
  const c = { GOLD: "text-amber-600 dark:text-ll-amber", SILVER: "text-slate-500 dark:text-slate-400", BRONZE: "text-orange-600 dark:text-ll-orange", SUPPRESSED: "text-slate-400 dark:text-ll-txt3" }[tier];
  return <span className={c}>{TIER[tier].label}</span>;
}
