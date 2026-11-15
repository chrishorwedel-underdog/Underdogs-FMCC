import { Link } from "react-router-dom";
import { ArrowLeft, Printer, Copy, Trophy } from "lucide-react";
import { toast } from "sonner";
import { useGet } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { openPlayer } from "@/components/player/PlayerPanel";

export const printPage = (cls = "printing-page") => {
  document.body.classList.add(cls);
  const done = () => { document.body.classList.remove(cls); window.removeEventListener("afterprint", done); };
  window.addEventListener("afterprint", done);
  setTimeout(() => window.print(), 50);
};

export const PrintButton = ({ id, label = "Print / save as PDF" }) => <button className="btn no-print" onClick={() => printPage()} data-testid={`${id}-print`}><Printer size={13} />{label}</button>;

const top = (squad, key, min = 0) => [...squad].filter((r) => r[key] != null && (r.minutes || 0) >= min).sort((a, b) => b[key] - a[key])[0];

const bestWin = (ms) => ms.filter((m) => Array.isArray(m.score) && m.score[0] > m.score[1]).sort((a, b) => (b.score[0] - b.score[1]) - (a.score[0] - a.score[1]))[0];

const summaryText = (s, stars, moments) => [
  `${s.club} · ${s.season} season report${s.status === "In Progress" ? " (so far)" : ""}`,
  s.league ? `League: ${s.league.pos}${["st", "nd", "rd"][s.league.pos - 1] || "th"} of ${s.league.of} in ${s.league.division}, ${s.league.pts} points` : "League: unavailable",
  `Honours: ${s.honours.map((h) => h.name || h.competition).join(", ") || "none"}`,
  ...stars.map(([l, r, v]) => `${l}: ${r.name} (${v})`),
  ...moments.map((m) => `• ${m}`),
  "Made with FM Command Centre"].join("\n");

const Star = ({ label, r, v }) => (
  <button className="rc-star" onClick={() => openPlayer(r.unique_id)} data-testid={`report-star-${label.toLowerCase().replace(/\s+/g, "-")}`}>
    <small>{label}</small><b>{r.name}</b><span className="mono">{v}</span></button>
);

export const SeasonReport = ({ season }) => {
  const [y1, y2] = season.split("/");
  const { data: s, isError } = useGet(["history-season", season], `/history/seasons/${y1}/${y2}`, undefined, { retry: false });
  const { data: ms } = useGet("history-milestones", "/history/milestones");
  if (isError) return <p className="note" data-testid="report-missing">That season isn't in your history.</p>;
  if (!s) return <Loading id="report-loading" rows={6} label="Building the season report" />;
  const sq = s.squad.filter((r) => r.appearances);
  const picks = [["Top scorer", top(sq, "goals"), "goals"], ["Most assists", top(sq, "assists"), "assists"], ["Best average rating", top(sq, "avg_rating", 900), "rating"], ["Ever-present", top(sq, "appearances"), "apps"]];
  const stars = picks.filter(([, r, k]) => r && r[k === "rating" ? "avg_rating" : k === "apps" ? "appearances" : k]).map(([l, r, k]) => [l, r, `${r[k === "rating" ? "avg_rating" : k === "apps" ? "appearances" : k]} ${k}`]);
  const win = bestWin(s.matches || []);
  const moments = [...(ms?.milestones || []).filter((m) => m.season === season).map((m) => m.title),
    ...(win ? [`Biggest win: ${win.score[0]}-${win.score[1]} ${win.home ? "vs" : "at"} ${win.opponent}`] : []),
    ...(s.academy.debuts.length ? [`Academy debuts: ${s.academy.debuts.join(", ")}`] : []),
    ...(s.academy.elite.length ? [`Elite Training graduates: ${s.academy.elite.join(", ")}`] : [])];
  const copy = () => navigator.clipboard.writeText(summaryText(s, stars, moments)).then(() => toast.success("Report copied, ready to paste anywhere"), () => toast.error("Couldn't copy on this device"));
  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div className="no-print" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Link to={`/club-history?season=${season}`} className="btn" data-testid="report-back"><ArrowLeft size={13} />Season page</Link>
        <span style={{ marginLeft: "auto" }} />
        <button className="btn" onClick={copy} data-testid="report-copy"><Copy size={13} />Copy as text</button>
        <button className="btn btn-p" onClick={() => printPage()} data-testid="report-print"><Printer size={13} />Print / save as PDF</button>
      </div>
      <article className="card rc print-area" data-testid="season-report">
        <header className="rc-head"><div><div className="eyebrow">Season report{s.status === "In Progress" ? " · so far" : ""}</div><h2>{s.club} · {s.season}</h2></div><Trophy size={28} /></header>
        <section className="rc-row">
          <div className="rc-box" data-testid="report-league"><small>League</small><b>{s.league ? `${s.league.pos} of ${s.league.of}` : "Unavailable"}</b><span>{s.league ? `${s.league.division} · ${s.league.pts} pts · W${s.league.w} D${s.league.d} L${s.league.l}` : "Not in the save yet"}</span></div>
          <div className="rc-box" data-testid="report-honours"><small>Honours</small><b>{s.honours.length || "None"}</b><span>{s.honours.map((h) => h.name || h.competition).join(", ") || "No trophies this season"}</span></div>
          <div className="rc-box" data-testid="report-recruit"><small>Transfers</small><b>{s.recruitment.arrivals.length} in · {s.recruitment.departures.length} out</b><span>{s.recruitment.arrivals.slice(0, 3).join(", ") || "No arrivals"}</span></div>
        </section>
        <h3>Top players</h3>
        <section className="rc-stars">{stars.length ? stars.map(([l, r, v]) => <Star key={l} label={l} r={r} v={v} />) : <p className="note">No player stats in the save yet.</p>}</section>
        <h3>Best moments</h3>
        <ul className="rc-moments" data-testid="report-moments">{moments.length ? moments.map((m) => <li key={m}>{m}</li>) : <li>No standout moments recorded yet.</li>}</ul>
        <footer className="rc-foot">From your save, read by FM Command Centre · {s.game_date}</footer>
      </article>
    </div>
  );
};
