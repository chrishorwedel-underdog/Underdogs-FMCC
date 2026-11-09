import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { gameDate } from "@/lib/api";
import { useGet, TabBar, PageHead } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";
import { WorldReport } from "@/components/world/WorldReport";

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
            <div className="card"><div className="ch">Squad CA gained</div><div className="num" data-testid="report-total">{data.summary.total_change > 0 ? "+" : ""}{data.summary.total_change}</div></div>
            <div className="card"><div className="ch">Rising / falling</div><div className="num" data-testid="report-rising">{data.summary.rising}<small>rising · {data.summary.falling} falling</small></div></div>
            <div className="card"><div className="ch">Squad changes</div><p className="sent">Joined: <b>{data.summary.joined.join(", ") || "nobody"}</b></p><p className="sent">Left: <b>{data.summary.left.join(", ") || "nobody"}</b></p></div>
          </div>
          <div className="card" style={{ padding: 8, overflowX: "auto" }}>
            <table className="tbl" data-testid="report-table">
              <thead><tr><th>Player</th><th>Age</th><th>CA gained</th><th>Minutes</th><th>Goals</th><th>Assists</th><th>Rating</th><th>Trend</th></tr></thead>
              <tbody>{data.rows.map((r) => (
                <tr key={r.unique_id} style={{ cursor: "default" }}><td>{r.name}</td><td>{r.age}</td>
                  <td className={`mono ${r.ca_change > 0 ? "up" : r.ca_change < 0 ? "down" : ""}`}>{r.ca_change > 0 ? "+" : ""}{r.ca_change}</td><td className="mono">{r.minutes}</td><td className="mono">{r.goals}</td><td className="mono">{r.assists}</td>
                  <td className="mono">{r.avg_rating ?? "—"}</td><td><span className={`st ${r.trend === "rising" ? "ok" : r.trend === "falling" ? "r" : "n"}`}>{r.trend}</span></td></tr>))}</tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

const World = () => {
  const [params, setParams] = useSearchParams();
  const country = params.get("country");
  const month = params.get("month");
  const { data, error } = useGet("world-report", "/world/report", { country, month });
  const go = (k, v) => { const n = new URLSearchParams(params); v ? n.set(k, v) : n.delete(k); setParams(n); window.scrollTo(0, 0); };
  if (error) return <div className="soon">{error.response?.data?.detail || "Couldn't load the report."}</div>;
  if (!data) return <p className="note">Loading the world report…</p>;
  return (
    <div>
      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginBottom: 14 }}>
        <select className="inp" style={{ width: 200 }} value={data.month} onChange={(e) => go("month", e.target.value)} data-testid="world-month-select">{data.months.map((m) => <option key={m} value={m}>{gameDate(`${m}-01`, { month: "long", year: "numeric" })}</option>)}</select>
        <select className="inp" style={{ width: 200 }} value={country || ""} onChange={(e) => go("country", e.target.value)} data-testid="world-country-select"><option value="">The World</option>{data.countries.map((c) => <option key={c.country} value={c.country}>{c.country}</option>)}</select>
        {country && <button className="btn" onClick={() => go("country", null)} data-testid="world-back">Back to the World report</button>}
      </div>
      <WorldReport d={data} openCountry={(c) => go("country", c)} />
    </div>
  );
};

export default function Reports() {
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") || "world";
  const setTab = (t) => { const n = new URLSearchParams(params); t === "world" ? n.delete("tab") : n.set("tab", t); setParams(n); };
  return (
    <div data-testid="reports-page">
      <PageHead eyebrow="Who's been making waves across every loaded league" title="World Monthly Reports">
        <TabBar id="reports" value={tab} onChange={setTab} tabs={[["world", "World & countries"], ["compare", "My squad"], ["rules", "Rules"]]} />
      </PageHead>
      {tab === "world" ? <World /> : tab === "compare" ? <Compare /> : <RulesTab module="reports" title="Monthly Report rules" />}
    </div>
  );
}
