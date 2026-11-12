import { Trophy, Dumbbell } from "lucide-react";
import { useGet, PageHead } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { Empty } from "@/components/Empty";
import { openPlayer } from "@/components/player/PlayerPanel";

const Gone = ({ p }) => (p.still_here ? null : <span className="tag st n">Left the club</span>);

const BreakoutList = ({ rows }) => (
  <div className="card" data-testid="trophies-breakout">
    <div className="ttl" style={{ display: "flex", alignItems: "center", gap: 8 }}><Trophy size={16} color="#F5C542" />Breakout Players</div>
    {!rows.length && <p className="note" data-testid="trophies-breakout-empty">No Breakout Player yet. The first is picked automatically when FMCC reads your May or June save.</p>}
    {rows.map((r) => (
      <div key={r.season} className="row" style={{ cursor: "pointer" }} onClick={() => openPlayer(r.unique_id)} data-testid={`trophies-breakout-${r.season}`}>
        <span className="st n mono" style={{ minWidth: 70, textAlign: "center" }}>{r.season}</span>
        <div style={{ flex: 1 }}><b>{r.name}</b><Gone p={r} /><small>{[r.note, r.reward].filter(Boolean).join(" · ")}</small></div>
      </div>))}
  </div>
);

const EliteList = ({ sessions }) => (
  <div className="card" data-testid="trophies-elite">
    <div className="ttl" style={{ display: "flex", alignItems: "center", gap: 8 }}><Dumbbell size={16} color="var(--grn)" />Elite Training sessions</div>
    {!sessions.length && <p className="note" data-testid="trophies-elite-empty">No Elite Training session yet. Sessions run automatically in January and September for your nominees.</p>}
    {sessions.map((s) => (
      <div key={s.id} className="trophy-session" data-testid={`trophies-elite-${s.id}`}>
        <div className="eyebrow">{s.label} · {s.players.length} player{s.players.length !== 1 ? "s" : ""} improved</div>
        {s.players.map((p) => (
          <button key={p.unique_id} className="wc-row green" style={{ background: "none", border: 0, width: "100%", textAlign: "left", cursor: "pointer" }} onClick={() => openPlayer(p.unique_id)} data-testid={`trophies-elite-${s.id}-${p.unique_id}`}>
            <i /><b>{p.name}</b><Gone p={p} /><span>{p.benefit}{p.category ? ` · ${p.category}` : ""}</span></button>))}
      </div>))}
  </div>
);

export default function Trophies() {
  const { data } = useGet("trophies", "/trophies");
  return (
    <div data-testid="trophies-page">
      <PageHead eyebrow="Your whole career" title="Trophy Cabinet" purpose="Every Breakout Player and Elite Training session, from your first season to today." />
      {!data ? <Loading id="trophies-loading" rows={5} label="Loading your trophies" /> : <>
        <div className="cel-stats" style={{ gridTemplateColumns: "repeat(3,minmax(0,1fr))", marginBottom: 18 }} data-testid="trophies-totals">
          <div><b className="mono">{data.totals.breakout}</b><small>Breakout Players</small></div>
          <div><b className="mono">{data.totals.sessions}</b><small>Elite Training sessions</small></div>
          <div><b className="mono">{data.totals.boosts}</b><small>Training boosts earned</small></div>
        </div>
        {!data.totals.breakout && !data.totals.sessions ? <Empty id="trophies-empty" reason="empty" text="Your cabinet is empty for now. Awards appear here automatically as your career goes on." /> : null}
        <div className="sgrid"><BreakoutList rows={data.breakout} /><EliteList sessions={data.elite} /></div>
        <small className="note" style={{ display: "block", marginTop: 14 }}>Rewards are described in general terms only. True CA and PA are never shown.</small>
      </>}
    </div>
  );
}
