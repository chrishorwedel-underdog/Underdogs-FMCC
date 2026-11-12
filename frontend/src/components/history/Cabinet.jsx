import { useState } from "react";
import { Link } from "react-router-dom";
import { Trophy, Pin, PinOff, Medal, Flag, Star } from "lucide-react";
import { toast } from "sonner";
import { api, errMsg } from "@/lib/api";
import { useGet, TabBar } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { openPlayer } from "@/components/player/PlayerPanel";
import { useQueryClient } from "@tanstack/react-query";

export const U = ({ v, unit = "" }) => (v == null || v === "" ? <span className="unavail" data-testid="unavailable">Unavailable</span> : <>{v}{unit}</>);
export const money = (v) => (v == null ? null : `${v < 0 ? "−" : ""}£${(Math.abs(v) / 1e6).toFixed(1)}m`);
export const seasonLink = (s) => `/club-history?season=${encodeURIComponent(s)}`;
export const Status = ({ s }) => <span className={`st ${s === "Completed" ? "ok" : "a"}`} data-testid="season-status">{s}</span>;

const Who = ({ r }) => (r.unique_id ? <button className="linkish" onClick={() => openPlayer(r.unique_id)}>{r.name}</button> : r.name ? <span>{r.name}</span> : null);

export const SeasonTable = ({ rows, id = "seasons-table" }) => (
  <div style={{ overflowX: "auto" }}><table className="tbl" data-testid={id}>
    <thead><tr><th>Season</th><th>Division</th><th>Finish</th><th>Points</th><th>Best cup run</th><th>Top scorer</th><th>Honours</th></tr></thead>
    <tbody>{rows.map((s) => <tr key={s.season} data-testid={`season-row-${s.season}`}>
      <td><Link to={seasonLink(s.season)} className="linkish"><b>{s.season}</b></Link> {s.status !== "Completed" && <Status s={s.status} />}</td>
      <td><U v={s.division} /></td><td className="mono">{s.finish ? `${s.finish}${s.of ? ` of ${s.of}` : ""}` : <U v={null} />}</td><td className="mono"><U v={s.points} /></td>
      <td><U v={s.best_cup} /></td><td>{s.top_scorer ? <><Who r={s.top_scorer} /> <span className="mono">({s.top_scorer.goals})</span></> : <U v={null} />}</td>
      <td>{s.honours.length ? s.honours.join(", ") : "—"}</td></tr>)}</tbody></table></div>
);

export const Timeline = ({ items, full }) => {
  const qc = useQueryClient();
  const pin = async (m) => {
    try { if (m.pinned) { await api.delete(`/history/pins/${encodeURIComponent(m.id)}`); } else { await api.post("/history/pins", { id: m.id }); } qc.invalidateQueries({ queryKey: ["history-cabinet"] }); qc.invalidateQueries({ queryKey: ["history-milestones"] }); } catch (e) { toast.error(errMsg(e)); }
  };
  if (!items.length) return <p className="note">No milestones yet.</p>;
  return <div className="timeline" data-testid="history-timeline">{items.map((m) => (
    <div key={m.id} className={`tl-item${m.pinned ? " pinned" : ""}`} data-testid={`milestone-row-${m.id}`}>
      <span className="tl-dot" /><span className="mono tl-season">{m.season}</span>
      <div style={{ flex: 1 }}>{m.unique_id ? <button className="linkish" onClick={() => openPlayer(m.unique_id)}><b>{m.title}</b></button> : m.link ? <Link to={m.link} className="linkish"><b>{m.title}</b></Link> : <b>{m.title}</b>}
        {m.note && <small style={{ display: "block", color: "var(--dim)" }}>{m.note}</small>}</div>
      {full && <button className="ib" style={{ width: 28, height: 28 }} onClick={() => pin(m)} title={m.pinned ? "Unpin" : "Pin this moment"} aria-label={m.pinned ? "Unpin" : "Pin"} data-testid={`milestone-pin-${m.id}`}>{m.pinned ? <PinOff size={13} /> : <Pin size={13} />}</button>}
    </div>))}</div>;
};

const Honour = ({ h }) => (
  <div className="row" data-testid={`honour-${h.season}-${h.competition}`}>
    <Trophy size={16} color={h.kind === "trophy" ? "#F5C542" : h.kind === "runner_up" ? "#B8C0CC" : "var(--grn)"} />
    <div style={{ flex: 1 }}><b>{h.competition || "Competition"}</b> {h.tenure ? <span className="tag st ok">Your tenure</span> : h.pre_save ? <span className="tag st n">Before this save</span> : null}
      <small>{[h.season, h.manager && `Manager ${h.manager}`, h.opponent && `Final vs ${h.opponent}${h.score ? ` ${h.score}` : ""}${h.venue ? ` at ${h.venue}` : ""}`, h.scorers && `Scorers: ${[].concat(h.scorers).join(", ")}`].filter(Boolean).join(" · ")}</small></div>
    {h.link_season && <Link to={seasonLink(h.link_season)} className="btn" style={{ padding: "3px 8px", fontSize: 12 }}>Season</Link>}
  </div>
);

