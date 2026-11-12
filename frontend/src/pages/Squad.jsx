import { usePersist, returnToRow } from "@/lib/remember";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { api, gameDate } from "@/lib/api";
import { TacticFit } from "@/components/squad/TacticFit";
import { TabBar, PageHead } from "@/lib/ui";
import { LineupView } from "@/components/squad/LineupView";
import { TryXI } from "@/components/squad/TryXI";
import { DepthView, RegistrationView } from "@/components/squad/DepthView";
import { RulesTab } from "@/components/rules/RulesTab";
import { LoanManager } from "@/components/squad/LoanManager";
import { useResizableTable, ResetWidths } from "@/components/ResizableCols";

const FILTERS = [["all", "All"], ["xi", "Best XI"], ["u21", "Under-21"]];

const Change = ({ v }) => (v == null ? <span style={{ color: "var(--dim)" }}>—</span> : <span className={`mono ${v > 0 ? "up" : v < 0 ? "down" : ""}`}>{v > 0 ? "+" : ""}{v}</span>);

const Row = ({ p, onOpen }) => (
  <tr onClick={() => onOpen(p.unique_id)} onKeyDown={(e) => { if (e.key === "Enter" && e.target === e.currentTarget) { e.preventDefault(); onOpen(p.unique_id); } }} tabIndex={0} data-row-uid={p.unique_id} data-testid={`squad-row-${p.unique_id}`}>
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

const VIEWS = [["lineup", "Lineup"], ["depth", "Depth chart"], ["fit", "Tactic fit"], ["players", "Players"], ["loans", "Loan Manager"], ["registration", "Registration"], ["rules", "Rules"]];

export default function Squad() {
  const [params, setParams] = useSearchParams();
  const [formation, setFormation] = usePersist("squad-formation", null);
  const [lastView, setLastView] = usePersist("squad-view", "lineup");
  const filter = params.get("filter") || "all";
  const view = params.get("view") || (params.get("filter") ? "players" : lastView);
  const openId = params.get("player");
  const { data } = useQuery({ queryKey: ["squad"], queryFn: () => api.get("/squad").then((r) => r.data) });
  const setParam = (k, v) => { if (k === "view" && v) { setLastView(v); } if (k === "player" && !v && openId) { returnToRow(openId); } const n = new URLSearchParams(params); v ? n.set(k, v) : n.delete(k); setParams(n); };
  const rz = useResizableTable("squad");
  const rows = (data?.players || []).filter((p) => filter === "all" || (filter === "u21" ? p.age < 21 : p.in_best_xi)).sort((a, b) => (b.best_role?.rating || 0) - (a.best_role?.rating || 0));
  return (
    <div data-testid="squad-page">
      <PageHead eyebrow={`Read from your save · ${gameDate(data?.game_date)}`} title="Squad" />
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginBottom: 18 }}>
        <TabBar id="squad-view" value={view} onChange={(v) => setParam("view", v)} tabs={VIEWS} />
        {view === "players" && <div className="seg">{FILTERS.map(([k, l]) => <button key={k} className={filter === k ? "on" : ""} onClick={() => setParam("filter", k === "all" ? null : k)} data-testid={`squad-filter-${k}`}>{l}</button>)}</div>}
      </div>
      {view === "lineup" && <LineupView formation={formation} setFormation={setFormation} />}
      {view === "lineup" && <TryXI formation={formation} />}
      {view === "depth" && <DepthView formation={formation} />}
      {view === "fit" && <TacticFit />}
      {view === "loans" && <LoanManager squad={data?.players || []} />}
      {view === "registration" && <RegistrationView />}
      {view === "rules" && <RulesTab module="squad" title="Development XI and registration rules" />}
      {view === "players" && <>
      <div className="card rise d1" style={{ padding: 8, overflowX: "auto" }}>
        <ResetWidths rz={rz} id="squad" />
        <table className="tbl" ref={rz.ref} data-testid="squad-table">
          <thead><tr><th>Player</th><th>Age</th><th>Positions</th><th>Ability gained since last save</th><th>Best role</th><th>Minutes</th><th>Contract</th></tr></thead>
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
    </div>
  );
}
