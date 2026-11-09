import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { api, gameDate } from "@/lib/api";
import { TacticFit } from "@/components/TacticApps";
import { PlayerSheet } from "@/components/PlayerSheet";
import { TabBar } from "@/lib/ui";
import { LineupView } from "@/components/squad/LineupView";
import { DepthView, RegistrationView } from "@/components/squad/DepthView";
import { RulesTab } from "@/components/rules/RulesTab";

const FILTERS = [["all", "All"], ["xi", "Best XI"], ["u21", "Under-21"]];

const Change = ({ v }) => (v == null ? <span style={{ color: "var(--dim)" }}>—</span> : <span className={`mono ${v > 0 ? "up" : v < 0 ? "down" : ""}`}>{v > 0 ? "+" : ""}{v}</span>);

const Row = ({ p, onOpen }) => (
  <tr onClick={() => onOpen(p.unique_id)} data-testid={`squad-row-${p.unique_id}`}>
    <td><b style={{ color: "var(--text)", fontWeight: 600 }}>{p.name}</b>
      {p.age < 21 && <span className="tag st g">U21</span>}
      {p.is_new && <span className="tag st ok">New</span>}
      {p.shared_name && <span className="tag st a" title="Another player in your squad has the same name. They are kept apart by game ID.">Same name</span>}
    </td>
    <td>{p.age}</td><td>{p.positions.join(", ")}</td>
    <td><Change v={p.ca_change} /></td>
    <td>{p.best_role?.name}<span className="mono" style={{ color: "var(--acc)", marginLeft: 6 }}>{p.best_role?.rating}</span></td>
    <td className="mono">{p.minutes}</td><td>{gameDate(p.contract_end, { month: "short", year: "numeric" })}</td>
  </tr>
);

const VIEWS = [["lineup", "Lineup"], ["depth", "Depth chart"], ["fit", "Tactic fit"], ["players", "Players"], ["registration", "Registration"], ["rules", "Rules"]];

export default function Squad() {
  const [params, setParams] = useSearchParams();
  const [formation, setFormation] = useState("433");
  const filter = params.get("filter") || "all";
  const view = params.get("view") || (params.get("filter") ? "players" : "lineup");
  const openId = params.get("player");
  const { data } = useQuery({ queryKey: ["squad"], queryFn: () => api.get("/squad").then((r) => r.data) });
  const setParam = (k, v) => { const n = new URLSearchParams(params); v ? n.set(k, v) : n.delete(k); setParams(n); };
  const rows = (data?.players || []).filter((p) => filter === "all" || (filter === "u21" ? p.age < 21 : p.in_best_xi)).sort((a, b) => (b.best_role?.rating || 0) - (a.best_role?.rating || 0));
  return (
    <div data-testid="squad-page">
      <div className="head rise">
        <div><div className="eyebrow">Read from your save · {gameDate(data?.game_date)}</div><h1 className="h">Squad</h1></div>
        <TabBar id="squad-view" value={view} onChange={(v) => setParam("view", v)} tabs={VIEWS} />
        {view === "players" && <div className="seg">{FILTERS.map(([k, l]) => <button key={k} className={filter === k ? "on" : ""} onClick={() => setParam("filter", k === "all" ? null : k)} data-testid={`squad-filter-${k}`}>{l}</button>)}</div>}
      </div>
      {view === "lineup" && <LineupView formation={formation} setFormation={setFormation} />}
      {view === "depth" && <DepthView formation={formation} />}
      {view === "fit" && <TacticFit />}
      {view === "registration" && <RegistrationView />}
      {view === "rules" && <RulesTab module="squad" title="Development XI and registration rules" />}
      {view === "players" && <>
      <div className="card rise d1" style={{ padding: 8, overflowX: "auto" }}>
        <table className="tbl" data-testid="squad-table">
          <thead><tr><th>Player</th><th>Age</th><th>Positions</th><th>CA gained since last save</th><th>Best role</th><th>Minutes</th><th>Contract</th></tr></thead>
          <tbody>{rows.map((p) => <Row key={p.unique_id} p={p} onOpen={(id) => setParam("player", id)} />)}</tbody>
        </table>
      </div>
      {data?.departed?.length > 0 && (
        <div className="card rise d2" style={{ marginTop: 16 }} data-testid="squad-departed">
          <div className="ttl">No longer in your squad</div>
          {data.departed.map((d) => <div className="row" key={d.unique_id}><span style={{ flex: 1 }}>{d.name}</span><small>Last seen {gameDate(d.last_seen_date)}</small></div>)}
        </div>
      )}
      </>}
      <PlayerSheet uid={openId ? Number(openId) : null} onClose={() => setParam("player", null)} />
    </div>
  );
}
