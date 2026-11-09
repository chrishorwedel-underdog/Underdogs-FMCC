import { useState } from "react";
import { toast } from "sonner";
import { UserPlus, Download, Trash2, Eye, Plus, X } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { MyPresets, NameUpdates } from "./CreatorExtras";

const KEYS = ["creator-batches", "editor-state"];
const DEFAULT = { name: "", count: 20, nations: [{ nation: "England", weight: 1 }], ethnicities: [], skin_lo: 1, skin_hi: 20, age_lo: 16, age_hi: 21,
  positions: ["GK", "DC", "DL", "DR", "DM", "MC", "AML", "AMR", "AMC", "ST"], ca_lo: 30, ca_hi: 60, pa_lo: 60, pa_hi: 100, foot: "any", height_lo: 170, height_hi: 192, faces: true, seed: 1 };

const Range = ({ f, set, lo, hi, label, min, max }) => (
  <label className="note" style={{ display: "grid", gap: 4 }}>{label}
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <input className="inp mono" style={{ width: 76, height: 32 }} type="number" min={min} max={max} value={f[lo]} onChange={(e) => set({ [lo]: Number(e.target.value) })} data-testid={`pc-${lo}`} />–
      <input className="inp mono" style={{ width: 76, height: 32 }} type="number" min={min} max={max} value={f[hi]} onChange={(e) => set({ [hi]: Number(e.target.value) })} data-testid={`pc-${hi}`} /></div></label>
);

const Chips = ({ all, sel, toggle, id }) => (
  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>{all.map((x) => <button key={x} className={`btn${sel.includes(x) ? " btn-p" : ""}`} style={{ height: 30 }} onClick={() => toggle(x)} data-testid={`pc-${id}-${x}`}>{x}</button>)}</div>
);

const Nations = ({ f, set, meta }) => {
  const [n, setN] = useState("");
  const upd = (i, p) => set({ nations: f.nations.map((x, j) => (j === i ? { ...x, ...p } : x)) });
  return (
    <div style={{ display: "grid", gap: 6 }} data-testid="pc-nations">
      {f.nations.map((x, i) => <div key={x.nation} style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <b style={{ minWidth: 120 }}>{x.nation}</b>{!meta.name_lists.includes(x.nation) ? <small className="st n" style={{ margin: 0 }}>names from {meta.closest[x.nation] || "England"}</small>
          : <small className="note" data-testid={`pc-count-${x.nation}`}>{meta.name_counts[x.nation].builtin} built-in{meta.name_counts[x.nation].update ? ` + ${meta.name_counts[x.nation].update} from update` : ""}</small>}
        <label className="note">share<input type="range" min={1} max={10} value={x.weight} onChange={(e) => upd(i, { weight: Number(e.target.value) })} data-testid={`pc-weight-${x.nation}`} /></label>
        <button className="ib" disabled={f.nations.length === 1} onClick={() => set({ nations: f.nations.filter((_, j) => j !== i) })} data-testid={`pc-remove-${x.nation}`}><X size={13} /></button></div>)}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}><select className="inp" style={{ width: 220, maxWidth: "100%", height: 32 }} value={n} onChange={(e) => setN(e.target.value)} data-testid="pc-nation-select">
        <option value="">Add a nationality…</option>{meta.nations.filter((x) => !f.nations.some((y) => y.nation === x)).map((x) => <option key={x}>{x}</option>)}</select>
        <button className="btn" disabled={!n} onClick={() => { set({ nations: [...f.nations, { nation: n, weight: 1 }] }); setN(""); }} data-testid="pc-nation-add"><Plus size={13} />Add</button></div>
    </div>
  );
};

const Batches = ({ act }) => {
  const { data = [] } = useGet("creator-batches", "/creator/batches");
  return (
    <div className="card" data-testid="pc-batches"><div className="ttl">Saved batches<span className="st n">{data.length}</span></div>
      {!data.length && <p className="note" style={{ marginTop: 6 }}>None yet.</p>}
      {data.map((d) => <div key={d.bid} className="row" data-testid={`pc-batch-${d.bid}`}>
        <div style={{ flex: 1 }}><b>{d.name}</b><small>{d.count} free agents · {d.faces.given} with NG_Regens faces · {d.sample.map((p) => p.name).join(", ")}…</small><small className="mono">{d.file_name}</small></div>
        <a className="btn" href={`${process.env.REACT_APP_BACKEND_URL}/api/creator/batches/${d.bid}/file`} data-testid={`pc-batch-download-${d.bid}`}><Download size={12} />File</a>
        <button className="btn btn-d" onClick={() => act(() => api.delete(`/creator/batches/${d.bid}`), "Batch removed, its file deleted and its faces released", KEYS)} data-testid={`pc-batch-remove-${d.bid}`}><Trash2 size={12} /></button></div>)}
    </div>
  );
};

