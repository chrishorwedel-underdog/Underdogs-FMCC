import { useState } from "react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

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
          {a.url ? <a className="btn" href={a.url} target="_blank" rel="noreferrer" data-testid={`app-get-${a.key}`}>Official page</a> : <span className="st n" title="FMCC doesn't know its official page yet">No official page set</span>}
        </div>))}
    </div>
  );
};
