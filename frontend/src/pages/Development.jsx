import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { api, ago } from "@/lib/api";
import { useGet, useAct, TabBar, PageHead } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { RulesTab } from "@/components/rules/RulesTab";

const PlanDialog = ({ row, loans, close }) => {
  const act = useAct();
  const p = row.plan;
  const [f, setF] = useState({ minutes_target: p?.minutes_target ?? row.target ?? 270, loan: p?.loan || "none", goal_gain: p?.goal_gain ?? 5, note: p?.note || "" });
  const { data: hist = [] } = useGet("plan-history", `/development/plans/${row.unique_id}/history`, { uid: row.unique_id });
  const save = async () => {
    const ok = await act(() => api.post("/development/plans", { unique_id: row.unique_id, ...f, goal_gain: f.goal_gain ? Number(f.goal_gain) : null, minutes_target: Number(f.minutes_target), expected_revision: p?.revision || 0 }),
      (d) => `Plan saved (version ${d.revision})`, ["development", "plan-history"]);
    if (ok) close();
  };
  return (
    <Dialog open onOpenChange={(o) => !o && close()}>
      <DialogContent data-testid="plan-dialog">
        <DialogHeader><DialogTitle>Development plan · {row.name}</DialogTitle><DialogDescription>Revising a plan keeps every earlier version.</DialogDescription></DialogHeader>
        <label className="lbl">Minutes per month</label><input className="inp" type="number" value={f.minutes_target} onChange={(e) => setF({ ...f, minutes_target: e.target.value })} data-testid="plan-minutes-input" />
        <label className="lbl">Loan plan</label>
        <select className="inp" value={f.loan} onChange={(e) => setF({ ...f, loan: e.target.value })} data-testid="plan-loan-select">{Object.entries(loans).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
        <label className="lbl">CA to gain (from today)</label><input className="inp" type="number" min={1} max={60} value={f.goal_gain} onChange={(e) => setF({ ...f, goal_gain: e.target.value })} data-testid="plan-goal-input" />
        <label className="lbl">Note</label><input className="inp" value={f.note} maxLength={300} onChange={(e) => setF({ ...f, note: e.target.value })} data-testid="plan-note-input" />
        <button className="btn btn-p btn-l" onClick={save} data-testid="plan-save-button">Save plan</button>
        {hist.length > 0 && <div data-testid="plan-history">{hist.map((h) => <div className="row" key={h.revision}><span className="mono">v{h.revision}</span><div style={{ flex: 1 }}>{h.minutes_target} min · {loans[h.loan]} · goal {h.goal_gain ? `+${h.goal_gain} CA` : "—"}<small>{ago(h.saved_at)}{h.note ? ` · ${h.note}` : ""}</small></div></div>)}</div>}
      </DialogContent>
    </Dialog>
  );
};

const Gain = ({ v }) => (v == null ? <span style={{ color: "var(--dim)" }}>—</span> : <span className={`mono ${v > 0 ? "up" : v < 0 ? "down" : ""}`}>{v > 0 ? "+" : ""}{v}</span>);

const Plans = () => {
  const { data } = useGet("development", "/development");
  const [edit, setEdit] = useState(null);
  if (!data) return <Loading id="dev-loading" label="Loading plans" />;
  return (
    <div className="card" style={{ padding: 8, overflowX: "auto" }}>
      <table className="tbl" data-testid="plans-table">
        <thead><tr><th>Player</th><th>Age</th><th title="CA gained since last month's save">CA gained</th><th>Goals</th><th>Assists</th><th>Mins / game</th><th>Avg rating</th><th>Minutes this month</th><th>Plan</th><th>Goal</th><th></th></tr></thead>
        <tbody>{data.rows.map((r) => (
          <tr key={r.unique_id} style={{ cursor: "default" }} data-testid={`plan-row-${r.unique_id}`}>
            <td><b style={{ color: "var(--text)" }}>{r.name}</b>{r.needs_minutes && <span className="tag st a" data-testid={`needs-minutes-${r.unique_id}`}>Needs minutes</span>}</td>
            <td>{r.age}</td><td data-testid={`dev-gain-${r.unique_id}`}><Gain v={r.ca_gain_month} />{r.ca_gain_season != null && <small style={{ display: "block", color: "var(--dim)" }}>season <Gain v={r.ca_gain_season} /></small>}</td>
            <td className="mono">{r.goals}</td><td className="mono">{r.assists}</td><td className="mono">{r.minutes_per_game ?? "—"}</td><td className="mono">{r.avg_rating ?? "—"}</td>
            <td style={{ minWidth: 180 }}>{r.target ? <div className="mb" style={{ gridTemplateColumns: "1fr 70px" }}><div className="track"><i style={{ width: `${Math.min(100, (r.month_minutes / r.target) * 100)}%`, background: r.needs_minutes ? "var(--amb)" : "var(--acc)" }} /></div><span className="mono">{r.month_minutes}/{r.target}</span></div> : <span className="mono">{r.month_minutes}</span>}</td>
            <td>{r.plan ? <>{data.loans[r.plan.loan]}<small style={{ display: "block", color: "var(--dim)" }}>version {r.plan.revision}</small></> : <span style={{ color: "var(--dim)" }}>No plan</span>}</td>
            <td>{r.goal_progress != null ? <span className="mono"><Gain v={r.goal_so_far} /> of +{r.plan.goal_gain} ({r.goal_progress}%)</span> : "—"}</td>
            <td><button className="btn" onClick={() => setEdit(r)} data-testid={`plan-edit-${r.unique_id}`}>{r.plan ? "Revise" : "Add plan"}</button></td>
          </tr>))}</tbody>
      </table>
      {edit && <PlanDialog row={edit} loans={data.loans} close={() => setEdit(null)} />}
    </div>
  );
};

export default function Development() {
  const [tab, setTab] = useState("plans");
  return (
    <div data-testid="development-page">
      <PageHead eyebrow="Minutes, loans and goals, tracked from every save" title="Squad Development">
        <TabBar id="development" value={tab} onChange={setTab} tabs={[["plans", "Plans"], ["rules", "Rules"]]} />
      </PageHead>
      {tab === "plans" ? <Plans /> : <RulesTab module="development" title="Squad Development rules" />}
    </div>
  );
}
