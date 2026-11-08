import { useState } from "react";
import { Save, Pencil, Trash2, RefreshCw, Undo2, Download, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const PK = ["creator-presets"];
const NK = ["creator-names", "creator-meta", "creator-names-check"];

const MyPreset = ({ p, f, load, act }) => {
  const [edit, setEdit] = useState(false);
  const [name, setName] = useState(p.name);
  const rename = () => act(() => api.patch(`/creator/presets/${p.pid}`, { name }), "Preset renamed", PK).then((r) => r && setEdit(false));
  if (edit) {
    return (
      <span style={{ display: "inline-flex", gap: 4 }}>
        <input className="inp" style={{ width: 160, height: 32 }} maxLength={40} value={name} onChange={(e) => setName(e.target.value)} data-testid={`pc-my-rename-input-${p.pid}`} />
        <button className="btn" disabled={!name.trim()} onClick={rename} data-testid={`pc-my-rename-save-${p.pid}`}>Save</button>
        <button className="btn" onClick={() => setEdit(false)} data-testid={`pc-my-rename-cancel-${p.pid}`}>Cancel</button>
      </span>
    );
  }
  return (
    <span style={{ display: "inline-flex", gap: 2, alignItems: "center" }} data-testid={`pc-my-${p.pid}`}>
      <button className="btn" title={p.note || "Your saved preset"} onClick={() => load(p.settings, p.name, p.note)} data-testid={`pc-my-load-${p.pid}`}>{p.name}<small className="st g" style={{ margin: "0 0 0 6px" }}>Yours</small></button>
      <button className="ib" title="Rename" onClick={() => setEdit(true)} data-testid={`pc-my-rename-${p.pid}`}><Pencil size={12} /></button>
      <button className="ib" title="Overwrite with the current settings" onClick={() => window.confirm(`Overwrite "${p.name}" with the settings below?`) && act(() => api.patch(`/creator/presets/${p.pid}`, { settings: f }), "Preset overwritten with the current settings", PK)} data-testid={`pc-my-overwrite-${p.pid}`}><Save size={12} /></button>
      <button className="ib" title="Delete" onClick={() => window.confirm(`Delete the preset "${p.name}"?`) && act(() => api.delete(`/creator/presets/${p.pid}`), "Preset deleted", PK)} data-testid={`pc-my-delete-${p.pid}`}><Trash2 size={12} /></button>
    </span>
  );
};

export const MyPresets = ({ f, load, copyName }) => {
  const { data = [] } = useGet("creator-presets", "/creator/presets");
  const act = useAct();
  const [name, setName] = useState(null);
  const save = () => act(() => api.post("/creator/presets", { name, settings: f }), (r) => `Saved "${r.name}". It's available in every career`, PK).then((r) => r && setName(null));
  return (
    <>
      {data.map((p) => <MyPreset key={p.pid} p={p} f={f} load={load} act={act} />)}
      {name === null
        ? <button className="btn btn-p" onClick={() => setName(copyName || f.name || "")} data-testid="pc-save-preset"><Save size={13} />Save as preset</button>
        : <span style={{ display: "inline-flex", gap: 4 }}>
            <input className="inp" autoFocus style={{ width: 180, height: 32 }} maxLength={40} placeholder="Preset name" value={name} onChange={(e) => setName(e.target.value)} data-testid="pc-save-preset-name" />
            <button className="btn btn-g" disabled={!name.trim()} onClick={save} data-testid="pc-save-preset-confirm">Save</button>
            <button className="btn" onClick={() => setName(null)} data-testid="pc-save-preset-cancel">Cancel</button>
          </span>}
    </>
  );
};

const Check = ({ c, act, done }) => (
  <div className="card" style={{ marginTop: 10 }} data-testid="pc-names-check-result">
    {c.sample && <p className="note" data-testid="pc-names-sample"><span className="st b">Sample</span>This browser preview uses a sample update file, not a published FMCC list.</p>}
    {!c.available ? <p className="note" data-testid="pc-names-up-to-date">{c.message || `You're up to date${c.installed ? ` (${c.installed})` : ""}.`}</p> : <>
      <b data-testid="pc-names-new-version">{c.version}: {c.total_added} new names{c.countries_added.length ? `, ${c.countries_added.length} new countries` : ""}</b>
      {!!c.countries_added.length && <p className="note">New countries: {c.countries_added.join(", ")}</p>}
      <div style={{ display: "grid", gap: 2, marginTop: 6 }}>{Object.entries(c.names_added).map(([n, v]) => <small key={n} data-testid={`pc-names-add-${n}`}>{n}: +{v.first} first, +{v.last} last · e.g. {v.examples.join(", ")}</small>)}</div>
      <div className="acts" style={{ marginTop: 10 }}>
        <button className="btn btn-g" onClick={() => act(() => api.post("/creator/names/install", { version: c.version }), (r) => `Installed ${r.version}. New batches can use ${r.total_added} more names`, NK).then((r) => r && done())} data-testid="pc-names-install"><Download size={13} />Install these names</button>
        <button className="btn" onClick={done} data-testid="pc-names-skip">Skip</button>
      </div></>}
  </div>
);

export const NameUpdates = () => {
  const { data } = useGet("creator-names", "/creator/names");
  const act = useAct();
  const [c, setC] = useState(null);
  if (!data) return null;
  const inst = data.installed;
  return (
    <div className="card" data-testid="pc-names">
      <div className="ttl"><BookOpen size={14} />Name lists<span className="st n" data-testid="pc-names-total">{data.total.builtin} built-in + {data.total.update} from updates</span></div>
      <p className="note" style={{ marginTop: 6 }} data-testid="pc-names-installed">{inst ? `Update installed: ${inst.version}${inst.sample ? " (sample)" : ""}, added to the built-in names.` : "Only FMCC's built-in names are in use."} Updates only add names; players you've already made keep theirs.</p>
      <div className="acts" style={{ marginTop: 8 }}>
        <button className="btn" onClick={() => act(() => api.get("/creator/names/check")).then((r) => r && setC(r))} data-testid="pc-names-check"><RefreshCw size={13} />Check for name updates</button>
        {data.can_rollback && <button className="btn" onClick={() => window.confirm(`Roll back to ${data.rollback_to}? New batches will stop using the names from ${inst.version}.`) && act(() => api.post("/creator/names/rollback"), (r) => `Rolled back to ${r.now}`, NK).then(() => setC(null))} data-testid="pc-names-rollback"><Undo2 size={13} />Roll back to {data.rollback_to}</button>}
      </div>
      {c && <Check c={c} act={act} done={() => setC(null)} />}
      <details style={{ marginTop: 10 }} data-testid="pc-names-counts"><summary className="note">Names per country ({data.countries.length})</summary>
        <div style={{ columns: "220px", marginTop: 6 }}>{data.countries.map((r) => <small key={r.nation} style={{ display: "block" }} data-testid={`pc-names-count-${r.nation}`}>{r.nation}: {r.builtin} built-in{r.update ? ` + ${r.update} from update` : ""}</small>)}</div>
      </details>
      <p className="note" style={{ marginTop: 8 }}>Using the sortitoutsi Real Name Fix? It renames clubs, competitions, awards and stadiums, not players by nationality, so it can't add to these lists. FMCC never touches its files: the fix stays in FM's database folders, and FMCC's player files go into editor data under FMCC's own names.</p>
    </div>
  );
};
