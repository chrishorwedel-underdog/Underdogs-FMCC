import { useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ReferenceLine, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, Legend } from "recharts";
import { Star, Scale, Download, Crosshair } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { useScout, fmtMoney, fmtWage, pctColor, num, useRaw } from "./ctx";

const PC = ["#4C8DFF", "#F2B54A", "#E879F9", "#34D399"];
const KIND = { own: ["#FACC15", "Your club"], target: ["#34D399", "Target zone"], shortlist: ["#E879F9", "Shortlist"], pool: ["#3B4252", "Rest of the pool"] };
const STAT_OPTS = ["npxg", "xa", "npg", "kp", "progp", "drb", "tkw", "intc", "pwon", "aerw", "passc", "sot", "chc", "prr"];
const Score = ({ v, label }) => <span className="mono" title={label} style={{ color: pctColor(v), fontWeight: 700 }}>{v ?? "–"}</span>;
const Gain = ({ g }) => g == null ? null : <span className="mono" style={{ color: g >= 0 ? "var(--grn)" : "var(--red)" }} title="Compared with your starter">{g >= 0 ? "▲" : "▼"} {Math.abs(g)}</span>;
const add = (act, uid) => act(() => api.post("/scouting/shortlist", { unique_id: uid, action: "add" }), "Added to your shortlist", ["recruit-board", "recruit-explore", "shortlist"]);

const Card = ({ p, open, act, onCompare }) => {
  const { prefs } = useScout();
  return (
    <div className="sugg-c" data-testid={`rcard-${p.unique_id}`}>
      <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}><b style={{ flex: 1, cursor: "pointer" }} onClick={() => open(p.unique_id)}>{p.name}</b><Score v={p.score} label="Role score" /><Gain g={p.gain} /></div>
      <small style={{ color: "var(--mut)" }}>{p.club} · age {p.age} · {fmtMoney(p.value, prefs)} · {fmtWage(p.wage, prefs)}{p.months_left != null ? ` · ${p.months_left} mo left` : ""}</small>
      {p.reason && <small>{p.reason}</small>}
      {!!p.tags?.length && <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>{p.tags.map((t) => <span key={t} className="st n" style={{ margin: 0 }}>{t}</span>)}</div>}
      {p.stage && <span className="st b" style={{ margin: 0, justifySelf: "start" }}>{p.stage} · philosophy {p.philosophy ?? "–"}</span>}
      {act && <div className="acts"><button className="btn" onClick={() => add(act, p.unique_id)} data-testid={`rcard-shortlist-${p.unique_id}`}><Star size={12} />Shortlist</button>
        {onCompare && <button className="btn" onClick={() => onCompare(p.unique_id)} data-testid={`rcard-compare-${p.unique_id}`}><Scale size={12} />Compare</button>}
        <button className="btn" onClick={() => open(p.unique_id)} data-testid={`rcard-open-${p.unique_id}`}>Open</button></div>}
    </div>
  );
};

