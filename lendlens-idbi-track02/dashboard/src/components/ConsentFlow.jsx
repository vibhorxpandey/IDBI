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
  const [accounts, setAccounts] = useState(
    ACCOUNTS.map((a) => ({ ...a, checked: a.primary }))
  );
  const [otp, setOtp] = useState("123456");
  const [consent, setConsent] = useState(null);
  const [fiData, setFiData] = useState(null);
  const [fetching, setFetching] = useState(false);

  const selected = accounts.filter((a) => a.checked);

  // Trigger the mock AA calls when we reach those steps.
  useEffect(() => {
    if (step === 3 && !consent) {
      api
        .aaConsent({
          customer_id: "CUST_PRIYA",
          purpose: "Loan eligibility assessment",
          account_refs: selected.map((a) => a.id),
          duration_months: 6,
        })
        .then(setConsent)
        .catch(() => setConsent({ consent_id: "CONSENT-OFFLINE", status: "ACTIVE", mock: true }));
    }
    if (step === 4 && !fiData) {
      setFetching(true);
      const t = setTimeout(() => {
        api
          .aaFetch({ consent_id: consent?.consent_id || "CONSENT-MOCK", customer_id: "CUST_PRIYA" })
          .then((d) => setFiData(d))
          .catch(() => setFiData(null))
          .finally(() => setFetching(false));
      }, 1300);
      return () => clearTimeout(t);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  const canNext =
    (step === 0 && selected.length > 0) ||
    (step === 1) ||
    (step === 2 && otp.length === 6) ||
    (step === 3 && consent) ||
    step === 4;

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl animate-fade-up">
        {/* header */}
        <div className="rounded-t-2xl bg-idbi-green px-5 py-4 text-white">
          <div className="flex items-center justify-between">
            <div className="font-semibold">Account Aggregator · Consent</div>
            <button onClick={onClose} className="text-white/80 hover:text-white text-sm">
              Skip ✕
            </button>
          </div>
          <div className="mt-1 inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2 py-0.5 text-[11px]">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-300" />
            Simulated AA flow — DPDP-compliant, consent-first
          </div>
        </div>

        {/* stepper */}
        <div className="flex gap-1 px-5 pt-4">
          {STEPS.map((s, i) => (
            <div key={s} className="flex-1">
              <div className={`h-1.5 rounded-full ${i <= step ? "bg-idbi-green" : "bg-slate-200"}`} />
              <div className={`mt-1 text-[10px] ${i === step ? "text-idbi-green font-semibold" : "text-slate-400"}`}>
                {s}
              </div>
            </div>
          ))}
        </div>

        {/* body */}
        <div className="min-h-[240px] px-5 py-5">
          {step === 0 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-600">
                Priya taps <b>“Check my eligibility.”</b> Select the accounts to share
                (read-only) via the Account Aggregator rail:
              </p>
              {accounts.map((a, i) => (
                <label
                  key={a.id}
                  className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 cursor-pointer hover:border-idbi-green"
                >
                  <input
                    type="checkbox"
                    checked={a.checked}
                    onChange={() =>
                      setAccounts((arr) =>
                        arr.map((x, j) => (j === i ? { ...x, checked: !x.checked } : x))
                      )
                    }
                    className="h-4 w-4 accent-idbi-green"
                  />
                  <div>
                    <div className="text-sm font-medium text-slate-800">{a.bank}</div>
                    <div className="text-xs text-slate-500">
                      {a.type} · {a.id}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-600">Purpose of data sharing:</p>
              <div className="rounded-lg border-2 border-idbi-green bg-idbi-greenLight p-3">
                <div className="text-sm font-semibold text-idbi-greenDark">
                  Loan eligibility assessment
                </div>
                <div className="text-xs text-slate-600">
                  6 months of statements · used only to assess pre-approved offers.
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {["DEPOSIT", "RECURRING_DEPOSIT"].map((f) => (
                  <span key={f} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3">
              <p className="text-sm text-slate-600">
                One-time password sent to the registered mobile <b>••••••3210</b>.
                <span className="text-slate-400"> (mock — any 6 digits)</span>
              </p>
              <input
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                inputMode="numeric"
                className="w-40 rounded-lg border border-slate-300 px-3 py-2 text-center text-lg tracking-[0.4em] focus:border-idbi-green focus:outline-none"
              />
            </div>
          )}

          {step === 3 && (
            <div className="flex flex-col items-center justify-center gap-2 py-6 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-3xl text-emerald-600">
                ✓
              </div>
              <div className="text-lg font-semibold text-slate-800">Consent granted</div>
              <div className="text-xs text-slate-500">
                {consent ? consent.consent_id : "creating consent artefact…"}
              </div>
              <div className="text-xs text-slate-400">
                Status: {consent?.status || "…"} · revocable anytime
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-3">
              {fetching || !fiData ? (
                <div className="flex flex-col items-center justify-center gap-3 py-8">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-idbi-green" />
                  <div className="text-sm text-slate-600">
                    Securely fetching 6 months of statements…
                  </div>
                </div>
              ) : (
                <div className="animate-fade-up space-y-3">
                  <div className="text-sm font-medium text-slate-700">Financial data received</div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-slate-50 p-3">
                      <div className="text-[11px] uppercase text-slate-500">Declared income</div>
                      <div className="text-lg font-bold text-slate-500 line-through">
                        {inr(fiData.summary.declared_income_on_file)}
                      </div>
                    </div>
                    <div className="rounded-lg bg-idbi-greenLight p-3">
                      <div className="text-[11px] uppercase text-idbi-greenDark">
                        Avg monthly credits
                      </div>
                      <div className="text-lg font-bold text-idbi-green">
                        {inr(fiData.summary.avg_monthly_credits)}
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500">{fiData.summary.note}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* footer */}
        <div className="flex items-center justify-between rounded-b-2xl border-t border-slate-100 px-5 py-3">
          <button
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0 || step >= 3}
            className="text-sm text-slate-500 disabled:opacity-30"
          >
            ← Back
          </button>
          {step < STEPS.length - 1 ? (
            <button
              onClick={next}
              disabled={!canNext}
              className="rounded-lg bg-idbi-green px-4 py-2 text-sm font-medium text-white hover:bg-idbi-greenDark disabled:opacity-40"
            >
              {step === 2 ? "Verify & grant" : "Continue"}
            </button>
          ) : (
            <button
              onClick={onClose}
              className="rounded-lg bg-idbi-green px-4 py-2 text-sm font-medium text-white hover:bg-idbi-greenDark"
            >
              Enter RM console →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
