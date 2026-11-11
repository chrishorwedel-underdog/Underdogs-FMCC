import { useEffect, useState } from "react";
import { Gavel, Download, Trash2, ListChecks, Search } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct, PageHead } from "@/lib/ui";
import { autoDownload } from "@/lib/autoDownload";

const KEYS = ["punishments", "changes"];

const ClubSearch = ({ club, setClub }) => {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState([]);
  useEffect(() => { const t = setTimeout(() => { api.get("/punish/clubs", { params: { q } }).then((r) => setRows(r.data)).catch(() => {}); }, 200); return () => clearTimeout(t); }, [q]);
  return (
    <div className="card" data-testid="punish-club-card">
      <div className="ttl"><Search size={14} />1 · Pick a club</div>
      <input className="inp" style={{ marginTop: 10 }} placeholder="Search any club in your database" value={q} onChange={(e) => setQ(e.target.value)} data-testid="punish-club-search" />
      <div style={{ maxHeight: 260, overflowY: "auto", marginTop: 8 }}>
        {rows.map((c) => <div key={c.uid} className={`pi${club?.uid === c.uid ? " sel" : ""}`} onClick={() => setClub(c)} data-testid={`punish-club-${c.uid}`}><span>{c.name}</span><small>{c.league}</small></div>)}
        {!rows.length && <p className="note">No clubs match.</p>}
      </div>
    </div>
  );
};

const PointsSeasons = ({ val, setVal }) => {
  const n = val.seasons || 1;
  const pts = (i) => (i === 1 ? val.points : val[`s${i}`] ?? val.points);
  const setPts = (i, v) => setVal({ ...val, [i === 1 ? "points" : `s${i}`]: v });
  const setN = (v) => {
    const k = Math.max(1, Math.min(10, v || 1));
    const next = { ...val, seasons: k };
    for (let i = 2; i <= 10; i += 1) { if (i > k) delete next[`s${i}`]; else if (next[`s${i}`] == null) next[`s${i}`] = val.points; }
    setVal(next);
  };
  const total = Array.from({ length: n }, (_, i) => Number(pts(i + 1)) || 0).reduce((a, b) => a + b, 0);
  return (
    <div style={{ width: "100%", marginTop: 8 }} data-testid="penalty-points-seasons">
      <label className="note" style={{ display: "flex", gap: 6, alignItems: "center", margin: 0 }}>Seasons
        <input className="inp" style={{ width: 70, height: 32 }} type="number" min={1} max={10} value={n} onChange={(e) => setN(Number(e.target.value))} data-testid="penalty-points-seasons-count" />
        <span style={{ marginLeft: "auto" }} data-testid="penalty-points-total">{n > 1 ? `${total} points in total` : ""}</span></label>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(130px,1fr))", gap: 6, marginTop: 8 }}>
        {Array.from({ length: n }, (_, i) => i + 1).map((i) => (
          <label key={i} className="note" style={{ display: "flex", gap: 6, alignItems: "center", margin: 0, whiteSpace: "nowrap" }}>{n > 1 ? `Season ${i}` : "Points"}
            <input className="inp" style={{ width: 64, height: 32 }} type="number" min={1} max={120} value={pts(i)} onChange={(e) => setPts(i, Number(e.target.value))} data-testid={`penalty-points-season-${i}`} /></label>))}
      </div>
    </div>
  );
};

const Penalty = ({ p, val, setVal }) => (
  <div className="chk" style={{ padding: "10px 12px", flexWrap: "wrap", borderColor: val ? "rgba(76,141,255,.45)" : undefined }} data-testid={`penalty-${p.key}`}>
    <input type="checkbox" checked={!!val} onChange={(e) => setVal(e.target.checked ? Object.fromEntries(p.params.map((x) => [x.key, x.default])) : null)} data-testid={`penalty-toggle-${p.key}`} />
    <div style={{ flex: 1 }}><b style={{ fontSize: 14 }}>{p.label}</b><small>{p.current_save ? "New career, or queue on your current FM27 save" : "New career only"}</small></div>
    {val && p.key === "points" && <PointsSeasons val={val} setVal={setVal} />}
    {val && p.key !== "points" && p.params.map((x) => <label key={x.key} className="note" style={{ display: "flex", gap: 6, alignItems: "center", margin: 0 }}>{x.unit}
      <input className="inp" style={{ width: 80, height: 32 }} type="number" min={x.min} max={x.max} value={val[x.key]} onChange={(e) => setVal({ ...val, [x.key]: Number(e.target.value) })} data-testid={`penalty-${p.key}-${x.key}`} /></label>)}
  </div>
);

