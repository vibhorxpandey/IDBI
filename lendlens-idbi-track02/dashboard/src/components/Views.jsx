// Route views for the sidebar nav. Each is built from the live API data
// (leads / portfolio / fairness) so every sidebar button lands on real content.
import UpliftHero from "./UpliftHero";
import { PRODUCT_COLOR, TIER } from "../theme";
import { inr, inrShort, pct, signedPct } from "../format";

const avg = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
const median = (a) => {
  if (!a.length) return 0;
  const s = [...a].sort((x, y) => x - y);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};

function Panel({ title, subtitle, right, children }) {
  return (
    <div className="glass p-5">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-[15.5px] font-bold tracking-tight text-slate-800 dark:text-ll-txt">{title}</h3>
          {subtitle && <p className="mt-0.5 text-xs text-slate-400 dark:text-ll-txt3">{subtitle}</p>}
        </div>
        {right}
      </div>
      {children}
    </div>
  );
}

function StatChips({ items }) {
  return (
    <div className="flex flex-wrap gap-2.5">
      {items.map((it) => (
        <div key={it.label} className="min-w-[120px] flex-1 rounded-[13px] border border-slate-200 bg-white/50 px-3.5 py-2.5 dark:border-white/[0.06] dark:bg-white/[0.03]">
          <div className="text-[10.5px] text-slate-400 dark:text-ll-txt3">{it.label}</div>
          <div className={`text-[17px] font-extrabold tracking-tight ${it.tone === "green" ? "text-idbi-green dark:text-ll-green" : "text-slate-800 dark:text-ll-txt"}`}>{it.value}</div>
        </div>
      ))}
    </div>
  );
}

function TierPill({ tier }) {
  const t = TIER[tier] || TIER.BRONZE;
  return <span className={`chip ${t.badge}`}><span className={`h-1.5 w-1.5 rounded-full ${t.dot}`} />{t.label}</span>;
}

