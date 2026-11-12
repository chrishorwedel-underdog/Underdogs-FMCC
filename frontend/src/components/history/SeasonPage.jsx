import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { useGet } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { openPlayer } from "@/components/player/PlayerPanel";
import { U, money, Status } from "@/components/history/Cabinet";

const Facts = ({ id, title, rows }) => (
  <div className="card" data-testid={`season-${id}`}><div className="ttl">{title}</div>
    <div className="facts">{rows.map(([l, v]) => <div key={l}><small>{l}</small><b className="mono">{v}</b></div>)}</div></div>
);

const List = ({ label, items }) => <p className="note" style={{ margin: "4px 0" }}><b style={{ color: "var(--text)" }}>{label}:</b> {items.length ? items.join(", ") : "None"}</p>;

export const SeasonPage = ({ season }) => {
  const [y1, y2] = season.split("/");
  const { data: s, isError } = useGet(["history-season", season], `/history/seasons/${y1}/${y2}`, undefined, { retry: false });
  if (isError) return <p className="note" data-testid="season-missing">That season isn't in your history. <Link className="linkish" to="/club-history?tab=seasons">Back to seasons</Link></p>;
  if (!s) return <Loading id="season-loading" rows={6} label="Loading season" />;
  const lg = s.league || {};
  const r = s.recruitment, a = s.academy, g = s.growth;
  return (
    <div style={{ display: "grid", gap: 16 }} data-testid="season-page">
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <Link to="/club-history?tab=seasons" className="btn" data-testid="season-back"><ArrowLeft size={13} />All seasons</Link>
        <h2 style={{ margin: 0, fontSize: 22 }}>{s.club} · {s.season}</h2><Status s={s.status} />
      </div>
      <div className="sgrid">
        <Facts id="league" title={<>League · <U v={lg.division} /></>} rows={[["Position", <U v={lg.pos} />], ["Played", <U v={lg.played} />], ["Won", <U v={lg.w} />], ["Drawn", <U v={lg.d} />], ["Lost", <U v={lg.l} />],
          ["Points", <U v={lg.pts} />], ["Goals for", <U v={lg.gf} />], ["Goals against", <U v={lg.ga} />], ["Goal difference", <U v={lg.gd} />]]} />
        <div className="card" data-testid="season-cups"><div className="ttl">Cups and continental</div>
          {s.cups.length ? s.cups.map((c, i) => <div key={i} className="row"><div style={{ flex: 1 }}><b>{c.competition}</b></div><span className="st n">{c.stage || "—"}</span></div>) : <p className="note"><U v={null} /> in this save.</p>}
          {s.honours.length > 0 && <><div className="eyebrow" style={{ marginTop: 8 }}>Honours</div>{s.honours.map((h, i) => <p key={i} className="note" style={{ margin: 0 }}>{h.competition} ({h.kind.replace("_", "-")})</p>)}</>}</div>
      </div>
      <div className="card" style={{ padding: 8, overflowX: "auto" }} data-testid="season-squad"><div className="ttl" style={{ padding: "4px 6px" }}>Season-end squad, as it was</div>
        <table className="tbl"><thead><tr><th>Player</th><th>Age</th><th>Apps</th><th>Starts</th><th>Minutes</th><th>Goals</th><th>Assists</th><th>Clean sheets</th><th>Avg rating</th><th>xG</th><th>xA</th><th>Awards</th></tr></thead>
          <tbody>{s.squad.map((p) => <tr key={p.unique_id} onClick={() => openPlayer(p.unique_id)} style={{ cursor: "pointer" }} data-testid={`season-squad-${p.unique_id}`}>
            <td><b>{p.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{(p.positions || []).join(", ")}{p.homegrown ? " · homegrown" : ""}</small></td>
            <td>{p.age}</td><td className="mono">{p.appearances}</td><td className="mono"><U v={p.starts} /></td><td className="mono">{p.minutes}</td><td className="mono">{p.goals}</td><td className="mono">{p.assists}</td>
            <td className="mono">{(p.positions || []).includes("GK") ? <U v={p.clean_sheets} /> : "—"}</td><td className="mono"><U v={p.avg_rating} /></td><td className="mono"><U v={p.npxg} /></td><td className="mono"><U v={p.xa} /></td>
            <td>{p.awards.join(", ") || "—"}</td></tr>)}</tbody></table></div>
      <div className="sgrid">
        <div className="card" data-testid="season-recruitment"><div className="ttl">Recruitment</div>
          <List label="Arrivals" items={r.arrivals} /><List label="Departures" items={r.departures} />
          <div className="facts" style={{ marginTop: 8 }}>{[["Spent", money(r.spent)], ["Received", money(r.received)], ["Net spend", money(r.net)]].map(([l, v]) => <div key={l}><small>{l}</small><b className="mono"><U v={v} /></b></div>)}</div>
          <small className="note">Open a player to revisit his scouting and Moneyball view.</small></div>
        <div className="card" data-testid="season-academy"><div className="ttl">Academy and development</div>
          <List label="First-team debuts (homegrown)" items={a.debuts} /><List label="Elite Training graduates" items={a.elite} />
          <p className="note" style={{ margin: "4px 0" }}>Homegrown senior minutes: <b className="mono">{a.homegrown_minutes}</b> · Confirmed Dynamic Potential changes: <b className="mono">{a.dp_changes}</b></p></div>
      </div>
      <Facts id="growth" title="Club growth" rows={[["Average attendance", <U v={g.attendance} />], ["Stadium capacity", <U v={g.capacity} />], ["Stadium", <U v={g.stadium} />], ["Wage bill", <U v={money(g.wage_bill)} />], ["Facilities", <U v={g.facilities} />], ["Academy", <U v={g.academy_level} />]]} />
      <small className="note" data-testid="season-sources">Saved as it happened from {s.sources.length} save read{s.sources.length !== 1 ? "s" : ""} ({s.sources.map((x) => `save ${x.save_no}, ${x.game_date}`).join("; ")}). Later reads only fill gaps.</small>
    </div>
  );
};