const NameSeed = ({ f, set }) => (
  <>
    <label className="note" style={{ display: "grid", gap: 4, marginTop: 14, maxWidth: 420 }}><b style={{ color: "var(--text)" }}>Batch name</b>
      <input className="inp" maxLength={60} placeholder="e.g. Academy wonderkids" value={f.name} onChange={(e) => set({ name: e.target.value })} data-testid="pc-name" />
      <small>What this batch is called in Saved batches and in the file's name. It isn't given to any player.</small></label>
    <section className="card" style={{ marginTop: 14, background: "var(--s2)", borderLeft: "3px solid var(--acc, #34D399)" }} data-testid="pc-name-seed">
      <div className="ttl" style={{ margin: 0 }} data-testid="pc-seed-title">Seed a Surname</div>
      <p className="note" style={{ marginTop: 6 }}>The seed is a number that decides which first names and surnames each created player gets, along with their face, age and other details. Use it to control the names in a batch:</p>
      <ul className="note" style={{ margin: "6px 0 0", paddingLeft: 18, display: "grid", gap: 2 }}>
        <li>Same seed and same settings: exactly the same names and players again.</li>
        <li>New seed: a fresh set of names. Use it if you don't like the surnames you got.</li>
        <li>Names come from each country's name list, so a Spanish player gets a Spanish surname.</li>
      </ul>
      <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 10, flexWrap: "wrap" }}>
        <b className="note" style={{ color: "var(--text)" }}>Seed</b>
        <input className="inp mono" style={{ width: 120 }} type="number" min={0} value={f.seed} onChange={(e) => set({ seed: Number(e.target.value) })} data-testid="pc-seed" />
        <button type="button" className="btn" onClick={() => set({ seed: Math.floor(Math.random() * 100000) })} data-testid="pc-seed-random">New seed</button>
        <small className="note">Preview to see the names this seed gives.</small>
      </div>
    </section>
  </>
);


