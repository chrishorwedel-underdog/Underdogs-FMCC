import { useState } from "react";
import { Zap } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct, TabBar, PageHead } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";

const Spark = ({ pts }) => {
  const v = pts.map((p) => p.rating || 0);
  if (v.length < 2) return <span className="mono">{v[0] ?? "—"}</span>;
  const lo = Math.min(...v) - 0.2, hi = Math.max(...v) + 0.2;
  const d = v.map((x, i) => `${(i / (v.length - 1)) * 100},${28 - ((x - lo) / (hi - lo)) * 26}`).join(" ");
  return <svg width="110" height="30" viewBox="0 0 100 30" preserveAspectRatio="none"><polyline points={d} fill="none" stroke="var(--acc)" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg>;
};

const Nominees = () => {
  const { data } = useGet("elite", "/elite");
  const act = useAct();
  const [pick, setPick] = useState("");
  if (!data) return <p className="note">Loading nominations…</p>;
  const nominate = (uid) => act(() => api.post("/elite/nominations", { unique_id: Number(uid), note: "" }), "Nominated for Elite Training", ["elite"]);
  const queue = () => act(() => api.post("/elite/queue"), (d) => `${d.queued} potential boost(s) ${d.auto_applied ? "applied to your save" : "waiting in Game changes"}${d.skipped_duplicates ? `, ${d.skipped_duplicates} already given this month` : ""}${d.not_qualified ? `, ${d.not_qualified} didn't qualify` : ""}`, ["elite", "changes", "home"]);
  return (
    <div className="homegrid">
      <div className="card" style={{ padding: 8, overflowX: "auto" }}>
        <div className="ttl" style={{ padding: 10 }}>Nominees<span style={{ marginLeft: "auto" }} /><button className="btn btn-p" disabled={!data.nominees.length} onClick={queue} data-testid="elite-queue-button"><Zap size={13} />Work out PA boosts</button></div>
        <table className="tbl" data-testid="elite-table">
          <thead><tr><th>Player</th><th>Age</th><th>Training rating</th><th>Trend</th><th>Growth</th><th>Rule</th><th></th></tr></thead>
          <tbody>{data.nominees.map((n) => (
            <tr key={n.unique_id} style={{ cursor: "default" }} data-testid={`elite-row-${n.unique_id}`}>
              <td><b style={{ color: "var(--text)" }}>{n.name}</b></td><td>{n.age}</td><td className="mono">{n.training_rating}</td><td><Spark pts={n.evidence} /></td>
              <td className="mono">{n.ca_growth > 0 ? "+" : ""}{n.ca_growth}</td>
              <td>{n.rule ? <>{n.rule}<small style={{ display: "block", color: "var(--dim)" }}>{n.preview}</small></> : <span style={{ color: "var(--dim)" }}>Doesn't qualify yet</span>}</td>
              <td><button className="btn" onClick={() => act(() => api.post(`/elite/nominations/${n.unique_id}/withdraw`), "Nomination withdrawn", ["elite"])} data-testid={`elite-withdraw-${n.unique_id}`}>Withdraw</button></td>
            </tr>))}</tbody>
        </table>
        {!data.nominees.length && <p className="note" style={{ padding: 10 }}>No nominees yet.</p>}
      </div>
      <div className="card"><div className="ttl">Nominate</div>
        <p className="note" style={{ marginTop: 6 }}>Best young trainees right now, from the save's training ratings:</p>
        {data.suggestions.map((s) => <div className="row" key={s.unique_id}><div style={{ flex: 1 }}>{s.name}<small>{s.age} · training {s.training_rating}</small></div><button className="btn" onClick={() => nominate(s.unique_id)} data-testid={`elite-nominate-${s.unique_id}`}>Nominate</button></div>)}
        <label className="lbl" style={{ marginTop: 12 }}>Or by game ID</label>
        <div style={{ display: "flex", gap: 8 }}><input className="inp mono" value={pick} onChange={(e) => setPick(e.target.value)} data-testid="elite-nominate-id" /><button className="btn" style={{ height: 40 }} disabled={!pick} onClick={() => nominate(pick)}>Add</button></div>
      </div>
    </div>
  );
};

export default function EliteTraining() {
  const [tab, setTab] = useState("nominees");
  return (
    <div data-testid="elite-page">
      <PageHead eyebrow="Nominations, training evidence and PA boosts" title="Elite Training">
        <TabBar id="elite" value={tab} onChange={setTab} tabs={[["nominees", "Nominees"], ["rules", "Rules"]]} />
      </PageHead>
      {tab === "nominees" ? <Nominees /> : <RulesTab module="elite" title="Elite Training rules" />}
    </div>
  );
}
