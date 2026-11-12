import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Star, Scale, Download, Save, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, errMsg } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { useScout, usePost, fmtMoney, fmtWage, toGBP, ContractTag, Pct, num, pctColor } from "./ctx";
import { AdvFilter } from "./Lab";

const SHORT = { npxg: "npxG", xa: "xA", kp: "OP-KP", progp: "PrgP", drb: "Drb", tkw: "TklW", intc: "Int", passc: "Cmp%", ktk: "KeyTkl", gls: "Gls", npg: "npG", chc: "ChC", pcmp: "PasCmp", sha: "Sh%", aerw: "AerW", blk: "Blk", pwon: "PossW", plost: "PossL", fd: "FD", acr: "Crs", drr: "Drb%", saves: "Svs", mlg: "MLG", padint: "pAdjInt", xgp: "xGP", savep: "Sv%", aerr: "Aer%", tkr: "Tkl%", xakp: "xA/KP", pwl: "W/L", padbc: "pAdjB+C" };
const short = (k, label) => SHORT[k] || (label || k).replace(" / 90", "").slice(0, 12);
const KEY_STATS = ["npxg", "xa", "kp", "progp", "drb", "tkw", "intc", "passc"];
const BASE = { mode: "p90", gender: "M", source: "save", q: "", group: null, league: null, preset: null, max_value: null, max_wage: null, min_age: 15, max_age: 45, min_minutes: 0, sort: "grade", dir: "desc", adv: null };

const Filters = ({ f, setF, meta, prefs, more }) => {
  const set = (k, fn = (v) => v || null) => (e) => setF({ ...f, [k]: fn(e.target.value) });
  const cap = (k, mult) => (e) => setF({ ...f, [k]: e.target.value ? Math.round(toGBP(Number(e.target.value) * mult, prefs)) : null });
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
      <input className="inp" style={{ width: 200 }} placeholder="Name or club" value={f.q} onChange={set("q", (v) => v)} data-testid="sp-search" />
      <select className="inp" style={{ width: 150 }} value={f.group || ""} onChange={set("group")} data-testid="sp-group"><option value="">All positions</option>{Object.entries(meta?.groups || {}).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
      <select className="inp" style={{ width: 170 }} value={f.league || ""} onChange={set("league")} data-testid="sp-league"><option value="">All leagues</option>{meta?.leagues.map((l) => <option key={l}>{l}</option>)}</select>
      <select className="inp" style={{ width: 230 }} value={f.preset || ""} onChange={set("preset")} data-testid="sp-preset"><option value="">Ready-made searches</option>{Object.entries(meta?.presets || {}).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
      {more && <>
      <input className="inp" style={{ width: 130 }} type="number" placeholder="Max value (m)" onChange={cap("max_value", 1e6)} data-testid="sp-max-value" />
      <input className="inp" style={{ width: 130 }} type="number" placeholder="Max wage (k/wk)" onChange={cap("max_wage", 1e3)} data-testid="sp-max-wage" />
      <input className="inp" style={{ width: 80 }} type="number" defaultValue={f.max_age} title="Max age" onBlur={(e) => { const v = Math.min(50, Math.max(14, Number(e.target.value) || 45)); e.target.value = v; setF({ ...f, max_age: v }); }} data-testid="sp-max-age" />
      <input className="inp" style={{ width: 110 }} type="number" placeholder="Min minutes" onChange={set("min_minutes", (v) => Number(v) || 0)} data-testid="sp-min-minutes" />
      <div className="seg" data-testid="sp-gender">{[["M", "Men"], ["F", "Women"]].map(([k, l]) => <button key={k} className={f.gender === k ? "on" : ""} onClick={() => setF({ ...f, gender: k })} data-testid={`sp-gender-${k}`}>{l}</button>)}</div>
      {meta?.html_imports > 0 && <div className="seg">{[["save", "From the save"], ["html", "HTML imports"]].map(([k, l]) => <button key={k} className={f.source === k ? "on" : ""} onClick={() => setF({ ...f, source: k })} data-testid={`sp-source-${k}`}>{l}</button>)}</div>}
      </>}
    </div>
  );
};

const Searches = ({ f, setF }) => {
  const [name, setName] = useState("");
  const { data = [] } = useGet("saved-searches", "/scout/searches");
  const act = useAct();
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
      <select className="inp" style={{ width: 190 }} value="" onChange={(e) => { const s = data.find((x) => x.key === e.target.value); if (s) setF({ ...BASE, ...s.filters }); }} data-testid="sp-saved-select">
        <option value="">My saved searches ({data.length})</option>{data.map((s) => <option key={s.key} value={s.key}>{s.name}</option>)}</select>
      <input className="inp" style={{ width: 160 }} placeholder="Name this search" value={name} onChange={(e) => setName(e.target.value)} data-testid="sp-save-name" />
      <button className="btn" disabled={!name.trim()} onClick={() => act(() => api.post("/scout/searches", { name, filters: f }), "Search saved", ["saved-searches"]).then(() => setName(""))} data-testid="sp-save-search"><Save size={13} />Save</button>
      {data.map((s) => <button key={s.key} className="btn" title={`Delete ${s.name}`} onClick={() => act(() => api.delete(`/scout/searches/${s.key}`), "Saved search deleted", ["saved-searches"])} data-testid={`sp-delete-search-${s.key}`}><Trash2 size={12} />{s.name}</button>)}
    </div>
  );
};

