import { useState } from "react";
import { FileUp } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const Who = ({ r, tag }) => <small style={{ display: "block" }}>{tag}: {r ? `${r.name} ${r.rating}` : "nobody"}</small>;

export const TacticFit = () => {
  const [formation, setFormation] = useState("433");
  const { data } = useGet("tactic-fit", "/squad/tactic-fit", { formation });
  const { data: tactics = [] } = useGet("tactics", "/squad/tactics");
  const { data: shapes = [] } = useGet("shapes", "/squad/shapes");
  const act = useAct();
  const nav = useNavigate();
  const upload = (f) => { const fd = new FormData(); fd.append("file", f); act(() => api.post("/squad/tactics/import", fd), (r) => `${r.name} imported (${r.formation})`, ["tactics"]).then((r) => r && setFormation(r.formation)); };
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 16 }} data-testid="tactic-fit">
      <div className="card"><div className="ttl">Tactic fit · {data?.formation}<span style={{ marginLeft: "auto" }} />
        <select className="inp" style={{ width: 150 }} value={formation} onChange={(e) => setFormation(e.target.value)} data-testid="tactic-formation"><option value="433">4-3-3</option><option value="4231">4-2-3-1</option></select>
        <label className="btn" data-testid="tactic-import"><FileUp size={13} />Import .fmf<input type="file" accept=".fmf" hidden onChange={(e) => { if (e.target.files[0]) upload(e.target.files[0]); e.target.value = ""; }} /></label>
        <button className="btn" onClick={() => act(() => api.post("/squad/tactics", { formation }), "Tactic saved", ["tactics"])} data-testid="tactic-save">Save as tactic</button></div>
        <p className="note" style={{ marginTop: 4 }}>{data?.note} Weakest slots first in Squad gaps.</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(210px,1fr))", gap: 10, marginTop: 10 }}>{data?.slots.map((s) => (
          <div key={s.slot} className="card" style={{ padding: 10, borderColor: data.gaps.some((g) => g.slot === s.slot) ? "var(--amb)" : undefined }} data-testid={`fit-slot-${s.slot}`}>
            <b>{s.label}</b><span className="st n">{s.score}</span><small style={{ display: "block", color: "var(--dim)" }}>{s.role_name}</small>
            <Who r={s.starter} tag="Starter" /><Who r={s.backup} tag="Backup" /><Who r={s.depth} tag="Depth" />
          </div>))}</div>
      </div>
      <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
        <div className="card" data-testid="squad-gaps"><div className="ttl">Squad gaps</div>
          {data?.gaps.map((g) => <div key={g.slot} className="row" style={{ cursor: "pointer" }} onClick={() => nav(`/scouting?group=${g.group}`)} data-testid={`gap-${g.slot}`}><div style={{ flex: 1 }}>{g.label}<small>{g.role_name} · find players</small></div><span className="mono">{g.score}</span></div>)}</div>
        <div className="card" data-testid="shape-advisor"><div className="ttl">Shape advisor</div>
          {shapes.map((s) => <div key={s.key} className="row"><div style={{ flex: 1 }}>{s.name}<small>depth {s.depth}</small></div><span className="mono" style={{ color: "var(--acc)" }}>{s.strength}</span></div>)}</div>
        <div className="card" data-testid="tactics-history"><div className="ttl">Your tactics</div>
          {tactics.map((t) => <div key={t.id} className="row" style={{ cursor: "pointer" }} onClick={() => setFormation(t.formation)}><div style={{ flex: 1 }}>{t.name}<small>{t.source}</small></div></div>)}
          {!tactics.length && <p className="note">Import an .fmf file or save a formation to keep it here.</p>}</div>
      </div>
    </div>
  );
};

export const AppsCard = () => {
  const { data } = useGet("apps", "/apps");
  const act = useAct();
  const [paths, setPaths] = useState({});
  return (
    <div className="card" style={{ marginTop: 20 }} data-testid="apps-card"><div className="ttl">Other Football Manager apps</div>
      <p className="note" style={{ marginTop: 4 }}>FMCC rebuilds their best ideas but never installs or updates these apps for you; their files aren't FMCC's to share.</p>
      {data?.apps.map((a) => (
        <div key={a.key} className="row" data-testid={`app-${a.key}`}>
          <div style={{ flex: 1 }}><b>{a.name}</b><small>{a.kind === "web" ? "Website" : a.installed === null ? "Detected in the Windows program" : a.installed ? `Installed · ${a.path}` : "Not installed"}</small></div>
          {a.kind === "windows" && <><input className="inp" style={{ width: 240, height: 32 }} placeholder="Path to its .exe" defaultValue={a.path || ""} onChange={(e) => setPaths({ ...paths, [a.key]: e.target.value })} data-testid={`app-path-${a.key}`} />
            <button className="btn" disabled={!paths[a.key]} onClick={() => act(() => api.put(`/apps/${a.key}/path`, { path: paths[a.key] }), "Saved", ["apps"])} data-testid={`app-path-save-${a.key}`}>Save</button>
            <button className="btn btn-p" onClick={() => act(() => api.post(`/apps/${a.key}/open`), `${a.name} opened`)} data-testid={`app-open-${a.key}`}>Open</button></>}
          {a.kind === "web" && a.url && <a className="btn btn-p" href={a.url} target="_blank" rel="noreferrer" data-testid={`app-open-${a.key}`}>Open</a>}
          {a.url ? <a className="btn" href={a.url} target="_blank" rel="noreferrer" data-testid={`app-get-${a.key}`}>Get it</a> : <span className="st n" title="FMCC doesn't know its official page yet">No official page set</span>}
        </div>))}
    </div>
  );
};
