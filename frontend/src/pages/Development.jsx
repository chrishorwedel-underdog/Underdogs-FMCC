import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { api, ago } from "@/lib/api";
import { useGet, useAct, TabBar, PageHead } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { RulesTab } from "@/components/rules/RulesTab";
import { useColWidths, ColGroup, ResizeTh } from "@/components/ResizableCols";
import { usePersist } from "@/lib/remember";

const COLS = { player: 230, age: 70, games: 80, mpg: 135, goals: 80, assists: 90, rating: 135, month: 190, plan: 150, goal: 130, progress: 280, act: 120 };
const HEAD = [["player", "Player"], ["age", "Age", "n"], ["games", "Games", "n"], ["mpg", "Mins / game", "n"], ["goals", "Goals", "n"], ["assists", "Assists", "n"], ["rating", "Avg rating", "n"],
  ["month", "Minutes this month"], ["plan", "Plan"], ["goal", "Goal"], ["progress", "Progress", "", "How he's coming along since last month's save and since the season started"], ["act", ""]];

const GOAL_OPTS = [["small", "Small improvement"], ["steady", "Steady improvement"], ["big", "Big improvement"], [null, "No goal"]];
const GOAL_TONE = { done: "var(--grn)", up: "var(--acc)", flat: "var(--mut)" };

const PlanDialog = ({ row, loans, close }) => {
  const act = useAct();
  const p = row.plan;
  const [f, setF] = useState({ minutes_target: p?.minutes_target ?? row.target ?? 270, loan: p?.loan || "none", goal_level: p?.goal_level ?? "steady", note: p?.note || "" });
  const { data: hist = [] } = useGet("plan-history", `/development/plans/${row.unique_id}/history`, { uid: row.unique_id });
  const save = async () => {
    const ok = await act(() => api.post("/development/plans", { unique_id: row.unique_id, ...f, goal_level: f.goal_level || null, minutes_target: Number(f.minutes_target), expected_revision: p?.revision || 0 }),
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
        <label className="lbl">Development goal (from today)</label>
        <div className="seg" style={{ flexWrap: "wrap" }} data-testid="plan-goal-choice">{GOAL_OPTS.map(([k, l]) => <button key={k || "none"} type="button" className={f.goal_level === k ? "on" : ""} onClick={() => setF({ ...f, goal_level: k })} data-testid={`plan-goal-${k || "none"}`}>{l}</button>)}</div>
        <small className="note">FMCC tracks it for you and tells you in plain words how he's getting on.</small>
        <label className="lbl">Note</label><input className="inp" value={f.note} maxLength={300} onChange={(e) => setF({ ...f, note: e.target.value })} data-testid="plan-note-input" />
        <button className="btn btn-p btn-l" onClick={save} data-testid="plan-save-button">Save plan</button>
        {hist.length > 0 && <div data-testid="plan-history">{hist.map((h) => <div className="row" key={h.revision}><span className="mono">v{h.revision}</span><div style={{ flex: 1 }}>{h.minutes_target} min · {loans[h.loan]} · goal {h.goal_label || "none"}<small>{ago(h.saved_at)}{h.note ? ` · ${h.note}` : ""}</small></div></div>)}</div>}
      </DialogContent>
    </Dialog>
  );
};

const Trend = ({ steps, id }) => {
  if (!steps?.length) return null;
  let y = 0;
  const pts = [0, ...steps.map((s) => (y += s === "up" ? 1 : s === "down" ? -1 : 0))];
  const lo = Math.min(...pts), hi = Math.max(...pts), span = Math.max(2, hi - lo);
  const xy = pts.map((v, i) => `${(i / (pts.length - 1)) * 56 + 2},${16 - ((v - lo) / span) * 12}`).join(" ");
  const last = pts[pts.length - 1] - pts[0];
  const col = last > 0 ? "var(--grn)" : last < 0 ? "var(--amb)" : "var(--mut)";
  const label = `${steps.filter((s) => s === "up").length} up, ${steps.filter((s) => s === "down").length} down, ${steps.filter((s) => s === "flat").length} steady over the last ${pts.length} saves`;
  return <svg width="60" height="20" viewBox="0 0 60 20" role="img" aria-label={label} data-testid={`dev-trend-${id}`}><title>{label}</title><polyline points={xy} fill="none" stroke={col} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" /></svg>;
};
const Games = ({ r }) => (
  <td className="n" data-testid={`dev-games-${r.unique_id}`}><span className="mono" style={{ color: "var(--text)" }}>{r.appearances}</span>
    {r.starts != null && <small style={{ display: "block", color: "var(--dim)" }}>{r.starts} started · {r.sub_apps} off the bench</small>}</td>
);
const TONE = { big: "var(--grn)", up: "var(--grn)", flat: "var(--mut)", down: "var(--amb)" };
const Progress = ({ n, small }) => (n ? <span style={{ color: TONE[n.tone], fontSize: small ? 12 : 13, display: "block" }}>{n.text}</span> : <span style={{ color: "var(--dim)", display: "block" }}>{small ? "" : "Needs two saves"}</span>);

const PROG = { big: 3, up: 2, flat: 1, down: 0 };
const SORTS = {
  player: (r) => r.name, age: (r) => r.age, games: (r) => r.appearances, mpg: (r) => r.minutes_per_game ?? -1, goals: (r) => r.goals, assists: (r) => r.assists,
  rating: (r) => r.avg_rating ?? -1, month: (r) => r.month_minutes, plan: (r) => (r.plan ? 1 : 0), goal: (r) => (r.goal_status ? { done: 3, up: 2, flat: 1 }[r.goal_status.tone] : 0),
  progress: (r) => (r.progress_month ? PROG[r.progress_month.tone] * 10 : -10) + (r.progress_season ? PROG[r.progress_season.tone] : 0),
};
const sortRows = (rows, s) => {
  if (!s?.col) return rows;
  const f = SORTS[s.col], m = s.dir === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => { const x = f(a), y = f(b); return (typeof x === "string" ? x.localeCompare(y) : x - y) * m; });
};

