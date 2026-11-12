import { useEffect } from "react";
import { usePersist } from "@/lib/remember";
import { Star, Scale, ListPlus, Eye } from "lucide-react";
import { sendToFm } from "@/lib/fmShortlist";
import { api } from "@/lib/api";
import { useGet, useAct, TabBar, PageHead } from "@/lib/ui";
import { RulesTab } from "@/components/rules/RulesTab";
import { ScoutCtx, useScout, fmtMoney } from "@/components/scout/ctx";
import { PlayersTab } from "@/components/scout/PlayersTab";
import { openPlayer } from "@/components/player/PlayerPanel";
import { MyClubTab, DealsTab } from "@/components/scout/ClubDeals";
import { ScatterTab, Breakdown } from "@/components/scout/Charts";
import { ComputedTab, RoleScoresTab } from "@/components/scout/Computed";
import { LeaguesTab } from "@/components/scout/LeaguesTab";
import { FormulasTab, Quadrant } from "@/components/scout/Lab";
import { ExploreTab, BoardTab, PicksTab, Compare4 } from "@/components/scout/Recruit";
import { PossessionTab, ImportTab } from "@/components/scout/DataTabs";
import { StatsTable } from "@/components/analysis/StatsTable";
import { MoneyballTab } from "@/components/scout/MoneyballTab";
import { SimilarTab } from "@/components/scout/SimilarTab";
import { YouthIntake } from "@/components/scout/YouthIntake";
import { RadarCompare } from "@/components/charts/RadarCompare";
import { WatchlistTab } from "@/components/scout/WatchlistTab";

const MAIN = [["players", "Find players"], ["similar", "Similar players"], ["youth", "Youth intake"], ["lists", "Lists"], ["compare", "Compare"], ["tools", "Tools"]];
const MAIN_KEYS = MAIN.map(([k]) => k);
const TOOL_GROUPS = [["Your own stats", [["computed", "Your own stats"], ["formulas", "Stat formulas"], ["roles", "Role ratings"]]],
  ["League strength", [["leagues", "League strength"], ["possession", "Possession"]]], ["Import from FM", [["import", "Import from FM"]]],
  ["More analysis", [["stats", "Stats Table"], ["myclub", "My Club"], ["deals", "Deals & Offers"], ["scatter", "Explore"], ["picks", "Director's picks"], ["rules", "Rules"]]]];
const TOOL_KEYS = TOOL_GROUPS.flatMap(([, t]) => t.map(([k]) => k));
const LISTS = { shortlist: "shortlist", watchlist: "watchlist", board: "board" };

const ToolPicker = ({ tab, setTab }) => (
  <div className="tool-groups" data-testid="scout-tools">
    {TOOL_GROUPS.map(([g, items]) => <div key={g} className="tool-group"><div className="eyebrow">{g}</div><TabBar id={`tools-${g.toLowerCase().replace(/[^a-z]+/g, "-")}`} value={tab} onChange={setTab} tabs={items} /></div>)}
  </div>
);

const Shortlist = ({ open }) => {
  const { data } = useGet("rankings", "/scouting/rankings", { shortlist_only: true, sort: "score" });
  const { prefs } = useScout();
  const act = useAct();
  return (
    <div className="card" style={{ padding: 8, overflowX: "auto" }}>
      {data?.rows.length > 0 && <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 6px 10px" }}>
        <small style={{ flex: 1, color: "var(--dim)" }}>Queue the whole list for FM's own shortlist; it goes in with your other game changes.</small>
        <button className="btn btn-p" onClick={() => sendToFm(act, data.rows.map((r) => r.unique_id))} data-testid="shortlist-send-fm"><ListPlus size={13} />Send all to FM shortlist</button></div>}
      <table className="tbl pin1" data-testid="rankings-table">
        <thead><tr><th>Player</th><th></th><th>Age</th><th>Club</th><th>Best role</th><th>Value</th><th>Score</th></tr></thead>
        <tbody>{data?.rows.map((r) => (
          <tr key={r.unique_id} onClick={() => open(r.unique_id)} data-testid={`ranking-row-${r.unique_id}`}>
            <td><b>{r.name}</b><small style={{ display: "block", color: "var(--dim)" }}>{r.nationality} · {r.positions.join(", ")}</small></td>
            <td onClick={(e) => e.stopPropagation()}><button className="ib" style={{ width: 28, height: 28, color: "var(--amb)" }} onClick={() => act(() => api.post("/scouting/shortlist", { unique_id: r.unique_id, action: "remove" }), "Removed from shortlist", ["rankings"])} data-testid={`shortlist-toggle-${r.unique_id}`}><Star size={14} fill="currentColor" /></button></td>
            <td>{r.age}</td><td>{r.club}</td><td>{r.best_role}</td><td className="mono">{fmtMoney(r.value, prefs)}</td><td className="mono" style={{ color: "var(--acc)" }}>{r.score}</td>
          </tr>))}</tbody>
      </table>
      {data && !data.rows.length && <p className="note" style={{ padding: 10 }}>Star players in the Players tab to shortlist them.</p>}
    </div>
  );
};

