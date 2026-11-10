import { useState } from "react";
import { Sprout, Plus, X, Wand2 } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { SeedResults, SeedHistory } from "./SeedResults";

const DEFAULT = { surname: "", mode: null, players: { GK: 1, DC: 2, MC: 2, ST: 1 }, staff: { Scout: 1, "First-Team Coach": 1, Physio: 1 }, nations: [{ nation: "England", count: 9 }],
  ethnicities: [], player_ages: { young: 1, prime: 1 }, staff_ages: { established: 1, senior: 1 }, skin_lo: 1, skin_hi: 20, height_lo: 170, height_hi: 192,
  ca_lo: 30, ca_hi: 60, pa_lo: 60, pa_hi: 100, include_own_club: false, faces: true, seed: 1 };
const sum = (o) => Object.values(o).reduce((a, b) => a + (Number(b) || 0), 0);

const N = ({ v, set, id, min = 0, max = 100, w = 58 }) => <input className="inp mono" style={{ width: w, height: 30 }} type="number" min={min} max={max} value={v} onChange={(e) => set(Math.max(min, Math.min(max, Number(e.target.value) || 0)))} data-testid={id} />;

const Range = ({ f, set, lo, hi, label, min, max }) => (
  <label className="note" style={{ display: "grid", gap: 4 }}>{label}
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}><N v={f[lo]} set={(v) => set({ [lo]: v })} min={min} max={max} id={`seed-${lo}`} w={70} />–<N v={f[hi]} set={(v) => set({ [hi]: v })} min={min} max={max} id={`seed-${hi}`} w={70} /></div></label>
);

const Counts = ({ title, keys, vals, set, id }) => (
  <div><div className="eyebrow">{title}<span style={{ marginLeft: 6, color: "var(--dim)" }}>{sum(vals)}</span></div>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: "6px 12px", marginTop: 6 }}>
      {keys.map((k) => <label key={k} className="note" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 6 }}>{k}
        <N v={vals[k] || 0} set={(v) => set({ ...vals, [k]: v })} id={`seed-${id}-${k}`} /></label>)}</div></div>
);

const Breakdown = ({ f, set, meta }) => (
  <div style={{ display: "grid", gap: 14 }} data-testid="seed-breakdown">
    <Counts title="Players by position" keys={meta.positions} vals={f.players} set={(v) => set({ players: v })} id="pl" />
    {Object.entries(meta.staff).map(([g, roles]) => <Counts key={g} title={g} keys={roles} vals={f.staff} set={(v) => set({ staff: v })} id="st" />)}
  </div>
);

const Nations = ({ f, set, meta, total }) => {
  const [n, setN] = useState("");
  const have = f.nations.reduce((a, x) => a + x.count, 0);
  const even = () => set({ nations: f.nations.map((x, i) => ({ ...x, count: Math.floor(total / f.nations.length) + (i < total % f.nations.length ? 1 : 0) })) });
  return (
    <div style={{ display: "grid", gap: 6 }} data-testid="seed-nations">
      <p className="note" style={{ margin: 0, color: have === total ? "var(--mut)" : "#F59E0B" }} data-testid="seed-nations-total">{have} of {total} people have a nationality{have !== total ? ` · ${have < total ? "add" : "remove"} ${Math.abs(total - have)}` : ""}</p>
      {f.nations.map((x, i) => <div key={x.nation} style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <b style={{ minWidth: 130 }}>{x.nation}</b><N v={x.count} max={300} set={(v) => set({ nations: f.nations.map((y, j) => (j === i ? { ...y, count: v } : y)) })} id={`seed-nat-count-${x.nation}`} />
        <button className="ib" disabled={f.nations.length === 1} onClick={() => set({ nations: f.nations.filter((_, j) => j !== i) })} data-testid={`seed-nat-remove-${x.nation}`}><X size={13} /></button></div>)}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        <select className="inp" style={{ width: 200, height: 32 }} value={n} onChange={(e) => setN(e.target.value)} data-testid="seed-nat-select">
          <option value="">Add a nationality…</option>{meta.nations.filter((x) => !f.nations.some((y) => y.nation === x)).map((x) => <option key={x}>{x}</option>)}</select>
        <button className="btn" disabled={!n} onClick={() => { set({ nations: [...f.nations, { nation: n, count: 0 }] }); setN(""); }} data-testid="seed-nat-add"><Plus size={13} />Add</button>
        <button className="btn" onClick={even} data-testid="seed-nat-even">Split evenly</button></div>
    </div>
  );
};

const Shares = ({ title, items, vals, set, id }) => (
  <div><div className="eyebrow">{title}</div>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))", gap: "6px 12px", marginTop: 6 }}>
      {items.map(([k, label]) => <label key={k} className="note" style={{ display: "grid", gap: 2 }}><span>{label} <b style={{ color: "var(--text)" }}>{vals[k] || 0}</b></span>
        <input type="range" min={0} max={10} value={vals[k] || 0} onChange={(e) => set({ ...vals, [k]: Number(e.target.value) })} data-testid={`seed-${id}-${k}`} /></label>)}</div></div>
);