function Table({ columns, rows, onRowClick }) {
  return (
    <div className="overflow-x-auto thin-scroll">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="text-[10.5px] uppercase tracking-wide text-slate-400 dark:text-ll-txt3">
            {columns.map((c) => (
              <th key={c.key} className={`pb-2 font-medium ${c.align === "right" ? "text-right" : "text-left"}`}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.customer_id || i} onClick={() => onRowClick?.(r)}
              className="cursor-pointer border-t border-slate-100 hover:bg-slate-50 dark:border-white/[0.05] dark:hover:bg-white/[0.03]">
              {columns.map((c) => (
                <td key={c.key} className={`py-2 ${c.align === "right" ? "text-right" : "text-left"} text-slate-700 dark:text-ll-txt2`}>
                  {c.render ? c.render(r) : r[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NameCell({ l }) {
  return (
    <div className="min-w-0">
      <div className="truncate font-medium text-slate-800 dark:text-ll-txt">
        {l.customer_id === "CUST_PRIYA" && <span className="text-amber-500 dark:text-ll-amber">★ </span>}{l.name}
      </div>
      <div className="truncate text-[11px] text-slate-400 dark:text-ll-txt3">{l.city}</div>
    </div>
  );
}

function ViewWrap({ children }) {
  return <div className="animate-fade-up flex flex-col gap-5">{children}</div>;
}

/* ------------------------------------------------------------------ Income */
export function IncomeView({ leads, onSelect }) {
  const rows = leads.map((l) => ({ ...l, mult: l.declared_income ? l.estimated_income / l.declared_income : 1 }));
  const unlocked = rows.filter((l) => l.estimated_income > l.declared_income * 1.1).length;
  const top = [...rows].sort((a, b) => b.mult - a.mult).slice(0, 14);
  return (
    <ViewWrap>
      <Panel title="Income & Repayment Engine" subtitle="Real income recovered from transactions — declared income is understated for gig / self-employed">
        <StatChips items={[
          { label: "Customers analysed", value: leads.length.toLocaleString("en-IN") },
          { label: "Median inferred income", value: inr(median(leads.map((l) => l.estimated_income))), tone: "green" },
          { label: "Income unlocked (>1.1×)", value: unlocked.toLocaleString("en-IN") },
          { label: "Avg income confidence", value: pct(avg(leads.map((l) => l.income_confidence || 0))) },
          { label: "FOIR cap", value: "50%" },
        ]} />
      </Panel>
      <Panel title="Biggest declared → inferred income gaps" subtitle="Where the ledger tells a very different story from the form">
        <Table onRowClick={onSelect}
          columns={[
            { key: "name", label: "Customer", render: (l) => <NameCell l={l} /> },
            { key: "declared_income", label: "Declared", align: "right", render: (l) => <span className="text-slate-400 line-through dark:text-ll-txt3">{inr(l.declared_income)}</span> },
            { key: "estimated_income", label: "Inferred", align: "right", render: (l) => <b className="text-idbi-green dark:text-ll-green">{inr(l.estimated_income)}</b> },
            { key: "mult", label: "×", align: "right", render: (l) => <span className="font-semibold">{l.mult.toFixed(1)}×</span> },
            { key: "max_affordable_emi", label: "Max EMI", align: "right", render: (l) => inr(l.max_affordable_emi) },
            { key: "tier", label: "Tier", align: "right", render: (l) => <TierPill tier={l.tier} /> },
          ]}
          rows={top} />
      </Panel>
    </ViewWrap>
  );
}

/* ------------------------------------------------------------------ Intent */
export function IntentView({ leads, portfolio, onSelect }) {
  const persuadables = [...leads].filter((l) => l.tier !== "SUPPRESSED").sort((a, b) => b.uplift_score - a.uplift_score).slice(0, 14);
  return (
    <ViewWrap>
      <UpliftHero portfolio={portfolio} leads={leads} />
      <Panel title="Top persuadables" subtitle="Highest uplift — a call here actually causes the conversion">
        <Table onRowClick={onSelect}
          columns={[
            { key: "name", label: "Customer", render: (l) => <NameCell l={l} /> },
            { key: "suggested_product", label: "Product", render: (l) => l.suggested_product },
            { key: "conversion_prob", label: "Conv.", align: "right", render: (l) => pct(l.conversion_prob) },
            { key: "uplift_score", label: "Uplift", align: "right", render: (l) => <b className="text-emerald-600 dark:text-ll-green">{signedPct(l.uplift_score)}</b> },
            { key: "best_time_to_contact", label: "Best time", align: "right", render: (l) => <span className="text-[12px]">{l.best_time_to_contact}</span> },
          ]}
          rows={persuadables} />
      </Panel>
    </ViewWrap>
  );
}

/* ------------------------------------------------------------------ Offers */
export function OffersView({ leads, portfolio, onSelect }) {
  const offered = leads.filter((l) => l.offer);
  const valByProduct = {};
  for (const l of offered) valByProduct[l.offer.product] = (valByProduct[l.offer.product] || 0) + l.offer.amount;
  const top = [...offered].sort((a, b) => b.offer.amount - a.offer.amount).slice(0, 15);
  return (
    <ViewWrap>
      <Panel title="Pre-approved Offers" subtitle="Back-solved from max affordable EMI, capped by a conservative income multiple">
        <StatChips items={[
          { label: "Total pre-approved value", value: inrShort(portfolio.total_offer_value), tone: "green" },
          { label: "Offers built", value: offered.length.toLocaleString("en-IN") },
          { label: "Avg offer", value: inrShort(avg(offered.map((l) => l.offer.amount))) },
          { label: "Largest offer", value: inrShort(Math.max(...offered.map((l) => l.offer.amount))) },
        ]} />
        <div className="mt-4 flex flex-wrap gap-2">
          {Object.entries(valByProduct).sort((a, b) => b[1] - a[1]).map(([p, v]) => (
            <div key={p} className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-[12px] dark:border-white/[0.08]">
              <i className="h-2.5 w-2.5 rounded-full" style={{ background: PRODUCT_COLOR[p] || "#64748b" }} />
              <span className="text-slate-500 dark:text-ll-txt2">{p}</span>
              <b className="text-slate-800 dark:text-ll-txt">{inrShort(v)}</b>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Largest pre-approved offers">
        <Table onRowClick={onSelect}
          columns={[
            { key: "name", label: "Customer", render: (l) => <NameCell l={l} /> },
            { key: "product", label: "Product", render: (l) => <span className="inline-flex items-center gap-1.5"><i className="h-2 w-2 rounded-full" style={{ background: PRODUCT_COLOR[l.offer.product] || "#64748b" }} />{l.offer.product}</span> },
            { key: "amount", label: "Amount", align: "right", render: (l) => <b className="text-slate-800 dark:text-ll-txt">{inr(l.offer.amount)}</b> },
            { key: "emi", label: "EMI/mo", align: "right", render: (l) => inr(l.offer.emi) },
            { key: "rate", label: "Rate", align: "right", render: (l) => `${l.offer.indicative_rate}%` },
            { key: "tenor", label: "Tenor", align: "right", render: (l) => `${l.offer.tenor_years}y` },
          ]}
          rows={top} />
      </Panel>
    </ViewWrap>
  );
}

/* ---------------------------------------------------------- Explainability */
export function ExplainView({ leads, onSelect }) {
  const freq = {};
  for (const l of leads) for (const r of l.reason_codes || []) freq[r] = (freq[r] || 0) + 1;
  const top = Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 12);
  const max = top.length ? top[0][1] : 1;
  const sample = leads.filter((l) => l.tier === "GOLD").slice(0, 10);
  return (
    <ViewWrap>
      <Panel title="Explainability" subtitle="Every lead carries 3 plain-English reasons — hybrid: detected intent/life-events + SHAP-ranked affordability drivers">
        <div className="space-y-2">
          {top.map(([reason, n]) => (
            <div key={reason} className="flex items-center gap-3">
              <div className="w-56 shrink-0 truncate text-[12.5px] text-slate-600 dark:text-ll-txt2">{reason}</div>
              <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-white/[0.05]">
                <div className="h-full rounded-full bg-gradient-to-r from-idbi-green to-emerald-400 dark:from-ll-green dark:to-emerald-400" style={{ width: `${(n / max) * 100}%` }} />
              </div>
              <div className="w-12 shrink-0 text-right text-[12px] font-semibold text-slate-500 dark:text-ll-txt3">{n.toLocaleString("en-IN")}</div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Sample Gold leads & their reasons" subtitle="Click a row for the full RM card">
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          {sample.map((l) => (
            <button key={l.customer_id} onClick={() => onSelect?.(l)}
              className="glass-hover rounded-xl border border-slate-200 p-3 text-left dark:border-white/[0.06]">
              <div className="flex items-center justify-between">
                <div className="font-medium text-slate-800 dark:text-ll-txt">{l.customer_id === "CUST_PRIYA" && <span className="text-amber-500 dark:text-ll-amber">★ </span>}{l.name}</div>
                <span className="text-[11px] text-slate-400 dark:text-ll-txt3">{l.suggested_product}</span>
              </div>
              <ul className="mt-1.5 space-y-1">
                {(l.reason_codes || []).map((r, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-[12px] text-slate-600 dark:text-ll-txt2"><span className="mt-0.5 text-idbi-green dark:text-ll-green">✓</span>{r}</li>
                ))}
              </ul>
            </button>
          ))}
        </div>
      </Panel>
    </ViewWrap>
  );
}

/* ---------------------------------------------------------------- Fairness */
export function FairnessView({ fairness }) {
  const rates = fairness.group_selection_rates || {};
  const groups = Object.entries(rates);
  const maxRate = groups.length ? Math.max(...groups.map(([, v]) => v)) : 1;
  const passes = fairness.passes;
  return (
    <ViewWrap>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_1.4fr]">
        <Panel title="80% (four-fifths) rule" subtitle={`Protected attribute: ${fairness.protected_attribute || "gender"}`}>
          <div className="flex flex-col items-center py-4">
            <div className={`text-[54px] font-extrabold leading-none tracking-tight ${passes ? "text-idbi-green dark:text-ll-green" : "text-rose-600 dark:text-ll-red"}`}>
              {fairness.disparate_impact_ratio?.toFixed(2)}
            </div>
            <div className="mt-1 text-xs text-slate-400 dark:text-ll-txt3">disparate-impact ratio</div>
            <div className={`mt-3 inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ring-1 ${passes ? "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-ll-green/10 dark:text-ll-green dark:ring-ll-green/25" : "bg-rose-50 text-rose-700 ring-rose-200 dark:bg-ll-red/10 dark:text-ll-red dark:ring-ll-red/25"}`}>
              {passes ? "PASSES" : "FAILS"} · threshold {(fairness.threshold ?? 0.8) * 100}%
            </div>
          </div>
        </Panel>
        <Panel title="Selection rate by group" subtitle={`${fairness.n_selected?.toLocaleString("en-IN") ?? "—"} selected of ${fairness.n_total?.toLocaleString("en-IN") ?? "—"}`}>
          <div className="space-y-4 py-2">
            {groups.map(([g, r]) => (
              <div key={g}>
                <div className="mb-1 flex justify-between text-[12.5px]">
                  <span className="text-slate-600 dark:text-ll-txt2">Group {g}</span>
                  <b className="text-slate-800 dark:text-ll-txt">{pct(r, 1)}</b>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-white/[0.05]">
                  <div className="h-full rounded-full bg-gradient-to-r from-ll-blue to-indigo-400" style={{ width: `${(r / maxRate) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[12px] text-slate-500 dark:text-ll-txt3">
            The four-fifths rule requires the least-selected group's rate to be ≥ 80% of the most-selected group's. Ratio ={" "}
            <b>{fairness.disparate_impact_ratio?.toFixed(3)}</b> — {passes ? "no adverse impact detected" : "adverse impact — thresholds would be rebalanced"}.
          </p>
        </Panel>
      </div>
    </ViewWrap>
  );
}

/* ---------------------------------------------------------------- Settings */
export function SettingsView({ apiBase, fairness, notify }) {
  const guards = [
    { label: "FOIR cap", value: "50%", note: "max EMI / income — never exceeded" },
    { label: "Fairness (80% rule)", value: `${(fairness?.threshold ?? 0.8) * 100}%`, note: "disparate-impact minimum" },
    { label: "Uplift suppression", value: "< 0.02", note: "leads below cutoff are hidden" },
    { label: "Random seed", value: "42", note: "byte-reproducible leads.json" },
  ];
  const rails = ["Account Aggregator (consent + fetch)", "ULI (borrower data)", "OCEN (offer handoff)"];
  return (
    <ViewWrap>
      <Panel title="Guard-rails" subtitle="Hard-coded & visible — from config.py">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {guards.map((g) => (
            <div key={g.label} className="rounded-[13px] border border-slate-200 p-3.5 dark:border-white/[0.06] dark:bg-white/[0.02]">
              <div className="text-[11px] text-slate-400 dark:text-ll-txt3">{g.label}</div>
              <div className="text-[20px] font-extrabold tracking-tight text-idbi-green dark:text-ll-green">{g.value}</div>
              <div className="mt-0.5 text-[10.5px] text-slate-400 dark:text-ll-txt3">{g.note}</div>
            </div>
          ))}
        </div>
      </Panel>
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <Panel title="Integration rails" subtitle="Round-1: simulated & clearly labelled">
          <ul className="space-y-2">
            {rails.map((r) => (
              <li key={r} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-[13px] dark:border-white/[0.06]">
                <span className="text-slate-600 dark:text-ll-txt2">{r}</span>
                <span className="chip bg-amber-100 text-amber-800 ring-1 ring-amber-300 dark:bg-ll-amber/10 dark:text-ll-amber dark:ring-ll-amber/25">MOCK</span>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="Environment">
          <div className="space-y-2 text-[13px]">
            <div className="flex justify-between"><span className="text-slate-500 dark:text-ll-txt3">API base</span><b className="text-slate-800 dark:text-ll-txt">{apiBase}</b></div>
            <div className="flex justify-between"><span className="text-slate-500 dark:text-ll-txt3">Determinism</span><b className="text-slate-800 dark:text-ll-txt">seed 42</b></div>
            <div className="flex justify-between"><span className="text-slate-500 dark:text-ll-txt3">Fraud detection</span><b className="text-slate-800 dark:text-ll-txt">downstream (out of scope)</b></div>
          </div>
          <button onClick={() => notify?.("Pipeline is deterministic — re-run `python run_all.py`", "info")}
            className="mt-4 w-full rounded-xl bg-idbi-green py-2.5 text-[13px] font-semibold text-white hover:bg-idbi-greenDark dark:bg-gradient-to-r dark:from-ll-blue dark:to-indigo-500">
            Re-run pipeline (mock)
          </button>
        </Panel>
      </div>
    </ViewWrap>
  );
}
