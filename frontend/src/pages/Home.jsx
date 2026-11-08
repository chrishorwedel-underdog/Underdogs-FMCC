import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Activity, Check } from "lucide-react";
import { api, ago, gameDate } from "@/lib/api";
import { ModuleCards } from "@/components/ModuleCards";
import { UpNext } from "@/components/Notify";

const WORDS = ["Nothing", "One thing", "Two things", "Three things", "Four things", "Five things"];
const greet = () => { const h = new Date().getHours(); return h < 12 ? "Good morning," : h < 18 ? "Good afternoon," : "Good evening,"; };

const Attention = ({ items }) => {
  const nav = useNavigate();
  return (
    <div className="card rise d3" data-testid="home-attention">
      <div className="ttl">Needs your attention<span className="st a mono" style={{ marginLeft: "auto" }}>{items.length}</span></div>
      {items.length === 0 && <p className="note" style={{ marginTop: 12 }}>All clear.</p>}
      {items.map((it, i) => (
        <div className="item" key={`${it.kind}-${it.unique_id}`} data-testid={`attention-item-${i}`}>
          <span className="bar" style={{ background: `var(--${it.tone})`, boxShadow: `0 0 10px var(--${it.tone})` }} />
          <div><p>{it.text}</p><small>{it.sub}</small>
            <div className="acts"><button className="btn" onClick={() => nav(`/squad?player=${it.unique_id}`)} data-testid={`attention-view-${i}`}>View player</button></div>
          </div>
        </div>
      ))}
    </div>
  );
};

const NextMatch = ({ f, club }) => (
  <div className="card rise d5" style={{ marginTop: 16 }} data-testid="home-next-match">
    <div className="ttl">Next match<span className="st g" style={{ marginLeft: "auto" }}>{f.home ? "Home" : "Away"}</span></div>
    <div className="vs">
      <div className="tm"><div className="crest">{club.slice(0, 2).toUpperCase()}</div>{club}</div>
      <div className="kick"><b className="mono">{f.kickoff}</b><small>{gameDate(f.date, { weekday: "short", day: "numeric", month: "short" })} · {f.competition}</small></div>
      <div className="tm"><div className="crest">{f.opponent.slice(0, 2).toUpperCase()}</div>{f.opponent}</div>
    </div>
    <div className="form">{f.form.map((r, i) => <i key={i} className={r}>{r}</i>)}</div>
  </div>
);

export default function Home() {
  const { data: d, isLoading } = useQuery({ queryKey: ["home"], queryFn: () => api.get("/home").then((r) => r.data) });
  if (isLoading || !d) return <p className="note">Loading your club…</p>;
  const n = d.attention.length;
  return (
    <div className="home-v2" data-testid="home-page">
      <div className="hero">
        <div>
          <div className="eyebrow rise">{gameDate(d.game_date)} · Season {d.season}</div>
          <h1 className="h rise d1">{greet()} <span className="serif">Boss.</span></h1>
          <p className="lede rise d2" data-testid="home-status-line">Everything is up to date. <b>{WORDS[Math.min(n, 5)]}</b> {n === 1 ? "needs" : "need"} your attention today.</p>
        </div>
        <div className="hchips rise d3">
          {d.next_fixture && <div className="hchip"><Activity size={15} />Next: <b>{d.next_fixture.opponent}</b></div>}
          <div className="hchip" data-testid="home-backup-chip"><Check size={15} /><b>Backup</b> saved {ago(d.last_backup)}</div>
        </div>
      </div>
      <UpNext />
      <ModuleCards d={d} />
      <div className="home-bottom" data-testid="home-bottom">
        <Attention items={d.attention} />
        {d.next_fixture && <NextMatch f={d.next_fixture} club={d.club_name} />}
      </div>
    </div>
  );
}
