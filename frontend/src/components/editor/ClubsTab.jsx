import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Trash2, Save, ListPlus, Ban } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { Pic } from "@/components/editor/FacesTab";

const Names = ({ c, act }) => {
  const [n, setN] = useState({ long: c.rename?.long || c.name, short: c.rename?.short || c.name.split(" ")[0] });
  return (
    <div className="card" data-testid="club-names-card"><div className="ttl">Name</div>
      <p className="note" style={{ marginTop: 4 }}>Written to a name file FM reads when it loads a save. It works on careers already started; restart FM to see it.</p>
      <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
        <input className="inp" value={n.long} maxLength={60} onChange={(e) => setN({ ...n, long: e.target.value })} data-testid="club-long-name" />
        <input className="inp" value={n.short} maxLength={30} onChange={(e) => setN({ ...n, short: e.target.value })} data-testid="club-short-name" />
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <button className="btn btn-p" disabled={n.long.trim().length < 2 || n.short.trim().length < 2} onClick={() => act(() => api.put(`/editor/clubs/${c.uid}/name`, n), "Rename saved", ["editor-clubs", "editor-status"])} data-testid="club-rename-save"><Save size={13} />Save name</button>
        {c.rename && <button className="btn btn-d" onClick={() => act(() => api.delete(`/editor/clubs/${c.uid}/name`), "Rename removed", ["editor-clubs", "editor-status"])} data-testid="club-rename-remove"><Trash2 size={13} />Use FM's name</button>}
      </div>
    </div>
  );
};

const Logo = ({ c, act }) => {
  const ref = useRef(null);
  const upload = (f) => { const fd = new FormData(); fd.append("file", f); act(() => api.post(`/editor/clubs/${c.uid}/logo`, fd), "Logo saved", ["editor-clubs", "editor-status"]); };
  return (
    <div className="card" data-testid="club-logo-card"><div className="ttl">Logo</div>
      <div style={{ display: "flex", gap: 14, alignItems: "center", marginTop: 10 }}>
        <Pic kind="logo" uid={c.uid} rev={c.logo_rev} size={72} label={c.name} />
        <input ref={ref} type="file" accept="image/png,image/jpeg" hidden onChange={(e) => e.target.files[0] && upload(e.target.files[0])} data-testid="club-logo-file" />
        <button className="btn" onClick={() => ref.current.click()} data-testid="club-logo-upload"><Upload size={13} />Upload logo</button>
        {c.logo && <button className="btn btn-d" onClick={() => act(() => api.delete(`/editor/clubs/${c.uid}/logo`), "Logo removed", ["editor-clubs", "editor-status"])} data-testid="club-logo-remove"><Trash2 size={13} /></button>}
      </div>
    </div>
  );
};

const Attributes = ({ uid, act }) => {
  const nav = useNavigate();
  const { data } = useGet("club-attrs", `/editor/clubs/${uid}/attributes`, { uid });
  const [v, setV] = useState({});
  useEffect(() => { setV({}); }, [uid]);
  if (!data) return <p className="note">Reading club…</p>;
  const changed = Object.fromEntries(Object.entries(v).filter(([k, x]) => x !== "" && Number(x) !== data.fields.find((f) => f.key === k)?.value).map(([k, x]) => [k, Number(x)]));
  const queue = async () => { const r = await act(() => api.post(`/editor/clubs/${uid}/attributes`, { values: changed }), (x) => `${x.queued} change(s) added to Game changes`, ["changes", "club-attrs"]); if (r) { setV({}); nav("/changes"); } };
  return (
    <div className="card" data-testid="club-attributes-card"><div className="ttl">Club attributes</div>
      {data.read_only ? <p className="note" style={{ marginTop: 6 }}>{data.read_only}</p> : <>
        <p className="note" style={{ marginTop: 4 }}>Changes go to Game changes, where you approve them as a batch with a preview, checks, a save backup and undo.</p>
        <div className="sgrid" style={{ marginTop: 8 }}>{data.fields.map((f) => (
          <label key={f.key} style={{ fontSize: 12.5 }}>{f.label}{f.min != null && <small style={{ color: "var(--dim)" }}> ({f.min}–{f.max})</small>}
            <input className="inp mono" type="number" value={v[f.key] ?? f.value} onChange={(e) => setV({ ...v, [f.key]: e.target.value })} data-testid={`club-attr-${f.key}`} /></label>))}</div>
        <button className="btn btn-red" style={{ marginTop: 12 }} disabled={!Object.keys(changed).length} onClick={queue} data-testid="club-attrs-queue"><ListPlus size={13} />Queue {Object.keys(changed).length} change(s)</button>
      </>}
      <div className="eyebrow" style={{ marginTop: 14 }}>Not editable yet</div>
      {data.not_editable.map((n) => <div className="row" key={n}><Ban size={13} style={{ color: "var(--dim)" }} /><small style={{ margin: 0 }}>{n}</small></div>)}
    </div>
  );
};

export const ClubsTab = () => {
  const act = useAct();
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(null);
  const { data = [] } = useGet("editor-clubs", "/editor/clubs", { q });
  const c = data.find((x) => x.uid === sel) || data[0];
  return (
    <div className="homegrid" style={{ gridTemplateColumns: "280px minmax(0,1fr)" }}>
      <div className="card" style={{ padding: 8, alignSelf: "start" }} data-testid="club-list">
        <input className="inp" placeholder="Search clubs" value={q} onChange={(e) => setQ(e.target.value)} data-testid="club-search" />
        {data.map((x) => <div key={x.uid} className={`pi${c?.uid === x.uid ? " sel" : ""}`} onClick={() => setSel(x.uid)} data-testid={`club-item-${x.uid}`}>
          <span>{x.rename?.long || x.name}</span><small>{x.rename ? `was ${x.name}` : x.league || ""}{x.logo ? " · logo" : ""}</small></div>)}
      </div>
      {c && <div style={{ display: "grid", gap: 16, alignContent: "start" }} key={c.uid}>
        <div className="sgrid"><Logo c={c} act={act} /><Names c={c} act={act} /></div>
        <Attributes uid={c.uid} act={act} />
      </div>}
    </div>
  );
};
