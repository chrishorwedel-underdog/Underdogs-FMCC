import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { useGet, PageHead } from "@/lib/ui";
import { money, openDossier } from "@/components/analysis/StatsTable";

const Idea = ({ title, rows, id }) => (
  <div className="card" data-testid={`ca-ideas-${id}`}><div className="ttl">{title}</div>
    {!rows?.length && <p className="note">Nobody fits yet.</p>}
    {rows?.map((r) => <div key={r.unique_id} className="row" style={{ cursor: "pointer" }} onClick={() => openDossier(r.unique_id)} data-testid={`ca-idea-${id}-${r.unique_id}`}>
      <div style={{ flex: 1 }}><b>{r.name}</b><small>{r.club} · {r.age} · {r.why}</small></div><span className="mono">{money(r.est_value)}</span><small className="note" style={{ marginLeft: 8 }}>{money(r.wage)}/wk</small></div>)}
  </div>
);

export default function ClubAnalysis() {
  const { data } = useGet("analysis-club", "/analysis/club");
  const nav = useNavigate();
  if (!data) return <p className="note">Looking at your squad…</p>;
  return (
    <div data-testid="club-analysis-page" style={{ display: "grid", gap: 16 }}>
      <PageHead eyebrow={data.club} title="Club Analysis" />
      <div className="card" data-testid="ca-todo"><div className="ttl">What to do first</div>
        {data.todo.map((t, i) => <div key={t.title} className="row" data-testid={`ca-todo-${i}`}><span className="mono" style={{ width: 22 }}>{i + 1}</span><div style={{ flex: 1 }}><b>{t.title}</b><small>{t.evidence}</small></div>
          <button className="btn" onClick={() => nav(t.link)} data-testid={`ca-todo-link-${i}`}>Look<ArrowRight size={13} /></button></div>)}
        {!data.todo.length && <p className="note">Nothing urgent. Your squad looks balanced.</p>}</div>
      <div className="card" data-testid="ca-positions"><div className="ttl">Where to strengthen</div>
        <div style={{ overflowX: "auto" }}><table className="tbl"><thead><tr><th>Area</th><th>Players</th><th>Best fit</th><th>Top two average</th><th>Average age</th></tr></thead>
          <tbody>{[...data.positions].sort((a, b) => a.avg_top2 - b.avg_top2).map((p) => <tr key={p.group} style={{ cursor: "default" }}><td><b>{p.label}</b></td><td>{p.count}</td><td className="mono">{p.best}%</td><td className="mono">{p.avg_top2}%</td><td>{p.avg_age ?? "—"}</td></tr>)}</tbody></table></div></div>
      {data.ideas.position && <><p className="note" style={{ margin: 0 }}>Signing ideas for your weakest area: <b>{data.ideas.position}</b></p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(min(320px,100%),1fr))", gap: 14 }}>
          <Idea title="Upgrade" rows={data.ideas.upgrade} id="upgrade" /><Idea title="Affordable" rows={data.ideas.affordable} id="affordable" /><Idea title="Successor (21 and under)" rows={data.ideas.successor} id="successor" /></div></>}
    </div>
  );
}