const Plans = () => {
  const { data } = useGet("development", "/development");
  const [edit, setEdit] = useState(null);
  const cw = useColWidths("development", COLS);
  const [sort, setSort] = usePersist("dev-sort", null);
  const sortBy = (col) => setSort((s) => (s?.col === col ? { col, dir: s.dir === "desc" ? "asc" : "desc" } : { col, dir: col === "player" ? "asc" : "desc" }));
  if (!data) return <Loading id="dev-loading" label="Loading plans" />;
  return (
    <div className="card" style={{ padding: 8, overflowX: "auto" }}>
      <div className="rz-bar"><small className="note">Click a heading to sort; click again to flip. Drag the edge of any heading to resize a column. Both are remembered.</small>
        <span style={{ display: "flex", gap: 8 }}>{sort && <button className="btn" onClick={() => setSort(null)} data-testid="plans-clear-sort">Default order</button>}
        {cw.changed && <button className="btn" onClick={cw.reset} data-testid="plans-reset-widths">Reset column widths</button>}</span></div>
      <table className="tbl dev-tbl rz-tbl" style={{ width: cw.total }} data-testid="plans-table">
        <ColGroup cols={Object.keys(COLS)} c={cw} />
        <thead><tr>{HEAD.map(([k, l, cls, t]) => <ResizeTh key={k} col={k} c={cw} label={l} className={cls} title={t} id="plans" sort={k === "act" ? null : { onClick: () => sortBy(k), dir: sort?.col === k ? sort.dir : null }} />)}</tr></thead>
        <tbody>{sortRows(data.rows, sort).map((r) => (
          <tr key={r.unique_id} style={{ cursor: "default" }} data-testid={`plan-row-${r.unique_id}`}>
            <td><b style={{ color: "var(--text)" }}>{r.name}</b>{r.needs_minutes && <span className="tag st a" data-testid={`needs-minutes-${r.unique_id}`}>Needs minutes</span>}</td>
            <td className="mono n">{r.age}</td><Games r={r} /><td className="mono n">{r.minutes_per_game ?? "—"}</td>
            <td className="mono n">{r.goals}</td><td className="mono n">{r.assists}</td><td className="mono n">{r.avg_rating ?? "—"}</td>
            <td style={{ minWidth: 180 }}>{r.target ? <div className="mb" style={{ gridTemplateColumns: "1fr 70px" }}><div className="track"><i style={{ width: `${Math.min(100, (r.month_minutes / r.target) * 100)}%`, background: r.needs_minutes ? "var(--amb)" : "var(--acc)" }} /></div><span className="mono">{r.month_minutes}/{r.target}</span></div> : <span className="mono">{r.month_minutes}</span>}</td>
            <td>{r.plan ? <>{data.loans[r.plan.loan]}<small style={{ display: "block", color: "var(--dim)" }}>version {r.plan.revision}</small></> : <span style={{ color: "var(--dim)" }}>No plan</span>}</td>
            <td>{r.plan?.goal_label ? <><span style={{ color: "var(--text)" }}>{r.plan.goal_label}</span>{r.goal_status && <small style={{ display: "block", color: GOAL_TONE[r.goal_status.tone] }} data-testid={`dev-goal-status-${r.unique_id}`}>{r.goal_status.text}</small>}</> : "—"}</td>
            <td data-testid={`dev-progress-${r.unique_id}`}><div className="dev-prog"><div><Progress n={r.progress_month} /><Progress n={r.progress_season} small /></div><Trend steps={r.trend} id={r.unique_id} /></div></td>
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
      <PageHead eyebrow="Minutes, loans and goals, tracked from every save" title="Youth Development">
        <TabBar id="development" value={tab} onChange={setTab} tabs={[["plans", "Plans"], ["rules", "Rules"]]} />
      </PageHead>
      {tab === "plans" ? <Plans /> : <RulesTab module="development" title="Youth Development rules" />}
    </div>
  );
}
