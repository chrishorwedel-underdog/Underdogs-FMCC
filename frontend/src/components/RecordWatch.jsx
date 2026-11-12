import { Link } from "react-router-dom";
import { Target } from "lucide-react";
import { useGet } from "@/lib/ui";
import { openPlayer } from "@/components/player/PlayerPanel";

const Row = ({ r }) => (
  <button className={`rw-row${r.gap < 0 ? " past" : ""}`} onClick={() => openPlayer(r.unique_id)} data-testid={`record-watch-${r.id}`}>
    <span className="rw-who"><b>{r.name}</b> is {r.text}</span>
    <small>{r.label}: {r.value} now · best {r.best.value} by {r.best.name}, {r.best.season}</small>
    <span className="rw-bar"><i style={{ width: `${Math.min(100, r.share * 100)}%` }} /></span>
  </button>
);

export const RecordWatch = () => {
  const { data } = useGet("record-watch", "/history/record-watch");
  if (!data?.items?.length) return null;
  return (
    <div className="card rise d3 rw" data-testid="record-watch-panel">
      <div className="cel-head"><Target size={16} /><b>Record Watch</b><span className="note" style={{ marginLeft: "auto" }}>{data.season} vs every completed season</span></div>
      <div style={{ display: "grid", gap: 6 }}>{data.items.map((r) => <Row key={r.id} r={r} />)}</div>
      <Link className="linkish" to="/club-history?tab=leaders" data-testid="record-watch-open-leaders">See all-time leaders</Link>
    </div>
  );
};
