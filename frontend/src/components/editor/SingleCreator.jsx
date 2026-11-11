import { useEffect, useState } from "react";
import { UserPlus, Download, Trash2, Pencil, Wand2, X } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { autoDownload } from "@/lib/autoDownload";

const KEYS = ["creator-singles", "editor-state"];
const blank = (meta) => ({
  first_name: "", last_name: "", common_name: "", nationality: "England", second_nationality: "", dob: "2008-01-01", ethnicity: "Northern European", skin_tone: 3,
  height: 180, weight: 75, left_foot: 8, right_foot: 20, positions: { "M (C)": 20 }, ca: 100, pa: 150, club: "Free agent", faces: true,
  attributes: Object.fromEntries(Object.values(meta.groups).flat().map((a) => [a, 10])), personality: Object.fromEntries(meta.personality.map((p) => [p, 10])),
});
const nice = (k) => k.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());

const Num = ({ label, v, set, min, max, id, w = 76 }) => (
  <label className="note" style={{ display: "grid", gap: 4 }}>{label}
    <input className="inp mono" style={{ width: w, height: 32 }} type="number" min={min} max={max} value={v} onChange={(e) => set(Number(e.target.value))} data-testid={`pcs-${id}`} /></label>
);
const Txt = ({ label, v, set, id, ph, w = 200 }) => (
  <label className="note" style={{ display: "grid", gap: 4 }}>{label}
    <input className="inp" style={{ width: w, maxWidth: "100%", height: 32 }} value={v} placeholder={ph} onChange={(e) => set(e.target.value)} data-testid={`pcs-${id}`} /></label>
);
const Pick = ({ label, v, set, opts, id, w = 200, blankLabel }) => (
  <label className="note" style={{ display: "grid", gap: 4 }}>{label}
    <select className="inp" style={{ width: w, maxWidth: "100%", height: 32 }} value={v} onChange={(e) => set(e.target.value)} data-testid={`pcs-${id}`}>
      {blankLabel && <option value="">{blankLabel}</option>}{opts.map((o) => <option key={o}>{o}</option>)}</select></label>
);

const Identity = ({ f, up, meta }) => (
  <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
    <Txt label="First name" v={f.first_name} set={(v) => up({ first_name: v })} id="first" ph="e.g. Chris" />
    <Txt label="Surname" v={f.last_name} set={(v) => up({ last_name: v })} id="last" ph="e.g. Horwedel" />
    <Txt label="Known as (optional)" v={f.common_name} set={(v) => up({ common_name: v })} id="common" ph="e.g. Chrissy" />
    <Pick label="Nationality" v={f.nationality} set={(v) => up({ nationality: v })} opts={meta.nations} id="nation" />
    <Pick label="Second nationality" v={f.second_nationality} set={(v) => up({ second_nationality: v })} opts={meta.nations.filter((n) => n !== f.nationality)} id="nation2" blankLabel="None" />
    <label className="note" style={{ display: "grid", gap: 4 }}>Date of birth<input className="inp mono" type="date" style={{ height: 32 }} value={f.dob} onChange={(e) => up({ dob: e.target.value })} data-testid="pcs-dob" /></label>
    <Txt label="Club" v={f.club} set={(v) => up({ club: v })} id="club" w={180} />
  </div>
);

const Looks = ({ f, up, meta }) => (
  <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "end" }}>
    <Pick label="Ethnicity" v={f.ethnicity} set={(v) => up({ ethnicity: v })} opts={meta.ethnicities} id="eth" w={230} />
    <Num label="Skin tone (1 light – 20 dark)" v={f.skin_tone} set={(v) => up({ skin_tone: v })} min={1} max={20} id="skin" />
    <Num label="Height (cm)" v={f.height} set={(v) => up({ height: v })} min={150} max={210} id="height" />
    <Num label="Weight (kg)" v={f.weight} set={(v) => up({ weight: v })} min={50} max={110} id="weight" />
    <Num label="Left foot (1–20)" v={f.left_foot} set={(v) => up({ left_foot: v })} min={1} max={20} id="left" />
    <Num label="Right foot (1–20)" v={f.right_foot} set={(v) => up({ right_foot: v })} min={1} max={20} id="right" />
  </div>
);

const Positions = ({ f, up, meta }) => (
  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 8 }} data-testid="pcs-positions">
    {meta.positions.map((p) => <label key={p} className="note" style={{ display: "grid", gap: 3 }}><b style={{ color: "var(--text)" }}>{p}</b>
      <select className="inp" style={{ height: 30 }} value={f.positions[p] || ""} data-testid={`pcs-pos-${p}`}
        onChange={(e) => { const n = { ...f.positions }; if (e.target.value) { n[p] = Number(e.target.value); } else { delete n[p]; } up({ positions: n }); }}>
        <option value="">Can't play</option>{meta.levels.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}</select></label>)}
  </div>
);

const Grid = ({ title, keys, vals, set, id }) => (
  <div><div className="eyebrow">{title}</div>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: "6px 12px", marginTop: 6 }}>
      {keys.map((k) => <label key={k} className="note" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 6 }}>{nice(k)}
        <input className="inp mono" style={{ width: 58, height: 28 }} type="number" min={1} max={20} value={vals[k]} onChange={(e) => set({ ...vals, [k]: Number(e.target.value) })} data-testid={`pcs-${id}-${k}`} /></label>)}
    </div></div>
);

