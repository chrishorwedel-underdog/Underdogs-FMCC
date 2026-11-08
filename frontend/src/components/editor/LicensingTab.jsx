import { useRef, useState } from "react";
import { FileUp, ScanSearch, Check, Undo2, Trash2, PenLine } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const KEYS = ["licensing", "editor-clubs", "editor-status", "changes"];

const Sources = ({ d, act }) => {
  const ref = useRef(null);
  const upload = (f) => { const fd = new FormData(); fd.append("file", f); act(() => api.post("/editor/licensing/import", fd), (r) => `${r.name} imported. Nothing changes until you apply it.`, KEYS); };
  return (
    <div className="card" data-testid="fix-sources-card">
      <div className="ttl"><ScanSearch size={15} />Real-names fix files</div>
      <p className="note" style={{ marginTop: 4 }}>FMCC scans the .lnc files in FM's name-file folder and any fix file you import, such as sortitoutsi's real names fix. Files already in FM's folder are active in FM; imported ones only count once you apply them.{!d.desktop && " Browser preview: a SAMPLE fix file and logo pack are used."}</p>
      {d.files.map((f) => (
        <div className="row" key={f.name + f.active} data-testid={`fix-file-${f.name}`}><div style={{ flex: 1 }}><b>{f.name}</b><small>{f.clubs} clubs · {f.comps} competitions · {f.stadiums} stadiums</small></div>
          <span className={`st ${f.active ? "ok" : "n"}`}>{f.active ? "Active in FM" : "Imported"}</span>
          {!f.active && <button className="btn btn-d" onClick={() => act(() => api.delete(`/editor/licensing/import/${encodeURIComponent(f.name)}`), "Imported file removed", KEYS)} data-testid={`fix-file-remove-${f.name}`}><Trash2 size={13} /></button>}</div>))}
      {!d.files.length && <p className="note" style={{ marginTop: 8 }}>No fix files found yet.</p>}
      <input ref={ref} type="file" accept=".lnc" hidden onChange={(e) => e.target.files[0] && upload(e.target.files[0])} data-testid="fix-import-file" />
      <button className="btn" style={{ marginTop: 10 }} onClick={() => ref.current.click()} data-testid="fix-import-button"><FileUp size={13} />Import a fix file</button>
      <div className="eyebrow" style={{ marginTop: 14 }}>Logo packs in your graphics folder</div>
      {d.logo_packs.map((p) => <div className="row" key={p.name}><div style={{ flex: 1 }}>{p.name}</div><small>{p.logos} logos</small></div>)}
      {!d.logo_packs.length && <p className="note" style={{ marginTop: 4 }}>None found. Unzip a logo pack into FM's graphics folder; FM shows its logos by itself.</p>}
    </div>
  );
};

const Clubs = ({ d, act }) => {
  const [sel, setSel] = useState([]);
  const open = d.clubs.filter((c) => c.unlicensed && !c.applied && !c.active_in_fm);
  const toggle = (u) => setSel(sel.includes(u) ? sel.filter((x) => x !== u) : [...sel, u]);
  const target = sel.length ? sel : open.map((c) => c.uid);
  return (
    <div className="card" style={{ padding: 8 }} data-testid="fix-clubs-card">
      <div className="ttl" style={{ padding: 10 }}>Unlicensed clubs<span className="st a mono">{d.clubs.filter((c) => c.unlicensed).length}</span><span style={{ marginLeft: "auto" }} />
        <button className="btn btn-p" disabled={!target.length} onClick={() => act(() => api.post("/editor/licensing/apply", { clubs: target, comps: [] }), (r) => `${r.applied} real name(s) applied`, KEYS).then(() => setSel([]))} data-testid="fix-apply-clubs"><Check size={13} />Apply real names ({target.length})</button></div>
      <table className="tbl"><thead><tr><th /><th>Name in your save</th><th>Real name</th><th>Logo</th><th>Status</th></tr></thead>
        <tbody>{d.clubs.map((c) => (
          <tr key={c.uid} style={{ cursor: "default" }} data-testid={`fix-club-${c.uid}`}>
            <td>{c.unlicensed && !c.applied && !c.active_in_fm && <Checkbox checked={sel.includes(c.uid)} onCheckedChange={() => toggle(c.uid)} data-testid={`fix-club-check-${c.uid}`} />}</td>
            <td>{c.current || <span style={{ color: "var(--dim)" }}>Not in this save</span>}</td>
            <td><b style={{ color: "var(--text)" }}>{c.real_long}</b><small style={{ display: "block", color: "var(--dim)" }}>{c.real_short} · {c.source}</small></td>
            <td>{c.logo_pack ? <span className="st ok">{c.logo_pack}</span> : c.fmcc_logo ? <span className="st b">FMCC logo</span> : <span className="st a" data-testid={`fix-club-nologo-${c.uid}`}>No logo</span>}</td>
            <td>{c.applied ? <><span className="st ok">Applied</span> <button className="btn" title="Undo" onClick={() => act(() => api.delete(`/editor/licensing/name/${c.uid}`), "Fix removed", KEYS)} data-testid={`fix-club-undo-${c.uid}`}><Undo2 size={13} /></button></>
              : c.active_in_fm ? <span className="st ok">Active in FM</span> : c.unlicensed ? <span className="st a">Unlicensed</span> : <span className="st n">Already real</span>}</td>
          </tr>))}</tbody></table>
      {!d.clubs.length && <p className="note" style={{ padding: 10 }}>No clubs in your fix files.</p>}
    </div>
  );
};

const Comps = ({ d, act }) => (
  <div className="card" data-testid="fix-comps-card"><div className="ttl">Competitions and divisions</div>
    <p className="note" style={{ marginTop: 4 }}>FMCC can't see competition names in your save, so these are listed straight from the fix files.</p>
    {d.comps.map((c) => (
      <div className="row" key={c.uid} data-testid={`fix-comp-${c.uid}`}><div style={{ flex: 1 }}><b>{c.real_long}</b><small>{c.real_short} · ID {c.uid} · {c.source}</small></div>
        {c.applied ? <button className="btn" onClick={() => act(() => api.delete(`/editor/licensing/comp/${c.uid}`), "Fix removed", KEYS)} data-testid={`fix-comp-undo-${c.uid}`}><Undo2 size={13} />Undo</button>
          : c.active_in_fm ? <span className="st ok">Active in FM</span>
            : <button className="btn btn-p" onClick={() => act(() => api.post("/editor/licensing/apply", { clubs: [], comps: [c.uid] }), "Competition name applied", KEYS)} data-testid={`fix-comp-apply-${c.uid}`}>Apply</button>}</div>))}
    {!d.comps.length && <p className="note" style={{ marginTop: 6 }}>None in your fix files.</p>}
  </div>
);

const Manual = ({ act }) => {
  const { data: clubs = [] } = useGet("editor-clubs", "/editor/clubs", { q: "" });
  const [f, setF] = useState({ uid: "", long: "", short: "", founded: "", stadium_id: "", stadium_name: "" });
  const [k, setK] = useState({ uid: "", long: "", short: "" });
  const num = (v) => (v === "" ? null : Number(v));
  const save = () => act(() => api.post(`/editor/licensing/manual/club/${f.uid}`, { long: f.long, short: f.short, founded: num(f.founded), stadium_id: num(f.stadium_id), stadium_name: f.stadium_name || null }),
    (r) => `Fix saved${r.founded_queued ? "; year founded added to Game changes" : ""}`, KEYS).then((r) => r && setF({ uid: "", long: "", short: "", founded: "", stadium_id: "", stadium_name: "" }));
  const inp = (o, set, key, ph, extra = {}) => <input className="inp" placeholder={ph} value={o[key]} onChange={(e) => set({ ...o, [key]: e.target.value })} data-testid={`manual-${set === setK ? "comp-" : ""}${key}`} {...extra} />;
  return (
    <div className="card" data-testid="fix-manual-card"><div className="ttl"><PenLine size={15} />Fix one yourself</div>
      <p className="note" style={{ marginTop: 4 }}>For a club the fix files miss. Turn on "Show unique IDs" in FM's preferences to find stadium and competition IDs.</p>
      <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
        <select className="inp" value={f.uid} onChange={(e) => setF({ ...f, uid: e.target.value })} data-testid="manual-club">
          <option value="">Choose a club</option>{clubs.map((c) => <option key={c.uid} value={c.uid}>{c.rename?.long || c.name}</option>)}</select>
        <div className="sgrid">{inp(f, setF, "long", "Real name")}{inp(f, setF, "short", "Short name")}</div>
        <div className="sgrid">{inp(f, setF, "founded", "Year founded (optional)", { type: "number" })}{inp(f, setF, "stadium_id", "Stadium ID (optional)", { type: "number" })}</div>
        {inp(f, setF, "stadium_name", "Real stadium name (with its ID)")}
        <button className="btn btn-p" disabled={!f.uid || f.long.trim().length < 2 || f.short.trim().length < 2} onClick={save} data-testid="manual-save">Save fix</button>
      </div>
      <div className="eyebrow" style={{ marginTop: 16 }}>Competition or division</div>
      <div style={{ display: "grid", gap: 8, marginTop: 6 }}>
        {inp(k, setK, "uid", "Competition ID", { type: "number" })}
        <div className="sgrid">{inp(k, setK, "long", "Real name")}{inp(k, setK, "short", "Short name")}</div>
        <button className="btn" disabled={!k.uid || k.long.trim().length < 2 || k.short.trim().length < 2} onClick={() => act(() => api.post(`/editor/licensing/manual/comp/${k.uid}`, { long: k.long, short: k.short }), "Competition fix saved", KEYS).then((r) => r && setK({ uid: "", long: "", short: "" }))} data-testid="manual-comp-save">Save competition fix</button>
      </div>
      <p className="note" style={{ marginTop: 12 }}>Nicknames can't be changed yet: FM's name files have no nickname command and FMLibreEditor can't write them.</p>
    </div>
  );
};

export const LicensingTab = () => {
  const act = useAct();
  const { data: d } = useGet("licensing", "/editor/licensing/scan");
  if (!d) return <p className="note">Scanning your fix files and logo packs…</p>;
  return (
    <div className="homegrid" data-testid="licensing-tab">
      <div style={{ display: "grid", gap: 16, alignContent: "start" }}><Clubs d={d} act={act} /><Comps d={d} act={act} /></div>
      <div style={{ display: "grid", gap: 16, alignContent: "start" }}><Sources d={d} act={act} /><Manual act={act} /></div>
    </div>
  );
};