export const ExploreTab = ({ open }) => {
  const [x, setX] = useState("npxg"), [y, setY] = useState("xa"), [role, setRole] = useState("af");
  const { data } = useGet("recruit-explore", "/recruit/explore", { x, y, role });
  const roleList = [["af", "Advanced Forward"], ["tf", "Target Forward"], ["w", "Winger"], ["if", "Inside Forward"], ["ap", "Advanced Playmaker"], ["bbm", "Box-to-Box"], ["dlp", "Deep-Lying Playmaker"], ["dm", "Defensive Midfielder"], ["wb", "Wing Back"], ["fb", "Full Back"], ["bpd", "Ball-Playing Defender"], ["cd", "Central Defender"], ["sk", "Sweeper Keeper"]];
  return (
    <div className="card" data-testid="explore-tab">
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <select className="inp" style={{ width: 200 }} value={x} onChange={(e) => setX(e.target.value)} data-testid="explore-x">{STAT_OPTS.map((k) => <option key={k} value={k}>{data?.labels?.[k] || k}</option>)}</select>
        <span className="note">against</span>
        <select className="inp" style={{ width: 200 }} value={y} onChange={(e) => setY(e.target.value)} data-testid="explore-y">{STAT_OPTS.map((k) => <option key={k} value={k}>{data?.labels?.[k] || k}</option>)}</select>
        <span className="note" style={{ marginLeft: "auto" }} data-testid="explore-count">{data ? `${data.count.toLocaleString()} players plotted, ${data.target} in the target zone` : "…"}</span>
      </div>
      <div style={{ height: 420, marginTop: 10 }}>
        <ResponsiveContainer><ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
          <XAxis type="number" dataKey="x" name={data?.labels?.[x]} stroke="#6B7280" fontSize={11} /><YAxis type="number" dataKey="y" name={data?.labels?.[y]} stroke="#6B7280" fontSize={11} /><ZAxis range={[40, 40]} />
          <Tooltip cursor={false} content={({ payload }) => payload?.[0] ? <div className="card" style={{ padding: 8 }}><b>{payload[0].payload.name}</b><small style={{ display: "block" }}>{payload[0].payload.club}</small></div> : null} />
          {data?.mx != null && <ReferenceLine x={data.mx} stroke="#6B7280" strokeDasharray="4 4" />}{data?.my != null && <ReferenceLine y={data.my} stroke="#6B7280" strokeDasharray="4 4" />}
          {Object.entries(KIND).reverse().map(([k, [c, l]]) => <Scatter key={k} name={l} data={(data?.points || []).filter((p) => p.kind === k)} fill={c} onClick={(p) => open(p.unique_id)} />)}
          <Legend />
        </ScatterChart></ResponsiveContainer>
      </div>
      <div className="ttl" style={{ marginTop: 10 }}>Ranked by role score
        <select className="inp" style={{ width: 220, marginLeft: 10 }} value={role} onChange={(e) => setRole(e.target.value)} data-testid="explore-role">{roleList.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></div>
      <div className="sugg">{data?.ranked.map((p) => <Card key={p.unique_id} p={p} open={open} />)}</div>
    </div>
  );
};

export const BoardTab = ({ open }) => {
  const { data } = useGet("recruit-board", "/recruit/board");
  const act = useAct();
  const [picks, setPicks] = useState(null);
  return (
    <div data-testid="board-tab">
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(240px,1fr))", gap: 12 }}>
        {data?.columns.map((col) => (
          <div key={col.slot} className="card" style={{ padding: 12 }} data-testid={`board-col-${col.slot}`}>
            <b>{col.label}</b><small style={{ display: "block", color: "var(--mut)" }}>{col.role_name}</small>
            <small style={{ display: "block", color: "#FACC15" }}>Starter: {col.starter ? `${col.starter.name} · ${col.starter.score ?? "–"}` : "nobody"}</small>
            <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
              {col.players.map((p) => <div key={p.unique_id}><Card p={p} open={open} />
                <select className="inp" style={{ height: 28, marginTop: 4 }} value={col.slot} onChange={(e) => act(() => api.put(`/recruit/board/${p.unique_id}`, { slot: e.target.value }), "Moved", ["recruit-board"])} data-testid={`board-move-${p.unique_id}`}>
                  {data.columns.map((c) => <option key={c.slot} value={c.slot}>Move to {c.label}</option>)}</select></div>)}
              {!col.players.length && <button className="btn" onClick={() => setPicks(col.role)} data-testid={`board-picks-${col.slot}`}><Crosshair size={12} />DOF picks</button>}
            </div>
          </div>))}
      </div>
      {picks && <div style={{ marginTop: 16 }}><PicksTab open={open} initialRole={picks} key={picks} /></div>}
    </div>
  );
};

const Strip = ({ row, n }) => (
  <div style={{ position: "relative", height: 16, background: "var(--s3)", borderRadius: 8, flex: 1 }}>
    <span style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 1, background: "#6B7280" }} title="Pool median" />
    {row.cells.slice(0, n).map((c, i) => c.pct != null && <span key={i} title={`${c.pct}th percentile`} style={{ position: "absolute", left: `calc(${c.pct}% - 6px)`, top: 2, width: 12, height: 12, borderRadius: 6, background: PC[i], border: "2px solid var(--bg)" }} />)}
  </div>
);

