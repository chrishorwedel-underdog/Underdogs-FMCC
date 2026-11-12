import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { api, errMsg } from "@/lib/api";
import { useGet, TabBar } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { openPlayer } from "@/components/player/PlayerPanel";
import { U, money } from "@/components/history/Cabinet";

const fmt = (r, v) => (v == null ? null : r.unit === " £" ? money(v) : `${v}${r.unit || ""}`);
const Holder = ({ h }) => <>{h.unique_id ? <button className="linkish" onClick={() => openPlayer(h.unique_id)}>{h.name}</button> : h.link ? <Link className="linkish" to={h.link}>{h.name || h.season}</Link> : h.name}</>;

const RecordRows = ({ id, rows }) => (
  <div className="card" style={{ padding: 8, overflowX: "auto" }} data-testid={`records-${id}`}>
    <table className="tbl"><thead><tr><th>Record</th><th>Holder</th><th>Value</th><th>Season / date</th><th>Previous holders</th></tr></thead>
      <tbody>{rows.map((r) => <tr key={r.key} data-testid={`record-${r.key}`}>
        <td><b>{r.label}</b>{r.save && <small style={{ display: "block", color: "var(--dim)" }}>Whole save: {r.save.name} ({r.save.value})</small>}</td>
        <td>{r.holder ? <Holder h={r.holder} /> : <U v={null} />}</td><td className="mono">{r.holder ? fmt(r, r.holder.value) : "—"}</td>
        <td>{r.holder ? (r.holder.link ? <Link className="linkish" to={r.holder.link}>{r.holder.date || r.holder.season}</Link> : r.holder.date || r.holder.season) : "—"}</td>
        <td><small>{r.previous.length ? r.previous.map((p) => `${p.name || p.season} ${fmt(r, p.value)}`).join(" · ") : "—"}</small></td></tr>)}</tbody></table></div>
);

export const Records = () => {
  const [scope, setScope] = useState("league");
  const [part, setPart] = useState("team");
  const { data } = useGet(["history-records", scope], "/history/records", { scope });
  return <div style={{ display: "grid", gap: 12 }}>
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      <TabBar id="records-scope" value={scope} onChange={setScope} tabs={[["league", "League"], ["all", "All competitions"]]} />
      <TabBar id="records-part" value={part} onChange={setPart} tabs={[["team", "Team"], ["players", "Players"], ["matches", "Matches"], ["transfers", "Transfers"]]} />
    </div>
    {!data ? <Loading id="records-loading" rows={6} label="Loading records" /> : <>
      <RecordRows id={part} rows={data[part]} />
      {part === "matches" && <div className="card" data-testid="records-h2h"><div className="ttl">Head-to-head (most-played opponents)</div>
        {data.h2h.length ? data.h2h.map((o) => <div key={o.opponent} className="row"><div style={{ flex: 1 }}><b>{o.opponent}</b></div><span className="mono">P{o.p} W{o.w} D{o.d} L{o.l}</span></div>) : <p className="note"><U v={null} />: needs match data from MatchLens.</p>}</div>}
      <small className="note">Rate stats and average ratings need at least {data.min_minutes} minutes. Breaking a record keeps the previous holders. Anything the save doesn't include shows as Unavailable.</small>
    </>}
  </div>;
};

const SeasonRows = ({ l }) => l.rows.map((r, i) => <div key={r.unique_id} className="row" style={{ cursor: "pointer" }} onClick={() => openPlayer(r.unique_id)} data-testid={`leader-${l.key}-row-${i}`}><span className="mono" style={{ width: 18 }}>{i + 1}</span><div style={{ flex: 1 }}><b>{r.name}</b><small>{r.minutes} minutes</small></div><b className="mono">{r.value}</b></div>);

const AllTimeRows = ({ l }) => {
  const max = Math.max(...l.rows.map((r) => r.value), 0) || 1;
  return l.rows.map((r, i) => <button key={r.season} className={`at-row${r.current ? " now" : ""}`} onClick={() => openPlayer(r.unique_id)} title={r.current ? "Current season, still in progress" : `${r.season} season leader`} data-testid={`alltime-${l.key}-row-${i}`}>
    <span className="mono">{i + 1}</span><span className="at-who"><b>{r.name}</b><small>{r.season}{r.current ? " · this season" : ""}</small></span><b className="mono">{r.value}</b>
    <span className="at-bar" style={{ width: `${Math.max(4, (r.value / max) * 100)}%` }} /></button>);
};

const LeaderGroup = ({ title, list, mode }) => <><div className="over" style={{ marginTop: 6 }}>{title}</div>
  <div className="lead-grid">{list.map((l) => <div key={l.key} className="card" data-testid={`leader-${l.key}`}><div className="ttl">{l.label}</div>
    {!l.available ? <p className="note"><U v={null} />{mode === "alltime" ? " in any season yet." : " for this season."}</p> : mode === "alltime" ? <AllTimeRows l={l} /> : <SeasonRows l={l} />}</div>)}</div></>;

