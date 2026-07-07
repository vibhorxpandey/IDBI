import { useEffect, useState } from "react";
import { api } from "./api";
import ConsentFlow from "./components/ConsentFlow";
import FairnessBadge from "./components/FairnessBadge";
import LeadDetail from "./components/LeadDetail";
import LeadQueue from "./components/LeadQueue";
import PortfolioPanel from "./components/PortfolioPanel";
import StatCards from "./components/StatCards";

function Header({ fairness, onReplay }) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-idbi-green font-bold text-white">
            L
          </div>
          <div>
            <div className="text-sm font-bold leading-tight text-slate-800">
              LendLens <span className="font-normal text-slate-400">· RM Console</span>
            </div>
            <div className="text-[11px] text-slate-400">
              IDBI Bank · Consent-first pre-approved offers
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <FairnessBadge fairness={fairness} />
          <button
            onClick={onReplay}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            ▶ Replay AA consent
          </button>
        </div>
      </div>
    </header>
  );
}

function Screen({ children }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-6">
      <div className="max-w-md rounded-xl border border-slate-200 bg-white p-6 text-center shadow-sm">
        {children}
      </div>
    </div>
  );
}

export default function App() {
  const [leads, setLeads] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [fairness, setFairness] = useState(null);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [showConsent, setShowConsent] = useState(true);
  const [showSuppressed, setShowSuppressed] = useState(false);

  useEffect(() => {
    Promise.all([api.leads({ include_suppressed: true }), api.portfolio(), api.fairness()])
      .then(([l, p, f]) => {
        setLeads(l);
        setPortfolio(p);
        setFairness(f);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <Screen>
        <div className="text-3xl">🔌</div>
        <h1 className="mt-2 text-lg font-semibold text-slate-800">Can’t reach the LendLens API</h1>
        <p className="mt-1 text-sm text-slate-500">{error}</p>
        <div className="mt-4 rounded-lg bg-slate-50 p-3 text-left text-xs text-slate-600">
          Start the backend, then reload:
          <pre className="mt-1 whitespace-pre-wrap font-mono text-[11px]">
            python run_all.py{"\n"}uvicorn api.main:app --port 8000
          </pre>
          <div className="mt-1 text-slate-400">API base: {api.base}</div>
        </div>
      </Screen>
    );
  }

  if (!leads || !portfolio || !fairness) {
    return (
      <Screen>
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-idbi-green" />
        <p className="mt-3 text-sm text-slate-500">Loading leads…</p>
      </Screen>
    );
  }

  const jumpPriya = () => {
    const p = leads.find((l) => l.customer_id === "CUST_PRIYA");
    if (p) setSelected(p);
  };

  return (
    <div className="min-h-screen">
      {showConsent && <ConsentFlow onClose={() => setShowConsent(false)} />}
      <Header fairness={fairness} onReplay={() => setShowConsent(true)} />

      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        <StatCards portfolio={portfolio} leads={leads} />

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <LeadQueue
              leads={leads}
              showSuppressed={showSuppressed}
              setShowSuppressed={setShowSuppressed}
              onSelect={setSelected}
              selectedId={selected?.customer_id}
              onJumpPriya={jumpPriya}
            />
          </div>
          <div>
            <LeadDetail lead={selected} onClose={() => setSelected(null)} />
          </div>
        </div>

        <PortfolioPanel portfolio={portfolio} />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-3 text-center text-[11px] text-slate-400">
          LendLens · Round-1 prototype · AA / ULI / OCEN rails are <b>simulated</b> and
          clearly labelled. No real bank / bureau calls · deterministic (seed 42).
        </div>
      </footer>
    </div>
  );
}
