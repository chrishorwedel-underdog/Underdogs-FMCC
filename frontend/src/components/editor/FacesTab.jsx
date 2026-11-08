import { useEffect, useRef, useState } from "react";
import { Upload, Shuffle, Trash2, Wand2, FolderOpen, Images } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { FacePicker } from "@/components/editor/FacePicker";

const BASE = `${process.env.REACT_APP_BACKEND_URL}/api/editor/image`;

export const Pic = ({ kind, uid, rev, size = 44, label }) => {
  const [bad, setBad] = useState(false);
  useEffect(() => { setBad(false); }, [uid, rev]);
  const key = `${uid}-${rev || "ng"}`;
  if (bad) return <span className="pic none" style={{ width: size, height: size }} data-testid={`${kind}-none-${uid}`}>{label?.slice(0, 2).toUpperCase()}</span>;
  return <img key={key} className="pic" src={`${BASE}/${kind}/${uid}?v=${rev || "ng"}`} alt={label} width={size} height={size} onError={() => setBad(true)} data-testid={`${kind}-img-${uid}`} />;
};

const NationFolders = ({ s, act }) => {
  const [m, setM] = useState(s.nation_folders || {});
  const { data } = useGet("editor-players-missing", "/editor/players", { missing: true, limit: 300 });
  const nations = [...new Set((data?.players || []).map((p) => p.nationality).filter(Boolean))].sort();
  if (!nations.length) return null;
  return (
    <div style={{ marginTop: 10 }} data-testid="nation-folders">
      <div className="eyebrow">NG_Regens folder for each nationality without faces</div>
      {nations.map((n) => (
        <div className="row" key={n}><div style={{ flex: 1 }}>{n}</div>
          <select className="inp" style={{ width: 200, height: 32 }} value={m[n] || ""} onChange={(e) => setM({ ...m, [n]: e.target.value })} data-testid={`nation-folder-${n}`}>
            <option value="">{s.ngregens.folders.find((f) => f.toLowerCase() === n.toLowerCase()) ? "Same name (automatic)" : "Not set"}</option>
            {s.ngregens.folders.map((f) => <option key={f} value={f}>{f}</option>)}
          </select></div>))}
      <button className="btn" style={{ marginTop: 8 }} onClick={() => act(() => api.put("/editor/nation-folders", { mapping: m }), "Folders saved", ["editor-status"])} data-testid="nation-folders-save">Save folders</button>
    </div>
  );
};

