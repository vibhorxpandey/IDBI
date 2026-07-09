import { useState } from "react";
import FairnessBadge from "./FairnessBadge";

export default function Topbar({ dark, setDark, fairness, query, setQuery, onReplay, notify }) {
  const [bellOpen, setBellOpen] = useState(false);
  return (
    <div className="flex items-center gap-3">
      <div className="glass flex max-w-[420px] flex-1 items-center gap-2.5 px-4 py-2.5">
        <svg viewBox="0 0 24 24" className="h-4 w-4 text-slate-400 dark:text-ll-txt3" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search leads by name, city, ID…"
          className="w-full bg-transparent text-[13px] text-slate-700 outline-none placeholder:text-slate-400 dark:text-ll-txt dark:placeholder:text-ll-txt3" />
        {query && <button onClick={() => setQuery("")} className="text-slate-400 hover:text-slate-600 dark:hover:text-ll-txt">✕</button>}
      </div>

      <div className="ml-auto flex items-center gap-2.5">
        <FairnessBadge fairness={fairness} />
        <button onClick={onReplay} className="hidden rounded-[11px] border border-slate-200 bg-white/60 px-3 py-2 text-xs font-medium text-slate-600 backdrop-blur hover:bg-white dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-ll-txt2 dark:hover:bg-white/[0.07] md:block">▶ Replay AA consent</button>

        <div className="flex rounded-[11px] border border-slate-200 bg-white/60 p-[3px] backdrop-blur dark:border-white/[0.08] dark:bg-white/[0.04]">
          <button onClick={() => setDark(true)} aria-label="Dark mode" className={`grid h-[30px] w-[34px] place-items-center rounded-lg ${dark ? "bg-slate-100 text-slate-700 dark:bg-white/[0.1] dark:text-ll-txt" : "text-slate-400"}`}>
            <svg viewBox="0 0 24 24" className="h-[15px] w-[15px]" fill="currentColor"><path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" /></svg>
          </button>
          <button onClick={() => setDark(false)} aria-label="Light mode" className={`grid h-[30px] w-[34px] place-items-center rounded-lg ${!dark ? "bg-slate-100 text-amber-500" : "text-ll-txt3"}`}>
            <svg viewBox="0 0 24 24" className="h-[15px] w-[15px]" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19" /></svg>
          </button>
        </div>

        <div className="relative">
          <button onClick={() => setBellOpen((v) => !v)} className="relative grid h-10 w-10 place-items-center rounded-[11px] border border-slate-200 bg-white/60 text-slate-500 backdrop-blur hover:bg-white dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-ll-txt2 dark:hover:bg-white/[0.07]">
            <span className="absolute right-2.5 top-2.5 h-1.5 w-1.5 rounded-full bg-ll-orange shadow-[0_0_0_3px_rgba(255,122,69,0.18)]" />
            <svg viewBox="0 0 24 24" className="h-[17px] w-[17px]" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.7 21a2 2 0 01-3.4 0" /></svg>
          </button>
          {bellOpen && (
            <div className="glass absolute right-0 top-12 z-50 w-64 animate-scale-in p-3">
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400 dark:text-ll-txt3">Alerts</div>
              <div className="space-y-2 text-xs text-slate-600 dark:text-ll-txt2">
                <div className="flex gap-2"><span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ll-green" />484 Gold leads ready for outreach today.</div>
                <div className="flex gap-2"><span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ll-blue" />Fairness check passed (DI {fairness?.disparate_impact_ratio?.toFixed(2)}).</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
