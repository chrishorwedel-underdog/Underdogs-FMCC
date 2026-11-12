import { useGet } from "@/lib/ui";
import { useScout, fmtMoney } from "./ctx";
import { Empty } from "@/components/Empty";

const List = ({ id, title, help, rows, open, prefs }) => (
  <div className="card" style={{ padding: 8, overflowX: "auto" }} data-testid={`mb-${id}`}>
    <div className="ttl" style={{ padding: "8px 8px 2px" }}>{title}</div>
    <p className="note" style={{ padding: "0 8px 8px" }}>{help}</p>
    <table className="tbl pin1">
      <thead><tr><th>Player</th><th>Age</th><th>Value</th><th title="Global grade from per-90 output, adjusted for league strength">Grade</th><th>Why</th></tr></thead>
      <tbody>{rows.map((r) => (
        <tr key={r.unique_id} onClick={() => open(r.unique_id)} tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter" && e.target === e.currentTarget) { e.preventDefault(); open(r.unique_id); } }} data-row-uid={r.unique_id} data-testid={`mb-${id}-row-${r.unique_id}`}>
          <td><b>{r.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{r.club} · {r.positions?.join(", ")}</small></td>
          <td>{r.age}</td><td className="mono">{fmtMoney(r.value, prefs)}</td><td className="mono" style={{ color: "var(--acc)" }}>{r.grade_global}</td><td><small>{r.why}</small></td>
        </tr>))}</tbody>
    </table>
    {!rows.length && <div style={{ padding: 8 }}><Empty id={`mb-${id}-empty`} reason="nobody" text="No player meets this list's bar yet. Players need enough minutes for a fair price and a grade; more appear as the season goes on." actions={[["Search all players instead", () => window.location.assign("/scouting?tab=players")]]} /></div>}
  </div>
);

export const MoneyballTab = () => {
  const { data } = useGet("moneyball", "/scout/moneyball");
  const { prefs, openPlayer } = useScout();
  if (!data) return <p className="note">Finding value…</p>;
  return (
    <div style={{ display: "grid", gap: 16 }} data-testid="moneyball-tab">
      {data.sample && <p className="note">Match stats are SAMPLE numbers in this preview.</p>}
      <List id="bargains" title="Bargains" help="Selling well under FMCC's fair price for what they produce." rows={data.bargains} open={openPlayer} prefs={prefs} />
      <List id="vfm" title="Value for money" help="The most grade for each pound spent." rows={data.vfm} open={openPlayer} prefs={prefs} />
      <List id="undervalued" title="Undervalued per-90 performers" help="Strong per-90 output but valued below a typical player in their position." rows={data.undervalued} open={openPlayer} prefs={prefs} />
    </div>
  );
};
