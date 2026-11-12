import { useState } from "react";
import { Plus, X } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct, TabBar } from "@/lib/ui";
import { useScout } from "./ctx";
import { Empty } from "@/components/Empty";

const Results = ({ res, keys, label, open, loosen }) => (
  <div className="card" style={{ padding: 8, overflowX: "auto" }} data-testid="similar-results">
    <p className="note" style={{ padding: "4px 8px 8px" }}>{res.base ? `Closest to ${res.base.name}. ` : ""}{res.how}.</p>
    <table className="tbl pin1">
      <thead><tr><th>Player</th><th>Age</th><th>Club</th>{keys.map((k) => <th key={k} title={label[k]}>{label[k]}</th>)}<th>Similarity</th></tr></thead>
      <tbody>{res.rows.map((r) => (
        <tr key={r.unique_id} onClick={() => open(r.unique_id)} tabIndex={0} onKeyDown={(e) => e.key === "Enter" && open(r.unique_id)} data-row-uid={r.unique_id} data-testid={`similar-row-${r.unique_id}`}>
          <td><b>{r.name}</b></td><td>{r.age}</td><td>{r.club}</td>{keys.map((k) => <td key={k} className="mono">{r.values?.[k] ?? "—"}</td>)}
          <td className="mono" style={{ color: "var(--acc)" }} data-testid={`similar-score-${r.unique_id}`}>{r.similarity}%</td>
        </tr>))}</tbody>
    </table>
    {!res.rows.length && <div style={{ padding: 8 }}><Empty id="similar-empty" reason="nobody" text="Nobody is close enough to every number. Fewer numbers or any position widens the search." actions={loosen} /></div>}
  </div>
);

export const SimilarTab = () => {
  const { openPlayer } = useScout();
  const { data: meta } = useGet("scout-meta", "/scout/meta");
  const act = useAct();
  const [by, setBy] = useState("player");
  const [q, setQ] = useState("");
  const [targets, setTargets] = useState({ npxg: 0.4, xa: 0.2 });
  const [mode, setMode] = useState("p90");
  const [group, setGroup] = useState("");
  const [res, setRes] = useState(null);
  const label = Object.fromEntries((meta?.metrics || []).map((m) => [m.key, m.label]));
  const run = (body) => act(() => api.post("/scout/similar", body), null, []).then((r) => r && setRes(r));
  const search = () => act(() => api.post("/scout/players", { q, limit: 8, view: "full", mode: "p90", gender: "M", source: "save", min_age: 15, max_age: 45, min_minutes: 0, sort: "grade", dir: "desc" }), null, []).then((r) => r && setRes({ pick: r.rows }));
  return (
    <div style={{ display: "grid", gap: 14 }} data-testid="similar-tab">
      <TabBar id="similar-by" value={by} onChange={(v) => { setBy(v); setRes(null); }} tabs={[["player", "Like a player"], ["numbers", "Match my numbers"]]} />
      {by === "player" && <div style={{ display: "flex", gap: 8 }}>
        <input className="inp" style={{ width: 260 }} placeholder="Type a player's name" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && q.trim() && search()} data-testid="similar-search" />
        <button className="btn btn-p" disabled={!q.trim()} onClick={search} data-testid="similar-search-button">Find</button></div>}
      {res?.pick && <div className="card" data-testid="similar-pick">{res.pick.map((p) => <div className="row" key={p.unique_id}><div style={{ flex: 1 }}>{p.name}<small>{p.club} · {p.age}</small></div>
        <button className="btn" onClick={() => run({ unique_id: p.unique_id })} data-testid={`similar-pick-${p.unique_id}`}>Find players like him</button></div>)}
        {!res.pick.length && <Empty id="similar-pick-empty" reason="nobody" text={`No player called "${q}" in the scouting data. Check the spelling or try just the surname.`} />}</div>}
      {by === "numbers" && meta && <div className="card" data-testid="similar-targets">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
          <div className="seg">{[["p90", "Per 90"], ["total", "Season totals"]].map(([k, l]) => <button key={k} className={mode === k ? "on" : ""} onClick={() => setMode(k)} data-testid={`similar-mode-${k}`}>{l}</button>)}</div>
          <select className="inp" style={{ width: 170 }} value={group} onChange={(e) => setGroup(e.target.value)} data-testid="similar-group"><option value="">Any position</option>{Object.entries(meta.groups).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></div>
        {Object.entries(targets).map(([k, v]) => <div key={k} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
          <select className="inp" style={{ width: 260 }} value={k} onChange={(e) => { const n = { ...targets }; delete n[k]; setTargets({ ...n, [e.target.value]: v }); }} data-testid={`similar-metric-${k}`}>{meta.metrics.filter((m) => m.key === k || !(m.key in targets)).map((m) => <option key={m.key} value={m.key}>{mode === "total" ? m.label.replace(" / 90", " (season total)") : m.label}</option>)}</select>
          <input className="inp mono" type="number" step="0.01" style={{ width: 100 }} value={v} onChange={(e) => setTargets({ ...targets, [k]: Number(e.target.value) })} data-testid={`similar-value-${k}`} />
          <button className="ib" aria-label="Remove" onClick={() => { const n = { ...targets }; delete n[k]; setTargets(n); }} data-testid={`similar-remove-${k}`}><X size={13} /></button></div>)}
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button className="btn" disabled={Object.keys(targets).length >= 8} onClick={() => { const m = meta.metrics.find((x) => !(x.key in targets)); if (m) { setTargets({ ...targets, [m.key]: 0 }); } }} data-testid="similar-add-metric"><Plus size={13} />Add a number</button>
          <button className="btn btn-p" disabled={!Object.keys(targets).length} onClick={() => run({ targets, mode, group: group || null })} data-testid="similar-run">Find closest players</button></div>
      </div>}
      {res?.rows && <Results res={res} keys={by === "numbers" ? Object.keys(targets) : []} label={label} open={openPlayer}
        loosen={by === "numbers" ? [...(group ? [["Any position", () => { setGroup(""); run({ targets, mode, group: null }); }]] : []), ...(Object.keys(targets).length > 1 ? [["Drop the last number", () => { const n = { ...targets }; delete n[Object.keys(n).pop()]; setTargets(n); run({ targets: n, mode, group: group || null }); }]] : [])] : []} />}
    </div>
  );
};