const CompareTable = ({ ids, clear }) => {
  const { view, prefs } = useScout();
  const { data = [] } = useGet("compare", "/scouting/compare", { ids: ids.filter((i) => i > 0).join(",") }, { enabled: ids.some((i) => i > 0) });
  const keys = data[0] && view === "full" ? Object.keys(data[0].attributes) : [];
  const money = (v) => fmtMoney(v, prefs);
  return (
    <div className="card" style={{ overflowX: "auto" }} data-testid="moneyball-compare">
      <div className="ttl">Side by side<span style={{ marginLeft: "auto" }} /><button className="btn" onClick={clear} data-testid="compare-clear">Clear</button></div>
      <table className="tbl" style={{ marginTop: 10 }}>
        <thead><tr><th></th>{data.map((p) => <th key={p.unique_id}>{p.name}</th>)}</tr></thead>
        <tbody>{[["Club", (p) => p.club], ["Age", (p) => p.age], ["Value", (p) => money(p.value)], ["Average rating", (p) => p.avg_rating ?? "—"], ["Value for money", (p) => p.vfm],
          ...(view === "full" ? [["Best roles", (p) => p.roles.map((r) => `${r.name} ${r.rating}`).join(" · ")]] : []), ...keys.map((k) => [k.replace(/_/g, " "), (p) => p.attributes[k]])].map(([l, fn]) => (
          <tr key={l} style={{ cursor: "default" }}><td style={{ color: "var(--mut)", textTransform: "capitalize" }}>{l}</td>{data.map((p) => <td key={p.unique_id} className="mono">{fn(p)}</td>)}</tr>))}</tbody>
      </table>
    </div>
  );
};

const ViewBar = ({ view, setView, prefs, setPrefs }) => (
  <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
    <TabBar id="scout-view" value={view} onChange={setView} tabs={[["full", "Full"], ["fair", "Fair play"], ["moneyball", "Moneyball"]]} />
    <select className="inp" style={{ width: 80, height: 36 }} value={prefs.currency} onChange={(e) => setPrefs({ ...prefs, currency: e.target.value })} data-testid="pref-currency"><option value="GBP">£</option><option value="EUR">€</option><option value="USD">$</option></select>
    <select className="inp" style={{ width: 120, height: 36 }} value={prefs.wages} onChange={(e) => setPrefs({ ...prefs, wages: e.target.value })} data-testid="pref-wages"><option value="week">Per week</option><option value="month">Per month</option><option value="year">Per year</option></select>
  </div>
);

const VIEW_NOTE = { full: "Full: everything, including hidden attributes, personality and a written report. Real CA and PA are never shown.", fair: "Fair play: only what your scouts would show you in the game. Attributes are ranges and hidden attributes are off.",
  moneyball: "Moneyball: match stats and price only. Attributes are switched off." };

