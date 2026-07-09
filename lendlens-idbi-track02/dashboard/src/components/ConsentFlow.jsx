import { useEffect, useState } from "react";
import { api } from "../api";
import { inr } from "../format";

const ACCOUNTS = [
  { id: "HDFC****1234", bank: "HDFC Bank", type: "Savings", primary: true },
  { id: "ICICI****5678", bank: "ICICI Bank", type: "Savings", primary: false },
];
const STEPS = ["Link accounts", "Purpose", "Verify (OTP)", "Consent", "Fetch data"];

export default function ConsentFlow({ onClose }) {
  const [step, setStep] = useState(0);
  const [accounts, setAccounts] = useState(ACCOUNTS.map((a) => ({ ...a, checked: a.primary })));
  const [otp, setOtp] = useState("123456");
  const [consent, setConsent] = useState(null);
  const [fiData, setFiData] = useState(null);
  const [fetching, setFetching] = useState(false);

  const selected = accounts.filter((a) => a.checked);

  useEffect(() => {
    if (step === 3 && !consent) {
      api.aaConsent({ customer_id: "CUST_PRIYA", purpose: "Loan eligibility assessment", account_refs: selected.map((a) => a.id), duration_months: 6 })
        .then(setConsent).catch(() => setConsent({ consent_id: "CONSENT-OFFLINE", status: "ACTIVE", mock: true }));
    }
    if (step === 4 && !fiData) {
      setFetching(true);
      const t = setTimeout(() => {
        api.aaFetch({ consent_id: consent?.consent_id || "CONSENT-MOCK", customer_id: "CUST_PRIYA" })
          .then((d) => setFiData(d)).catch(() => setFiData(null)).finally(() => setFetching(false));
      }, 1300);
      return () => clearTimeout(t);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  const canNext = (step === 0 && selected.length > 0) || step === 1 || (step === 2 && otp.length === 6) || (step === 3 && consent) || step === 4;
  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));

  const card = "glass w-full max-w-lg animate-scale-in overflow-hidden shadow-2xl";
  const box = "rounded-lg border border-slate-200 p-3 dark:border-white/[0.08]";
  const muted = "text-slate-600 dark:text-ll-txt2";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className={card}>
        <div className="rounded-t-2xl bg-idbi-green px-5 py-4 text-white dark:bg-gradient-to-r dark:from-idbi-green dark:to-emerald-600">
          <div className="flex items-center justify-between">
            <div className="font-semibold">Account Aggregator · Consent</div>
            <button onClick={onClose} className="text-sm text-white/80 hover:text-white">Skip ✕</button>
          </div>
          <div className="mt-1 inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2 py-0.5 text-[11px]">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-300" />Simulated AA flow — DPDP-compliant, consent-first
          </div>
        </div>

        <div className="flex gap-1 px-5 pt-4">
          {STEPS.map((s, i) => (
            <div key={s} className="flex-1">
              <div className={`h-1.5 rounded-full ${i <= step ? "bg-idbi-green dark:bg-ll-green" : "bg-slate-200 dark:bg-white/10"}`} />
              <div className={`mt-1 text-[10px] ${i === step ? "font-semibold text-idbi-green dark:text-ll-green" : "text-slate-400 dark:text-ll-txt3"}`}>{s}</div>
            </div>
          ))}
        </div>

        <div className="min-h-[240px] px-5 py-5">
          {step === 0 && (
            <div className="space-y-3">
              <p className={`text-sm ${muted}`}>Priya taps <b className="dark:text-ll-txt">“Check my eligibility.”</b> Select the accounts to share (read-only) via the Account Aggregator rail:</p>
              {accounts.map((a, i) => (
                <label key={a.id} className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 p-3 hover:border-idbi-green dark:border-white/[0.08] dark:hover:border-ll-green/50">
                  <input type="checkbox" checked={a.checked} onChange={() => setAccounts((arr) => arr.map((x, j) => (j === i ? { ...x, checked: !x.checked } : x)))} className="h-4 w-4 accent-idbi-green dark:accent-ll-green" />
                  <div>
                    <div className="text-sm font-medium text-slate-800 dark:text-ll-txt">{a.bank}</div>
                    <div className="text-xs text-slate-500 dark:text-ll-txt3">{a.type} · {a.id}</div>
                  </div>
                </label>
              ))}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-3">
              <p className={`text-sm ${muted}`}>Purpose of data sharing:</p>
              <div className="rounded-lg border-2 border-idbi-green bg-idbi-greenLight p-3 dark:border-ll-green/40 dark:bg-ll-green/[0.08]">
                <div className="text-sm font-semibold text-idbi-greenDark dark:text-ll-green">Loan eligibility assessment</div>
                <div className={`text-xs ${muted}`}>6 months of statements · used only to assess pre-approved offers.</div>
              </div>
              <div className="flex flex-wrap gap-2">
                {["DEPOSIT", "RECURRING_DEPOSIT"].map((f) => (
                  <span key={f} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600 dark:bg-white/[0.06] dark:text-ll-txt2">{f}</span>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3">
              <p className={`text-sm ${muted}`}>One-time password sent to the registered mobile <b className="dark:text-ll-txt">••••••3210</b>.<span className="text-slate-400 dark:text-ll-txt3"> (mock — any 6 digits)</span></p>
              <input value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))} inputMode="numeric"
                className="w-40 rounded-lg border border-slate-300 px-3 py-2 text-center text-lg tracking-[0.4em] focus:border-idbi-green focus:outline-none dark:border-white/15 dark:bg-white/[0.04] dark:text-ll-txt dark:focus:border-ll-green" />
            </div>
          )}

          {step === 3 && (
            <div className="flex flex-col items-center justify-center gap-2 py-6 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-3xl text-emerald-600 dark:bg-ll-green/15 dark:text-ll-green">✓</div>
              <div className="text-lg font-semibold text-slate-800 dark:text-ll-txt">Consent granted</div>
              <div className="text-xs text-slate-500 dark:text-ll-txt3">{consent ? consent.consent_id : "creating consent artefact…"}</div>
              <div className="text-xs text-slate-400 dark:text-ll-txt3">Status: {consent?.status || "…"} · revocable anytime</div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-3">
              {fetching || !fiData ? (
                <div className="flex flex-col items-center justify-center gap-3 py-8">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-idbi-green dark:border-white/10 dark:border-t-ll-green" />
                  <div className={`text-sm ${muted}`}>Securely fetching 6 months of statements…</div>
                </div>
              ) : (
                <div className="animate-fade-up space-y-3">
                  <div className="text-sm font-medium text-slate-700 dark:text-ll-txt">Financial data received</div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className={box + " dark:bg-white/[0.03]"}>
                      <div className="text-[11px] uppercase text-slate-500 dark:text-ll-txt3">Declared income</div>
                      <div className="text-lg font-bold text-slate-500 line-through dark:text-ll-txt3">{inr(fiData.summary.declared_income_on_file)}</div>
                    </div>
                    <div className="rounded-lg bg-idbi-greenLight p-3 dark:bg-ll-green/[0.08] dark:ring-1 dark:ring-ll-green/15">
                      <div className="text-[11px] uppercase text-idbi-greenDark dark:text-ll-green">Avg monthly credits</div>
                      <div className="text-lg font-bold text-idbi-green dark:text-ll-green">{inr(fiData.summary.avg_monthly_credits)}</div>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-ll-txt3">{fiData.summary.note}</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between rounded-b-2xl border-t border-slate-100 px-5 py-3 dark:border-white/[0.06]">
          <button onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0 || step >= 3} className="text-sm text-slate-500 disabled:opacity-30 dark:text-ll-txt2">← Back</button>
          {step < STEPS.length - 1 ? (
            <button onClick={next} disabled={!canNext} className="rounded-lg bg-idbi-green px-4 py-2 text-sm font-medium text-white hover:bg-idbi-greenDark disabled:opacity-40 dark:disabled:opacity-30">{step === 2 ? "Verify & grant" : "Continue"}</button>
          ) : (
            <button onClick={onClose} className="rounded-lg bg-idbi-green px-4 py-2 text-sm font-medium text-white hover:bg-idbi-greenDark">Enter RM console →</button>
          )}
        </div>
      </div>
    </div>
  );
}
