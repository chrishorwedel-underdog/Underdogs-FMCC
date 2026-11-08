import { useRef, useState } from "react";
import { FileUp, RefreshCw, RotateCcw, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const KEYS = ["leagues", "scout-players", "scout-meta", "myclub", "deals"];
const STATUS = { matched: ["Matched", "ok"], confirmed: ["Confirmed", "ok"], unsure: ["Please confirm", "a"], estimated: ["Estimated from reputation", "b"], womens: ["Women's league: not adjusted", "n"] };

const LeagueRow = ({ l, rows }) => {
  const act = useAct();
  const [m, setM] = useState(l.multiplier);
  const [st, tone] = STATUS[l.status];
  return (
    <tr style={{ cursor: "default" }} data-testid={`league-row-${l.name}`}>
      <td><b>{l.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{l.country || "Country unknown"} · reputation {l.reputation ?? "—"}</small></td>
      <td><span className={`st ${tone}`} data-testid={`league-status-${l.name}`}>{st}</span>{l.between?.some(Boolean) && <small style={{ display: "block", color: "var(--dim)", marginTop: 4 }}>{l.between.every(Boolean) ? `between ${l.between.join(" and ")}` : `placed from ${l.between.filter(Boolean)[0]} (nearest on the list)`}</small>}</td>
      <td>{l.status !== "womens" && <select className="inp" style={{ width: 250, height: 32 }} value={l.status === "estimated" ? "" : l.opta_name || ""}
        onChange={(e) => act(() => api.put(`/leagues/${encodeURIComponent(l.name)}/match`, { opta_name: e.target.value || null }), "Match saved", KEYS)} data-testid={`league-match-${l.name}`}>
        <option value="">Not on the list</option>{[...new Set([...(l.candidates || []), ...(l.opta_name ? [l.opta_name] : [])])].map((c) => <option key={c}>{c}</option>)}
        <optgroup label="Whole list">{rows.map((r) => <option key={`all-${r.name}`} value={r.name}>{r.rank}. {r.name}</option>)}</optgroup></select>}</td>
      <td className="mono">{l.opta != null ? l.opta.toFixed(2) : "—"}</td>
      <td><div style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <input className="inp mono" style={{ width: 84, height: 32 }} type="number" step="0.01" value={m} onChange={(e) => setM(e.target.value)} data-testid={`league-mult-${l.name}`} />
        {Number(m) !== l.multiplier && <button className="btn btn-p" onClick={() => act(() => api.put(`/leagues/${encodeURIComponent(l.name)}/multiplier`, { value: Number(m) }), "Multiplier saved", KEYS)} data-testid={`league-mult-save-${l.name}`}>Save</button>}
        {l.edited && <><span className="st a">Edited</span><button className="btn" title={`Back to the formula (${l.auto_multiplier})`} onClick={() => act(() => api.put(`/leagues/${encodeURIComponent(l.name)}/multiplier`, { value: null }), "Back to the formula", KEYS).then(() => setM(l.auto_multiplier))} data-testid={`league-mult-reset-${l.name}`}><RotateCcw size={12} /></button></>}
      </div></td>
    </tr>
  );
};

const Recalc = () => {
  const act = useAct();
  const [reset, setReset] = useState(false);
  const [preview, setPreview] = useState(null);
  const run = (apply) => act(() => api.post("/leagues/recalculate", { apply, reset_edits: reset }), apply ? "Estimated leagues recalculated" : null, apply ? KEYS : ["none"]).then((r) => setPreview(apply ? null : r));
  return (
    <div className="card" data-testid="recalc-card"><div className="ttl"><RefreshCw size={14} />Recalculate from reputations</div>
      <p className="note" style={{ marginTop: 4 }}>Re-places every estimated league using the save's current reputations. You see old and new values before anything is saved.</p>
      <label className="note" style={{ display: "flex", gap: 6, marginTop: 8 }}><input type="checkbox" checked={reset} onChange={(e) => setReset(e.target.checked)} data-testid="recalc-reset-edits" />Also reset my edits</label>
      <button className="btn" style={{ marginTop: 8 }} onClick={() => run(false)} data-testid="recalc-preview">Show the changes</button>
      {preview && <div style={{ marginTop: 8 }} data-testid="recalc-diff">{preview.changes.length ? preview.changes.map((c) => <div key={c.league} className="row">{c.league}<span className="mono" style={{ marginLeft: "auto" }}>{c.old} → {c.new}</span></div>) : <p className="note">Nothing would change.</p>}
        <button className="btn btn-p" style={{ marginTop: 8 }} onClick={() => run(true)} data-testid="recalc-apply">Save these values</button></div>}
    </div>
  );
};

export const LeaguesTab = () => {
  const { data } = useGet("leagues", "/leagues");
  const act = useAct();
  const file = useRef(null);
  const [q, setQ] = useState("");
  if (!data) return null;
  const upload = (f) => { const fd = new FormData(); fd.append("file", f); act(() => api.post("/leagues/import", fd), (r) => `${r.count} leagues imported`, KEYS); };
  return (
    <div style={{ display: "grid", gap: 16 }} data-testid="leagues-tab">
      <div className="card" style={{ overflowX: "auto" }}>
        <div className="ttl">Leagues in your save<span className="st n" data-testid="league-list-meta">{data.list.count} leagues · {data.list.source}{data.list.updated ? ` · ${data.list.updated}` : ""}</span></div>
        <p className="note" style={{ marginTop: 4 }}>Multiplier = (Opta average ÷ {data.list.reference.toFixed(3)})^{data.list.exponent}. The Premier League is 1.000. Global grade = 20 + (local grade − 20) × multiplier.</p>
        <table className="tbl" style={{ marginTop: 8 }}><thead><tr><th>Save league</th><th>Status</th><th>On the list as</th><th>Opta</th><th>Multiplier</th></tr></thead>
          <tbody>{data.leagues.map((l) => <LeagueRow key={`${l.name}-${l.multiplier}`} l={l} rows={data.rows} />)}</tbody></table>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Recalc />
        <div className="card" data-testid="league-list-card"><div className="ttl">The ranking list</div>
          <p className="note" style={{ marginTop: 4 }}>Built in from your workbook. Import a newer one (the workbook or a CSV with Competition, Country and Opta Average) at any time; older lists are kept.</p>
          <input ref={file} type="file" accept=".xlsx,.csv" hidden onChange={(e) => { if (e.target.files[0]) upload(e.target.files[0]); e.target.value = ""; }} data-testid="league-import-input" />
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}><button className="btn" onClick={() => file.current.click()} data-testid="league-import"><FileUp size={13} />Import a list</button>
            {data.list.revision > 0 && <button className="btn" onClick={() => act(() => api.post("/leagues/use-builtin"), "Back to the built-in list", KEYS)} data-testid="league-use-builtin"><Trash2 size={13} />Use the built-in list</button>}</div>
          <p className="note" style={{ marginTop: 10 }} data-testid="league-duplicates">{data.duplicates.length ? `${data.duplicates.length} duplicate entries: FMCC uses the highest-ranked one for each.` : "No duplicate entries in this list."}</p>
          {data.duplicates.map((d) => <div key={`${d.rank}`} className="row">{d.rank}. {d.name}<small style={{ marginLeft: 8 }}>kept #{d.kept}</small></div>)}
        </div>
      </div>
      <div className="card" style={{ overflowX: "auto" }} data-testid="league-full-list"><div className="ttl">All {data.rows.length} leagues<span style={{ marginLeft: "auto" }} /><input className="inp" style={{ width: 220 }} placeholder="Search the list" value={q} onChange={(e) => setQ(e.target.value)} data-testid="league-list-search" /></div>
        <table className="tbl" style={{ marginTop: 8 }}><thead><tr><th>#</th><th>Competition</th><th>Country</th><th>Opta</th><th>Multiplier</th></tr></thead>
          <tbody>{data.rows.filter((r) => !q || `${r.name} ${r.country}`.toLowerCase().includes(q.toLowerCase())).slice(0, q ? 200 : 25).map((r) => <tr key={r.rank} style={{ cursor: "default" }}><td className="mono">{r.rank}</td><td>{r.name}</td><td>{r.country}</td><td className="mono">{r.opta.toFixed(2)}</td><td className="mono">{r.multiplier.toFixed(3)}</td></tr>)}</tbody></table>
        {!q && <p className="note" style={{ padding: 8 }}>Showing the top 25. Search to see the rest.</p>}
      </div>
    </div>
  );
};
