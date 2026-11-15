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

const TONE = { big: "var(--grn)", up: "var(--grn)", flat: "var(--mut)", down: "var(--amb)" };
const Change = ({ v }) => (v == null ? <span style={{ color: "var(--dim)" }}>—</span> : <span style={{ color: TONE[v.tone] }}>{v.text}</span>);

const Row = ({ p, onOpen }) => (
  <tr onClick={() => onOpen(p.unique_id)} onKeyDown={(e) => { if (e.key === "Enter" && e.target === e.currentTarget) { e.preventDefault(); onOpen(p.unique_id); } }} tabIndex={0} data-row-uid={p.unique_id} data-testid={`squad-row-${p.unique_id}`}>
    <td><b style={{ color: "var(--text)", fontWeight: 600 }}>{p.name}</b>
      {p.age < 21 && <span className="tag st g">U21</span>}
      {p.is_new && <span className="tag st ok">New</span>}
      {p.shared_name && <span className="tag st a" title="Another player in your squad has the same name. They are kept apart by game ID.">Same name</span>}
    </td>
    <td className="mono n">{p.age}</td><td>{p.positions.join(", ")}</td>
    <td><Change v={p.progress} /></td>
    <td>{p.best_role?.name}<span className="mono" style={{ color: "var(--acc)", marginLeft: 6 }}>{p.best_role?.rating}</span></td>
    <td className="mono n">{p.minutes}</td><td>{gameDate(p.contract_end, { month: "short", year: "numeric" })}</td>
  </tr>
);

const POS = { Goalkeepers: ["GK"], Defenders: ["D (", "WB"], Midfielders: ["DM", "M (", "AM"], Forwards: ["ST"] };
const matches = (sf) => (p) => (!sf.q || p.name.toLowerCase().includes(sf.q.toLowerCase()))
  && (!sf.pos || p.positions.some((x) => POS[sf.pos].some((k) => x.startsWith(k))))
  && (!sf.age || (sf.age === "u21" ? p.age < 21 : sf.age === "30" ? p.age >= 30 : p.age >= 21 && p.age < 30));

const Card = ({ p, onOpen }) => (
  <button className="sq-card" onClick={() => onOpen(p.unique_id)} data-row-uid={p.unique_id} data-testid={`squad-card-${p.unique_id}`}>
    <b>{p.name}{p.age < 21 && <span className="tag st g">U21</span>}{p.is_new && <span className="tag st ok">New</span>}{p.shared_name && <span className="tag st a" title="Another player in your squad has the same name. They are kept apart by game ID.">Same name</span>}</b>
    <small>{p.age} · {p.positions.join(", ")}</small>
    <span>{p.best_role?.name} <span className="mono" style={{ color: "var(--acc)" }}>{p.best_role?.rating}</span></span>
    <Change v={p.progress} />
    <small>{p.minutes} minutes · contract to {gameDate(p.contract_end, { month: "short", year: "numeric" })}</small>
  </button>
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
  const [sf, setSf] = usePersist("squad-card-filters", { q: "", pos: "", age: "" });
  const [layout, setLayout] = usePersist("squad-layout", "table");
  const [sort, setSort] = usePersist("squad-sort", null);
  const SQ = { Player: (p) => p.name, Age: (p) => p.age, Positions: (p) => p.positions.join(","), "Progress since last save": (p) => ({ big: 3, up: 2, flat: 1, down: 0 }[p.progress?.tone] ?? -1), "Best role": (p) => p.best_role?.rating || 0, Minutes: (p) => p.minutes, Contract: (p) => p.contract_end || "" };
  const sortBy = (k) => setSort((s) => (s?.k === k ? { k, dir: s.dir === "desc" ? "asc" : "desc" } : { k, dir: ["Player", "Positions", "Contract"].includes(k) ? "asc" : "desc" }));
  const H = ({ k, n }) => <th className={`sortable${n ? " n" : ""}`} onClick={() => sortBy(k)} aria-sort={sort?.k === k ? (sort.dir === "asc" ? "ascending" : "descending") : undefined} data-testid={`squad-head-${k.split(" ")[0].toLowerCase()}`}>{k}{sort?.k === k && <span className="sort-ar">{sort.dir === "asc" ? " ▲" : " ▼"}</span>}</th>;
  const base = (data?.players || []).filter((p) => filter === "all" || (filter === "u21" ? p.age < 21 : p.in_best_xi)).filter(matches(sf)).sort((a, b) => (b.best_role?.rating || 0) - (a.best_role?.rating || 0));
  const rows = !sort ? base : [...base].sort((a, b) => { const x = SQ[sort.k](a), y = SQ[sort.k](b); return (typeof x === "string" ? x.localeCompare(y) : x - y) * (sort.dir === "asc" ? 1 : -1); });
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
      <div className="sq-filters" style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", marginBottom: 12 }} data-testid="squad-filters">
        <input className="inp" style={{ width: 200 }} placeholder="Search by name" value={sf.q} onChange={(e) => setSf({ ...sf, q: e.target.value })} data-testid="squad-search" />
        <select className="inp" style={{ width: "auto" }} value={sf.pos} onChange={(e) => setSf({ ...sf, pos: e.target.value })} data-testid="squad-pos"><option value="">Any position</option>{Object.keys(POS).map((k) => <option key={k}>{k}</option>)}</select>
        <select className="inp" style={{ width: "auto" }} value={sf.age} onChange={(e) => setSf({ ...sf, age: e.target.value })} data-testid="squad-age"><option value="">Any age</option><option value="u21">Under 21</option><option value="21-29">21 to 29</option><option value="30">30 and over</option></select>
        <span className="note">{rows.length} player{rows.length === 1 ? "" : "s"}</span>
        <div className="seg" style={{ marginLeft: "auto" }}>{[["table", "Table"], ["cards", "Cards"]].map(([k, l]) => <button key={k} className={layout === k ? "on" : ""} onClick={() => setLayout(k)} data-testid={`squad-layout-${k}`}>{l}</button>)}</div>
      </div>
      {!rows.length && (sf.q || sf.pos || sf.age) && <div className="card" style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }} data-testid="squad-no-match"><span className="note">No players match these filters.</span><button className="btn" onClick={() => setSf({ q: "", pos: "", age: "" })} data-testid="squad-clear-filters">Clear filters</button></div>}
      {layout === "cards" ? <div className="sq-cards rise d1" data-testid="squad-cards">{rows.map((p) => <Card key={p.unique_id} p={p} onOpen={(id) => setParam("player", id)} />)}</div> :
      <div className="card rise d1 tbl-scroll" style={{ padding: 8, overflowX: "auto" }}>
        {sort && <button className="btn rz-reset" onClick={() => setSort(null)} data-testid="squad-clear-sort">Default order</button>}
        <ResetWidths rz={rz} id="squad" />
        <table className="tbl" ref={rz.ref} data-testid="squad-table">
          <thead><tr><H k="Player" /><H k="Age" n /><H k="Positions" /><H k="Progress since last save" /><H k="Best role" /><H k="Minutes" n /><H k="Contract" /></tr></thead>
          <tbody>{rows.map((p) => <Row key={p.unique_id} p={p} onOpen={(id) => setParam("player", id)} />)}</tbody>
        </table>
      </div>}
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
