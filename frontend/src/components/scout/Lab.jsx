import { useState } from "react";
import { Plus, Trash2, Download, FileUp, Search } from "lucide-react";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer, ReferenceArea, LineChart, Line, Legend } from "recharts";
import { api } from "@/lib/api";
import { useGet, useAct, money } from "@/lib/ui";
import { useScout, fmtMoney } from "./ctx";

const FKEYS = ["formulas", "scout-meta", "scout-players", "scatter", "quadrant"];

export const FormulasTab = () => {
  const { data } = useGet("formulas", "/scout/formulas");
  const [f, setF] = useState({ key: "", name: "", expr: "" });
  const [prev, setPrev] = useState(null);
  const act = useAct();
  const check = async (expr) => { setF((x) => ({ ...x, expr })); if (expr.trim()) setPrev((await api.post("/scout/formulas/preview", { name: "x", expr })).data); else setPrev(null); };
  const save = () => act(() => api.put(`/scout/formulas/${f.key}`, { name: f.name, expr: f.expr }), "Formula saved", FKEYS).then((r) => r && setF({ key: "", name: "", expr: "" }));
  const exportAll = () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify({ formulas: data.items.map(({ key, name, expr }) => ({ key, name, expr })) }, null, 2)], { type: "application/json" })); a.download = "fmcc-formulas.json"; a.click(); };
  const importFile = async (file) => { try { const j = JSON.parse(await file.text()); act(() => api.post("/scout/formulas/import", j), (r) => `${r.imported.length} formulas imported`, FKEYS); } catch { act(() => Promise.reject({ response: { data: { detail: "That isn't an FMCC formulas file" } } })); } };
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }} data-testid="formulas-tab">
      <div className="card"><div className="ttl"><Plus size={14} />Write a formula<span className="st n">{data?.items.length || 0}/{data?.limit}</span></div>
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <input className="inp" style={{ width: 140 }} placeholder="short_name" value={f.key} onChange={(e) => setF({ ...f, key: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "") })} data-testid="formula-key" />
          <input className="inp" placeholder="Name, e.g. Finishing vs xG" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} data-testid="formula-name" /></div>
        <textarea className="inp mono" style={{ height: 80, marginTop: 8, padding: 10 }} maxLength={300} placeholder="npg - npxg" value={f.expr} onChange={(e) => check(e.target.value)} data-testid="formula-expr" />
        <p className="note" style={{ marginTop: 6 }}>Use any stat key, minutes, age, value, wage, grade, c_ for computed stats and f_ for your other formulas. + − * /, brackets, min, max, abs, if(condition, then, otherwise).</p>
        {prev && (prev.ok ? <div className="soon" data-testid="formula-preview">{prev.rows.map((r) => <div key={r.name}>{r.name}: <b className="mono">{r.value ?? "blank"}</b></div>)}<small>{prev.note}</small></div>
          : <div className="soon" style={{ color: "var(--red)" }} data-testid="formula-error">{prev.error}</div>)}
        <button className="btn btn-p" style={{ marginTop: 10 }} disabled={!f.key || !f.name || !prev?.ok} onClick={save} data-testid="formula-save">Save formula</button>
        <details style={{ marginTop: 10 }}><summary className="note">Stat keys</summary><p className="note mono" style={{ fontSize: 11 }}>{data?.names.join(" · ")}</p></details>
      </div>
      <div className="card"><div className="ttl">Your formulas<span style={{ marginLeft: "auto" }} />
        <button className="btn" disabled={!data?.items.length} onClick={exportAll} data-testid="formula-export"><Download size={12} />Export</button>
        <label className="btn" data-testid="formula-import"><FileUp size={12} />Import<input type="file" accept=".json" hidden onChange={(e) => { if (e.target.files[0]) importFile(e.target.files[0]); e.target.value = ""; }} /></label></div>
        {data?.items.map((x) => <div key={x.key} className="row" data-testid={`formula-${x.key}`}><div style={{ flex: 1 }}>{x.name}<small className="mono">{x.key} = {x.expr} · version {x.revision}</small></div>
          <button className="btn" onClick={() => setF({ key: x.key, name: x.name, expr: x.expr })} data-testid={`formula-edit-${x.key}`}>Edit</button>
          <button className="btn btn-d" onClick={() => act(() => api.delete(`/scout/formulas/${x.key}`), "Formula removed", FKEYS)} data-testid={`formula-delete-${x.key}`}><Trash2 size={12} /></button></div>)}
        {!data?.items.length && <p className="note">No formulas yet. They appear as columns in Players, on the Scatter and Quadrant charts and in filters.</p>}
      </div>
    </div>
  );
};

