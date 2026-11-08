import { createContext, useContext, useEffect, useState } from "react";

export const isRaw = () => localStorage.getItem("fmcc-raw") === "1";
export const setRaw = (v) => { localStorage.setItem("fmcc-raw", v ? "1" : "0"); window.dispatchEvent(new Event("fmcc-raw")); };
export const useRaw = () => {
  const [raw, set] = useState(isRaw());
  useEffect(() => { const f = () => set(isRaw()); window.addEventListener("fmcc-raw", f); return () => window.removeEventListener("fmcc-raw", f); }, []);
  return raw;
};
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const ScoutCtx = createContext({});
export const useScout = () => useContext(ScoutCtx);

const RATE = { GBP: ["£", 1], EUR: ["€", 1.17], USD: ["$", 1.27] };
const PER = { week: [1, "/wk"], month: [52 / 12, "/mo"], year: [52, "/yr"] };

export const fmtMoney = (v, prefs) => {
  if (v == null) return "—";
  const [sym, r] = RATE[prefs?.currency || "GBP"];
  const x = v * r;
  if (!x) return `${sym}0`;
  return x >= 1e6 ? `${sym}${(x / 1e6).toFixed(1)}m` : `${sym}${Math.round(x / 1000)}k`;
};
export const fmtWage = (v, prefs) => {
  if (v == null) return "—";
  const [sym, r] = RATE[prefs?.currency || "GBP"];
  const [m, suf] = PER[prefs?.wages || "week"];
  const x = v * r * m;
  return `${sym}${x >= 1e6 ? `${(x / 1e6).toFixed(2)}m` : `${Math.round(x / 1000)}k`}${suf}`;
};
export const toGBP = (v, prefs) => v / RATE[prefs?.currency || "GBP"][1];
export const pctColor = (p) => (p == null ? "var(--dim)" : p >= 80 ? "var(--grn)" : p >= 60 ? "var(--acc)" : p >= 40 ? "var(--amb)" : "var(--red)");
export const num = (v) => (v == null ? "—" : Math.abs(v) >= 100 ? Math.round(v) : Math.abs(v) >= 10 ? v.toFixed(1) : v.toFixed(2));

export const usePost = (key, url, body, opts = {}) =>
  useQuery({ queryKey: [key, body], queryFn: () => api.post(url, body).then((r) => r.data), ...opts });

export const ContractTag = ({ m }) => (m == null || m > 12 ? null
  : <span className={`tag st ${m <= 6 ? "r" : "a"}`} data-testid="contract-warning">{m} months left</span>);

const PctCell = ({ v, p, marker, raw }) => (
  <td className="mono" style={{ minWidth: 70 }}>
    <span title={marker || undefined}>{num(v)}{marker && <sup style={{ color: "var(--amb)" }}>×</sup>}</span>
    {p != null && !raw && <span style={{ display: "block", height: 3, borderRadius: 2, marginTop: 4, width: `${Math.max(4, p)}%`, background: pctColor(p) }} title={`${p}th percentile`} />}
  </td>
);
export const Pct = (props) => <PctCell {...props} raw={useRaw()} />;