export const Compare4 = ({ ids, clear }) => {
  const [mode, setMode] = useState("profile");
  const raw = useRaw();
  const { data } = useGet("recruit-compare", "/recruit/compare", { ids: ids.join(",") });
  if (!data) return <div className="soon">Loading…</div>;
  const n = data.players.length;
  return (
    <div className="card" data-testid="compare4">
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        {data.players.map((p, i) => <span key={p.unique_id} className="st" style={{ margin: 0, background: PC[i], color: "#08090B" }}>{"ABCD"[i]} · {p.name}</span>)}
        <span style={{ marginLeft: "auto" }} />
        {[["profile", "Profile"], ["radar", "Overlay radar"], ["pizza", "Pizzas"]].map(([k, l]) => <button key={k} className={`btn${mode === k ? " btn-p" : ""}`} onClick={() => setMode(k)} data-testid={`compare-mode-${k}`}>{l}</button>)}
        <button className="btn" onClick={clear} data-testid="compare-clear">Clear</button>
      </div>
      {mode === "profile" && data.groups.map((g) => <div key={g.group} style={{ marginTop: 12 }}><div className="eyebrow">{g.group}</div>
        {g.rows.map((r) => <div key={r.key} style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 6 }} data-testid={`compare-row-${r.key}`}>
          <small style={{ width: 190 }}>{r.label}</small>{!raw && <Strip row={r} n={n} />}
          {r.cells.map((c, i) => <span key={i} className="mono" style={{ width: 58, textAlign: "right", color: PC[i], textDecoration: r.best === i ? "underline" : "none" }}>{c.raw == null ? "—" : num(c.raw)}</span>)}</div>)}</div>)}
      {mode === "radar" && <div style={{ height: 420 }}><ResponsiveContainer><RadarChart data={data.radar}><PolarGrid stroke="#2A2F37" /><PolarAngleAxis dataKey="axis" fontSize={11} stroke="#8B919B" />
        {data.players.map((p, i) => <Radar key={p.unique_id} dataKey={`p${i}`} name={p.name} stroke={PC[i]} fill={PC[i]} fillOpacity={0.12} />)}<Legend /></RadarChart></ResponsiveContainer></div>}
      {mode === "pizza" && <div style={{ display: "grid", gridTemplateColumns: `repeat(${n},1fr)`, gap: 10 }}>{data.players.map((p, i) => <div key={p.unique_id} style={{ height: 260 }}>
        <ResponsiveContainer><RadarChart data={data.radar}><PolarGrid stroke="#2A2F37" /><PolarAngleAxis dataKey="axis" fontSize={9} stroke="#8B919B" /><Radar dataKey={`p${i}`} stroke={PC[i]} fill={PC[i]} fillOpacity={0.5} /></RadarChart></ResponsiveContainer><p className="note" style={{ textAlign: "center" }}>{p.name}</p></div>)}</div>}
      <div className="ttl" style={{ marginTop: 16 }}>Role fit</div>
      <table className="tbl" data-testid="compare-roles"><tbody>{data.roles.map((r) => <tr key={r.role}><td>{r.name}</td>{r.scores.map((s, i) => <td key={i}><Score v={s} /></td>)}</tr>)}</tbody></table>
      <div className="ttl" style={{ marginTop: 16 }}>Where they sit: non-penalty xG against goals</div>
      <div style={{ height: 300 }} data-testid="compare-sit"><ResponsiveContainer><ScatterChart><XAxis type="number" dataKey="x" name="npxG/90" stroke="#6B7280" fontSize={11} /><YAxis type="number" dataKey="y" name="Goals/90" stroke="#6B7280" fontSize={11} /><ZAxis range={[36, 36]} />
        <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#6B7280" strokeDasharray="4 4" label={{ value: "goals = xG", fill: "#6B7280", fontSize: 10 }} /><Tooltip cursor={false} content={({ payload }) => payload?.[0] ? <div className="card" style={{ padding: 6 }}>{payload[0].payload.name}</div> : null} />
        <Scatter data={data.sit.filter((s) => !s.own && !s.sel)} fill="#3B4252" /><Scatter data={data.sit.filter((s) => s.own && !s.sel)} fill="#FACC15" /><Scatter data={data.sit.filter((s) => s.sel)} fill="#4C8DFF" /></ScatterChart></ResponsiveContainer></div>
    </div>
  );
};

