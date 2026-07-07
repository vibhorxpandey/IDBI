import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PRODUCT_COLOR, TIER, TIER_ORDER } from "../theme";

function Panel({ title, subtitle, children }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export default function PortfolioPanel({ portfolio }) {
  const tierData = TIER_ORDER.map((t) => ({
    name: TIER[t].label,
    count: portfolio.by_tier?.[t] || 0,
    fill: TIER[t].bar,
  }));

  const productData = Object.entries(portfolio.by_product || {}).map(([name, value]) => ({
    name,
    value,
    fill: PRODUCT_COLOR[name] || "#64748b",
  }));

  const upliftData = (portfolio.uplift_curve || []).map((d) => ({
    decile: d.decile,
    uplift: +(d.observed_uplift * 100).toFixed(1),
  }));
  const ate = (portfolio.uplift_ate || 0) * 100;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <Panel title="Leads by tier" subtitle="Gold first; suppressed hidden from RMs">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={tierData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
            <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip cursor={{ fill: "#f1f5f9" }} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {tierData.map((d, i) => (
                <Cell key={i} fill={d.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Panel>

      <Panel title="Leads by product" subtitle="Suggested product mix (surfaced)">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={productData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={80}
              paddingAngle={2}
            >
              {productData.map((d, i) => (
                <Cell key={i} fill={d.fill} />
              ))}
            </Pie>
            <Tooltip />
            <Legend iconType="circle" wrapperStyle={{ fontSize: 11 }} />
          </PieChart>
        </ResponsiveContainer>
      </Panel>

      <Panel
        title="Uplift by decile"
        subtitle={`Top decile = most persuadable · Qini ${portfolio.uplift_qini ?? "—"}`}
      >
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={upliftData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
            <XAxis dataKey="decile" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
            <Tooltip cursor={{ fill: "#f1f5f9" }} formatter={(v) => [`${v}%`, "observed uplift"]} />
            <ReferenceLine y={ate} stroke="#b03030" strokeDasharray="4 3" />
            <Bar dataKey="uplift" radius={[4, 4, 0, 0]}>
              {upliftData.map((d, i) => (
                <Cell key={i} fill={d.decile === 1 ? "#0b6b3a" : d.decile <= 3 ? "#2e8b57" : "#9bbcae"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-1 text-[11px] text-slate-400">
          Dashed line = overall avg treatment effect ({ate.toFixed(1)}%)
        </div>
      </Panel>
    </div>
  );
}
