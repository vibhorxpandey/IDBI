// Indian-format rupee + percentage helpers.

export function inr(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  const neg = n < 0;
  let s = String(Math.abs(Math.round(n)));
  if (s.length > 3) {
    const last3 = s.slice(-3);
    const rest = s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",");
    s = rest + "," + last3;
  }
  return (neg ? "-" : "") + "₹" + s;
}

// Compact: ₹18 L, ₹2.8 Cr
export function inrShort(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  if (n >= 1e7) return "₹" + (n / 1e7).toFixed(2).replace(/\.?0+$/, "") + " Cr";
  if (n >= 1e5) return "₹" + (n / 1e5).toFixed(1).replace(/\.0$/, "") + " L";
  return inr(n);
}

export function pct(x, digits = 0) {
  if (x === null || x === undefined || isNaN(x)) return "—";
  return (x * 100).toFixed(digits) + "%";
}

export function signedPct(x, digits = 0) {
  if (x === null || x === undefined || isNaN(x)) return "—";
  const v = (x * 100).toFixed(digits);
  return (x >= 0 ? "+" : "") + v + "%";
}
