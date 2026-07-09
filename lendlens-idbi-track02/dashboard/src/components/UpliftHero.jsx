import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { pct } from "../format";

function useDark() {
  return typeof document !== "undefined" && document.documentElement.classList.contains("dark");
}

export default function UpliftHero({ portfolio, leads }) {
  const dark = useDark();
  const surfaced = leads.filter((l) => l.tier !== "SUPPRESSED");
  const avgConv = surfaced.length ? surfaced.reduce((a, l) => a + (l.conversion_prob || 0), 0) / surfaced.length : 0;

  const data = (portfolio.uplift_curve || []).map((d) => ({
    decile: `D${d.decile}`,
    uplift: +(d.observed_uplift * 100).toFixed(1),
    top: d.decile <= 3,
  }));
  const ate = (portfolio.uplift_ate || 0) * 100;
  const axisTick = { fontSize: 11, fill: dark ? "#8b909e" : "#64748b" };

  return (
    <div className="glass p-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-[15.5px] font-bold tracking-tight text-slate-800 dark:text-ll-txt">Persuasion lift by decile</h3>
          <p className="mt-0.5 text-xs text-slate-400 dark:text-ll-txt3">Uplift model — who a call actually converts</p>
        </div>
        <div className="flex gap-4 text-[11px]">
          <span className="flex items-center gap-1.5 text-slate-500 dark:text-ll-txt2"><i className="h-2 w-2 rounded-[3px] bg-ll-green" />Persuadable</span>
          <span className="flex items-center gap-1.5 text-slate-500 dark:text-ll-txt2"><i className="h-2 w-2 rounded-[3px]" style={{ background: dark ? "#3f4452" : "#cbd5e1" }} />Lower lift</span>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2.5">
        <Chip label="Surfaced leads" value={portfolio.surfaced?.toLocaleString("en-IN")} tone="green" />
        <Chip label="Avg conversion" value={pct(avgConv)} />
        <Chip label="Qini" value={portfolio.uplift_qini?.toFixed(3) ?? "—"} />
        <Chip label="ATE" value={`${ate.toFixed(1)}%`} />
      </div>

      <div className="mt-3 h-[210px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 6, left: -20, bottom: 0 }}>
            <XAxis dataKey="decile" tick={axisTick} axisLine={false} tickLine={false} />
            <YAxis tick={axisTick} axisLine={false} tickLine={false} unit="%" />
            <Tooltip
              cursor={{ fill: dark ? "rgba(255,255,255,.04)" : "#f1f5f9" }}
              contentStyle={{ background: dark ? "rgba(18,20,28,.95)" : "#fff", border: "1px solid rgba(120,120,140,.2)", borderRadius: 10, fontSize: 12 }}
              formatter={(v) => [`${v}%`, "observed uplift"]}
            />
            <ReferenceLine y={ate} stroke={dark ? "#ff5f6d" : "#b03030"} strokeDasharray="4 3" />
            <Bar dataKey="uplift" radius={[4, 4, 0, 0]}>
              {data.map((d, i) => <Cell key={i} fill={d.top ? "url(#gGreen)" : (dark ? "#3f4452" : "#cbd5e1")} />)}
            </Bar>
            <defs>
              <linearGradient id="gGreen" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#5bf0a3" /><stop offset="1" stopColor="#26b56f" />
              </linearGradient>
            </defs>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-1 text-[11px] text-slate-400 dark:text-ll-txt3">Dashed line = average treatment effect ({ate.toFixed(1)}%). Top-3 deciles drive most incremental conversions.</div>
    </div>
  );
}

function Chip({ label, value, tone }) {
  return (
    <div className="rounded-[11px] border border-slate-200 bg-white/50 px-3 py-2 backdrop-blur dark:border-white/[0.06] dark:bg-white/[0.03]">
      <div className="text-[10.5px] text-slate-400 dark:text-ll-txt3">{label}</div>
      <div className={`text-[15px] font-bold tracking-tight ${tone === "green" ? "text-idbi-green dark:text-ll-green" : "text-slate-800 dark:text-ll-txt"}`}>{value}</div>
    </div>
  );
}
