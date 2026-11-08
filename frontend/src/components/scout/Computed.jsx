import { useState } from "react";
import { AlertTriangle, RotateCcw, Trash2, Plus } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { useScout, ContractTag } from "./ctx";

const KEYS = ["computed", "scout-meta", "scout-players", "tactical"];

const Archetype = ({ a, labels }) => {
  const [w, setW] = useState(a.metrics);
  const act = useAct();
  const dirty = JSON.stringify(w) !== JSON.stringify(a.metrics);
  return (
    <div className="card" style={{ padding: 14 }} data-testid={`arch-${a.key}`}>
      <div className="ttl">{a.name}{!a.builtin && <span className="st b">Custom</span>}{a.changed?.length > 0 && <span className="st a" title={`Changed from default: ${a.changed.join(", ")}`} data-testid={`arch-changed-${a.key}`}><AlertTriangle size={11} /> differs from default</span>}</div>
      {Object.entries(w).map(([m, v]) => (
        <div key={m} style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 6, fontSize: 12.5 }}>
          <span style={{ flex: 1, color: a.defaults && a.defaults[m] !== v ? "var(--amb)" : "var(--mut)" }}>{labels[m]}{a.phases?.[m] && <span className="tag st n">{a.phases[m] === "in" ? "in poss." : "out of poss."}</span>}</span>
          <input type="range" min="0" max="10" value={v} onChange={(e) => setW({ ...w, [m]: Number(e.target.value) })} data-testid={`arch-weight-${a.key}-${m}`} />
          <span className="mono" style={{ width: 18 }}>{v}</span>
        </div>))}
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <button className="btn btn-p" disabled={!dirty} onClick={() => act(() => api.put(`/scout/computed/${a.key}`, { name: a.name, metrics: w, phases: a.phases }), "Weights saved", KEYS)} data-testid={`arch-save-${a.key}`}>Save weights</button>
        <button className="btn" onClick={() => act(() => api.delete(`/scout/computed/${a.key}`), a.builtin ? "Back to default weights" : "Computed stat removed", KEYS)} data-testid={`arch-reset-${a.key}`}>{a.builtin ? <><RotateCcw size={12} />Default</> : <><Trash2 size={12} />Remove</>}</button>
      </div>
    </div>
  );
};

const NewComputed = ({ metrics, count }) => {
  const [name, setName] = useState("");
  const [sel, setSel] = useState({});
  const [phase, setPhase] = useState({});
  const act = useAct();
  const n = Object.keys(sel).length;
  const save = () => act(() => api.put(`/scout/computed/${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 30) || "custom"}`, { name, metrics: sel, phases: phase }), "Computed stat created", KEYS).then((r) => { if (r) { setName(""); setSel({}); } });
  return (
    <div className="card" style={{ padding: 14 }} data-testid="new-computed">
      <div className="ttl"><Plus size={14} />New computed stat<span className="st n">{count}/6 custom</span></div>
      <input className="inp" style={{ marginTop: 8 }} placeholder="Name, e.g. Ball-carrying 8" value={name} onChange={(e) => setName(e.target.value)} data-testid="new-computed-name" />
      <p className="note" style={{ marginTop: 6 }}>Pick 3 to 12 stats ({n} picked). Weights go from 0 to 10.</p>
      <div style={{ maxHeight: 220, overflowY: "auto", marginTop: 6 }}>{metrics.map((m) => (
        <div key={m.key} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, padding: "3px 0" }}>
          <input type="checkbox" checked={m.key in sel} onChange={(e) => { const s = { ...sel }; if (e.target.checked) s[m.key] = 5; else delete s[m.key]; setSel(s); }} data-testid={`new-computed-pick-${m.key}`} />
          <span style={{ flex: 1 }}>{m.label}</span>
          {m.key in sel && <><select className="inp" style={{ width: 100, height: 28 }} value={phase[m.key] || "in"} onChange={(e) => setPhase({ ...phase, [m.key]: e.target.value })}><option value="in">In poss.</option><option value="out">Out of poss.</option></select>
            <input className="inp" style={{ width: 56, height: 28 }} type="number" min="0" max="10" value={sel[m.key]} onChange={(e) => setSel({ ...sel, [m.key]: Math.max(0, Math.min(10, Number(e.target.value))) })} /></>}
        </div>))}</div>
      <button className="btn btn-p" style={{ marginTop: 10 }} disabled={!name.trim() || n < 3 || n > 12 || count >= 6} onClick={save} data-testid="new-computed-save">Create</button>
    </div>
  );
};