export const PicksTab = ({ open, initialRole = "fb", onCompare }) => {
  const [f, setF] = useState({ role: initialRole, budget: 30000000, max_wage: 80000, skip_refuse: true, skip_against: true, include_not_for_sale: false });
  const [res, setRes] = useState(null);
  const act = useAct();
  const run = async () => setRes(await act(() => api.post("/recruit/picks", f)));
  const all = res ? Object.values(res.columns).flat() : [];
  return (
    <div className="card" data-testid="picks-tab">
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <select className="inp" style={{ width: 180 }} value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })} data-testid="picks-role">
          {["sk", "cd", "bpd", "fb", "wb", "dm", "dlp", "bbm", "ap", "w", "if", "af", "tf"].map((r) => <option key={r} value={r}>{r.toUpperCase()}</option>)}</select>
        <label className="note">Budget £<input className="inp" style={{ width: 130, display: "inline-block", marginLeft: 4 }} type="number" value={f.budget} onChange={(e) => setF({ ...f, budget: Number(e.target.value) })} data-testid="picks-budget" /></label>
        <label className="note">Max wage £/wk<input className="inp" style={{ width: 110, display: "inline-block", marginLeft: 4 }} type="number" value={f.max_wage} onChange={(e) => setF({ ...f, max_wage: Number(e.target.value) })} data-testid="picks-wage" /></label>
        {[["skip_refuse", "Leave out likely refusals"], ["skip_against", "Leave out against my philosophy"], ["include_not_for_sale", "Include not for sale"]].map(([k, l]) =>
          <label key={k} className="note" style={{ display: "flex", gap: 4 }}><input type="checkbox" checked={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.checked })} data-testid={`picks-${k}`} />{l}</label>)}
        <button className="btn btn-g" onClick={run} data-testid="picks-run">Get ten picks</button>
      </div>
      {res && <>
        <p className="note" style={{ marginTop: 10 }} data-testid="picks-starter">Benchmark: {res.starter ? `${res.starter.name} (score ${res.starter.score})` : "no starter in this role"}</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 10, marginTop: 8 }}>
          {Object.entries(res.columns).map(([k, v]) => <div key={k} data-testid={`picks-col-${k}`}><div className="eyebrow">{k}</div><div style={{ display: "grid", gap: 8, marginTop: 6 }}>
            {v.map((p) => <Card key={p.unique_id} p={p} open={open} act={act} onCompare={onCompare} />)}{!v.length && <small className="note">Nobody fits this column.</small>}</div></div>)}
        </div>
        {!!res.left_out.length && <p className="note" style={{ marginTop: 10 }} data-testid="picks-left-out">Considered and left out: {res.left_out.map((l) => `${l.name} (${l.score}, ${l.why})`).join("; ")}</p>}
        <div className="acts" style={{ marginTop: 10 }}>
          <button className="btn" disabled={!all.length} onClick={() => Promise.all(all.map((p) => api.post("/scouting/shortlist", { unique_id: p.unique_id, action: "add" }))).then(() => act(async () => ({ data: {} }), `${all.length} added to the shortlists`, ["recruit-board", "shortlist"]))} data-testid="picks-add-all">Add all to the shortlists</button>
          {onCompare && <button className="btn" disabled={!all.length} onClick={() => onCompare(all.slice(0, 4).map((p) => p.unique_id), true)} data-testid="picks-compare-top">Compare top four</button>}
        </div></>}
    </div>
  );
};

const Bar = ({ v }) => <span style={{ display: "inline-block", width: 90, height: 6, borderRadius: 3, background: "var(--s3)", verticalAlign: "middle" }}><span style={{ display: "block", height: 6, borderRadius: 3, width: `${v || 0}%`, background: pctColor(v) }} /></span>;

