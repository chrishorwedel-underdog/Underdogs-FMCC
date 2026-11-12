import { Loading } from "@/components/Loading";

import { useMemo, useState } from "react";
import { Download, Save, Trash2, Plus, X, SlidersHorizontal } from "lucide-react";
import { useGet } from "@/lib/ui";
import { RoleWeights } from "./RoleWeights";

export const money = (v) => (v == null ? "—" : v >= 1e6 ? `£${(v / 1e6).toFixed(v >= 1e7 ? 0 : 1)}m` : v >= 1e3 ? `£${Math.round(v / 1e3)}k` : `£${v}`);
export const openDossier = (uid) => window.dispatchEvent(new CustomEvent("fmcc-dossier", { detail: uid }));
const get = (r, k) => k.split(".").reduce((o, x) => (o == null ? undefined : o[x]), r);
const VIEWS = "fmcc-stats-views";
const OPS = [">=", "<=", "=", "top %", "bottom %"];
const DEFAULT_COLS = ["age", "minutes", "est_value", "role_fit", "p90.npxg", "p90.xa", "p90.progp", "p90.tkw", "p90.prr", "p90.drb"];
const shade = (p) => (p == null ? undefined : `hsla(${Math.round(p * 1.2)}, 70%, 45%, ${0.18 + Math.abs(p - 50) / 260})`);

const pct = (rows, k) => {
  const vals = rows.map((r) => get(r, k)).filter((v) => typeof v === "number").sort((a, b) => a - b);
  return (v) => (typeof v !== "number" || vals.length < 2 ? null : Math.round((vals.filter((x) => x < v).length / (vals.length - 1)) * 100));
};

const test = (r, c, rows, cache) => {
  const v = c.field === "league" || c.field === "club" || c.field === "group" ? get(r, c.field) : get(r, c.field);
  if (c.op === "=") return String(v ?? "").toLowerCase() === String(c.value).toLowerCase();
  if (c.op === "top %" || c.op === "bottom %") {
    cache[c.field] = cache[c.field] || pct(rows, c.field);
    const p = cache[c.field](v);
    return p != null && (c.op === "top %" ? p >= 100 - Number(c.value) : p <= Number(c.value));
  }
  return typeof v === "number" && (c.op === ">=" ? v >= Number(c.value) : v <= Number(c.value));
};

const Filters = ({ conds, set, mode, setMode, fields }) => (
  <div className="card" style={{ display: "grid", gap: 8 }} data-testid="st-filters">
    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}><b className="note" style={{ color: "var(--text)" }}>Advanced filters</b>
      <div className="seg">{["AND", "OR"].map((m) => <button key={m} className={mode === m ? "on" : ""} onClick={() => setMode(m)} data-testid={`st-mode-${m}`}>{m}</button>)}</div>
      <button className="btn" onClick={() => set([...conds, { field: "age", op: "<=", value: 23 }])} data-testid="st-add-cond"><Plus size={13} />Add condition</button></div>
    {conds.map((c, i) => <div key={i} style={{ display: "flex", gap: 6, flexWrap: "wrap" }} data-testid={`st-cond-${i}`}>
      <select className="inp" style={{ width: 220, height: 32 }} value={c.field} onChange={(e) => set(conds.map((x, j) => (j === i ? { ...x, field: e.target.value } : x)))} data-testid={`st-cond-field-${i}`}>
        {fields.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
      <select className="inp" style={{ width: 110, height: 32 }} value={c.op} onChange={(e) => set(conds.map((x, j) => (j === i ? { ...x, op: e.target.value } : x)))} data-testid={`st-cond-op-${i}`}>{OPS.map((o) => <option key={o}>{o}</option>)}</select>
      <input className="inp" style={{ width: 140, height: 32 }} value={c.value} onChange={(e) => set(conds.map((x, j) => (j === i ? { ...x, value: e.target.value } : x)))} data-testid={`st-cond-value-${i}`} />
      <button className="ib" onClick={() => set(conds.filter((_, j) => j !== i))} data-testid={`st-cond-remove-${i}`}><X size={13} /></button></div>)}
  </div>
);