const Made = ({ act, edit }) => {
  const { data = [] } = useGet("creator-singles", "/creator/single");
  return (
    <div className="card" data-testid="pcs-list"><div className="ttl">Your created players<span className="st n">{data.length}</span></div>
      {!data.length && <p className="note" style={{ marginTop: 6 }}>None yet.</p>}
      {data.map((d) => <div key={d.id} className="row" data-testid={`pcs-made-${d.id}`}>
        <div style={{ flex: 1 }}><b>{d.player.name}</b><small>{d.player.nationality} · {Object.keys(d.player.positions).join(", ")} · {d.player.club}{d.player.face ? " · NG_Regens face" : ""}</small><small className="mono">{d.file_name}</small></div>
        <button className="btn" onClick={() => edit(d)} data-testid={`pcs-edit-${d.id}`}><Pencil size={12} />Edit</button>
        <a className="btn" href={`${process.env.REACT_APP_BACKEND_URL}/api/creator/single/${d.id}/file`} data-testid={`pcs-download-${d.id}`}><Download size={12} />File</a>
        <button className="btn btn-d" onClick={() => window.confirm(`Delete ${d.player.name}?`) && act(() => api.delete(`/creator/single/${d.id}`), "Player deleted and file removed", KEYS)} data-testid={`pcs-delete-${d.id}`}><Trash2 size={12} /></button></div>)}
    </div>
  );
};

export const SingleCreator = () => {
  const { data: meta } = useGet("creator-single-meta", "/creator/single/meta");
  const act = useAct();
  const [f, setF] = useState(null);
  const [editing, setEditing] = useState(null);
  const [vary, setVary] = useState(1);
  const up = (p) => setF((x) => ({ ...x, ...p }));
  const auto = (base, v = vary) => act(() => api.post("/creator/single/auto-attributes", { positions: base.positions, ca: base.ca, variation: v }), null, []).then((a) => a && setF({ ...base, attributes: a }));
  useEffect(() => { if (meta && !f) { auto(blank(meta)); } }, [meta]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!meta || !f) return null;
  const save = () => act(() => (editing ? api.put(`/creator/single/${editing}`, f) : api.post("/creator/single", f)),
    (r) => `${r.player.name} ${editing ? "updated" : "created"}${r.placed ? " and placed in your FM editor data folder" : ""}. The file is downloading`, KEYS)
    .then((r) => { if (r) { autoDownload(`/creator/single/${r.id}/file`, r.file_name); setEditing(null); auto(blank(meta)); } });
  const load = (d) => { const { id, name, face, ...rest } = d.player; setF(rest); setEditing(d.id); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const a = meta.groups;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: 16 }} data-testid="single-creator">
      <div className="card" style={{ display: "grid", gap: 18 }}>
        <div className="ttl" style={{ margin: 0 }}><UserPlus size={14} />{editing ? `Editing ${f.first_name} ${f.last_name}` : "Build a player"}<span className="st b">New careers</span>
          {editing && <button className="btn" style={{ marginLeft: "auto" }} onClick={() => { setEditing(null); auto(blank(meta)); }} data-testid="pcs-cancel-edit"><X size={12} />Stop editing</button>}</div>
        <p className="note" style={{ margin: 0 }}>Make one player exactly how you want them. They're saved as an FMCC editor data file; pick it from FM's database list when you start a new career.</p>
        <div><div className="eyebrow">Who they are</div><Identity f={f} up={up} meta={meta} /></div>
        <div><div className="eyebrow">Looks and build</div><Looks f={f} up={up} meta={meta} /></div>
        <div><div className="eyebrow">Positions</div><Positions f={f} up={up} meta={meta} /></div>
        <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "end" }}>
          <Num label="Current ability (1–200)" v={f.ca} set={(v) => up({ ca: v })} min={1} max={200} id="ca" w={90} />
          <Num label="Potential ability (1–200)" v={f.pa} set={(v) => up({ pa: v })} min={1} max={200} id="pa" w={90} />
          <button className="btn" onClick={() => { const v = vary + 1; setVary(v); auto(f, v); }} data-testid="pcs-auto"><Wand2 size={13} />Fill attributes from positions and ability</button>
        </div>
        <Grid title="Technical" keys={a.Technical} vals={f.attributes} set={(v) => up({ attributes: v })} id="attr" />
        <Grid title="Mental" keys={a.Mental} vals={f.attributes} set={(v) => up({ attributes: v })} id="attr" />
        <Grid title="Physical" keys={a.Physical} vals={f.attributes} set={(v) => up({ attributes: v })} id="attr" />
        <Grid title="Goalkeeping" keys={a.Goalkeeping} vals={f.attributes} set={(v) => up({ attributes: v })} id="attr" />
        <Grid title="Personality (hidden in FM)" keys={meta.personality} vals={f.personality} set={(v) => up({ personality: v })} id="pers" />
        <label className="note" style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" checked={f.faces} onChange={(e) => up({ faces: e.target.checked })} data-testid="pcs-faces" />Match a face from NG_Regens</label>
        <div className="acts"><button className="btn btn-g btn-l" disabled={!f.first_name || !f.last_name} onClick={save} data-testid="pcs-save"><UserPlus size={16} />{editing ? "Save changes" : "Create player"}</button></div>
      </div>
      <Made act={act} edit={load} />
    </div>
  );
};
