// Shared tier + product styling used across the console.
// Badge classes carry light + dark (Fundly) variants.

export const TIER = {
  GOLD: {
    label: "Gold",
    badge:
      "bg-amber-100 text-amber-800 ring-1 ring-amber-300 dark:bg-ll-amber/10 dark:text-ll-amber dark:ring-ll-amber/25",
    dot: "bg-amber-500 dark:bg-ll-amber",
    bar: "#ffb547",
    row: "hover:bg-amber-50 dark:hover:bg-white/[0.04]",
  },
  SILVER: {
    label: "Silver",
    badge:
      "bg-slate-200 text-slate-700 ring-1 ring-slate-300 dark:bg-white/[0.06] dark:text-slate-300 dark:ring-white/10",
    dot: "bg-slate-400 dark:bg-slate-400",
    bar: "#8b909e",
    row: "hover:bg-slate-50 dark:hover:bg-white/[0.04]",
  },
  BRONZE: {
    label: "Bronze",
    badge:
      "bg-orange-100 text-orange-800 ring-1 ring-orange-300 dark:bg-ll-orange/10 dark:text-ll-orange dark:ring-ll-orange/25",
    dot: "bg-orange-700 dark:bg-ll-orange",
    bar: "#ff7a45",
    row: "hover:bg-orange-50 dark:hover:bg-white/[0.04]",
  },
  SUPPRESSED: {
    label: "Suppressed",
    badge:
      "bg-slate-100 text-slate-500 ring-1 ring-slate-300 dark:bg-white/[0.03] dark:text-ll-txt3 dark:ring-white/[0.06]",
    dot: "bg-slate-300 dark:bg-white/20",
    bar: "#3f4452",
    row: "hover:bg-slate-50 dark:hover:bg-white/[0.03] opacity-70",
  },
};

// Product palette — brightened so it reads on the dark surface too.
export const PRODUCT_COLOR = {
  Home: "#3fe08a",
  Auto: "#3e8bff",
  Personal: "#a855f7",
  Mortgage: "#ffb547",
};

export const TIER_ORDER = ["GOLD", "SILVER", "BRONZE", "SUPPRESSED"];
