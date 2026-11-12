import { X, Trophy, Dumbbell } from "lucide-react";
import { useGet } from "@/lib/ui";
import { usePersist } from "@/lib/remember";
import { openPlayer } from "@/components/player/PlayerPanel";

const STATS = [["appearances", "Apps"], ["minutes", "Minutes"], ["goals", "Goals"], ["assists", "Assists"], ["avg_rating", "Avg rating"]];

const BreakoutCard = ({ c }) => (
  <>
    <div className="cel-stats" data-testid="celebration-breakout-stats">{STATS.map(([k, l]) => <div key={k}><b className="mono">{c.stats[k] ?? "—"}</b><small>{l}</small></div>)}</div>
    {c.note && <p className="note" style={{ margin: 0 }}>{c.note}, the best season among his teammates.</p>}
    <p className="cel-reward" data-testid="celebration-breakout-reward">Reward: {c.reward}</p>
    <button className="btn" style={{ justifySelf: "start" }} onClick={() => openPlayer(c.unique_id)} data-testid="celebration-breakout-open">View player</button>
  </>
);

const EliteCard = ({ c }) => (
  <>
    <p className="note" style={{ margin: 0 }}>{c.summary}</p>
    <div style={{ display: "grid", gap: 4 }}>{c.players.map((p) => (
      <button key={p.unique_id} className="wc-row green" onClick={() => openPlayer(p.unique_id)} data-testid={`celebration-elite-${p.unique_id}`}><i /><b>{p.name}{p.age ? `, ${p.age}` : ""}</b><span>{p.benefit}</span></button>))}</div>
  </>
);

export const Celebrations = () => {
  const { data } = useGet("celebrations", "/celebrations");
  const [gone, setGone] = usePersist("celebrations-dismissed", {});
  const cards = (data?.cards || []).filter((c) => !gone[c.id]);
  if (!cards.length) return null;
  return cards.map((c) => (
    <section key={c.id} className={`card rise cel cel-${c.kind}`} data-testid={`celebration-${c.kind}`}>
      <div className="cel-head">{c.kind === "breakout" ? <Trophy size={20} color="#F5C542" /> : <Dumbbell size={20} color="var(--grn)" />}
        <b data-testid={`celebration-${c.kind}-title`}>{c.title}</b>
        <button className="ib" style={{ marginLeft: "auto", width: 28, height: 28 }} onClick={() => setGone((g) => ({ ...g, [c.id]: true }))} aria-label="Dismiss" data-testid={`celebration-${c.kind}-dismiss`}><X size={14} /></button></div>
      {c.kind === "breakout" ? <BreakoutCard c={c} /> : <EliteCard c={c} />}
      <small className="note">Described in general terms only. True CA and PA are never shown.</small>
    </section>
  ));
};
