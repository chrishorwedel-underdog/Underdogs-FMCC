import { useState } from "react";
import { useGet, PageHead, TabBar } from "@/lib/ui";
import { Loading } from "@/components/Loading";
import { money, openDossier } from "@/components/analysis/StatsTable";

const LISTS = [["expiring", "Contracts ending within a year"], ["free", "Free agents"], ["clauses", "Lowest release clauses"], ["u21", "Best under-21s"], ["loans", "Loan-listed"]];

const Rows = ({ rows, extra }) => (
  <div style={{ overflowX: "auto" }}><table className="tbl"><thead><tr><th>#</th><th>Player</th><th>Club</th><th>Age</th><th>Best role</th><th>Est. value</th><th>Contract ends</th>{extra && <th>{extra[0]}</th>}</tr></thead>
    <tbody>{rows.map((r, i) => <tr key={r.unique_id} onClick={() => openDossier(r.unique_id)} data-testid={`tm-row-${r.unique_id}`}><td className="mono">{i + 1}</td><td><b>{r.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{(r.positions || []).join(", ")}</small></td>
      <td>{r.club || "Free agent"}<small style={{ display: "block", color: "var(--dim)" }}>{r.league}</small></td><td>{r.age}</td><td>{r.top_roles?.[0]?.name} {r.role_fit}%</td><td className="mono">{money(r.est_value)}</td><td>{r.contract_end || "—"}</td>{extra && <td className="mono">{extra[1](r)}</td>}</tr>)}</tbody></table></div>
);

const Rankings = ({ rows }) => {
  const [by, setBy] = useState({ league: "", club: "", nationality: "", group: "", age: "", gender: "M" });
  const opts = (k) => [...new Set(rows.filter((r) => k !== "club" || !by.league || r.league === by.league).map((r) => r[k]).filter(Boolean))].sort();
  const shown = rows.filter((r) => (!by.gender || r.gender === by.gender) && ["league", "club", "nationality", "group"].every((k) => !by[k] || r[k] === by[k]) && (!by.age || (by.age === "u21" ? r.age <= 21 : by.age === "u25" ? r.age <= 25 : r.age >= 30)));
  const sum = shown.reduce((a, r) => a + r.est_value, 0);
  return (
    <div style={{ display: "grid", gap: 10 }} data-testid="tm-rankings">
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {[["league", "Any league"], ["club", "Any club"], ["nationality", "Any country"], ["group", "Any position"]].map(([k, l]) => <select key={k} className="inp" style={{ width: 170, height: 32 }} value={by[k]} onChange={(e) => setBy({ ...by, [k]: e.target.value })} data-testid={`tm-rank-${k}`}><option value="">{l}</option>{opts(k).map((x) => <option key={x}>{x}</option>)}</select>)}
        <select className="inp" style={{ width: 130, height: 32 }} value={by.age} onChange={(e) => setBy({ ...by, age: e.target.value })} data-testid="tm-rank-age"><option value="">Any age</option><option value="u21">Under 21</option><option value="u25">Under 25</option><option value="o30">30 and over</option></select>
        <select className="inp" style={{ width: 110, height: 32 }} value={by.gender} onChange={(e) => setBy({ ...by, gender: e.target.value })} data-testid="tm-rank-gender"><option value="M">Men</option><option value="F">Women</option><option value="">Both</option></select>
      </div>
      <p className="note" data-testid="tm-rank-summary">{shown.length} players · total {money(sum)} · average age {shown.length ? (shown.reduce((a, r) => a + r.age, 0) / shown.length).toFixed(1) : "—"}{by.club ? ` · ${shown.filter((r) => r.nationality !== shown[0]?.nationality).length} not from the main nation` : ""}</p>
      <Rows rows={shown.slice(0, 100)} />
    </div>
  );
};

export default function TransferMarket() {
  const { data } = useGet("analysis-market", "/analysis/market");
  const [tab, setTab] = useState("lists");
  const [list, setList] = useState("expiring");
  const [scope, setScope] = useState("world");
  if (!data) return <Loading id="market-loading" label="Loading the market" />;
  const changes = data.changes.filter((c) => scope === "world" || c.league === data.my_league);
  return (
    <div data-testid="transfer-market-page">
      <PageHead eyebrow="Who's available and what's moving" title="Transfer Market" />
      {data.sample && <p className="note">SAMPLE save in this preview. Values are FMCC's own estimates.</p>}
      <div style={{ marginBottom: 14 }}><TabBar id="tm" value={tab} onChange={setTab} tabs={[["lists", "Ready-made lists"], ["changes", "Since your last save"], ["rankings", "Rankings"]]} /></div>
      {tab === "lists" && <div style={{ display: "grid", gap: 10 }}>
        <div className="seg" style={{ justifySelf: "start", flexWrap: "wrap" }}>{LISTS.map(([k, l]) => <button key={k} className={list === k ? "on" : ""} onClick={() => setList(k)} data-testid={`tm-list-${k}`}>{l} ({data.lists[k].length})</button>)}</div>
        {data.notes[list] && <p className="note" data-testid="tm-list-note">{data.notes[list]}.</p>}
        <Rows rows={data.lists[list]} extra={list === "clauses" ? ["Release clause", (r) => money(r.release_clause)] : null} /></div>}
      {tab === "changes" && <div className="card" data-testid="tm-changes">
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}><b>Changes since {data.since || "your last save"}</b>
          <div className="seg" style={{ marginLeft: "auto" }}>{[["world", "World"], ["league", "My league"]].map(([k, l]) => <button key={k} className={scope === k ? "on" : ""} onClick={() => setScope(k)} data-testid={`tm-changes-${k}`}>{l}</button>)}</div></div>
        {!changes.length && <p className="note">Nothing yet; this fills in after FMCC reads two saves.</p>}
        {changes.map((c) => <div key={`${c.unique_id}-${c.kind}`} className="row" style={{ cursor: "pointer" }} onClick={() => openDossier(c.unique_id)}><div style={{ flex: 1 }}><b>{c.name}</b><small>{c.league}</small></div><span className={`st ${c.kind === "move" ? "b" : "n"}`}>{c.text}</span></div>)}
      </div>}
      {tab === "rankings" && <Rankings rows={data.rankings} />}
    </div>
  );
}
