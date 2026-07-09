import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { PRODUCT_COLOR, TIER, TIER_ORDER } from "../theme";
import { inrShort } from "../format";

function useDark() {
  return typeof document !== "undefined" && document.documentElement.classList.contains("dark");
}

export default function BreakdownPanel({ portfolio, leads }) {
  const dark = useDark();

  // exposure (offer value) by tier — real
  const surfaced = leads.filter((l) => l.tier !== "SUPPRESSED" && l.offer);
  const valByTier = {};
  const cntByTier = {};
  for (const l of surfaced) {
    valByTier[l.tier] = (valByTier[l.tier] || 0) + l.offer.amount;
    cntByTier[l.tier] = (cntByTier[l.tier] || 0) + 1;
  }

  const productData = Object.entries(portfolio.by_product || {}).map(([name, value]) => ({ name, value, fill: PRODUCT_COLOR[name] || "#64748b" }));
  const total = portfolio.total_offer_value || 0;

  return (
    <div className="glass p-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-[15.5px] font-bold tracking-tight text-slate-800 dark:text-ll-txt">Book breakdown</h3>
          <p className="mt-0.5 text-xs text-slate-400 dark:text-ll-txt3">Pre-approved exposure by tier & product</p>
        </div>
      </div>

      <div className="mt-2 text-[26px] font-extrabold tracking-tight text-slate-800 dark:text-ll-txt">{inrShort(total)}</div>
      <div className="text-[11px] text-slate-400 dark:text-ll-txt3">across {portfolio.surfaced?.toLocaleString("en-IN")} surfaced leads</div>

      <div className="mt-2 grid grid-cols-2 items-center gap-2">
        {/* donut: product mix */}
        <div className="h-[130px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={productData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={38} outerRadius={58} paddingAngle={2} stroke="none">
                {productData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Pie>
              <Tooltip contentStyle={{ background: dark ? "rgba(18,20,28,.95)" : "#fff", border: "1px solid rgba(120,120,140,.2)", borderRadius: 10, fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        {/* product legend */}
        <div className="flex flex-col gap-1.5">
          {productData.map((p) => (
            <div key={p.name} className="flex items-center gap-2 text-[12px]">
              <i className="h-2.5 w-2.5 rounded-full" style={{ background: p.fill }} />
              <span className="text-slate-500 dark:text-ll-txt2">{p.name}</span>
              <span className="ml-auto font-semibold text-slate-800 dark:text-ll-txt">{p.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* tier exposure rows */}
      <div className="mt-3 space-y-2 border-t border-slate-100 pt-3 dark:border-white/[0.06]">
        {TIER_ORDER.filter((t) => t !== "SUPPRESSED").map((t) => (
          <div key={t} className="flex items-center gap-2.5 text-[12.5px]">
            <i className="h-2.5 w-2.5 rounded-full" style={{ background: TIER[t].bar }} />
            <span className="text-slate-500 dark:text-ll-txt2">{TIER[t].label} risk</span>
            <span className="text-[11px] text-slate-400 dark:text-ll-txt3">{(cntByTier[t] || 0).toLocaleString("en-IN")} leads</span>
            <span className="ml-auto font-bold text-slate-800 dark:text-ll-txt">{inrShort(valByTier[t] || 0)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