const Mix = ({ f, set, meta }) => {
  const eth = Object.fromEntries(f.ethnicities.map((e) => [e.ethnicity, e.share]));
  return (
    <div style={{ display: "grid", gap: 14 }}>
      <Shares title="Ethnicity mix (all at 0 = typical for each nationality)" items={meta.ethnicities.map((e) => [e, e])} vals={eth}
        set={(v) => set({ ethnicities: Object.entries(v).filter(([, s]) => s > 0).map(([ethnicity, share]) => ({ ethnicity, share })) })} id="eth" />
      <Shares title="Player age mix" items={meta.player_ages.map((b) => [b.key, `${b.label} (${b.lo}–${b.hi})`])} vals={f.player_ages} set={(v) => set({ player_ages: v })} id="page" />
      <Shares title="Staff age mix" items={meta.staff_ages.map((b) => [b.key, `${b.label} (${b.lo}–${b.hi})`])} vals={f.staff_ages} set={(v) => set({ staff_ages: v })} id="sage" />
      <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
        <Range f={f} set={set} lo="skin_lo" hi="skin_hi" label="Skin tone (1 light – 20 dark; 1–20 = typical per ethnicity)" min={1} max={20} />
        <Range f={f} set={set} lo="height_lo" hi="height_hi" label="Player height (cm)" min={150} max={210} />
        <Range f={f} set={set} lo="ca_lo" hi="ca_hi" label={`Current ability (up to ${meta.caps.ca})`} min={1} max={meta.caps.ca} />
        <Range f={f} set={set} lo="pa_lo" hi="pa_hi" label={`Potential ability (up to ${meta.caps.pa})`} min={1} max={meta.caps.pa} />
      </div>
    </div>
  );
};

const Mode = ({ mode, set, meta }) => (
  <div style={{ display: "grid", gap: 6 }}>
    <div className="seg" style={{ justifySelf: "start" }} data-testid="seed-mode">
      <button className={mode === "new" ? "on" : ""} onClick={() => set({ mode: "new" })} data-testid="seed-mode-new">New save</button>
      <button className={mode === "current" ? "on" : ""} onClick={() => set({ mode: "current" })} data-testid="seed-mode-current">Current save</button></div>
    <small className="note" data-testid="seed-mode-note">{mode === "new" ? "Creates brand-new players and staff in an FMCC editor data file. Pick it from FM's database list when you start the new save."
      : `Renames existing low-profile players (free agents, youngsters and fringe players, not ${meta.club}'s) in your running save. Their club, age and ability stay the same. Staff can only be seeded into a new save.`}</small>
  </div>
);

export const SeedTab = () => {
  const { data: meta } = useGet("seed-meta", "/seed/meta");
  const { data: draft, refetch } = useGet("seed-draft", "/seed/draft");
  const act = useAct();
  const [f, setF] = useState(DEFAULT);
  const set = (p) => setF((x) => ({ ...x, ...p }));
  if (!meta) return null;
  const mode = f.mode || meta.suggested_mode;
  const body = { ...f, mode };
  const total = sum(f.players) + sum(f.staff);
  const create = () => act(() => api.post("/seed/create", { ...body, seed: Math.floor(Math.random() * 999999) }), (r) => `${r.people.length} ${r.mode === "new" ? "people created" : "players picked"}. Check them below`, ["seed-draft"]);
  const apply = () => window.confirm(mode === "new" ? `Seed ${draft.people.length} new people called ${draft.surname} into a new-save file?` : `Rename ${draft.people.length} players in your save to ${draft.surname}?`)
    && act(() => api.post("/seed/apply"), (r) => (r.mode === "new" ? `${draft.surname} seeded: ${r.people.length} people${r.placed ? " placed in your FM editor data folder" : ". Download the file from Seeded surnames"}` : `${draft.surname} seeded: ${r.people.length - r.failed} players renamed${r.sample ? " in the SAMPLE save" : ""}`), ["seed-draft", "seed-history", "editor-state"]);
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: 16 }} data-testid="seed-tab">
      <div className="card" style={{ display: "grid", gap: 18 }}>
        <div className="ttl" style={{ margin: 0 }}><Sprout size={14} />Seed a Surname</div>
        <p className="note" style={{ margin: 0 }}>Spread one surname through the football world: players, coaches, scouts, physios and front-office staff who all share it. Set it up, press Create to see and edit the people, then press Seed The Surname to put them in your game.</p>
        <label className="note" style={{ display: "grid", gap: 4, maxWidth: 360 }}><b style={{ color: "var(--text)" }}>Surname to seed</b>
          <input className="inp" maxLength={40} placeholder="e.g. Horwedel" value={f.surname} onChange={(e) => set({ surname: e.target.value })} data-testid="seed-surname" /></label>
        <Mode mode={mode} set={set} meta={meta} />
        <div><div className="eyebrow">How many, and who <span style={{ color: "var(--text)" }} data-testid="seed-total">{total} people</span></div><Breakdown f={f} set={set} meta={meta} /></div>
        <div><div className="eyebrow">Nationalities and how many of each</div><Nations f={f} set={set} meta={meta} total={total} /></div>
        <Mix f={f} set={set} meta={meta} />
        <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
          {mode === "new" && <label className="note" style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" checked={f.faces} onChange={(e) => set({ faces: e.target.checked })} data-testid="seed-faces" />Match NG_Regens faces for players</label>}
          {mode === "current" && <label className="note" style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" checked={f.include_own_club} onChange={(e) => set({ include_own_club: e.target.checked })} data-testid="seed-own-club" />Include {meta.club}'s low-profile players</label>}
        </div>
        <div className="acts">
          <button className="btn btn-l" disabled={f.surname.trim().length < 2 || !total} onClick={create} data-testid="seed-create"><Wand2 size={16} />Create</button>
          <button className="btn btn-g btn-l" disabled={!draft?.people?.length} onClick={apply} data-testid="seed-apply"><Sprout size={16} />Seed The Surname</button>
        </div>
      </div>
      {draft?.people?.length > 0 && <SeedResults d={draft} meta={meta} act={act} onChange={refetch} />}
      <SeedHistory act={act} />
    </div>
  );
};
