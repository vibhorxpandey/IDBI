import { inrShort } from "../format";

export default function PreApprovedCard({ portfolio, onReplay, onBatch }) {
  return (
    <div className="glass flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-[15.5px] font-bold tracking-tight text-slate-800 dark:text-ll-txt">Pre-approved book</h3>
        <span className="text-xs font-medium text-slate-400 dark:text-ll-txt2">Surfaced leads</span>
      </div>

      {/* glass gradient credit card */}
      <div className="relative overflow-hidden rounded-[18px] p-5" style={{ background: "linear-gradient(125deg,#0b6b3a,#075232 42%,#04351f)" }}>
        <div className="pointer-events-none absolute inset-0 opacity-70" style={{ background: "radial-gradient(150px 120px at 88% -10%, rgba(255,190,120,.5), transparent 60%), radial-gradient(180px 160px at 10% 120%, rgba(62,139,255,.35), transparent 60%)" }} />
        <div className="pointer-events-none absolute inset-0 rounded-[18px] ring-1 ring-inset ring-white/15" />
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-2 text-[13px] font-bold text-white">
            <div className="grid h-[22px] w-[22px] place-items-center rounded-md bg-white/15 backdrop-blur"><svg viewBox="0 0 24 24" className="h-3.5 w-3.5"><path d="M4 13l5 5L20 6" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" /></svg></div>
            IDBI · Retail
          </div>
          <div className="h-[19px] w-[26px] rounded-[5px] bg-gradient-to-br from-amber-200 to-amber-500 opacity-90" />
        </div>
        <div className="relative z-10 mt-6 font-mono text-[13px] tracking-[3px] text-white/75">•••• •••• •••• 3056</div>
        <div className="relative z-10 mt-3.5 flex items-end justify-between">
          <div>
            <div className="text-[11px] text-white/70">Total pre-approved value</div>
            <div className="text-[26px] font-extrabold leading-tight tracking-tight text-white">{inrShort(portfolio.total_offer_value)}</div>
          </div>
          <div className="text-right text-[11px] text-white/70">
            <div>{portfolio.surfaced?.toLocaleString("en-IN")} leads</div>
            <div className="text-ll-green">▲ ready to call</div>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button onClick={onReplay} className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-idbi-green py-3 text-[13px] font-semibold text-white shadow-lg shadow-idbi-green/25 transition hover:bg-idbi-greenDark dark:bg-gradient-to-br dark:from-ll-blue dark:to-indigo-500 dark:shadow-ll-blue/30 dark:hover:brightness-110">
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 3l14 9-14 9V3z" /></svg>Replay AA consent
        </button>
        <button onClick={onBatch} className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white/60 py-3 text-[13px] font-semibold text-slate-700 backdrop-blur transition hover:bg-white dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-ll-txt dark:hover:bg-white/[0.07]">
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16v6H4zM4 14h16v6H4z" /></svg>Batch run
        </button>
      </div>
    </div>
  );
}