export const ProfileLab = ({ uid, view, onCompare }) => {
  const [role, setRole] = useState(null);
  const [more, setMore] = useState(false);
  const [note, setNote] = useState("");
  const act = useAct();
  const raw = useRaw();
  const { data: d } = useGet("recruit-profile", `/recruit/player/${uid}`, { role, view });
  if (!d) return null;
  const P = d.player;
  return (
    <div style={{ display: "grid", gap: 12, marginTop: 12 }} data-testid="profile-lab">
      <div className="soon" style={{ display: "flex", gap: 14, flexWrap: "wrap" }} data-testid="profile-lab-header">
        <small>Age {P.age}{P.height ? ` · ${P.height} cm` : ""}{P.foot ? ` · ${P.foot} foot` : ""} · {P.nationality}</small>
        <small>{P.minutes} min{P.avg_rating ? ` · avg ${P.avg_rating}` : ""} · {P.best_role || "–"}</small>
        <small>League: {P.league_word} than yours</small><span className={`st ${P.confidence === "High" ? "ok" : P.confidence === "Medium" ? "a" : "r"}`} style={{ margin: 0 }}>{P.confidence} confidence</span>
        {onCompare && <button className="btn" onClick={() => onCompare(uid)} data-testid="profile-add-compare"><Scale size={12} />Add to compare</button>}
        <a className="btn" href={`/scouting?tab=scatter`} data-testid="profile-show-explore">Show in Explore</a>
        <button className="btn" onClick={() => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(d, null, 2)], { type: "application/json" })); a.download = `${P.name}.json`; a.click(); }} data-testid="profile-export"><Download size={12} />Export report</button>
      </div>
      <div className="card" style={{ padding: 12 }}>
        <div className="ttl">Assess as<select className="inp" style={{ width: 260, marginLeft: 10 }} value={d.role} onChange={(e) => setRole(e.target.value)} data-testid="assess-role">{d.role_options.map((r) => <option key={r} value={r}>{d.role_labels[r]}</option>)}</select></div>
        <div style={{ display: "flex", gap: 24, marginTop: 8 }} data-testid="assess-scores">
          <div><small className="note">Role score</small><div style={{ fontSize: 28 }}><Score v={d.role_score} /></div></div>
          <div><small className="note">Philosophy score</small><div style={{ fontSize: 28 }}><Score v={d.philosophy} /></div></div>
          <div><small className="note">Character test</small><div><span className={`st ${d.character.result === "pass" ? "ok" : d.character.result === "fail" ? "r" : "a"}`} style={{ margin: 0 }} data-testid="character-test">{d.character.text}</span></div></div>
        </div>
        <div className="eyebrow" style={{ marginTop: 10 }}>What the role needs</div>
        {d.needs.map((n) => <div key={n.key} style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 4 }} title={`League average ${d.benchmarks[n.key]?.league_avg ?? "–"}, top 10% ${d.benchmarks[n.key]?.top10 ?? "–"}`}>
          <small style={{ width: 200 }}>{n.label}</small>{!raw && <Bar v={n.pct} />}<span className="mono" style={{ width: 50 }}>{num(n.raw)}</span>
          <span style={{ color: "var(--acc)", letterSpacing: 1 }} title="Weight">{"●".repeat(Math.max(1, Math.round(n.weight * 5)))}</span>{!raw && <small className="mono">{n.pct ?? "–"}</small>}
          {d.trend[n.key] != null && <small style={{ color: d.trend[n.key] >= 0 ? "var(--grn)" : "var(--red)" }}>{d.trend[n.key] >= 0 ? "↑" : "↓"}</small>}</div>)}
      </div>
      <div className="card" style={{ padding: 12 }} data-testid="profile-summary"><div className="ttl">Summary</div>
        <p className="note">Strengths: {d.summary.strengths.join(", ") || "nothing stands out yet"}. Weak spots: {d.summary.weak.join(", ") || "none clear"}.</p></div>
      <div className="card" style={{ padding: 12 }}><div className="ttl">Role fit</div>
        {d.fit.map((r) => <div key={r.role} className="row" style={{ cursor: "pointer" }} onClick={() => setRole(r.role)} data-testid={`fit-role-${r.role}`}><span style={{ flex: 1 }}>{r.name}</span><Score v={r.score} label="Role score" /><small style={{ marginLeft: 10 }}>philosophy {r.philosophy ?? "–"}</small></div>)}</div>
      <button className="btn" onClick={() => setMore(!more)} data-testid="profile-show-more">{more ? "Show less" : "Show more: indices, philosophy, new stats, similar players"}</button>
      {more && <>
        <div className="card" style={{ padding: 12 }} data-testid="profile-indices"><div className="ttl">Indices</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginTop: 6 }}>{Object.entries(d.indices).map(([k, v]) => <div key={k} style={{ display: "flex", gap: 8, alignItems: "center" }} title="Average percentile of the stats behind it">
            <small style={{ width: 120 }}>{v.label}</small><Bar v={v.value} /><small className="mono">{v.value ?? "–"}</small>{v.luck && <span className="st a" style={{ margin: 0 }} title="Goals well ahead of xG">luck</span>}</div>)}</div></div>
        <Philosophy d={d} act={act} />
        <div className="card" style={{ padding: 12 }} data-testid="profile-extra"><div className="ttl">More stats</div>
          {Object.entries(d.extra).map(([k, v]) => <div key={k} className="row"><span style={{ flex: 1 }}>{k}</span><span className="mono">{v}</span></div>)}</div>
        <div className="card" style={{ padding: 12 }}><div className="ttl">Similar players</div>
          {d.similar.map((s) => <div key={s.unique_id} className="row"><span style={{ flex: 1 }}>{s.name}<small>{s.club}</small></span><small className="mono">{s.similarity}% similar</small></div>)}</div>
      </>}
      <div className="card" style={{ padding: 12 }} data-testid="profile-pipeline"><div className="ttl">Pipeline and notes<span className="st b">{d.pipeline[0]?.stage || "Not tracked"}</span></div>
        <div className="acts" style={{ marginTop: 6 }}>{["Watching", "Scouted", "Bid", "Signed", "Rejected"].map((s) => <button key={s} className={`btn${d.pipeline[0]?.stage === s ? " btn-p" : ""}`} onClick={() => act(() => api.put(`/recruit/pipeline/${uid}`, { stage: s, note }), `Marked ${s}`, ["recruit-profile", "recruit-board"]).then(() => setNote(""))} data-testid={`pipeline-${s.toLowerCase()}`}>{s}</button>)}</div>
        <input className="inp" style={{ marginTop: 6 }} placeholder="Note (saved with the next step)" maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} data-testid="pipeline-note" />
        {d.pipeline.slice(0, 5).map((p) => <small key={p.id} style={{ display: "block", marginTop: 4 }}>{p.stage}{p.note ? ` · ${p.note}` : ""} · {p.at.slice(0, 10)}</small>)}</div>
    </div>
  );
};

const Philosophy = ({ d, act }) => {
  const [w, setW] = useState(d.weights);
  return (
    <div className="card" style={{ padding: 12 }} data-testid="profile-philosophy"><div className="ttl">Your philosophy</div>
      {Object.entries(d.trait_labels).map(([k, l]) => <div key={k} style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 4 }}><small style={{ width: 190 }}>{l}</small><Bar v={d.traits[k]} />
        <input type="range" min={0} max={5} value={w[k] ?? 1} onChange={(e) => setW({ ...w, [k]: Number(e.target.value) })} data-testid={`phil-${k}`} /><small className="mono">{w[k] ?? 1}</small></div>)}
      <button className="btn btn-p" style={{ marginTop: 8 }} onClick={() => act(() => api.put("/recruit/philosophy", { weights: w }), "Philosophy saved", ["recruit-profile", "recruit-board"])} data-testid="phil-save">Save weights</button>
    </div>
  );
};
