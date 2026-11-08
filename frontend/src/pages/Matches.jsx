import { useEffect, useState } from "react";
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { PlayCircle, Plug } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { gameDate } from "@/lib/api";
import { useGet, TabBar, PageHead } from "@/lib/ui";
import { Chalkboard } from "@/components/matches/Chalkboard";

const TT = { background: "#121519", border: "1px solid rgba(255,255,255,.13)", borderRadius: 10, fontSize: 12 };

const XgTimeline = ({ m }) => {
  let u = 0, t = 0;
  const pts = [{ minute: 0, us: 0, them: 0 }, ...m.shots.map((s) => { if (s.team === "us") u += s.xg; else t += s.xg; return { minute: s.minute, us: +u.toFixed(2), them: +t.toFixed(2) }; }), { minute: 95, us: +u.toFixed(2), them: +t.toFixed(2) }];
  return (
    <div style={{ height: 170 }} data-testid="xg-timeline"><ResponsiveContainer><LineChart data={pts}>
      <XAxis dataKey="minute" type="number" domain={[0, 95]} stroke="#5C626C" fontSize={11} /><YAxis stroke="#5C626C" fontSize={11} width={28} /><Tooltip contentStyle={TT} />
      <Line type="stepAfter" dataKey="us" name={m.club_name} stroke="#4C8DFF" dot={false} strokeWidth={2} /><Line type="stepAfter" dataKey="them" name={m.opponent} stroke="#FF8A5B" dot={false} strokeWidth={2} />
    </LineChart></ResponsiveContainer></div>
  );
};

const Momentum = ({ m }) => (
  <div style={{ height: 90 }} data-testid="momentum"><ResponsiveContainer><AreaChart data={m.momentum}>
    <XAxis dataKey="minute" hide /><YAxis hide /><ReferenceLine y={0} stroke="rgba(255,255,255,.2)" /><Tooltip contentStyle={TT} />
    <Area dataKey="value" name="Momentum" stroke="#4C8DFF" fill="#4C8DFF" fillOpacity={0.25} />
  </AreaChart></ResponsiveContainer></div>
);

const PlayerCards = ({ m }) => {
  const ours = m.players.filter((p) => p.team === "us").sort((a, b) => b.rating - a.rating);
  return (
    <div className="card" data-testid="player-cards"><div className="ttl">Player match cards</div>
      {ours.map((p) => (
        <div className="row" key={p.unique_id} data-testid={`player-card-${p.unique_id}`}>
          <span className={`st ${p.rating >= 7.5 ? "ok" : p.rating < 6.3 ? "r" : "n"}`} style={{ margin: 0, minWidth: 38, textAlign: "center" }}>{p.rating}</span>
          <div style={{ flex: 1 }}><b>{p.name}</b> <span style={{ color: "var(--dim)", fontSize: 12 }}>{p.pos}</span>
            <small>{p.goals}G {p.assists}A · xG {p.xg} · xA {p.xa} · {p.key_passes} key passes · {p.prog_passes} progressive · {p.passes_completed}/{p.passes} passes · {p.duels_won} duels won · {p.pressures} pressures · {p.def_actions} def. actions</small></div>
        </div>))}
    </div>
  );
};

const MatchView = ({ id }) => {
  const { data: m } = useGet("match", `/matches/${id}`, { id });
  const [layer, setLayer] = useState("shots");
  const [f, setF] = useState({ team: "both", half: "all", player: "", kind: "all" });
  if (!m) return <p className="note">Loading match…</p>;
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div className="card" data-testid="match-summary">
        <div style={{ display: "flex", alignItems: "center", gap: 20, flexWrap: "wrap" }}>
          <div className="kick" style={{ textAlign: "left" }}><b data-testid="match-score">{m.club_name} {m.score.us} – {m.score.them} {m.opponent}</b><small>{gameDate(m.date, { day: "numeric", month: "short", year: "numeric" })} · {m.competition} · {m.home ? "Home" : "Away"} · xG {m.xg.us} – {m.xg.them}</small></div>
          <button className="btn" style={{ marginLeft: "auto" }} disabled title="Opens the FMMatchLens viewer inside the Windows program" data-testid="replay-button"><PlayCircle size={14} />Goal replays · Windows program</button>
        </div>
        <div className="sgrid" style={{ marginTop: 14 }}><div><div className="eyebrow">xG timeline</div><XgTimeline m={m} /></div><div><div className="eyebrow">Momentum</div><Momentum m={m} /></div></div>
      </div>
      <div className="card">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
          <TabBar id="layer" value={layer} onChange={setLayer} tabs={[["shots", "Shots"], ["passes", "Passes"], ["defensive", "Defensive"], ["heat", "Heat map"]]} />
          <select className="inp" style={{ width: 150 }} value={f.team} onChange={set("team")} data-testid="filter-team"><option value="both">Both teams</option><option value="us">{m.club_name}</option><option value="them">{m.opponent}</option></select>
          <select className="inp" style={{ width: 120 }} value={f.half} onChange={set("half")} data-testid="filter-half"><option value="all">Full match</option><option value="1">1st half</option><option value="2">2nd half</option></select>
          <select className="inp" style={{ width: 190 }} value={f.player} onChange={set("player")} data-testid="filter-player"><option value="">All players</option>{[["us", m.club_name], ["them", m.opponent]].map(([t, n]) => <optgroup key={t} label={n}>{m.players.filter((p) => p.team === t).map((p) => <option key={p.unique_id} value={p.unique_id}>{p.name}</option>)}</optgroup>)}</select>
          {layer === "passes" && <select className="inp" style={{ width: 150 }} value={f.kind} onChange={set("kind")} data-testid="filter-pass-kind"><option value="all">All passes</option><option value="progressive">Progressive</option><option value="key">Key passes</option></select>}
        </div>
        <Chalkboard m={m} layer={layer} f={f} />
      </div>
      <PlayerCards m={m} />
    </div>
  );
};