const Tactical = ({ items }) => {
  const { view, openPlayer } = useScout();
  const [t, setT] = useState({ key: "pressing_fwd", in_w: 5, out_w: 5, group: "" });
  const { data = [] } = useGet("tactical", "/scout/tactical", { ...t, view, group: t.group || undefined });
  return (
    <div className="card" style={{ gridColumn: "1 / -1", overflowX: "auto" }} data-testid="tactical-search">
      <div className="ttl">Tactical archetype search</div>
      <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap", marginTop: 8 }}>
        <select className="inp" style={{ width: 240 }} value={t.key} onChange={(e) => setT({ ...t, key: e.target.value })} data-testid="tactical-archetype">{items.map((a) => <option key={a.key} value={a.key}>{a.name}</option>)}</select>
        <label className="note">In possession <input type="range" min="0" max="10" value={t.in_w} onChange={(e) => setT({ ...t, in_w: Number(e.target.value) })} data-testid="tactical-in" /> {t.in_w}</label>
        <label className="note">Out of possession <input type="range" min="0" max="10" value={t.out_w} onChange={(e) => setT({ ...t, out_w: Number(e.target.value) })} data-testid="tactical-out" /> {t.out_w}</label>
      </div>
      <table className="tbl" style={{ marginTop: 8 }}><thead><tr><th>Player</th><th>Age</th><th>Score</th><th>In poss.</th><th>Out of poss.</th><th>Grade</th></tr></thead>
        <tbody>{data.slice(0, 25).map((r) => <tr key={r.unique_id} onClick={() => openPlayer(r.unique_id)} data-testid={`tactical-row-${r.unique_id}`}><td><b>{r.name}</b><ContractTag m={r.months_left} /><small style={{ display: "block", color: "var(--dim)" }}>{r.club} · {r.cohort}</small></td>
          <td>{r.age}</td><td className="mono" style={{ color: "var(--acc)" }}>{r.score}</td><td className="mono">{r.in_score ?? "—"}</td><td className="mono">{r.out_score ?? "—"}</td><td className="mono">{r.grade_global}</td></tr>)}</tbody></table>
    </div>
  );
};

export const ComputedTab = () => {
  const { data } = useGet("computed", "/scout/computed");
  if (!data) return null;
  const labels = Object.fromEntries(data.metrics.map((m) => [m.key, m.label]));
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(320px,1fr))", gap: 14 }} data-testid="computed-tab">
      <Tactical items={data.items} />
      {data.items.map((a) => <Archetype key={`${a.key}-${a.revision || 0}`} a={a} labels={labels} />)}
      <NewComputed metrics={data.metrics} count={data.custom_count} />
    </div>
  );
};

export const RoleScoresTab = () => {
  const { view, openPlayer } = useScout();
  const { data: meta } = useGet("scout-meta", "/scout/meta");
  const [role, setRole] = useState("bpd");
  const { data = [] } = useGet("role-scores", "/scout/roles", { role }, { enabled: view !== "moneyball" });
  if (view === "moneyball") return <div className="soon" data-testid="roles-moneyball">Role scores come from attributes, which Moneyball switches off. Switch to Full or Fair play to see them.</div>;
  return (
    <div className="card" style={{ overflowX: "auto" }} data-testid="role-scores">
      <div className="ttl">Role scores across the whole save<span style={{ marginLeft: "auto" }} />
        <select className="inp" style={{ width: 280 }} value={role} onChange={(e) => setRole(e.target.value)} data-testid="role-select">{meta?.roles.map((r) => <option key={r.key} value={r.key}>{r.name}</option>)}</select></div>
      <table className="tbl" style={{ marginTop: 8 }}><thead><tr><th>#</th><th>Player</th><th>Age</th><th>Club</th><th>Positions</th><th>Suitability</th></tr></thead>
        <tbody>{data.map((r, i) => <tr key={r.unique_id} onClick={() => openPlayer(r.unique_id)} data-testid={`role-row-${r.unique_id}`}><td className="mono">{i + 1}</td><td><b>{r.name}</b>{!r.natural && <span className="tag st n">out of position</span>}</td><td>{r.age}</td><td>{r.club}</td><td>{r.positions?.join(", ")}</td><td className="mono" style={{ color: "var(--acc)" }}>{r.rating}</td></tr>)}</tbody></table>
    </div>
  );
};
