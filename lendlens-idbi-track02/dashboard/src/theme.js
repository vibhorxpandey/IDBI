// Shared tier + product styling used across the console.

export const TIER = {
  GOLD: {
    label: "Gold",
    badge: "bg-amber-100 text-amber-800 ring-1 ring-amber-300",
    dot: "bg-amber-500",
    bar: "#d97706",
    row: "hover:bg-amber-50",
  },
  SILVER: {
    label: "Silver",
    badge: "bg-slate-200 text-slate-700 ring-1 ring-slate-300",
    dot: "bg-slate-400",
    bar: "#94a3b8",
    row: "hover:bg-slate-50",
  },
  BRONZE: {
    label: "Bronze",
    badge: "bg-orange-100 text-orange-800 ring-1 ring-orange-300",
    dot: "bg-orange-700",
    bar: "#b45309",
    row: "hover:bg-orange-50",
  },
  SUPPRESSED: {
    label: "Suppressed",
    badge: "bg-slate-100 text-slate-500 ring-1 ring-slate-300",
    dot: "bg-slate-300",
    bar: "#cbd5e1",
    row: "hover:bg-slate-50 opacity-70",
  },
};

export const PRODUCT_COLOR = {
  Home: "#0b6b3a",
  Auto: "#2563eb",
  Personal: "#7c3aed",
  Mortgage: "#b45309",
};

export const TIER_ORDER = ["GOLD", "SILVER", "BRONZE", "SUPPRESSED"];
