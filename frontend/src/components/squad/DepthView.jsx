import { useGet } from "@/lib/ui";

export const DepthView = ({ formation }) => {
  const { data: plan } = useGet("plan", "/squad/plan", { formation });
  if (!plan) return <p className="note">Loading depth chart…</p>;
  return (
    <div className="homegrid">
      <div className="bento" data-testid="depth-chart">
        {plan.formation.slots.map((s) => (
          <div className="card" key={s.key} data-testid={`depth-slot-${s.key}`}>
            <div className="ch">{s.label}<span className="st n">{s.pos}</span></div>
            <p className="note" style={{ marginTop: 4 }}>{s.role_name}</p>
            <div className="mbars">
              {plan.depth[s.key].slice(0, 4).map((r, i) => (
                <div className="mb" key={r.unique_id} style={{ gridTemplateColumns: "110px 1fr 30px" }}>
                  <span style={{ color: i === 0 ? "var(--text)" : undefined }}>{i + 1}. {plan.players[r.unique_id].name}</span>
                  <div className="track"><i style={{ width: `${r.rating}%`, background: i === 0 ? "var(--acc)" : "var(--mut)" }} /></div><span className="mono">{r.rating}</span>
                </div>
              ))}
              {plan.depth[s.key].length === 0 && <span className="note">Nobody plays here naturally.</span>}
            </div>
          </div>
        ))}
      </div>
      <div className="card" data-testid="weak-positions">
        <div className="ttl">Weakest positions</div>
        {plan.weak.slice(0, 6).map((w) => (
          <div className="row" key={w.slot}><div style={{ flex: 1 }}>{w.label}<small>{w.options} natural {w.options === 1 ? "option" : "options"}</small></div>
            <span className={`st ${w.best < plan.best.strength - 5 ? "a" : "n"}`}>{w.best}</span></div>
        ))}
        <p className="note" style={{ marginTop: 8 }}>Ratings are role ratings (0–100) for the role in this shape.</p>
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