const Cond = ({ c, set, del, fields }) => (
  <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
    <select className="inp" style={{ width: 120, height: 30 }} value={c.kind} onChange={(e) => set({ ...c, kind: e.target.value })}><option value="value">Value</option><option value="stat">Stat vs stat</option><option value="pct">Percentile</option></select>
    <select className="inp" style={{ width: 200, height: 30 }} value={c.kind === "stat" ? c.a : c.field} onChange={(e) => set({ ...c, [c.kind === "stat" ? "a" : "field"]: e.target.value })}>{fields.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
    <select className="inp" style={{ width: 60, height: 30 }} value={c.cmp} onChange={(e) => set({ ...c, cmp: e.target.value })}>{[">=", ">", "<=", "<", "="].map((o) => <option key={o}>{o}</option>)}</select>
    {c.kind === "stat" ? <select className="inp" style={{ width: 200, height: 30 }} value={c.b} onChange={(e) => set({ ...c, b: e.target.value })}>{fields.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
      : <input className="inp" style={{ width: 80, height: 30 }} type="number" value={c.value} onChange={(e) => set({ ...c, value: Number(e.target.value) })} />}
    {c.kind === "pct" && <select className="inp" style={{ width: 140, height: 30 }} value={c.pool} onChange={(e) => set({ ...c, pool: e.target.value })}><option value="position">same position</option><option value="league">same league</option><option value="save">whole save</option></select>}
    <button className="btn" onClick={del}><Trash2 size={11} /></button>
  </div>
);

const Group = ({ g, set, del, fields, depth }) => {
  const upd = (i, v) => set({ ...g, items: g.items.map((x, j) => (j === i ? v : x)) });
  const rm = (i) => set({ ...g, items: g.items.filter((_, j) => j !== i) });
  return (
    <div style={{ border: "1px solid var(--line2)", borderRadius: 12, padding: 8, display: "grid", gap: 6 }} data-testid={`adv-group-${depth}`}>
      <div style={{ display: "flex", gap: 6 }}><div className="seg">{["and", "or"].map((o) => <button key={o} className={g.op === o ? "on" : ""} onClick={() => set({ ...g, op: o })} data-testid={`adv-op-${depth}-${o}`}>{o.toUpperCase()}</button>)}</div>
        <button className="btn" onClick={() => set({ ...g, items: [...g.items, { kind: "value", field: "minutes", cmp: ">=", value: 900, a: "npg", b: "npxg", pool: "position" }] })} data-testid={`adv-add-${depth}`}>+ condition</button>
        {depth < 2 && <button className="btn" onClick={() => set({ ...g, items: [...g.items, { op: "or", items: [] }] })} data-testid={`adv-add-group-${depth}`}>+ group</button>}
        {del && <button className="btn" onClick={del}><Trash2 size={11} /></button>}</div>
      {g.items.map((x, i) => (x.items ? <Group key={i} g={x} set={(v) => upd(i, v)} del={() => rm(i)} fields={fields} depth={depth + 1} /> : <Cond key={i} c={x} set={(v) => upd(i, v)} del={() => rm(i)} fields={fields} />))}
    </div>
  );
};

export const AdvFilter = ({ value, onChange, meta }) => {
  const [g, setG] = useState(value || { op: "and", items: [] });
  const fields = [["minutes", "Minutes"], ["age", "Age"], ["value", "Value"], ["wage", "Wage"], ["grade", "Grade"], ...(meta?.metrics || []).map((m) => [m.key, m.label]),
    ...(meta?.archetypes || []).map((a) => [`c:${a.key}`, a.name]), ...(meta?.formulas || []).map((f) => [`f:${f.key}`, `Formula: ${f.name}`])];
  return (
    <div className="card" style={{ padding: 10, marginBottom: 12 }} data-testid="adv-filter">
      <Group g={g} set={setG} fields={fields} depth={0} />
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}><button className="btn btn-p" onClick={() => onChange(g.items.length ? g : null)} data-testid="adv-apply"><Search size={12} />Apply filter</button>
        <button className="btn" onClick={() => { setG({ op: "and", items: [] }); onChange(null); }} data-testid="adv-clear">Clear</button>
        <span className="note">Saved with your searches. Uses only stats, price, age and minutes, so nothing hidden can be found in Fair play.</span></div>
    </div>
  );
};

export const Quadrant = () => {
  const { openPlayer, prefs } = useScout();
  const { data: meta } = useGet("scout-meta", "/scout/meta");
  const [perf, setPerf] = useState("grade");
  const { data } = useGet("quadrant", "/scout/quadrant", { perf });
  const pts = data?.points || [];
  const max = { c: Math.max(1, ...pts.map((p) => p.cost)), p: Math.max(1, ...pts.map((p) => p.perf)), pm: Math.min(0, ...pts.map((p) => p.perf)) };
  return (
    <div className="card" style={{ marginTop: 16 }} data-testid="quadrant-card">
      <div className="ttl">Quadrant: performance against total cost<span style={{ marginLeft: "auto" }} />
        <select className="inp" style={{ width: 240 }} value={perf} onChange={(e) => setPerf(e.target.value)} data-testid="quadrant-perf"><option value="grade">Global grade</option>
          {meta?.archetypes.map((a) => <option key={a.key} value={`c:${a.key}`}>{a.name}</option>)}{meta?.formulas.map((f) => <option key={f.key} value={`f:${f.key}`}>Formula: {f.name}</option>)}</select></div>
      <div style={{ height: 420, marginTop: 8 }}><ResponsiveContainer><ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
        {data?.mid_cost != null && <>
          <ReferenceArea x1={0} x2={data.mid_cost} y1={data.mid_perf} y2={max.p} fill="#34D399" fillOpacity={0.05} label={{ value: "Hidden gems", position: "insideTopLeft", fill: "#34D399", fontSize: 11 }} />
          <ReferenceArea x1={data.mid_cost} x2={max.c} y1={data.mid_perf} y2={max.p} fill="#4C8DFF" fillOpacity={0.05} label={{ value: "Stars", position: "insideTopRight", fill: "#4C8DFF", fontSize: 11 }} />
          <ReferenceArea x1={data.mid_cost} x2={max.c} y1={max.pm} y2={data.mid_perf} fill="#F87171" fillOpacity={0.05} label={{ value: "Overpriced", position: "insideBottomRight", fill: "#F87171", fontSize: 11 }} />
          <ReferenceArea x1={0} x2={data.mid_cost} y1={max.pm} y2={data.mid_perf} fill="#9CA3AF" fillOpacity={0.04} label={{ value: "Avoid", position: "insideBottomLeft", fill: "#9CA3AF", fontSize: 11 }} />
          <ReferenceLine x={data.mid_cost} stroke="#F2B54A" strokeDasharray="4 4" /><ReferenceLine y={data.mid_perf} stroke="#F2B54A" strokeDasharray="4 4" /></>}
        <XAxis type="number" dataKey="cost" stroke="#6B7280" fontSize={11} tickFormatter={money} domain={[0, max.c]} /><YAxis type="number" dataKey="perf" stroke="#6B7280" fontSize={11} />
        <Tooltip content={({ active, payload }) => (active && payload?.[0] ? <div className="card" style={{ padding: 8, fontSize: 12 }}><b>{payload[0].payload.name}</b><br />{payload[0].payload.zone} · cost {fmtMoney(payload[0].payload.cost, prefs)}</div> : null)} />
        <Scatter data={pts} fill="#4C8DFF" fillOpacity={0.75} onClick={(p) => openPlayer(p.unique_id)} cursor="pointer" />
      </ScatterChart></ResponsiveContainer></div>
      <p className="note">Total cost = value + wage × contract weeks left (bonuses aren't in the save). Click a dot to open the profile.</p>
    </div>
  );
};

export const Replacement = ({ uid }) => {
  const { prefs, openPlayer } = useScout();
  const [caps, setCaps] = useState({});
  const [on, setOn] = useState(false);
  const { data } = useGet("replacement", `/scout/replacement/${uid}`, { uid, ...caps }, { enabled: on });
  if (!on) return <button className="btn" onClick={() => setOn(true)} data-testid="profile-find-replacement"><Search size={13} />Find a replacement</button>;
  const cap = (k, m) => (e) => setCaps({ ...caps, [k]: e.target.value ? Math.round(Number(e.target.value) * m) : undefined });
  return (
    <div className="card" style={{ padding: 12 }} data-testid="replacement-card"><div className="ttl">Replacements for {data?.target.name}</div>
      <div style={{ display: "flex", gap: 6, marginTop: 6 }}><input className="inp" style={{ height: 30 }} type="number" placeholder="Max fee £m" onChange={cap("max_value", 1e6)} data-testid="repl-max-value" />
        <input className="inp" style={{ height: 30 }} type="number" placeholder="Max wage £k/wk" onChange={cap("max_wage", 1e3)} data-testid="repl-max-wage" /><input className="inp" style={{ height: 30 }} type="number" placeholder="Max age" onChange={cap("max_age", 1)} data-testid="repl-max-age" /></div>
      {data?.rows.map((r) => <div key={r.unique_id} className="row" style={{ cursor: "pointer" }} onClick={() => openPlayer(r.unique_id)} data-testid={`repl-${r.unique_id}`}>
        <div style={{ flex: 1 }}>{r.name}<small>{r.club} · {r.age} · style {r.style}%</small></div><span className="mono">{r.similarity}%</span>
        <span className="mono" style={{ width: 90, textAlign: "right", color: r.saving > 0 ? "var(--grn)" : "var(--red)" }}>{r.saving > 0 ? "saves " : "costs "}{fmtMoney(Math.abs(r.saving), prefs)}</span></div>)}
      {data && !data.rows.length && <p className="note">Nobody matches these caps.</p>}
    </div>
  );
};

export const PriceExplained = ({ uid, view }) => {
  const { data } = useGet("price", `/scout/price/${uid}`, { uid, view });
  if (!data) return null;
  return (
    <div className="card" style={{ padding: 12 }} data-testid="price-explained"><div className="ttl">Price explained</div>
      {data.factors.map((f) => <div key={f.factor} className="row" style={{ fontSize: 12.5 }}><span style={{ width: 120 }}>{f.factor}</span><span className={`st ${f.effect === "raises" ? "ok" : "a"}`} style={{ marginLeft: 0 }}>{f.effect}</span><small style={{ marginLeft: 8, marginTop: 0 }}>{f.detail}</small></div>)}
      <p className="note" style={{ marginTop: 6 }}>{data.note}</p>
    </div>
  );
};

export const HistoryChart = ({ seasons }) => (seasons?.length > 1 ? (
  <div style={{ height: 180 }} data-testid="profile-history-chart"><ResponsiveContainer><LineChart data={seasons}>
    <XAxis dataKey="season" stroke="#6B7280" fontSize={11} /><YAxis yAxisId="g" stroke="#4C8DFF" fontSize={11} /><YAxis yAxisId="v" orientation="right" stroke="#A3E635" fontSize={11} tickFormatter={money} />
    <Tooltip contentStyle={{ background: "#14181D", border: "1px solid #2A2F36", fontSize: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
    <Line yAxisId="g" dataKey="grade" name="Grade (form)" stroke="#4C8DFF" /><Line yAxisId="v" dataKey="value" name="Value" stroke="#A3E635" /></LineChart></ResponsiveContainer></div>) : null);