const Saved = ({ act }) => {
  const { data = [] } = useGet("punishments", "/punish");
  return (
    <div className="card" data-testid="punish-saved">
      <div className="ttl">Saved punishments<span className="st n">{data.length}</span></div>
      {!data.length && <p className="note" style={{ marginTop: 6 }}>None yet. Each one you make is kept here and in your history.</p>}
      {data.map((d) => (
        <div key={d.pid} className="row" data-testid={`punishment-${d.pid}`}>
          <div style={{ flex: 1 }}><b>{d.name}</b><small>{d.summary}</small><small className="mono">{d.file_name}{d.queued ? " · queued on current save" : ""}</small></div>
          <a className="btn" href={`${process.env.REACT_APP_BACKEND_URL}/api/punish/${d.pid}/file`} data-testid={`punishment-download-${d.pid}`}><Download size={12} />File</a>
          <button className="btn" onClick={() => act(() => api.post(`/punish/${d.pid}/queue`), (r) => `${r.queued.length} change(s) queued in Game changes${r.new_career_only.length ? ` · new career only: ${r.new_career_only.join(", ")}` : ""}`, KEYS)} data-testid={`punishment-queue-${d.pid}`}><ListChecks size={12} />Queue on current save</button>
          <button className="btn btn-d" onClick={() => act(() => api.delete(`/punish/${d.pid}`), "Punishment removed and its file deleted", KEYS)} data-testid={`punishment-remove-${d.pid}`}><Trash2 size={12} /></button>
        </div>))}
    </div>
  );
};

export default function Punish() {
  const { data: meta } = useGet("punish-meta", "/punish/meta");
  const act = useAct();
  const [club, setClub] = useState(null);
  const [pens, setPens] = useState({});
  const [sum, setSum] = useState(null);
  const chosen = Object.fromEntries(Object.entries(pens).filter(([, v]) => v));
  const n = Object.keys(chosen).length;
  useEffect(() => {
    if (!club || !n) { setSum(null); return; }
    const t = setTimeout(() => { api.post("/punish/preview", { club_uid: club.uid, penalties: chosen }).then((r) => setSum(r.data)).catch((e) => setSum({ error: e.response?.data?.detail })); }, 250);
    return () => clearTimeout(t);
  }, [club, JSON.stringify(chosen)]); // eslint-disable-line react-hooks/exhaustive-deps
  const make = () => act(() => api.post("/punish", { club_uid: club.uid, penalties: chosen }), (r) => r.placed ? `Saved ${r.file_name} in your FM editor data folder. The file is downloading` : `Made ${r.file_name}. The file is downloading`, KEYS)
    .then((r) => {
      if (!r) return;
      setPens({});
      autoDownload(`/punish/${r.pid}/file`, r.file_name);
      if (meta?.edition === "FM27" && r.rows.some((x) => x.current_save)) {
        act(() => api.post(`/punish/${r.pid}/queue`), (q) => `${q.queued.length} change(s) for your current save queued in Game changes`, KEYS);
      }
    });
  const groups = [...new Set((meta?.penalties || []).map((p) => p.group))];
  return (
    <div data-testid="punish-page">
      <PageHead eyebrow="Inspired by sortitoutsi's Punish Manchester City, for any club" title="Punish a Club" />
      <div className="sq" style={{ gridTemplateColumns: "360px minmax(0,1fr)" }}>
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}><ClubSearch club={club} setClub={setClub} /></div>
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
          <div className="card" data-testid="punish-penalties">
            <div className="ttl"><Gavel size={14} />2 · Choose penalties<span style={{ marginLeft: "auto" }} />
              {meta?.presets.map((p) => <button key={p.key} className="btn" onClick={() => setPens(p.penalties)} data-testid={`punish-preset-${p.key}`}>{p.name}</button>)}
              <button className="btn" onClick={() => setPens({})} data-testid="punish-clear">Clear</button></div>
            {groups.map((g) => <div key={g} style={{ marginTop: 14 }}><div className="eyebrow">{g}</div>
              <div style={{ display: "grid", gap: 8, marginTop: 6 }}>{meta.penalties.filter((p) => p.group === g).map((p) => <Penalty key={p.key} p={p} val={pens[p.key]} setVal={(v) => setPens({ ...pens, [p.key]: v })} />)}</div></div>)}
          </div>
          <div className="card" data-testid="punish-summary">
            <div className="ttl">3 · Check the summary</div>
            {!club && <p className="note" style={{ marginTop: 6 }}>Pick a club first.</p>}
            {club && !n && <p className="note" style={{ marginTop: 6 }}>Switch on at least one penalty, or pick a preset.</p>}
            {sum?.error && <p className="note" style={{ color: "var(--red)" }} data-testid="punish-summary-error">{sum.error}</p>}
            {sum?.summary && <><p className="sent" style={{ fontSize: 16, marginTop: 8 }} data-testid="punish-summary-text">{sum.summary}</p>
              {sum.rows.filter((r) => !r.current_save).length > 0 && <small className="note" data-testid="punish-new-career-only">New career only: {sum.rows.filter((r) => !r.current_save).map((r) => `${r.label} (${r.why_not})`).join("; ")}</small>}
              <p className="note" style={{ marginTop: 8 }}>{meta?.desktop ? "Make the file, then start a new career in FM and pick it from the database list at the top right." : "Browser preview: the file is made for you to download, not placed in an FM folder."} Whether FM accepts it is on your Test checklist.</p>
              <button className="btn btn-g btn-l" style={{ marginTop: 10 }} onClick={make} data-testid="punish-make">Make the new-career file</button></>}
          </div>
          <Saved act={act} />
        </div>
      </div>
    </div>
  );
}
