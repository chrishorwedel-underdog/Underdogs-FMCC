import { useState } from "react";
import { Star, Scale } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct, TabBar, PageHead, money } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";

const Flag = ({ f }) => (f ? <span className={`tag st ${f === "over" ? "ok" : "r"}`}>{f === "over" ? "Beats his rating" : "Below his rating"}</span> : null);

const Rankings = ({ shortlistOnly, compare, toggleCompare }) => {
  const [f, setF] = useState({ role: "", league: "", max_age: 40, q: "", sort: "score" });
  const { data: meta } = useGet("scout-meta", "/scouting/meta");
  const { data } = useGet("rankings", "/scouting/rankings", { ...f, role: f.role || undefined, league: f.league || undefined, shortlist_only: shortlistOnly });
  const act = useAct();
  const star = (r) => act(() => api.post("/scouting/shortlist", { unique_id: r.unique_id, action: r.shortlisted ? "remove" : "add" }), r.shortlisted ? "Removed from shortlist" : "Added to shortlist", ["rankings"]);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 14 }}>
        <select className="inp" style={{ width: 260 }} value={f.role} onChange={set("role")} data-testid="scout-role-select"><option value="">Any role (best role)</option>{meta?.roles.map((r) => <option key={r.key} value={r.key}>{r.name}</option>)}</select>
        <select className="inp" style={{ width: 180 }} value={f.league} onChange={set("league")} data-testid="scout-league-select"><option value="">All leagues</option>{meta?.leagues.map((l) => <option key={l}>{l}</option>)}</select>
        <input className="inp" style={{ width: 110 }} type="number" value={f.max_age} onChange={set("max_age")} title="Max age" data-testid="scout-max-age" />
        <input className="inp" style={{ width: 220 }} placeholder="Name or club" value={f.q} onChange={set("q")} data-testid="scout-search" />
        <select className="inp" style={{ width: 180 }} value={f.sort} onChange={set("sort")} data-testid="scout-sort"><option value="score">Sort: overall score</option><option value="vfm">Sort: value for money</option><option value="fit">Sort: role fit</option><option value="pa">Sort: potential</option></select>
      </div>
      <div className="card" style={{ padding: 8, overflowX: "auto" }}>
        <table className="tbl" data-testid="rankings-table">
          <thead><tr><th></th><th>Player</th><th>Age</th><th>Club</th><th>Best role</th><th>Fit</th><th>CA/PA</th><th>Value</th><th>Rating</th><th>Score</th><th>Value for money</th><th></th></tr></thead>
          <tbody>{data?.rows.map((r) => (
            <tr key={r.unique_id} style={{ cursor: "default" }} data-testid={`ranking-row-${r.unique_id}`}>
              <td><button className="ib" style={{ width: 28, height: 28, color: r.shortlisted ? "var(--amb)" : undefined }} onClick={() => star(r)} data-testid={`shortlist-toggle-${r.unique_id}`}><Star size={14} fill={r.shortlisted ? "currentColor" : "none"} /></button></td>
              <td><b style={{ color: "var(--text)" }}>{r.name}</b><Flag f={r.flag} />{r.seen_vs_us > 0 && <span className="tag st b" title={`Match rating ${r.match_rating} vs us · xG/90 ${r.per90?.xg} · pressures/90 ${r.per90?.pressures}`} data-testid={`seen-vs-us-${r.unique_id}`}>Seen vs us</span>}<small style={{ display: "block", color: "var(--dim)" }}>{r.nationality} · {r.positions.join(", ")}</small></td>
              <td>{r.age}</td><td>{r.club}<small style={{ display: "block", color: "var(--dim)" }}>{r.league}</small></td><td>{r.best_role}</td>
              <td className="mono">{r.fit}</td><td className="mono">{r.ca}/{r.pa}</td><td className="mono">{money(r.value)}</td><td className="mono">{r.avg_rating ?? "—"}</td>
              <td className="mono" style={{ color: "var(--acc)" }}>{r.score}</td><td className="mono">{r.vfm}</td>
              <td><button className={`btn${compare.includes(r.unique_id) ? " btn-p" : ""}`} onClick={() => toggleCompare(r.unique_id)} data-testid={`compare-toggle-${r.unique_id}`}><Scale size={13} /></button></td>
            </tr>))}</tbody>
        </table>
        {data && <p className="note" style={{ padding: 10 }} data-testid="rankings-total">{data.total} players match. Showing the top {Math.min(80, data.total)}.</p>}
      </div>
    </div>
  );
};

const Compare = ({ ids, clear }) => {
  const { data = [] } = useGet("compare", "/scouting/compare", { ids: ids.join(",") }, { enabled: ids.length > 0 });
  if (!ids.length) return <div className="soon">Pick up to 4 players with the scales button in Rankings or Shortlist to compare them here.</div>;
  const keys = data[0] ? Object.keys(data[0].attributes) : [];
  return (
    <div className="card" style={{ overflowX: "auto" }} data-testid="moneyball-compare">
      <div className="ttl">Moneyball comparison<span style={{ marginLeft: "auto" }} /><button className="btn" onClick={clear} data-testid="compare-clear">Clear</button></div>
      <table className="tbl" style={{ marginTop: 10 }}>
        <thead><tr><th></th>{data.map((p) => <th key={p.unique_id}>{p.name}</th>)}</tr></thead>
        <tbody>
          {[["Club", (p) => p.club], ["Age", (p) => p.age], ["Value", (p) => money(p.value)], ["CA / PA", (p) => `${p.ca}/${p.pa}`], ["Average rating", (p) => p.avg_rating ?? "—"],
            ["Best roles", (p) => p.roles.map((r) => `${r.name} ${r.rating}`).join(" · ")], ["Value for money", (p) => p.vfm], ["Performance", (p) => (p.flag === "over" ? "Beats his rating" : p.flag === "under" ? "Below his rating" : "As expected")],
            ...keys.map((k) => [k.replace(/_/g, " "), (p) => p.attributes[k]])].map(([l, fn]) => (
            <tr key={l} style={{ cursor: "default" }}><td style={{ color: "var(--mut)", textTransform: "capitalize" }}>{l}</td>{data.map((p) => <td key={p.unique_id} className="mono">{fn(p)}</td>)}</tr>))}
        </tbody>
      </table>
    </div>
  );
};

export default function Scouting() {
  const [tab, setTab] = useState("rankings");
  const [compare, setCompare] = useState([]);
  const toggle = (id) => setCompare((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id].slice(-4)));
  return (
    <div data-testid="scouting-page">
      <PageHead eyebrow="Every player in the save, ranked by your rules" title="Scouting">
        <TabBar id="scouting" value={tab} onChange={setTab} tabs={[["rankings", "Rankings"], ["shortlist", "Shortlist"], ["compare", `Moneyball${compare.length ? ` (${compare.length})` : ""}`], ["rules", "Rules"]]} />
      </PageHead>
      {tab === "rankings" && <Rankings compare={compare} toggleCompare={toggle} />}
      {tab === "shortlist" && <Rankings shortlistOnly compare={compare} toggleCompare={toggle} />}
      {tab === "compare" && <Compare ids={compare} clear={() => setCompare([])} />}
      {tab === "rules" && <RulesTab module="scouting" title="Scouting and Moneyball rules" />}
    </div>
  );
}