export const StatsTable = () => {
  const { data: meta } = useGet("analysis-meta", "/analysis/meta");
  const { data } = useGet("analysis-table", "/analysis/table");
  const q = new URLSearchParams(window.location.search);
  const [f, setF] = useState({ group: q.get("group") || "", league: "", club: "", minMin: 0, gender: "M", noOwn: false, search: "", maxAge: q.get("maxage") || "" });
  const [conds, setConds] = useState([]);
  const [mode, setMode] = useState("AND");
  const [cols, setCols] = useState(DEFAULT_COLS);
  const [against, setAgainst] = useState("filter");
  const [sort, setSort] = useState(["est_value", -1]);
  const [views, setViews] = useState(() => JSON.parse(localStorage.getItem(VIEWS) || "{}"));
  const [weights, setWeights] = useState(false);
  const rows = useMemo(() => data?.rows || [], [data]);
  const fields = useMemo(() => (meta ? [["league", "League"], ["club", "Club"], ["group", "Position group"], ...Object.values(meta.groups).flat()] : []), [meta]);
  const label = Object.fromEntries(fields);
  const shown = useMemo(() => {
    const cache = {};
    let r = rows.filter((x) => (!f.group || x.group === f.group) && (!f.league || x.league === f.league) && (!f.club || x.club === f.club) && (x.minutes || 0) >= f.minMin
      && (!f.gender || x.gender === f.gender) && !(f.noOwn && x.own) && (!f.search || x.name.toLowerCase().includes(f.search.toLowerCase())) && (!f.maxAge || (x.age || 0) <= Number(f.maxAge)));
    if (conds.length) { r = r.filter((x) => (mode === "AND" ? conds.every((c) => test(x, c, rows, cache)) : conds.some((c) => test(x, c, rows, cache)))); }
    return [...r].sort((a, b) => ((get(a, sort[0]) ?? -1e12) > (get(b, sort[0]) ?? -1e12) ? 1 : -1) * sort[1]);
  }, [rows, f, conds, mode, sort]);
  const base = against === "save" ? rows : against === "league" ? rows.filter((x) => x.league === (f.league || shown[0]?.league)) : against === "position" ? rows.filter((x) => x.group === (f.group || shown[0]?.group)) : shown;
  const pcts = useMemo(() => Object.fromEntries(cols.map((k) => [k, pct(base, k)])), [base, cols]);
  if (!meta || !data) return <Loading id="stats-table-loading" rows={6} label="Loading every player in your save" />;
  const opts = (k) => [...new Set(rows.map((r) => r[k]).filter(Boolean))].sort();
  const csv = () => {
    const head = ["Name", "Club", "League", "Positions", ...cols.map((k) => label[k] || k)];
    const lines = shown.map((r) => [r.name, r.club, r.league, (r.positions || []).join(" "), ...cols.map((k) => get(r, k) ?? "")].map((v) => `"${String(v).replace(/"/g, '""')}"`).join(","));
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([[head.join(","), ...lines].join("\n")], { type: "text/csv" }));
    a.download = "fmcc-stats.csv"; a.click();
  };
  const saveView = () => { const n = window.prompt("Name this view"); if (n) { const v = { ...views, [n]: { cols, conds, mode, f, against } }; setViews(v); localStorage.setItem(VIEWS, JSON.stringify(v)); } };
  const loadView = (n) => { const v = views[n]; if (v) { setCols(v.cols); setConds(v.conds); setMode(v.mode); setF(v.f); setAgainst(v.against); } };
  const fmt = (k, v) => (v == null ? "—" : k === "est_value" || k === "wage" ? money(v) : typeof v === "number" ? (Number.isInteger(v) ? v : v.toFixed(2)) : v);
  return (
    <div style={{ display: "grid", gap: 12 }} data-testid="stats-table">
      {data.sample && <p className="note" data-testid="st-sample-note">SAMPLE save: per-90 stats in this preview are SAMPLE figures built from each player's attributes.</p>}
      <div className="card" style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "end" }} data-testid="st-quick">
        <input className="inp" style={{ width: 180, height: 32 }} placeholder="Search name" value={f.search} onChange={(e) => setF({ ...f, search: e.target.value })} data-testid="st-search" />
        {[["group", "Any position", ["GK", "CB", "FB", "DM", "CM", "AM", "W", "ST"]], ["league", "Any league", opts("league")], ["club", "Any club", opts("club")]].map(([k, ph, o]) =>
          <select key={k} className="inp" style={{ width: 170, height: 32 }} value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} data-testid={`st-${k}`}><option value="">{ph}</option>{o.map((x) => <option key={x}>{x}</option>)}</select>)}
        <label className="note">Min minutes <input className="inp mono" style={{ width: 80, height: 32 }} type="number" value={f.minMin} onChange={(e) => setF({ ...f, minMin: Number(e.target.value) })} data-testid="st-minmin" /></label>
        <label className="note">Max age <input className="inp mono" style={{ width: 64, height: 32 }} type="number" value={f.maxAge} onChange={(e) => setF({ ...f, maxAge: e.target.value })} data-testid="st-maxage" /></label>
        <select className="inp" style={{ width: 110, height: 32 }} value={f.gender} onChange={(e) => setF({ ...f, gender: e.target.value })} data-testid="st-gender"><option value="M">Men</option><option value="F">Women</option><option value="">Both</option></select>
        <label className="note" style={{ display: "flex", gap: 6, alignItems: "center" }}><input type="checkbox" checked={f.noOwn} onChange={(e) => setF({ ...f, noOwn: e.target.checked })} data-testid="st-noown" />Leave out my club</label>
      </div>
      <Filters conds={conds} set={setConds} mode={mode} setMode={setMode} fields={fields} />
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <span className="note">Compare against</span>
        <select className="inp" style={{ width: 170, height: 32 }} value={against} onChange={(e) => setAgainst(e.target.value)} data-testid="st-against">
          <option value="filter">My current filter</option><option value="save">Whole save</option><option value="league">One league</option><option value="position">One position</option></select>
        <select className="inp" style={{ width: 200, height: 32 }} value="" onChange={(e) => e.target.value && setCols(cols.includes(e.target.value) ? cols.filter((c) => c !== e.target.value) : [...cols, e.target.value])} data-testid="st-columns">
          <option value="">Add or remove a column…</option>{Object.entries(meta.groups).map(([g, cs]) => <optgroup key={g} label={g}>{cs.map(([k, l]) => <option key={k} value={k}>{cols.includes(k) ? "✓ " : ""}{l}</option>)}</optgroup>)}</select>
        <button className="btn" onClick={saveView} data-testid="st-save-view"><Save size={13} />Save view</button>
        {Object.keys(views).length > 0 && <select className="inp" style={{ width: 160, height: 32 }} value="" onChange={(e) => loadView(e.target.value)} data-testid="st-load-view"><option value="">Load a view…</option>{Object.keys(views).map((n) => <option key={n}>{n}</option>)}</select>}
        {Object.keys(views).length > 0 && <button className="ib" title="Delete all saved views" onClick={() => { setViews({}); localStorage.removeItem(VIEWS); }} data-testid="st-clear-views"><Trash2 size={13} /></button>}
        <button className="btn" onClick={csv} data-testid="st-csv"><Download size={13} />Export CSV</button>
        <button className="btn" onClick={() => setWeights(true)} data-testid="st-weights"><SlidersHorizontal size={13} />Role weightings</button>
        <span className="note" data-testid="st-count" style={{ marginLeft: "auto" }}>{shown.length} players</span>
      </div>
      <div className="st-wrap"><table className="tbl st-tbl">
        <thead><tr><th className="st-name">Player</th><th>Club</th><th>Best role</th>{cols.map((k) => <th key={k} onClick={() => setSort([k, sort[0] === k ? -sort[1] : -1])} style={{ cursor: "pointer" }} data-testid={`st-sort-${k}`}>{label[k] || k}{sort[0] === k ? (sort[1] < 0 ? " ↓" : " ↑") : ""}</th>)}</tr></thead>
        <tbody>{shown.slice(0, 400).map((r) => <tr key={r.unique_id} onClick={() => openDossier(r.unique_id)} data-testid={`st-row-${r.unique_id}`}>
          <td className="st-name"><b>{r.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{(r.positions || []).join(", ")} · {r.age}</small></td>
          <td>{r.club}{r.own ? " (you)" : ""}</td><td>{r.top_roles?.[0]?.name || "—"}</td>
          {cols.map((k) => <td key={k} className="mono" style={{ background: shade(pcts[k](get(r, k))) }}>{fmt(k, get(r, k))}</td>)}</tr>)}</tbody></table></div>
      {shown.length > 400 && <p className="note">Showing the first 400; narrow the filters or export to see all {shown.length}.</p>}
      <RoleWeights open={weights} onClose={() => setWeights(false)} roles={meta.roles} />
    </div>
  );
};