const exportCsv = async (body) => {
  try {
    const r = await api.post("/scout/export", body, { responseType: "blob" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(r.data);
    a.download = "fmcc-scouting.csv";
    a.click();
  } catch (e) { toast.error(errMsg(e)); }
};

export const PlayersTab = () => {
  const { view, prefs, openPlayer, compare, toggleCompare } = useScout();
  const [params] = useSearchParams();
  const [f, setF] = useState({ ...BASE, group: params.get("group") });
  useEffect(() => { setF((x) => ({ ...x, group: params.get("group") })); }, [params]);
  const [cols, setCols] = useState("key");
  const [adv, setAdv] = useState(false);
  const [heat, setHeat] = useState(false);
  const [more, setMore] = useState(false);
  const { data: meta } = useGet("scout-meta", "/scout/meta");
  const body = { ...f, view, limit: 100 };
  const { data, isLoading } = usePost("scout-players", "/scout/players", body, { enabled: !!meta });
  const act = useAct();
  const statKeys = cols === "all" ? meta?.metrics.map((m) => m.key) || [] : cols === "key" ? KEY_STATS : [];
  const label = Object.fromEntries((meta?.metrics || []).map((m) => [m.key, m.label]));
  const isPct = Object.fromEntries((meta?.metrics || []).map((m) => [m.key, m.kind === "pct"]));
  const sortBy = (k) => setF({ ...f, sort: k, dir: f.sort === k && f.dir === "desc" ? "asc" : "desc" });
  const Th = ({ k, children, title }) => <th onClick={() => sortBy(k)} tabIndex={0} onKeyDown={(e) => e.key === "Enter" && sortBy(k)} aria-label={title || undefined} style={{ cursor: "pointer", whiteSpace: "nowrap", color: f.sort === k ? "var(--acc)" : undefined }} title={title}>{children}{f.sort === k ? (f.dir === "desc" ? " ↓" : " ↑") : ""}</th>;
  const star = (r) => act(() => api.post("/scouting/shortlist", { unique_id: r.unique_id, action: "add" }), `${r.name} added to the shortlist`, ["rankings"]);
  return (
    <div>
      <div className="sp-sticky" data-testid="sp-filters">
      <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}><Filters f={f} setF={setF} meta={meta} prefs={prefs} more={more} /></div>
        <button className={`btn${more ? " btn-p" : ""}`} onClick={() => setMore(!more)} aria-expanded={more} data-testid="sp-more-filters">{more ? "Fewer filters" : "More filters"}</button>
      </div>
      {more && <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginBottom: 12 }} data-testid="sp-more-panel">
        <div className="seg" data-testid="sp-mode">{[["total", "Season totals"], ["p90", "Per 90"], ["adjusted", "Possession + league adjusted"]].map(([k, l]) => <button key={k} className={f.mode === k ? "on" : ""} onClick={() => setF({ ...f, mode: k })} data-testid={`sp-mode-${k}`}>{l}</button>)}</div>
        <div className="seg" data-testid="sp-cols">{[["key", "Key stats"], ["all", `All stats (${meta?.metrics.length || 0})`], ["computed", "Computed"], ["formulas", `Formulas (${meta?.formulas.length || 0})`], ["actions", "Actions per 90"]].map(([k, l]) => <button key={k} className={cols === k ? "on" : ""} onClick={() => setCols(k)} data-testid={`sp-cols-${k}`}>{l}</button>)}</div>
        <button className={`btn${adv || f.adv ? " btn-p" : ""}`} onClick={() => setAdv(!adv)} data-testid="sp-adv-toggle">Advanced filter{f.adv ? " (on)" : ""}</button>
        <button className={`btn${heat ? " btn-p" : ""}`} onClick={() => setHeat(!heat)} data-testid="sp-heat-toggle">Heat colours</button>
        <span style={{ marginLeft: "auto" }} /><Searches f={f} setF={setF} />
        <button className="btn" onClick={() => exportCsv(body)} data-testid="sp-export-csv"><Download size={13} />Export CSV</button>
      </div>}
      </div>
      {more && adv && <AdvFilter value={f.adv} meta={meta} onChange={(v) => setF({ ...f, adv: v })} />}
      <div className="card" style={{ padding: 8, overflowX: "auto" }}>
        <table className="tbl pin2" data-testid="sp-table">
          <thead><tr><th></th><Th k="name">Player</Th><Th k="age">Age</Th><Th k="grade" title="Global grade: 20 + (local grade − 20) × league multiplier">Grade</Th>
            <Th k="value">Value</Th><Th k="fair_price">Fair price</Th><Th k="wage">Wage</Th><Th k="minutes">Mins</Th>
            {statKeys.map((k) => <Th key={k} k={k} title={label[k]}>{short(k, label[k])}</Th>)}
            {cols === "computed" && meta?.archetypes.map((a) => <Th key={a.key} k={`c:${a.key}`}>{a.name}</Th>)}
            {cols === "formulas" && meta?.formulas.map((x) => <Th key={x.key} k={`f:${x.key}`}>{x.name}</Th>)}
            {cols === "actions" && ["Defensive actions", "Progressive actions", "Box involvement"].map((a) => <th key={a}>{a}</th>)}<th></th></tr></thead>
          <tbody>{data?.rows.map((r) => {
            const marker = f.mode === "adjusted" && (r.poss_mult !== 1 || r.league_mult !== 1) ? `Possession ×${r.poss_mult} · league ×${r.league_mult}` : null;
            return (
              <tr key={r.unique_id} onClick={() => openPlayer(r.unique_id)} data-testid={`sp-row-${r.unique_id}`}>
                <td onClick={(e) => e.stopPropagation()}>{!r.own && r.source === "save" && <button className="ib" style={{ width: 26, height: 26 }} onClick={() => star(r)} title="Add to shortlist" data-testid={`sp-star-${r.unique_id}`}><Star size={13} /></button>}</td>
                <td><b style={{ color: "var(--text)" }}>{r.name}</b>{r.own && <span className="tag st g">Your club</span>}<ContractTag m={r.months_left} />{r.league_scored === false && <span className="tag st a" title={r.league_note} data-testid={`sp-noscore-${r.unique_id}`}>No strength score</span>}{r.source === "html" && !r.linked && <span className="tag st n">Not linked</span>}
                  <small style={{ display: "block", color: "var(--dim)" }}>{r.club} · {r.positions?.join(", ")}</small></td>
                <td>{r.age}</td>
                <td className="mono" style={{ color: "var(--acc)" }} title={r.minutes < 400 ? "Not enough minutes" : `Local ${r.grade_local} · league ×${r.league_mult}`}>{r.minutes < 400 ? "—" : r.grade_global ?? "—"}</td>
                <td className="mono">{r.value ? fmtMoney(r.value, prefs) : "—"}</td>
                <td className="mono" title={r.fair_price ? `Confidence: ${r.confidence}` : "Not enough minutes"}>{r.fair_price ? fmtMoney(r.fair_price, prefs) : "—"}</td>
                <td className="mono">{fmtWage(r.wage, prefs)}</td><td className="mono">{r.minutes}</td>
                {statKeys.map((k) => (heat && r.pct[k] != null ? <td key={k} className="mono" style={{ background: `color-mix(in srgb, ${pctColor(r.pct[k])} 22%, transparent)` }} title={`${r.pct[k]}th percentile`}>{num(r.stats[k])}</td>
                  : <Pct key={k} v={r.stats[k]} p={r.pct[k]} marker={isPct[k] ? null : marker} />))}
                {cols === "formulas" && meta?.formulas.map((x) => <td key={x.key} className="mono">{num(r.f?.[x.key])}</td>)}
                {cols === "computed" && meta?.archetypes.map((a) => <Pct key={a.key} v={r.computed?.[a.key]} p={r.computed?.[a.key]} />)}
                {cols === "actions" && ["Defensive actions", "Progressive actions", "Box involvement"].map((a) => <td key={a} className="mono">{num(r.actions?.[a])}</td>)}
                <td onClick={(e) => e.stopPropagation()}><button className={`btn${compare.includes(r.unique_id) ? " btn-p" : ""}`} onClick={() => toggleCompare(r.unique_id)} title="Compare" data-testid={`sp-compare-${r.unique_id}`}><Scale size={13} /></button></td>
              </tr>);
          })}</tbody>
        </table>
        {isLoading && <p className="note" style={{ padding: 10 }}>Loading players…</p>}
        {data && <p className="note" style={{ padding: 10 }} data-testid="sp-total">{data.total} players match. Showing {Math.min(100, data.total)}. Percentiles and grades need {meta?.min_minutes.percentiles} minutes; a fair price needs {meta?.min_minutes.fair_price}.{meta?.sample ? " Match stats are SAMPLE numbers in this preview." : ""}</p>}
      </div>
    </div>
  );
};