export const Leaders = () => {
  const [mode, setMode] = useState("season");
  const [season, setSeason] = useState(null);
  const { data } = useGet(["history-leaders", mode, season], "/history/leaders", { mode, ...(season ? { season } : {}) });
  return <div style={{ display: "grid", gap: 12 }}>
    <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
      <TabBar id="leaders-mode" value={mode} onChange={setMode} tabs={[["season", "Current season"], ["alltime", "All-Time"]]} />
      {data && mode === "season" && <><span className="note">Season</span>
        <select className="inp" style={{ width: "auto" }} value={data.season || ""} onChange={(e) => setSeason(e.target.value)} data-testid="leaders-season">{data.seasons.map((s) => <option key={s}>{s}</option>)}</select>
        {data.status === "In Progress" && <span className="st a">In Progress</span>}</>}
      {data && mode === "alltime" && <span className="note" data-testid="alltime-note">Each season's leader, ranked. {data.completed} completed season{data.completed === 1 ? "" : "s"} plus <span className="gold-t">this season in gold</span>.</span>}
    </div>
    {!data ? <Loading id="leaders-loading" rows={6} label="Loading leaders" /> : <>
      <LeaderGroup title="Regular stats" list={data.leaders.filter((l) => l.group === "regular")} mode={data.mode} />
      <LeaderGroup title="Analytical stats" list={data.leaders.filter((l) => l.group === "analytical")} mode={data.mode} />
      <small className="note">Season totals for players at your club. Average rating needs at least {data.min_minutes} minutes; clean sheets count goalkeepers only.{data.mode === "alltime" ? " The current season's line moves as the season goes on." : ""}</small>
    </>}
  </div>;
};

const CMP = [["division", "Division"], ["finish", "League finish"], ["ppg", "Points per game"], ["gd_pg", "Goal difference per game"], ["squad_age", "Squad age (by minutes)"], ["academy_minutes", "Academy minutes"], ["attendance", "Average attendance"], ["spend", "Transfer spend"]];

export const Compare = ({ seasons }) => {
  const [a, setA] = useState(seasons[1] || seasons[0]);
  const [b, setB] = useState(seasons[0]);
  const { data } = useGet(["history-compare", a, b], "/history/compare", { a, b }, { enabled: !!a && !!b });
  const pick = (v, set, id) => <select className="inp" style={{ width: "auto" }} value={v || ""} onChange={(e) => set(e.target.value)} data-testid={id}>{seasons.map((s) => <option key={s}>{s}</option>)}</select>;
  return <div className="card" style={{ display: "grid", gap: 10 }} data-testid="history-compare">
    <div style={{ display: "flex", gap: 10, alignItems: "center" }}>{pick(a, setA, "compare-a")}<span className="note">vs</span>{pick(b, setB, "compare-b")}</div>
    {seasons.length < 2 && <p className="note">You'll be able to compare once your history has two seasons.</p>}
    {data && <table className="tbl"><thead><tr><th></th><th>{data.a.season}</th><th>{data.b.season}</th></tr></thead>
      <tbody>{CMP.map(([k, l]) => <tr key={k}><td>{l}</td>{[data.a, data.b].map((s, i) => <td key={i} className="mono">{k === "spend" ? <U v={money(s[k])} /> : <U v={s[k]} />}</td>)}</tr>)}</tbody></table>}
  </div>;
};

export const HallOfFame = () => {
  const qc = useQueryClient();
  const { data } = useGet("history-hof", "/history/hall-of-fame");
  const { data: pl } = useGet("history-players", "/history/players");
  const [uid, setUid] = useState("");
  const go = async (fn, msg) => { try { await fn(); toast.success(msg); qc.invalidateQueries({ queryKey: ["history-hof"] }); } catch (e) { toast.error(errMsg(e)); } };
  if (!data) return <Loading id="hof-loading" rows={4} label="Loading Hall of Fame" />;
  return <div style={{ display: "grid", gap: 12 }}>
    <div className="card" style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }} data-testid="hof-induct">
      <b>Induct a club legend</b>
      <select className="inp" style={{ width: "auto" }} value={uid} onChange={(e) => setUid(e.target.value)} data-testid="hof-player"><option value="">Pick a player…</option>{(pl?.players || []).map((p) => <option key={p.unique_id} value={p.unique_id}>{p.name} ({p.apps} apps, {p.goals} goals)</option>)}</select>
      <button className="btn btn-p" disabled={!uid} onClick={() => go(() => api.post("/history/hall-of-fame", { unique_id: Number(uid) }), "Inducted into the Hall of Fame")} data-testid="hof-induct-button">Induct</button></div>
    {!data.members.length && <p className="note" data-testid="hof-empty">No legends yet.</p>}
    {data.members.map((m) => <div key={m.unique_id} className="card" data-testid={`hof-${m.unique_id}`}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}><button className="linkish" onClick={() => openPlayer(m.unique_id)}><b style={{ fontSize: 16 }}>{m.name}</b></button>
        <button className="btn" style={{ marginLeft: "auto", padding: "3px 8px", fontSize: 12 }} onClick={() => go(() => api.delete(`/history/hall-of-fame/${m.unique_id}`), "Removed from the Hall of Fame")} data-testid={`hof-remove-${m.unique_id}`}>Remove</button></div>
      <div className="facts" style={{ margin: "8px 0" }}>{[["Appearances", m.totals.appearances], ["Goals", m.totals.goals], ["Assists", m.totals.assists], ["Minutes", m.totals.minutes]].map(([l, v]) => <div key={l}><small>{l}</small><b className="mono">{v}</b></div>)}</div>
      <p className="note" style={{ margin: 0 }}>Honours: {m.honours.join(", ") || "None yet"} · Seasons: {m.seasons.map((s) => s.season).join(", ")}</p>
      <p className="note" style={{ margin: 0 }}>Defining matches: {m.defining_matches.length ? m.defining_matches.map((d) => <Link key={d.id} className="linkish" to={`/matches?match=${d.id}`} style={{ marginRight: 8 }}>vs {d.opponent} ({d.rating})</Link>) : <U v={null} />}</p>
    </div>)}
  </div>;
};
