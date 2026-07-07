import { inrShort, pct } from "../format";

function Card({ label, value, sub, accent }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${accent || "text-slate-800"}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

export default function StatCards({ portfolio, leads }) {
  const surfaced = leads.filter((l) => l.tier !== "SUPPRESSED");
  const gold = portfolio.by_tier?.GOLD ?? 0;
  const avgConv =
    surfaced.length > 0
      ? surfaced.reduce((a, l) => a + (l.conversion_prob || 0), 0) / surfaced.length
      : 0;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card
        label="Surfaced leads"
        value={portfolio.surfaced?.toLocaleString("en-IN")}
        sub={`${portfolio.suppressed?.toLocaleString("en-IN")} suppressed by uplift`}
        accent="text-idbi-green"
      />
      <Card label="Gold leads" value={gold.toLocaleString("en-IN")} sub="top-priority, call first" accent="text-amber-600" />
      <Card
        label="Pre-approved value"
        value={inrShort(portfolio.total_offer_value)}
        sub="across surfaced leads"
      />
      <Card label="Avg. conversion" value={pct(avgConv)} sub="predicted, if contacted" />
    </div>
  );
}