export const CreatorTab = () => {
  const { data: meta } = useGet("creator-meta", "/creator/meta");
  const act = useAct();
  const [f, setF] = useState(DEFAULT);
  const [prev, setPrev] = useState(null);
  const [copy, setCopy] = useState("");
  const set = (p) => { setF((x) => ({ ...x, ...p })); setPrev(null); };
  const load = (s, name, note) => { set({ ...DEFAULT, nations: f.nations, ethnicities: f.ethnicities, ...s, name, seed: f.seed }); if (note) { toast.info(note); } };
  const toggle = (k) => (v) => set({ [k]: f[k].includes(v) ? f[k].filter((x) => x !== v) : [...f[k], v] });
  if (!meta) return null;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: 16 }} data-testid="creator-tab">
      <div className="card">
        <div className="ttl"><UserPlus size={14} />Player Creator<span className="st b">New careers only</span></div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }} data-testid="pc-presets">
          {meta.presets.map((p) => <button key={p.key} className="btn" title={p.about} onClick={() => { load(p.settings, p.name); setCopy(`${p.name} (copy)`); }} data-testid={`pc-preset-${p.key}`}>{p.name}</button>)}
          <MyPresets f={f} load={(s, n, note) => { load(s, n, note); setCopy(`${n} (copy)`); }} copyName={copy} />
          <button className="btn" onClick={() => { set(DEFAULT); setCopy(""); }} data-testid="pc-reset">Reset</button>
        </div>
        <p className="note" style={{ marginTop: 8 }}>Presets fill in the settings below; you can change anything before you preview. Built-in presets can't be changed, but saving one makes your own copy. Makes a batch of new free-agent players as an FMCC editor data file. Pick it from FM's database list when you start a new career. Players already in the game keep their clubs; in a running career you can only rename players.</p>
        <NameSeed f={f} set={set} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(300px, 100%), 1fr))", gap: 18, marginTop: 14 }}>
          <div style={{ display: "grid", gap: 14, alignContent: "start" }}>
            <label className="note" style={{ display: "grid", gap: 4 }}>How many players<input className="inp mono" style={{ width: 100 }} type="number" min={1} max={200} value={f.count} onChange={(e) => set({ count: Number(e.target.value) })} data-testid="pc-count" /></label>
            <div><div className="eyebrow">Nationalities</div><Nations f={f} set={set} meta={meta} /></div>
            <div><div className="eyebrow">Ethnicity mix (none picked = typical for each nationality)</div><Chips all={meta.ethnicities} sel={f.ethnicities} toggle={toggle("ethnicities")} id="eth" /></div>
            <Range f={f} set={set} lo="skin_lo" hi="skin_hi" label="Skin tone (FM's 1 light – 20 dark scale; leave at 1–20 for typical tones per ethnicity)" min={1} max={20} />
          </div>
          <div style={{ display: "grid", gap: 14, alignContent: "start" }}>
            <div><div className="eyebrow">Positions</div><Chips all={meta.positions} sel={f.positions} toggle={toggle("positions")} id="pos" /></div>
            <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
              <Range f={f} set={set} lo="age_lo" hi="age_hi" label="Age" min={15} max={40} />
              <Range f={f} set={set} lo="height_lo" hi="height_hi" label="Height (cm)" min={150} max={210} />
              <Range f={f} set={set} lo="ca_lo" hi="ca_hi" label="Current ability (1–200)" min={1} max={200} />
              <Range f={f} set={set} lo="pa_lo" hi="pa_hi" label="Potential ability (1–200)" min={1} max={200} />
            </div>
            <label className="note" style={{ display: "grid", gap: 4 }}>Preferred foot<select className="inp" style={{ width: 200 }} value={f.foot} onChange={(e) => set({ foot: e.target.value })} data-testid="pc-foot">
              <option value="any">Natural mix</option><option value="right">Right</option><option value="left">Left</option><option value="both">Either</option></select></label>
            <label className="note" style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" checked={f.faces} onChange={(e) => set({ faces: e.target.checked })} data-testid="pc-faces" />
              Match a face from NG_Regens {meta.ng_installed ? "(by nationality folder)" : "(not installed, so players will have no face)"}</label>
          </div>
        </div>
        <div className="acts" style={{ marginTop: 16 }}>
          <button className="btn btn-l" onClick={() => act(() => api.post("/creator/preview", f)).then((r) => r && setPrev(r))} data-testid="pc-preview"><Eye size={16} />Preview</button>
          <button className="btn btn-g btn-l" onClick={() => act(() => api.post("/creator/batches", f), (r) => `${r.players.length} players made${r.placed ? " and placed in your FM editor data folder" : ". Download the file from Saved batches"}`, KEYS).then((r) => r && setPrev(null))} data-testid="pc-create"><UserPlus size={16} />Make the players</button>
        </div>
      </div>
      {prev && <div className="card" data-testid="pc-preview-card">
        <div className="ttl">Preview: {prev.count} players<span className="st n">{Object.entries(prev.by_nation).map(([k, v]) => `${k} ${v}`).join(" · ")}</span></div>
        {!!prev.borrowed_names.length && <p className="note">FMCC has no name list for {prev.borrowed_names.join(", ")}, so their names come from the closest list.</p>}
        <div style={{ overflowX: "auto" }}><table className="tbl" style={{ marginTop: 8 }}><thead><tr><th>Name</th><th>Nation</th><th>Ethnicity · skin</th><th>Age</th><th>Pos</th><th>Foot</th><th>Height</th></tr></thead>
          <tbody>{prev.players.map((p) => <tr key={p.id} data-testid={`pc-row-${p.id}`}><td><b>{p.name}</b>{p.name_source === "update" && <small className="st g" style={{ marginLeft: 6 }} data-testid={`pc-row-update-${p.id}`}>update</small>}</td><td>{p.nationality}</td><td>{p.ethnicity} · {p.skin_tone}</td><td>{p.age}</td><td>{p.position}</td><td>{p.foot}</td><td>{p.height}</td></tr>)}</tbody></table></div>
        {prev.count > prev.players.length && <p className="note">Showing the first {prev.players.length}.</p>}
      </div>}
      <NameUpdates onChange={() => setPrev(null)} />
      <Batches act={act} />
    </div>
  );
};
