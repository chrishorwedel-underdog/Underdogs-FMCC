import { useEffect, useState } from "react";
import { gameDate } from "@/lib/api";
import { useGet, TabBar, PageHead } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";

const Compare = () => {
  const { data: months = [] } = useGet("report-months", "/reports/months");
  const [a, setA] = useState(null);
  const [b, setB] = useState(null);
  useEffect(() => {
    if (months.length && a === null) { setA(months[Math.max(0, months.length - 2)].save_no); setB(months[months.length - 1].save_no); }
  }, [months, a]);
  const { data } = useGet("report", "/reports/compare", { a, b }, { enabled: a !== null && b !== null });
  const Sel = ({ v, set, id }) => <select className="inp" style={{ width: 200 }} value={v ?? ""} onChange={(e) => set(Number(e.target.value))} data-testid={id}>{months.map((m) => <option key={m.save_no} value={m.save_no}>{gameDate(m.game_date)}</option>)}</select>;
  return (
    <div>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 16 }}><Sel v={a} set={setA} id="report-from" /><span className="note">compared with</span><Sel v={b} set={setB} id="report-to" /></div>
      {months.length < 2 && <div className="soon">Reports appear once FMCC has read saves from two different in-game months.</div>}
      {data && (
        <>
          <div className="bento" style={{ marginBottom: 16 }}>
            <div className="card"><div className="ch">Squad ability change</div><div className="num" data-testid="report-total">{data.summary.total_change > 0 ? "+" : ""}{data.summary.total_change}</div></div>
            <div className="card"><div className="ch">Rising / falling</div><div className="num" data-testid="report-rising">{data.summary.rising}<small>rising · {data.summary.falling} falling</small></div></div>
            <div className="card"><div className="ch">Squad changes</div><p className="sent">Joined: <b>{data.summary.joined.join(", ") || "nobody"}</b></p><p className="sent">Left: <b>{data.summary.left.join(", ") || "nobody"}</b></p></div>
          </div>
          <div className="card" style={{ padding: 8, overflowX: "auto" }}>
            <table className="tbl" data-testid="report-table">
              <thead><tr><th>Player</th><th>Age</th><th>Ability</th><th>Change</th><th>Minutes</th><th>Goals</th><th>Rating</th><th>Trend</th></tr></thead>
              <tbody>{data.rows.map((r) => (
                <tr key={r.unique_id} style={{ cursor: "default" }}><td>{r.name}</td><td>{r.age}</td><td className="mono">{r.ca_from} → {r.ca_to}</td>
                  <td className={`mono ${r.ca_change > 0 ? "up" : r.ca_change < 0 ? "down" : ""}`}>{r.ca_change > 0 ? "+" : ""}{r.ca_change}</td><td className="mono">{r.minutes}</td><td className="mono">{r.goals}</td>
                  <td className="mono">{r.avg_rating ?? "—"}</td><td><span className={`st ${r.trend === "rising" ? "ok" : r.trend === "falling" ? "r" : "n"}`}>{r.trend}</span></td></tr>))}</tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default function Reports() {
  const [tab, setTab] = useState("compare");
  return (
    <div data-testid="reports-page">
      <PageHead eyebrow="An automatic squad snapshot every in-game month" title="Monthly Reports">
        <TabBar id="reports" value={tab} onChange={setTab} tabs={[["compare", "Compare months"], ["rules", "Rules"]]} />
      </PageHead>
      {tab === "compare" ? <Compare /> : <RulesTab module="reports" title="Monthly Report rules" />}
    </div>
  );
}
