import { useNavigate } from "react-router-dom";
import { useFeatures, isOff } from "@/lib/features";

const FEAT = { squad: "squad", development: "development", scouting: "scouting", report: "reports", breakout: "breakout" };
import { Users, TrendingUp, Search, BarChart3, Zap, Star, ArrowRight } from "lucide-react";

const Card = ({ icon: Icon, title, tag, to, delay, children, id, open }) => {
  const nav = useNavigate();
  const { data: feats } = useFeatures();
  if (isOff(feats, FEAT[id])) return null;
  return (
    <div className={`card click rise ${delay}`} onClick={() => nav(to)} data-testid={`home-card-${id}`}>
      <div className="ch"><span className="tile"><Icon size={15} /></span>{title}{tag}</div>
      {children}
      <div className="open">{open}<ArrowRight size={14} /></div>
    </div>
  );
};


export const ModuleCards = ({ d }) => (
  <div className="bento">
    <Card id="squad" icon={Users} title="Squad" to="/squad" delay="d2" open="Open squad" tag={<span className="st g">{d.squad_size} players</span>}>
      <div className="num" data-testid="home-xi-average">{d.squad.xi_average}<small>Best XI strength</small></div>
      <p className="sent">Weakest spot: <b data-testid="home-weak-spot">{d.squad.weak_spot || "—"}</b></p>
    </Card>
    <Card id="development" icon={TrendingUp} title="Development" to="/development" delay="d3" open="Open plans" tag={d.development.count ? <span className="st a">Act</span> : <span className="st ok">On track</span>}>
      <div className="num" data-testid="home-dev-count">{d.development.count}<small>under-21s need minutes</small></div>
      <div className="mbars">
        {d.development.players.map((p) => (
          <div className="mb" key={p.unique_id}><span>{p.name}</span><div className="track"><i style={{ width: `${Math.min(100, (p.minutes / d.development.target) * 100)}%`, background: "var(--amb)" }} /></div><span className="mono">{p.minutes}/{d.development.target}</span></div>
        ))}
      </div>
    </Card>
    <Card id="scouting" icon={Search} title="Scouting" to="/scouting" delay="d4" open="Open rankings">
      <p className="sent" style={{ marginTop: 18 }}>Every player in the save ranked by role fit, age, potential and value, with shortlists and Moneyball.</p>
    </Card>
    <Card id="report" icon={BarChart3} title="Since last save" to="/reports" delay="d5" open="Open reports">
      {d.has_previous ? (
        <>
          <div className="num" data-testid="home-ca-change">{d.report.total_change > 0 ? "+" : ""}{d.report.total_change}<small>squad ability change</small></div>
          {d.report.riser && <p className="sent">Biggest riser: <b>{d.report.riser.name}</b> ({d.report.riser.change > 0 ? "+" : ""}{d.report.riser.change})</p>}
        </>
      ) : <div className="soon" data-testid="home-report-empty">Read one more save to compare players between saves.</div>}
    </Card>
    <Card id="elite" icon={Zap} title="Game changes" to="/changes" delay="d6" open="Open game changes" tag={d.pending_changes ? <span className="st a">Waiting</span> : <span className="st ok">Clear</span>}>
      <div className="num" data-testid="home-pending-changes">{d.pending_changes}<small>changes waiting for you</small></div>
      <p className="sent">Elite Training, Breakout Player and Dynamic Potential changes.</p>
    </Card>
    <Card id="breakout" icon={Star} title="Breakout Player" to="/breakout" delay="d7" open="Open Breakout Player">
      <div className="num" data-testid="home-weeks-left">{d.awards.weeks_left}<small>weeks to season end</small></div>
      <div className="ticks">{Array.from({ length: 40 }, (_, i) => <i key={i} className={i < 40 - Math.min(40, d.awards.weeks_left) ? "past" : ""} style={{ height: i % 7 === 0 ? "100%" : "55%" }} />)}</div>
      <p className="sent">Breakout picks can be made official at season end.</p>
    </Card>
  </div>
);
