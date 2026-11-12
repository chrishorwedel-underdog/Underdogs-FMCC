import { GripVertical } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const Slot = ({ s, plan, formation }) => {
  const act = useAct();
  const rows = plan.depth[s.key];
  const move = (from, to) => {
    if (from === to) return;
    const order = rows.map((r) => r.unique_id);
    const [x] = order.splice(from, 1);
    order.splice(to, 0, x);
    act(() => api.put("/squad/depth", { formation: formation || plan.formation.key, slot: s.key, order }), "Depth chart updated", ["plan"]);
  };
  return (
    <div className="card" data-testid={`depth-slot-${s.key}`}>
      <div className="ch">{s.label}<span className="st n">{s.pos}</span>{plan.depth_custom?.includes(s.key) && <span className="st g">Your order</span>}</div>
      <p className="note" style={{ marginTop: 4 }}>{s.role_name}</p>
      <div className="mbars">
        {rows.slice(0, 6).map((r, i) => (
          <div className="mb" key={r.unique_id} style={{ gridTemplateColumns: "14px 110px 1fr 30px", cursor: "grab" }} draggable data-testid={`depth-row-${s.key}-${i}`}
            onDragStart={(e) => e.dataTransfer.setData("text/fmcc-depth", `${s.key}:${i}`)} onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { const [k, from] = e.dataTransfer.getData("text/fmcc-depth").split(":"); if (k === s.key) move(Number(from), i); }}>
            <GripVertical size={12} style={{ color: "var(--dim)" }} />
            <span style={{ color: i === 0 ? "var(--text)" : undefined }}>{i + 1}. {plan.players[r.unique_id].name} ({plan.players[r.unique_id].age})</span>
            <div className="track"><i style={{ width: `${r.rating}%`, background: i === 0 ? "var(--acc)" : "var(--mut)" }} /></div><span className="mono">{r.rating}</span>
          </div>
        ))}
        {rows.length === 0 && <span className="note">Nobody plays here naturally.</span>}
      </div>
    </div>
  );
};

export const DepthView = ({ formation }) => {
  const { data: plan } = useGet("plan", "/squad/plan", { formation });
  if (!plan) return <p className="note">Loading depth chart…</p>;
  return (
    <div className="homegrid">
      <div className="bento" data-testid="depth-chart">
        {plan.formation.slots.map((s) => <Slot key={s.key} s={s} plan={plan} formation={formation} />)}
      </div>
      <div className="card" data-testid="weak-positions">
        <div className="ttl">Weakest positions</div>
        {plan.weak.slice(0, 6).map((w) => (
          <div className="row" key={w.slot}><div style={{ flex: 1 }}>{w.label}<small>{w.options} natural {w.options === 1 ? "option" : "options"}</small></div>
            <span className={`st ${w.best < plan.best.strength - 5 ? "a" : "n"}`}>{w.best}</span></div>
        ))}
        <p className="note" style={{ marginTop: 8 }}>Ratings are role ratings (0–100) for the role in this shape. Drag players within a position to set your own order; FMCC keeps it for this tactic.</p>
      </div>
    </div>
  );
};

export const RegistrationView = () => {
  const { data } = useGet("registration", "/squad/registration");
  if (!data) return <p className="note">Checking registration…</p>;
  return (
    <div className="sgrid" data-testid="registration-view">
      <div className="card"><div className="ttl">Squad registration<span className="st n" style={{ marginLeft: "auto" }}>{data.preset}</span></div>
        {data.checks.map((c) => (
          <div className="row" key={c.key} data-testid={`registration-${c.key}`}>
            <div style={{ flex: 1 }}><b>{c.label}</b><small>{c.detail}</small></div>
            <span className="mono">{c.value}</span><span className={`st ${c.ok ? "ok" : "r"}`}>{c.ok ? "OK" : "Breach"} · {c.limit}</span>
          </div>
        ))}
      </div>
      <div className="card"><div className="ttl">Suggestions</div>
        {data.suggestions.length === 0 && <p className="note" style={{ marginTop: 10 }}>Nothing to change.</p>}
        <ul className="why">{data.suggestions.map((s, i) => <li key={i} data-testid={`registration-suggestion-${i}`}><i style={{ background: "var(--amb)" }} />{s}</li>)}</ul>
      </div>
    </div>
  );
};