const Season = () => {
  const { data } = useGet("season90", "/matches/season");
  if (!data?.players?.length) return <div className="soon">No matches recorded yet this season.</div>;
  return (
    <div className="card" style={{ padding: 8, overflowX: "auto" }}>
      <table className="tbl" data-testid="season-table">
        <thead><tr><th>Player</th><th>Apps</th><th>Rating</th><th>Trend</th><th>xG/90</th><th>xA/90</th><th>Key passes/90</th><th>Progressive/90</th><th>Pressures/90</th><th>Def. actions/90</th><th>Pass %</th></tr></thead>
        <tbody>{data.players.map((p) => (
          <tr key={p.unique_id} style={{ cursor: "default" }}><td>{p.name}</td><td>{p.matches}</td><td className="mono">{p.avg_rating}</td>
            <td><svg width="70" height="20" viewBox="0 0 100 20" preserveAspectRatio="none"><polyline fill="none" stroke="var(--acc)" strokeWidth="2" vectorEffect="non-scaling-stroke" points={p.trend.map((r, i) => `${(i / Math.max(1, p.trend.length - 1)) * 100},${20 - ((r - 5) / 5) * 20}`).join(" ")} /></svg></td>
            {["xg", "xa", "key_passes", "prog_passes", "pressures", "def_actions"].map((k) => <td key={k} className="mono">{p.per90[k]}</td>)}<td className="mono">{p.pass_pct}</td></tr>))}</tbody>
      </table>
    </div>
  );
};

const Setup = ({ ml }) => {
  const nav = useNavigate();
  return (
    <div className="card" data-testid="matchlens-setup">
      <div className="ttl">Match add-on<span className={`st ${ml.installed ? "ok" : "a"}`} style={{ marginLeft: "auto" }} data-testid="matchlens-status">{ml.installed ? `Installed · FMMatchLens ${ml.fmmatchlens}` : "Not installed"}</span></div>
      <p className="note" style={{ marginTop: 6 }}>The FMMatchLens add-on is installed, checked and removed in Connections, and its own dashboard shows your live and saved matches. This page shows labelled sample matches: reading .fmlens files here waits until their format is known.</p>
      <div style={{ marginTop: 10 }}><button className="btn btn-p" onClick={() => nav("/connections")} data-testid="matchlens-open-connections"><Plug size={13} />Open Connections</button></div>
    </div>
  );
};

export default function Matches() {
  const { data } = useGet("matches", "/matches");
  const [tab, setTab] = useState("match");
  const [id, setId] = useState(null);
  const newest = data?.matches?.[0]?.id;
  useEffect(() => { if (newest) setId(newest); }, [newest]);
  if (!data) return <p className="note">Loading matches…</p>;
  return (
    <div data-testid="matches-page">
      <PageHead eyebrow="Sample matches · Sofascore/Opta-style view" title="Matches">
        <TabBar id="matches" value={tab} onChange={setTab} tabs={[["match", "Match"], ["season", "Season per 90"], ["setup", "Setup"]]} />
      </PageHead>
      {tab === "setup" && <Setup ml={data.matchlens} />}
      {tab === "season" && <Season />}
      {tab === "match" && (!data.matches.length ? <div style={{ display: "grid", gap: 16 }}><div className="soon" data-testid="matches-empty">No matches yet. Sample matches appear here after the match add-on is installed (in Connections) and a save is read.</div>{!data.matchlens.installed && <Setup ml={data.matchlens} />}</div> : (
        <div className="homegrid" style={{ gridTemplateColumns: "260px minmax(0,1fr)" }}>
          <div className="card" style={{ padding: 8, alignSelf: "start" }} data-testid="match-list">
            {data.matches.map((m) => <div key={m.id} className={`pi${m.id === id ? " sel" : ""}`} onClick={() => setId(m.id)} data-testid={`match-item-${m.id}`}>
              <span><b>{m.score.us}–{m.score.them}</b> {m.opponent}</span><small>{gameDate(m.date, { day: "numeric", month: "short" })}</small></div>)}
          </div>
          {id && <MatchView id={id} />}
        </div>))}
    </div>
  );
}
