import { Award, Trophy } from "lucide-react";
import { Loading } from "@/components/Loading";
import { useGet } from "@/lib/ui";
import { openPlayer } from "@/components/player/PlayerPanel";

const Row = ({ r, top }) => (
  <tr onClick={() => openPlayer(r.unique_id)} style={{ cursor: "pointer" }} data-testid={`breakout-row-${r.unique_id}`}>
    <td className="mono">{r.rank ?? "—"}</td>
    <td><b style={{ color: "var(--text)" }}>{r.name}</b>{top && <span className="tag st ok">Leading</span>}<small style={{ display: "block", color: "var(--dim)" }}>{r.position}</small></td>
    <td>{r.age}</td><td className="mono">{r.minutes}</td><td className="mono">{r.avg_rating ?? "—"}</td>
    <td className="mono" data-testid={`breakout-grade-${r.unique_id}`}>{r.grade ?? "—"}</td>
    <td className="mono">{r.teammate_pct != null ? `Better than ${r.teammate_pct}%` : <span style={{ color: "var(--dim)" }}>{r.reason}</span>}</td>
  </tr>
);

export const Breakout = () => {
  const { data } = useGet("breakout", "/breakout");
  if (!data) return <Loading id="breakout-loading" rows={5} label="Loading Breakout" />;
  const w = data.winner;
  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div className="card" data-testid="breakout-status">
        {w ? <div style={{ display: "flex", gap: 12, alignItems: "center" }}><Trophy size={22} color="#F5C542" />
          <div><div className="ttl" data-testid="breakout-winner">{w.name} is your Breakout Player of {data.season}</div><p className="note" style={{ margin: 0 }}>{w.note}. Picked and applied automatically.</p></div></div>
          : <div style={{ display: "flex", gap: 12, alignItems: "center" }}><Award size={22} color="var(--acc)" />
            <div><div className="ttl">Season {data.season}: {data.leader ? `${data.leader.name} is leading` : "no eligible player yet"}</div>
              <p className="note" style={{ margin: 0 }} data-testid="breakout-how">The winner is picked and applied automatically when FMCC reads your season-end save (May or June). Nothing to approve.</p></div></div>}
      </div>
      <p className="note" style={{ margin: 0 }} data-testid="breakout-rules-note">Fair for every position: each player's season grade is scored against players in his own position, then ranked against your teammates. First-team players only (22 and over, not U21 or U18), at least {data.min_minutes} minutes, and each player can only win once in his career.</p>
      <div className="card" style={{ padding: 8, overflowX: "auto" }}>
        <table className="tbl" data-testid="breakout-table">
          <thead><tr><th>#</th><th>Player</th><th>Age</th><th>Minutes</th><th>Avg rating</th><th>Season grade</th><th>Among teammates</th></tr></thead>
          <tbody>{data.standings.map((r, i) => <Row key={r.unique_id} r={r} top={i === 0 && !w} />)}
            {data.ineligible.map((r) => <Row key={r.unique_id} r={r} />)}</tbody>
        </table>
        {!data.standings.length && <p className="note" style={{ padding: 10 }} data-testid="breakout-empty">No first-team player is eligible yet. Players need {data.min_minutes} minutes this season.</p>}
      </div>
      {data.past.length > 0 && <div className="card" data-testid="breakout-past"><div className="ttl">Past winners (can't win again)</div>
        {data.past.map((p) => <div key={p.season} className="row" style={{ cursor: "pointer" }} onClick={() => openPlayer(p.unique_id)} data-testid={`breakout-past-${p.season}`}><div style={{ flex: 1 }}><b>{p.name}</b><small>{p.note}</small></div><span className="st n">{p.season}</span></div>)}</div>}
    </div>
  );
};