const Block = ({ id, icon: I, title, total, children, empty }) => (
  <div className="card" data-testid={`cabinet-${id}`}><div className="ttl" style={{ display: "flex", alignItems: "center", gap: 8 }}><I size={15} />{title}{total != null && <span className="st n mono" style={{ marginLeft: "auto" }}>{total}</span>}</div>
    {children || <p className="note" data-testid={`cabinet-${id}-empty`}>{empty}</p>}</div>
);

export const Cabinet = () => {
  const [scope, setScope] = useState("save");
  const { data } = useGet(["history-cabinet", scope], "/history/cabinet", { scope });
  if (!data) return <Loading id="cabinet-loading" rows={5} label="Loading the cabinet" />;
  const none = "Nothing yet. FMCC adds these when your save includes them.";
  const f = data.fmcc_awards;
  return <div style={{ display: "grid", gap: 16 }}>
    <TabBar id="cabinet-scope" value={scope} onChange={setScope} tabs={[["save", "This save"], ["full", "Full club history"]]} />
    <div className="sgrid">
      <div className="card cab-latest" data-testid="cabinet-latest"><div className="eyebrow">Latest honour</div>
        {data.latest ? <Honour h={data.latest} /> : <p className="note">No honour in this save yet.{data.in_progress ? ` ${data.in_progress.season} is in progress.` : ""}</p>}</div>
      <div className="card" data-testid="cabinet-timeline"><div className="eyebrow" style={{ marginBottom: 6 }}>Club milestones</div><Timeline items={data.timeline.slice(0, 5)} /></div>
    </div>
    <div className="card" data-testid="cabinet-last-three"><div className="eyebrow" style={{ marginBottom: 6 }}>Last three completed seasons</div>
      {data.last_three.length ? <SeasonTable rows={data.last_three} id="cabinet-seasons" /> : <p className="note">No completed season yet. {data.in_progress && <Link className="linkish" to={seasonLink(data.in_progress.season)}>Open {data.in_progress.season} (in progress)</Link>}</p>}</div>
    <div className="sgrid">
      <Block id="trophies" icon={Trophy} title="Trophies" total={data.totals.trophies} empty={none}>{data.trophies.length ? data.trophies.map((h, i) => <Honour key={i} h={h} />) : null}</Block>
      <Block id="promotions" icon={Flag} title="Promotions and runner-up finishes" total={data.totals.promotions + data.totals.runner_up} empty={none}>
        {data.promotions.length + data.runner_up.length ? <>{data.promotions.map((h, i) => <Honour key={`p${i}`} h={h} />)}{data.runner_up.map((h, i) => <Honour key={`r${i}`} h={h} />)}
          <small className="note">Promotions {data.totals.promotions} · Runners-up {data.totals.runner_up}</small></> : null}</Block>
      <Block id="individual" icon={Medal} title="Individual awards" total={data.individual.length + f.totals.breakout} empty="No player or manager awards yet.">
        {data.individual.length + f.breakout.length ? <>{f.breakout.map((b) => <div key={b.season} className="row"><Star size={14} color="#F5C542" /><div style={{ flex: 1 }}><Who r={b} /><small>Breakout Player {b.season} · {b.reward}</small></div></div>)}
          {data.individual.map((a, i) => <div key={i} className="row"><Medal size={14} /><div style={{ flex: 1 }}>{a.player_uid ? <Who r={{ unique_id: a.player_uid, name: a.player }} /> : <b>{a.player || a.title}</b>}<small>{a.award || a.title} · {a.season}</small></div></div>)}</> : null}</Block>
      <Block id="elite" icon={Star} title="Elite Training sessions" total={f.totals.sessions} empty="No session yet.">
        {f.elite.length ? f.elite.map((s) => <div key={s.id} style={{ marginBottom: 6 }}><div className="eyebrow">{s.label}</div>{s.players.map((p) => <div key={p.unique_id} className="row"><div style={{ flex: 1 }}><Who r={p} /><small>{p.benefit}</small></div></div>)}</div>) : null}</Block>
    </div>
    <small className="note">Only what FMCC read from your save, plus FMCC's own awards. Rewards are described in general terms; true CA and PA are never shown.</small>
  </div>;
};
