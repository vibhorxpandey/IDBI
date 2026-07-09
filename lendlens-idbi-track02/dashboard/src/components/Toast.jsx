import { useEffect } from "react";

export default function Toast({ toast, onDone }) {
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(onDone, 3200);
    return () => clearTimeout(t);
  }, [toast, onDone]);

  if (!toast) return null;
  const tone = {
    ok: "text-ll-green",
    info: "text-ll-blue",
    warn: "text-ll-amber",
  }[toast.tone || "info"];

  return (
    <div className="fixed bottom-6 left-1/2 z-[60] -translate-x-1/2 animate-fade-up">
      <div className="glass flex items-center gap-3 px-4 py-3 shadow-xl">
        <span className={`grid h-6 w-6 place-items-center rounded-full bg-current/10 ${tone}`}>
          <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M20 6L9 17l-5-5" /></svg>
        </span>
        <div className="text-sm font-medium text-slate-700 dark:text-ll-txt">{toast.msg}</div>
      </div>
    </div>
  );
}
