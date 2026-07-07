// Small fairness indicator that reads the /fairness summary.
export default function FairnessBadge({ fairness }) {
  if (!fairness) return null;
  const ratio = fairness.disparate_impact_ratio;
  const passes = fairness.passes;
  const cls = passes
    ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
    : "bg-rose-50 text-rose-700 ring-rose-200";
  return (
    <div
      title={`Protected attribute: ${fairness.protected_attribute} · ${fairness.rule}`}
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ring-1 ${cls}`}
    >
      <span className={`h-2 w-2 rounded-full ${passes ? "bg-emerald-500" : "bg-rose-500"}`} />
      Fairness&nbsp;
      <span className="font-semibold">{passes ? "PASS" : "FAIL"}</span>
      <span className="opacity-70">·</span>
      <span>DI {ratio?.toFixed(2)}</span>
      <span className="opacity-70 hidden sm:inline">· 80% rule</span>
    </div>
  );
}
