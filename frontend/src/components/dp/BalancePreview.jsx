import { FlaskConical } from "lucide-react";
import { useGet } from "@/lib/ui";

const Bar = ({ r }) => {
  const n = r.players || 1;
  return (
    <div style={{ display: "flex", height: 8, borderRadius: 4, overflow: "hidden", background: "var(--line)" }} data-testid={`dp-preview-bar-${r.position}`}>
      {[["rising", "var(--grn)"], ["steady", "var(--mut)"], ["falling", "var(--red)"], ["waiting", "var(--amb)"]].map(([k, c]) => <i key={k} title={`${r[k]} ${k}`} style={{ width: `${(r[k] / n) * 100}%`, background: c, display: "block" }} />)}
    </div>
  );
};

export const BalancePreview = () => {
  const { data, isFetching, refetch } = useGet("dp-preview", "/dp/preview", undefined, { staleTime: 0 });
  if (!data) return <p className="note">Running the season-end rules over your save…</p>;
  const t = data.totals;
  return (
    <div className="card" data-testid="dp-preview">
      <div className="ttl"><FlaskConical size={14} />Balance preview · season-end review · {data.season}
        <span style={{ marginLeft: "auto" }} /><button className="btn" disabled={isFetching} onClick={() => refetch()} data-testid="dp-preview-rerun">{isFetching ? "Running…" : "Run again"}</button></div>
      <p className="note" style={{ marginTop: 4 }} data-testid="dp-preview-note">{data.note}</p>
      <p style={{ margin: "10px 0" }} data-testid="dp-preview-totals"><b>{t.players}</b> players: <span style={{ color: "var(--grn)" }}>{t.rising} rising</span> · {t.steady} steady · <span style={{ color: "var(--red)" }}>{t.falling} falling</span> · <span style={{ color: "var(--amb)" }}>{t.waiting} waiting</span></p>
      <table className="tbl" data-testid="dp-preview-table">
        <thead><tr><th>Position</th><th>Players</th><th>Rising</th><th>Steady</th><th>Falling</th><th>Waiting</th><th>Average rise</th><th>Average fall</th><th style={{ width: 180 }} /></tr></thead>
        <tbody>{data.positions.map((r) => (
          <tr key={r.position} data-testid={`dp-preview-row-${r.position}`}>
            <td>{r.label}</td><td className="mono">{r.players}</td><td className="mono" style={{ color: "var(--grn)" }}>{r.rising}</td><td className="mono">{r.steady}</td>
            <td className="mono" style={{ color: "var(--red)" }}>{r.falling}</td><td className="mono" style={{ color: "var(--amb)" }}>{r.waiting}</td>
            <td className="mono">{r.avg_up != null ? `+${r.avg_up}` : "\u2014"}</td><td className="mono">{r.avg_down ?? "\u2014"}</td><td><Bar r={r} /></td>
          </tr>))}</tbody>
      </table>
    </div>
  );
};