export default function Scouting({ initialTab = "players" }) {
  const start = new URLSearchParams(window.location.search).get("tab");
  const [main, setMainRaw] = usePersist("scout-main", initialTab);
  const [tab, setTab] = usePersist("scout-tool", "computed");
  const [list, setList] = usePersist("scout-list", "shortlist");
  const [cmpView, setCmpView] = usePersist("scout-compare-view", "radar");
  const [view, setView] = usePersist("scout-view", "full");
  const setMain = (k) => setMainRaw(k);
  useEffect(() => {
    if (!start) { return; }
    if (start === "moneyball") { setMainRaw("players"); setView("moneyball"); }
    else if (LISTS[start]) { setMainRaw("lists"); setList(start); }
    else if (TOOL_KEYS.includes(start)) { setMainRaw("tools"); setTab(start); }
    else if (MAIN_KEYS.includes(start)) { setMainRaw(start); }
  }, [start]); // eslint-disable-line react-hooks/exhaustive-deps
  const shown = MAIN_KEYS.includes(main) ? main : "players";
  const [compare, setCompare] = usePersist("scout-compare", []);
  const setOpen = (uid) => { if (uid) { openPlayer(uid); } };
  const { data: saved } = useGet("scout-prefs", "/scout/prefs");
  const act = useAct();
  const prefs = saved || { currency: "GBP", wages: "week" };
  const setPrefs = (p) => act(() => api.put("/scout/prefs", p), null, ["scout-prefs"]);
  const toggleCompare = (id) => setCompare((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id].slice(-4)));
  return (
    <ScoutCtx.Provider value={{ view, prefs, openPlayer: setOpen, compare, toggleCompare }}>
      <div data-testid="scouting-page">
        <PageHead eyebrow="Search, compare and find value across every loaded league" title="Scout Players">
          <ViewBar view={view} setView={setView} prefs={prefs} setPrefs={setPrefs} />
        </PageHead>
        <p className="note" style={{ marginBottom: 10 }} data-testid="scout-view-note"><Scale size={12} style={{ display: "inline", verticalAlign: -1 }} /> {VIEW_NOTE[view]}</p>
        <div style={{ overflowX: "auto", marginBottom: 14 }}><TabBar id="scout-main" value={shown} onChange={setMain} tabs={MAIN.map(([k, l]) => [k, k === "compare" && compare.length ? `${l} (${compare.length})` : l])} /></div>
        {shown === "players" && <>{view === "moneyball" && <div style={{ marginBottom: 16 }} data-testid="moneyball-view"><div className="eyebrow" style={{ marginBottom: 8 }}>Value for money</div><MoneyballTab /></div>}<PlayersTab /></>}
        {shown === "similar" && <SimilarTab />}
        {shown === "youth" && <YouthIntake />}
        {shown === "lists" && <>
          <div style={{ marginBottom: 12 }}><TabBar id="scout-lists" value={list} onChange={setList} tabs={[["shortlist", "Shortlist"], ["watchlist", "Watchlist"], ["board", "Shortlist board"]]} /></div>
          <p className="note" style={{ marginBottom: 10 }} data-testid="lists-explainer"><Star size={12} style={{ display: "inline", verticalAlign: -1 }} /> Shortlist: players you're considering, and the ones you can send to FM's own shortlist. <Eye size={12} style={{ display: "inline", verticalAlign: -1 }} /> Watchlist: players you get bell alerts about, with your own rules.</p>
          {list === "shortlist" && <Shortlist open={setOpen} />}
          {list === "watchlist" && <WatchlistTab open={setOpen} />}
          {list === "board" && <BoardTab open={setOpen} />}</>}
        {shown === "compare" && (compare.length ? <>
          <div style={{ marginBottom: 12 }}><TabBar id="compare-view" value={cmpView} onChange={setCmpView} tabs={[["radar", "Radar"], ["side", "Side by side"], ["breakdown", "Stat breakdown"]]} /></div>
          {cmpView === "radar" && <RadarCompare ids={compare} view={view} />}
          {cmpView === "side" && <Compare4 ids={compare} clear={() => setCompare([])} />}
          {cmpView === "breakdown" && <Breakdown ids={compare} />}</>
          : <div className="soon" data-testid="compare-empty">Press Compare in any player panel, or the scales button in Find players, to add up to four players here.</div>)}
        {shown === "tools" && <ToolPicker tab={tab} setTab={setTab} />}
        {shown === "tools" && tab === "stats" && <StatsTable />}
        {shown === "tools" && tab === "myclub" && <MyClubTab />}
        {shown === "tools" && tab === "deals" && <><DealsTab /><Quadrant /></>}
        {shown === "tools" && tab === "formulas" && <FormulasTab />}
        {shown === "tools" && tab === "scatter" && <ExploreTab open={setOpen} />}
        {shown === "tools" && tab === "picks" && <PicksTab open={setOpen} onCompare={(id, many) => (many ? setCompare(id) : toggleCompare(id))} />}
        {shown === "tools" && tab === "computed" && <ComputedTab />}
        {shown === "tools" && tab === "roles" && <RoleScoresTab />}
        {shown === "tools" && tab === "leagues" && <LeaguesTab />}
        {shown === "tools" && tab === "possession" && <PossessionTab />}
        {shown === "tools" && tab === "import" && <ImportTab />}
        {shown === "tools" && tab === "rules" && <RulesTab module="scouting" title="Scouting and Moneyball rules" />}
      </div>
    </ScoutCtx.Provider>
  );
}
