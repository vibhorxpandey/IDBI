import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import UpliftHero from "./components/UpliftHero";
import PreApprovedCard from "./components/PreApprovedCard";
import LeadQueueTable from "./components/LeadQueueTable";
import BreakdownPanel from "./components/BreakdownPanel";
import LeadDetailModal from "./components/LeadDetailModal";
import ConsentFlow from "./components/ConsentFlow";
import Toast from "./components/Toast";
import { IncomeView, IntentView, OffersView, ExplainView, FairnessView, SettingsView } from "./components/Views";

function useTheme() {
  const [dark, setDark] = useState(() => {
    const s = localStorage.getItem("ll-theme");
    return s ? s === "dark" : true;
  });
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("ll-theme", dark ? "dark" : "light");
  }, [dark]);
  return [dark, setDark];
}

function Screen({ children }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="glass max-w-md p-6 text-center">{children}</div>
    </div>
  );
}

export default function App() {
  const [dark, setDark] = useTheme();
  const [leads, setLeads] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [fairness, setFairness] = useState(null);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [showConsent, setShowConsent] = useState(true);
  const [active, setActive] = useState("dashboard");
  const [query, setQuery] = useState("");
  const [toast, setToast] = useState(null);

  const notify = (msg, tone = "info") => setToast({ msg, tone, id: Date.now() });

  useEffect(() => {
    Promise.all([api.leads({ include_suppressed: true }), api.portfolio(), api.fairness()])
      .then(([l, p, f]) => { setLeads(l); setPortfolio(p); setFairness(f); })
      .catch((e) => setError(e.message));
  }, []);

  const jumpPriya = () => {
    const p = leads?.find((l) => l.customer_id === "CUST_PRIYA");
    if (p) setSelected(p); else notify("Priya not found in this dataset", "warn");
  };

  if (error) {
    return (
      <Screen>
        <div className="text-3xl">🔌</div>
        <h1 className="mt-2 text-lg font-semibold text-slate-800 dark:text-ll-txt">Can’t reach the LendLens API</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-ll-txt2">{error}</p>
        <div className="mt-4 rounded-lg bg-slate-50 p-3 text-left text-xs text-slate-600 dark:bg-white/[0.04] dark:text-ll-txt2">
          Start the backend, then reload:
          <pre className="mt-1 whitespace-pre-wrap font-mono text-[11px]">uvicorn api.main:app --port 8000</pre>
          <div className="mt-1 text-slate-400 dark:text-ll-txt3">API base: {api.base}</div>
        </div>
      </Screen>
    );
  }

  if (!leads || !portfolio || !fairness) {
    return (
      <Screen>
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-idbi-green dark:border-white/10 dark:border-t-ll-blue" />
        <p className="mt-3 text-sm text-slate-500 dark:text-ll-txt2">Loading leads…</p>
      </Screen>
    );
  }

  return (
    <div className="min-h-screen">
      {showConsent && <ConsentFlow onClose={() => setShowConsent(false)} />}
      {selected && <LeadDetailModal lead={selected} onClose={() => setSelected(null)} notify={notify} />}
      <Toast toast={toast} onDone={() => setToast(null)} />

      <div className="mx-auto flex min-h-screen max-w-[1240px] gap-4 p-4 lg:p-6">
        <Sidebar active={active} setActive={setActive} notify={notify} />

        <main className="flex min-w-0 flex-1 flex-col gap-5">
          <Topbar dark={dark} setDark={setDark} fairness={fairness} query={query} setQuery={setQuery} onReplay={() => setShowConsent(true)} notify={notify} />

          {active === "dashboard" && (
            <>
              {/* row 1: hero + pre-approved card */}
              <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.65fr_1fr]">
                <UpliftHero portfolio={portfolio} leads={leads} />
                <PreApprovedCard portfolio={portfolio} onReplay={() => setShowConsent(true)} onBatch={() => notify("Batch scoring queued — 5,001 customers", "info")} />
              </div>
              {/* row 2: queue + breakdown */}
              <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.65fr_1fr]">
                <LeadQueueTable leads={leads} query={query} onSelect={setSelected} selectedId={selected?.customer_id} onJumpPriya={jumpPriya} />
                <BreakdownPanel portfolio={portfolio} leads={leads} />
              </div>
            </>
          )}

          {active === "queue" && (
            <LeadQueueTable leads={leads} query={query} onSelect={setSelected} selectedId={selected?.customer_id} onJumpPriya={jumpPriya} />
          )}
          {active === "income" && <IncomeView leads={leads} onSelect={setSelected} />}
          {active === "intent" && <IntentView leads={leads} portfolio={portfolio} onSelect={setSelected} />}
          {active === "offers" && <OffersView leads={leads} portfolio={portfolio} onSelect={setSelected} />}
          {active === "explain" && <ExplainView leads={leads} onSelect={setSelected} />}
          {active === "fairness" && <FairnessView fairness={fairness} />}
          {active === "settings" && <SettingsView apiBase={api.base} fairness={fairness} notify={notify} />}

          <div className="pb-1 text-center text-[11px] text-slate-400 dark:text-ll-txt3">
            LendLens · Round-1 prototype · AA / ULI / OCEN rails are <b>simulated</b> and clearly labelled · deterministic (seed 42).
          </div>
        </main>
      </div>
    </div>
  );
}