const Row = ({ p, act, canPick, onPick, hasPack }) => {
  const ref = useRef(null);
  const upload = (f) => { const fd = new FormData(); fd.append("file", f); act(() => api.post(`/editor/faces/${p.unique_id}`, fd), `New face for ${p.name}`, ["editor-players", "editor-status", "editor-players-missing"]); };
  return (
    <tr style={{ cursor: "default" }} data-testid={`face-row-${p.unique_id}`}>
      <td><Pic kind="face" uid={p.unique_id} rev={p.image_rev} label={p.name} /></td>
      <td><b style={{ color: "var(--text)" }}>{p.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{p.age} · {p.nationality} · {p.club}</small></td>
      <td>{p.face ? <span className={`st ${p.custom ? "b" : "ok"}`} data-testid={`face-source-${p.unique_id}`}>{p.face}</span> : <span className="st a" data-testid={`face-source-${p.unique_id}`}>No face</span>}
        {p.revisions > 0 && <small style={{ display: "block", color: "var(--dim)" }}>{p.revisions} version(s) kept</small>}</td>
      <td style={{ whiteSpace: "nowrap" }}>
        <input ref={ref} type="file" accept="image/png,image/jpeg" hidden onChange={(e) => e.target.files[0] && upload(e.target.files[0])} data-testid={`face-file-${p.unique_id}`} />
        <button className="btn" onClick={() => ref.current.click()} data-testid={`face-upload-${p.unique_id}`}><Upload size={13} />Upload</button>{" "}
        <button className="btn" onClick={() => onPick(p)} data-testid={`face-pick-${p.unique_id}`}><Images size={13} />Pick face</button>{" "}
        {canPick && <button className="btn" onClick={() => act(() => api.post(`/editor/faces/${p.unique_id}/another`), "Another NG_Regens face picked", ["editor-players", "editor-players-missing", "editor-status", "ng-folder"])} data-testid={`face-another-${p.unique_id}`}><Shuffle size={13} />Another NG_Regens</button>}{" "}
        {p.custom && <button className="btn btn-d" onClick={() => act(() => api.delete(`/editor/faces/${p.unique_id}`), "FMCC face removed", ["editor-players", "editor-status", "editor-players-missing"])} data-testid={`face-remove-${p.unique_id}`}><Trash2 size={13} /></button>}
      </td>
    </tr>
  );
};

export const FacesTab = ({ s }) => {
  const act = useAct();
  const [q, setQ] = useState("");
  const [missing, setMissing] = useState(false);
  const [picking, setPicking] = useState(null);
  const { data } = useGet("editor-players", "/editor/players", { q, missing });
  const folderFor = (p) => s.nation_folders?.[p.nationality] || s.ngregens.folders.find((f) => f.toLowerCase() === (p.nationality || "").toLowerCase());
  const fill = () => act(() => api.post("/editor/fill-missing-faces"), (r) => `${r.filled} face(s) added${Object.keys(r.unmatched).length ? ` · no folder set for ${Object.keys(r.unmatched).join(", ")}` : ""}`, ["editor-players", "editor-status", "editor-players-missing"]);
  return (
    <div className="homegrid">
      <div className="card" style={{ padding: 8 }} data-testid="faces-card">
        <div style={{ display: "flex", gap: 8, padding: 10, flexWrap: "wrap" }}>
          <input className="inp" style={{ maxWidth: 280 }} placeholder="Search players or clubs" value={q} onChange={(e) => setQ(e.target.value)} data-testid="faces-search" />
          <label className="chipx"><input type="checkbox" checked={missing} onChange={(e) => setMissing(e.target.checked)} data-testid="faces-missing-only" />Only players without a face</label>
          <span className="note" style={{ marginLeft: "auto", alignSelf: "center" }} data-testid="faces-total">{data?.total ?? "…"} players</span>
        </div>
        <table className="tbl"><thead><tr><th /><th>Player</th><th>Face</th><th>Change</th></tr></thead>
          <tbody>{(data?.players || []).map((p) => <Row key={p.unique_id} p={p} act={act} onPick={setPicking} hasPack={s.ngregens.installed && s.ngregens.folders.length > 0} canPick={!!folderFor(p)} />)}</tbody></table>
        {picking && <FacePicker player={picking} folders={s.ngregens.folders} defaultFolder={folderFor(picking)} onClose={() => setPicking(null)} />}
      </div>
      <div className="card" style={{ alignSelf: "start" }} data-testid="ngregens-card">
        <div className="ttl"><FolderOpen size={15} />NG_Regens<span style={{ marginLeft: "auto" }} className={`st ${s.ngregens.installed ? "ok" : "a"}`} data-testid="ngregens-status">{s.ngregens.installed ? `${s.ngregens.faces} faces mapped` : "Not found"}</span></div>
        <p className="note" style={{ marginTop: 6 }}>{s.ngregens.installed
          ? <>FMCC reads NG_Regens's own face list and never edits its files. Your changes go into FMCC's folder next to it.{!s.desktop && " Browser preview: this is a small SAMPLE stand-in pack with drawn portraits, not the real NG_Regens."}</>
          : <>Install NG_Regens from ngregens.org, unzip its picture pack into FM's graphics folder and run its scan. FMCC then builds on it.</>}</p>
        <p className="note mono" style={{ marginTop: 6, fontSize: 11 }}>{s.ngregens.folder}</p>
        <button className="btn btn-p" style={{ marginTop: 10 }} disabled={!s.ngregens.installed} onClick={fill} data-testid="fill-missing-button"><Wand2 size={13} />Give a face to everyone without one</button>
        {s.ngregens.installed && <NationFolders s={s} act={act} key={JSON.stringify(s.nation_folders)} />}
      </div>
    </div>
  );
};
