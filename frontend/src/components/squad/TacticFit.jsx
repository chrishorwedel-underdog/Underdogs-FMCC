import { useEffect, useState } from "react";
import { FileUp, Trash2, Hammer } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const SHOW = 5;
const tone = (r) => (r >= 70 ? "#34D399" : r >= 55 ? "var(--acc)" : r >= 40 ? "#FBBF24" : "#F87171");

const Ranked = ({ s }) => {
  const [all, setAll] = useState(false);
  const rows = all ? s.ranked : s.ranked.slice(0, SHOW);
  return (
    <div data-testid={`fit-ranked-${s.slot}`}>
      {rows.map((r, i) => (
        <div key={r.unique_id} style={{ display: "grid", gridTemplateColumns: "18px 1fr 34px", gap: 6, alignItems: "center", padding: "3px 0", opacity: r.natural ? 1 : 0.55 }}
          title={r.natural ? (r.positions || []).join(", ") : `Out of position (${(r.positions || []).join(", ")})`} data-testid={`fit-rank-${s.slot}-${r.unique_id}`}>
          <small className="mono" style={{ color: "var(--dim)" }}>{i + 1}</small>
          <div style={{ minWidth: 0 }}>
            <small style={{ display: "block", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{r.name}{!r.natural && " · out of position"}</small>
            <div style={{ height: 3, background: "var(--line)", borderRadius: 2 }}><div style={{ width: `${r.rating}%`, height: 3, background: tone(r.rating), borderRadius: 2 }} /></div>
          </div>
          <span className="mono" style={{ textAlign: "right", color: tone(r.rating) }}>{r.rating}</span>
        </div>))}
      {s.ranked.length > SHOW && <button className="btn" style={{ marginTop: 6, height: 26, fontSize: 12 }} onClick={() => setAll(!all)} data-testid={`fit-more-${s.slot}`}>{all ? "Show top 5" : `Show all ${s.ranked.length}`}</button>}
    </div>
  );
};

const Slot = ({ s, gap, onRole }) => (
  <div className="card" style={{ padding: 10, borderColor: gap ? "var(--amb)" : undefined }} data-testid={`fit-slot-${s.slot}`}>
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}><b>{s.label}</b><small className="mono" style={{ color: "var(--dim)" }}>{s.slot}</small>
      <span className="st n" style={{ marginLeft: "auto" }} title="Slot score: starter 60%, backup 30%, depth 10%">{s.score}</span></div>
    <select className="inp" style={{ height: 30, margin: "6px 0 8px", fontSize: 12 }} value={s.role} onChange={(e) => onRole(s.slot, e.target.value)} data-testid={`fit-role-${s.slot}`}>
      {s.role_options.map((o) => <option key={o.key} value={o.key}>{o.name}</option>)}</select>
    <Ranked s={s} />
  </div>
);

const TacticList = ({ tactics, current, pick, act, onDeleted }) => (
  <div className="card" data-testid="tactics-history"><div className="ttl">Your tactics</div>
    {tactics.map((t) => (
      <div key={t.id} className="row" style={{ cursor: "pointer", background: current === t.id ? "rgba(255,255,255,.04)" : undefined }} onClick={() => pick(t.id)} data-testid={`tactic-item-${t.id}`}>
        <div style={{ flex: 1 }}>{t.name}<small>{t.source}</small></div>
        {!t.from_save && <button className="ib" onClick={(e) => { e.stopPropagation(); act(() => api.delete(`/squad/tactics/${t.id}`), "Tactic removed", ["tactics", "tactic-fit"]).then((r) => r && onDeleted(t)); }} aria-label={`Remove ${t.name}`} data-testid={`tactic-delete-${t.id}`}><Trash2 size={12} /></button>}
      </div>))}
    {!tactics.length && <p className="note">Read a save, import an .fmf file or build a tactic to keep it here.</p>}
  </div>
);

export const TacticFit = () => {
  const [sel, setSel] = useState({ tactic: null, formation: null, picks: {} });
  const [name, setName] = useState("");
  const picks = Object.entries(sel.picks).map(([k, v]) => `${k}:${v}`).join(",");
  const { data } = useGet(["tactic-fit", sel.tactic, sel.formation, picks], "/squad/tactic-fit", { ...(sel.tactic ? { tactic: sel.tactic } : {}), ...(sel.formation ? { formation: sel.formation } : {}), ...(picks ? { picks } : {}) });
  const { data: tactics = [] } = useGet("tactics", "/squad/tactics");
  const { data: shapes = [] } = useGet("shapes", "/squad/shapes");
  const act = useAct();
  const nav = useNavigate();
  const pick = (id) => setSel({ tactic: id, formation: null, picks: {} });
  useEffect(() => { if (!sel.tactic && !sel.formation && data) { setSel((s) => ({ ...s, tactic: data.tactic?.id || null, formation: data.tactic ? null : data.formation_key })); } }, [data]); // eslint-disable-line react-hooks/exhaustive-deps
  const onDeleted = (t) => { if (t.id === sel.tactic) setSel({ tactic: null, formation: t.formation, picks: {} }); };
  const setRole = (slot, role) => setSel({ ...sel, picks: { ...Object.fromEntries((data?.slots || []).map((s) => [s.slot, s.role])), [slot]: role } });
  const upload = (f) => { const fd = new FormData(); fd.append("file", f); act(() => api.post("/squad/tactics/import", fd), (r) => `${r.name} imported (${(data?.formations || []).find(([k]) => k === r.formation)?.[1] || r.formation})`, ["tactics"]).then((r) => r && pick(r.id)); };
  const save = () => act(() => api.post("/squad/tactics", { formation: data.formation_key, name, roles: Object.fromEntries(data.slots.map((s) => [s.slot, s.role])) }), "Tactic saved", ["tactics"]).then((r) => { if (r) { setName(""); pick(r.id); } });
  const edited = !sel.tactic || picks;
  return (
    <div className="fit-grid" style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 300px", gap: 16 }} data-testid="tactic-fit">
      <div className="card">
        <div className="ttl" style={{ flexWrap: "wrap", gap: 8 }}>Tactic fit · <span data-testid="fit-title">{data?.tactic && !picks ? data.tactic.name : "Your build"} ({data?.formation})</span><span style={{ marginLeft: "auto" }} />
          <select className="inp" style={{ width: 200 }} value={sel.tactic || ""} onChange={(e) => (e.target.value ? pick(e.target.value) : setSel({ tactic: null, formation: data?.formation_key, picks: {} }))} data-testid="tactic-select">
            <option value="">Build your own…</option>{tactics.map((t) => <option key={t.id} value={t.id}>{t.name} · {t.source}</option>)}</select>
          <label className="btn" data-testid="tactic-import"><FileUp size={13} />Import .fmf<input type="file" accept=".fmf" hidden onChange={(e) => { if (e.target.files[0]) upload(e.target.files[0]); e.target.value = ""; }} data-testid="tactic-import-input" /></label>
        </div>
        {!sel.tactic && <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", margin: "8px 0" }} data-testid="tactic-builder">
          <Hammer size={14} style={{ color: "var(--acc)" }} /><small>Formation</small>
          <select className="inp" style={{ width: 190 }} value={data?.formation_key || ""} onChange={(e) => setSel({ tactic: null, formation: e.target.value, picks: {} })} data-testid="tactic-formation">
            {(data?.formations || []).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
          <small style={{ color: "var(--dim)" }}>then pick a role in each slot below</small></div>}
        {edited && data && <div style={{ display: "flex", gap: 8, margin: "8px 0" }}>
          <input className="inp" style={{ width: 220 }} placeholder={`Name (default ${data.formation})`} value={name} maxLength={60} onChange={(e) => setName(e.target.value)} data-testid="tactic-name" />
          <button className="btn btn-p" onClick={save} data-testid="tactic-save">Save as tactic</button></div>}
        <p className="note" style={{ marginTop: 4 }} data-testid="fit-note">{data?.note} Each slot ranks your whole squad from best to worst fit.</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(220px,1fr))", gap: 10, marginTop: 10 }}>
          {data?.slots.map((s) => <Slot key={s.slot} s={s} gap={data.gaps.some((g) => g.slot === s.slot)} onRole={setRole} />)}</div>
      </div>
      <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
        <TacticList tactics={tactics} current={sel.tactic} pick={pick} act={act} onDeleted={onDeleted} />
        <div className="card" data-testid="squad-gaps"><div className="ttl">Squad gaps</div>
          {data?.gaps.map((g) => <div key={g.slot} className="row" style={{ cursor: "pointer" }} onClick={() => nav(`/scouting?group=${g.group}`)} data-testid={`gap-${g.slot}`}><div style={{ flex: 1 }}>{g.label}<small>{g.role_name} · find players</small></div><span className="mono">{g.score}</span></div>)}</div>
        <div className="card" data-testid="shape-advisor"><div className="ttl">Shape advisor</div>
          {shapes.map((s) => <div key={s.key} className="row" style={{ cursor: "pointer" }} onClick={() => setSel({ tactic: null, formation: s.key, picks: {} })} data-testid={`shape-${s.key}`}><div style={{ flex: 1 }}>{s.name}<small>depth {s.depth}</small></div><span className="mono" style={{ color: "var(--acc)" }}>{s.strength}</span></div>)}</div>
      </div>
    </div>
  );
};
