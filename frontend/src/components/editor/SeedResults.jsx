import { useEffect, useState } from "react";
import { Download, Trash2, X } from "lucide-react";
import { api } from "@/lib/api";
import { useGet } from "@/lib/ui";

const Cell = ({ v, onSave, id, type = "text", w = 110, min, max }) => {
  const [x, setX] = useState(v ?? "");
  useEffect(() => { setX(v ?? ""); }, [v]);
  const commit = () => {
    const val = type === "number" ? Math.max(min, Math.min(max, Number(x) || min)) : x;
    if (String(val) === String(v ?? "")) { setX(v ?? ""); return; }
    setX(val);
    onSave(val).then((r) => { if (!r) { setX(v ?? ""); } });
  };
  return <input className={`inp${type === "number" ? " mono" : ""}`} style={{ width: w, height: 28 }} type={type} min={min} max={max} value={x}
    onChange={(e) => setX(e.target.value)} onBlur={commit} data-testid={id} />;
};

const Sel = ({ v, opts, onSave, id, w = 130 }) => (
  <select className="inp" style={{ width: w, height: 28 }} value={v || ""} onChange={(e) => onSave(e.target.value)} data-testid={id}>{opts.map((o) => <option key={o}>{o}</option>)}</select>
);

const NewRow = ({ p, meta, save, drop }) => {
  const roles = Object.values(meta.staff).flat();
  return (
    <tr style={{ cursor: "default" }} data-testid={`seed-row-${p.pid}`}>
      <td><Cell v={p.first_name} onSave={(v) => save(p, { first_name: v })} id={`seed-first-${p.pid}`} /></td>
      <td><Cell v={p.last_name} onSave={(v) => save(p, { last_name: v })} id={`seed-last-${p.pid}`} /></td>
      <td>{p.kind === "player" ? <Sel v={p.position} opts={meta.positions} onSave={(v) => save(p, { position: v })} id={`seed-pos-${p.pid}`} w={80} />
        : <Sel v={p.role} opts={roles} onSave={(v) => save(p, { role: v })} id={`seed-role-${p.pid}`} w={190} />}</td>
      <td><Sel v={p.nationality} opts={meta.nations} onSave={(v) => save(p, { nationality: v })} id={`seed-nat-${p.pid}`} /></td>
      <td><Cell v={p.age} type="number" w={60} min={15} max={75} onSave={(v) => save(p, { age: v })} id={`seed-age-${p.pid}`} /></td>
      <td>{p.kind === "player" ? <Cell v={p.height} type="number" w={66} min={150} max={210} onSave={(v) => save(p, { height: v })} id={`seed-height-${p.pid}`} /> : "—"}</td>
      <td><Sel v={p.ethnicity} opts={meta.ethnicities} onSave={(v) => save(p, { ethnicity: v })} id={`seed-eth-${p.pid}`} w={170} /></td>
      <td><Cell v={p.skin_tone} type="number" w={56} min={1} max={20} onSave={(v) => save(p, { skin_tone: v })} id={`seed-skin-${p.pid}`} /></td>
      <td><Cell v={p.ca} type="number" w={60} min={1} max={meta.caps.ca} onSave={(v) => save(p, { ca: v })} id={`seed-ca-${p.pid}`} /></td>
      <td><Cell v={p.pa} type="number" w={60} min={1} max={meta.caps.pa} onSave={(v) => save(p, { pa: v })} id={`seed-pa-${p.pid}`} /></td>
      <td><button className="ib" onClick={() => drop(p)} title="Leave out" data-testid={`seed-drop-${p.pid}`}><X size={13} /></button></td>
    </tr>
  );
};

const CurRow = ({ p, save, drop }) => (
  <tr style={{ cursor: "default" }} data-testid={`seed-row-${p.pid}`}>
    <td style={{ color: "var(--dim)" }}>{p.current_name}</td>
    <td><Cell v={p.first_name} onSave={(v) => save(p, { first_name: v })} id={`seed-first-${p.pid}`} /></td>
    <td><Cell v={p.last_name} onSave={(v) => save(p, { last_name: v })} id={`seed-last-${p.pid}`} /></td>
    <td>{p.position}</td><td>{p.nationality}{!p.matched_nation && <small className="st n" style={{ marginLeft: 4 }}>closest</small>}</td><td>{p.age}</td><td>{p.club}</td>
    <td><button className="ib" onClick={() => drop(p)} title="Leave out" data-testid={`seed-drop-${p.pid}`}><X size={13} /></button></td>
  </tr>
);

export const SeedResults = ({ d, meta, act, onChange }) => {
  const save = (p, patch) => act(() => api.patch(`/seed/draft/${p.pid}`, patch), null, ["seed-draft"]);
  const drop = (p) => act(() => api.delete(`/seed/draft/${p.pid}`), null, ["seed-draft"]).then(onChange);
  const cur = d.mode === "current";
  return (
    <div className="card" data-testid="seed-results">
      <div className="ttl">Results: {d.people.length} {cur ? "players to rename" : "new people"} called {d.surname}
        <span className="st n">{d.people.filter((p) => p.kind === "player").length} players · {d.people.filter((p) => p.kind === "staff").length} staff</span></div>
      {d.note && <p className="note" data-testid="seed-results-note">{d.note}</p>}
      <p className="note">{cur ? "Only the names change; each player keeps their club, age and ability. Edit any name, or leave someone out." : "Change anything before you seed. Ability can't go above the caps."}</p>
      <div style={{ overflowX: "auto" }}><table className="tbl" style={{ marginTop: 8 }}>
        <thead><tr>{(cur ? ["Now called", "First name", "Surname", "Pos", "Nation", "Age", "Club", ""] : ["First name", "Surname", "Position / role", "Nation", "Age", "Height", "Ethnicity", "Skin", "CA", "PA", ""]).map((h) => <th key={h}>{h}</th>)}</tr></thead>
        <tbody>{d.people.map((p) => (cur ? <CurRow key={p.pid} p={p} save={save} drop={drop} /> : <NewRow key={p.pid} p={p} meta={meta} save={save} drop={drop} />))}</tbody></table></div>
    </div>
  );
};

export const SeedHistory = ({ act }) => {
  const { data = [] } = useGet("seed-history", "/seed/history");
  return (
    <div className="card" data-testid="seed-history"><div className="ttl">Seeded surnames<span className="st n">{data.length}</span></div>
      {!data.length && <p className="note" style={{ marginTop: 6 }}>None yet.</p>}
      {data.map((s) => <div key={s.id} className="row" data-testid={`seed-history-${s.id}`}>
        <div style={{ flex: 1 }}><b>{s.surname}</b><small>{s.count} {s.mode === "new" ? "new people for a new save" : "players renamed in your save"}{s.failed ? ` · ${s.failed} failed` : ""}{s.mode === "current" && s.sample ? " (SAMPLE save)" : ""} · {s.names.join(", ")}…</small>
          {s.file_name && <small className="mono">{s.file_name}</small>}</div>
        {s.mode === "new" && <><a className="btn" href={`${process.env.REACT_APP_BACKEND_URL}/api/seed/history/${s.id}/file`} data-testid={`seed-history-file-${s.id}`}><Download size={12} />File</a>
          <button className="btn btn-d" onClick={() => window.confirm(`Remove the ${s.surname} seed and delete its file?`) && act(() => api.delete(`/seed/history/${s.id}`), "Seed removed and its file deleted", ["seed-history", "editor-state"])} data-testid={`seed-history-remove-${s.id}`}><Trash2 size={12} /></button></>}
      </div>)}
    </div>
  );
};
