import logo from "../assets/lendlens-logo-dark.png";

const NAV = [
  { group: null, items: [
    { icon: "grid", label: "Dashboard", key: "dashboard" },
    { icon: "queue", label: "Lead queue", key: "queue" },
  ]},
  { group: "DECISION ENGINE", items: [
    { icon: "income", label: "Income engine", key: "income" },
    { icon: "intent", label: "Intent engine", key: "intent" },
    { icon: "offer", label: "Offers", key: "offers" },
    { icon: "explain", label: "Explainability", key: "explain" },
    { icon: "fair", label: "Fairness", key: "fairness" },
  ]},
  { group: "SYSTEM", items: [{ icon: "cog", label: "Settings", key: "settings" }] },
];

function Icon({ name }) {
  const p = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" };
  const d = {
    grid: <><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>,
    queue: <><path d="M8 6h13M8 12h13M8 18h13" /><circle cx="3.5" cy="6" r="1" /><circle cx="3.5" cy="12" r="1" /><circle cx="3.5" cy="18" r="1" /></>,
    income: <path d="M3 12h4l3 8 4-16 3 8h4" />,
    intent: <path d="M12 3l8 3v6c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V6l8-3z" />,
    offer: <><path d="M20.6 12.6L12 21l-9-9V4h8l9.6 8.6z" /><circle cx="7.5" cy="7.5" r="1.2" /></>,
    explain: <><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></>,
    fair: <><path d="M12 3v18M5 7l7-2 7 2" /><path d="M5 7l-2 6a3 3 0 006 0L7 7M19 7l-2 6a3 3 0 006 0l-2-6" /></>,
    cog: <><circle cx="12" cy="12" r="3.2" /><path d="M19.4 15a1.6 1.6 0 00.3 1.8 2 2 0 11-2.8 2.8 1.6 1.6 0 00-2.7.7 1.6 1.6 0 01-3.2 0 1.6 1.6 0 00-2.7-.7 2 2 0 11-2.8-2.8 1.6 1.6 0 00-.7-2.7 1.6 1.6 0 010-3.2 1.6 1.6 0 00.7-2.7 2 2 0 112.8-2.8 1.6 1.6 0 001.8.3 1.6 1.6 0 001-1.5 1.6 1.6 0 013.2 0 1.6 1.6 0 001 1.5 1.6 1.6 0 001.8-.3 2 2 0 112.8 2.8 1.6 1.6 0 00-.3 1.8 1.6 1.6 0 001.5 1 1.6 1.6 0 010 3.2 1.6 1.6 0 00-1.5 1z" /></>,
  };
  return <svg viewBox="0 0 24 24" className="h-[18px] w-[18px]" {...p}>{d[name]}</svg>;
}

export default function Sidebar({ active, setActive, notify }) {
  return (
    <aside className="hidden w-[218px] shrink-0 flex-col px-4 py-6 lg:flex">
      <img src={logo} alt="LendLens" className="ml-1 mb-1 h-9 w-auto object-contain object-left" />
      <div className="ml-2 mb-6 text-[9.5px] font-semibold tracking-[2px] text-slate-400 dark:text-ll-txt3">IDBI · TRACK 02</div>

      <nav className="flex flex-col gap-0.5">
        {NAV.map((sec, si) => (
          <div key={si}>
            {sec.group && <div className="px-3 pb-1.5 pt-4 text-[10px] font-bold tracking-[1.6px] text-slate-400 dark:text-ll-txt3">{sec.group}</div>}
            {sec.items.map((it) => {
              const on = active === it.key;
              return (
                <button key={it.key}
                  onClick={() => setActive(it.key)}
                  className={`group relative flex w-full items-center gap-3 rounded-[11px] px-3 py-[11px] text-[13.5px] font-medium transition ${
                    on
                      ? "bg-idbi-greenLight text-idbi-greenDark dark:bg-white/[0.06] dark:text-white dark:shadow-[inset_0_0_0_1px_rgba(255,255,255,0.08)]"
                      : "text-slate-500 hover:bg-slate-100 hover:text-slate-800 dark:text-ll-txt2 dark:hover:bg-white/[0.04] dark:hover:text-ll-txt"
                  }`}>
                  {on && <span className="absolute -left-4 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded bg-idbi-green dark:bg-gradient-to-b dark:from-ll-pink dark:to-ll-purple" />}
                  <Icon name={it.icon} />{it.label}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="mt-auto flex items-center gap-3 rounded-[14px] border border-slate-200 p-2.5 dark:border-white/[0.06] dark:bg-white/[0.02]">
        <div className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-ll-pink to-ll-purple text-[13px] font-bold text-white">VP</div>
        <div className="min-w-0">
          <div className="truncate text-[12.5px] font-semibold text-slate-800 dark:text-ll-txt">Vibhor Pandey</div>
          <div className="text-[10.5px] text-slate-400 dark:text-ll-txt3">Underwriting · Admin</div>
        </div>
      </div>
    </aside>
  );
}
