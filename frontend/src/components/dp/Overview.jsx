import { useState } from "react";
import { Play, Snowflake, Flag, TrendingUp, TrendingDown, Minus, PauseCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { PlayerDetail } from "./PlayerDetail";

const KEYS = ["dp-overview", "dp-records", "changes"];
const STAGE = { before_winter: "Before the winter review", winter_done: "Winter review done", season_done: "Season-end review done" };

export const Signal = ({ r }) => {
  if (r.status === "superseded") return <span className="st n" data-testid={`dp-signal-${r.unique_id}`}>Settled at season-end</span>;
  if (r.status === "held" || r.status === "flag") return <span className="st a" data-testid={`dp-signal-${r.unique_id}`}><PauseCircle size={12} />{r.status === "held" ? "Held" : "Watching"}</span>;
  if (r.change > 0) return <span className="st g" data-testid={`dp-signal-${r.unique_id}`}><TrendingUp size={12} />+{r.change}</span>;
  if (r.change < 0) return <span className="st r" data-testid={`dp-signal-${r.unique_id}`}><TrendingDown size={12} />{r.change}</span>;
  return <span className="st n" data-testid={`dp-signal-${r.unique_id}`}><Minus size={12} />Steady</span>;
};

export const RecordCard = ({ r, open, children }) => (
  <div className="card" style={{ padding: 14, cursor: "pointer" }} onClick={() => open(r.unique_id)} data-testid={`dp-card-${r.kind}-${r.unique_id}`}>
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}><b style={{ flex: 1 }}>{r.name}</b><Signal r={r} /></div>
    <small style={{ display: "block", color: "var(--dim)" }}>{r.kind === "winter" ? "Winter review" : "Season-end review"} · {r.club} · {r.position}{r.status === "needs_review" ? " · needs your review" : ""}</small>
    {r.kind === "season_end" && r.winter_applied > 0 && <small style={{ display: "block" }} data-testid={`dp-season-total-${r.unique_id}`}>Season total {r.change + r.winter_applied > 0 ? "+" : ""}{r.change + r.winter_applied} (including +{r.winter_applied} at winter)</small>}
    <p className="note" style={{ margin: "6px 0 0" }}>{r.reason}</p>
    {children}
  </div>
);

const Status = ({ o, act }) => {
  const [date, setDate] = useState(o.winter_date);
  const run = (kind) => (kind === "winter" || window.confirm("Run the season-end review now? It settles the whole season and should run after the final competitive match."))
    && act(() => api.post(`/dp/review/${kind}`, {}), (r) => r.summary + (r.applied?.waiting_reason ? `. Waiting in Game changes: ${r.applied.waiting_reason}` : ""), KEYS);
  const locked = o.reviewed.winter + o.reviewed.season_end > 0;
  return (
    <div className="card" data-testid="dp-status">
      <div className="ttl"><Snowflake size={14} />{o.season} · <span data-testid="dp-stage">{STAGE[o.stage]}</span></div>
      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginTop: 10 }}>
        <small>Winter review date (splits the season into two halves)</small>
        <input className="inp" type="date" style={{ width: 170 }} value={date} disabled={locked} onChange={(e) => setDate(e.target.value)} data-testid="dp-winter-date" />
        {!locked && date !== o.winter_date && <button className="btn" onClick={() => act(() => api.put("/dp/season", { winter_date: date }), "Winter date saved", KEYS)} data-testid="dp-winter-date-save">Save date</button>}
        {o.winter_suggested && <small style={{ color: "var(--dim)" }}>Suggested from the winter transfer window</small>}
      </div>
      <p className="note" style={{ marginTop: 8 }}>{o.covered} players reviewed (change who in "Who's reviewed"). Results go into your save straight away; anything needing your review waits.</p>
      <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
        <button className={`btn ${o.next_review === "winter" ? "btn-p" : ""}`} onClick={() => run("winter")} data-testid="dp-run-winter"><Play size={13} />Run winter review</button>
        <button className={`btn ${o.next_review === "season_end" ? "btn-p" : ""}`} onClick={() => run("season_end")} data-testid="dp-run-season"><Flag size={13} />Run season-end review</button>
      </div>
    </div>
  );
};

const Counts = ({ c }) => (
  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(120px,1fr))", gap: 10 }} data-testid="dp-counts">
    {[["rising", "Rising", "var(--grn)"], ["steady", "Steady", "var(--mut)"], ["falling", "Falling", "var(--red)"], ["held", "Held or watching", "var(--amb)"], ["review", "Needs your review", "var(--acc)"]].map(([k, l, col]) => (
      <div key={k} className="card" style={{ padding: 12 }} data-testid={`dp-count-${k}`}><small>{l}</small><b style={{ display: "block", fontSize: 24, color: col }}>{c[k]}</b></div>))}
  </div>
);

export const Overview = () => {
  const { data: o } = useGet("dp-overview", "/dp");
  const { data: recs = [] } = useGet("dp-records", "/dp/records");
  const act = useAct();
  const [open, setOpen] = useState(null);
  if (!o) return <p className="note">Loading Dynamic Potential…</p>;
  const latest = recs.filter((r) => r.kind === (o.reviewed.season_end ? "season_end" : "winter"));
  return (
    <div style={{ display: "grid", gap: 16 }} data-testid="dp-overview">
      <Status key={o.winter_date} o={o} act={act} />
      <Counts c={o.counts} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(280px,1fr))", gap: 12 }} data-testid="dp-cards">
        {latest.map((r) => <RecordCard key={r.id} r={r} open={setOpen} />)}
      </div>
      {!latest.length && <p className="note" data-testid="dp-empty">No review has run this season yet.</p>}
      <PlayerDetail uid={open} onClose={() => setOpen(null)} />
    </div>
  );
};
