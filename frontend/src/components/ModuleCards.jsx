import { useNavigate } from "react-router-dom";
import { Users, TrendingUp, Search, BarChart3, Zap, Trophy, ArrowRight } from "lucide-react";

const Card = ({ icon: Icon, title, tag, to, delay, children, id, open }) => {
  const nav = useNavigate();
  return (
    <div className={`card click rise ${delay}`} onClick={() => nav(to)} data-testid={`home-card-${id}`}>
      <div className="ch"><span className="tile"><Icon size={15} /></span>{title}{tag}</div>
      {children}
      <div className="open">{open}<ArrowRight size={14} /></div>
    </div>
  );
};

const Soon = ({ stage, text }) => <div className="soon">{text} <b style={{ color: "var(--text)" }}>Arrives in stage {stage}.</b></div>;

export const ModuleCards = ({ d }) => (
  <div className="bento">
    <Card id="squad" icon={Users} title="Squad" to="/squad" delay="d2" open="Open squad" tag={<span className="st g">{d.squad_size} players</span>}>
      <div className="num" data-testid="home-xi-average">{d.squad.xi_average}<small>Best XI average ability</small></div>
      <p className="sent">Weakest spot: <b data-testid="home-weak-spot">{d.squad.weak_spot || "—"}</b></p>
    </Card>
    <Card id="development" icon={TrendingUp} title="Development" to="/squad?filter=u21" delay="d3" open="See under-21s" tag={d.development.count ? <span className="st a">Act</span> : <span className="st ok">On track</span>}>
      <div className="num" data-testid="home-dev-count">{d.development.count}<small>under-21s need minutes</small></div>
      <div className="mbars">
        {d.development.players.map((p) => (
          <div className="mb" key={p.unique_id}><span>{p.name}</span><div className="track"><i style={{ width: `${Math.min(100, (p.minutes / d.development.target) * 100)}%`, background: "var(--amb)" }} /></div><span className="mono">{p.minutes}/{d.development.target}</span></div>
        ))}
      </div>
    </Card>
    <Card id="scouting" icon={Search} title="Scouting" to="/scouting" delay="d4" open="Preview" tag={<span className="st n">Stage 2</span>}>
      <Soon stage={2} text="Automatic rankings of every player in the save." />
    </Card>
    <Card id="report" icon={BarChart3} title="Since last save" to="/squad" delay="d5" open="See changes">
      {d.has_previous ? (
        <>
          <div className="num" data-testid="home-ca-change">{d.report.total_change > 0 ? "+" : ""}{d.report.total_change}<small>squad ability change</small></div>
          {d.report.riser && <p className="sent">Biggest riser: <b>{d.report.riser.name}</b> ({d.report.riser.change > 0 ? "+" : ""}{d.report.riser.change})</p>}
        </>
      ) : <div className="soon" data-testid="home-report-empty">Read one more save to compare players between saves.</div>}
    </Card>
    <Card id="elite" icon={Zap} title="Elite Training" to="/elite-training" delay="d6" open="Preview" tag={<span className="st n">Stage 2</span>}>
      <Soon stage={2} text="Nominations and training evidence from your save." />
    </Card>
    <Card id="awards" icon={Trophy} title="Awards" to="/awards" delay="d7" open="Preview">
      <div className="num" data-testid="home-weeks-left">{d.awards.weeks_left}<small>weeks to season end</small></div>
      <div className="ticks">{Array.from({ length: 40 }, (_, i) => <i key={i} className={i < 40 - Math.min(40, d.awards.weeks_left) ? "past" : ""} style={{ height: i % 7 === 0 ? "100%" : "55%" }} />)}</div>
      <p className="sent">Breakout reviews open at season end.</p>
    </Card>
  </div>
);
