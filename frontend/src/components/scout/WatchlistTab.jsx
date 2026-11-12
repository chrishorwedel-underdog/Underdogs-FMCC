import { useState } from "react";
import { Trash2, SlidersHorizontal } from "lucide-react";
import { WatchRules } from "@/components/scout/WatchRules";
import { Loading } from "@/components/Loading";
import { Empty } from "@/components/Empty";
import { useWatchlist, useToggleWatch } from "@/components/WatchButton";

const TONE = { up: "var(--grn)", down: "var(--red)", info: "#F5C542" };
const money = (v) => (v ? `£${(v / 1e6).toFixed(1)}m` : "—");

export const WatchlistTab = ({ open }) => {
  const { data } = useWatchlist();
  const toggle = useToggleWatch();
  const [edit, setEdit] = useState(null);
  if (!data) return <Loading id="watchlist-loading" rows={5} label="Loading your watchlist" />;
  if (!data.rows.length) return <Empty id="watchlist-empty" reason="empty" text="Nobody watched yet. Press the eye button on any player in Find players, Squad or a player profile. You'll get a bell notice when his grade moves 2+ points, his value moves 10%+, or his contract status changes." />;
  return (
    <div className="card" style={{ padding: 0, overflowX: "auto" }} data-testid="watchlist-tab">
      <p className="note" style={{ padding: "12px 14px 0" }}>Checked every time FMCC reads your save. Standard alerts: grade ±2, value ±10%, new deal, last 6 months, free agent or transfer. Set your own rules per player to replace them.</p>
      <table className="tbl">
        <thead><tr><th>Player</th><th>Club</th><th>Grade</th><th>Value</th><th>Contract ends</th><th>Alert rules</th><th>Latest change</th><th></th></tr></thead>
        <tbody>{data.rows.map((r) => (
          <tr key={r.unique_id} onClick={() => open(r.unique_id)} data-row-uid={r.unique_id} data-testid={`watch-row-${r.unique_id}`}>
            <td><b>{r.last.name}</b></td><td>{r.last.club || "Free agent"}</td><td className="mono">{r.last.grade ?? "—"}</td><td className="mono">{money(r.last.value)}</td>
            <td className="mono">{r.last.contract_end || "—"}</td>
            <td onClick={(e) => e.stopPropagation()} data-testid={`watch-rules-${r.unique_id}`}>
              {r.rules.length ? r.rules.map((x) => <small key={x.id} style={{ display: "block", color: x.now ? "#F5C542" : "var(--text)" }}>{x.text}{x.now ? " (true now)" : ""}</small>) : <small style={{ color: "var(--dim)" }}>Standard alerts</small>}
              <button className="btn" style={{ marginTop: 4, padding: "3px 8px", fontSize: 12 }} onClick={() => setEdit(r)} data-testid={`watch-rules-edit-${r.unique_id}`}><SlidersHorizontal size={12} />{r.rules.length ? "Edit" : "Set rules"}</button></td>
            <td data-testid={`watch-latest-${r.unique_id}`}>{r.latest ? <span style={{ color: TONE[r.latest.tone] }}>{r.latest.text}<small style={{ display: "block", color: "var(--dim)" }}>{r.latest.game_date}</small></span> : <span style={{ color: "var(--dim)" }}>No change yet</span>}</td>
            <td onClick={(e) => e.stopPropagation()}><button className="ib" style={{ width: 28, height: 28 }} onClick={() => toggle(r.unique_id, r.last.name, true)} aria-label={`Remove ${r.last.name} from watchlist`} data-testid={`watch-remove-${r.unique_id}`}><Trash2 size={13} /></button></td>
          </tr>))}</tbody>
      </table>
      {edit && <WatchRules row={edit} onClose={() => setEdit(null)} />}
    </div>
  );
};
